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

  const extraDates = form.querySelector("[data-extra-dates]");
  form.querySelector("[data-add-date]")?.addEventListener("click", () => {
    if (!extraDates) return;
    const entry = document.createElement("div");
    entry.className = "date-entry additional-date hours-only-field";
    entry.innerHTML = `
      <label class="field">
        <span>Otra fecha *</span>
        <input type="date" name="fecha" ${form.dataset.dateMin ? `min="${form.dataset.dateMin}"` : ""} ${form.dataset.dateMax ? `max="${form.dataset.dateMax}"` : ""} required>
      </label>
      <button class="ui-btn icon-btn danger-btn" type="button" aria-label="Quitar fecha" title="Quitar fecha">
        <i class="bi bi-trash"></i>
      </button>`;
    entry.querySelector("button").addEventListener("click", () => entry.remove());
    extraDates.appendChild(entry);
    entry.querySelector("input").focus();
  });

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

  const reimbursementInput = form.querySelector("[data-request-reimbursement]");
  const reimbursementHelp = form.querySelector("[data-reimbursement-help]");
  const francoInput = form.querySelector("[data-franco-check]");
  const francoHelp = form.querySelector("[data-franco-help]");
  const primaryDate = form.querySelector('input[name="fecha"]');
  const holidaysWithoutReturn = new Set(
    (form.dataset.holidaysNoReturn || "").split(",").filter(Boolean),
  );
  const holidays = new Set(
    (form.dataset.holidays || "").split(",").filter(Boolean),
  );
  const defaultReimbursementHelp = reimbursementHelp?.textContent || "";
  const defaultFrancoHelp = francoHelp?.textContent || "";
  const isSundaySat = () => {
    const convenio = (
      form.dataset.fixedConvenio
      || form.querySelector('select[name="usuario_id"]')?.selectedOptions[0]?.dataset.convenio
      || ""
    ).toUpperCase();
    const parts = (primaryDate?.value || "").split("-").map(Number);
    return convenio === "SAT" && parts.length === 3
      && new Date(parts[0], parts[1] - 1, parts[2]).getDay() === 0;
  };
  const updateReimbursementAvailability = (isWorkedDay) => {
    if (!reimbursementInput) return;
    const sundaySat = isSundaySat();
    const unavailable = holidaysWithoutReturn.has(primaryDate?.value || "") || sundaySat;
    reimbursementInput.disabled = !isWorkedDay || unavailable;
    if (unavailable) reimbursementInput.checked = false;
    reimbursementInput.closest(".check-field")?.classList.toggle(
      "disabled-option", unavailable,
    );
    if (reimbursementHelp) {
      reimbursementHelp.textContent = unavailable
        ? sundaySat
          ? "El trabajo en domingo no permite solicitar reintegro."
          : "Este feriado no genera devolución del día."
        : defaultReimbursementHelp;
    }
    if (francoInput) {
      francoInput.disabled = !isWorkedDay || sundaySat;
      if (sundaySat) francoInput.checked = false;
      francoInput.closest(".check-field")?.classList.toggle(
        "disabled-option", sundaySat,
      );
    }
    if (francoHelp) {
      francoHelp.textContent = sundaySat
        ? "Se registrará automáticamente como trabajo en domingo."
        : defaultFrancoHelp;
    }
  };

  const updateRecordType = () => {
    const recordType = form.querySelector('input[name="tipo_registro"]:checked')?.value;
    const isHours = recordType === "HORAS";
    const isWorkedDay = recordType === "DIA_TRABAJADO";
    const isOther = recordType === "OTRAS";
    const includesExtra = form.querySelector("[data-include-extra]")?.checked ?? false;
    const showsExtraTime = isHours;
    form.querySelectorAll(".hours-only-field").forEach((field) => {
      field.classList.toggle("hidden", !isHours);
      field.querySelectorAll("select, input, button").forEach((control) => {
        control.disabled = !isHours;
      });
    });
    form.querySelectorAll(".day-worked-only-field").forEach((field) => {
      field.classList.toggle("hidden", !isWorkedDay);
      field.querySelectorAll("select, input, button").forEach((control) => {
        control.disabled = !isWorkedDay;
      });
    });
    form.querySelectorAll(".associated-loads-field").forEach((field) => {
      const isAssociatedLoad = isHours || isWorkedDay;
      field.classList.toggle("hidden", !isAssociatedLoad);
      field.querySelectorAll("select, input, textarea, button").forEach((control) => {
        control.disabled = !isAssociatedLoad;
      });
    });
    form.querySelectorAll(".extra-time-fields").forEach((fields) => {
      fields.classList.toggle("hidden", !showsExtraTime);
      fields.querySelectorAll("select, input, button").forEach((control) => {
        control.disabled = !showsExtraTime;
      });
    });
    form.querySelectorAll(".other-only-field").forEach((field) => {
      field.classList.toggle("hidden", !isOther);
      field.querySelectorAll("select, input, button").forEach((control) => {
        control.disabled = !isOther;
      });
    });
    const workedExtraQuantity = form.querySelector('input[name="cantidad_horas_extra"]');
    if (workedExtraQuantity) workedExtraQuantity.disabled = !isWorkedDay || !includesExtra;
    form.querySelector(".worked-extra-quantity")?.classList.toggle(
      "hidden", !isWorkedDay || !includesExtra,
    );
    updateReimbursementAvailability(isWorkedDay);
    updateOtherQuantityMode();
    updateWorkedDayPreview();
  };
  const otherQuantity = form.querySelector("[data-other-quantity]");
  const exteriorQuantity = form.querySelector("[data-exterior-quantity]");
  const standardQuantity = form.querySelector("[data-standard-quantity]");
  const userSelect = form.querySelector('select[name="usuario_id"]');
  const otherTypeSelect = form.querySelector('select[name="tipo_otra_carga"]');
  const journeyStartInput = form.querySelector("[data-journey-start-time]");
  const journeyEndInput = form.querySelector("[data-journey-end-time]");
  const journeyStartDate = form.querySelector("[data-journey-start-date]");
  const journeyEndDate = form.querySelector("[data-journey-end-date]");
  const workedSummary = form.querySelector("[data-worked-summary]");
  const workedExtraQuestion = form.querySelector("[data-worked-extra-question]");
  const workedExtraRange = form.querySelector("[data-worked-extra-range]");
  const workedExtraQuantity = form.querySelector('input[name="cantidad_horas_extra"]');
  const localDate = (value) => {
    const [year, month, day] = (value || "").split("-").map(Number);
    return year && month && day ? new Date(year, month - 1, day) : null;
  };
  const isoLocalDate = (value) => [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, "0"),
    String(value.getDate()).padStart(2, "0"),
  ].join("-");
  const updateWorkedDayPreview = () => {
    if (!journeyStartInput || !journeyEndInput) return;
    const startDateValue = primaryDate?.value || "";
    if (journeyStartDate) journeyStartDate.value = startDateValue;
    const dateValue = localDate(startDateValue);
    if (!dateValue || !journeyStartInput.value || !journeyEndInput.value) return;
    const startMinutes = timeToMinutes(journeyStartInput.value);
    const endMinutes = timeToMinutes(journeyEndInput.value);
    const crossesMidnight = endMinutes < startMinutes;
    if (crossesMidnight) dateValue.setDate(dateValue.getDate() + 1);
    if (journeyEndDate) journeyEndDate.value = isoLocalDate(dateValue);
    if (endMinutes === startMinutes) {
      if (workedSummary) workedSummary.textContent = "La hora final debe ser distinta de la inicial.";
      if (workedExtraQuestion) workedExtraQuestion.textContent = "Elegí horas de inicio y finalización distintas.";
      return;
    }
    const totalMinutes = (endMinutes - startMinutes + 1440) % 1440;
    const totalHours = totalMinutes / 60;
    const convenio = currentConvention();
    const startDateObject = localDate(startDateValue);
    const touchesSunday = convenio === "SAT" && (
      startDateObject?.getDay() === 0 || (crossesMidnight && dateValue.getDay() === 0)
    );
    const isWorkedDay = form.querySelector('input[name="tipo_registro"]:checked')?.value === "DIA_TRABAJADO";
    const includeExtraInput = form.querySelector("[data-include-extra]");
    const extraChoice = form.querySelector(".worked-extra-choice");
    const shortFranco = !holidays.has(startDateValue)
      && !(convenio === "SAT" && startDateObject?.getDay() === 0)
      && totalHours < 4;
    updateReimbursementAvailability(isWorkedDay);
    if (shortFranco) {
      if (includeExtraInput) {
        includeExtraInput.checked = false;
        includeExtraInput.disabled = true;
      }
      extraChoice?.classList.add("hidden");
      if (workedExtraQuantity) workedExtraQuantity.disabled = true;
      form.querySelector(".worked-extra-quantity")?.classList.add("hidden");
      if (reimbursementInput) {
        reimbursementInput.checked = false;
        reimbursementInput.disabled = true;
        reimbursementInput.closest(".check-field")?.classList.add("disabled-option");
      }
      if (reimbursementHelp) {
        reimbursementHelp.textContent = "Con menos de 4 horas se cargan horas extras al 100%; no corresponde reintegro del día.";
      }
    } else {
      if (includeExtraInput) includeExtraInput.disabled = !isWorkedDay;
      extraChoice?.classList.toggle("hidden", !isWorkedDay);
    }
    const dayLabel = shortFranco
      ? `${totalHours.toLocaleString("es-AR")} h extras al 100% por franco`
      : holidays.has(startDateValue) ? "Feriado trabajado" : "Franco trabajado";
    if (workedSummary) {
      workedSummary.innerHTML = `
        <span><i class="bi bi-calendar-check"></i> ${dayLabel}</span>
        <span><i class="bi bi-clock"></i> Horario informado: ${totalHours.toLocaleString("es-AR")} h</span>
        <span><i class="bi bi-moon-stars"></i> Las horas nocturnas se calcularán según el convenio</span>
        ${shortFranco ? '<span><i class="bi bi-cup-hot"></i> Comida y merienda se calcularán sobre estas horas extras</span>' : ""}
        ${touchesSunday ? '<span><i class="bi bi-calendar-week"></i> Domingo trabajado SAT</span>' : ""}`;
    }
    if (workedExtraQuestion && !shortFranco) {
      workedExtraQuestion.textContent = `El horario informado abarca ${totalHours.toLocaleString("es-AR")} horas. ¿Hiciste horas extras?`;
    }
    if (workedExtraQuantity) workedExtraQuantity.max = String(totalHours);
    if (workedExtraQuantity?.value && Number(workedExtraQuantity.value) > totalHours) {
      workedExtraQuantity.value = String(totalHours);
    }
    if (workedExtraRange && workedExtraQuantity) {
      const extraHours = Number(workedExtraQuantity.value);
      if (extraHours > 0) {
        const finishAbsolute = startMinutes + totalMinutes;
        workedExtraRange.textContent = `Se tomarán las últimas ${extraHours.toLocaleString("es-AR")} h del horario informado: ${formatTime(finishAbsolute - extraHours * 60)} a ${formatTime(finishAbsolute)}.`;
      } else {
        workedExtraRange.textContent = "Ingresá la cantidad; se tomará desde el final del horario informado.";
      }
    }
  };
  const suggestJourneyEnd = () => {
    if (!journeyStartInput?.value || !journeyEndInput) return;
    journeyEndInput.value = formatTime(timeToMinutes(journeyStartInput.value) + 60);
    syncTimeSelectFromHidden(journeyEndInput);
    updateWorkedDayPreview();
  };
  const mainConceptDescription = form.querySelector("[data-main-concept-description]");
  const updateMainConceptDescription = () => {
    if (!mainConceptDescription) return;
    mainConceptDescription.textContent = otherTypeSelect?.selectedOptions[0]?.dataset.description
      || "Seleccioná un concepto para ver qué representa.";
  };
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
    updateOtherQuantityMode();
    updateMainConceptDescription();
  };
  const updateOtherQuantityMode = () => {
    const isOther = form.querySelector('input[name="tipo_registro"]:checked')?.value === "OTRAS";
    const isExterior = (otherTypeSelect?.value || "").trim().toUpperCase() === "EXTERIOR PRENSA";
    standardQuantity?.classList.toggle("hidden", isExterior);
    exteriorQuantity?.classList.toggle("hidden", !isExterior);
    if (otherQuantity) otherQuantity.disabled = !isOther || isExterior;
    standardQuantity?.querySelectorAll("button").forEach((button) => {
      button.disabled = !isOther || isExterior;
    });
    if (exteriorQuantity) exteriorQuantity.disabled = !isOther || !isExterior;
  };
  const changeOtherQuantity = (delta) => {
    if (!otherQuantity) return;
    const nextValue = Math.max(0.5, (Number(otherQuantity.value) || 1) + delta);
    otherQuantity.value = String(Math.round(nextValue * 2) / 2);
  };
  form.querySelector("[data-other-quantity-down]")?.addEventListener("click", () => changeOtherQuantity(-0.5));
  form.querySelector("[data-other-quantity-up]")?.addEventListener("click", () => changeOtherQuantity(0.5));
  form.querySelector("[data-include-extra]")?.addEventListener("change", updateRecordType);
  form.querySelector("[data-franco-check]")?.addEventListener("change", updateRecordType);
  primaryDate?.addEventListener("change", updateRecordType);
  journeyStartInput?.addEventListener("change", suggestJourneyEnd);
  journeyEndInput?.addEventListener("change", updateWorkedDayPreview);
  workedExtraQuantity?.addEventListener("input", updateWorkedDayPreview);
  userSelect?.addEventListener("change", updateOtherTypes);
  otherTypeSelect?.addEventListener("change", () => {
    updateOtherQuantityMode();
    updateMainConceptDescription();
  });

  const conceptSection = form.querySelector("[data-additional-concepts]");
  const conceptRows = conceptSection?.querySelector("[data-concept-rows]");
  const conceptTemplate = conceptSection?.querySelector("[data-concept-template]");
  const currentConvention = () => (
    form.dataset.fixedConvenio
    || userSelect?.selectedOptions[0]?.dataset.convenio
    || ""
  ).toUpperCase();
  const configureConceptRow = (row) => {
    const typeSelect = row.querySelector('select[name="concepto_adicional_tipo"]');
    const quantityInput = row.querySelector('input[name="concepto_adicional_cantidad"]');
    const exteriorSelect = row.querySelector("[data-additional-exterior-quantity]");
    const description = row.querySelector("[data-concept-description]");
    const filterOptions = () => {
      const convenio = currentConvention();
      Array.from(typeSelect.options).forEach((option) => {
        if (!option.dataset.convenio) return;
        const allowed = option.dataset.convenio.toUpperCase() === convenio;
        option.hidden = !allowed;
        option.disabled = !allowed;
        if (!allowed && option.selected) typeSelect.value = "";
      });
    };
    const updateRow = () => {
      const option = typeSelect.selectedOptions[0];
      description.textContent = option?.dataset.description
        || "Seleccioná un concepto para ver qué representa.";
      const exterior = (typeSelect.value || "").trim().toUpperCase() === "EXTERIOR PRENSA";
      quantityInput.classList.toggle("hidden", exterior);
      quantityInput.disabled = exterior;
      if (exterior) quantityInput.removeAttribute("name");
      else quantityInput.name = "concepto_adicional_cantidad";
      exteriorSelect.classList.toggle("hidden", !exterior);
      exteriorSelect.disabled = !exterior;
      if (exterior) exteriorSelect.name = "concepto_adicional_cantidad";
      else exteriorSelect.removeAttribute("name");
    };
    typeSelect.addEventListener("change", updateRow);
    row.querySelector("[data-remove-concept]")?.addEventListener("click", () => row.remove());
    filterOptions();
    updateRow();
    row._filterConceptOptions = filterOptions;
  };
  conceptSection?.querySelector("[data-add-concept]")?.addEventListener("click", () => {
    if (!conceptRows || !conceptTemplate) return;
    const row = conceptTemplate.content.firstElementChild.cloneNode(true);
    conceptRows.appendChild(row);
    configureConceptRow(row);
    row.querySelector("select")?.focus();
  });
  userSelect?.addEventListener("change", () => {
    conceptRows?.querySelectorAll(".additional-concept-row").forEach((row) => {
      row._filterConceptOptions?.();
    });
  });
  form.querySelectorAll('input[name="tipo_registro"]').forEach((radio) => {
    radio.addEventListener("change", updateRecordType);
  });
  updateRecordType();
  updateOtherTypes();
});
