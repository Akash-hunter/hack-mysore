const accountForm = document.querySelector("#account-form");

accountForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!accountForm.reportValidity()) return;

  const flow = accountForm.dataset.flow === "signup" ? "signup" : "login";
  for (const input of accountForm.querySelectorAll("input")) input.value = "";
  window.location.assign(`/select-role?flow=${flow}`);
});
