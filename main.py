from flask import Flask, render_template, request, session, redirect
from house_crew import HouseCrew
import os

app = Flask(__name__)
app.secret_key = "house_secret"

crew = HouseCrew()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    area = request.form["area"]
    budget = request.form["budget"]
    rooms = request.form["rooms"]
    style = request.form["style"]
    furniture = request.form["furniture"]

    # ask AI
    result = crew.generate_plan(area, budget, rooms, style, furniture)

    return render_template("result.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
