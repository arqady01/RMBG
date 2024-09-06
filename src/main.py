import sys
import os
from PyQt5.QtWidgets import QApplication
from gui import MainWindow

def main():
    # Set the environment variable to use the local model
    os.environ['U2NET_HOME'] = os.path.join(os.path.dirname(__file__), '..', 'models')
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()