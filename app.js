document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();

  const toggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) toggle.addEventListener("click", () => sidebar.classList.toggle("sidebar-open"));

  document.querySelectorAll(".notice-close").forEach(btn => btn.addEventListener("click", () => btn.closest(".notice").remove()));

  function bindSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;
    input.addEventListener("input", () => {
      const query = input.value.trim().toLowerCase();
      table.querySelectorAll("tbody tr").forEach(row => {
        row.hidden = !row.dataset.search.includes(query);
      });
    });
  }
  bindSearch("studentSearch", "studentsTable");
  bindSearch("allocationSearch", "allocationTable");

  const studentDialog = document.getElementById("studentDialog");
  const hallDialog = document.getElementById("hallDialog");
  document.querySelectorAll(".edit-student").forEach(button => button.addEventListener("click", () => {
    document.getElementById("studentEditForm").action = `/students/${button.dataset.id}/edit`;
    document.getElementById("editStudentNo").value = button.dataset.no;
    document.getElementById("editStudentName").value = button.dataset.name;
    document.getElementById("editStudentSubject").value = button.dataset.subject;
    studentDialog.showModal();
  }));
  document.querySelectorAll(".edit-hall").forEach(button => button.addEventListener("click", () => {
    document.getElementById("hallEditForm").action = `/halls/${button.dataset.id}/edit`;
    document.getElementById("editHallName").value = button.dataset.name;
    document.getElementById("editHallCapacity").value = button.dataset.capacity;
    hallDialog.showModal();
  }));
  document.querySelectorAll(".dialog-close").forEach(button => button.addEventListener("click", () => button.closest("dialog").close()));
  [studentDialog, hallDialog].forEach(dialog => {
    if (!dialog) return;
    dialog.addEventListener("click", event => {
      if (event.target === dialog) dialog.close();
    });
  });

  const dashboard = window.examDashboard;
  if (dashboard && window.Chart) {
    const donut = document.getElementById("utilizationChart");
    if (donut) new Chart(donut, {
      type: "doughnut",
      data: { labels: ["Allocated", "Available"], datasets: [{ data: [dashboard.dashboard.allocated, dashboard.available], backgroundColor: ["#6558e8", "#ececf4"], borderWidth: 0, hoverOffset: 5, borderRadius: 8 }] },
      options: { responsive: true, maintainAspectRatio: false, cutout: "78%", plugins: { legend: { display: false }, tooltip: { enabled: true } } }
    });
    const subject = document.getElementById("subjectChart");
    if (subject) new Chart(subject, {
      type: "bar",
      data: { labels: dashboard.subjects, datasets: [{ label: "Students", data: dashboard.subjectCounts, backgroundColor: "#7669ed", borderRadius: 7, maxBarThickness: 34 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: "#9293a6" } }, y: { beginAtZero: true, ticks: { precision: 0, color: "#9293a6" }, grid: { color: "#f0f0f5" } } } }
    });
  }
});