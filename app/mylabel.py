from PyQt5 import QtWidgets, QtGui, QtCore


class MyLabel(QtWidgets.QLabel):
    got_clicked: QtCore.pyqtSignal = QtCore.pyqtSignal(str, object)

    def __init__(self, name: str, data: dict = None) -> None:
        super(MyLabel, self).__init__()
        self.name: str = name
        self.data: dict = data
        self.setToolTip('Click to copy the link (works for some applications), otherwise right-click to save this.')

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            self.got_clicked.emit("left", self)
        else:
            self.got_clicked.emit("right", self)

    def set_data(self, new_data: dict) -> None:
        self.data = new_data
