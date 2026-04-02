const ACCESSIBILITY_STORAGE_KEY = "accessibility-preferences-v1";
const ACCESSIBILITY_DEFAULTS = {
    fontSize: "normal",
    contrast: "standard",
    motion: "normal",
};
const ACCESSIBILITY_ALLOWED_VALUES = {
    fontSize: ["normal", "large"],
    contrast: ["standard", "high"],
    motion: ["normal", "reduced"],
};
let pushRegistrationPromise = null;

function sanitizeAccessibilityPreferences(rawPreferences = {}) {
    const normalizedPreferences = { ...ACCESSIBILITY_DEFAULTS };

    Object.entries(ACCESSIBILITY_ALLOWED_VALUES).forEach(([key, allowedValues]) => {
        if (allowedValues.includes(rawPreferences[key])) {
            normalizedPreferences[key] = rawPreferences[key];
        }
    });

    return normalizedPreferences;
}

function applyAccessibilityPreferences(preferences) {
    const normalizedPreferences = sanitizeAccessibilityPreferences(preferences);
    const root = document.documentElement;

    Object.entries(normalizedPreferences).forEach(([key, value]) => {
        root.dataset[key] = value;
    });

    return normalizedPreferences;
}

function loadAccessibilityPreferences() {
    try {
        const storedPreferences = window.localStorage.getItem(ACCESSIBILITY_STORAGE_KEY);
        if (!storedPreferences) {
            return { ...ACCESSIBILITY_DEFAULTS };
        }

        return sanitizeAccessibilityPreferences(JSON.parse(storedPreferences));
    } catch (error) {
        return { ...ACCESSIBILITY_DEFAULTS };
    }
}

function saveAccessibilityPreferences(preferences) {
    window.localStorage.setItem(ACCESSIBILITY_STORAGE_KEY, JSON.stringify(preferences));
}

function initAccessibilityControls() {
    const form = document.querySelector("[data-accessibility-controls]");
    if (!form) {
        return;
    }

    const preferences = applyAccessibilityPreferences(loadAccessibilityPreferences());
    const controls = {
        fontSize: form.querySelector("[name='fontSize']"),
        contrast: form.querySelector("[name='contrast']"),
        motion: form.querySelector("[name='motion']"),
    };

    Object.entries(controls).forEach(([key, control]) => {
        if (control) {
            control.value = preferences[key];
        }
    });

    form.addEventListener("change", () => {
        const nextPreferences = sanitizeAccessibilityPreferences({
            fontSize: controls.fontSize ? controls.fontSize.value : ACCESSIBILITY_DEFAULTS.fontSize,
            contrast: controls.contrast ? controls.contrast.value : ACCESSIBILITY_DEFAULTS.contrast,
            motion: controls.motion ? controls.motion.value : ACCESSIBILITY_DEFAULTS.motion,
        });

        applyAccessibilityPreferences(nextPreferences);
        saveAccessibilityPreferences(nextPreferences);
        announceForScreenReader("Preferintele de accesibilitate au fost actualizate.");
    });
}

function initAccessibilityFlyout() {
    const flyout = document.querySelector("[data-accessibility-flyout]");
    const toggle = document.querySelector("[data-accessibility-toggle]");
    const panel = document.querySelector("[data-accessibility-panel]");
    if (!flyout || !toggle || !panel) {
        return;
    }

    const firstFocusableControl = panel.querySelector("select, input, button, textarea, a[href]");

    function setExpandedState(isExpanded) {
        toggle.setAttribute("aria-expanded", isExpanded ? "true" : "false");
        flyout.dataset.open = isExpanded ? "true" : "false";
    }

    function openFlyout() {
        if (!panel.hidden) {
            return;
        }

        panel.hidden = false;
        setExpandedState(true);

        if (firstFocusableControl) {
            window.setTimeout(() => {
                firstFocusableControl.focus({ preventScroll: true });
            }, 0);
        }
    }

    function closeFlyout({ restoreFocus = false } = {}) {
        if (panel.hidden) {
            return;
        }

        panel.hidden = true;
        setExpandedState(false);

        if (restoreFocus) {
            toggle.focus({ preventScroll: true });
        }
    }

    toggle.addEventListener("click", () => {
        if (panel.hidden) {
            openFlyout();
            return;
        }

        closeFlyout({ restoreFocus: true });
    });

    document.addEventListener("click", (event) => {
        if (panel.hidden || flyout.contains(event.target)) {
            return;
        }

        closeFlyout();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || panel.hidden) {
            return;
        }

        event.preventDefault();
        closeFlyout({ restoreFocus: true });
    });
}

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

function getScreenReaderAnnouncer() {
    return document.querySelector("[data-screenreader-announcer]");
}

function announceForScreenReader(message, politeness = "polite") {
    const announcer = getScreenReaderAnnouncer();
    if (!announcer || !message) {
        return;
    }

    announcer.setAttribute("aria-live", politeness);
    announcer.textContent = "";

    window.setTimeout(() => {
        announcer.textContent = message;
    }, 30);
}

function focusMessageRegion(element) {
    if (!element) {
        return;
    }

    if (!element.hasAttribute("tabindex")) {
        element.setAttribute("tabindex", "-1");
    }

    element.focus({ preventScroll: false });
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

function createMapFallbackMessage(message) {
    const paragraph = document.createElement("p");
    paragraph.className = "map-fallback-message";
    paragraph.textContent = message;
    paragraph.setAttribute("role", "status");
    return paragraph;
}

function renderMapFallback(mapElement, message) {
    if (!mapElement) {
        return;
    }

    clearElement(mapElement);
    mapElement.classList.add("has-fallback");
    mapElement.appendChild(createMapFallbackMessage(message));
}

function parseCoordinateValue(input, min, max) {
    if (!input) {
        return null;
    }

    const rawValue = input.value.trim();
    if (!rawValue) {
        return null;
    }

    const numericValue = Number(rawValue);
    if (!Number.isFinite(numericValue) || numericValue < min || numericValue > max) {
        return null;
    }

    return numericValue;
}

function setNotificationCounter(counter, unreadCount) {
    if (!counter) {
        return;
    }

    const normalizedCount = Number.isFinite(unreadCount) ? unreadCount : 0;
    counter.textContent = String(normalizedCount);
    counter.setAttribute("aria-label", `${normalizedCount} notificări necitite`);
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
            setNotificationCounter(counter, Number(payload.unread_count ?? 0));
        })
        .catch(() => {
            counter.textContent = "?";
            counter.setAttribute("aria-label", "Numărul notificărilor necitite nu a putut fi încărcat");
        });
}

function initLocationPickerMap() {
    const mapElement = document.getElementById("location-picker-map");
    const latitudeInput = document.getElementById("latitude");
    const longitudeInput = document.getElementById("longitude");
    const selectedPoint = document.getElementById("selected-point");
    const form = document.querySelector("[data-location-form]");
    const wizardForm = document.querySelector("[data-incident-wizard]");
    const nextButton = document.querySelector("[data-wizard-next]");
    const backButton = document.querySelector("[data-wizard-back]");
    const progressItems = Array.from(document.querySelectorAll("[data-wizard-progress-step]"));
    const stepPanels = Array.from(document.querySelectorAll("[data-wizard-step-panel]"));
    const mobileWizardQuery = window.matchMedia("(max-width: 980px)");

    if (!mapElement || !latitudeInput || !longitudeInput || !selectedPoint) {
        return;
    }

    let map = null;
    let marker = null;
    let fallbackRendered = false;
    let geolocationAttempted = false;

    function isNarrowWizard() {
        return mobileWizardQuery.matches;
    }

    function getStepHeading(step) {
        return wizardForm
            ? wizardForm.querySelector(`[data-wizard-step-panel="${step}"] [data-wizard-step-heading]`)
            : null;
    }

    function setSelectedPointMessage(message, politeness = "polite") {
        selectedPoint.setAttribute("aria-live", politeness);
        selectedPoint.textContent = message;
        announceForScreenReader(message, politeness);
    }

    function readCoordinates() {
        const latitude = parseCoordinateValue(latitudeInput, -90, 90);
        const longitude = parseCoordinateValue(longitudeInput, -180, 180);
        const hasLatitude = latitudeInput.value.trim() !== "";
        const hasLongitude = longitudeInput.value.trim() !== "";

        if (latitude === null || longitude === null) {
            if (hasLatitude || hasLongitude) {
                setSelectedPointMessage("Poziția selectată nu mai este validă. Alege din nou locația dispozitivului sau un punct pe hartă.");
            }
            return null;
        }

        return { latitude, longitude };
    }

    function updateMarker(latitude, longitude, shouldCenterMap = false) {
        if (!map) {
            return;
        }

        const latLng = [latitude, longitude];

        if (marker) {
            marker.setLatLng(latLng);
        } else {
            marker = L.marker(latLng).addTo(map);
        }

        if (shouldCenterMap) {
            const defaults = getMapDefaults();
            map.setView(latLng, Math.max(map.getZoom(), defaults.zoom));
        }
    }

    function syncCoordinateState() {
        const coordinates = readCoordinates();
        if (nextButton) {
            nextButton.disabled = !coordinates;
        }

        return coordinates;
    }

    function updateProgress(step) {
        progressItems.forEach((item) => {
            if (item.dataset.wizardProgressStep === String(step)) {
                item.setAttribute("aria-current", "step");
            } else {
                item.removeAttribute("aria-current");
            }
        });
    }

    function setWizardStep(step, options = {}) {
        if (!wizardForm) {
            return;
        }

        const nextStep = step === 2 ? 2 : 1;
        const coordinates = syncCoordinateState();
        if (nextStep === 2 && !coordinates) {
            return;
        }

        wizardForm.dataset.wizardStep = String(nextStep);
        updateProgress(nextStep);

        if (isNarrowWizard()) {
            stepPanels.forEach((panel) => {
                panel.hidden = panel.dataset.wizardStepPanel !== String(nextStep);
            });
        } else {
            stepPanels.forEach((panel) => {
                panel.hidden = false;
            });
        }

        if (map && nextStep === 1) {
            window.setTimeout(() => {
                map.invalidateSize();
            }, 0);
        }

        if (options.focusHeading) {
            const heading = getStepHeading(nextStep);
            if (heading) {
                focusMessageRegion(heading);
            }
        }
    }

    function initializeMapIfNeeded() {
        if (map || fallbackRendered) {
            if (map) {
                window.setTimeout(() => {
                    map.invalidateSize();
                }, 0);
            }
            return;
        }

        if (typeof L === "undefined") {
            renderMapFallback(
                mapElement,
                "Harta nu a putut fi încărcată. Formularul nu poate fi trimis până când poziția nu poate fi setată."
            );
            fallbackRendered = true;
            setSelectedPointMessage("Harta nu este disponibilă. Poziția sesizării nu a putut fi stabilită.", "assertive");
            return;
        }

        const defaults = getMapDefaults();
        map = L.map(mapElement).setView([defaults.lat, defaults.lng], defaults.zoom);
        mapElement.classList.remove("has-fallback");

        L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors",
        }).addTo(map);

        map.on("click", (event) => {
            const { lat, lng } = event.latlng;
            setCoordinates(
                lat,
                lng,
                    `Locație selectată pe hartă: ${lat.toFixed(6)}, ${lng.toFixed(6)}.`
            );
        });

        const initialCoordinates = syncCoordinateState();
        if (initialCoordinates) {
            updateMarker(initialCoordinates.latitude, initialCoordinates.longitude, true);
            setSelectedPointMessage(
                `Locație curentă în formular: ${initialCoordinates.latitude.toFixed(6)}, ${initialCoordinates.longitude.toFixed(6)}.`
            );
        }

        window.setTimeout(() => {
            map.invalidateSize();
        }, 0);
    }

    function syncWizardLayout() {
        const coordinates = syncCoordinateState();

        if (wizardForm) {
            const activeStep = wizardForm.dataset.wizardStep === "2" && coordinates ? 2 : 1;
            wizardForm.dataset.wizardStep = String(activeStep);
            setWizardStep(activeStep);
        }

        initializeMapIfNeeded();
    }

    function setCoordinates(latitude, longitude, message) {
        latitudeInput.value = latitude.toFixed(6);
        longitudeInput.value = longitude.toFixed(6);
        syncCoordinateState();
        updateMarker(latitude, longitude, true);
        setSelectedPointMessage(message ?? `Locație selectată: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}.`);
    }

    if (form) {
        form.addEventListener("submit", (event) => {
            if (syncCoordinateState() !== null) {
                return;
            }

            event.preventDefault();
            if (wizardForm && isNarrowWizard()) {
                setWizardStep(1);
            }
            setSelectedPointMessage(
                "Selectează locația sesizării direct pe hartă înainte de trimitere.",
                "assertive"
            );
            focusMessageRegion(selectedPoint);
        });
    }

    if (nextButton) {
        nextButton.addEventListener("click", () => {
            if (syncCoordinateState() === null) {
                setSelectedPointMessage(
                    "Alege mai întâi locația sesizării direct pe hartă.",
                    "assertive"
                );
                focusMessageRegion(selectedPoint);
                return;
            }

            setWizardStep(2, { focusHeading: true });
        });
    }

    if (backButton) {
        backButton.addEventListener("click", () => {
            setWizardStep(1, { focusHeading: true });
        });
    }

    function requestDeviceLocation() {
        if (geolocationAttempted) {
            return;
        }

        geolocationAttempted = true;

        if (!("geolocation" in navigator)) {
            setSelectedPointMessage("Browserul curent nu poate citi locația dispozitivului. Alege manual un punct pe hartă.", "assertive");
            return;
        }

        setSelectedPointMessage("Încercăm să preluăm locația dispozitivului...");

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                setCoordinates(
                    latitude,
                    longitude,
                    `Locația dispozitivului a fost preluată: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}.`
                );
            },
            (error) => {
                let message = "Locația dispozitivului nu a putut fi determinată. Alege manual un punct pe hartă.";
                if (error && error.code === 1) {
                    message = "Accesul la locația dispozitivului a fost refuzat. Alege manual un punct pe hartă.";
                } else if (error && error.code === 2) {
                    message = "Dispozitivul nu a putut determina poziția curentă. Alege manual un punct pe hartă.";
                } else if (error && error.code === 3) {
                    message = "Determinarea poziției a expirat. Alege manual un punct pe hartă.";
                }

                setSelectedPointMessage(message, "assertive");
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000,
            }
        );
    }

    if (typeof mobileWizardQuery.addEventListener === "function") {
        mobileWizardQuery.addEventListener("change", syncWizardLayout);
    } else if (typeof mobileWizardQuery.addListener === "function") {
        mobileWizardQuery.addListener(syncWizardLayout);
    }

    syncWizardLayout();
    requestDeviceLocation();
}

function initIncidentsMap() {
    const mapElement = document.getElementById("incidents-map");
    if (!mapElement) {
        return;
    }

    if (typeof L === "undefined") {
        renderMapFallback(mapElement, "Harta nu este disponibilă momentan. Lista textuală a sesizărilor rămâne funcțională.");
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
            renderMapFallback(mapElement, "Harta nu a putut încărca marker-ele. Folosește lista sesizărilor pentru navigare.");
        });
}

function initDetailMap() {
    const mapElement = document.getElementById("incident-detail-map");
    if (!mapElement) {
        return;
    }

    if (typeof L === "undefined") {
        renderMapFallback(mapElement, "Harta poziției nu este disponibilă. Coordonatele rămân afișate textual.");
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
            hint.textContent = "Categoria aleasă nu are departament implicit. Poți selecta orice departament sau \"Nu știu\".";
            return;
        }

        hint.textContent = `Categoria selectată recomandă ${defaultDepartmentName}, dar poți alege alt departament sau "Nu știu".`;
    }

    categorySelect.addEventListener("change", updateSuggestedDepartmentOptions);
    updateSuggestedDepartmentOptions();
}

function isValidatableField(field) {
    if (!(field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement)) {
        return false;
    }

    return !["hidden", "submit", "button", "reset"].includes(field.type);
}

function ensureFieldErrorElement(field) {
    if (!field.id) {
        return null;
    }

    let errorElement = document.getElementById(`${field.id}-error`);
    if (!errorElement) {
        errorElement = document.createElement("p");
        errorElement.id = `${field.id}-error`;
        errorElement.className = "field-error";
        errorElement.hidden = true;
        field.insertAdjacentElement("afterend", errorElement);
    }

    const describedByTokens = new Set((field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
    describedByTokens.add(errorElement.id);
    field.setAttribute("aria-describedby", Array.from(describedByTokens).join(" "));

    return errorElement;
}

function getFieldLabelText(form, field) {
    if (!field.id) {
        return field.name || "campul selectat";
    }

    const label = form.querySelector(`label[for="${field.id}"]`);
    return label ? label.textContent.trim() : (field.name || field.id);
}

function updateFieldAccessibilityState(field) {
    if (!isValidatableField(field)) {
        return;
    }

    const errorElement = ensureFieldErrorElement(field);
    if (!errorElement) {
        return;
    }

    if (field.checkValidity()) {
        field.removeAttribute("aria-invalid");
        errorElement.hidden = true;
        errorElement.textContent = "";
        return;
    }

    field.setAttribute("aria-invalid", "true");
    errorElement.hidden = false;
    errorElement.textContent = field.validationMessage;
}

function renderFormErrorSummary(form, invalidFields) {
    const summary = form.querySelector("[data-form-error-summary]");
    if (!summary) {
        return;
    }

    if (invalidFields.length === 0) {
        summary.hidden = true;
        clearElement(summary);
        return;
    }

    clearElement(summary);
    const intro = document.createElement("p");
    intro.textContent = "Formularul are campuri care trebuie corectate:";

    const list = document.createElement("ul");
    invalidFields.forEach((field) => {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = field.id ? `#${field.id}` : "#";
        link.textContent = getFieldLabelText(form, field);
        link.addEventListener("click", (event) => {
            event.preventDefault();
            field.focus();
        });
        item.appendChild(link);
        list.appendChild(item);
    });

    summary.appendChild(intro);
    summary.appendChild(list);
    summary.hidden = false;
    focusMessageRegion(summary);
}

function initAccessibleForms() {
    const forms = document.querySelectorAll("[data-accessible-form]");
    if (forms.length === 0) {
        return;
    }

    forms.forEach((form) => {
        const fields = Array.from(form.querySelectorAll("input, select, textarea")).filter(isValidatableField);
        let hasAttemptedSubmit = false;

        fields.forEach((field) => {
            ensureFieldErrorElement(field);
            field.addEventListener("blur", () => updateFieldAccessibilityState(field));
            field.addEventListener("input", () => {
                updateFieldAccessibilityState(field);
                if (hasAttemptedSubmit) {
                    const invalidFields = fields.filter((candidate) => !candidate.checkValidity());
                    renderFormErrorSummary(form, invalidFields);
                }
            });
            field.addEventListener("change", () => {
                updateFieldAccessibilityState(field);
                if (hasAttemptedSubmit) {
                    const invalidFields = fields.filter((candidate) => !candidate.checkValidity());
                    renderFormErrorSummary(form, invalidFields);
                }
            });
        });

        form.addEventListener("submit", (event) => {
            const invalidFields = fields.filter((field) => !field.checkValidity());
            invalidFields.forEach((field) => updateFieldAccessibilityState(field));

            if (invalidFields.length > 0) {
                hasAttemptedSubmit = true;
                renderFormErrorSummary(form, invalidFields);
                event.preventDefault();
                return;
            }

            renderFormErrorSummary(form, []);
        });
    });
}

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let index = 0; index < rawData.length; index += 1) {
        outputArray[index] = rawData.charCodeAt(index);
    }

    return outputArray;
}

async function ensurePushServiceWorkerRegistration() {
    if (pushRegistrationPromise) {
        return pushRegistrationPromise;
    }

    if (!("serviceWorker" in navigator)) {
        throw new Error("Browserul curent nu suportă notificări pe dispozitiv.");
    }

    const serviceWorkerUrl = document.body.dataset.pushServiceWorkerUrl;
    if (!serviceWorkerUrl) {
        throw new Error("Serviciul pentru notificări pe dispozitiv nu este configurat.");
    }

    pushRegistrationPromise = navigator.serviceWorker.register(serviceWorkerUrl, { scope: "/" });
    return pushRegistrationPromise;
}

async function ensureCurrentDevicePushSubscription() {
    const body = document.body;
    const publicKey = body.dataset.pushPublicKey;
    const subscribeUrl = body.dataset.pushSubscribeUrl;

    if (body.dataset.pushEnabled !== "true" || !publicKey || !subscribeUrl) {
        throw new Error("Notificările pe dispozitiv nu sunt configurate pe server.");
    }

    if (typeof Notification === "undefined") {
        throw new Error("Browserul curent nu suportă Web Push.");
    }

    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
        throw new Error("Browserul nu a permis notificări pe dispozitiv pentru acest website.");
    }

    const registration = await ensurePushServiceWorkerRegistration();
    let subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
        subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(publicKey),
        });
    }

    const response = await fetch(subscribeUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        body: JSON.stringify(subscription.toJSON()),
    });

    const payload = await response.json();
    if (!response.ok || !payload.ok) {
        throw new Error(payload.message || "Dispozitivul nu a putut fi abonat pentru notificări.");
    }

    return payload;
}

function setFollowFormMessage(form, message, isError = false) {
    const statusBox = form.querySelector("[data-follow-status]");
    const errorBox = form.querySelector("[data-follow-error]");

    if (statusBox) {
        statusBox.textContent = isError ? "" : message;
    }

    if (errorBox) {
        errorBox.hidden = !isError;
        errorBox.textContent = isError ? message : "";
        if (isError) {
            focusMessageRegion(errorBox);
        }
    }

    announceForScreenReader(message, isError ? "assertive" : "polite");
}

function initFollowForms() {
    const forms = document.querySelectorAll("[data-follow-form]");
    if (forms.length === 0) {
        return;
    }

    forms.forEach((form) => {
        const pushCheckbox = form.querySelector("input[name='channels'][value='web_push']");
        const hiddenSubscriptionInput = form.querySelector("[data-push-subscription-id]");
        const submitButton = form.querySelector("button[type='submit']");

        if (!pushCheckbox || !hiddenSubscriptionInput || !submitButton) {
            return;
        }

        form.addEventListener("submit", async (event) => {
            if (!pushCheckbox.checked) {
                hiddenSubscriptionInput.value = "";
                return;
            }

            event.preventDefault();
            submitButton.disabled = true;
            submitButton.setAttribute("aria-disabled", "true");
            setFollowFormMessage(form, "Activăm notificările pe dispozitivul curent...");

            try {
                const payload = await ensureCurrentDevicePushSubscription();
                hiddenSubscriptionInput.value = String(payload.subscription_id);
                setFollowFormMessage(form, "Dispozitivul a fost pregătit pentru notificări.");
                form.submit();
            } catch (error) {
                const selectedChannels = Array.from(form.querySelectorAll("input[name='channels']:checked"))
                    .map((input) => input.value);
                const message = error instanceof Error ? error.message : "Notificările pe dispozitiv nu au putut fi activate.";

                hiddenSubscriptionInput.value = "";
                if (selectedChannels.length > 1) {
                    pushCheckbox.checked = false;
                    setFollowFormMessage(
                        form,
                        `${message} Formularul va fi salvat doar cu celelalte canale selectate.`,
                        true
                    );
                    submitButton.disabled = false;
                    submitButton.setAttribute("aria-disabled", "false");
                    window.setTimeout(() => form.submit(), 60);
                    return;
                }

                setFollowFormMessage(form, message, true);
                submitButton.disabled = false;
                submitButton.setAttribute("aria-disabled", "false");
            }
        });
    });
}

function initPushSupport() {
    if (document.body.dataset.pushEnabled !== "true") {
        return;
    }

    ensurePushServiceWorkerRegistration().catch(() => {
        announceForScreenReader("Serviciul pentru notificări pe dispozitiv nu a putut fi pregătit.");
    });
}

function initIncidentPhotoUpload() {
    const form = document.querySelector("[data-photo-upload-form]");
    if (!form) {
        return;
    }

    const pickerInput = form.querySelector("[data-photo-picker-input]");
    const photoInput = form.querySelector("[data-photo-input]");
    const addButton = form.querySelector("[data-add-photos-button]");
    const processingStatusInput = form.querySelector("[data-photo-processing-status]");
    const statusBox = form.querySelector("[data-photo-upload-status]");
    const errorBox = form.querySelector("[data-photo-upload-errors]");
    const previewGrid = form.querySelector("[data-photo-preview-grid]");
    const submitButton = form.querySelector("button[type='submit']");

    if (!pickerInput || !photoInput || !addButton || !processingStatusInput || !statusBox || !errorBox || !previewGrid || !submitButton) {
        return;
    }

    const maxFiles = Number(form.dataset.photoMaxFiles || 3);
    const maxSizeBytes = Number(form.dataset.photoMaxSizeBytes || (5 * 1024 * 1024));
    const readyStatus = form.dataset.photoProcessingReady || "processed-jpeg-v1";
    let isProcessing = false;
    let processedItems = [];
    let previewUrls = [];

    function revokePreviewUrls() {
        previewUrls.forEach((previewUrl) => URL.revokeObjectURL(previewUrl));
        previewUrls = [];
    }

    function setStatus(message, tone = "info") {
        statusBox.textContent = message;
        statusBox.className = `photo-upload-status is-${tone}`;
        announceForScreenReader(message, tone === "error" ? "assertive" : "polite");
    }

    function setErrors(messages) {
        clearElement(errorBox);

        messages.forEach((message) => {
            const paragraph = document.createElement("p");
            paragraph.className = "photo-upload-error";
            paragraph.textContent = message;
            errorBox.appendChild(paragraph);
        });

        if (messages.length > 0) {
            focusMessageRegion(errorBox);
            announceForScreenReader(messages[0], "assertive");
        }
    }

    function formatPreparedPhotoCount(count) {
        if (count === 1) {
            return "1 fotografie pregătită pentru trimitere.";
        }

        return `${count} fotografii pregătite pentru trimitere.`;
    }

    function syncProcessedFiles() {
        if (typeof window.DataTransfer === "undefined") {
            if (processedItems.length === 0) {
                photoInput.value = "";
            }
            return;
        }

        const dataTransfer = new DataTransfer();
        processedItems.forEach((item) => dataTransfer.items.add(item.file));
        photoInput.files = dataTransfer.files;
    }

    function updateActionState() {
        submitButton.disabled = isProcessing;
        submitButton.setAttribute("aria-disabled", isProcessing ? "true" : "false");

        const limitReached = processedItems.length >= maxFiles;
        addButton.disabled = isProcessing || limitReached;
        addButton.setAttribute("aria-disabled", addButton.disabled ? "true" : "false");
        addButton.title = limitReached ? `Ai atins limita de ${maxFiles} fotografii.` : "";
    }

    function renderPreviewCards(items) {
        clearElement(previewGrid);
        revokePreviewUrls();

        items.forEach((item, index) => {
            previewUrls.push(item.previewUrl);

            const card = document.createElement("article");
            card.className = "photo-preview-card";
            card.setAttribute("role", "listitem");

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

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "ghost-button photo-preview-remove";
            removeButton.textContent = "Șterge fotografia";
            removeButton.setAttribute("aria-label", `Șterge fotografia ${item.file.name} din formular`);
            removeButton.addEventListener("click", () => {
                processedItems = processedItems.filter((_, candidateIndex) => candidateIndex !== index);
                syncProcessedFiles();
                renderPreviewCards(processedItems);
                setErrors([]);

                if (processedItems.length === 0) {
                    processingStatusInput.value = "no-files";
                    setStatus("Toate fotografiile au fost eliminate din formular.", "info");
                    updateActionState();
                    return;
                }

                processingStatusInput.value = readyStatus;
                setStatus(
                    `Fotografia ${item.file.name} a fost eliminată. ${formatPreparedPhotoCount(processedItems.length)}`,
                    "info"
                );
                updateActionState();
            });

            meta.appendChild(title);
            meta.appendChild(detail);
            card.appendChild(image);
            card.appendChild(meta);
            card.appendChild(removeButton);
            previewGrid.appendChild(card);
        });
    }

    function resetUploadState() {
        processedItems = [];
        processingStatusInput.value = "no-files";
        syncProcessedFiles();
        pickerInput.value = "";
        setErrors([]);
        clearElement(previewGrid);
        revokePreviewUrls();
        setStatus("Fotografiile vor fi procesate local în browser înainte de trimitere.", "info");
    }

    resetUploadState();
    updateActionState();

    addButton.addEventListener("click", () => {
        if (addButton.disabled) {
            return;
        }

        pickerInput.click();
    });

    pickerInput.addEventListener("change", async () => {
        const selectedFiles = Array.from(pickerInput.files || []);
        pickerInput.value = "";

        if (selectedFiles.length === 0) {
            return;
        }

        setErrors([]);

        if ((processedItems.length + selectedFiles.length) > maxFiles) {
            processingStatusInput.value = processedItems.length > 0 ? readyStatus : "error";
            setErrors([`Poți selecta maximum ${maxFiles} fotografii per sesizare.`]);
            setStatus(
                processedItems.length > 0
                    ? `Selecția nouă a fost respinsă deoarece ar depăși limita de ${maxFiles} fotografii. Fotografiile deja adăugate au fost păstrate.`
                    : `Selecția a fost respinsă deoarece depășește limita de ${maxFiles} fotografii.`,
                "error"
            );
            updateActionState();
            return;
        }

        if (!supportsClientPhotoProcessing()) {
            processingStatusInput.value = processedItems.length > 0 ? readyStatus : "unsupported";
            setErrors([
                "Browserul curent nu suportă procesarea locală a fotografiilor. Poți trimite sesizarea fără poze.",
            ]);
            setStatus(
                processedItems.length > 0
                    ? "Fotografiile noi nu au putut fi procesate în browser. Fotografiile deja adăugate au fost păstrate."
                    : "Procesarea foto nu este suportată în acest browser.",
                "error"
            );
            updateActionState();
            return;
        }

        isProcessing = true;
        processingStatusInput.value = "processing";
        updateActionState();
        setStatus(
            selectedFiles.length === 1
                ? "Procesăm fotografia selectată..."
                : `Procesăm ${selectedFiles.length} fotografii selectate...`,
            "info"
        );

        try {
            const processedBatch = [];

            for (let index = 0; index < selectedFiles.length; index += 1) {
                setStatus(`Procesăm fotografia ${index + 1} din ${selectedFiles.length}...`, "info");
                const processed = await compressImageFile(selectedFiles[index], maxSizeBytes);
                processedBatch.push({
                    ...processed,
                    previewUrl: URL.createObjectURL(processed.file),
                });
            }

            processedItems = [...processedItems, ...processedBatch];
            syncProcessedFiles();
            processingStatusInput.value = readyStatus;
            setErrors([]);
            renderPreviewCards(processedItems);
            setStatus(
                `${
                    processedBatch.length === 1
                        ? `Fotografia ${processedBatch[0].file.name} a fost adăugată.`
                        : `${processedBatch.length} fotografii au fost adăugate.`
                } ${formatPreparedPhotoCount(processedItems.length)}${
                    processedItems.length >= maxFiles ? ` Ai atins limita de ${maxFiles} fotografii.` : ""
                }`,
                "success"
            );
        } catch (error) {
            processingStatusInput.value = processedItems.length > 0 ? readyStatus : "error";
            const errorMessage = error instanceof Error ? error.message : "Fotografiile nu au putut fi procesate.";
            setErrors([errorMessage]);
            setStatus(
                processedItems.length > 0
                    ? `${errorMessage} Fotografiile deja adăugate au fost păstrate.`
                    : "Fotografiile nu au putut fi procesate.",
                "error"
            );
        } finally {
            isProcessing = false;
            updateActionState();
        }
    });

    form.addEventListener("submit", (event) => {
        const selectedCount = processedItems.length;

        if (isProcessing) {
            event.preventDefault();
            setErrors(["Așteaptă finalizarea procesării fotografiilor înainte de trimitere."]);
            setStatus("Procesarea fotografiilor este în curs.", "error");
            return;
        }

        if (selectedCount > 0 && processingStatusInput.value !== readyStatus) {
            event.preventDefault();
            setErrors(["Fotografiile selectate nu au fost procesate corect. Reîncearcă selecția."]);
            setStatus("Fotografiile nu sunt pregătite pentru trimitere.", "error");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initAccessibilityControls();
    initAccessibilityFlyout();
    initAccessibleForms();
    initNotificationCounter();
    initPushSupport();
    initLocationPickerMap();
    initIncidentsMap();
    initDetailMap();
    initIncidentCategoryDepartmentSync();
    initFollowForms();
    initIncidentPhotoUpload();
});
