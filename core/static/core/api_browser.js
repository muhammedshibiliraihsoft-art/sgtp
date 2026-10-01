(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const routeList = byId("route-list");
  const search = byId("route-search");
  const routeCount = byId("route-count");
  const methodSelect = byId("http-method");
  const pathInput = byId("api-path");
  const description = byId("operation-description");
  const tokenInput = byId("access-token");
  const requestBody = byId("request-body");
  const responseStatus = byId("response-status");
  const responseBody = byId("response-body");
  const pageError = byId("page-error");
  let operations = [];

  function showError(message) {
    pageError.textContent = message;
    pageError.hidden = false;
  }

  function clearError() {
    pageError.textContent = "";
    pageError.hidden = true;
  }

  function addRouteButton(operation) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "route-button";
    button.dataset.search = `${operation.method} ${operation.path} ${operation.tags.join(" ")}`.toLowerCase();

    const method = document.createElement("span");
    method.className = `method method-${operation.method}`;
    method.textContent = operation.method.toUpperCase();
    const path = document.createElement("span");
    path.className = "route-path";
    path.textContent = operation.path;
    button.append(method, path);
    button.addEventListener("click", () => {
      document.querySelectorAll(".route-button[aria-current='true']").forEach((item) => {
        item.removeAttribute("aria-current");
      });
      button.setAttribute("aria-current", "true");
      methodSelect.value = operation.method.toUpperCase();
      pathInput.value = operation.path;
      description.textContent = operation.description || operation.summary || "No endpoint description is available.";
      requestBody.value = operation.hasBody ? "{}" : "";
      clearError();
    });
    routeList.appendChild(button);
  }

  async function loadSchema() {
    try {
      const response = await fetch("/api/schema/", {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error(`Could not load the protected API schema (HTTP ${response.status}).`);
      }
      const schema = await response.json();
      const supportedMethods = new Set(["get", "post", "put", "patch", "delete"]);
      Object.entries(schema.paths || {}).forEach(([path, pathItem]) => {
        if (!path.startsWith("/api/v1/")) return;
        Object.entries(pathItem).forEach(([method, operation]) => {
          if (!supportedMethods.has(method.toLowerCase()) || !operation || typeof operation !== "object") return;
          operations.push({
            method,
            path,
            tags: Array.isArray(operation.tags) ? operation.tags : [],
            summary: operation.summary || "",
            description: operation.description || "",
            hasBody: Boolean(operation.requestBody),
          });
        });
      });
      operations.sort((a, b) => a.path.localeCompare(b.path) || a.method.localeCompare(b.method));
      operations.forEach(addRouteButton);
      routeCount.textContent = `${operations.length} implemented operations`;
      if (!operations.length) routeCount.textContent = "No API operations were found.";
    } catch (error) {
      routeCount.textContent = "API list unavailable";
      showError(error.message || "Could not load the API list.");
    }
  }

  search.addEventListener("input", () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    routeList.querySelectorAll(".route-button").forEach((button) => {
      const matches = button.dataset.search.includes(query);
      button.hidden = !matches;
      if (matches) visible += 1;
    });
    routeCount.textContent = `${visible} of ${operations.length} operations`;
  });

  byId("clear-token").addEventListener("click", () => {
    tokenInput.value = "";
    tokenInput.focus();
  });

  async function getCsrfToken() {
    const response = await fetch("/api/v1/auth/csrf/", {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      cache: "no-store",
    });
    const data = await response.json();
    if (!response.ok || !data.csrf_token) throw new Error("Could not obtain the CSRF token required for this request.");
    return data.csrf_token;
  }

  byId("api-request-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    const method = methodSelect.value.toUpperCase();
    let target;
    try {
      target = new URL(pathInput.value.trim(), window.location.origin);
    } catch (_error) {
      showError("Enter a valid API path.");
      return;
    }
    if (target.origin !== window.location.origin || !target.pathname.startsWith("/api/v1/")) {
      showError("Requests are restricted to this site's /api/v1/ endpoints.");
      return;
    }
    if (/[{}]/.test(target.pathname)) {
      showError("Replace the {path} placeholders with real values before sending.");
      return;
    }

    const headers = { Accept: "application/json" };
    const accessToken = tokenInput.value.trim();
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
    const unsafe = !["GET", "HEAD", "OPTIONS"].includes(method);
    let body;
    if (unsafe) {
      headers["X-CSRFToken"] = await getCsrfToken().catch((error) => {
        showError(error.message);
        return null;
      });
      if (!headers["X-CSRFToken"]) return;
      if (requestBody.value.trim()) {
        try {
          body = JSON.stringify(JSON.parse(requestBody.value));
          headers["Content-Type"] = "application/json";
        } catch (_error) {
          showError("Request body must be valid JSON.");
          return;
        }
      }
    }

    responseStatus.textContent = "Sending…";
    responseBody.textContent = "";
    try {
      const response = await fetch(target, {
        method,
        headers,
        body,
        credentials: "same-origin",
        cache: "no-store",
      });
      const text = await response.text();
      let data = text;
      try { data = text ? JSON.stringify(JSON.parse(text), null, 2) : "(empty response)"; } catch (_error) { /* Keep non-JSON response text. */ }
      responseStatus.textContent = `HTTP ${response.status} ${response.statusText}`;
      responseBody.textContent = data;

      // Keep a returned access token only in the page's password input (memory).
      if (response.ok && typeof data === "string") {
        try {
          const parsed = JSON.parse(text);
          if (typeof parsed.access === "string") tokenInput.value = parsed.access;
        } catch (_error) { /* Response is not a JSON token response. */ }
      }
    } catch (_error) {
      responseStatus.textContent = "Request failed";
      responseBody.textContent = "The request could not reach this site's API.";
    }
  });

  loadSchema();
})();
