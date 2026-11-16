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

  // Organization and reviewer pickers submit as soon as a value is chosen.
  document.querySelectorAll("select[data-autosubmit]").forEach(function (select) {
    select.addEventListener("change", function () { select.form.submit(); });
  });

  // Setup page: rebuild the search index for the active organization.
  const rebuild = document.getElementById("rebuild");
  if (rebuild) {
    rebuild.addEventListener("click", function () {
      const status = document.getElementById("rebuild-status");
      const template = rebuild.dataset.template;
      rebuild.disabled = true;
      status.textContent = "Rebuilding… (the first run downloads the embedding model)";
      fetch("/api/index/rebuild", { method: "POST", headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ template_id: template }) })
        .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.detail); return d; }); })
        .then(function (d) {
          const s = d[template];
          document.getElementById("chunks").textContent = s.chunks;
          status.textContent = "Done: " + s.files_read + " files, " + s.chunks + " chunks in " + s.seconds + " s";
        })
        .catch(function (e) { status.textContent = "Failed: " + e.message; })
        .finally(function () { rebuild.disabled = false; });
    });
  }

  // Close the mobile menu after choosing a page or pressing Escape.
  const toggle = document.getElementById("nav-toggle");
  // The Menu control is a real <button> so keyboard and screen-reader users can open it.
  const menuButton = document.querySelector(".menu-btn");
  function setMenu(open) {
    if (!toggle) return;
    toggle.checked = open;
    if (menuButton) menuButton.setAttribute("aria-expanded", open ? "true" : "false");
  }
  if (toggle) {
    if (menuButton) {
      menuButton.addEventListener("click", function () {
        setMenu(!toggle.checked);
        if (toggle.checked) { const first = document.querySelector(".sidebar a"); if (first) first.focus(); }
      });
    }
    toggle.addEventListener("change", function () { setMenu(toggle.checked); });  // clicking the dark backdrop
    document.querySelectorAll(".sidebar a").forEach(function (link) {
      link.addEventListener("click", function () { setMenu(false); });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && toggle.checked) { setMenu(false); if (menuButton) menuButton.focus(); }
    });
  }
})();
