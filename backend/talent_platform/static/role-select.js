const roleChoices = [...document.querySelectorAll("[data-role]")];
const continueButton = document.querySelector("#continue-role");
const roleForm = document.querySelector("#role-form");
const roleInput = document.querySelector("#role-input");
let selectedRole = null;

function selectRole(role) {
  selectedRole = role;
  for (const choice of roleChoices) {
    choice.setAttribute("aria-pressed", String(choice.dataset.role === role));
  }
  continueButton.disabled = false;
}

for (const choice of roleChoices) {
  choice.addEventListener("click", () => selectRole(choice.dataset.role));
}

continueButton.addEventListener("click", () => {
  if (!selectedRole) return;
  roleInput.value = selectedRole;
  roleForm.requestSubmit();
});
