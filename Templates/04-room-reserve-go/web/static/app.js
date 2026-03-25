async function refreshSlots() {
  const roomSelect = document.querySelector("#room-select");
  const dateInput = document.querySelector("#date-input");
  const slotSelect = document.querySelector("#slot-select");

  if (!roomSelect || !dateInput || !slotSelect) {
    return;
  }

  if (!roomSelect.value || !dateInput.value) {
    return;
  }

  const response = await fetch(`/api/slots?room_id=${roomSelect.value}&date=${dateInput.value}`);
  if (!response.ok) {
    return;
  }

  const slots = await response.json();
  slotSelect.innerHTML = "";

  slots.forEach((slot) => {
    const option = document.createElement("option");
    option.value = slot.ID;
    option.textContent = `${slot.StartTime} - ${slot.EndTime}`;
    slotSelect.appendChild(option);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const roomSelect = document.querySelector("#room-select");
  const dateInput = document.querySelector("#date-input");

  if (roomSelect) {
    roomSelect.addEventListener("change", refreshSlots);
  }

  if (dateInput) {
    dateInput.addEventListener("change", refreshSlots);
  }
});

