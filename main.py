# main.py
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import timedelta
import traceback

from crew import HouseCrew  # your crew.py HouseCrew class

app = Flask(__name__, template_folder="templates")
# Use SESSION_SECRET for Flask sessions (you already added it in Replit secrets)
app.secret_key = os.getenv("SESSION_SECRET", "dev_local_secret")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

crew = HouseCrew()


# simple default/fallback result object (safe shape for template)
def default_result():
    return {
        "summary": "No plan generated.",
        "room_plan": [],
        "materials": [],
        "estimated_cost": "N/A",
        "design_features": []
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    area = request.form.get("area", "").strip()
    budget = request.form.get("budget", "").strip()
    rooms = request.form.get("rooms", "").strip()
    style = request.form.get("style", "").strip()
    furniture = request.form.get("furniture", "").strip()

    # Try to generate plan safely
    try:
        plan = crew.generate_plan(area, budget, rooms, style, furniture)
        # If crew returned None or not a dict, replace with fallback
        if not isinstance(plan, dict):
            app.logger.warning(
                "generate_plan returned non-dict, using fallback.")
            plan = default_result()
    except Exception as e:
        # Log full traceback to console for debugging
        app.logger.error("Error generating plan: %s", str(e))
        traceback.print_exc()
        plan = default_result()

    # Pass both names so your template can use either `result` or `plan`.
    # Some templates use `result.summary` (old) while others may use `plan`.
    return render_template("result.html",
                           plan=plan,
                           result=plan,
                           area=area,
                           budget=budget,
                           rooms=rooms,
                           style=style,
                           furniture=furniture)


if __name__ == "__main__":
    print(
        "Starting app. Make sure GEMINI_API_KEY (if used) is set in environment/secrets."
    )
    app.run(host="0.0.0.0", port=5000, debug=True)
