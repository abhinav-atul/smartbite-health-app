# SmartBite - Food & Health App

SmartBite is an AI-powered lightweight web application designed to help individuals build healthier eating habits by making smart, context-aware food choices. It takes user goals, dietary restrictions, and available ingredients to propose custom, nutritious meal recommendations.

## Vertical
**Food & Health App**: "Design a smart solution that helps individuals make better food choices and build healthier eating habits by leveraging available data, user behavior, or contextual inputs."

## Approach & Logic
- **Architecture**: A minimalist, clean architecture using a Python (`Flask`) backend and a vanilla HTML/CSS/JS frontend to keep the repository under the 1 MB limit and ensure efficiency.
- **AI Integration**: The core of the app utilizes the **Google Gemini API** (Google Services) to process user inputs (context, goals, restrictions) and return structured, personalized meal recommendations. 
- **Interface**: Uses a modern two-step flow (Onboarding Form -> Intelligent Recommendations) styled with glassmorphism and smooth micro-animations.

## How it Works
1. The user inputs their health goals (e.g., Weight loss, Muscle gain).
2. The user inputs any dietary restrictions (e.g., Vegan, Keto).
3. The user lists the ingredients currently available in their fridge or pantry.
4. The backend securely constructs a tailored prompt and queries the **Gemini 1.5 Flash Model**.
5. The frontend dynamically renders the custom recipe, nutritional tips, and cooking instructions visually.

## Assumptions Made
*   The user is using a modern web browser that supports CSS variables and modern JavaScript.
*   The user has a stable internet connection for the Gemini API call.
*   The application expects ingredients in a text format.

## Local Setup Instructions
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file in the root directory and add your Google API key:
   ```env
   GEMINI_API_KEY=your_key_here
   ```
4. Run the app: `flask run` (or `python app.py`)
5. Visit `http://localhost:5000`

## Cloud Deployment (Google Cloud Run)
The application includes a `Dockerfile` and is fully ready to be deployed to Google Cloud Run natively.
