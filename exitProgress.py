from PySide6.QtWidgets import QVBoxLayout, QProgressBar, QLabel, QFrame
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QThread

class ExitProgressWindow(QFrame):
    def __init__(self, master):
        super().__init__()
        self.master = master

        self.initUI()
        
        self.exitProgressThread = ExitProgressThread(self)

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
        self.label.setFont(QFont("Helvetica", 10))
        layout.addWidget(self.label, 1, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    
class ExitProgressThread(QThread):
    def __init__(self, master):
        super().__init__()
        self.master = master
    
    def run(self):
        activeThreadCount = self.master.master.threadpool.activeThreadCount()
        while activeThreadCount >= 0:
            killedThreadCount = self.master.progressBar.maximum() - activeThreadCount
            if killedThreadCount > self.master.progressBar.value():
                self.master.progressBar.setValue(killedThreadCount)
            
            if activeThreadCount == 0:
                break
            else:
                activeThreadCount = self.master.master.threadpool.activeThreadCount()
        
        self.msleep(50)
            