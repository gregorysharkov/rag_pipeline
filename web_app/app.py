import os
import logging
import tempfile
import json
from datetime import datetime, timedelta

from backend.agents.web_search_agent import WebSearchAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.improved_script_writing_agent import ImprovedScriptWritingAgent
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from openai import OpenAI
from utils.file_utils import remove_files, save_files

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload size

# Configure Flask-Session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "flask_session"
)
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=1)
app.config["SESSION_USE_SIGNER"] = True
Session(app)

# Create uploads directory if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

# Initialize OpenAI client
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


@app.route("/")
def index():
    """Home page / landing page."""
    # Clear session data for a fresh start
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
            if not (files_to_remove and session.get("reference_files")):
                flash("No files to remove.", "warning")

            updated_files = remove_files(
                files_to_remove, session.get("reference_files", []), app.config["UPLOAD_FOLDER"]
            )
            session["reference_files"] = updated_files

        # Handle file uploads - append to existing files if any
        if "reference_files" in request.files and any(request.files.getlist("reference_files")):
            uploaded_files = session.get("reference_files", [])
            files = request.files.getlist("reference_files")
            uploaded_files = uploaded_files.extend(save_files(files, app.config["UPLOAD_FOLDER"]))

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
        # Initialize the WebSearchAgent and perform the search
        web_search_agent = WebSearchAgent(client)
        topic = session.get("topic", "")

        # Add additional context if available
        if session.get("additional_context"):
            topic += f". {session.get('additional_context')}"

        # Add target audience if available
        if session.get("target_audience"):
            topic += f". Target audience: {session.get('target_audience')}"

        # Perform the search
        search_results = web_search_agent.run(topic)

        # Add IDs to the search results for selection
        for i, result in enumerate(search_results):
            result["id"] = str(i + 1)

        session["search_results"] = search_results
        print(f"{search_results=}")

        if refresh_requested:
            flash("Search results refreshed successfully!", "success")
            # Clear previous selections when refreshing
            if "selected_search_results" in session:
                session.pop("selected_search_results")

    return render_template("web_search.html", step=3, total_steps=len(WIZARD_STEPS) - 1)


@app.route("/plan", methods=["GET", "POST"])
def plan():
    """Third step of the wizard: Plan the video script."""
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    if request.method == "POST":
        # Get selected references from session
        selected_refs = []
        if "selected_search_results" in session and "search_results" in session:
            selected_ids = session["selected_search_results"]
            for result in session["search_results"]:
                if result["id"] in selected_ids:
                    selected_refs.append(
                        {
                            "title": result["title"],
                            "url": result["url"],
                            "summary": result["summary"],
                        }
                    )

        # Check if we have any references
        if not selected_refs:
            flash("Please select at least one reference before generating a plan.", "warning")
            return redirect(url_for("web_search"))

        # Create an instance of PlanningAgent and generate the plan
        planning_agent = PlanningAgent(client=client)

        logger.info(f"Generating plan for topic: {session['topic']}")
        logger.info(f"Number of references: {len(selected_refs)}")

        try:
            # Generate plan using PlanningAgent
            plan_result = planning_agent.run(
                topic=session["topic"],
                references=selected_refs,
                additional_context=session.get("additional_context"),
            )

            logger.info(f"Plan generation result: {plan_result}")

            # Check if the plan_result is empty (indicates an error in the agent)
            if not plan_result or not plan_result.get("sections"):
                logger.error("Plan result is empty or missing sections")
                flash("Failed to generate a plan. Please try again or check your inputs.", "error")
                return render_template("plan.html", step=3, total_steps=len(WIZARD_STEPS) - 1)

            # Extract essential details for cookie-based session
            session["video_title"] = plan_result["title"]
            session["target_audience"] = plan_result["target_audience"]
            session["duration"] = plan_result["duration"]

            # Store full plan data in session
            session["plan"] = plan_result
            logger.info(
                f"Stored plan in session with {len(plan_result.get('sections', []))} sections"
            )
            print(f"{plan_result=}")
            flash("Script plan generated successfully!", "success")
            return redirect(url_for("script"))

        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}", exc_info=True)
            flash(f"Error generating plan: {str(e)}", "error")
            return render_template("plan.html", step=3, total_steps=len(WIZARD_STEPS) - 1)

    # For GET requests, check if we have plan data to display
    plan_data = session.get("plan")

    return render_template(
        "plan.html",
        step=3,
        total_steps=len(WIZARD_STEPS) - 1,
        plan_data=plan_data,
        video_title=session.get("video_title", ""),
        target_audience=session.get("target_audience", ""),
        duration=session.get("duration", ""),
    )


@app.route("/script", methods=["GET", "POST"])
def script():
    """Script step: Write the video script."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Load plan data from session
    plan_data = session.get("plan")
    if not plan_data or not plan_data.get("sections"):
        flash("Please create a script plan first.", "warning")
        return redirect(url_for("plan"))

    if request.method == "POST":
        # Save script sections
        section_titles = request.form.getlist("section_titles[]")
        section_contents = request.form.getlist("section_contents[]")

        script_sections = [
            {"title": title, "content": content}
            for title, content in zip(section_titles, section_contents)
        ]

        # Save script sections to session
        session["script"] = script_sections
        session["script_complete"] = True

        # Proceed to next step
        return redirect(url_for("edit"))

    # Format plan data for the template
    sections = []
    if plan_data and plan_data.get("sections"):
        sections = [
            {
                "name": section["name"],
                "key_points": section["points"],
                "key_message": section["key_message"],
            }
            for section in plan_data["sections"]
        ]

    return render_template(
        "script.html",
        step=4,
        total_steps=len(WIZARD_STEPS) - 1,
        sections=sections,
        video_title=session.get("video_title", ""),
        target_audience=session.get("target_audience", ""),
        duration=session.get("duration", ""),
    )


@app.route("/edit", methods=["GET", "POST"])
def edit():
    """Edit step: Enhance the script with editing options."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Load script sections from session
    script_sections = session.get("script")
    if not script_sections or not session.get("script_complete"):
        flash("Please create a script first.", "warning")
        return redirect(url_for("script"))

    if request.method == "POST":
        # Save editing options
        edit_options = request.form.getlist("edit_options[]")
        additional_instructions = request.form.get("additional_instructions", "")
        edited_script = request.form.get("edited_script", "")

        # Debug logging
        logger.debug(f"Received edited_script: {edited_script[:100]}...")  # Print first 100 chars
        logger.debug(f"Form keys: {list(request.form.keys())}")

        # Save to session
        session["edit"] = {
            "edit_options": edit_options,
            "additional_instructions": additional_instructions,
            "edited_script": edited_script,
        }

        session["edit_complete"] = True

        # Proceed to next step
        return redirect(url_for("short_video"))

    # Prepare combined script content if needed
    combined_script = ""
    if script_sections:
        for section in script_sections:
            combined_script += f"**[{section.get('title', '')}]**\n\n"
            combined_script += f"{section.get('content', '')}\n\n"

    return render_template(
        "edit.html",
        step=5,
        total_steps=len(WIZARD_STEPS) - 1,
        script_sections=script_sections,
        combined_script=combined_script,
    )


@app.route("/short_video", methods=["GET", "POST"])
def short_video():
    """Short Video step: Generate YouTube Shorts from the main script."""
    # Check if previous steps were completed
    if "topic" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Check for script content - either edited script or script sections
    edit_data = session.get("edit")
    script_data = session.get("script")

    if not edit_data and not script_data:
        flash("Please create a script first.", "warning")
        return redirect(url_for("script"))

    # Get the edited script or build from script sections
    edited_script = ""
    if edit_data and edit_data.get("edited_script"):
        edited_script = edit_data.get("edited_script")
    elif script_data:
        # Create a combined script from the sections
        for section in script_data:
            edited_script += f"**[{section.get('title', '')}]**\n\n"
            edited_script += f"{section.get('content', '')}\n\n"

        logger.debug(f"Auto-generated edited script from sections: {edited_script[:100]}...")

    if request.method == "POST":
        # Save shorts generation options
        shorts_count = request.form.get("shorts_count", "3")
        shorts_duration = request.form.get("shorts_duration", "30")
        shorts_focus = request.form.getlist("shorts_focus[]")
        generated_shorts = request.form.getlist("generated_shorts[]")

        # Save to session
        session["shorts"] = {
            "shorts_count": shorts_count,
            "shorts_duration": shorts_duration,
            "shorts_focus": shorts_focus,
            "generated_shorts": generated_shorts,
        }

        # Proceed to completion
        flash("Congratulations! You've completed the YouTube Script Generator wizard.", "success")
        return redirect(url_for("index"))

    return render_template(
        "short_video.html", step=6, total_steps=len(WIZARD_STEPS) - 1, edited_script=edited_script
    )


# Add routes for other steps (to be implemented)


@app.route("/save_workflow", methods=["POST"])
def save_workflow():
    """Save the current workflow data to a file."""
    # TODO: Implement saving logic
    return redirect(url_for("index"))


@app.route("/api/generate-script-section", methods=["POST"])
def generate_script_section():
    """API endpoint to generate content for a specific script section."""
    # Check if the user is logged in and has a valid session
    if "topic" not in session or "plan" not in session:
        return jsonify({"error": "Missing session data. Please complete the previous steps."}), 400

    # Parse the request
    try:
        data = request.get_json()
        section_index = int(data.get("section_index", -1))

        if section_index < 0:
            return jsonify({"error": "Invalid section index."}), 400
    except Exception as e:
        logger.error(f"Error parsing request: {str(e)}")
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    # Get required data from session
    topic = session.get("topic", "")
    plan = session.get("plan", {})

    # Get references
    references = []
    if session.get("selected_search_results") and session.get("search_results"):
        for result in session.get("search_results", []):
            if result.get("id") in session.get("selected_search_results", []):
                references.append(result)

    # Additional context
    additional_context = session.get("additional_context", "")

    # Validate plan and section index
    if not plan or "sections" not in plan or section_index >= len(plan["sections"]):
        return jsonify({"error": "Invalid plan or section index."}), 400

    try:
        # Initialize the script writing agent
        script_writing_agent = ImprovedScriptWritingAgent(client)

        # Generate content for the specific section
        section_content = script_writing_agent.generate_section_content(
            topic=topic,
            plan=plan,
            section_index=section_index,
            references=references,
            additional_context=additional_context,
        )

        return jsonify(
            {
                "section_index": section_index,
                "section_name": plan["sections"][section_index]["name"],
                "content": section_content,
            }
        )
    except Exception as e:
        logger.error(f"Error generating script section: {str(e)}")
        return jsonify({"error": f"Error generating script: {str(e)}"}), 500


@app.route("/api/generate-all-sections", methods=["POST"])
def generate_all_sections():
    """API endpoint to generate content for all script sections."""
    # Check if the user is logged in and has a valid session
    if "topic" not in session or "plan" not in session:
        return jsonify({"error": "Missing session data. Please complete the previous steps."}), 400

    # Get required data from session
    topic = session.get("topic", "")
    plan = session.get("plan", {})

    # Get references
    references = []
    if session.get("selected_search_results") and session.get("search_results"):
        for result in session.get("search_results", []):
            if result.get("id") in session.get("selected_search_results", []):
                references.append(result)

    # Additional context
    additional_context = session.get("additional_context", "")

    # Validate plan
    if not plan or "sections" not in plan or not plan["sections"]:
        return jsonify({"error": "Invalid plan structure or no sections available."}), 400

    try:
        # Initialize the script writing agent
        script_writing_agent = ImprovedScriptWritingAgent(client)

        # Generate content for all sections
        all_sections_content = script_writing_agent.generate_all_section_contents(
            topic=topic, plan=plan, references=references, additional_context=additional_context
        )

        # Format the response
        response_data = {"sections": []}

        for i, content in all_sections_content.items():
            if i < len(plan["sections"]):
                response_data["sections"].append(
                    {
                        "section_index": i,
                        "section_name": plan["sections"][i]["name"],
                        "content": content,
                    }
                )

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error generating all script sections: {str(e)}")
        return jsonify({"error": f"Error generating script: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
