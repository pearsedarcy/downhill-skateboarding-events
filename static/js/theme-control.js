const themeToggle = document.querySelector(".theme-controller");
const logo = document.querySelector('img[alt="SDH Logo"]');

function setTheme(isDark) {
  const theme = isDark ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  themeToggle.checked = isDark;
  themeToggle.blur();
  logo.className = isDark ? "logo-dark" : "logo-light";
}

document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme") || "light";
  themeToggle.checked = savedTheme === "dark";
  logo.className = savedTheme === "dark" ? "logo-dark" : "logo-light";
});

themeToggle.addEventListener("change", (e) => {
  setTheme(e.target.checked);
});
