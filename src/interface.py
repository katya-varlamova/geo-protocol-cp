import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QRadioButton, QButtonGroup
)
from pyqt_loading_progressbar.loadingProgressBar import LoadingProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Mock classes for auth_client and Reciever
class AuthClient:
    def login(self, username, password):
        return username == "user" and password == "pass"

    def register(self, username, password):
        return True  # Assume registration is always successful

    def get_users(self):
        return ["user1", "user2", "user3"]

auth_client = AuthClient()

class Reciever:
    active = False
    initiator_name = ""
    want_recv = False
    want_share = False
    want_get = False

    @staticmethod
    def get_conn():
        # Simulate waiting for a connection
        import time
        time.sleep(5)  # Simulate a delay for connection
        Reciever.active = True

class Worker(QThread):
    finished = pyqtSignal()

    def run(self):
        Reciever.get_conn()
        self.finished.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auth Application")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.pages = {
            "login": self.create_login_page(),
            "role_selection": self.create_role_selection_page(),
            "registration": self.create_registration_page(),
            "initiator_connection": self.create_user_selection_page(),
            "waiting_connection_1": self.create_waiting_connection_1_page(),
            "waiting_connection_2": self.create_waiting_connection_2_page(),
            "connection_success": self.create_connection_success_page()
        }

        self.current_page = None
        self.show_page("login")

    def show_page(self, page_name):
        if self.current_page:
            self.layout.removeWidget(self.current_page)
            self.current_page.hide()

        self.current_page = self.pages[page_name]
        self.layout.addWidget(self.current_page)
        self.current_page.show()

    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Login"))
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.password_input)
        
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)
        
        register_button = QPushButton("Register")
        register_button.clicked.connect(lambda: self.show_page("registration"))
        layout.addWidget(register_button)
        
        page.setLayout(layout)
        return page

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if auth_client.login(username, password):
            self.show_page("role_selection")
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials.")

    def create_role_selection_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Role"))
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Waiting Connection", "Initiator Connection"])
        
        layout.addWidget(self.role_combo)
        select_button = QPushButton("Select Role")
        select_button.clicked.connect(self.handle_role_selection)
        layout.addWidget(select_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.show_page("login"))
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def handle_role_selection(self):
        selected_role = self.role_combo.currentText()
        
        if "Initiator Connection" == selected_role:
            self.show_page("initiator_connection")
        else:
            self.show_page("waiting_connection_1")

    def create_registration_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Register"))
        
        self.reg_username_input = QLineEdit()
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(QLabel("Username"))
        layout.addWidget(self.reg_username_input)
        layout.addWidget(QLabel("Password"))
        layout.addWidget(self.reg_password_input)

        register_button = QPushButton("Register")
        register_button.clicked.connect(self.handle_registration)
        layout.addWidget(register_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.show_page("login"))
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def handle_registration(self):
        username = self.reg_username_input.text()
        password = self.reg_password_input.text()

        if auth_client.register(username, password):
            QMessageBox.information(self, "Success", "Registration successful!")
            self.show_page("login")
        else:
            QMessageBox.warning(self, "Error", "Registration failed.")


    def start_waiting(self):
        self.loading_indicator = LoadingProgressBar()  # Assuming you have this widget
        self.layout.addWidget(self.loading_indicator)
        
        self.worker = Worker()
        self.worker.finished.connect(self.on_waiting_finished)
        
        self.worker.start()


    def on_waiting_finished(self):
        self.loading_indicator.hide()

        if Reciever.active:
            self.show_page("waiting_connection_2")
        else:
            self.show_page("role_selection")

    def create_waiting_connection_1_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.show_page("role_selection"))
    
        start_waiting_button = QPushButton("Start Waiting")
        start_waiting_button.clicked.connect(self.start_waiting)
        
        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.show_page("role_selection"))
        layout.addWidget(start_waiting_button)
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def create_user_selection_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select User"))

        self.user_combo = QComboBox()
        self.user_combo.addItems(auth_client.get_users())

        layout.addWidget(self.user_combo)

        geo_question_label = QLabel("Do you want to share geolocation?")
        
        self.geo_yes_radio = QRadioButton("Yes")
        self.geo_no_radio = QRadioButton("No")
        
        layout.addWidget(geo_question_label)
        
        layout.addWidget(self.geo_yes_radio)
        layout.addWidget(self.geo_no_radio)

        initiate_button = QPushButton("Initiate Connection")
        initiate_button.clicked.connect(lambda: self.handle_waiting_connection_2(True, self.geo_yes_radio.isChecked()))

        #initiate_button.clicked.connect(self.initiate_connection)
        
        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.show_page("role_selection"))

        layout.addWidget(initiate_button)
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page
        
    def create_waiting_connection_2_page(self):
      page = QWidget()
      layout = QVBoxLayout()

      user_name = Reciever.initiator_name  # Assuming this is set somewhere in your code
      share_question_label = QLabel(f"Do you want to share geolocation with user {user_name}?")

      layout = QVBoxLayout()
      bg1 = QButtonGroup(page)
      share_yes_radio = QRadioButton("Yes")
      share_no_radio = QRadioButton("No")
      bg1.addButton(share_yes_radio)
      bg1.addButton(share_no_radio)

      get_question_label = QLabel(f"Do you want to receive geolocation from user {user_name}?")

      bg2 = QButtonGroup(page)
      get_yes_radio = QRadioButton("Yes")
      get_no_radio = QRadioButton("No")
      bg2.addButton(get_yes_radio)
      bg2.addButton(get_no_radio)

      select_button = QPushButton("Select")
      select_button.clicked.connect(lambda: self.handle_waiting_connection_2(share_yes_radio.isChecked(), get_yes_radio.isChecked()))

      back_button = QPushButton("Back")
      back_button.clicked.connect(lambda: self.show_page("role_selection"))

      layout.addWidget(share_question_label)
      layout.addWidget(share_yes_radio)
      layout.addWidget(share_no_radio)
      layout.addWidget(get_question_label)
      layout.addWidget(get_yes_radio)
      layout.addWidget(get_no_radio)
      layout.addWidget(select_button)
      layout.addWidget(back_button)

      page.setLayout(layout)
      return page

    def handle_waiting_connection_2(self, want_share, want_get):
      #user = self.user_combo.currentText()
      
      Reciever.want_share = want_share
      Reciever.want_get = want_get
      
      if not Reciever.want_share:
          # Go back to role selection
          self.show_page("role_selection")
      elif Reciever.want_share and not Reciever.want_get:
          # Start sharing only in a separate thread (not implemented in this mockup)
          pass  # Placeholder for sharing logic
          # After sharing logic completes, go back to role selection
          #self.show_page("role_selection")
      elif Reciever.want_share and Reciever.want_get:
          # Stay on this page or go to another logic (not defined in the requirements)
          pass  # Placeholder

    def create_connection_success_page(self):
      page = QWidget()
      layout = QVBoxLayout()

      success_label = QLabel("Connection Successful!")
      
      back_button = QPushButton("Back")
      back_button.clicked.connect(lambda: self.show_page("role_selection"))

      layout.addWidget(success_label)
      layout.addWidget(back_button)

      page.setLayout(layout)
      return page

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(400, 300)  # Set an appropriate size for your application
    window.show()
    sys.exit(app.exec_())
