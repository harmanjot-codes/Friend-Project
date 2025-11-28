import google.generativeai as genai
import os
import json

# Load API key from Replit Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing. Add it in Replit Secrets!")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class HouseCrew:

    def generate_plan(self, area, budget, rooms, style, furniture):
        """
        Generates a complete house plan using Gemini AI.
        """

        model = genai.GenerativeModel("gemini-pro")

        prompt = f"""
        You are an expert architect AI.
        Create a full HOUSE CONSTRUCTION PLAN based on the following details:

        🔹 Total Area: {area} sq ft
        🔹 Budget: ₹{budget}
        🔹 Number of Rooms Needed: {rooms}
        🔹 Preferred Style: {style}
        🔹 Include Furniture in Plan: {furniture}

        Provide the output ONLY in pure JSON format:

        {{
            "summary": "Short 3-4 line summary of the full house plan",
            "room_plan": [
                {{"room": "Bedroom 1", "size": "12x14 ft"}},
                {{"room": "Kitchen", "size": "10x12 ft"}}
            ],
            "materials": [
                "Bricks - 5000 units",
                "Cement - 30 bags"
            ],
            "estimated_cost": "₹xx,xx,xxx",
            "design_features": [
                "Ventilated rooms",
                "Modern lighting"
            ]
        }}
        """

        # Generate the response
        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # If Gemini returns fenced code block like ```json ... ```
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            raw_text = raw_text.replace("json", "").strip()

        try:
            return json.loads(raw_text)
        except Exception:
            return {
                "summary": "AI could not fully generate the JSON. Showing fallback output.",
                "room_plan": [],
                "materials": [],
                "estimated_cost": "N/A",
                "design_features": []
            }
