import os
import json
from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

# Ensure the API key is set
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

prompt_template = """
You are SmartBite, a highly intelligent and supportive Food & Health AI assistant. 
A user has provided the following information:

Current Goals: {goals}
Dietary Preferences/Restrictions: {diet}
Available Ingredients: {ingredients}

Based on this, suggest 2 or 3 healthy, simple meals they can make. Format your response cleanly in HTML. Use headings (<h3>), bullet points (<ul><li>), and strong tags (<strong>). Do not include ` ```html ` markdown wrappers, just return the raw HTML content. Keep it encouraging and engaging to Wow the user.
"""

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        goals = data.get('goals', '')
        diet = data.get('diet', '')
        ingredients = data.get('ingredients', '')

        prompt = prompt_template.format(goals=goals, diet=diet, ingredients=ingredients)

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return jsonify({
            "success": True,
            "recommendation": response.text.replace("```html","").replace("```","")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Local dev server
    app.run(debug=True, port=5000)
