function getMapDefaults() {
    const body = document.body;
    return {
        lat: Number(body.dataset.mapDefaultLat || 44.6369),
        lng: Number(body.dataset.mapDefaultLng || 22.6597),
        zoom: Number(body.dataset.mapDefaultZoom || 13),
    };
}

function initNotificationCounter() {
    const counter = document.getElementById("notification-count");
    const unreadUrl = document.body.dataset.unreadUrl;

    if (!counter || !unreadUrl) {
        return;
    }

    fetch(unreadUrl)
        .then((response) => response.json())
        .then((payload) => {
            counter.textContent = String(payload.unread_count ?? 0);
        })
        .catch(() => {
            counter.textContent = "?";
        });
}

function initLocationPickerMap() {
    const mapElement = document.getElementById("location-picker-map");
    if (!mapElement || typeof L === "undefined") {
        return;
    }

    const defaults = getMapDefaults();
    const latitudeInput = document.getElementById("latitude");
    const longitudeInput = document.getElementById("longitude");
    const selectedPoint = document.getElementById("selected-point");

    const map = L.map(mapElement).setView([defaults.lat, defaults.lng], defaults.zoom);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    let marker = null;

    map.on("click", (event) => {
        const { lat, lng } = event.latlng;
        latitudeInput.value = lat.toFixed(6);
        longitudeInput.value = lng.toFixed(6);
        selectedPoint.textContent = `Coordonate alese: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;

        if (marker) {
            marker.setLatLng(event.latlng);
        } else {
            marker = L.marker(event.latlng).addTo(map);
        }
    });
}

function initIncidentsMap() {
    const mapElement = document.getElementById("incidents-map");
    if (!mapElement || typeof L === "undefined") {
        return;
    }

    const defaults = getMapDefaults();
    const map = L.map(mapElement).setView([defaults.lat, defaults.lng], defaults.zoom);
    const markersUrl = mapElement.dataset.markersUrl;

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    fetch(`${markersUrl}?${new URLSearchParams(window.location.search)}`)
        .then((response) => response.json())
        .then((payload) => {
            const bounds = [];

            // Marker-ele folosesc aceleasi filtre ca lista, ca sa nu apara diferente intre harta si carduri.
            payload.markers.forEach((markerData) => {
                const marker = L.marker([markerData.latitude, markerData.longitude]).addTo(map);
                marker.bindPopup(`
                    <strong>${markerData.title}</strong><br>
                    ${markerData.category}<br>
                    ${markerData.status} · ${markerData.priority}<br>
                    <a href="${markerData.url}">Detalii</a>
                `);
                bounds.push([markerData.latitude, markerData.longitude]);
            });

            if (bounds.length > 0) {
                map.fitBounds(bounds, { padding: [24, 24] });
            }
        })
        .catch(() => {
            mapElement.innerHTML = "<p class='muted-text'>Harta nu a putut incarca marker-ele.</p>";
        });
}

function initDetailMap() {
    const mapElement = document.getElementById("incident-detail-map");
    if (!mapElement || typeof L === "undefined") {
        return;
    }

    const lat = Number(mapElement.dataset.lat);
    const lng = Number(mapElement.dataset.lng);
    const title = mapElement.dataset.title;

    const map = L.map(mapElement).setView([lat, lng], 16);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    L.marker([lat, lng]).addTo(map).bindPopup(title).openPopup();
}

document.addEventListener("DOMContentLoaded", () => {
    initNotificationCounter();
    initLocationPickerMap();
    initIncidentsMap();
    initDetailMap();
});
