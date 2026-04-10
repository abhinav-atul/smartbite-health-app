# 🍏 SmartBite — AI-Powered Food & Health Assistant

SmartBite is an intelligent, context-aware web application that helps individuals build healthier eating habits. It uses **Google Gemini** to generate personalised meal recommendations based on the user's health goals, dietary restrictions, available ingredients, allergies, and activity level.

## Vertical

**Food & Health App** — *"Design a smart solution that helps individuals make better food choices and build healthier eating habits by leveraging available data, user behavior, or contextual inputs."*

## ✨ Google Services Integration

| Service | Purpose |
|---|---|
| **Google Gemini API** | Core AI engine — analyses user context and generates creative, nutritious meal plans |
| **Google Sign-In (GIS)** | Secure, one-tap authentication via Google Identity Services |
| **Google Cloud Run** | Serverless deployment target with auto-scaling |

## 🧠 Approach & Logic

1. **Authentication Gate** — Users sign in with their Google account (or use demo mode). This creates a secure server-side session.
2. **Smart Onboarding Form** — Collects structured inputs: health goals (dropdown), activity level, dietary preferences, allergies, and available ingredients.
3. **AI-Powered Recommendations** — A carefully engineered prompt is sent to Google Gemini 2.5 Flash. The model returns 3 personalised, creative meal ideas with ingredients, estimated calories, and health tips.
4. **Dynamic Results Dashboard** — The AI response is rendered as rich HTML with smooth transitions and animations.
5. **Meal History** — Past recommendations are saved to `localStorage` for future reference.

### Architecture Diagram

```
┌────────────┐       ┌──────────────┐       ┌─────────────────┐
│  Frontend   │──────►│  Flask API   │──────►│  Google Gemini  │
│  (Vanilla)  │◄──────│  (Python)    │◄──────│  2.5 Flash      │
└────────────┘       └──────────────┘       └─────────────────┘
       │                     │
       │                     ▼
       │              ┌──────────────┐
       └─────────────►│ Google GIS   │
                      │ (Sign-In)    │
                      └──────────────┘
```

## 🏗️ How It Works

1. User lands on the welcome page featuring SmartBite's capabilities.
2. User signs in via **Google Sign-In** (or demo mode).
3. User fills in their profile: goals, activity, diet, allergies, and fridge contents.
4. Backend constructs a rich prompt and queries **Gemini 2.5 Flash**.
5. Frontend smoothly transitions to the results view with animated, styled meal cards.

## 🔒 Security

- API keys stored in environment variables, never committed (`.gitignore`).
- Google ID tokens verified server-side via `google-auth`.
- User input sanitized and length-limited before prompt injection.
- Session management via Flask's signed cookies.

## ♿ Accessibility

- Semantic HTML5 elements (`<nav>`, `<main>`, `<section>`, `<footer>`).
- ARIA labels on interactive elements.
- Keyboard-navigable form with proper focus states.
- Responsive design that works on mobile, tablet, and desktop.

## 📫 Assumptions

- Modern web browser with JavaScript enabled.
- Stable internet connection for API calls.
- Ingredients provided as free-text input.
- Google Gemini API key is valid and has quota available.

## 🚀 Local Setup

```bash
# 1. Clone
git clone https://github.com/abhinav-atul/smartbite-health-app.git
cd smartbite-health-app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
#    Create a .env file:
echo GEMINI_API_KEY=your_key_here > .env

# 4. Run
python app.py

# 5. Open http://localhost:5000
```

## ☁️ Cloud Run Deployment

```bash
gcloud run deploy smartbite \
  --source . \
  --port 5000 \
  --set-env-vars GEMINI_API_KEY=your_key_here \
  --allow-unauthenticated
```
