// CSRF token helper
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// XSS protection helper - escape HTML special characters
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// API helpers
const api = {
    async get(url) {
        const res = await fetch(url);
        return res.json();
    },
    async post(url, data) {
        const res = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async postForm(url, formData) {
        const res = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken()
            },
            body: formData,
        });
        return res.json();
    },
    async put(url, data) {
        const res = await fetch(url, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken()
            },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async putForm(url, formData) {
        const res = await fetch(url, {
            method: "PUT",
            headers: {
                "X-CSRFToken": getCsrfToken()
            },
            body: formData,
        });
        return res.json();
    },
    async del(url) {
        const res = await fetch(url, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": getCsrfToken()
            }
        });
        return res.json();
    },
};

// ===== Theme Management =====
const THEME_KEY = "theme";

function getTheme() {
    return localStorage.getItem(THEME_KEY) || "system";
}

function setTheme(mode) {
    localStorage.setItem(THEME_KEY, mode);
    applyTheme();
    updateThemeButtons();
}

function applyTheme() {
    const mode = getTheme();
    const root = document.documentElement;
    if (mode === "light") {
        root.setAttribute("data-theme", "light");
    } else if (mode === "dark") {
        root.setAttribute("data-theme", "dark");
    } else {
        // system: remove attribute, let @media (prefers-color-scheme) work
        root.removeAttribute("data-theme");
    }
}

function updateThemeButtons() {
    const mode = getTheme();
    document.querySelectorAll(".theme-toggle button").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.theme === mode);
    });
}

// Listen for system theme changes
if (window.matchMedia) {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (getTheme() === "system") {
            // CSS @media handles it, but update buttons in case UI needs refresh
            updateThemeButtons();
        }
    });
}

// ===== Global Grade Management =====
let currentGrade = localStorage.getItem("selectedGrade") || "初一";

function onGradeChange(grade) {
    currentGrade = grade;
    localStorage.setItem("selectedGrade", grade);
    location.reload();
}

// ===== Init =====
document.addEventListener("DOMContentLoaded", () => {
    const sel = document.getElementById("globalGradeSelect");
    if (sel) sel.value = currentGrade;

    // Apply theme on load (before paint to avoid flash)
    applyTheme();
    updateThemeButtons();
});

// Apply theme immediately (before DOMContentLoaded to prevent flash)
applyTheme();

// Toast notification
function toast(msg, duration = 2000) {
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), duration);
}

// Render difficulty badge
function difficultyBadge(level) {
    const labels = { 1: "简单", 2: "中等", 3: "困难" };
    return `<span class="difficulty difficulty-${level}">${labels[level] || "未知"}</span>`;
}

// Render tags (with XSS protection)
function renderTags(tags) {
    try {
        const arr = typeof tags === "string" ? JSON.parse(tags) : tags;
        return arr.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("");
    } catch {
        return "";
    }
}

// Render grade badge
function gradeBadge(grade) {
    if (!grade) return "";
    return `<span class="grade-badge">${grade}</span>`;
}

// Pagination helper
function renderPagination(page, pages, onPageChange) {
    if (pages <= 1) return "";
    let html = '<div class="pagination">';
    html += `<button ${page <= 1 ? "disabled" : ""} onclick="${onPageChange}(${page - 1})">上一页</button>`;
    html += `<span class="page-info">${page} / ${pages}</span>`;
    html += `<button ${page >= pages ? "disabled" : ""} onclick="${onPageChange}(${page + 1})">下一页</button>`;
    html += "</div>";
    return html;
}
