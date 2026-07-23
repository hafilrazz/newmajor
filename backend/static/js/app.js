/* NeuroLens UI helpers */
(function () {
  const toggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }

  // Auto-hide flash messages
  document.querySelectorAll("[data-auto-dismiss]").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // Confirm destructive actions
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (!window.confirm(el.getAttribute("data-confirm"))) {
        e.preventDefault();
      }
    });
  });

  // Image preview for file inputs
  document.querySelectorAll("[data-preview-target]").forEach((input) => {
    const targetId = input.getAttribute("data-preview-target");
    const target = document.getElementById(targetId);
    if (!target) return;
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      target.src = url;
      target.hidden = false;
      const meta = document.getElementById(targetId + "Meta");
      if (meta) {
        meta.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
        meta.hidden = false;
      }
    });
  });
})();
