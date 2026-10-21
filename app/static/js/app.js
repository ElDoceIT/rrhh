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

document.querySelectorAll("[data-multi-check]").forEach((dropdown) => {
  const summary = dropdown.querySelector("[data-multi-check-summary]");
  const inputs = Array.from(dropdown.querySelectorAll('input[type="checkbox"]'));
  const updateSummary = () => {
    const checked = inputs.filter((input) => input.checked);
    if (!summary) return;
    summary.textContent = checked.length === 0
      ? summary.dataset.emptyLabel
      : checked.length === 1
        ? checked[0].nextElementSibling?.textContent.trim()
        : `${checked.length} opciones seleccionadas`;
  };
  inputs.forEach((input) => input.addEventListener("change", updateSummary));
  updateSummary();
});

document.addEventListener("click", (event) => {
  document.querySelectorAll("[data-multi-check][open]").forEach((dropdown) => {
    if (!dropdown.contains(event.target)) dropdown.removeAttribute("open");
  });
});

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

function updateAutomaticDraftRows() {
  document.querySelectorAll("[data-auto-row]").forEach((row) => {
    const key = row.dataset.autoKey;
    const isNocturnal = row.dataset.autoMode === "NOCTURNIDAD";
    const sources = Array.from(document.querySelectorAll(
      isNocturnal ? "[data-night-source]" : "[data-auto-source]",
    )).filter((source) => (
      isNocturnal ? source.dataset.nightKey : source.dataset.autoKey
    ) === key);
    const draftHours = sources.reduce(
      (total, source) => total + Number(
        isNocturnal ? source.dataset.nightHours || 0 : source.dataset.autoHours || 0,
      ), 0,
    );
    const baseHours = Number(row.dataset.autoBaseHours || 0);
    const divisor = Number(row.dataset.autoDivisor || 1);
    const quantity = isNocturnal
      ? baseHours + draftHours
      : Math.floor((baseHours + draftHours) / divisor);
    row.classList.toggle("hidden", draftHours <= 0 || quantity <= 0);
    const quantityElement = row.querySelector("[data-auto-quantity]");
    if (quantityElement) quantityElement.textContent = isNocturnal
      ? quantity.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : String(quantity);
    const observation = row.querySelector("[data-auto-observation]");
    if (observation) {
      observation.textContent = `Cálculo automático sobre ${(baseHours + draftHours).toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} horas ${isNocturnal ? "nocturnas" : "extras"}.`;
    }
  });
}

function updateDraftCount() {
  const sourceCount = document.querySelectorAll("[data-draft-row]").length;
  const automaticCount = Array.from(document.querySelectorAll("[data-auto-row]"))
    .filter((row) => !row.classList.contains("hidden")).length;
  const count = sourceCount + automaticCount;
  const countChip = document.querySelector("#draft-count");
  const actionCount = document.querySelector("#draft-action-count");
  const confirmButton = document.querySelector("#confirm-batch-form button");
  if (countChip) countChip.textContent = String(count);
  if (actionCount) actionCount.textContent = String(count);
  if (confirmButton) confirmButton.disabled = sourceCount === 0;
}

document.querySelectorAll(".remove-draft").forEach((button) => {
  button.addEventListener("click", () => {
    const index = button.dataset.draftIndex;
    document.querySelectorAll(`[data-draft-index="${index}"]`).forEach((item) => item.remove());
    updateAutomaticDraftRows();
    updateDraftCount();
  });
});

updateAutomaticDraftRows();
updateDraftCount();

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

const authorizationGroups = [...document.querySelectorAll("[data-authorization-group]")];
function setAuthorizationGroupExpanded(group, expanded) {
  group.classList.toggle("is-collapsed", !expanded);
  const button = group.querySelector(".authorization-group-toggle");
  if (button) {
    button.setAttribute("aria-expanded", String(expanded));
    button.setAttribute("aria-label", `${expanded ? "Comprimir" : "Desplegar"} cargas del usuario`);
  }
}
authorizationGroups.forEach((group) => {
  group.querySelector(".authorization-group-toggle")?.addEventListener("click", () => {
    setAuthorizationGroupExpanded(group, group.classList.contains("is-collapsed"));
  });
});
document.querySelector("#expand-all-users")?.addEventListener("click", () => {
  authorizationGroups.forEach((group) => setAuthorizationGroupExpanded(group, true));
});
document.querySelector("#collapse-all-users")?.addEventListener("click", () => {
  authorizationGroups.forEach((group) => setAuthorizationGroupExpanded(group, false));
});

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
    entry.className = "date-entry additional-date multi-load-date-field";
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
  const standardReimbursementField = form.querySelector("[data-standard-reimbursement-field]");
  const cisprenReimbursementField = form.querySelector("[data-cispren-reimbursement-field]");
  const cisprenReimbursement = form.querySelector("[data-cispren-reimbursement]");
  const cisprenReimbursementHelp = form.querySelector("[data-cispren-reimbursement-help]");
  const compensatoryDateField = form.querySelector("[data-compensatory-date-field]");
  const compensatoryDateInput = compensatoryDateField?.querySelector('input[name="fecha_descanso_compensatorio"]');
  const francoInput = form.querySelector("[data-franco-check]");
  const francoHelp = form.querySelector("[data-franco-help]");
  const primaryDate = form.querySelector('input[name="fecha"]');
  const holidaysWithoutReturn = new Set(
    (form.dataset.holidaysNoReturn || "").split(",").filter(Boolean),
  );
  const holidays = new Set(
    (form.dataset.holidays || "").split(",").filter(Boolean),
  );
  const defaultReimbursementHelp = "Si no lo solicitás, indicá qué día vas a tomar.";
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
    const sundaySat = isSundaySat();
    const unavailable = holidaysWithoutReturn.has(primaryDate?.value || "") || sundaySat;
    const isCispren = currentConvention() === "CISPREN";
    const isFc = currentConvention() === "FC";
    const isMonotributista = currentConvention() === "MONOTRIBUTISTA";
    const noReimbursement = isFc || isMonotributista;
    standardReimbursementField?.classList.toggle("hidden", isCispren || noReimbursement);
    cisprenReimbursementField?.classList.toggle("hidden", !isCispren);
    if (reimbursementInput) {
      reimbursementInput.disabled = !isWorkedDay || unavailable || isCispren || noReimbursement;
      if (unavailable || isCispren || noReimbursement) reimbursementInput.checked = false;
      reimbursementInput.closest(".check-field")?.classList.toggle(
        "disabled-option", unavailable,
      );
    }
    if (cisprenReimbursement) {
      cisprenReimbursement.disabled = !isWorkedDay || unavailable || !isCispren;
      if (unavailable || !isCispren) cisprenReimbursement.value = "NO";
    }
    if (reimbursementHelp) {
      reimbursementHelp.textContent = unavailable
        ? sundaySat
          ? "El trabajo en domingo no permite solicitar reintegro."
          : "Este feriado no genera devolución del día."
        : defaultReimbursementHelp;
    }
    if (cisprenReimbursementHelp) {
      cisprenReimbursementHelp.textContent = unavailable
        ? sundaySat
          ? "El trabajo en domingo no permite solicitar reintegro."
          : "Este feriado no genera devolución del día."
        : "Elegí medio reintegro, reintegro completo o no solicitar.";
    }
    const requestsReimbursement = isCispren
      ? cisprenReimbursement?.value !== "NO"
      : Boolean(reimbursementInput?.checked);
    const asksCompensatoryDate = isWorkedDay
      && !unavailable && !noReimbursement && !requestsReimbursement;
    compensatoryDateField?.classList.toggle("hidden", !asksCompensatoryDate);
    if (compensatoryDateInput) {
      compensatoryDateInput.disabled = !asksCompensatoryDate;
      compensatoryDateInput.required = asksCompensatoryDate;
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
    form.querySelector("[data-request-details]")?.classList.toggle("hidden", !recordType);
    const isHours = recordType === "HORAS";
    const isWorkedDay = recordType === "DIA_TRABAJADO";
    const isOther = recordType === "OTRAS";
    const isNocturnalJourney = isOther
      && (otherTypeSelect?.value || "").trim().toUpperCase() === "NOCTURNAS EN JORNADA";
    const isDailyOther = isOther
      && otherTypeSelect?.selectedOptions[0]?.dataset.loadMode === "CARGA_POR_DIA";
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
      const isAssociatedLoad = (isHours || isWorkedDay) && currentConvention() !== "FC";
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
    const allowMultipleDates = isHours || isNocturnalJourney || isDailyOther;
    form.querySelector("[data-add-date]")?.classList.toggle("hidden", !allowMultipleDates);
    form.querySelector("[data-multi-date-help]")?.classList.toggle("hidden", !allowMultipleDates);
    form.querySelectorAll(".multi-load-date-field").forEach((field) => {
      field.classList.toggle("hidden", !allowMultipleDates);
      field.querySelectorAll("input, button").forEach((control) => {
        control.disabled = !allowMultipleDates;
      });
    });
    const workedExtraQuantity = form.querySelector('input[name="cantidad_horas_extra"]');
    if (workedExtraQuantity) workedExtraQuantity.disabled = !isWorkedDay || !includesExtra;
    form.querySelector(".worked-extra-quantity")?.classList.toggle(
      "hidden", !isWorkedDay || !includesExtra,
    );
    updateReimbursementAvailability(isWorkedDay);
    updateOtherQuantityMode();
    updateDateSelectionMode();
    const articleAvailable = isHours && form.dataset.hsArticulo === "true";
    hoursArticle?.classList.toggle("hidden", !articleAvailable);
    setHoursArticleEnabled(
      articleAvailable
      && hoursArticle?.querySelector("[data-article-enabled]")?.value === "SI",
    );
    updateWorkedDayPreview();
  };
  const otherQuantity = form.querySelector("[data-other-quantity]");
  const exteriorQuantity = form.querySelector("[data-exterior-quantity]");
  const standardQuantity = form.querySelector("[data-standard-quantity]");
  const otherQuantityField = form.querySelector("[data-other-quantity-field]");
  const nocturnalFields = form.querySelector("[data-other-nocturnal-fields]");
  const nocturnalStart = nocturnalFields?.querySelector('input[name="jornada_nocturna_inicio"]');
  const nocturnalEnd = nocturnalFields?.querySelector('input[name="jornada_nocturna_fin"]');
  const nocturnalPreview = nocturnalFields?.querySelector("[data-nocturnal-preview]");
  const dateMode = form.querySelector("[data-date-mode]");
  const datePeriod = form.querySelector("[data-date-period]");
  const specificDates = form.querySelector("[data-specific-dates]");
  const hoursArticle = form.querySelector("[data-article-hours-calculator]");
  const otherArticle = form.querySelector("[data-article-other-calculator]");
  const mainObservations = form.querySelector("[data-main-observations]");
  const userSelect = form.querySelector('select[name="usuario_id"]');
  const otherTypeSelect = form.querySelector('select[name="tipo_otra_carga"]');
  const journeyStartInput = form.querySelector("[data-journey-start-time]");
  const journeyEndInput = form.querySelector("[data-journey-end-time]");
  const journeyStartDate = form.querySelector("[data-journey-start-date]");
  const journeyEndDate = form.querySelector("[data-journey-end-date]");
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
      if (workedExtraQuestion) workedExtraQuestion.textContent = "Elegí horas de inicio y finalización distintas.";
      return;
    }
    const totalMinutes = (endMinutes - startMinutes + 1440) % 1440;
    const totalHours = totalMinutes / 60;
    const convenio = currentConvention();
    const startDateObject = localDate(startDateValue);
    const isWorkedDay = form.querySelector('input[name="tipo_registro"]:checked')?.value === "DIA_TRABAJADO";
    const includeExtraInput = form.querySelector("[data-include-extra]");
    const extraChoice = form.querySelector(".worked-extra-choice");
    const noMinimumWorkedDay = convenio === "FC" || convenio === "MONOTRIBUTISTA";
    const shortWorkedDay = !noMinimumWorkedDay
      && !(convenio === "SAT" && startDateObject?.getDay() === 0)
      && totalHours < 4;
    updateReimbursementAvailability(isWorkedDay);
    const canIncludeExtra = isWorkedDay && !shortWorkedDay;
    if (includeExtraInput) {
      includeExtraInput.disabled = !canIncludeExtra;
      if (!canIncludeExtra) {
        includeExtraInput.checked = false;
        form.querySelector(".worked-extra-quantity")?.classList.add("hidden");
      }
    }
    extraChoice?.classList.toggle("hidden", !canIncludeExtra);
    if (!canIncludeExtra) {
      if (workedExtraQuantity) workedExtraQuantity.disabled = true;
      form.querySelector(".worked-extra-quantity")?.classList.add("hidden");
    }
    if (shortWorkedDay) {
      if (reimbursementInput) {
        reimbursementInput.checked = false;
        reimbursementInput.disabled = true;
        reimbursementInput.closest(".check-field")?.classList.add("disabled-option");
      }
      if (cisprenReimbursement) {
        cisprenReimbursement.value = "NO";
        cisprenReimbursement.disabled = true;
      }
      compensatoryDateField?.classList.add("hidden");
      if (compensatoryDateInput) {
        compensatoryDateInput.disabled = true;
        compensatoryDateInput.required = false;
      }
    } else {
      updateReimbursementAvailability(isWorkedDay);
    }
    if (workedExtraQuestion && !shortWorkedDay) {
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
  reimbursementInput?.addEventListener("change", () => updateReimbursementAvailability(true));
  cisprenReimbursement?.addEventListener("change", () => updateReimbursementAvailability(true));
  const suggestJourneyEnd = () => {
    if (!journeyStartInput?.value || !journeyEndInput) return;
    journeyEndInput.value = formatTime(timeToMinutes(journeyStartInput.value) + 60);
    syncTimeSelectFromHidden(journeyEndInput);
    updateWorkedDayPreview();
  };
  const mainConceptDescription = form.querySelector("[data-main-concept-description]");
  const updateMainConceptDescription = () => {
    if (!mainConceptDescription) return;
    const selected = otherTypeSelect?.selectedOptions[0];
    const description = selected?.dataset.description
      || "Seleccioná un concepto para ver qué representa.";
    const dailyQuantity = selected?.dataset.loadMode === "CARGA_POR_DIA"
      ? ` Se cargará ${Number(selected.dataset.defaultQuantity).toLocaleString("es-AR")} por cada fecha.`
      : "";
    mainConceptDescription.textContent = description + dailyQuantity;
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
    const isArticle = (otherTypeSelect?.value || "").trim().toUpperCase() === "HS ARTICULO";
    const isNocturnalJourney = (otherTypeSelect?.value || "").trim().toUpperCase() === "NOCTURNAS EN JORNADA";
    const isDailyOther = otherTypeSelect?.selectedOptions[0]?.dataset.loadMode === "CARGA_POR_DIA";
    otherQuantityField?.classList.toggle("hidden", !isOther || isArticle || isNocturnalJourney || isDailyOther);
    standardQuantity?.classList.toggle("hidden", isExterior);
    exteriorQuantity?.classList.toggle("hidden", !isExterior);
    if (otherQuantity) otherQuantity.disabled = !isOther || isExterior || isArticle || isNocturnalJourney || isDailyOther;
    standardQuantity?.querySelectorAll("button").forEach((button) => {
      button.disabled = !isOther || isExterior || isArticle || isNocturnalJourney || isDailyOther;
    });
    if (exteriorQuantity) exteriorQuantity.disabled = !isOther || !isExterior || isArticle;
    nocturnalFields?.classList.toggle("hidden", !isOther || !isNocturnalJourney);
    nocturnalFields?.querySelectorAll("input, select").forEach((control) => {
      control.disabled = !isOther || !isNocturnalJourney;
      control.required = isOther && isNocturnalJourney;
    });
    otherArticle?.classList.toggle("hidden", !isOther || !isArticle);
    otherArticle?.querySelectorAll("input, select").forEach((input) => {
      input.disabled = !isOther || !isArticle;
      if (!input.matches('input[type="hidden"]')) input.required = isOther && isArticle;
    });
    const allowMultipleDates = form.querySelector('input[name="tipo_registro"]:checked')?.value === "HORAS"
      || (isOther && (isNocturnalJourney || isDailyOther));
    form.querySelector("[data-add-date]")?.classList.toggle("hidden", !allowMultipleDates);
    form.querySelector("[data-multi-date-help]")?.classList.toggle("hidden", !allowMultipleDates);
    form.querySelectorAll(".multi-load-date-field").forEach((field) => {
      field.classList.toggle("hidden", !allowMultipleDates);
      field.querySelectorAll("input, button").forEach((control) => {
        control.disabled = !allowMultipleDates;
      });
    });
    updateDateSelectionMode();
  };

  function updateDateSelectionMode() {
    const isHours = form.querySelector('input[name="tipo_registro"]:checked')?.value === "HORAS";
    const isNocturnalJourney = form.querySelector('input[name="tipo_registro"]:checked')?.value === "OTRAS"
      && (otherTypeSelect?.value || "").trim().toUpperCase() === "NOCTURNAS EN JORNADA";
    const isDailyOther = form.querySelector('input[name="tipo_registro"]:checked')?.value === "OTRAS"
      && otherTypeSelect?.selectedOptions[0]?.dataset.loadMode === "CARGA_POR_DIA";
    const isArticle = form.querySelector('input[name="tipo_registro"]:checked')?.value === "OTRAS"
      && (otherTypeSelect?.value || "").trim().toUpperCase() === "HS ARTICULO";
    const usesMode = isHours || isNocturnalJourney || isDailyOther;
    const mode = dateMode?.querySelector('input[name="modo_fechas"]:checked')?.value || "FECHAS";
    const usePeriod = usesMode && mode === "PERIODO";
    dateMode?.classList.toggle("hidden", !usesMode);
    dateMode?.querySelectorAll("input").forEach((input) => {
      input.disabled = !usesMode;
    });
    datePeriod?.classList.toggle("hidden", !usePeriod);
    datePeriod?.querySelectorAll("input").forEach((input) => {
      input.disabled = !usePeriod;
      input.required = usePeriod && input.type === "date";
    });
    if (specificDates) {
      specificDates.classList.toggle("hidden", usePeriod || isArticle);
      specificDates.querySelectorAll('input[name="fecha"]').forEach((input) => {
        input.disabled = usePeriod || isArticle;
        input.required = !usePeriod && !isArticle;
      });
    }
    const allowSpecificMultiple = usesMode && !usePeriod;
    form.querySelector("[data-add-date]")?.classList.toggle("hidden", !allowSpecificMultiple);
    form.querySelector("[data-multi-date-help]")?.classList.toggle("hidden", !allowSpecificMultiple);
    if (usePeriod) {
      const from = datePeriod?.querySelector('input[name="periodo_fecha_desde"]');
      const to = datePeriod?.querySelector('input[name="periodo_fecha_hasta"]');
      if (from && !from.value) from.value = form.dataset.dateMin || "";
      if (to && !to.value) to.value = form.dataset.dateMax || "";
    }
    updatePeriodPreview();
    updateNocturnalPreview();
  }

  function updatePeriodPreview() {
    const preview = datePeriod?.querySelector("[data-period-preview]");
    if (!preview || datePeriod?.classList.contains("hidden")) return;
    const fromValue = datePeriod.querySelector('input[name="periodo_fecha_desde"]')?.value;
    const toValue = datePeriod.querySelector('input[name="periodo_fecha_hasta"]')?.value;
    const weekdays = new Set(Array.from(
      datePeriod.querySelectorAll('input[name="periodo_dias_semana"]:checked'),
    ).map((input) => Number(input.value)));
    if (!fromValue || !toValue || !weekdays.size) {
      preview.textContent = "Completá el período y elegí al menos un día de la semana.";
      return;
    }
    const cursor = localDate(fromValue);
    const finish = localDate(toValue);
    if (!cursor || !finish || cursor > finish) {
      preview.textContent = "Revisá las fechas del período.";
      return;
    }
    const isNocturnalJourney = form.querySelector('input[name="tipo_registro"]:checked')?.value === "OTRAS"
      && (otherTypeSelect?.value || "").trim().toUpperCase() === "NOCTURNAS EN JORNADA";
    let valid = 0;
    let omittedHolidays = 0;
    while (cursor <= finish) {
      const iso = isoLocalDate(cursor);
      const pythonWeekday = (cursor.getDay() + 6) % 7;
      if (weekdays.has(pythonWeekday)) {
        if (isNocturnalJourney && holidays.has(iso)) omittedHolidays += 1;
        else valid += 1;
      }
      cursor.setDate(cursor.getDate() + 1);
    }
    const isDailyOther = form.querySelector('input[name="tipo_registro"]:checked')?.value === "OTRAS"
      && otherTypeSelect?.selectedOptions[0]?.dataset.loadMode === "CARGA_POR_DIA";
    const sharedData = isDailyOther
      ? "La misma cantidad configurada y observación se aplicarán a todas las fechas."
      : "El mismo horario y observación se aplicarán a todas las fechas.";
    preview.textContent = `Se generarán ${valid} registros${omittedHolidays ? ` y se omitirán ${omittedHolidays} feriados` : ""}. ${sharedData}`;
  }

  const overlapMinutes = (start, end, rangeStart, rangeEnd) => {
    const segments = (from, to) => from < to ? [[from, to]] : [[from, 1440], [0, to]];
    return segments(start, end).reduce((total, [a, b]) => total
      + segments(rangeStart, rangeEnd).reduce(
        (subtotal, [c, d]) => subtotal + Math.max(0, Math.min(b, d) - Math.max(a, c)), 0,
      ), 0);
  };
  function updateNocturnalPreview() {
    if (!nocturnalPreview || !nocturnalStart?.value || !nocturnalEnd?.value) return;
    if (nocturnalStart.value === nocturnalEnd.value) {
      nocturnalPreview.textContent = "La jornada no puede comenzar y finalizar a la misma hora.";
      return;
    }
    const rangeFrom = form.dataset.nocturnalFrom;
    const rangeTo = form.dataset.nocturnalTo;
    if (!rangeFrom || !rangeTo) {
      nocturnalPreview.textContent = "RRHH debe configurar una única franja nocturna para tu convenio.";
      return;
    }
    const quantity = overlapMinutes(
      timeToMinutes(nocturnalStart.value), timeToMinutes(nocturnalEnd.value),
      timeToMinutes(rangeFrom), timeToMinutes(rangeTo),
    ) / 60;
    const mode = dateMode?.querySelector('input[name="modo_fechas"]:checked')?.value || "FECHAS";
    let periodSummary = "";
    if (mode === "PERIODO") {
      const fromValue = datePeriod?.querySelector('input[name="periodo_fecha_desde"]')?.value;
      const toValue = datePeriod?.querySelector('input[name="periodo_fecha_hasta"]')?.value;
      const weekdays = new Set(Array.from(
        datePeriod?.querySelectorAll('input[name="periodo_dias_semana"]:checked') || [],
      ).map((input) => Number(input.value)));
      if (fromValue && toValue && weekdays.size) {
        const cursor = localDate(fromValue);
        const finish = localDate(toValue);
        let valid = 0;
        let omittedHolidays = 0;
        while (cursor && finish && cursor <= finish) {
          const iso = isoLocalDate(cursor);
          const pythonWeekday = (cursor.getDay() + 6) % 7;
          if (weekdays.has(pythonWeekday)) {
            if (holidays.has(iso)) omittedHolidays += 1;
            else valid += 1;
          }
          cursor.setDate(cursor.getDate() + 1);
        }
        periodSummary = ` Se generarán ${valid} registros${omittedHolidays ? ` y se omitirán ${omittedHolidays} feriados` : ""}.`;
      }
    }
    nocturnalPreview.textContent = quantity > 0
      ? `Se calcularán ${quantity.toLocaleString("es-AR")} horas nocturnas por jornada (franja ${rangeFrom} a ${rangeTo}).${periodSummary}`
      : `El horario no se superpone con la franja nocturna ${rangeFrom} a ${rangeTo}.`;
  }

  const updateArticleResult = (row) => {
    if (!row) return;
    const endDate = row.querySelector("[data-article-end-date]")?.value;
    const endTime = row.querySelector("[data-article-end-time]")?.value;
    const nextDate = row.querySelector("[data-article-next-date]")?.value;
    const nextTime = row.querySelector("[data-article-next-time]")?.value;
    const result = row.querySelector("[data-article-result]");
    const nextDateInput = row.querySelector("[data-article-next-date]");
    nextDateInput?.setCustomValidity("");
    row.dataset.articleValid = "false";
    result?.classList.remove("article-result-error");
    if (!endDate || !endTime || !nextDate || !nextTime) {
      if (result) result.textContent = "Completá ambos momentos para calcular las HS ARTICULO.";
      return;
    }
    const end = new Date(`${endDate}T${endTime}:00`);
    const next = new Date(`${nextDate}T${nextTime}:00`);
    const rest = (next - end) / 3600000;
    if (rest <= 0) {
      const message = "El inicio de la jornada siguiente debe ser posterior al fin de la anterior.";
      nextDateInput?.setCustomValidity(message);
      if (result) {
        result.textContent = message;
        result.classList.add("article-result-error");
      }
    } else if (rest >= 12) {
      row.dataset.articleValid = "true";
      if (result) result.textContent = `Descanso real: ${rest.toLocaleString("es-AR")} h. Se cumplieron las 12 horas; no corresponde HS ARTICULO.`;
    } else if (result) {
      row.dataset.articleValid = "true";
      const articleHours = Math.round((12 - rest) * 2) / 2;
      result.textContent = `Descanso real: ${rest.toLocaleString("es-AR")} h. Corresponden ${articleHours.toLocaleString("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} HS ARTICULO.`;
    }
  };

  otherArticle?.querySelectorAll("[data-article-time-control]").forEach((control) => {
    const hour = control.querySelector("[data-article-hour]");
    const minute = control.querySelector("[data-article-minute]");
    const hidden = control.querySelector('input[type="hidden"]');
    const sync = () => {
      hidden.value = hour.value && minute.value ? `${hour.value}:${minute.value}` : "";
      updateArticleResult(otherArticle);
    };
    hour?.addEventListener("change", sync);
    minute?.addEventListener("change", sync);
  });
  otherArticle?.querySelectorAll("[data-article-end-date], [data-article-next-date]").forEach((input) => {
    input.addEventListener("change", () => updateArticleResult(otherArticle));
  });

  const articleDates = () => {
    const mode = dateMode?.querySelector('input[name="modo_fechas"]:checked')?.value || "FECHAS";
    if (mode === "PERIODO") {
      const from = localDate(datePeriod?.querySelector('input[name="periodo_fecha_desde"]')?.value);
      const to = localDate(datePeriod?.querySelector('input[name="periodo_fecha_hasta"]')?.value);
      const weekdays = new Set(Array.from(
        datePeriod?.querySelectorAll('input[name="periodo_dias_semana"]:checked') || [],
      ).map((input) => Number(input.value)));
      if (!from || !to || from > to || !weekdays.size) return [];
      const dates = [];
      while (from <= to) {
        if (weekdays.has((from.getDay() + 6) % 7)) dates.push(isoLocalDate(from));
        from.setDate(from.getDate() + 1);
      }
      return dates;
    }
    return Array.from(new Set(Array.from(
      specificDates?.querySelectorAll('input[name="fecha"]') || [],
    ).map((input) => input.value).filter(Boolean))).sort();
  };

  const formatArticleDate = (iso) => {
    const [year, month, day] = iso.split("-");
    return `${day}/${month}/${year}`;
  };

  const setArticleTimeValue = (input, value) => {
    if (!input) return;
    input.value = value || "";
    const control = input.closest("[data-article-time-control]");
    const [hour = "", minute = ""] = (value || "").split(":");
    if (control?.querySelector("[data-article-hour]")) {
      control.querySelector("[data-article-hour]").value = hour;
      control.querySelector("[data-article-minute]").value = minute || "00";
    }
  };

  const setArticleEndFromSource = (row) => {
    const source = row.querySelector("[data-article-source]")?.value;
    if (!source || !endInput.value) return;
    const endDate = localDate(source);
    if (startInput.value && timeToMinutes(endInput.value) < timeToMinutes(startInput.value)) {
      endDate.setDate(endDate.getDate() + 1);
    }
    const endDateInput = row.querySelector("[data-article-end-date]");
    const endTimeInput = row.querySelector("[data-article-end-time]");
    if (endDateInput) endDateInput.value = isoLocalDate(endDate);
    setArticleTimeValue(endTimeInput, endInput.value);
    updateArticleResult(row);
  };

  const refreshArticleSources = () => {
    const dates = articleDates();
    hoursArticle?.querySelectorAll(".article-calculation-row").forEach((row) => {
      const select = row.querySelector("[data-article-source]");
      const previous = select.value;
      select.innerHTML = '<option value="">Seleccionar jornada</option>'
        + dates.map((value) => `<option value="${value}">${formatArticleDate(value)} · finaliza ${endInput.value || "--:--"}</option>`).join("");
      if (dates.includes(previous)) select.value = previous;
      else if (dates.length === 1) select.value = dates[0];
      if (select.value) setArticleEndFromSource(row);
    });
  };

  const addArticleRow = () => {
    const rows = hoursArticle?.querySelector("[data-article-rows]");
    const template = hoursArticle?.querySelector("[data-article-row-template]");
    if (!rows || !template) return;
    const row = template.content.firstElementChild.cloneNode(true);
    rows.appendChild(row);
    row.querySelectorAll("input, select").forEach((input) => {
      input.disabled = false;
    });
    row.querySelectorAll("[data-article-time-control]").forEach((control) => {
      const hour = control.querySelector("[data-article-hour]");
      const minute = control.querySelector("[data-article-minute]");
      const hidden = control.querySelector('input[type="hidden"]');
      const sync = () => {
        hidden.value = hour.value && minute.value ? `${hour.value}:${minute.value}` : "";
        updateArticleResult(row);
      };
      hour.addEventListener("change", sync);
      minute.addEventListener("change", sync);
    });
    row.querySelector("[data-article-source]")?.addEventListener("change", () => {
      setArticleEndFromSource(row);
    });
    row.querySelectorAll("[data-article-end-date], [data-article-end-time], [data-article-next-date], [data-article-next-time]").forEach((input) => {
      input.addEventListener("change", () => updateArticleResult(row));
    });
    row.querySelector("[data-article-remove]")?.addEventListener("click", () => {
      row.remove();
      if (!rows.children.length) setHoursArticleEnabled(false);
    });
    refreshArticleSources();
  };

  const setHoursArticleEnabled = (enabled) => {
    const panel = hoursArticle?.querySelector("[data-article-panel]");
    const flag = hoursArticle?.querySelector("[data-article-enabled]");
    panel?.classList.toggle("hidden", !enabled);
    if (flag) flag.value = enabled ? "SI" : "NO";
    panel?.querySelectorAll("input, select, button").forEach((input) => {
      input.disabled = !enabled;
    });
    if (enabled && !hoursArticle?.querySelector(".article-calculation-row")) addArticleRow();
    if (enabled) refreshArticleSources();
  };

  hoursArticle?.querySelector("[data-article-toggle]")?.addEventListener("click", () => {
    const enabled = hoursArticle.querySelector("[data-article-enabled]")?.value !== "SI";
    setHoursArticleEnabled(enabled);
  });
  hoursArticle?.querySelector("[data-article-add]")?.addEventListener("click", addArticleRow);
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
    updateRecordType();
  });
  nocturnalStart?.addEventListener("change", updateNocturnalPreview);
  nocturnalEnd?.addEventListener("change", updateNocturnalPreview);
  dateMode?.querySelectorAll('input[name="modo_fechas"]').forEach((input) => {
    input.addEventListener("change", updateRecordType);
  });
  datePeriod?.querySelectorAll("input").forEach((input) => {
    input.addEventListener("change", () => {
      updatePeriodPreview();
      updateNocturnalPreview();
    });
  });
  specificDates?.addEventListener("change", refreshArticleSources);
  datePeriod?.addEventListener("change", refreshArticleSources);
  startInput.addEventListener("change", refreshArticleSources);
  endInput.addEventListener("change", refreshArticleSources);
  form.addEventListener("submit", (event) => {
    if (hoursArticle?.querySelector("[data-article-enabled]")?.value !== "SI") return;
    const rows = Array.from(hoursArticle.querySelectorAll(".article-calculation-row"));
    rows.forEach(updateArticleResult);
    const invalid = rows.find((row) => row.dataset.articleValid !== "true");
    if (!invalid) return;
    event.preventDefault();
    invalid.scrollIntoView({ behavior: "smooth", block: "center" });
    const firstIncomplete = invalid.querySelector(
      "select:invalid, input:not([type='hidden']):invalid",
    );
    if (firstIncomplete) firstIncomplete.reportValidity();
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
