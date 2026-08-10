const themeButton = document.querySelector("#theme-toggle");

function updateThemeIcon() {
  if (!themeButton) return;
  const dark = document.documentElement.dataset.theme === "dark";
  themeButton.innerHTML = `<i class="bi ${dark ? "bi-sun-fill" : "bi-moon-stars-fill"}"></i>`;
}

themeButton?.addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme !== "dark";
  if (dark) document.documentElement.dataset.theme = "dark";
  else delete document.documentElement.dataset.theme;
  localStorage.setItem("app_theme", dark ? "dark" : "light");
  updateThemeIcon();
});

updateThemeIcon();

const addRequestPanel = document.querySelector("#add-request-panel");
document.querySelector("#show-add-request")?.addEventListener("click", () => {
  addRequestPanel?.classList.remove("hidden");
  addRequestPanel?.scrollIntoView({ behavior: "smooth", block: "start" });
});
document.querySelector("#hide-add-request")?.addEventListener("click", () => {
  addRequestPanel?.classList.add("hidden");
});

document.querySelectorAll(".reintegro-select").forEach((select) => {
  select.addEventListener("change", () => {
    const index = select.dataset.reintegroIndex;
    document.querySelectorAll(`input[name="reintegros"][data-reintegro-index="${index}"]`).forEach((input) => {
      input.value = select.value;
    });
  });
});

function updateDraftCount() {
  const count = document.querySelectorAll("[data-draft-row]").length;
  const countChip = document.querySelector("#draft-count");
  const actionCount = document.querySelector("#draft-action-count");
  const confirmButton = document.querySelector("#confirm-batch-form button");
  if (countChip) countChip.textContent = String(count);
  if (actionCount) actionCount.textContent = String(count);
  if (confirmButton) confirmButton.disabled = count === 0;
}

document.querySelectorAll(".remove-draft").forEach((button) => {
  button.addEventListener("click", () => {
    const index = button.dataset.draftIndex;
    document.querySelectorAll(`[data-draft-index="${index}"]`).forEach((item) => item.remove());
    updateDraftCount();
  });
});

const draftPage = document.querySelector(".draft-table");
let allowDraftNavigation = false;
const hasPendingDrafts = () => document.querySelectorAll("[data-draft-row]").length > 0;

if (draftPage) {
  document.querySelector("#add-request-form")?.addEventListener("submit", () => {
    allowDraftNavigation = true;
  });
  document.querySelector("#confirm-batch-form")?.addEventListener("submit", () => {
    allowDraftNavigation = true;
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link || allowDraftNavigation || !hasPendingDrafts()) return;
    const confirmed = window.confirm(
      "Tenés cargas sin procesar. Si salís de esta página, se perderán. ¿Querés salir igualmente?"
    );
    if (!confirmed) event.preventDefault();
    else allowDraftNavigation = true;
  });

  window.addEventListener("beforeunload", (event) => {
    if (allowDraftNavigation || !hasPendingDrafts()) return;
    event.preventDefault();
    event.returnValue = "";
  });

  window.addEventListener("pageshow", () => {
    allowDraftNavigation = false;
  });
}

const hourCheckboxes = [...document.querySelectorAll(".hour-checkbox")];
const selectAllHours = document.querySelector("#select-all-hours");
const authorizeButton = document.querySelector("#authorize-selected");
const rejectButton = document.querySelector("#reject-selected");
const selectedCount = document.querySelector("#selected-count");

function updateAuthorizationSelection() {
  const checked = hourCheckboxes.filter((item) => item.checked).length;
  if (selectedCount) selectedCount.textContent = checked;
  if (authorizeButton) authorizeButton.disabled = checked === 0;
  if (rejectButton) rejectButton.disabled = checked === 0;
  if (selectAllHours) {
    selectAllHours.checked = checked > 0 && checked === hourCheckboxes.length;
    selectAllHours.indeterminate = checked > 0 && checked < hourCheckboxes.length;
  }
  document.querySelectorAll(".select-user-hours").forEach((control) => {
    const userItems = hourCheckboxes.filter((item) => item.dataset.userId === control.dataset.userId);
    const userChecked = userItems.filter((item) => item.checked).length;
    control.checked = userChecked > 0 && userChecked === userItems.length;
    control.indeterminate = userChecked > 0 && userChecked < userItems.length;
  });
}

selectAllHours?.addEventListener("change", () => {
  hourCheckboxes.forEach((item) => { item.checked = selectAllHours.checked; });
  updateAuthorizationSelection();
});
document.querySelectorAll(".select-user-hours").forEach((control) => {
  control.addEventListener("change", () => {
    hourCheckboxes
      .filter((item) => item.dataset.userId === control.dataset.userId)
      .forEach((item) => { item.checked = control.checked; });
    updateAuthorizationSelection();
  });
});
hourCheckboxes.forEach((item) => item.addEventListener("change", updateAuthorizationSelection));

function syncTimeSelectFromHidden(input) {
  const control = input?.closest("[data-time-select]");
  if (!control || !input.value) return;
  const [hour, minute] = input.value.split(":");
  control.querySelector("[data-time-hour]").value = hour;
  control.querySelector("[data-time-minute]").value = minute;
}

document.querySelectorAll("[data-time-select]").forEach((control) => {
  const hourSelect = control.querySelector("[data-time-hour]");
  const minuteSelect = control.querySelector("[data-time-minute]");
  const hiddenInput = control.querySelector('input[type="hidden"]');
  const updateHiddenTime = () => {
    hiddenInput.value = hourSelect.value && minuteSelect.value
      ? `${hourSelect.value}:${minuteSelect.value}`
      : "";
    hiddenInput.dispatchEvent(new Event("change"));
  };
  hourSelect.addEventListener("change", updateHiddenTime);
  minuteSelect.addEventListener("change", updateHiddenTime);
  syncTimeSelectFromHidden(hiddenInput);
});

document.querySelectorAll(".request-form").forEach((form) => {
  const startInput = form.querySelector("[data-start-time]");
  const endInput = form.querySelector("[data-end-time]");
  const durationInput = form.querySelector("[data-duration-hours]");
  if (!startInput || !endInput || !durationInput) return;

  const clampDuration = (value) => Math.min(16, Math.max(0.5, value));
  const timeToMinutes = (value) => {
    const [hours, minutes] = value.split(":").map(Number);
    return hours * 60 + minutes;
  };
  const formatTime = (minutes) => {
    const normalized = ((minutes % 1440) + 1440) % 1440;
    return `${String(Math.floor(normalized / 60)).padStart(2, "0")}:${String(normalized % 60).padStart(2, "0")}`;
  };
  const updateEndTime = () => {
    if (!startInput.value) return;
    const duration = clampDuration(Number(durationInput.value) || 1);
    durationInput.value = String(duration);
    endInput.value = formatTime(timeToMinutes(startInput.value) + Math.round(duration * 60));
    syncTimeSelectFromHidden(endInput);
  };
  const changeDuration = (delta) => {
    durationInput.value = String(clampDuration((Number(durationInput.value) || 1) + delta));
    updateEndTime();
  };

  form.querySelector("[data-duration-down]")?.addEventListener("click", () => changeDuration(-0.5));
  form.querySelector("[data-duration-up]")?.addEventListener("click", () => changeDuration(0.5));
  startInput.addEventListener("change", updateEndTime);
  endInput.addEventListener("change", () => {
    if (!startInput.value || !endInput.value) return;
    let minutes = timeToMinutes(endInput.value) - timeToMinutes(startInput.value);
    if (minutes <= 0) minutes += 1440;
    const hours = minutes / 60;
    if (hours >= 0.5 && hours <= 16) durationInput.value = String(Math.round(hours * 2) / 2);
  });

  const updateRecordType = () => {
    const recordType = form.querySelector('input[name="tipo_registro"]:checked')?.value;
    const isHours = recordType === "HORAS";
    const isOther = recordType === "OTRAS";
    form.querySelectorAll(".hours-only-field").forEach((field) => {
      field.classList.toggle("hidden", !isHours);
      field.querySelectorAll("select, input, button").forEach((control) => {
        control.disabled = !isHours;
      });
    });
    form.querySelectorAll(".other-only-field").forEach((field) => {
      field.classList.toggle("hidden", !isOther);
      field.querySelectorAll("select, input, button").forEach((control) => {
        control.disabled = !isOther;
      });
    });
  };
  const otherQuantity = form.querySelector("[data-other-quantity]");
  const userSelect = form.querySelector('select[name="usuario_id"]');
  const otherTypeSelect = form.querySelector('select[name="tipo_otra_carga"]');
  const updateOtherTypes = () => {
    if (!otherTypeSelect) return;
    const convenio = (
      form.dataset.fixedConvenio
      || userSelect?.selectedOptions[0]?.dataset.convenio
      || ""
    ).toUpperCase();
    Array.from(otherTypeSelect.options).forEach((option) => {
      if (!option.dataset.convenio) return;
      const isAllowed = option.dataset.convenio.toUpperCase() === convenio;
      option.hidden = !isAllowed;
      option.disabled = !isAllowed;
      if (!isAllowed && option.selected) otherTypeSelect.value = "";
    });
  };
  const changeOtherQuantity = (delta) => {
    if (!otherQuantity) return;
    const nextValue = Math.max(0.01, (Number(otherQuantity.value) || 1) + delta);
    otherQuantity.value = String(Math.round(nextValue * 100) / 100);
  };
  form.querySelector("[data-other-quantity-down]")?.addEventListener("click", () => changeOtherQuantity(-1));
  form.querySelector("[data-other-quantity-up]")?.addEventListener("click", () => changeOtherQuantity(1));
  userSelect?.addEventListener("change", updateOtherTypes);
  form.querySelectorAll('input[name="tipo_registro"]').forEach((radio) => {
    radio.addEventListener("change", updateRecordType);
  });
  updateRecordType();
  updateOtherTypes();
});
