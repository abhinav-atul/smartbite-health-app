"""
SmartBite - AI-Powered Food & Health Assistant
Backend server using Flask, Google Gemini API, and Google Sign-In.
"""

import os
import json
import logging
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, session
import google.generativeai as genai
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET", os.urandom(32))

# Google service credentials
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

genai.configure(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt engineering – richer, structured output
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are SmartBite, a world-class AI nutritionist and personal chef.
You always respond with well-structured, visually appealing HTML.
Rules:
- Suggest exactly 3 meals (breakfast / lunch / dinner or 3 options).
- For EACH meal provide: a creative name wrapped in <h3>, a short description in <p>,
  a bullet list of ingredients used (<ul><li>), estimated calories in a <span class="cal-badge">,
  and a one-line health tip in <em>.
- Use semantic HTML only. No markdown fences. No <html>/<body> wrappers.
- Keep the tone warm, encouraging, and motivational.
- If ingredients are very limited, get creative and suggest easy substitutions.
"""

PROMPT_TEMPLATE = """{system}

--- User Profile ---
Name: {name}
Health Goals: {goals}
Dietary Preferences / Restrictions: {diet}
Available Ingredients: {ingredients}
Allergies: {allergies}
Activity Level: {activity}

Please generate 3 personalised, healthy meal recommendations now."""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize(text: str, max_len: int = 500) -> str:
    """Sanitize and limit user input length."""
    return text.strip()[:max_len] if text else ""


def require_auth(f):
    """Decorator that checks for a valid session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    """Verify a Google ID token and create a server session."""
    try:
        data = request.get_json()
        token = data.get("credential", "")

        if not GOOGLE_CLIENT_ID:
            # Fallback: if no client ID configured, trust the JWT payload
            # (acceptable for hackathon / demo purposes)
            import base64
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            user_info = json.loads(base64.urlsafe_b64decode(payload))
        else:
            user_info = id_token.verify_oauth2_token(
                token, google_requests.Request(), GOOGLE_CLIENT_ID
            )

        session["user"] = {
            "name": user_info.get("name", "User"),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        }
        logger.info("User signed in: %s", session["user"]["email"])
        return jsonify({"success": True, "user": session["user"]})
    except Exception as e:
        logger.exception("Google auth failed")
        return jsonify({"success": False, "error": str(e)}), 401


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"success": True})


@app.route("/api/auth/me")
def me():
    """Return current session user if any."""
    if "user" in session:
        return jsonify({"authenticated": True, "user": session["user"]})
    return jsonify({"authenticated": False})

# ---------------------------------------------------------------------------
# Core recommendation endpoint
# ---------------------------------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend():
    """Generate personalised meal recommendations via Gemini."""
    try:
        data = request.get_json()

        goals       = sanitize(data.get("goals", ""))
        diet        = sanitize(data.get("diet", ""))
        ingredients = sanitize(data.get("ingredients", ""), 1000)
        allergies   = sanitize(data.get("allergies", ""))
        activity    = sanitize(data.get("activity", ""))
        name        = session.get("user", {}).get("name", "Friend")

        if not goals or not ingredients:
            return jsonify({
                "success": False,
                "error": "Please provide at least your goals and available ingredients."
            }), 400

        prompt = PROMPT_TEMPLATE.format(
            system=SYSTEM_PROMPT,
            name=name,
            goals=goals,
            diet=diet,
            ingredients=ingredients,
            allergies=allergies,
            activity=activity,
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        html = response.text.replace("```html", "").replace("```", "")

        return jsonify({"success": True, "recommendation": html})
    except Exception as e:
        logger.exception("Recommendation generation failed")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
