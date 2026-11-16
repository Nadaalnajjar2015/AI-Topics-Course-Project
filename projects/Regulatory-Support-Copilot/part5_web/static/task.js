// Task page: live timeline polling and review buttons. Plain JavaScript, no framework.
(function () {
  "use strict";
  const timeline = document.getElementById("timeline");
  if (!timeline) return;
  const taskId = timeline.dataset.task;

  function renderSteps(task) {
    timeline.replaceChildren(...task.steps.map(function (step) {
      const li = document.createElement("li");
      li.className = "step step-" + step.status;
      const icon = document.createElement("span");
      icon.className = "icon";
      const name = document.createElement("strong");
      name.textContent = step.name;
      const status = document.createElement("span");
      status.className = "step-status";
      status.textContent = step.status;
      li.append(icon, " ", name, " ", status);
      if (step.started_at && step.finished_at) {
        const duration = document.createElement("span");
        duration.className = "duration";
        const seconds = (new Date(step.finished_at) - new Date(step.started_at)) / 1000;
        duration.textContent = seconds.toFixed(1) + " s";
        li.append(" ", duration);
      }
      if (step.message) {
        const message = document.createElement("div");
        message.className = "step-message";
        message.textContent = step.message;  // textContent: never trusted HTML
        li.append(message);
      }
      return li;
    }));
  }

  // Poll every 2 seconds while running; stop and reload with the full cards when it is not.
  function poll() {
    fetch("/api/tasks/" + encodeURIComponent(taskId))
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (task) {
        renderSteps(task);
        if (task.status === "running") setTimeout(poll, 2000);
        else window.location.reload();
      })
      .catch(function () { setTimeout(poll, 5000); });
  }
  if (timeline.dataset.status === "running") setTimeout(poll, 2000);

  function editedContent(box) {
    const form = box.querySelector(".edit-form");
    if (box.dataset.kind === "reply") return form.querySelector("textarea[name=reply]").value;
    const checks = Array.from(form.querySelectorAll(".check-edit")).map(function (fs) {
      return {
        check_id: fs.dataset.checkId,
        steps: fs.querySelector("textarea[name=steps]").value.split("\n").map(function (s) { return s.trim(); }).filter(Boolean),
        expected: fs.querySelector("input[name=expected]").value.trim(),
      };
    });
    const content = { description: form.querySelector("textarea[name=description]").value };
    if (checks.length) content.checks = checks;
    return content;
  }

  document.querySelectorAll(".review").forEach(function (box) {
    const error = box.querySelector(".review-error");
    box.addEventListener("click", function (event) {
      const button = event.target.closest("button");
      if (!button) return;
      event.preventDefault();
      if (button.dataset.toggle) {
        box.querySelector("." + button.dataset.toggle + "-form").hidden = false;
        return;
      }
      const decision = button.dataset.decision;
      const body = { item_id: box.dataset.item, decision: decision, edited_content: null, comment: null };
      if (decision === "edit") body.edited_content = editedContent(box);
      if (decision === "reject") {
        body.comment = box.querySelector("input[name=comment]").value.trim();
        if (!body.comment) { error.textContent = "Please write a short comment before rejecting."; error.hidden = false; return; }
      }
      box.querySelectorAll("button").forEach(function (b) { b.disabled = true; });
      fetch("/api/tasks/" + encodeURIComponent(taskId) + "/review", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      }).then(function (r) {
        if (r.ok) { window.location.reload(); return; }
        return r.json().then(function (data) { throw new Error(data.detail || "Review failed"); });
      }).catch(function (e) {
        error.textContent = e.message; error.hidden = false;
        box.querySelectorAll("button").forEach(function (b) { b.disabled = false; });
      });
    });
  });
})();
