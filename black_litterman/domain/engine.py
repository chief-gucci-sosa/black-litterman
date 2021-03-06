import numpy as np
import pandas as pd
from scipy import optimize
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from black_litterman.market_data.data_readers import BaseDataReader
from black_litterman.domain.views import ViewCollection, View
from black_litterman.constants import Configuration, Weights


@dataclass(frozen=True)
class CalculationSettings:
    tau: float
    risk_aversion: float
    start_date: str
    calculation_date: str
    asset_universe: Dict[str, str]

    @staticmethod
    def parse_from_config(config: Dict[str, Any]) -> "CalculationSettings":

        config_params = config[Configuration.PARAMETERS]
        config_data = config[Configuration.MARKET_DATA]

        calc_settings = CalculationSettings(config_params[Configuration.TAU],
                                            config_params[Configuration.RISK_AVERSION],
                                            config_data[Configuration.FIRST_DATE],
                                            config_data[Configuration.LAST_DATE],
                                            config_data[Configuration.ASSET_UNIVERSE])
        return calc_settings


class BLEngine:

    def __init__(self,
                 data_reader: BaseDataReader,
                 calc_settings: CalculationSettings):

        self._market_data_engine = data_reader.get_market_data_engine(calc_settings.start_date,
                                                                      calc_settings.calculation_date)
        self._calc_settings = calc_settings

    def get_market_weights(self,
                           end_date: Optional[str] = None) -> pd.Series:
        """
        return the implied market clearing weights
        """

        if end_date is None:
            end_date = self._calc_settings.calculation_date

        weights = self._market_data_engine.get_market_weights(end_date)
        weights.name = Weights.MARKET
        return weights

    def get_market_returns(self,
                           start_date: str,
                           end_date: str) -> pd.Series:
        """
        return the implied market clearing expected returns
        """

        return self._market_data_engine.get_implied_returns(start_date, end_date, self._calc_settings.risk_aversion)

    def get_asset_universe(self) -> List[str]:
        """
        return the names of the current available assets from the
        calculation settings
        """

        return list(self._calc_settings.asset_universe.keys())

    def get_dates(self) -> Tuple[str, str]:
        """
        get the start and end date from the calc settings
        """

        return self._calc_settings.start_date, self._calc_settings.calculation_date

    def get_black_litterman_weights(self,
                                    view_collection: ViewCollection,
                                    start_date: str,
                                    end_date: str) -> pd.Series:
        """
        derive target portfolio weights based on the Black-Litterman
        portfolio optimisation model
        """

        # get the market data
        market_weights = self._market_data_engine.get_market_weights(end_date)
        market_cov = self._market_data_engine.get_annualised_cov_matrix(start_date, end_date)

        # get the view specific data
        view_mat = view_collection.get_view_matrix(list(self._calc_settings.asset_universe))
        view_out_performance = view_collection.get_view_out_performances()
        view_cov = self.get_view_covariances_from_confidences(market_weights, market_cov, view_collection)

        # calc BL weights
        bl_weights = self._get_weights(market_weights, market_cov, view_mat, view_cov, view_out_performance)
        bl_weights.name = Weights.BLACK_LITTERMAN
        return bl_weights

    def get_view_covariances_from_confidences(self,
                                              market_weights: pd.Series,
                                              market_covariance: pd.DataFrame,
                                              view_collection: ViewCollection) -> pd.DataFrame:
        """
        build a diagonal covariance matrix from the views
        based on the confidence in each view
        """

        cov_by_view = dict()
        all_views = view_collection.get_all_views()

        for view in all_views:
            var = self._confidence_to_variance(view, market_weights, market_covariance)
            cov_by_view.update({view.id: var})

        var_series = pd.Series(cov_by_view)
        cov_matrix = pd.DataFrame(np.diag(var_series), index=var_series.index, columns=var_series.index)
        return cov_matrix

    def _get_weights(self,
                     market_weights: pd.Series,
                     market_cov: pd.DataFrame,
                     view_matrix: pd.DataFrame,
                     view_cov: pd.DataFrame,
                     view_out_performance: pd.Series) -> pd.Series:
        """
        Black-Litterman calculation to derive target weights
        """

        try:
            mat_1 = (view_cov.divide(self._calc_settings.tau) +
                     view_matrix.dot(market_cov).dot(view_matrix.T))
        except ValueError:
            print("matrix not aligned?")
        mat_1_inv = pd.DataFrame(np.linalg.inv(mat_1.values),
                                 index=mat_1.index, columns=mat_1.index)
        mat_2 = (view_out_performance.divide(self._calc_settings.risk_aversion)
                 - view_matrix.dot(market_cov).dot(market_weights))

        bl_weights = market_weights + view_matrix.T.dot(mat_1_inv).dot(mat_2)
        return bl_weights

    def _get_view_target_weights(self,
                                 view: View,
                                 market_weights: pd.Series,
                                 market_covariance: pd.DataFrame,
                                 view_matrix: pd.DataFrame,
                                 view_out_performance: pd.Series) -> pd.Series:
        """
        get target weights based on the view allocation and
        stated confidence in the view
        """

        zero_view_cov = pd.DataFrame([0], index=[view.id], columns=[view.id])
        full_confidence_weights = self._get_weights(market_weights, market_covariance, view_matrix, zero_view_cov,
                                                    view_out_performance)
        max_weight_difference = full_confidence_weights - market_weights
        target_weights = market_weights.add(view.confidence * max_weight_difference)

        return target_weights

    @staticmethod
    def _get_sum_squares_error(series_1: pd.Series,
                               series_2: pd.Series) -> float:
        """
        get the sum squared errors between two
        series
        """

        diff = series_1.subtract(series_2)
        sum_square = sum([x ** 2 for x in diff])
        return sum_square

    def _confidence_to_variance(self,
                                view: View,
                                market_weights: pd.Series,
                                market_covariance: pd.DataFrame,):
        """
        convert a view confidence level to a variance for
        that view
        """

        view_matrix = view.get_view_data_frame(list(self._calc_settings.asset_universe))
        view_out_performance = pd.Series([view.out_performance], index=[view.id])
        target_weights = self._get_view_target_weights(view, market_weights, market_covariance,
                                                       view_matrix, view_out_performance)

        def _error_vs_target_weights(var) -> float:
            view_cov = pd.DataFrame(var, index=[view.id], columns=[view.id])
            weights_for_cov = self._get_weights(market_weights, market_covariance, view_matrix, view_cov,
                                                view_out_performance)

            return self._get_sum_squares_error(weights_for_cov, target_weights)

        variance = optimize.minimize(_error_vs_target_weights, np.array(0.1), method="BFGS")
        return variance.x[0]
