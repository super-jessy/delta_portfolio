from PyQt6.QtWidgets import QApplication
import sys
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
