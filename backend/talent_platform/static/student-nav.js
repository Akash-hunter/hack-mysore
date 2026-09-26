const studentNavigation = document.querySelector(".student-navigation");

studentNavigation?.addEventListener("click", (event) => {
  const link = event.target.closest(".student-nav-link");
  if (!link) return;

  for (const item of studentNavigation.querySelectorAll(".student-nav-link")) {
    const isCurrent = item === link;
    item.classList.toggle("active", isCurrent);
    if (isCurrent) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  }
});
