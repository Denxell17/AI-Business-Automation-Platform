"use strict";
document.querySelectorAll("[data-assistant-form]").forEach((form) => {
  form.addEventListener("submit", () => {
    form.setAttribute("aria-busy", "true");
    form.querySelector("button[type=submit]").disabled = true;
    form.querySelector("[data-assistant-status]").hidden = false;
  });
});
