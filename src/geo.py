import sys
import random
import time
from PyQt5.QtWidgets import (
  QApplication,
  QWidget,
  QVBoxLayout,
  QLabel,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl
import folium 
# Функция для генерации случайной геопозиции
def generate_random_geoposition():
  latitude = random.uniform(40.65, 40.85)
  longitude = random.uniform(-74.10, -73.90)
  return latitude, longitude

class GeopositionApp(QWidget):
  def __init__(self):
    super().__init__()
    self.setFixedSize(1200, 880)

    # Инициализация карты
    self.map_view = QWebEngineView()
    self.map_view.setUrl(QUrl.fromLocalFile("/Users/kate/Desktop/geo-protocol-cp/src/pyqt/real_time_map.html"))

    # Инициализация таймера для обновления геопозиции
    self.timer = QTimer()
    self.timer.timeout.connect(self.update_map)
    self.timer.start(5000) # Обновление каждые 5 секунд

    # Создание макета
    layout = QVBoxLayout()
    layout.addWidget(self.map_view)
    self.setLayout(layout)

    # Заголовок окна
    self.setWindowTitle("Real-Time Geoposition")

  # Функция для обновления карты
  def update_map(self):
    # Генерация новой случайной геопозиции
    latitude, longitude = generate_random_geoposition()

    # Создание новой HTML-страницы карты
    new_map = folium.Map(location=[latitude, longitude], zoom_start=12)
    folium.Marker(
      location=[latitude, longitude],
      popup="Current Location",
      icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(new_map)
    new_map.save("real_time_map.html")

    # Обновление карты в QWebEngineView
    self.map_view.setUrl(QUrl.fromLocalFile("/Users/kate/Desktop/geo-protocol-cp/src/pyqt/real_time_map.html"))

if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = GeopositionApp()
  window.show()
  sys.exit(app.exec_())
