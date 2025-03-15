import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload size

# Create uploads directory if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize OpenAI client - simplified initialization to avoid parameter issues
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Define the steps in the wizard
WIZARD_STEPS = ["context", "references", "plan", "script", "edit", "short_video", "complete"]

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

    # For GET requests, we keep all existing session data
    return render_template("context.html", step=1, total_steps=len(WIZARD_STEPS) - 1)


@app.route("/references", methods=["GET", "POST"])
def references():
    """Second step: References and resources."""
    # Check if previous step was completed
    if "topic" not in session:
        flash("Please complete the previous step first.", "warning")
        return redirect(url_for("context"))

    if request.method == "POST":
        # Save web search preference
        session["use_web_search"] = "use_web_search" in request.form

        # Handle removal of previously uploaded files
        if "files_to_remove" in request.form and request.form.get("files_to_remove"):
            files_to_remove = request.form.get("files_to_remove").split(",")
            if files_to_remove and session.get("reference_files"):
                # Filter out files that should be removed
                updated_files = []
                for file in session.get("reference_files", []):
                    if file["stored_name"] not in files_to_remove:
                        updated_files.append(file)
                    else:
                        # Delete the file from the filesystem
                        try:
                            os.remove(file["path"])
                        except (OSError, FileNotFoundError):
                            # File might not exist, just continue
                            pass

                session["reference_files"] = updated_files

        # Handle file uploads - append to existing files if any
        if "reference_files" in request.files and any(request.files.getlist("reference_files")):
            uploaded_files = session.get("reference_files", [])
            files = request.files.getlist("reference_files")
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    # Generate a unique filename to prevent collisions
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                    file.save(file_path)

                    # Store file info in session
                    uploaded_files.append(
                        {
                            "original_name": filename,
                            "stored_name": unique_filename,
                            "path": file_path,
                            "type": filename.rsplit(".", 1)[1].lower(),
                        }
                    )

            session["reference_files"] = uploaded_files
            if uploaded_files:
                flash(f"Successfully uploaded {len(files)} file(s) to the server.", "success")

        # Handle web links - append to existing links if any
        if "web_links[]" in request.form and any(
            link.strip() for link in request.form.getlist("web_links[]")
        ):
            web_links = session.get("web_links", [])
            links = request.form.getlist("web_links[]")
            descriptions = request.form.getlist("web_link_descriptions[]")

            new_links_count = 0
            for i in range(len(links)):
                if links[i].strip():  # Only add non-empty links
                    web_links.append(
                        {
                            "url": links[i],
                            "description": descriptions[i] if i < len(descriptions) else "",
                        }
                    )
                    new_links_count += 1

            session["web_links"] = web_links
            if new_links_count > 0:
                flash(f"Successfully added {new_links_count} web link(s).", "success")

        # Proceed to next step
        return redirect(url_for("plan"))

    return render_template("references.html", step=2, total_steps=len(WIZARD_STEPS) - 1)


@app.route("/plan", methods=["GET", "POST"])
def plan():
    """Third step: Plan the video script."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    if request.method == "POST":
        # Save plan data
        session["plan_notes"] = request.form.get("plan_notes", "")
        session["structure_preference"] = request.form.get("structure_preference", "")
        session["key_points"] = request.form.getlist("key_points[]")

        # Proceed to next step
        return redirect(url_for("script"))

    return render_template("plan.html", step=3, total_steps=len(WIZARD_STEPS) - 1)


# Add routes for other steps (to be implemented)


@app.route("/save_workflow", methods=["POST"])
def save_workflow():
    """Save the current workflow data to a file."""
    # TODO: Implement saving logic
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
