function getMapDefaults() {
    const body = document.body;
    return {
        lat: Number(body.dataset.mapDefaultLat || 44.6369),
        lng: Number(body.dataset.mapDefaultLng || 22.6597),
        zoom: Number(body.dataset.mapDefaultZoom || 13),
    };
}

function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) {
        return "0 B";
    }

    const units = ["B", "KB", "MB"];
    let value = bytes;
    let unitIndex = 0;

    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex += 1;
    }

    const roundedValue = unitIndex === 0 ? value.toFixed(0) : value.toFixed(1);
    return `${roundedValue} ${units[unitIndex]}`;
}

function clearElement(element) {
    if (!element) {
        return;
    }

    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function supportsClientPhotoProcessing() {
    return (
        typeof window.FileReader !== "undefined"
        && typeof window.DataTransfer !== "undefined"
        && typeof window.URL !== "undefined"
        && typeof window.URL.createObjectURL === "function"
        && typeof HTMLCanvasElement !== "undefined"
        && typeof HTMLCanvasElement.prototype.toBlob === "function"
        && typeof Blob !== "undefined"
        && typeof Blob.prototype.arrayBuffer === "function"
    );
}

function getFileExtension(filename) {
    const extension = filename.includes(".") ? filename.slice(filename.lastIndexOf(".")).toLowerCase() : "";
    return extension;
}

function detectPhotoTypeFromSignature(signatureBytes) {
    if (signatureBytes.length >= 3
        && signatureBytes[0] === 0xFF
        && signatureBytes[1] === 0xD8
        && signatureBytes[2] === 0xFF) {
        return "jpeg";
    }

    if (signatureBytes.length >= 8
        && signatureBytes[0] === 0x89
        && signatureBytes[1] === 0x50
        && signatureBytes[2] === 0x4E
        && signatureBytes[3] === 0x47
        && signatureBytes[4] === 0x0D
        && signatureBytes[5] === 0x0A
        && signatureBytes[6] === 0x1A
        && signatureBytes[7] === 0x0A) {
        return "png";
    }

    if (signatureBytes.length >= 12
        && signatureBytes[0] === 0x52
        && signatureBytes[1] === 0x49
        && signatureBytes[2] === 0x46
        && signatureBytes[3] === 0x46
        && signatureBytes[8] === 0x57
        && signatureBytes[9] === 0x45
        && signatureBytes[10] === 0x42
        && signatureBytes[11] === 0x50) {
        return "webp";
    }

    return null;
}

async function validatePhotoFileStructure(file) {
    const extension = getFileExtension(file.name);
    const expectedType = {
        ".jpg": "jpeg",
        ".jpeg": "jpeg",
        ".png": "png",
        ".webp": "webp",
    }[extension];

    if (!expectedType) {
        throw new Error(`Extensia fisierului ${file.name} nu este permisa.`);
    }

    const signatureBuffer = await file.slice(0, 12).arrayBuffer();
    const signatureBytes = new Uint8Array(signatureBuffer);
    const detectedType = detectPhotoTypeFromSignature(signatureBytes);

    if (detectedType !== expectedType) {
        throw new Error(`Structura fisierului ${file.name} nu corespunde extensiei declarate.`);
    }
}

function createCanvasToBlob(canvas, quality) {
    return new Promise((resolve, reject) => {
        canvas.toBlob((blob) => {
            if (!blob) {
                reject(new Error("Browserul nu a putut genera fotografia comprimata."));
                return;
            }
            resolve(blob);
        }, "image/jpeg", quality);
    });
}

function loadImageFromFile(file) {
    return new Promise((resolve, reject) => {
        const imageUrl = URL.createObjectURL(file);
        const image = new Image();

        image.onload = () => {
            URL.revokeObjectURL(imageUrl);
            resolve(image);
        };

        image.onerror = () => {
            URL.revokeObjectURL(imageUrl);
            reject(new Error(`Fisierul ${file.name} nu poate fi decodat ca imagine.`));
        };

        image.src = imageUrl;
    });
}

function buildOutputFilename(filename) {
    const stem = filename.includes(".") ? filename.slice(0, filename.lastIndexOf(".")) : filename;
    const safeStem = (stem || "fotografie")
        .replace(/[^\w.-]+/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-|-$/g, "")
        .slice(0, 80);

    return `${safeStem || "fotografie"}.jpg`;
}

async function compressImageFile(file, maxSizeBytes) {
    await validatePhotoFileStructure(file);

    const image = await loadImageFromFile(file);
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d", { alpha: false });

    if (!context) {
        throw new Error("Browserul nu poate procesa imaginile selectate.");
    }

    let width = image.naturalWidth;
    let height = image.naturalHeight;
    const maxInitialEdge = 2560;
    const maxOriginalEdge = Math.max(width, height);

    if (maxOriginalEdge > maxInitialEdge) {
        const scale = maxInitialEdge / maxOriginalEdge;
        width = Math.max(1, Math.round(width * scale));
        height = Math.max(1, Math.round(height * scale));
    }

    const qualitySteps = [0.9, 0.82, 0.74, 0.66, 0.58, 0.5, 0.42, 0.34];

    while (true) {
        canvas.width = width;
        canvas.height = height;
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, width, height);
        context.drawImage(image, 0, 0, width, height);

        for (const quality of qualitySteps) {
            const jpegBlob = await createCanvasToBlob(canvas, quality);
            if (jpegBlob.size <= maxSizeBytes) {
                const outputFile = new File([jpegBlob], buildOutputFilename(file.name), { type: "image/jpeg" });
                return {
                    file: outputFile,
                    width,
                    height,
                    sizeBytes: jpegBlob.size,
                };
            }
        }

        if (Math.max(width, height) <= 960) {
            break;
        }

        width = Math.max(1, Math.round(width * 0.85));
        height = Math.max(1, Math.round(height * 0.85));
    }

    throw new Error(`Fotografia ${file.name} nu a putut fi adusa sub limita de 5 MB.`);
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

function initIncidentCategoryDepartmentSync() {
    const categorySelect = document.getElementById("category_id");
    const suggestedDepartmentSelect = document.querySelector("[data-suggested-department-select]");
    const hint = document.querySelector("[data-department-suggestion-hint]");

    if (!categorySelect || !suggestedDepartmentSelect) {
        return;
    }

    function updateSuggestedDepartmentOptions() {
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        const defaultDepartmentId = selectedOption ? selectedOption.dataset.defaultDepartmentId || "" : "";
        const defaultDepartmentName = selectedOption ? selectedOption.dataset.defaultDepartmentName || "" : "";

        suggestedDepartmentSelect.value = defaultDepartmentId || "";

        if (!hint) {
            return;
        }

        if (!defaultDepartmentId) {
            hint.textContent = "Categoria aleasa nu are departament implicit. Poti selecta orice departament sau \"Nu stiu\".";
            return;
        }

        hint.textContent = `Categoria selectata recomanda ${defaultDepartmentName}, dar poti alege alt departament sau "Nu stiu".`;
    }

    categorySelect.addEventListener("change", updateSuggestedDepartmentOptions);
    updateSuggestedDepartmentOptions();
}

function initIncidentPhotoUpload() {
    const form = document.querySelector("[data-photo-upload-form]");
    if (!form) {
        return;
    }

    const photoInput = form.querySelector("[data-photo-input]");
    const processingStatusInput = form.querySelector("[data-photo-processing-status]");
    const statusBox = form.querySelector("[data-photo-upload-status]");
    const errorBox = form.querySelector("[data-photo-upload-errors]");
    const previewGrid = form.querySelector("[data-photo-preview-grid]");
    const submitButton = form.querySelector("button[type='submit']");

    if (!photoInput || !processingStatusInput || !statusBox || !errorBox || !previewGrid || !submitButton) {
        return;
    }

    const maxFiles = Number(form.dataset.photoMaxFiles || 3);
    const maxSizeBytes = Number(form.dataset.photoMaxSizeBytes || (5 * 1024 * 1024));
    const readyStatus = form.dataset.photoProcessingReady || "processed-jpeg-v1";
    let isProcessing = false;
    let previewUrls = [];

    function revokePreviewUrls() {
        previewUrls.forEach((previewUrl) => URL.revokeObjectURL(previewUrl));
        previewUrls = [];
    }

    function setStatus(message, tone = "info") {
        statusBox.textContent = message;
        statusBox.className = `photo-upload-status is-${tone}`;
    }

    function setErrors(messages) {
        clearElement(errorBox);

        messages.forEach((message) => {
            const paragraph = document.createElement("p");
            paragraph.className = "photo-upload-error";
            paragraph.textContent = message;
            errorBox.appendChild(paragraph);
        });
    }

    function renderPreviewCards(items) {
        clearElement(previewGrid);
        revokePreviewUrls();

        items.forEach((item) => {
            previewUrls.push(item.previewUrl);

            const card = document.createElement("article");
            card.className = "photo-preview-card";

            const image = document.createElement("img");
            image.src = item.previewUrl;
            image.alt = `Preview pentru ${item.file.name}`;
            image.loading = "lazy";

            const meta = document.createElement("div");
            meta.className = "photo-preview-meta";

            const title = document.createElement("strong");
            title.textContent = item.file.name;

            const detail = document.createElement("span");
            detail.textContent = `${item.width} × ${item.height} · ${formatBytes(item.sizeBytes)}`;

            meta.appendChild(title);
            meta.appendChild(detail);
            card.appendChild(image);
            card.appendChild(meta);
            previewGrid.appendChild(card);
        });
    }

    function resetUploadState() {
        processingStatusInput.value = "no-files";
        setErrors([]);
        clearElement(previewGrid);
        revokePreviewUrls();
        setStatus("Fotografiile vor fi procesate local in browser inainte de trimitere.", "info");
    }

    function updateSubmitState() {
        submitButton.disabled = isProcessing;
    }

    resetUploadState();
    updateSubmitState();

    photoInput.addEventListener("change", async () => {
        const selectedFiles = Array.from(photoInput.files || []);
        resetUploadState();

        if (selectedFiles.length === 0) {
            return;
        }

        if (selectedFiles.length > maxFiles) {
            photoInput.value = "";
            processingStatusInput.value = "error";
            setErrors([`Poti selecta maximum ${maxFiles} fotografii.`]);
            setStatus("Selectia de fotografii a fost respinsa.", "error");
            return;
        }

        if (!supportsClientPhotoProcessing()) {
            photoInput.value = "";
            processingStatusInput.value = "unsupported";
            setErrors([
                "Browserul curent nu suporta procesarea locala a fotografiilor. Poti trimite sesizarea fara poze.",
            ]);
            setStatus("Procesarea foto nu este suportata in acest browser.", "error");
            return;
        }

        isProcessing = true;
        processingStatusInput.value = "processing";
        updateSubmitState();
        setStatus("Procesam fotografiile in browser...", "info");

        try {
            const dataTransfer = new DataTransfer();
            const processedItems = [];

            for (let index = 0; index < selectedFiles.length; index += 1) {
                setStatus(`Procesam fotografia ${index + 1} din ${selectedFiles.length}...`, "info");
                const processed = await compressImageFile(selectedFiles[index], maxSizeBytes);
                dataTransfer.items.add(processed.file);
                processedItems.push({
                    ...processed,
                    previewUrl: URL.createObjectURL(processed.file),
                });
            }

            photoInput.files = dataTransfer.files;
            processingStatusInput.value = readyStatus;
            renderPreviewCards(processedItems);
            setStatus("Fotografiile sunt pregatite pentru trimitere.", "success");
        } catch (error) {
            photoInput.value = "";
            processingStatusInput.value = "error";
            setErrors([error instanceof Error ? error.message : "Fotografiile nu au putut fi procesate."]);
            setStatus("Fotografiile nu au putut fi procesate.", "error");
        } finally {
            isProcessing = false;
            updateSubmitState();
        }
    });

    form.addEventListener("submit", (event) => {
        const selectedCount = photoInput.files ? photoInput.files.length : 0;

        if (isProcessing) {
            event.preventDefault();
            setErrors(["Asteapta finalizarea procesarii fotografiilor inainte de trimitere."]);
            setStatus("Procesarea fotografiilor este in curs.", "error");
            return;
        }

        if (selectedCount > 0 && processingStatusInput.value !== readyStatus) {
            event.preventDefault();
            setErrors(["Fotografiile selectate nu au fost procesate corect. Reincearca selectia."]);
            setStatus("Fotografiile nu sunt pregatite pentru trimitere.", "error");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initNotificationCounter();
    initLocationPickerMap();
    initIncidentsMap();
    initDetailMap();
    initIncidentCategoryDepartmentSync();
    initIncidentPhotoUpload();
});
