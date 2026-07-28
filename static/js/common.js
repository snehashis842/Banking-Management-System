// Global utility functions, shared across every page (via base.html).

function showLoading(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML =
      '<div class="loading"><div class="spinner"></div>Loading...</div>';
  }
}

function showError(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = `<div class="alert alert-error">${message}</div>`;
  }
}

function showSuccess(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = `<div class="alert alert-success">${message}</div>`;
  }
}

// Handle authentication errors globally
function handleAuthError(response) {
  if (response.status === 401 || response.status === 403) {
    setTimeout(() => {
      window.location.href = "/";
    }, 2000);
    return true;
  }
  return false;
}

// Escapes HTML-significant characters before inserting untrusted data
// (user names, emails, addresses, etc.) into innerHTML template strings.
// Any value that came from a database record populated via user input
// MUST go through this before being placed in an innerHTML string —
// template literals do not escape by default, unlike Jinja's {{ }}.
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
