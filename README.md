# 🍏 SmartBite — AI Food & Health Assistant

> **Note:** This project was created in the AMD Slingshot regional ideathon, in the promptathon, within 2 hours.

🚀 **Live Server:** [https://smartbite-health-app-994936472168.europe-west1.run.app/](https://smartbite-health-app-994936472168.europe-west1.run.app/)

A smart, context-aware web application that helps individuals **make better food choices and build healthier eating habits** by leveraging user data, dietary context, and AI-powered analysis.

---

## Chosen Vertical

**Food & Health App** — *"Design a smart solution that helps individuals make better food choices and build healthier eating habits by leveraging available data, user behavior, or contextual inputs."*

---

## Approach & Logic

SmartBite acts as a **personalised AI nutritionist**. It follows a three-step contextual flow:

### 1. Authentication (Google Sign-In — Optional)
Users can optionally sign in using **Google Identity Services (OAuth 2.0)**. Signed-in users get personalised greetings and session persistence. Guest users can use the full app without signing in.

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
- Sends it to **Google Gemini** with structured JSON output constraints
- Receives **structured JSON** with meal name, description, macronutrient breakdown, and a health tip
- Renders interactive, animated meal cards with colour-coded macro tags

### Decision-Making Logic
| Context | How it's used |
|---|---|
| Health Goal | Gemini tunes calorie targets and food types (e.g. high-protein for muscle gain) |
| Allergies | Strictly excluded from all meal suggestions |
| Diet Type | Respects dietary constraints (Vegan, Keto, etc.) |
| Activity Level | Adjusts macronutrient ratios and portion sizes |
| Time of Day | Auto-detected from server clock; influences meal type recommendations |
| Available Ingredients | Meals are built only from what the user actually has |
| Body Metrics | BMI and caloric needs calculated for personalised targets |

---

## How the Solution Works

```
┌─────────────┐    Google Sign-In    ┌──────────────┐
│   Browser    │ ◄─────────────────► │  Google GIS  │
│  (Vanilla    │                     └──────────────┘
│   HTML/CSS/  │    Google Analytics  ┌──────────────┐
│   JS SPA)    │ ──────────────────► │  Google Tag  │
│              │                     │  Manager     │
│              │ ◄── REST API ────► ┌──────────────┐     ┌────────────────┐
│              │                    │  Flask        │────►│ Google Gemini  │
└─────────────┘                    │  Backend      │◄────│ API            │
                                   └──────────────┘     └────────────────┘
                                          │
                                   ┌──────────────┐     ┌────────────────┐
                                   │ Google Cloud  │◄────│ Google Cloud   │
                                   │ Run           │     │ Build (CI/CD)  │
                                   └──────────────┘     └────────────────┘
                                          │
                                   ┌──────────────┐
                                   │ Google Cloud  │
                                   │ Logging       │
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
| `/api/config` | GET | Expose non-secret config (Client ID) |
| `/api/health` | GET | Cloud Run health check |

---

## Google Services Used

| # | Service | Where | Purpose |
|---|---|---|---|
| 1 | **Google Gemini API** | `app.py` | Core AI — powers health analysis and meal generation with structured JSON output |
| 2 | **Google Sign-In (GIS)** | `index.html`, `script.js`, `app.py` | OAuth 2.0 identity with server-side token verification |
| 3 | **Google Cloud Run** | Deployment | Serverless container hosting with auto-scaling |
| 4 | **Google Cloud Build** | CI/CD | Automatic build & deploy on every `git push` to `main` |
| 5 | **Google Cloud Logging** | `app.py` | Structured JSON logs auto-ingested by Cloud Logging on Cloud Run |
| 6 | **Google Analytics** | `index.html` | User engagement and usage analytics via gtag.js |
| 7 | **Google Fonts** | `index.html`, `style.css` | Premium typography (Outfit + Inter) |

---

## Security Implementation

SmartBite follows **OWASP best practices** for web application security:

| Security Measure | Implementation |
|---|---|
| **Content Security Policy (CSP)** | Strict CSP header restricting script/style/image sources |
| **HSTS** | `Strict-Transport-Security` enforces HTTPS |
| **X-Frame-Options** | Set to `DENY` — prevents clickjacking |
| **X-Content-Type-Options** | Set to `nosniff` — prevents MIME sniffing |
| **X-XSS-Protection** | Enabled with `mode=block` |
| **Referrer-Policy** | `strict-origin-when-cross-origin` |
| **Permissions-Policy** | Camera, microphone, and geolocation disabled |
| **Input Sanitization** | All user inputs stripped of `< > { } [ ] \` and length-limited |
| **Input Validation** | Server-side range checks on numeric fields (age, weight, height) |
| **Request Size Limit** | `MAX_CONTENT_LENGTH` set to 1 MB |
| **API Key Protection** | Keys stored in environment variables, never in source code |
| **XSS Prevention** | Client-side `escHtml()` function for all dynamic content |
| **Token Verification** | Google ID tokens verified cryptographically via `google-auth` library |

---

## Evaluation Criteria Alignment

| Criteria | How we address it |
|---|---|
| **Code Quality** | Type-annotated Python functions with docstrings. Clean MVC separation. Modular utility functions. Consistent naming conventions throughout. |
| **Security** | Full OWASP header suite (CSP, HSTS, X-Frame-Options). Input sanitization + range validation. API keys in env vars. Cryptographic token verification. XSS-safe rendering. |
| **Efficiency** | Lightweight stack (Flask + vanilla JS, zero frontend frameworks). Single Gemini model instance reused. Docker uses `python:slim`. No unnecessary dependencies. |
| **Testing** | Comprehensive input validation on both client and server with descriptive error messages. Structured JSON API responses enable predictable testing. Health check endpoint for monitoring. |
| **Accessibility** | Semantic HTML5 (`nav`, `main`, `section`, `footer`). ARIA labels on interactive elements. Keyboard-navigable forms. Responsive design. `color-scheme: dark` meta tag. |
| **Google Services** | Deep integration of **7 Google services**: Gemini API, Sign-In, Cloud Run, Cloud Build, Cloud Logging, Analytics, and Fonts. |

---

## Assumptions

- Users have a modern web browser with JavaScript enabled.
- A stable internet connection is available for Gemini API calls.
- Ingredients are entered as comma-separated free text.
- The Gemini API key has available quota for the free tier.
- Nutritional values from Gemini are approximate estimates, not medical advice.

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
