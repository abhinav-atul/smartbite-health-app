"""
SmartBite — AI-Powered Food & Health Assistant
==============================================
Backend server using Flask + Google Gemini API + Google Sign-In.
Designed for the AMD Slingshot Food & Health Challenge.

Google Services integrated:
    1. Google Gemini API (generative AI)
    2. Google Sign-In (OAuth 2.0 identity)
    3. Google Cloud Run (serverless deployment)
    4. Google Cloud Build (CI/CD pipeline)
    5. Google Cloud Logging (structured JSON logs)
    6. Google Fonts (typography)
"""

import os
import json
import logging
import re
import base64
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

from flask import Flask, Response, request, jsonify, send_from_directory, session
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
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request limit

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Structured JSON logging (auto-ingested by Google Cloud Logging on Cloud Run)
logging.basicConfig(
    level=logging.INFO,
    format='{"severity":"%(levelname)s","timestamp":"%(asctime)s",'
           '"logger":"%(name)s","message":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("smartbite")

# ---------------------------------------------------------------------------
# Security — HTTP Headers (OWASP best practices)
# ---------------------------------------------------------------------------

@app.after_request
def set_security_headers(response: Response) -> Response:
    """Attach security headers to every response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://accounts.google.com https://www.googletagmanager.com https://www.google-analytics.com 'unsafe-inline'; "
        "style-src 'self' https://fonts.googleapis.com https://accounts.google.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' https://*.googleusercontent.com data:; "
        "connect-src 'self' https://accounts.google.com https://www.google-analytics.com; "
        "frame-src https://accounts.google.com; "
    )
    return response

# ---------------------------------------------------------------------------
# Prompt Engineering
# ---------------------------------------------------------------------------
MEAL_PROMPT: str = """You are SmartBite, a world-class AI nutritionist.
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

ANALYSIS_PROMPT: str = """You are SmartBite, an expert nutritionist AI.
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
    """Sanitize user input by stripping whitespace, removing dangerous
    characters, and enforcing a maximum length limit.

    Args:
        text: Raw user input string.
        max_len: Maximum allowed character length (default 500).

    Returns:
        Cleaned and truncated string safe for prompt injection.
    """
    if not text:
        return ""
    cleaned = re.sub(r"[<>{}\[\]\\]", "", text.strip())
    return cleaned[:max_len]


def get_time_of_day() -> str:
    """Return a human-readable time-of-day label for contextual meal
    recommendations based on the server's current local time.

    Returns:
        Descriptive string like 'morning (breakfast time)'.
    """
    hour: int = datetime.now().hour
    if hour < 11:
        return "morning (breakfast time)"
    elif hour < 15:
        return "afternoon (lunch time)"
    elif hour < 19:
        return "evening (snack / early dinner)"
    return "night (dinner time)"


def extract_json(text: str) -> Union[list, dict]:
    """Extract and parse JSON from Gemini response text, gracefully
    handling markdown code fences that the model sometimes wraps around
    its JSON output.

    Args:
        text: Raw response text from Gemini.

    Returns:
        Parsed Python object (list or dict).

    Raises:
        json.JSONDecodeError: If the cleaned text is not valid JSON.
    """
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def validate_required(data: Optional[Dict], fields: list) -> Optional[Tuple[Dict, int]]:
    """Validate that a JSON request body contains all required fields.

    Args:
        data: Parsed JSON body (may be None).
        fields: List of required field names.

    Returns:
        None if valid, or a (jsonify error response, status code) tuple.
    """
    if not data:
        return jsonify({"success": False, "error": "Request body is required."}), 400
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}"
        }), 400
    return None

# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------

@app.route("/")
def serve_index() -> Response:
    """Serve the main single-page application."""
    return send_from_directory("static", "index.html")


@app.route("/api/config")
def config() -> Response:
    """Expose non-secret configuration to the frontend.
    Only the Google Client ID is shared — never API keys."""
    return jsonify({"googleClientId": GOOGLE_CLIENT_ID})


@app.route("/<path:path>")
def serve_static(path: str) -> Response:
    """Serve any static asset (CSS, JS, images)."""
    return send_from_directory("static", path)

# ---------------------------------------------------------------------------
# Auth endpoints — Google Sign-In (OAuth 2.0)
# ---------------------------------------------------------------------------

@app.route("/api/auth/google", methods=["POST"])
def google_auth() -> Tuple[Response, int]:
    """Verify a Google ID token and establish a server-side session.

    When GOOGLE_CLIENT_ID is configured, the token is cryptographically
    verified using Google's public keys. Otherwise, a demo fallback
    decodes the JWT payload without verification (development only).

    Returns:
        JSON with user info on success, error on failure.
    """
    try:
        data: Dict = request.get_json()
        token: str = data.get("credential", "")

        if not token:
            return jsonify({"success": False, "error": "No credential provided."}), 400

        if GOOGLE_CLIENT_ID:
            # Production: cryptographic verification via Google's public keys
            user_info = id_token.verify_oauth2_token(
                token, google_requests.Request(), GOOGLE_CLIENT_ID
            )
            logger.info("Google Sign-In verified for: %s", user_info.get("email"))
        else:
            # Development: decode JWT payload without verification
            payload: str = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            user_info = json.loads(base64.urlsafe_b64decode(payload))
            logger.info("Demo sign-in for: %s", user_info.get("name"))

        session["user"] = {
            "name": user_info.get("name", "User"),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        }
        return jsonify({"success": True, "user": session["user"]}), 200
    except Exception as e:
        logger.exception("Auth error: %s", str(e))
        return jsonify({"success": False, "error": "Authentication failed."}), 401


@app.route("/api/auth/logout", methods=["POST"])
def logout() -> Response:
    """Destroy the current user session."""
    session.clear()
    logger.info("User logged out.")
    return jsonify({"success": True})


@app.route("/api/auth/me")
def me() -> Response:
    """Check if the current request has an active session."""
    if "user" in session:
        return jsonify({"authenticated": True, "user": session["user"]})
    return jsonify({"authenticated": False})

# ---------------------------------------------------------------------------
# Core API — Meal Recommendations (Google Gemini)
# ---------------------------------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend() -> Tuple[Response, int]:
    """Generate AI-powered meal recommendations using Google Gemini.

    Accepts user profile context (goal, diet, allergies, activity level,
    available ingredients) and returns structured meal suggestions with
    full macronutrient breakdowns.

    Returns:
        JSON array of meal objects on success.
    """
    try:
        data: Dict = request.get_json()

        # Validate required inputs
        err = validate_required(data, ["goal", "ingredients"])
        if err:
            return err

        goal: str        = sanitize(data.get("goal", ""))
        diet: str        = sanitize(data.get("diet", ""))
        ingredients: str = sanitize(data.get("ingredients", ""), 1000)
        allergies: str   = sanitize(data.get("allergies", ""))
        activity: str    = sanitize(data.get("activity", ""))
        meal_type: str   = sanitize(data.get("mealType", "Any"))
        count: int       = min(int(data.get("count", 3)), 5)
        name: str        = session.get("user", {}).get("name", "Friend")

        prompt: str = MEAL_PROMPT.format(
            count=count, name=name, goal=goal, diet=diet,
            allergies=allergies or "None", activity=activity or "Moderate",
            meal_type=meal_type, ingredients=ingredients,
            time_of_day=get_time_of_day(),
        )

        logger.info("Generating %d meals for goal=%s, diet=%s", count, goal, diet)
        response = model.generate_content(prompt)
        meals: list = extract_json(response.text)

        logger.info("Successfully generated %d meals.", len(meals))
        return jsonify({"success": True, "meals": meals}), 200
    except json.JSONDecodeError:
        logger.warning("Gemini returned non-JSON response.")
        return jsonify({"success": False,
                        "error": "AI returned an unexpected format. Please try again."}), 502
    except Exception as e:
        logger.exception("Recommendation error: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------------------------
# Health Analysis API (Google Gemini)
# ---------------------------------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze() -> Tuple[Response, int]:
    """Perform a quick health analysis using Google Gemini.

    Calculates BMI, recommended daily calorie intake, macronutrient
    targets, water intake, and personalised health tips.

    Returns:
        JSON with health metrics on success.
    """
    try:
        data: Dict = request.get_json()

        # Validate required inputs
        err = validate_required(data, ["age", "weight", "height"])
        if err:
            return err

        age: int        = int(data.get("age", 25))
        weight: float   = float(data.get("weight", 70))
        height: float   = float(data.get("height", 170))
        goal: str       = sanitize(data.get("goal", "Maintenance"))
        activity: str   = sanitize(data.get("activity", "Moderate"))

        # Input range validation
        if not (10 <= age <= 120):
            return jsonify({"success": False, "error": "Age must be between 10 and 120."}), 400
        if not (20 <= weight <= 400):
            return jsonify({"success": False, "error": "Weight must be between 20 and 400 kg."}), 400
        if not (100 <= height <= 280):
            return jsonify({"success": False, "error": "Height must be between 100 and 280 cm."}), 400

        prompt: str = ANALYSIS_PROMPT.format(
            age=age, weight=weight, height=height,
            goal=goal, activity=activity,
        )

        logger.info("Analyzing health for age=%d, weight=%.1f, height=%.1f", age, weight, height)
        response = model.generate_content(prompt)
        analysis: dict = extract_json(response.text)

        logger.info("Health analysis complete: BMI=%.1f", analysis.get("bmi", 0))
        return jsonify({"success": True, "analysis": analysis}), 200
    except (ValueError, TypeError) as e:
        logger.warning("Invalid input for analysis: %s", str(e))
        return jsonify({"success": False, "error": "Invalid numeric input."}), 400
    except Exception as e:
        logger.exception("Analysis error: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------------------------------------------------------
# Health Check (for Google Cloud Run)
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health() -> Response:
    """Health check endpoint used by Google Cloud Run to verify
    the container is running and responsive."""
    return jsonify({"status": "healthy", "service": "smartbite"})

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port: int = int(os.environ.get("PORT", 5000))
    logger.info("Starting SmartBite on port %d", port)
    app.run(debug=True, host="0.0.0.0", port=port)
