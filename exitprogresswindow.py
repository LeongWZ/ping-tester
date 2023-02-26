from PySide6.QtWidgets import QVBoxLayout, QProgressBar, QLabel, QFrame
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class ExitProgressWindow(QFrame):
    def __init__(self, master):
        super().__init__()
        self.master = master

        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        self.setBackgroundRole(self.master.backgroundRole())
        self.setFrameStyle(QFrame.Box | QFrame.Raised)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.progressBar = QProgressBar()
        self.progressBar.setFixedWidth(400)
        layout.addWidget(self.progressBar, 1, alignment=Qt.AlignHCenter|Qt.AlignBottom)

        self.label = QLabel()
        self.label.setText("Exiting...")
        layout.addWidget(self.label, 1, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        