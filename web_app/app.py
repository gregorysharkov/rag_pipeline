import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

# Initialize OpenAI client - simplified initialization to avoid parameter issues
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Define the steps in the wizard
WIZARD_STEPS = ["context", "references", "plan", "script", "edit", "short_video", "complete"]


@app.route("/")
def index():
    """Landing page that redirects to the first step of the wizard."""
    # Reset session data when starting a new workflow
    session.clear()
    return redirect(url_for("context"))


@app.route("/context", methods=["GET", "POST"])
def context():
    """First step of the wizard: Collect context information."""
    if request.method == "POST":
        # Save form data to session
        session["topic"] = request.form.get("topic", "")
        session["additional_context"] = request.form.get("additional_context", "")

        # Handle target audience (could be from dropdown or custom input)
        target_audience = request.form.get("target_audience", "")
        session["target_audience"] = target_audience

        session["content_type"] = request.form.get("content_type", "")
        session["tone"] = request.form.get("tone", "")

        # Proceed to next step
        return redirect(url_for("references"))

    return render_template("context.html", step=1, total_steps=len(WIZARD_STEPS) - 1)


@app.route("/references", methods=["GET", "POST"])
def references():
    """Second step: Web search and references."""
    # Check if previous step was completed
    if "topic" not in session:
        flash("Please complete the previous step first.")
        return redirect(url_for("context"))

    # TODO: Implement web search agent logic
    # This will be implemented in the next iteration

    return render_template("references.html", step=2, total_steps=len(WIZARD_STEPS) - 1)


# Add routes for other steps (to be implemented)


@app.route("/save_workflow", methods=["POST"])
def save_workflow():
    """Save the current workflow data to a file."""
    # TODO: Implement saving logic
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
