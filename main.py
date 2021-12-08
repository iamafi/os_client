import sys

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets

from sign_in.signin import LoginScreen


if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #     sys.exit('Not enough args')

    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    login = LoginScreen(app, widget)
    widget.addWidget(login)
    widget.setFixedSize(800, 567)
    widget.setWindowTitle("Library Management System")
    widget.show()
    sys.exit(app.exec_())
