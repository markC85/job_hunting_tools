import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Standalone PySide6 App")
window.resize(800, 600)

label = QLabel("Hello, PySide6!", window)
label.setAlignment(Qt.AlignCenter)
window.setCentralWidget(label)

window.show()
sys.exit(app.exec())