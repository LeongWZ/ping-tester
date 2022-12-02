from PySide6.QtWidgets import QApplication

from window import Window

import sys


def main():           
    app = QApplication()
    win = Window()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
