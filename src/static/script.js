const map = L.map('map').setView([0, 0], 2); // Начальная точка и зум
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

const socket = io();

let marker; // Переменная для хранения текущего маркера

socket.on('new_position', function(data) {
    const { lat, lon } = data;
    
    // Если маркер существует, обновляем его позицию
    if (marker) {
        marker.setLatLng([lat, lon]);
    } else {
        // Если маркера нет, создаем новый
        marker = L.marker([lat, lon]).addTo(map);
    }
    
    // Устанавливаем новую позицию центра карты
    map.setView([lat, lon], 13);
});

