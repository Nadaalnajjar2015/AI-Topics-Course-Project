// Shared page behaviour: table search/status filters and closing the mobile menu. No framework.
(function () {
  "use strict";

  // <div data-table-filter="table-id"> with an <input type=search> and buttons carrying data-status.
  document.querySelectorAll("[data-table-filter]").forEach(function (bar) {
    const table = document.getElementById(bar.dataset.tableFilter);
    if (!table) return;
    const input = bar.querySelector("input[type=search]");
    const buttons = bar.querySelectorAll("button[data-status]");
    const empty = document.getElementById(bar.dataset.tableFilter + "-empty");
    let status = "all";

    function apply() {
      const query = (input ? input.value : "").trim().toLowerCase();
      let shown = 0;
      table.querySelectorAll("tbody tr[data-status]").forEach(function (row) {
        const statusOk = status === "all" || row.dataset.status === status;
        const textOk = !query || row.textContent.toLowerCase().indexOf(query) !== -1;
        row.hidden = !(statusOk && textOk);
        if (!row.hidden) shown += 1;
      });
      if (empty) empty.hidden = shown > 0;
    }

    if (input) input.addEventListener("input", apply);
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        status = button.dataset.status;
        buttons.forEach(function (b) {
          b.classList.toggle("active", b === button);
          b.setAttribute("aria-pressed", b === button ? "true" : "false");
        });
        apply();
      });
    });
  });

  // Close the mobile menu after choosing a page or pressing Escape.
  const toggle = document.getElementById("nav-toggle");
  if (toggle) {
    document.querySelectorAll(".sidebar a").forEach(function (link) {
      link.addEventListener("click", function () { toggle.checked = false; });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") toggle.checked = false;
    });
  }
})();
