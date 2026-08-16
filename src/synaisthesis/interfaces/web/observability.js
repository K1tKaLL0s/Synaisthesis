/* M14.WEB.OBSERVABILITY page renderer.
 *
 * Contract: this renderer never derives state.  It only reads fields that
 * already exist in the frozen-schema API payload and renders them verbatim.
 */
"use strict";

function renderObservability(payload, container) {
  container.textContent = "";
  if (!payload || !Array.isArray(payload.pages)) {
    return;
  }
  const header = document.createElement("p");
  header.className = "field";
  header.textContent =
    "schema_version=" + payload.schema_version +
    " rendered_from_store=" + payload.rendered_from_store;
  container.appendChild(header);
  for (const page of payload.pages) {
    const section = document.createElement("section");
    section.className = "page";

    const title = document.createElement("h2");
    title.textContent = page.title;
    section.appendChild(title);

    const status = document.createElement("span");
    status.className = "status " + page.status;
    status.textContent = page.status;
    section.appendChild(status);

    const route = document.createElement("div");
    route.className = "field";
    route.textContent = "route: " + (page.route === null ? "(未选定)" : page.route);
    section.appendChild(route);

    if (page.inputs && page.inputs.length) {
      const inputs = document.createElement("div");
      inputs.className = "field";
      inputs.textContent = "inputs: " +
        page.inputs.map(function (item) {
          return item.aggregate_type + "/" + item.aggregate_id;
        }).join(", ");
      section.appendChild(inputs);
    }

    if (page.gates && page.gates.length) {
      const gates = document.createElement("ul");
      page.gates.forEach(function (gate) {
        const item = document.createElement("li");
        item.className = "field";
        item.textContent = gate.gate_type + " " + gate.gate_id + " [" + gate.status + "]";
        gates.appendChild(item);
      });
      section.appendChild(gates);
    }

    if (page.artifacts && page.artifacts.length) {
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(page.artifacts, null, 2);
      section.appendChild(pre);
    }

    container.appendChild(section);
  }
}

function loadObservability(baseUrl) {
  const projectId = document.getElementById("project-id").value.trim();
  const container = document.getElementById("pages");
  const error = document.getElementById("error");
  error.textContent = "";
  if (!projectId) {
    error.textContent = "project_id 不能为空";
    return;
  }
  fetch(baseUrl + "?project_id=" + encodeURIComponent(projectId))
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (payload) {
      renderObservability(payload, container);
    })
    .catch(function (err) {
      error.textContent = "加载失败: " + err.message;
    });
}

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("load").addEventListener("click", function () {
    loadObservability("/api/observability");
  });
});

/* exported for contract tests: window.renderObservability */
window.renderObservability = renderObservability;
