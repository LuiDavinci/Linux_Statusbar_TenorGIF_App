from PyQt5 import QtWidgets, QtCore


class MySystemTray(QtWidgets.QSystemTrayIcon):
    open_main_signal: QtCore.pyqtSignal = QtCore.pyqtSignal(bool)

    def __init__(self) -> None:
        super(MySystemTray, self).__init__()
        self.open_window: bool = False
        self.activated.connect(self.showMenuOnTrigger)

    def showMenuOnTrigger(self, reason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.open_main_signal.emit(True)
