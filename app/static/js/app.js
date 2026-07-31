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
