from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import QDialog, QPushButton, QMessageBox, QMainWindow, QComboBox, QBoxLayout, QWidget, QHBoxLayout, \
    QTableWidget
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtGui
import sys
from globals import DEBUG

from utils.utils import send_request


def handle_error(response):
    if response["result"] == 'error':
        raise Exception(response["error"])


METHODS = (
    "authentication",
)

STATUS_MAP = {
    1: "Pending",
    2: "Borrowed",
    3: "Returned",
    0: "Rejected",
    4: "Overdue"
}


# Utility function to return proper verbose status
def verbose_status(borrow_request: dict):
    status = borrow_request['status']
    return STATUS_MAP[status] if status != 4 else f'{STATUS_MAP[status]} - {borrow_request["overdue_days"]}d'


ROLE_MAP = {
    0: 'Student',
    1: 'Admin'
}

session_key = ''


class LoginScreen(QDialog):
    def __init__(self, app, widget):
        self.app = app
        self.widget = widget
        super(LoginScreen, self).__init__()
        loadUi("gui/signin.ui", self)
        self.background_image.setPixmap(QtGui.QPixmap("resources/login_back.png"))
        self.inha_label.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login_button.clicked.connect(self.login)
        self.account = {}

    def login(self):
        try:
            username = self.username.text()
            password = self.password.text()
            if username == "" or password == "":
                self.error.setText("Fields cannot be empty")
            else:
                request = {
                    "method": METHODS[0],
                    "id": username,
                    "password": password
                }

                if DEBUG:
                    response = {
                        'result': 'success',
                        # 'error': 'adsd',
                        'session_key': 'akdjnaksdnakjd',
                        'account': {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': True
                        }
                    }
                else:
                    response = send_request(request)


                handle_error(response)

                if response["result"] == "incorrect-credentials":
                    self.error.setText("Incorrect credentials")
                else:
                    self.account = {
                        'id': response['account']['id'],
                        'name': response['account']['name'],
                        'role': ROLE_MAP[int(response['account']['is_admin'])],
                    }
                    global session_key
                    session_key = response['session_key']
                    if response["account"]["is_admin"]:
                        screen = AdministratorScreen(self.app, self.widget, self.account)
                    else:
                        screen = StudentScreen(self.app, self.widget, self.account)
                    self.widget.addWidget(screen)
                    self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())


class ChangePassword(QMainWindow):
    def __init__(self, parent=None):
        try:
            super(ChangePassword, self).__init__(parent)
            self.parent = parent
            loadUi("gui/change_password.ui", self)
            self.setWindowTitle("Change Password")
            self.setGeometry(230, 100, 350, 346)
            self.setFixedSize(350, 346)
            self.save.clicked.connect(self.save_changes)
            self.cancel.clicked.connect(self.cancel_changes)
            self.show()
        except Exception as e:
            raise e
            print(e)

    def cancel_changes(self):
        self.hide()

    def save_changes(self):
        try:
            global session_key
            old_password = self.old_password.text()
            new_password = self.new_password.text()
            repeat_password = self.repeat_password.text()
            request = {
                'method': 'change-password',
                'session_key': session_key,
                'old_password': old_password,
                'new_password': new_password
            }

            if old_password == '' or new_password == '' or repeat_password == '':
                self.error.setText("Fields cannot be empty")
            elif new_password == repeat_password:
                if DEBUG:
                    response = {
                        'result': 'success',
                        'session_key': 'new_session'
                    }
                else:
                    response = send_request(request)


                handle_error(response)
                if response['result'] == 'success':
                    session_key = response['session_key']
                    self.hide()
                elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                    self.hide()
                    self.parent.hide()
                    login = LoginScreen(self.parent.app, self.parent.widget)
                    self.parent.widget.addWidget(login)
                    self.parent.widget.setCurrentIndex(self.parent.widget.currentIndex() + 1)
                elif response['result'] == 'incorrect-old-password':
                    self.error.setText('Incorrect old password!')
                else:
                    raise Exception(response['result'])
            else:
                self.error.setText('New password does not correspond!')
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.parent.app.exec_())


class Settings(QMainWindow):
    def __init__(self, parent=None):
        try:
            super(Settings, self).__init__(parent)
            self.parent = parent
            self.widget = parent.widget
            self.app = parent.app
            loadUi("gui/settings.ui", self)
            self.setWindowTitle("Settings")
            self.setGeometry(210, 150, 350, 240)
            self.setFixedSize(350, 240)
            self.name.setText(parent.account['name'])
            self.id.setText(parent.account['id'])
            self.role.setText(parent.account['role'])
            self.log_out.clicked.connect(self.logout)
            self.change_password.clicked.connect(self.go_change_password)
            self.show()
        except Exception as e:
            raise e
            print(e)

    def go_change_password(self):
        ChangePassword(self)

    def logout(self):
        parent = self.parent
        try:
            request = {
                "method": "logout",
                "session_key": session_key
            }

            if DEBUG:
                response = {
                    'result': 'success'
                }
            else:
                response = send_request(request)

            self.hide()

            login = LoginScreen(parent.app, parent.widget)
            parent.widget.addWidget(login)
            parent.widget.setCurrentIndex(parent.widget.currentIndex() + 1)
        except Exception as e:
            raise e
            print(e)


class StudentScreen(QDialog):
    def __init__(self, app, widget, account):
        try:
            super(StudentScreen, self).__init__()
            self.buttons = []
            self.app = app
            self.widget = widget
            self.account = account
            loadUi("gui/studentMyBooks.ui", self)
            self.iut.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
            self.iut_2.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
            self.my_books_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.all_books_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.settings.clicked.connect(self.show_settings)
            self.settings_2.clicked.connect(self.show_settings)
            self.refresh.clicked.connect(self.go_refresh)
            self.refresh_2.clicked.connect(self.go_refresh)
            self.search_btn.clicked.connect(self.do_search)
            self.discard_search.clicked.connect(self.clean_search_field)

            request = {
                "method": "student-get",
                "session_key": session_key
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'my_borrow_requests': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 0
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 1
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 2
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 3
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 4
                        },
                    ],
                    'books': [
                        {
                            'isbn': 'asdassda11',
                            'name': 'hhh221h',
                            'author': 'mafi',
                            'requested': True
                        },
                        {
                            'isbn': 'asdasaada22',
                            'name': 'hh355hh',
                            'author': 'mafi',
                            'requested': True
                        },
                        {
                            'isbn': 'asdasdsa333s',
                            'name': 'hh000hh',
                            'author': 'mafi',
                            'requested': False
                        },
                    ]
                }
            else:
                response = send_request(request)

            handle_error(response)
            if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            else:
                self.load_my_books(response["my_borrow_requests"])
                self.load_all_books(response["books"])

            if response['fine_message']:
                FineMessage(response['fine_message'], response['fine_value'], self)
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def clean_search_field(self):
        self.search_field.setText('')
        self.go_refresh()

    def go_refresh(self):
        request = {
            "method": "student-get",
            "session_key": session_key
        }

        if DEBUG:
            response = {
                'result': 'success',
                'my_borrow_requests': [
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhh',
                        'author': 'mafi',
                        'borrow_date': '13.21.22',
                        'due_date': '44.53.33',
                        'status': 0
                    },
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhh',
                        'author': 'mafi',
                        'borrow_date': '13.21.22',
                        'due_date': '44.53.33',
                        'status': 1
                    },
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhh',
                        'author': 'mafi',
                        'borrow_date': '13.21.22',
                        'due_date': '44.53.33',
                        'status': 2
                    },
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhh',
                        'author': 'mafi',
                        'borrow_date': '13.21.22',
                        'due_date': '44.53.33',
                        'status': 3
                    },
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhh',
                        'author': 'mafi',
                        'borrow_date': '13.21.22',
                        'due_date': '44.53.33',
                        'status': 4
                    },
                ],
                'books': [
                    {
                        'isbn': 'asdassda11',
                        'name': 'hhh221h',
                        'author': 'mafi',
                        'requested': True
                    },
                    {
                        'isbn': 'asdasaada22',
                        'name': 'hh355hh',
                        'author': 'mafi',
                        'requested': True
                    },
                    {
                        'isbn': 'asdasdsa333s',
                        'name': 'hh000hh',
                        'author': 'mafi',
                        'requested': False
                    },
                ]
            }
        else:
            response = send_request(request)

        handle_error(response)
        if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
            login = LoginScreen(self.app, self.widget)
            self.widget.addWidget(login)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        else:
            self.load_my_books(response["my_borrow_requests"])
            self.load_all_books(response["books"])

    def show_settings(self):
        Settings(self)

    def load_my_books(self, books):
        try:
            header = self.my_books_table.horizontalHeader()
            self.my_books_table.setColumnWidth(0, 120)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            self.my_books_table.setColumnWidth(3, 90)
            self.my_books_table.setColumnWidth(4, 90)
            self.my_books_table.setColumnWidth(5, 90)
            row = 0
            self.my_books_table.setRowCount(len(books))
            for book in books:
                self.my_books_table.setItem(row, 0, QtWidgets.QTableWidgetItem(book['isbn']))
                self.my_books_table.setItem(row, 1, QtWidgets.QTableWidgetItem(book['name']))
                self.my_books_table.setItem(row, 2, QtWidgets.QTableWidgetItem(book['author']))
                self.my_books_table.setItem(row, 3, QtWidgets.QTableWidgetItem(book['borrow_date']))
                self.my_books_table.setItem(row, 4, QtWidgets.QTableWidgetItem(book['due_date']))
                self.my_books_table.setItem(row, 5, QtWidgets.QTableWidgetItem(verbose_status(book)))
                if book['status'] == 0:
                    self.my_books_table.item(row, 5).setForeground(QBrush(QColor(137, 137, 137)))
                elif book['status'] == 1:
                    self.my_books_table.item(row, 5).setForeground(QBrush(QColor(233, 164, 30)))
                elif book['status'] == 2:
                    self.my_books_table.item(row, 5).setForeground(QBrush(QColor(14, 173, 39)))
                elif book['status'] == 3:
                    self.my_books_table.item(row, 5).setForeground(QBrush(QColor(35, 92, 171)))
                else:
                    self.my_books_table.item(row, 5).setForeground(QBrush(QColor(197, 29, 29)))

                row += 1

        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def load_all_books(self, books):
        try:
            header = self.all_books_table.horizontalHeader()
            self.all_books_table.setColumnWidth(0, 120)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            self.all_books_table.setColumnWidth(4, 90)
            row = 0
            self.all_books_table.setRowCount(len(books))
            self.buttons = []
            for book in books:
                self.all_books_table.setItem(row, 0, QtWidgets.QTableWidgetItem(book['isbn']))
                self.all_books_table.setItem(row, 1, QtWidgets.QTableWidgetItem(book['name']))
                self.all_books_table.setItem(row, 2, QtWidgets.QTableWidgetItem(book['author']))
                self.all_books_table.setItem(row, 3, QtWidgets.QTableWidgetItem(book['copies_in_stock']))

                btn = QPushButton(self.all_books_table)
                if book['requested']:
                    btn.setText('Requested')
                    btn.setEnabled(False)
                    btn.setStyleSheet('background-color: rgb(130, 138, 149); color: rgb(255, 255, 255); '
                                      'border: 1px solid  rgb(255, 255, 255);')
                else:
                    btn.setStyleSheet('background-color: rgb(28, 99, 183); color: rgb(255, 255, 255); '
                                      'border: 1px solid  rgb(255, 255, 255);')
                    btn.setText('Request')
                btn.setObjectName(book['isbn'])
                self.buttons.append(btn)
                btn.clicked.connect(lambda state, x=len(self.buttons) - 1: self.request_book(x))

                self.all_books_table.setCellWidget(row, 4, btn)
                row += 1
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def request_book(self, btn_id):
        try:
            btn = self.buttons[btn_id]
            request = {
                "method": "student-request-book",
                "session_key": session_key,
                'isbn': btn.objectName(),
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'my_borrow_requests': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 0
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 1
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 2
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 3
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi',
                            'borrow_date': '13.21.22',
                            'due_date': '44.53.33',
                            'status': 4
                        },
                    ],
                    'books': [
                        {
                            'isbn': 'asdassda11',
                            'name': 'hhh221h',
                            'author': 'mafi',
                            'requested': True
                        },
                        {
                            'isbn': 'asdasaada22',
                            'name': 'hh355hh',
                            'author': 'mafi',
                            'requested': True
                        },
                        {
                            'isbn': 'asdasdsa333s',
                            'name': 'hh000hh',
                            'author': 'mafi',
                            'requested': False
                        },
                    ]
                }
            else:
                response = send_request(request)

            handle_error(response)
            if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            elif response['result'] == 'success-wait':
                WaitingList(response['message'], self)
                self.go_refresh()
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Book Request")

                if response['result'] == 'book-not-found':
                    msg.setText("Book was not found!")
                    msg.setIcon(QMessageBox.Critical)
                    msg.exec_()
                else:
                    msg.setText("You have requested a book")
                    msg.exec_()

                self.load_my_books(response["my_borrow_requests"])
                self.load_all_books(response["books"])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def do_search(self):
        filter_by = self.search_field.text()

        request = {
            'method': 'student-filter-books',
            'session_key': session_key,
            'filter_by': filter_by
        }

        response = send_request(request)

        if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
            login = LoginScreen(self.app, self.widget)
            self.widget.addWidget(login)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        else:
            self.load_all_books(response["books"])


class WaitingList(QMainWindow):
    def __init__(self, message, parent=None):
        try:
            super(WaitingList, self).__init__(parent)
            self.parent = parent
            loadUi("gui/waitingList.ui", self)
            self.setWindowTitle("Waiting list")
            self.setGeometry(230, 100, 350, 346)
            self.setFixedSize(355, 316)
            self.cancel_btn.clicked.connect(self.cancel)
            self.message.setText(message)
            self.show()
        except Exception as e:
            raise e
            print(e)

    def cancel(self):
        self.hide()


class FineMessage(QMainWindow):
    def __init__(self, fine_message, fine_value, parent=None):
        try:
            super(FineMessage, self).__init__(parent)
            self.parent = parent
            loadUi("gui/attention.ui", self)
            self.setWindowTitle("You have an overdue")
            self.setGeometry(230, 100, 350, 346)
            self.setFixedSize(266, 286)
            self.cancel_btn.clicked.connect(self.cancel)
            self.fine_message.setText(fine_message)
            self.fine_value.setText(f'Total: {fine_value} UZS')
            self.show()
        except Exception as e:
            raise e
            print(e)

    def cancel(self):
        self.hide()


class AddAccount(QMainWindow):
    def __init__(self, parent=None):
        try:
            super(AddAccount, self).__init__(parent)
            self.parent = parent
            loadUi("gui/add_account.ui", self)
            self.setWindowTitle("Add Account")
            self.setGeometry(210, 70, 352, 432)
            self.setFixedSize(352, 432)
            self.add.clicked.connect(self.add_account)
            self.cancel.clicked.connect(self.cancel_account)
            self.show()
        except Exception as e:
            raise e
            print(e)

    def cancel_account(self):
        self.hide()

    def add_account(self):
        try:
            name = self.name.text()
            uid = self.id.text()
            librarian = self.librarian.isChecked()
            student = self.student.isChecked()
            password = self.password.text()
            repeat_password = self.repeat_password.text()

            if name == '' or uid == '' or not (librarian or student) or password == '' or repeat_password == '':
                self.error.setText("Fields cannot be empty")
            elif password != repeat_password:
                self.error.setText('Passwords do not correspond to each other!')
            else:
                request = {
                    "method": "admin-create-update-account",
                    "session_key": session_key,
                    'account': {
                        'id': uid,
                        'name': name,
                        'is_admin': librarian
                    },
                    'password': password
                }

                if DEBUG:
                    response = {
                        'result': 'success',
                        'accounts': [
                            {
                                'id': '213132',
                                'name': 'david',
                                'is_admin': False
                            },
                            {
                                'id': '213112',
                                'name': 'mafi',
                                'is_admin': False
                            },
                            {
                                'id': '2132',
                                'name': 'yasya',
                                'is_admin': True
                            }
                        ],
                        'books': [
                            {
                                'isbn': 'asdasdads',
                                'name': 'hhhh',
                                'author': 'mafi'
                            },
                            {
                                'isbn': 'asdasdads',
                                'name': 'hhhssh',
                                'author': 'mafi'
                            },
                            {
                                'isbn': 'asdaaaaaaasdads',
                                'name': 'hhhh',
                                'author': 'mafi'
                            },
                        ],
                        'sorted_borrow_requests': {
                            'pending': [
                                {
                                    'borrow_request_id': 22,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'best',
                                    'status': 1,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                                {
                                    'borrow_request_id': 23,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'besaaadt',
                                    'status': 1,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                            ],
                            'others': [
                                {
                                    'borrow_request_id': 25,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'best',
                                    'status': 2,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                                {
                                    'borrow_request_id': 26,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'best',
                                    'status': 3,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                            ]
                        }
                    }
                else:
                    response = send_request(request)

                handle_error(response)

                if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                    self.hide()
                    login = LoginScreen(self.parent.app, self.parent.widget)
                    self.parent.widget.addWidget(login)
                    self.parent.widget.setCurrentIndex(self.parent.widget.currentIndex() + 1)
                else:
                    self.hide()
                    self.parent.load_accounts(response['accounts'])
                    self.parent.load_books(response['books'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.parent.app.exec_())


class AddBook(QMainWindow):
    def __init__(self, parent=None):
        try:
            super(AddBook, self).__init__(parent)
            self.parent = parent
            loadUi("gui/add_book.ui", self)
            self.setWindowTitle("Add Book")
            self.setGeometry(210, 100, 353, 340)
            self.setFixedSize(353, 378)
            self.add.clicked.connect(self.add_book)
            self.cancel.clicked.connect(self.cancel_book)
            self.show()
        except Exception as e:
            raise e
            print(e)

    def cancel_book(self):
        self.hide()

    def add_book(self):
        try:
            name = self.name.text()
            isbn = self.isbn.text()
            author = self.author.text()
            copies_available = int(self.copies_available.text())
            borrow_days = int(self.borrow_days.text())

            if name == '' or isbn == '' or author == '' or copies_available == '' or borrow_days == '':
                self.error.setText("Fields cannot be empty")
            else:
                request = {
                    "method": "admin-create-update-book",
                    "session_key": session_key,
                    'book': {
                        'isbn': isbn,
                        'name': name,
                        'author': author,
                        'copies_available': copies_available,
                        'borrow_days': borrow_days,
                    }
                }
                if DEBUG:
                    response = {
                        'result': 'success',
                        'accounts': [
                            {
                                'id': '213132',
                                'name': 'david',
                                'is_admin': False
                            },
                            {
                                'id': '213112',
                                'name': 'mafi',
                                'is_admin': False
                            },
                            {
                                'id': '2132',
                                'name': 'yasya',
                                'is_admin': True
                            }
                        ],
                        'books': [
                            {
                                'isbn': 'asdasdads',
                                'name': 'hhhh',
                                'author': 'mafi'
                            },
                            {
                                'isbn': 'asdasdads',
                                'name': 'hhhssh',
                                'author': 'mafi'
                            },
                            {
                                'isbn': 'asdaaaaaaasdads',
                                'name': 'hhhh',
                                'author': 'mafi'
                            },
                        ],
                        'sorted_borrow_requests': {
                            'pending': [
                                {
                                    'borrow_request_id': 22,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'best',
                                    'status': 1,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                                {
                                    'borrow_request_id': 23,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'besaaadt',
                                    'status': 1,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                            ],
                            'others': [
                                {
                                    'borrow_request_id': 25,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'best',
                                    'status': 2,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                                {
                                    'borrow_request_id': 26,
                                    'account_id': 'maernk',
                                    'account_name': 'mafi',
                                    'isbn': '3242342fs',
                                    'book_name': 'best',
                                    'status': 3,
                                    'borrow_date': '34-21-131',
                                    'due_date': '23-13-121'
                                },
                            ]
                        }
                    }
                else:
                    response = send_request(request)

                handle_error(response)

                if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                    self.hide()
                    login = LoginScreen(self.parent.app, self.parent.widget)
                    self.parent.widget.addWidget(login)
                    self.parent.widget.setCurrentIndex(self.parent.widget.currentIndex() + 1)
                else:
                    self.hide()
                    self.parent.load_accounts(response['accounts'])
                    self.parent.load_books(response['books'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.parent.app.exec_())


class PendingButtonsWidget(QWidget):

    def __init__(self, parent=None, request_id=None):
        super(PendingButtonsWidget, self).__init__(parent)
        self.parent = parent
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        btn1 = QPushButton(parent)
        btn1.setText('✓')
        btn1.setStyleSheet('background-color: rgb(21, 193, 90); color: rgb(255, 255, 255); '
                           'border: 1px solid  rgb(255, 255, 255);')
        btn2 = QPushButton(parent)
        btn2.setText('✕')
        btn2.setStyleSheet('background-color: rgb(207, 60, 1); color: rgb(255, 255, 255); '
                           'border: 1px solid  rgb(255, 255, 255);')
        btn1.clicked.connect(lambda state, x=request_id: self.accept(x))
        btn2.clicked.connect(lambda state, x=request_id: self.reject(x))
        layout.addWidget(btn1)
        layout.addWidget(btn2)

        self.setLayout(layout)

    def accept(self, request_id):
        try:
            request = {
                'method': 'admin-change-request-status',
                'session_key': session_key,
                'borrow_request_id': request_id,
                'new_status': 2
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)
            msg = QMessageBox()
            msg.setWindowTitle("Process Request")

            if response['result'] == 'borrow-request-not-found':
                msg.setText("Borrow request was not found!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.parent.app, self.parent.widget)
                self.parent.widget.addWidget(login)
                self.parent.widget.setCurrentIndex(self.parent.widget.currentIndex() + 1)
                return
            elif response['result'] == 'cannot-accept':
                msg.setWindowTitle('Could not accept')
                msg.setText('There is no copies of the book available. One of them must be returned first')
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
                return
            else:
                msg.setText("Borrow Request was accepted")
                msg.exec_()

            self.parent.load_accounts(response["accounts"])
            self.parent.load_books(response["books"])
            self.parent.load_pending(response['sorted_borrow_requests']['pending'])
            self.parent.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.parent.app.exec_())

    def reject(self, request_id):
        try:
            request = {
                'method': 'admin-change-request-status',
                'session_key': session_key,
                'borrow_request_id': request_id,
                'new_status': 0
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)
            msg = QMessageBox()
            msg.setWindowTitle("Process Request")

            if response['result'] == 'borrow-request-not-found':
                msg.setText("Borrow request was not found!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.parent.widget)
                self.parent.widget.addWidget(login)
                self.parent.widget.setCurrentIndex(self.parent.widget.currentIndex() + 1)
                return
            else:
                msg.setText("Borrow Request was rejected!")
                msg.exec_()

            self.parent.load_accounts(response["accounts"])
            self.parent.load_books(response["books"])
            self.parent.load_pending(response['sorted_borrow_requests']['pending'])
            self.parent.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.parent.app.exec_())


class AdministratorScreen(QDialog):
    def __init__(self, app, widget, account):
        try:
            super(AdministratorScreen, self).__init__()
            self.accounts_edit_buttons = []
            self.books_edit_buttons = []
            self.accounts_delete_buttons = []
            self.books_delete_buttons = []
            self.request_ids = []
            self.app = app
            self.widget = widget
            self.account = account
            loadUi("gui/administrator.ui", self)
            self.iut.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
            self.iut_2.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
            self.iut_3.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
            self.iut_4.setPixmap(QtGui.QPixmap("resources/iut-logo-blue-min.png"))
            self.requests_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.borrow_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.settings.clicked.connect(self.show_settings)
            self.settings_2.clicked.connect(self.show_settings)
            self.settings_3.clicked.connect(self.show_settings)
            self.settings_4.clicked.connect(self.show_settings)
            self.add_account.clicked.connect(self.go_add_account)
            self.add_book.clicked.connect(self.go_add_book)
            self.refresh.clicked.connect(self.go_refresh)
            self.refresh_2.clicked.connect(self.go_refresh)
            self.refresh_3.clicked.connect(self.go_refresh)
            self.refresh_4.clicked.connect(self.go_refresh)
            self.search_btn.clicked.connect(self.do_search)
            self.discard_search.clicked.connect(self.clean_search_field)

            request = {
                "method": "admin-get",
                "session_key": session_key
            }


            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)
            if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                self.hide()
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            else:
                self.load_accounts(response['accounts'])
                self.load_books(response['books'])
                self.load_pending(response['sorted_borrow_requests']['pending'])
                self.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def clean_search_field(self):
        self.search_field.setText('')
        self.go_refresh()

    def go_refresh(self):
        request = {
            "method": "admin-get",
            "session_key": session_key
        }

        if DEBUG:
            response = {
                'result': 'success',
                'accounts': [
                    {
                        'id': '213132',
                        'name': 'david',
                        'is_admin': False
                    },
                    {
                        'id': '213112',
                        'name': 'mafi',
                        'is_admin': False
                    },
                    {
                        'id': '2132',
                        'name': 'yasya',
                        'is_admin': True
                    }
                ],
                'books': [
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhh',
                        'author': 'mafi'
                    },
                    {
                        'isbn': 'asdasdads',
                        'name': 'hhhssh',
                        'author': 'mafi'
                    },
                    {
                        'isbn': 'asdaaaaaaasdads',
                        'name': 'hhhh',
                        'author': 'mafi'
                    },
                ],
                'sorted_borrow_requests': {
                    'pending': [
                        {
                            'borrow_request_id': 22,
                            'account_id': 'maernk',
                            'account_name': 'mafi',
                            'isbn': '3242342fs',
                            'book_name': 'best',
                            'status': 1,
                            'borrow_date': '34-21-131',
                            'due_date': '23-13-121'
                        },
                        {
                            'borrow_request_id': 23,
                            'account_id': 'maernk',
                            'account_name': 'mafi',
                            'isbn': '3242342fs',
                            'book_name': 'besaaadt',
                            'status': 1,
                            'borrow_date': '34-21-131',
                            'due_date': '23-13-121'
                        },
                    ],
                    'others': [
                        {
                            'borrow_request_id': 25,
                            'account_id': 'maernk',
                            'account_name': 'mafi',
                            'isbn': '3242342fs',
                            'book_name': 'best',
                            'status': 2,
                            'borrow_date': '34-21-131',
                            'due_date': '23-13-121'
                        },
                        {
                            'borrow_request_id': 26,
                            'account_id': 'maernk',
                            'account_name': 'mafi',
                            'isbn': '3242342fs',
                            'book_name': 'best',
                            'status': 3,
                            'borrow_date': '34-21-131',
                            'due_date': '23-13-121'
                        },
                    ]
                }
            }
        else:
            response = send_request(request)

        handle_error(response)
        if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
            self.hide()
            login = LoginScreen(self.app, self.widget)
            self.widget.addWidget(login)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        else:
            self.load_accounts(response['accounts'])
            self.load_books(response['books'])
            self.load_pending(response['sorted_borrow_requests']['pending'])
            self.load_borrow(response['sorted_borrow_requests']['others'])

    def load_pending(self, requests):
        header = self.requests_table.horizontalHeader()
        self.requests_table.setColumnWidth(0, 140)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.requests_table.setColumnWidth(2, 120)
        self.requests_table.setColumnWidth(3, 90)
        self.requests_table.setColumnWidth(4, 90)
        self.requests_table.setRowCount(len(requests))
        row = 0
        for book in requests:
            self.requests_table.setItem(row, 0, QtWidgets.QTableWidgetItem(book['isbn']))
            self.requests_table.setItem(row, 1, QtWidgets.QTableWidgetItem(book['book_name']))
            self.requests_table.setItem(row, 2, QtWidgets.QTableWidgetItem(book['account_id']))
            self.requests_table.setItem(row, 3, QtWidgets.QTableWidgetItem(STATUS_MAP[book['status']]))
            self.requests_table.setCellWidget(row, 4, PendingButtonsWidget(self, book['borrow_request_id']))
            if book['status'] == 1:
                self.requests_table.item(row, 3).setForeground(QBrush(QColor(233, 164, 30)))
            # TODO button
            row += 1

    def load_borrow(self, requests):
        header = self.borrow_table.horizontalHeader()
        self.borrow_table.setColumnWidth(0, 140)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.borrow_table.setColumnWidth(2, 120)
        self.borrow_table.setColumnWidth(3, 90)
        self.borrow_table.setColumnWidth(4, 90)
        self.borrow_table.setRowCount(len(requests))
        row = 0
        self.request_ids = []
        for book in requests:
            self.borrow_table.setItem(row, 0, QtWidgets.QTableWidgetItem(book['isbn']))
            self.borrow_table.setItem(row, 1, QtWidgets.QTableWidgetItem(book['book_name']))
            self.borrow_table.setItem(row, 2, QtWidgets.QTableWidgetItem(book['account_id']))
            self.borrow_table.setItem(row, 3, QtWidgets.QTableWidgetItem(verbose_status(book)))
            if book['status'] == 2 or book['status'] == 4:
                btn = QPushButton(self.borrow_table)
                btn.setText('Return')
                btn.setStyleSheet('background-color: rgb(35, 92, 171); color: rgb(255, 255, 255); '
                                  'border: 1px solid  rgb(255, 255, 255);')
                self.request_ids.append(book['borrow_request_id'])
                btn.clicked.connect(lambda state, x=len(self.request_ids) - 1: self.returned(x))
                self.borrow_table.setCellWidget(row, 4, btn)
            else:
                self.borrow_table.removeCellWidget(row, 4)
            if book['status'] == 0:
                self.borrow_table.item(row, 3).setForeground(QBrush(QColor(137, 137, 137)))
            elif book['status'] == 4:
                self.borrow_table.item(row, 3).setForeground(QBrush(QColor(197, 29, 29)))
            elif book['status'] == 2:
                self.borrow_table.item(row, 3).setForeground(QBrush(QColor(14, 173, 39)))
            elif book['status'] == 3:
                self.borrow_table.item(row, 3).setForeground(QBrush(QColor(35, 92, 171)))
            # TODO button
            row += 1

    def returned(self, request_id):
        try:
            request = {
                'method': 'admin-change-request-status',
                'session_key': session_key,
                'borrow_request_id': self.request_ids[request_id],
                'new_status': 3
            }


            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)
            msg = QMessageBox()
            msg.setWindowTitle("Process Request")

            if response['result'] == 'borrow-request-not-found':
                msg.setText("Borrow request was not found!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
                return
            else:
                msg.setText("Book was returned!")
                msg.exec_()

            self.load_accounts(response["accounts"])
            self.load_books(response["books"])
            self.load_pending(response['sorted_borrow_requests']['pending'])
            self.load_borrow(response['sorted_borrow_requests']['others'])

        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def go_add_account(self):
        AddAccount(self)

    def go_add_book(self):
        AddBook(self)

    def show_settings(self):
        Settings(self)

    def load_accounts(self, accounts):
        header = self.accounts_table.horizontalHeader()
        self.accounts_table.setColumnWidth(0, 120)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.accounts_table.setColumnWidth(2, 120)
        self.accounts_table.setColumnWidth(3, 90)
        self.accounts_table.setColumnWidth(4, 90)
        row = 0
        self.accounts_table.setRowCount(len(accounts))
        for acc in accounts:
            combo = QComboBox(self.accounts_table)
            combo.addItem(ROLE_MAP[0])
            combo.addItem(ROLE_MAP[1])
            combo.setCurrentIndex(acc['is_admin'])
            self.accounts_table.setItem(row, 0, QtWidgets.QTableWidgetItem(acc['id']))
            self.accounts_table.setItem(row, 1, QtWidgets.QTableWidgetItem(acc['name']))
            self.accounts_table.setCellWidget(row, 2, combo)
            # self.accounts_table.setItem(row, 2, QtWidgets.QTableWidgetItem(ROLE_MAP[acc['is_admin']]))
            btn1 = QPushButton(self.accounts_table)
            btn1.setText('Save')
            btn1.setStyleSheet('background-color: rgb(255, 255, 255); color: rgb(233, 164, 30); '
                               'border: 1px solid  rgb(233, 164, 30);')
            btn1.setObjectName(f'edit_{acc["id"]}')
            self.accounts_edit_buttons.append(btn1)
            btn1.clicked.connect(lambda state, x=row: self.edit_account(x))
            self.accounts_table.setCellWidget(row, 3, btn1)
            btn2 = QPushButton(self.accounts_table)
            btn2.setText('Delete')
            btn2.setStyleSheet('background-color: rgb(255, 255, 255); color: rgb(197, 29, 29); '
                               'border: 1px solid  rgb(197, 29, 29); margin-right: 1px')
            btn2.setObjectName(f'delete_{acc["id"]}')
            self.accounts_delete_buttons.append(btn2)
            btn2.clicked.connect(lambda state, x=len(self.accounts_delete_buttons) - 1: self.delete_account(x))
            self.accounts_table.setCellWidget(row, 4, btn2)
            row += 1

    def edit_account(self, row):
        try:
            request = {
                "method": "admin-create-update-account",
                "session_key": session_key,
                'account': {
                    'id': self.accounts_table.item(row, 0).text(),
                    'name': self.accounts_table.item(row, 1).text(),
                    'is_admin': bool(self.accounts_table.cellWidget(row, 2).currentIndex())
                }
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)
            msg = QMessageBox()
            msg.setWindowTitle("Edit Account")

            if response['result'] == 'last-admin-restriction':
                msg.setText("You cannot change role of last admin!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            else:
                msg.setText("You have successfully edited an account")
                msg.exec_()

                self.load_accounts(response["accounts"])
                self.load_books(response["books"])
                self.load_pending(response['sorted_borrow_requests']['pending'])
                self.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def delete_account(self, btn_id):
        try:
            btn = self.accounts_delete_buttons[btn_id]

            request = {
                "method": "admin-delete-account",
                "session_key": session_key,
                'id': btn.objectName()[7:],
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)

            msg = QMessageBox()
            msg.setWindowTitle("Delete Account")

            if response['result'] == 'account-not-found':
                msg.setText("Account was not found!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
                return
            elif response['result'] == 'last-admin-restriction':
                msg.setText("You cannot delete last admin!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
                return
            else:
                msg.setText("You have successfully deleted an account")
                msg.exec_()
                self.load_accounts(response["accounts"])
                self.load_books(response["books"])
                self.load_pending(response['sorted_borrow_requests']['pending'])
                self.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def load_books(self, books):
        header = self.books_table.horizontalHeader()
        self.books_table.setColumnWidth(0, 140)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.books_table.setColumnWidth(2, 140)
        self.books_table.setColumnWidth(3, 90)
        self.books_table.setColumnWidth(4, 90)
        self.books_table.setColumnWidth(5, 90)
        self.books_table.setRowCount(len(books))
        row = 0
        for book in books:
            self.books_table.setItem(row, 0, QtWidgets.QTableWidgetItem(book['isbn']))
            self.books_table.setItem(row, 1, QtWidgets.QTableWidgetItem(book['name']))
            self.books_table.setItem(row, 2, QtWidgets.QTableWidgetItem(book['author']))
            self.books_table.setItem(row, 3, QtWidgets.QTableWidgetItem(book['copies_in_stock']))

            # Set columns 0 and 3 as non-editable
            item_0 = self.books_table.item(row, 0)
            item_0.setFlags(item_0.flags() ^ Qt.ItemIsEditable)
            item_3 = self.books_table.item(row, 3)
            item_3.setFlags(item_3.flags() ^ Qt.ItemIsEditable)

            btn1 = QPushButton(self.books_table)
            btn1.setText('Save')
            btn1.setStyleSheet('background-color: rgb(255, 255, 255); color: rgb(233, 164, 30); '
                               'border: 1px solid  rgb(233, 164, 30);')
            btn1.setObjectName(f'edit_{book["isbn"]}')
            self.books_edit_buttons.append(btn1)

            btn1.clicked.connect(lambda state, x=row: self.edit_book(x))
            self.books_table.setCellWidget(row, 4, btn1)
            btn2 = QPushButton(self.books_table)
            btn2.setText('Delete')
            btn2.setStyleSheet('background-color: rgb(255, 255, 255); color: rgb(197, 29, 29); '
                               'border: 1px solid  rgb(197, 29, 29); margin-right: 1px')
            btn2.setObjectName(f'delete_{book["isbn"]}')
            self.books_delete_buttons.append(btn2)
            btn2.clicked.connect(lambda state, x=len(self.books_delete_buttons) - 1: self.delete_book(x))
            self.books_table.setCellWidget(row, 5, btn2)
            row += 1

    def edit_book(self, row):
        try:
            request = {
                "method": "admin-create-update-book",
                "session_key": session_key,
                'book': {
                    'isbn': self.books_table.item(row, 0).text(),
                    'name': self.books_table.item(row, 1).text(),
                    'author': self.books_table.item(row, 2).text()
                }
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)
            if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                self.hide()
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            else:
                msg = QMessageBox()
                msg.setWindowTitle("Edit Book")

                msg.setText("You have successfully edited a book")
                msg.exec_()

                self.load_accounts(response["accounts"])
                self.load_books(response["books"])
                self.load_pending(response['sorted_borrow_requests']['pending'])
                self.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def delete_book(self, btn_id):
        try:
            btn = self.books_delete_buttons[btn_id]
            request = {
                "method": "admin-delete-book",
                "session_key": session_key,
                'isbn': btn.objectName()[7:],
            }

            if DEBUG:
                response = {
                    'result': 'success',
                    'accounts': [
                        {
                            'id': '213132',
                            'name': 'david',
                            'is_admin': False
                        },
                        {
                            'id': '213112',
                            'name': 'mafi',
                            'is_admin': False
                        },
                        {
                            'id': '2132',
                            'name': 'yasya',
                            'is_admin': True
                        }
                    ],
                    'books': [
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdasdads',
                            'name': 'hhhssh',
                            'author': 'mafi'
                        },
                        {
                            'isbn': 'asdaaaaaaasdads',
                            'name': 'hhhh',
                            'author': 'mafi'
                        },
                    ],
                    'sorted_borrow_requests': {
                        'pending': [
                            {
                                'borrow_request_id': 22,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 23,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'besaaadt',
                                'status': 1,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ],
                        'others': [
                            {
                                'borrow_request_id': 25,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 2,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                            {
                                'borrow_request_id': 26,
                                'account_id': 'maernk',
                                'account_name': 'mafi',
                                'isbn': '3242342fs',
                                'book_name': 'best',
                                'status': 3,
                                'borrow_date': '34-21-131',
                                'due_date': '23-13-121'
                            },
                        ]
                    }
                }
            else:
                response = send_request(request)

            handle_error(response)

            msg = QMessageBox()
            msg.setWindowTitle("Delete Book")

            if response['result'] == 'book-not-found':
                msg.setText("Book was not found!")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
            elif response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
                login = LoginScreen(self.app, self.widget)
                self.widget.addWidget(login)
                self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
            else:
                msg.setText("You have successfully deleted a book")
                msg.exec_()
                self.load_accounts(response["accounts"])
                self.load_books(response["books"])
                self.load_pending(response['sorted_borrow_requests']['pending'])
                self.load_borrow(response['sorted_borrow_requests']['others'])
        except Exception as err:
            raise err
            print("Error:", err)
            sys.exit(self.app.exec_())

    def do_search(self):
        filter_by = self.search_field.text()

        request = {
            'method': 'admin-filter-books',
            'session_key': session_key,
            'filter_by': filter_by
        }

        response = send_request(request)

        if response["result"] == 'session-incorrect' or response['result'] == 'permission-denied':
            login = LoginScreen(self.app, self.widget)
            self.widget.addWidget(login)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        else:
            self.load_books(response["books"])
