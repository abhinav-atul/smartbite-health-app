# 🍏 SmartBite — AI Food & Health Assistant

A smart, context-aware web application that helps individuals **make better food choices and build healthier eating habits** by leveraging user data, dietary context, and AI-powered analysis.

---

## Chosen Vertical

**Food & Health App** — *"Design a smart solution that helps individuals make better food choices and build healthier eating habits by leveraging available data, user behavior, or contextual inputs."*

---

## Approach & Logic

SmartBite acts as a **personalised AI nutritionist**. It follows a three-step contextual flow:

### 1. Authentication (Google Sign-In)
Users sign in using **Google Identity Services**. This establishes identity and enables personalised sessions.

### 2. Health Profile & Analysis
Users enter body metrics (age, weight, height), goals, activity level, dietary preferences, and allergies. The app sends this to the **Google Gemini API** which returns:
- **BMI** and BMI category
- **Recommended daily calories**, protein, carbs, and fat
- **Daily water intake** target
- **3 personalised health tips**

This data is displayed in a live stats dashboard bar.

### 3. Contextual Meal Recommendations
Users enter available ingredients and select a meal type (Breakfast / Lunch / Dinner / Snack). The system:
- Combines ingredients + profile + goal + allergies + **time of day** into a rich prompt
- Sends it to **Google Gemini 2.5 Flash**
- Receives **structured JSON** with meal name, description, macronutrient breakdown, and a health tip
- Renders interactive, animated meal cards in the UI

### Decision-Making Logic
| Context | How it's used |
|---|---|
| Health Goal | Gemini tunes calorie targets and food types |
| Allergies | Excluded from all suggestions |
| Activity Level | Adjusts macro ratios |
| Time of Day | Auto-detected; influences meal type |
| Available Ingredients | Meals built from what the user actually has |

---

## How the Solution Works

```
┌─────────────┐    Google Sign-In    ┌──────────────┐
│   Browser    │ ◄─────────────────► │  Google GIS  │
│  (Vanilla    │                     └──────────────┘
│   HTML/CSS/  │
│   JS SPA)    │ ◄── REST API ────► ┌──────────────┐     ┌────────────────┐
│              │                    │  Flask        │────►│ Google Gemini  │
└─────────────┘                    │  Backend      │◄────│ 2.5 Flash API  │
                                   └──────────────┘     └────────────────┘
                                          │
                                   ┌──────────────┐
                                   │ Google Cloud  │
                                   │ Run (Deploy)  │
                                   └──────────────┘
```

**Key API endpoints:**
| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/google` | POST | Verify Google ID token, create session |
| `/api/auth/me` | GET | Check current session |
| `/api/auth/logout` | POST | Destroy session |
| `/api/recommend` | POST | Generate meal recommendations via Gemini |
| `/api/analyze` | POST | Generate health metrics via Gemini |

---

## Google Services Used

| # | Service | Integration |
|---|---|---|
| 1 | **Google Gemini API** | Core AI brain — powers both health analysis and meal generation |
| 2 | **Google Sign-In (GIS)** | Identity & authentication via OAuth 2.0 |
| 3 | **Google Cloud Run** | Production deployment with auto-scaling |
| 4 | **Google Cloud Build** | CI/CD — rebuilds on every push to `main` |

---

## Evaluation Criteria Alignment

| Criteria | How we address it |
|---|---|
| **Code Quality** | Clean MVC separation: `app.py` (backend logic), `static/` (frontend). Well-commented, modular functions, consistent naming. |
| **Security** | API keys in env vars (never committed). Google ID token verification. Input sanitization with length limits. XSS-safe HTML rendering. |
| **Efficiency** | Lightweight stack (Flask + vanilla JS). No heavy frameworks. Single Gemini model instance reused across requests. Docker image uses `python:slim`. |
| **Testing** | Structured JSON responses enable predictable testing. Input validation on both client and server. Graceful error handling with user-facing toasts. |
| **Accessibility** | Semantic HTML5 (`nav`, `main`, `section`, `footer`). ARIA labels on all interactive elements. Keyboard-navigable forms. Responsive design (mobile ↔ desktop). |
| **Google Services** | Deep integration of 4 Google services (Gemini, Sign-In, Cloud Run, Cloud Build). |

---

## Assumptions

- Users have a modern web browser with JavaScript enabled.
- A stable internet connection is available for Gemini API calls.
- Ingredients are entered as comma-separated free text.
- The Gemini API key has available quota.
- Nutritional values from Gemini are estimates, not medical advice.

---

## Local Setup

```bash
git clone https://github.com/abhinav-atul/smartbite-health-app.git
cd smartbite-health-app
pip install -r requirements.txt
echo GEMINI_API_KEY=your_key_here > .env
python app.py
# Open http://localhost:5000
```

## Cloud Run Deployment

```bash
gcloud run deploy smartbite --source . --port 5000 \
  --set-env-vars GEMINI_API_KEY=your_key \
  --allow-unauthenticated
```
