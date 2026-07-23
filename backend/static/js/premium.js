/* NeuroLens premium UI interactions */
(function () {
  const sidebar = document.getElementById("appSidebar");
  const backdrop = document.getElementById("sidebarBackdrop");
  const menuBtn = document.getElementById("menuBtn");

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("open");
    if (backdrop) backdrop.classList.add("show");
  }
  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("show");
  }

  if (menuBtn) menuBtn.addEventListener("click", openSidebar);
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  document.querySelectorAll("[data-auto-dismiss]").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .35s ease, transform .35s ease";
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 360);
    }, 4800);
  });

  document.querySelectorAll("[data-preview-target]").forEach((input) => {
    const id = input.getAttribute("data-preview-target");
    const img = document.getElementById(id);
    const meta = document.getElementById(id + "Meta");
    if (!img) return;
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) return;
      img.src = URL.createObjectURL(file);
      img.hidden = false;
      if (meta) {
        meta.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
        meta.hidden = false;
      }
    });
  });

  document.querySelectorAll("input[type=range][data-range-label]").forEach((range) => {
    const label = document.querySelector(range.getAttribute("data-range-label"));
    if (!label) return;
    const sync = () => {
      label.textContent = range.value;
    };
    range.addEventListener("input", sync);
    sync();
  });

  window.NLCharts = {
    bar(canvasId, labels, values, color) {
      const el = document.getElementById(canvasId);
      if (!el || typeof Chart === "undefined") return;
      const ctx = el.getContext("2d");
      const gradient = ctx.createLinearGradient(0, 0, 0, 260);
      gradient.addColorStop(0, color || "rgba(20,184,166,0.9)");
      gradient.addColorStop(1, color || "rgba(15,118,110,0.35)");
      new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: gradient,
              borderRadius: 10,
              borderSkipped: false,
              maxBarThickness: 42,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: "#0b1220" },
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: "#64748b", font: { size: 11, weight: "600" } },
            },
            y: {
              grid: { color: "rgba(15,23,42,0.06)" },
              ticks: { color: "#94a3b8" },
              beginAtZero: true,
            },
          },
        },
      });
    },
    line(canvasId, labels, values) {
      const el = document.getElementById(canvasId);
      if (!el || typeof Chart === "undefined") return;
      const ctx = el.getContext("2d");
      const gradient = ctx.createLinearGradient(0, 0, 0, 260);
      gradient.addColorStop(0, "rgba(99,102,241,0.28)");
      gradient.addColorStop(1, "rgba(99,102,241,0.02)");
      new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              data: values,
              borderColor: "#6366f1",
              backgroundColor: gradient,
              fill: true,
              tension: 0.4,
              pointRadius: 3.5,
              pointBackgroundColor: "#14b8a6",
              pointBorderColor: "#fff",
              pointBorderWidth: 2,
              borderWidth: 3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: "#0b1220" },
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: "#64748b", maxTicksLimit: 8, font: { size: 11 } },
            },
            y: {
              grid: { color: "rgba(15,23,42,0.06)" },
              ticks: { color: "#94a3b8" },
              beginAtZero: true,
            },
          },
        },
      });
    },
    doughnut(canvasId, labels, values) {
      const el = document.getElementById(canvasId);
      if (!el || typeof Chart === "undefined") return;
      new Chart(el.getContext("2d"), {
        type: "doughnut",
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: [
                "#0d9488",
                "#6366f1",
                "#06b6d4",
                "#f59e0b",
                "#e11d48",
                "#8b5cf6",
              ],
              borderWidth: 0,
              hoverOffset: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "62%",
          plugins: {
            legend: {
              position: "bottom",
              labels: {
                boxWidth: 10,
                usePointStyle: true,
                padding: 14,
                color: "#64748b",
              },
            },
          },
        },
      });
    },
  };
})();
