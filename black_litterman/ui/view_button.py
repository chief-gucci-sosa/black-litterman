from typing import List
from PySide2 import QtWidgets, QtCore, QtGui
from black_litterman.domain.views import View
from black_litterman.ui.view_designer_control import ViewDesignerDialog


class ViewButton(QtWidgets.QWidget):

    def __init__(self,
                 view: View,
                 asset_universe: List[str]):

        super().__init__()
        self._view = view
        self._asset_universe = asset_universe
        self._create_controls()
        self._initialise_controls(view)
        self._add_event_handlers()
        self._add_controls_to_layout()
        self._size_layout()

    def _create_controls(self):

        self._edit_button = QtWidgets.QPushButton("Edit")
        self._edit_button.setMinimumHeight(30)
        self._edit_button.setMinimumWidth(100)

        self._delete_button = QtWidgets.QPushButton("Delete")
        self._delete_button.setMinimumHeight(30)
        self._delete_button.setMinimumWidth(100)

        self._name_label = QtWidgets.QLabel()
        self._name_label.setMinimumHeight(30)

    def _initialise_controls(self,
                             view: View):

        self._name_label.setText(view.name)

    def _add_event_handlers(self):

        self._edit_button.clicked.connect(self._show_designer)

    def _add_controls_to_layout(self):

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self._name_label, 0, 0, 1, 2)
        self.layout.addWidget(self._edit_button, 1, 0)
        self.layout.addWidget(self._delete_button, 1, 1)

    def _size_layout(self):

        self.layout.setColumnStretch(0, 5)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)

    def _show_designer(self):
        designer = ViewDesignerDialog(self._view, self._asset_universe)
        result = designer.exec_()
        if result:
            print("done")

        designer.deleteLater()


if __name__ == "__main__":

    import sys
    from PySide2 import QtGui
    from black_litterman.domain.views import ViewAllocation

    app = QtWidgets.QApplication([])
    app.setFont(QtGui.QFont("Arial", 10))

    v = View(1, "Bonds outperform equity", 0.5, 2, ViewAllocation("test_1"))
    widget = ViewButton(v, ["asset_1", "asset_2", "asset_3", "asset_4"])
    widget.setWindowTitle("View button")
    widget.resize(30, 100)
    widget.show()

    sys.exit(app.exec_())





