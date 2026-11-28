(() => {
  const btn = document.getElementById("theme-toggle");
  function effectiveTheme() {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr === "light" || attr === "dark") return attr;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  function syncToggle() {
    if (!btn) return;
    const dark = effectiveTheme() === "dark";
    btn.setAttribute("aria-pressed", dark ? "true" : "false");
    btn.title = dark ? "Switch to light mode (D)" : "Switch to dark mode (D)";
  }
  function toggleTheme() {
    const next = effectiveTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (_) {}
    syncToggle();
  }
  syncToggle();
  if (btn) btn.addEventListener("click", toggleTheme);

  const bar = document.getElementById("read-progress");
  if (bar) {
    let ticking = false;
    const updateProgress = () => {
      ticking = false;
      const doc = document.documentElement;
      const max = doc.scrollHeight - window.innerHeight;
      const ratio = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      bar.style.transform = `scaleX(${ratio.toFixed(4)})`;
    };
    updateProgress();
    window.addEventListener("scroll", () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(updateProgress);
      }
    }, { passive: true });
    window.addEventListener("resize", updateProgress, { passive: true });
  }

  document.addEventListener("keydown", (e) => {
    if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.isContentEditable)) return;
    if (e.key === "d" || e.key === "D") toggleTheme();
  });
})();
