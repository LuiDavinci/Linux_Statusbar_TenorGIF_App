from PyQt5 import QtWidgets


class CustomDialog(QtWidgets.QDialog):

    def __init__(self, dialog_title: str, dialog_text: str) -> None:
        super(CustomDialog, self).__init__()
        self.setWindowTitle(dialog_title)
        label: QtWidgets.QLabel = QtWidgets.QLabel(dialog_text)

        button_box: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(label)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
