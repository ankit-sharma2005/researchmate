(() => {
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-icon");

  const showTheme = (theme) => {
    root.setAttribute("data-bs-theme", theme);
    if (icon) {
      icon.textContent = theme === "dark" ? "☀" : "☾";
      toggle.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light theme" : "Switch to dark theme",
      );
      toggle.setAttribute(
        "title",
        theme === "dark" ? "Switch to light theme" : "Switch to dark theme",
      );
    }
  };

  if (toggle) {
    showTheme(root.getAttribute("data-bs-theme") || "light");
    toggle.addEventListener("click", () => {
      const nextTheme = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      showTheme(nextTheme);
      try {
        localStorage.setItem("researchmate-theme", nextTheme);
      } catch (error) {
        // The current page theme still works when browser storage is unavailable.
      }
    });
  }
})();
