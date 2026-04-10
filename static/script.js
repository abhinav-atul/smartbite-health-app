/**
 * SmartBite — Client Application v3
 * Multi-view SPA: Landing → Profile → Dashboard
 * Integrates: Google Sign-In, Gemini recommendations, Health analysis
 */

// ── Config ──────────────────────────────────────────────────────
const GOOGLE_CLIENT_ID = "";  // Set via Google Cloud Console for production

// ── DOM Helpers ─────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// ── Refs ────────────────────────────────────────────────────────
const views = {
    landing:   $("#viewLanding"),
    profile:   $("#viewProfile"),
    dashboard: $("#viewDashboard"),
};

let userProfile = null;  // cached health profile

// ── View Manager ────────────────────────────────────────────────
function showView(name) {
    Object.values(views).forEach((v) => {
        v.classList.remove("active");
        v.style.display = "none";
    });
    const target = views[name];
    target.style.display = "block";
    void target.offsetWidth;          // trigger reflow
    target.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ── Toast ───────────────────────────────────────────────────────
function toast(msg, type = "info") {
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .4s"; }, 3500);
    setTimeout(() => el.remove(), 4000);
}

// ── Google Sign-In ──────────────────────────────────────────────
function handleGoogleSignIn(response) {
    fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: response.credential }),
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.success) {
                onSignedIn(data.user);
            } else {
                toast("Sign-in failed: " + data.error, "error");
            }
        })
        .catch(() => toast("Network error during sign-in.", "error"));
}
window.handleGoogleSignIn = handleGoogleSignIn;

function onSignedIn(user) {
    $("#userAvatar").src = user.picture || "";
    $("#userName").textContent = user.name || "User";
    $("#userChip").classList.remove("hidden");
    const gBtn = $("#googleSignInBtn");
    if (gBtn) gBtn.style.display = "none";

    // Check if profile is already saved in localStorage
    const saved = localStorage.getItem("smartbite_profile");
    if (saved) {
        userProfile = JSON.parse(saved);
        showView("dashboard");
        loadAnalysis();
    } else {
        showView("profile");
    }
}

// ── Init ────────────────────────────────────────────────────────
window.addEventListener("load", () => {
    // Check server session
    fetch("/api/auth/me")
        .then((r) => r.json())
        .then((data) => {
            if (data.authenticated) onSignedIn(data.user);
        })
        .catch(() => {});

    // Render Google button or demo button
    if (GOOGLE_CLIENT_ID && typeof google !== "undefined") {
        google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleSignIn,
        });
        google.accounts.id.renderButton($("#googleSignInBtn"), {
            theme: "filled_black", size: "medium", shape: "pill",
        });
    } else {
        createDemoButton();
    }
});

function createDemoButton() {
    const btn = document.createElement("button");
    btn.className = "btn-link";
    btn.style.cssText = "color:var(--c-primary-lt);font-weight:600;font-size:.85rem";
    btn.textContent = "🔑 Demo Sign In";
    btn.addEventListener("click", () => {
        const name = prompt("Enter your name:");
        if (!name) return;
        const user = { name, email: "", picture: "" };
        fetch("/api/auth/google", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential: "h." + btoa(JSON.stringify(user)) + ".s" }),
        })
            .then((r) => r.json())
            .then((d) => { if (d.success) onSignedIn(d.user); });
    });
    $("#googleSignInBtn").appendChild(btn);
}

// ── Logout ──────────────────────────────────────────────────────
$("#btnLogout").addEventListener("click", () => {
    fetch("/api/auth/logout", { method: "POST" }).then(() => {
        $("#userChip").classList.add("hidden");
        const gBtn = $("#googleSignInBtn");
        if (gBtn) gBtn.style.display = "block";
        showView("landing");
    });
});

// ── Profile Form ────────────────────────────────────────────────
$("#profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    userProfile = {
        age:      $("#pAge").value,
        weight:   $("#pWeight").value,
        height:   $("#pHeight").value,
        goal:     $("#pGoal").value,
        activity: $("#pActivity").value,
        diet:     $("#pDiet").value || "None",
        allergies:$("#pAllergies").value || "None",
    };
    localStorage.setItem("smartbite_profile", JSON.stringify(userProfile));
    showView("dashboard");
    loadAnalysis();
});

// ── Load Health Analysis ────────────────────────────────────────
async function loadAnalysis() {
    if (!userProfile) return;
    try {
        const res = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(userProfile),
        });
        const data = await res.json();
        if (data.success) {
            const a = data.analysis;
            $("#statBMI").textContent = parseFloat(a.bmi).toFixed(1);
            $("#statCal").textContent = a.daily_calories;
            $("#statProtein").textContent = a.protein_g + "g";
            $("#statWater").textContent = parseFloat(a.water_liters).toFixed(1) + "L";

            // Show a random tip
            if (a.tips && a.tips.length) {
                const tip = a.tips[Math.floor(Math.random() * a.tips.length)];
                $("#tipsText").textContent = tip;
                $("#tipsBanner").classList.remove("hidden");
            }
        }
    } catch (err) {
        console.warn("Analysis failed:", err);
    }
}

// ── Meal Generation ─────────────────────────────────────────────
$("#mealForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btnLabel = $(".btn-label");
    const spinner  = $("#spinner");

    btnLabel.textContent = "Generating…";
    spinner.classList.remove("hidden");
    $("#btnGenerate").disabled = true;

    const payload = {
        goal:        userProfile?.goal || "Balanced",
        diet:        userProfile?.diet || "None",
        allergies:   userProfile?.allergies || "None",
        activity:    userProfile?.activity || "Moderate",
        ingredients: $("#mIngredients").value,
        mealType:    $("#mMealType").value,
        count:       $("#mCount").value,
    };

    try {
        const res = await fetch("/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (data.success && Array.isArray(data.meals)) {
            renderMeals(data.meals);
            toast("Meals generated successfully!", "success");
        } else {
            toast(data.error || "Failed to generate meals.", "error");
        }
    } catch (err) {
        toast("Server unreachable. Is the backend running?", "error");
    } finally {
        btnLabel.textContent = "✨ Generate Meals";
        spinner.classList.add("hidden");
        $("#btnGenerate").disabled = false;
    }
});

// ── Render Meal Cards ───────────────────────────────────────────
function renderMeals(meals) {
    const container = $("#mealsContainer");
    container.innerHTML = "";

    meals.forEach((m, i) => {
        const card = document.createElement("div");
        card.className = "meal-card";
        card.style.animationDelay = `${i * 0.1}s`;

        const ingredientsList = Array.isArray(m.ingredients)
            ? m.ingredients.join(", ")
            : m.ingredients || "";

        card.innerHTML = `
            <div class="meal-name">${escHtml(m.name || "Meal")}</div>
            <div class="meal-desc">${escHtml(m.description || "")}</div>
            <div class="meal-macros">
                <span class="macro-tag macro-cal">${m.calories || 0} kcal</span>
                <span class="macro-tag macro-protein">${m.protein || 0}g protein</span>
                <span class="macro-tag macro-carbs">${m.carbs || 0}g carbs</span>
                <span class="macro-tag macro-fat">${m.fat || 0}g fat</span>
            </div>
            <div class="meal-ingredients"><strong>Ingredients:</strong> ${escHtml(ingredientsList)}</div>
            <div class="meal-tip">💡 ${escHtml(m.tip || "")}</div>
        `;
        container.appendChild(card);
    });

    // Save to history
    try {
        const history = JSON.parse(localStorage.getItem("smartbite_history") || "[]");
        history.unshift({ date: new Date().toISOString(), count: meals.length });
        localStorage.setItem("smartbite_history", JSON.stringify(history.slice(0, 30)));
    } catch (_) {}
}

function escHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ── Edit Profile ────────────────────────────────────────────────
$("#btnEditProfile").addEventListener("click", () => {
    // Prefill form with saved data
    if (userProfile) {
        $("#pAge").value = userProfile.age || "";
        $("#pWeight").value = userProfile.weight || "";
        $("#pHeight").value = userProfile.height || "";
        $("#pGoal").value = userProfile.goal || "";
        $("#pActivity").value = userProfile.activity || "";
        $("#pDiet").value = userProfile.diet || "";
        $("#pAllergies").value = userProfile.allergies || "";
    }
    showView("profile");
});
