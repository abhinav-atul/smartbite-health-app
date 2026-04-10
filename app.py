"""
SmartBite — AI-Powered Food & Health Assistant
==============================================
Backend server using Flask + Google Gemini API + Google Sign-In.
Designed for the AMD Slingshot Food & Health Challenge.
"""

import os
import json
import logging
import re
from datetime import datetime
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3-flash-preview")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartbite")

# ---------------------------------------------------------------------------
# Prompt Engineering
# ---------------------------------------------------------------------------
MEAL_PROMPT = """You are SmartBite, a world-class AI nutritionist.
Generate exactly {count} meal suggestions based on the user profile below.

RULES:
- Each meal MUST include: name, short description, ingredient list, approximate
  calories, protein (g), carbs (g), fat (g), and one motivational health tip.
- Respond ONLY with a valid JSON array. No markdown, no explanation outside JSON.
- Each object schema: {{"name":"","description":"","ingredients":[],"calories":0,
  "protein":0,"carbs":0,"fat":0,"tip":"","mealType":""}}

USER PROFILE:
- Name: {name}
- Goal: {goal}
- Diet: {diet}
- Allergies: {allergies}
- Activity Level: {activity}
- Meal Type Requested: {meal_type}
- Available Ingredients: {ingredients}
- Time of Day: {time_of_day}

Generate the JSON array now:"""

ANALYSIS_PROMPT = """You are SmartBite, an expert nutritionist AI.
A user wants a quick health analysis. Respond ONLY with valid JSON.

User Info:
- Age: {age}, Weight: {weight} kg, Height: {height} cm
- Goal: {goal}, Activity: {activity}

Respond with this exact JSON schema:
{{"bmi": <float>, "bmi_category": "<string>", "daily_calories": <int>,
  "protein_g": <int>, "carbs_g": <int>, "fat_g": <int>,
  "water_liters": <float>, "tips": ["<tip1>","<tip2>","<tip3>"]}}"""

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sanitize(text: str, max_len: int = 500) -> str:
    """Strip and truncate user input."""
    if not text:
        return ""
    return re.sub(r"[<>{}]", "", text.strip()[:max_len])


def get_time_of_day() -> str:
    """Return contextual time label."""
    hour = datetime.now().hour
    if hour < 11:
        return "morning (breakfast time)"
    elif hour < 15:
        return "afternoon (lunch time)"
    elif hour < 19:
        return "evening (snack / early dinner)"
    return "night (dinner time)"


def extract_json(text: str):
    """Extract JSON from Gemini response, handling markdown fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)

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
# Auth endpoints – Google Sign-In
# ---------------------------------------------------------------------------

@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    """Verify Google ID token and establish a session."""
    try:
        data = request.get_json()
        token = data.get("credential", "")

        if GOOGLE_CLIENT_ID:
            user_info = id_token.verify_oauth2_token(
                token, google_requests.Request(), GOOGLE_CLIENT_ID
            )
        else:
            # Demo / fallback: decode JWT payload without verification
            import base64
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            user_info = json.loads(base64.urlsafe_b64decode(payload))

        session["user"] = {
            "name": user_info.get("name", "User"),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        }
        return jsonify({"success": True, "user": session["user"]})
    except Exception as e:
        logger.exception("Auth error")
        return jsonify({"success": False, "error": str(e)}), 401


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/auth/me")
def me():
    if "user" in session:
        return jsonify({"authenticated": True, "user": session["user"]})
    return jsonify({"authenticated": False})

# ---------------------------------------------------------------------------
# Core API — Meal Recommendations
# ---------------------------------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend():
    """Generate AI-powered meal recommendations."""
    try:
        data = request.get_json()
        goal        = sanitize(data.get("goal", ""))
        diet        = sanitize(data.get("diet", ""))
        ingredients = sanitize(data.get("ingredients", ""), 1000)
        allergies   = sanitize(data.get("allergies", ""))
        activity    = sanitize(data.get("activity", ""))
        meal_type   = sanitize(data.get("mealType", "Any"))
        count       = min(int(data.get("count", 3)), 5)
        name        = session.get("user", {}).get("name", "Friend")

        if not goal or not ingredients:
            return jsonify({"success": False,
                            "error": "Please provide your goal and ingredients."}), 400

        prompt = MEAL_PROMPT.format(
            count=count, name=name, goal=goal, diet=diet,
            allergies=allergies or "None", activity=activity or "Moderate",
            meal_type=meal_type, ingredients=ingredients,
            time_of_day=get_time_of_day(),
        )

        response = model.generate_content(prompt)
        meals = extract_json(response.text)
        return jsonify({"success": True, "meals": meals})
    except json.JSONDecodeError:
        logger.warning("Gemini returned non-JSON: %s", response.text[:200])
        return jsonify({"success": False,
                        "error": "AI returned an unexpected format. Please try again."}), 502
    except Exception as e:
        logger.exception("Recommendation error")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------------------------
# Health Analysis API
# ---------------------------------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Quick health metrics analysis via Gemini."""
    try:
        data = request.get_json()
        age      = int(data.get("age", 25))
        weight   = float(data.get("weight", 70))
        height   = float(data.get("height", 170))
        goal     = sanitize(data.get("goal", "Maintenance"))
        activity = sanitize(data.get("activity", "Moderate"))

        prompt = ANALYSIS_PROMPT.format(
            age=age, weight=weight, height=height,
            goal=goal, activity=activity,
        )
        response = model.generate_content(prompt)
        analysis = extract_json(response.text)
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        logger.exception("Analysis error")
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
