[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![MIT](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)
[![GitHub issues](https://img.shields.io/github/issues/Naereen/StrapDown.js.svg)](https://GitHub.com/Naereen/StrapDown.js/issues/)

# Black-Litterman asset allocation tool

This tool provides a simple python-based GUI application for constructing
multi-asset portfolios based on the **Black-Litterman** framework.

## Theoretical basis

The Black-Litterman asset allocation model allows an investor to construct a portfolio
based around the "market portfolio", but accounting for their own views about future 
market developments.  These views can be specified either as directional views on the
out/under performance of a single asset class, or can be on the relative performance
of one basket of assets against another.

The methodology employed in this tool is taken from 
"*A Step By Step Guide to the Black-Litterman Model*" by Thomas Idzorek.  A more 
theoretical (although still very accessible) justification for the model is 
provided by Charlotta Mankert and Michael J Selier in their 2011 paper 
"*Mathematical Derivation and Practical Implications for the use of the
Black-Litterman Model*".

## Configuring the app

The app can either run using local data or data from the Refinitiv DataStream API. If you are using 
the latter then a credentials file **black_litterman/credentials.json** must be added with a valid 
username and password for the API.

The settings.json file allows you to configure various other parameters of the model, including
the available universe of assets, the start date for the market data, the risk aversion and the 
Black-Litterman tau parameter. Detailed descriptions of these last two parameters are provided in the 
aforementioned academic resources.

## Using the app

![App image](resources/app_example.png)

1) The main chart shows the market portfolio allocation against the Black-Litterman
allocation (if one or more view is defined)

2) The views panel on the left can be used to add new market views up to a maximum 
of 4.  Currently, the app only supports single-asset relative views.

3) The chart can be changed to show the implied expected returns based on the current
market weights and covariances

4) The current calculation date can be changed - by default, this will be the prior business
day.  You can also change the start date, which sets the window over which the covariance matrix
is calculated.

## Configuring views

![View configuration](resources/view_config_example.png)

* The confidence describes how sure you are of a view - this is converted
into a covariance for the purposes of the model, as set out in the Idzorek
paper

* A view can be an absolute directional view on the performance of an asset, or 
a view on the performance of one asset vs another.  Although the Black-Litterman model
allows for views on *baskets* of assets, I have not had time to implement this here
(chiefly due to challenges on the UI side)

* You can select which asset(s) the view applies to - it is perfectly possible to have 
multiple views involving the same asset