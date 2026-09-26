const workspaceStep = document.querySelector("#workspace-step");
const accessStep = document.querySelector("#access-step");
const domainChoices = [...document.querySelectorAll("[data-domain]")];
const continueButton = document.querySelector("#continue-button");
const backButton = document.querySelector("#back-button");
const signInForm = document.querySelector("#sign-in-form");
const organizationField = document.querySelector("#organization-field");
const organizationInput = document.querySelector("#organization-input");
const emailInput = document.querySelector("#email-input");
const passwordInput = document.querySelector("#password-input");
const statusMessage = document.querySelector("#sign-in-status");
const previewLink = document.querySelector("#preview-link");
const roleConfig = {
  student: {
    label: "STUDENT",
    title: "Student sign in",
    description: "Continue to your personal profile and opportunities.",
    emailLabel: "Student email",
    emailPlaceholder: "you@school.edu",
    preview: "Open student dashboard preview",
  },
  recruiter: {
    label: "RECRUITER",
    title: "Recruiter sign in",
    description: "Continue to your company hiring workspace.",
    emailLabel: "Work email",
    emailPlaceholder: "you@company.com",
    preview: "Open recruiter dashboard preview",
  },
  institution: {
    label: "INSTITUTION",
    title: "Institution sign in",
    description: "Continue to your institution outcomes workspace.",
    emailLabel: "Institution email",
    emailPlaceholder: "you@institution.edu",
    preview: "Open institution dashboard preview",
  },
};
let selectedDomain = null;

function selectDomain(domain) {
  selectedDomain = domain;
  for (const choice of domainChoices) {
    choice.setAttribute("aria-pressed", String(choice.dataset.domain === domain));
  }
  continueButton.disabled = false;
}

function showAccessStep() {
  if (!selectedDomain) return;
  const config = roleConfig[selectedDomain];
  workspaceStep.hidden = true;
  accessStep.hidden = false;
  document.querySelector("#access-title").textContent = config.title;
  document.querySelector("#access-description").textContent = config.description;
  document.querySelector("#email-label").textContent = config.emailLabel;
  emailInput.placeholder = config.emailPlaceholder;
  organizationField.hidden = selectedDomain === "student";
  organizationInput.required = selectedDomain !== "student";
  organizationInput.placeholder = selectedDomain === "recruiter"
    ? "Company name"
    : "Institution name";
  document.querySelector("#selected-domain-tag").textContent = ` / ${config.label}`;
  previewLink.textContent = `${config.preview} ->`;
  previewLink.href = `/dashboard?role=${selectedDomain}`;
  document.querySelector('[data-flow-step="1"]').classList.remove("active");
  document.querySelector('[data-flow-step="1"]').classList.add("complete");
  document.querySelector('[data-flow-step="2"]').classList.add("active");
  statusMessage.textContent = "";
  emailInput.focus();
}

function showWorkspaceStep() {
  accessStep.hidden = true;
  workspaceStep.hidden = false;
  document.querySelector('[data-flow-step="1"]').classList.add("active");
  document.querySelector('[data-flow-step="1"]').classList.remove("complete");
  document.querySelector('[data-flow-step="2"]').classList.remove("active");
  document.querySelector(`[data-domain="${selectedDomain}"]`)?.focus();
}

for (const choice of domainChoices) {
  choice.addEventListener("click", () => selectDomain(choice.dataset.domain));
}

continueButton.addEventListener("click", showAccessStep);
backButton.addEventListener("click", showWorkspaceStep);
signInForm.addEventListener("submit", (event) => {
  event.preventDefault();
  statusMessage.textContent = "Sign-in is not connected in this local preview. Credentials were not sent or saved.";
  emailInput.value = "";
  passwordInput.value = "";
  organizationInput.value = "";
});
