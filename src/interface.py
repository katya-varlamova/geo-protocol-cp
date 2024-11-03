import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QComboBox, QRadioButton, QButtonGroup
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl
import folium 
from pyqt_loading_progressbar.loadingProgressBar import LoadingProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import random
from auth_client import AuthClient
from client import Reciever, Initiator

import sys
import time
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QMainWindow, QApplication

MAP_HTML_PATH = "/home/kate/Desktop/geo_protocol/src/real_time_map.html"

class GeopositionSignal(QObject):
    geopositionUpdated = pyqtSignal(tuple)

    def update_geoposition(self, location):
        print("GeopositionSignal")
        self.geopositionUpdated.emit(location)

class Worker(QThread):
    finished = pyqtSignal(tuple)
    def __init__(self, reciever):
        super(QThread, self).__init__()
        self.reciever = reciever
        

    def run(self):
        self.reciever.active = False
        res, msg = self.reciever.get_conn()
        self.finished.emit((res, msg))

class WorkerGeopositionExchange(QThread):
    finished_exchange = pyqtSignal()
    def __init__(self, client, signal):
        super(QThread, self).__init__()
        self.client = client
        self.signal = signal
        print("init sig")
        

    def run(self):
        print("run sig")
        self.client.exchange_geoposition(self.signal)
        self.finished_exchange.emit()
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auth Application")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.auth_client = AuthClient()
        self.roles = ["ожидающий соединения", "инициатор соединения"]
        self.ROLE_WAITER = 0
        self.ROLE_INITIATOR = 1
        self.pages = {
            "login": self.create_login_page(),
            "role_selection": self.create_role_selection_page(),
            "registration": self.create_registration_page(),
            "waiting_connection_1": self.create_waiting_connection_1_page(),
            "geoposition" : self.create_geoposition_show_page()
        }

        self.current_page = None
        self.show_page("login")
        self.client = None

    def create_geoposition_show_page(self):
        page = QWidget()
        self.map_view = QWebEngineView()
        self.map_view.setUrl(QUrl.fromLocalFile(MAP_HTML_PATH))

        layout = QVBoxLayout()
        layout.addWidget(self.map_view)

        page.setLayout(layout)

        return page

    def update_map(self, location):
        latitude, longitude = location[0], location[1]

        new_map = folium.Map(location=[latitude, longitude], zoom_start=12)
        folium.Marker(
        location=[latitude, longitude],
        popup="Current Location",
        icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(new_map)
        new_map.save("real_time_map.html")

        self.map_view.setUrl(QUrl.fromLocalFile(MAP_HTML_PATH))


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
        
        layout.addWidget(QLabel("Вход"))
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(QLabel("Логин"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Пароль"))
        layout.addWidget(self.password_input)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)
        
        register_button = QPushButton("Регистрация")
        register_button.clicked.connect(lambda: self.show_page("registration"))
        layout.addWidget(register_button)
        
        page.setLayout(layout)
        return page

    def handle_login(self):
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        
        if self.auth_client.login(self.username, self.password):
            self.show_page("role_selection")
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")

    def create_role_selection_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Выберете роль"))
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(self.roles)
        
        layout.addWidget(self.role_combo)
        select_button = QPushButton("Выбрать роль")
        select_button.clicked.connect(self.handle_role_selection)
        layout.addWidget(select_button)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(lambda: self.show_page("login"))
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def handle_role_selection(self):
        selected_role = self.role_combo.currentText()
        
        if self.roles[self.ROLE_INITIATOR] == selected_role:
            self.client = Initiator(self.username, self.password)
            users = [el["username"] + " [" + el["address"] + "]" for el in self.auth_client.get_users() if el["username"] != self.username]
            self.pages["initiator_connection"] = self.create_user_selection_page(users)
            self.show_page("initiator_connection")
        elif self.roles[self.ROLE_WAITER] == selected_role:
            self.client = Reciever(self.username, self.password)
            self.show_page("waiting_connection_1")
        else:
            QMessageBox.warning(self, "Ошибка", "сделайте выбор!")

    def create_registration_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Регистрация"))
        
        self.reg_username_input = QLineEdit()
        self.reg_password_input = QLineEdit()
        self.reg_address_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(QLabel("Логин"))
        layout.addWidget(self.reg_username_input)
        layout.addWidget(QLabel("Пароль"))
        layout.addWidget(self.reg_password_input)
        layout.addWidget(QLabel("Адрес, на котором будет ожидаться соединение"))
        layout.addWidget(self.reg_address_input)

        register_button = QPushButton("Зарегистрироваться")
        register_button.clicked.connect(self.handle_registration)
        layout.addWidget(register_button)

        back_button = QPushButton("Назад")
        back_button.clicked.connect(lambda: self.show_page("login"))
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def handle_registration(self):
        username = self.reg_username_input.text()
        password = self.reg_password_input.text()
        address = self.reg_address_input.text()

        if self.auth_client.register(username, password, address):
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.show_page("login")
        else:
            QMessageBox.warning(self, "Ошибка", "Регистрация не прошла")


    def start_waiting(self):
        self.loading_indicator = LoadingProgressBar() 
        self.layout.addWidget(self.loading_indicator)
        
        self.worker = Worker(self.client)
        self.worker.finished.connect(self.on_waiting_finished)
        
        self.worker.start()


    def on_waiting_finished(self, res):
        self.loading_indicator.hide()
        if not res[0]:
            QMessageBox.warning(self, "Ошибка", res[1])
            self.show_page("role_selection")
            return
        if self.client.active:
            initiator_name = self.client.initiator_name
            print(initiator_name)
            self.pages["waiting_connection_2"] = self.create_waiting_connection_2_page(initiator_name)
            self.show_page("waiting_connection_2")
        else:
            self.show_page("role_selection")

    def create_waiting_connection_1_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        back_button = QPushButton("Назад")
        back_button.clicked.connect(lambda: self.show_page("role_selection"))
    
        start_waiting_button = QPushButton("Начать ожидание")
        start_waiting_button.clicked.connect(self.start_waiting)
        
        layout.addWidget(start_waiting_button)
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page

    def create_user_selection_page(self, users):
        page = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Выберете того, чью геопозицию хотите видеть"))

        self.user_combo = QComboBox()
        self.user_combo.addItems(users)

        layout.addWidget(self.user_combo)

        geo_question_label = QLabel("Хотите ли вы сами делиться гепозицией?")
        
        geo_yes_radio = QRadioButton("Да")
        geo_yes_radio.setChecked(True)
        geo_no_radio = QRadioButton("Нет")
        
        layout.addWidget(geo_question_label)
        
        layout.addWidget(geo_yes_radio)
        layout.addWidget(geo_no_radio)

        initiate_button = QPushButton("Инициировать подключение")
        initiate_button.clicked.connect(lambda: self.handle_connection_initiation(geo_yes_radio.isChecked()))

        back_button = QPushButton("Назад")
        back_button.clicked.connect(lambda: self.show_page("role_selection"))

        layout.addWidget(initiate_button)
        layout.addWidget(back_button)

        page.setLayout(layout)
        return page
    
    def handle_connection_initiation(self, want_share):
        reciever = self.user_combo.currentText()
        self.client.want_share = want_share
        ret, message = self.client.exchange(reciever.split("[")[1].split("]")[0])
        if not ret:
            QMessageBox.warning(self, "Ошибка", message)
            self.show_page("role_selection")
            return
        if self.client.want_share != want_share:
            QMessageBox.warning(self, "Предупреждение", "Отказано в получении геопозиции")

        self.geoposition_signal = GeopositionSignal()
        self.geoposition_signal.geopositionUpdated.connect(self.update_map)
        self.worker_geo_exchange = WorkerGeopositionExchange(self.client, self.geoposition_signal)
        self.worker_geo_exchange.finished_exchange.connect(self.on_waiting_exchange_finished)
    
        self.worker_geo_exchange.start()
        self.show_page("geoposition")
        return
    
    def create_waiting_connection_2_page(self, initiator_name):
      page = QWidget()
      layout = QVBoxLayout()

      share_question_label = QLabel(f"Хотите ли вы делиться геопозицией с {initiator_name}?")

      layout = QVBoxLayout()
      bg1 = QButtonGroup(page)
      share_yes_radio = QRadioButton("Да")
      share_yes_radio.setChecked(True)
      share_no_radio = QRadioButton("Нет")
      bg1.addButton(share_yes_radio)
      bg1.addButton(share_no_radio)

      get_question_label = QLabel(f"Хотите ли вы получать геопозицию от {initiator_name}?")

      bg2 = QButtonGroup(page)
      get_yes_radio = QRadioButton("Да")
      get_yes_radio.setChecked(True)
      get_no_radio = QRadioButton("Нет")
      bg2.addButton(get_yes_radio)
      bg2.addButton(get_no_radio)

      select_button = QPushButton("Выбрать")
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

    def on_waiting_exchange_finished(self):
        if hasattr(self, "loading_indicator"):
            self.loading_indicator.hide()
        self.show_page("role_selection")
    
    def handle_waiting_connection_2(self, want_share, want_get):
        self.client.want_get = want_get
        self.client.want_share = want_share
        ret, message = self.client.exchange()
        if not ret:
            QMessageBox.warning(self, "Ошибка", message)
            self.show_page("role_selection")
            return

        if not self.client.want_share:
            QMessageBox.warning(self, "Ошибка", "Отказано делиться геопозицией")
            self.show_page("role_selection")
            return
        elif self.client.want_share and not self.client.want_get:
            self.loading_indicator = LoadingProgressBar()
            self.layout.addWidget(self.loading_indicator)
        elif self.client.want_share and self.client.want_get:
            self.show_page("geoposition")
        
        self.geoposition_signal = GeopositionSignal()
        self.geoposition_signal.geopositionUpdated.connect(self.update_map)
        self.worker_geo_exchange = WorkerGeopositionExchange(self.client, self.geoposition_signal)
        self.worker_geo_exchange.finished_exchange.connect(self.on_waiting_exchange_finished)
    
        self.worker_geo_exchange.start()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(400, 300)  # Set an appropriate size for your application
    window.show()
    sys.exit(app.exec_())
