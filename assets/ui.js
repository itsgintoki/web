(() => {
  const site = document.querySelector(".site");

  const stackButton = document.querySelector(".grid-icon");
  const stackPopover = document.getElementById("stack-popover");
  const stackMenu = stackButton && stackButton.closest(".stack-menu");
  if (stackButton && stackPopover && stackMenu) {
    const setStackOpen = (open, restoreFocus = false) => {
      stackPopover.hidden = !open;
      stackButton.setAttribute("aria-expanded", String(open));

      if (open) {
        stackPopover.focus({ preventScroll: true });
      } else if (restoreFocus) {
        stackButton.focus({ preventScroll: true });
      }
    };

    stackButton.addEventListener("click", () => setStackOpen(stackPopover.hidden));

    document.addEventListener("pointerdown", (event) => {
      if (!stackPopover.hidden && !stackMenu.contains(event.target)) setStackOpen(false);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !stackPopover.hidden) setStackOpen(false, true);
    });

    document.addEventListener("focusin", (event) => {
      if (!stackPopover.hidden && !stackMenu.contains(event.target)) setStackOpen(false);
    });
  }

  const resumeTrigger = document.getElementById("resume-trigger");
  const resumeModal = document.getElementById("resume-modal");
  if (!resumeTrigger || !resumeModal) return;

  const dialog = resumeModal.querySelector(".resume-dialog");
  const closeButton = resumeModal.querySelector(".resume-close");
  if (!dialog || !closeButton) return;

  const setResumeOpen = (open) => {
    if (!open) {
      resumeModal.hidden = true;
      document.body.classList.remove("modal-open");
      if (site) site.inert = false;
      resumeTrigger.setAttribute("aria-expanded", "false");
      resumeTrigger.focus({ preventScroll: true });
      return;
    }

    resumeModal.hidden = false;
    document.body.classList.add("modal-open");
    if (site) site.inert = true;
    resumeTrigger.setAttribute("aria-expanded", "true");
    closeButton.focus({ preventScroll: true });
  };

  resumeTrigger.addEventListener("click", (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    setResumeOpen(true);
  });

  closeButton.addEventListener("click", () => setResumeOpen(false));

  resumeModal.addEventListener("click", (event) => {
    if (event.target === resumeModal) setResumeOpen(false);
  });

  dialog.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;

    const focusable = [...dialog.querySelectorAll("a[href], button:not([disabled])")]
      .filter((element) => element.offsetParent !== null);
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !resumeModal.hidden) setResumeOpen(false);
  });
})();
