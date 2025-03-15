import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename
import uuid
import random
import datetime

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
WIZARD_STEPS = [
    "context",
    "references",
    "web_search",
    "plan",
    "script",
    "edit",
    "short_video",
    "complete",
]

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

        # Proceed to next step - either web search or plan depending on setting
        if session.get("use_web_search", True):
            return redirect(url_for("web_search"))
        else:
            return redirect(url_for("plan"))

    return render_template("references.html", step=2, total_steps=len(WIZARD_STEPS) - 1)


@app.route("/web_search", methods=["GET", "POST"])
def web_search():
    """Web search step: Show search results from the web."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Skip this step if web search is disabled
    if not session.get("use_web_search", True):
        return redirect(url_for("plan"))

    if request.method == "POST":
        # Save selected search results
        selected_results = request.form.getlist("selected_results[]")
        if selected_results:
            session["selected_search_results"] = selected_results
            flash(
                f"Selected {len(selected_results)} search results to include in your script.",
                "success",
            )

        # Proceed to next step
        return redirect(url_for("plan"))

    # For GET requests, perform the web search if not already done or if refresh requested
    refresh_requested = request.args.get("refresh", "0") == "1"
    if "search_results" not in session or refresh_requested:
        # This would be replaced with actual web search functionality
        # For now, we'll use mock data
        mock_search_results = [
            {
                "id": "1",
                "title": "How to Create Engaging YouTube Videos",
                "url": "https://example.com/youtube-tips",
                "summary": "A comprehensive guide on creating engaging content for YouTube, including tips on scripting, filming, and editing.",
            },
            {
                "id": "2",
                "title": "YouTube Script Writing: Best Practices",
                "url": "https://example.com/script-writing",
                "summary": "Learn the best practices for writing effective YouTube scripts that keep viewers engaged and boost your channel's performance.",
            },
            {
                "id": "3",
                "title": f"Everything You Need to Know About {session.get('topic', 'Your Topic')}",
                "url": "https://example.com/topic-guide",
                "summary": f"An in-depth exploration of {session.get('topic', 'your topic')}, covering key concepts, recent developments, and expert insights.",
            },
            {
                "id": "4",
                "title": "Video Production Tips for Beginners",
                "url": "https://example.com/video-production",
                "summary": "Essential tips and tricks for beginners looking to improve their video production quality without expensive equipment.",
            },
            {
                "id": "5",
                "title": f"{session.get('content_type', 'Content')} Creation Guide",
                "url": "https://example.com/content-creation",
                "summary": f"A step-by-step guide to creating high-quality {session.get('content_type', 'content')} that resonates with your target audience.",
            },
        ]

        # If refreshing, add some variation to show different results
        if refresh_requested:
            random.shuffle(mock_search_results)
            # Add a couple more results to show variation
            additional_results = [
                {
                    "id": "6",
                    "title": f"Latest Trends in {session.get('topic', 'Your Field')}",
                    "url": "https://example.com/latest-trends",
                    "summary": f"Stay up-to-date with the latest developments and trends in {session.get('topic', 'your field')} for {datetime.datetime.now().year}.",
                },
                {
                    "id": "7",
                    "title": f"Expert Insights: {session.get('topic', 'Topic')} for {session.get('target_audience', 'Your Audience')}",
                    "url": "https://example.com/expert-insights",
                    "summary": f"Expert advice on creating {session.get('content_type', 'content')} about {session.get('topic', 'your topic')} specifically tailored for {session.get('target_audience', 'your target audience')}.",
                },
            ]
            mock_search_results = mock_search_results[:3] + additional_results

            flash("Search results refreshed successfully!", "success")
            # Clear previous selections when refreshing
            if "selected_search_results" in session:
                session.pop("selected_search_results")

        session["search_results"] = mock_search_results

    return render_template("web_search.html", step=3, total_steps=len(WIZARD_STEPS) - 1)


@app.route("/plan", methods=["GET", "POST"])
def plan():
    """Plan step: Plan the video script."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    if request.method == "POST":
        # Save video details
        session["video_title"] = request.form.get("video_title", "")
        session["video_audience"] = request.form.get("video_audience", "")
        session["video_duration"] = request.form.get("video_duration", "5")

        # Save script plan sections
        section_names = request.form.getlist("section_names[]")
        section_key_points = request.form.getlist("section_key_points[]")

        script_plan = []
        for i in range(len(section_names)):
            if section_names[i].strip():  # Only add non-empty sections
                script_plan.append(
                    {
                        "name": section_names[i],
                        "key_points": section_key_points[i] if i < len(section_key_points) else "",
                    }
                )

        session["script_plan"] = script_plan

        # Proceed to next step
        return redirect(url_for("script"))

    return render_template(
        "plan.html",
        step=4 if session.get("use_web_search", True) else 3,
        total_steps=len(WIZARD_STEPS) - 1,
    )


@app.route("/script", methods=["GET", "POST"])
def script():
    """Script step: Write the video script."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    if "script_plan" not in session or not session["script_plan"]:
        flash("Please create a script plan first.", "warning")
        return redirect(url_for("plan"))

    if request.method == "POST":
        # Save script sections
        section_titles = request.form.getlist("section_titles[]")
        section_contents = request.form.getlist("section_contents[]")

        script_sections = []
        for i in range(len(section_titles)):
            if section_titles[i].strip():  # Only add non-empty sections
                script_sections.append(
                    {
                        "title": section_titles[i],
                        "content": section_contents[i] if i < len(section_contents) else "",
                    }
                )

        session["script_sections"] = script_sections

        # Proceed to next step
        return redirect(url_for("edit"))

    return render_template(
        "script.html",
        step=5 if session.get("use_web_search", True) else 4,
        total_steps=len(WIZARD_STEPS) - 1,
    )


# Add routes for other steps (to be implemented)


@app.route("/save_workflow", methods=["POST"])
def save_workflow():
    """Save the current workflow data to a file."""
    # TODO: Implement saving logic
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
