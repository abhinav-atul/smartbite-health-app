/**
 * SmartBite — Client-side application logic
 * Handles: Google Sign-In, step transitions, API calls, meal history.
 */

// ───────────────────────── CONFIG ─────────────────────────
// Replace with your own Google OAuth Client ID (or leave empty for demo flow)
const GOOGLE_CLIENT_ID = "";   // Set from Google Cloud Console

// ───────────────────────── DOM REFS ─────────────────────────
const $ = (sel) => document.querySelector(sel);
const welcomeSection  = $("#welcomeSection");
const step1           = $("#step1");
const step2           = $("#step2");
const preferencesForm = $("#preferencesForm");
const btnSubmit       = $("#btn-submit");
const btnBack         = $("#btn-back");
const btnLogout       = $("#btnLogout");
const recipeResult    = $("#recipeResult");
const loadingSpinner  = $("#loadingSpinner");
const btnText         = $(".btn-text");
const userMenu        = $("#userMenu");
const userAvatar      = $("#userAvatar");
const userNameEl      = $("#userName");

let currentUser = null;

// ───────────────────────── STEP MANAGEMENT ─────────────────────────
function showStep(sectionToShow) {
    [welcomeSection, step1, step2].forEach((s) => {
        s.classList.remove("active");
        s.style.display = "none";
    });
    sectionToShow.style.display = "block";
    // Trigger reflow for the CSS animation
    void sectionToShow.offsetWidth;
    sectionToShow.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ───────────────────────── GOOGLE SIGN-IN ─────────────────────────
/**
 * Called by the Google Identity Services library after user signs in.
 */
function handleGoogleSignIn(response) {
    fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: response.credential }),
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.success) {
                setUser(data.user);
                showStep(step1);
            } else {
                showToast("Sign-in failed: " + data.error, "error");
            }
        })
        .catch(() => showToast("Network error during sign-in.", "error"));
}

// Expose globally so the GIS library callback can find it
window.handleGoogleSignIn = handleGoogleSignIn;

function setUser(user) {
    currentUser = user;
    userAvatar.src = user.picture || "";
    userNameEl.textContent = user.name || "User";
    userMenu.classList.remove("hidden");
    // Hide the Google sign-in button
    const gsiBtn = $("#googleSignInBtn");
    if (gsiBtn) gsiBtn.style.display = "none";
}

function clearUser() {
    currentUser = null;
    userMenu.classList.add("hidden");
    const gsiBtn = $("#googleSignInBtn");
    if (gsiBtn) gsiBtn.style.display = "block";
}

// ───────────────────────── INIT: Render Google button ─────────────────────────
window.addEventListener("load", () => {
    // Check if already signed in (server session)
    fetch("/api/auth/me")
        .then((r) => r.json())
        .then((data) => {
            if (data.authenticated) {
                setUser(data.user);
                showStep(step1);
            }
        })
        .catch(() => {});

    // Render the Google sign-in button if GIS library is loaded and client ID is set
    if (GOOGLE_CLIENT_ID && typeof google !== "undefined") {
        google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleSignIn,
        });
        google.accounts.id.renderButton($("#googleSignInBtn"), {
            theme: "filled_black",
            size: "medium",
            shape: "pill",
            text: "signin_with",
        });
    } else {
        // Demo mode: show a manual sign-in button when no client ID is configured
        const demoBtn = document.createElement("button");
        demoBtn.className = "btn-logout";
        demoBtn.style.cssText = "border-color:var(--primary-light);color:var(--primary-light);padding:0.5rem 1.2rem;font-size:0.85rem;";
        demoBtn.textContent = "🔑 Demo Sign In";
        demoBtn.addEventListener("click", () => {
            const name = prompt("Enter your name for the demo:");
            if (!name) return;
            const user = { name, email: "", picture: "" };
            // Create a lightweight session on the server
            fetch("/api/auth/google", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // Send a fake JWT-like token with base64 payload for demo
                body: JSON.stringify({
                    credential: "header." + btoa(JSON.stringify(user)) + ".sig",
                }),
            })
                .then((r) => r.json())
                .then((data) => {
                    if (data.success) { setUser(data.user); showStep(step1); }
                });
        });
        $("#googleSignInBtn").appendChild(demoBtn);
    }
});

// ───────────────────────── LOGOUT ─────────────────────────
btnLogout.addEventListener("click", () => {
    fetch("/api/auth/logout", { method: "POST" })
        .then(() => {
            clearUser();
            showStep(welcomeSection);
        });
});

// ───────────────────────── FORM SUBMISSION ─────────────────────────
preferencesForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
        goals:       $("#goals").value,
        diet:        $("#diet").value,
        ingredients: $("#ingredients").value,
        allergies:   $("#allergies").value,
        activity:    $("#activity").value,
    };

    // Loading state
    btnText.textContent = "Generating…";
    loadingSpinner.classList.remove("hidden");
    btnSubmit.disabled = true;

    try {
        const res = await fetch("/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (data.success) {
            recipeResult.innerHTML = data.recommendation;
            saveMealToHistory(payload, data.recommendation);
            showStep(step2);
        } else {
            showToast(data.error || "Could not generate recommendations.", "error");
        }
    } catch (err) {
        showToast("Server unreachable – is the backend running?", "error");
    } finally {
        btnText.textContent = "✨ Generate My Meals";
        loadingSpinner.classList.add("hidden");
        btnSubmit.disabled = false;
    }
});

// ───────────────────────── BACK BUTTON ─────────────────────────
btnBack.addEventListener("click", () => showStep(step1));

// ───────────────────────── MEAL HISTORY (localStorage) ─────────────────────────
function saveMealToHistory(input, html) {
    try {
        const history = JSON.parse(localStorage.getItem("smartbite_history") || "[]");
        history.unshift({
            date: new Date().toISOString(),
            goals: input.goals,
            diet: input.diet,
        });
        // Keep only last 20 entries
        localStorage.setItem("smartbite_history", JSON.stringify(history.slice(0, 20)));
    } catch (_) { /* localStorage unavailable */ }
}

// ───────────────────────── TOAST NOTIFICATIONS ─────────────────────────
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
        padding: 0.9rem 1.6rem; border-radius: 12px; font-size: 0.9rem;
        font-weight: 500; z-index: 9999; animation: slideUp 0.4s ease forwards;
        color: #fff; max-width: 90vw; text-align: center;
        background: ${type === "error" ? "#EF4444" : "#7C3AED"};
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.4s ease";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}
