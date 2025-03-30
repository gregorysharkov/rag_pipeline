import logging
import os
from datetime import timedelta
import re

from backend.agents.improved_script_writing_agent import ImprovedScriptWritingAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.scripting_editing_agent import ScriptEditingAgent
from backend.agents.web_search_agent import WebSearchAgent
from backend.session.session import ScriptSession
from backend.session.web_search_result import WebSearchResult
from backend.session.plan import Plan, PlanSection
from backend.session.edit_options import EditOptions
from backend.session.shorts_options import ShortsOptions
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
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
    session["script_session"] = ScriptSession(
        topic="",
        additional_context="",
        target_audience="",
        content_type="",
        tone="",
        use_web_search=True,
    )
    return redirect(url_for("context"))


@app.route("/context", methods=["GET", "POST"])
def context():
    """First step of the wizard: Collect context information."""
    current_session = session["script_session"]
    if request.method == "POST":
        # Save form data to session
        current_session.topic = request.form.get("topic", "")
        current_session.additional_context = request.form.get("additional_context", "")

        # Handle target audience (could be from dropdown or custom input)
        current_session.target_audience = request.form.get("target_audience", "")

        current_session.content_type = request.form.get("content_type", "")
        current_session.tone = request.form.get("tone", "")

        # Proceed to next step
        session["script_session"] = current_session
        return redirect(url_for("references"))

    # For GET requests, we keep all existing session data
    return render_template(
        "context.html", script_session=current_session, step=1, total_steps=len(WIZARD_STEPS) - 1
    )


@app.route("/references", methods=["GET", "POST"])
def references():
    """Second step: References and resources."""
    # Check if previous step was completed
    current_session = session["script_session"]
    if current_session.topic == "":
        flash("Please complete the previous step first.", "warning")
        return redirect(url_for("context"))

    if request.method == "POST":
        # Save web search preference
        current_session.use_web_search = "use_web_search" in request.form

        # Handle removal of previously uploaded files
        if "files_to_remove" in request.form and request.form.get("files_to_remove"):
            files_to_remove = request.form.get("files_to_remove").split(",")
            if not (files_to_remove and current_session.reference_files):
                flash("No files to remove.", "warning")

            updated_files = remove_files(
                files_to_remove, current_session.reference_files, app.config["UPLOAD_FOLDER"]
            )
            current_session.reference_files = updated_files
            session["script_session"] = current_session

        # Handle file uploads - append to existing files if any
        if "reference_files" in request.files and any(request.files.getlist("reference_files")):
            uploaded_files = current_session.reference_files
            files_from_form = request.files.getlist("reference_files")
            uploaded_files.extend(save_files(files_from_form, app.config["UPLOAD_FOLDER"]))
            current_session.reference_files = uploaded_files
            session["script_session"] = current_session

            if uploaded_files:
                flash(
                    f"Successfully uploaded {len(files_from_form)} file(s) to the server.",
                    "success",
                )

        # Handle web links - append to existing links if any
        if "web_links[]" in request.form and any(
            link.strip() for link in request.form.getlist("web_links[]")
        ):
            web_links = current_session.web_links
            links = request.form.getlist("web_links[]")
            descriptions = request.form.getlist("web_link_descriptions[]")

            new_links_count = 0
            for i in range(len(links)):
                if links[i].strip():  # Only add non-empty links
                    from backend.session.web_link import WebLink

                    web_links.append(
                        WebLink(
                            url=links[i],
                            description=descriptions[i] if i < len(descriptions) else "",
                        )
                    )
                    new_links_count += 1

            current_session.web_links = web_links
            session["script_session"] = current_session
            if new_links_count > 0:
                flash(f"Successfully added {new_links_count} web link(s).", "success")

        # Proceed to next step - either web search or plan depending on setting
        if current_session.use_web_search:
            return redirect(url_for("web_search"))
        else:
            return redirect(url_for("plan"))

    return render_template(
        "references.html", script_session=current_session, step=2, total_steps=len(WIZARD_STEPS) - 1
    )


@app.route("/web_search", methods=["GET", "POST"])
def web_search():
    """Web search step: Show search results from the web."""
    # Check if previous steps were completed
    current_session = session["script_session"]
    if current_session.topic == "":
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Skip this step if web search is disabled
    if not current_session.use_web_search:
        flash("Web search step skipped as requested.", "info")
        return redirect(url_for("plan"))

    if request.method == "POST":
        # Save selected search results
        selected_results = request.form.getlist("selected_results[]")
        if selected_results:
            # Store selected IDs in the session object
            current_session.selected_search_results = selected_results
            session["script_session"] = current_session
            flash(
                f"Selected {len(selected_results)} search results to include in your script.",
                "success",
            )

        # Proceed to next step
        return redirect(url_for("plan"))

    # For GET requests, perform the web search if not already done or if refresh requested
    refresh_requested = request.args.get("refresh", "0") == "1"
    if not current_session.web_search_results or refresh_requested:
        # Initialize the WebSearchAgent and perform the search
        web_search_agent = WebSearchAgent(client)
        topic = current_session.topic

        # Add additional context if available
        if current_session.additional_context:
            topic += f". {current_session.additional_context}"

        # Add target audience if available
        if current_session.target_audience:
            topic += f". Target audience: {current_session.target_audience}"

        # Perform the search
        search_results = web_search_agent.run(topic)

        # Add IDs to the search results for selection
        processed_results = []
        for i, result in enumerate(search_results):
            processed_result = WebSearchResult(
                title=result["title"], url=result["url"], snippet=result["summary"]
            )
            processed_result.id = str(i + 1)  # Add ID for selection
            processed_results.append(processed_result)

        current_session.web_search_results = processed_results
        session["script_session"] = current_session

        if refresh_requested:
            flash("Search results refreshed successfully!", "success")
            # Clear previous selections when refreshing
            current_session.selected_search_results = []
            session["script_session"] = current_session

    # Mark web search as viewed even if no results are selected
    current_session.web_search_viewed = True
    session["script_session"] = current_session

    return render_template(
        "web_search.html",
        script_session=current_session,
        step=3,
        total_steps=len(WIZARD_STEPS) - 1,
        is_web_search_skipped=False,
    )


@app.route("/plan", methods=["GET", "POST"])
def plan():
    """Third step of the wizard: Plan the video script."""
    # Check if previous steps were completed
    if "script_session" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Get current session
    current_session = session["script_session"]

    # Check if web search is skipped
    is_web_search_skipped = not current_session.use_web_search

    if request.method == "POST":
        # Get selected references from session
        selected_refs = []
        if current_session.selected_search_results and current_session.web_search_results:
            selected_ids = current_session.selected_search_results
            for result in current_session.web_search_results:
                if result.id in selected_ids:
                    selected_refs.append(
                        {
                            "title": result.title,
                            "url": result.url,
                            "summary": result.snippet,
                        }
                    )

        # Check if we have any references
        if not selected_refs and not is_web_search_skipped:
            flash("Please select at least one reference before generating a plan.", "warning")
            return redirect(url_for("web_search"))

        # Create an instance of PlanningAgent and generate the plan
        planning_agent = PlanningAgent(client=client)

        logger.info(f"Generating plan for topic: {current_session.topic}")
        logger.info(f"Number of references: {len(selected_refs)}")

        try:
            # Generate plan using PlanningAgent
            plan_result = planning_agent.run(
                topic=current_session.topic,
                references=selected_refs,
                additional_context=current_session.additional_context,
            )

            logger.info(f"Plan generation result: {plan_result}")

            # Check if the plan_result is empty (indicates an error in the agent)
            if not plan_result or not plan_result.get("sections"):
                logger.error("Plan result is empty or missing sections")
                flash("Failed to generate a plan. Please try again or check your inputs.", "error")
                return render_template(
                    "plan.html",
                    step=3 if is_web_search_skipped else 4,
                    total_steps=len(WIZARD_STEPS) - 1,
                    is_web_search_skipped=is_web_search_skipped,
                    script_session=current_session,
                )

            # Store plan data in current_session
            current_session.plan = Plan.from_dict(plan_result)
            current_session.video_title = plan_result["title"]
            current_session.video_audience = plan_result["target_audience"]
            current_session.video_duration = plan_result["duration"]

            # Update the session with the modified current_session
            session["script_session"] = current_session

            # Also keep these values in the regular session for backward compatibility
            session["video_title"] = plan_result["title"]
            session["target_audience"] = plan_result["target_audience"]
            session["duration"] = plan_result["duration"]
            session["plan"] = plan_result

            flash("Script plan generated successfully!", "success")
            return redirect(url_for("script"))

        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}", exc_info=True)
            flash(f"Error generating plan: {str(e)}", "error")
            return render_template(
                "plan.html",
                step=3 if is_web_search_skipped else 4,
                total_steps=len(WIZARD_STEPS) - 1,
                is_web_search_skipped=is_web_search_skipped,
                script_session=current_session,
            )

    # For GET requests, check if we have plan data to display
    plan_data = session.get("plan")

    return render_template(
        "plan.html",
        step=3 if is_web_search_skipped else 4,
        total_steps=len(WIZARD_STEPS) - 1,
        plan_data=plan_data,
        video_title=session.get("video_title", ""),
        target_audience=session.get("target_audience", ""),
        duration=session.get("duration", ""),
        is_web_search_skipped=is_web_search_skipped,
        script_session=current_session,
    )


@app.route("/script", methods=["GET", "POST"])
def script():
    """Script step: Write the video script."""
    # Check if previous steps were completed
    if "script_session" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Get current session
    current_session = session["script_session"]

    # Check if a plan exists
    if not current_session.plan:
        flash("Please create a script plan first.", "warning")
        return redirect(url_for("plan"))

    # Check if web search is skipped
    is_web_search_skipped = not current_session.use_web_search

    if request.method == "POST":
        # Save script sections
        section_titles = request.form.getlist("section_titles[]")
        section_contents = request.form.getlist("section_contents[]")

        script_sections = [
            {"title": title, "content": content}
            for title, content in zip(section_titles, section_contents)
        ]

        # Save script sections to script_session
        current_session.script_sections = script_sections
        current_session.script_complete = True
        session["script_session"] = current_session

        # Also save to regular session for backward compatibility
        session["script"] = script_sections
        session["script_sections"] = script_sections
        session["script_complete"] = True

        # Proceed to next step
        return redirect(url_for("edit"))

    # Format plan data for the template
    sections = []
    if current_session.plan:
        sections = [
            {
                "name": section.name,
                "key_points": section.points,
                "key_message": section.key_message,
            }
            for section in current_session.plan.sections
        ]

    return render_template(
        "script.html",
        step=4 if is_web_search_skipped else 5,
        total_steps=len(WIZARD_STEPS) - 1,
        sections=sections,
        is_web_search_skipped=is_web_search_skipped,
        script_session=current_session,
    )


@app.route("/edit", methods=["GET", "POST"])
def edit():
    """Edit step: Enhance the script with editing options."""
    # Check if previous steps were completed
    if "script_session" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Get current session
    current_session = session["script_session"]

    # Check if script sections exist
    if not current_session.script_sections or not current_session.script_complete:
        flash("Please create a script first.", "warning")
        return redirect(url_for("script"))

    # Ensure edit_options is an EditOptions object
    try:
        # Try to access an attribute to verify it's an EditOptions object
        _ = current_session.edit_options.edit_options
    except (AttributeError, TypeError):
        # If it fails, convert to an EditOptions object
        logger.warning("Converting edit_options from old format to new format in edit route")
        # Check if we have any old-format edit data
        edit_data = session.get("edit", {})

        # Create a new EditOptions object
        current_session.edit_options = EditOptions(
            edit_options=edit_data.get("edit_options", []),
            additional_instructions=edit_data.get("additional_instructions", ""),
            edited_script=edit_data.get("edited_script", ""),
            is_complete=session.get("edit_complete", False),
        )
        session["script_session"] = current_session

    # Check if web search is skipped
    is_web_search_skipped = not current_session.use_web_search

    if request.method == "POST":
        # Save editing options
        edit_options = request.form.getlist("edit_options[]")
        additional_instructions = request.form.get("additional_instructions", "")
        edited_script = request.form.get("edited_script", "")

        # Debug logging
        logger.debug(f"Received edited_script: {edited_script[:100]}...")  # Print first 100 chars
        logger.debug(f"Form keys: {list(request.form.keys())}")

        # Prepare combined script content if no edited script was provided
        if not edited_script:
            combined_script = ""
            if current_session.script_sections:
                for section in current_session.script_sections:
                    combined_script += f"**[{section.get('title', '')}]**\n\n"
                    combined_script += f"{section.get('content', '')}\n\n"

            # Use the script editing agent to generate the edited script
            agent = ScriptEditingAgent()
            edited_script = agent.edit_script(combined_script, edit_options, additional_instructions)

        # Debug logging
        logger.debug(f"Final edited_script length: {len(edited_script)}")
        logger.debug(f"Final edited_script preview: {edited_script[:100]}...")

        # Save the edited script and options to session
        try:
            # Try to access as an EditOptions object
            current_session.edit_options.edit_options = edit_options
            current_session.edit_options.additional_instructions = additional_instructions
            current_session.edit_options.edited_script = edited_script
            current_session.edit_options.is_complete = True
        except (AttributeError, TypeError):
            # If it fails, create a new EditOptions object
            logger.warning("Converting edit_options from old format to new format")
            current_session.edit_options = EditOptions(
                edit_options=edit_options,
                additional_instructions=additional_instructions,
                edited_script=edited_script,
                is_complete=True,
            )

        session["script_session"] = current_session

        # Also save to regular session for backward compatibility
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
    if current_session.script_sections:
        for section in current_session.script_sections:
            combined_script += f"**[{section.get('title', '')}]**\n\n"
            combined_script += f"{section.get('content', '')}\n\n"

    return render_template(
        "edit.html",
        step=5 if is_web_search_skipped else 6,
        total_steps=len(WIZARD_STEPS) - 1,
        script_sections=current_session.script_sections,
        combined_script=combined_script,
        is_web_search_skipped=is_web_search_skipped,
        script_session=current_session,
    )


@app.route("/short_video", methods=["GET", "POST"])
def short_video():
    """Short Video step: Generate YouTube Shorts from the main script."""
    # Check if previous steps were completed
    if "script_session" not in session:
        flash("Please complete the context step first.", "warning")
        return redirect(url_for("context"))

    # Get current session
    current_session = session["script_session"]

    # Check if previous steps were completed
    if not current_session.script_sections or not current_session.script_complete:
        flash("Please create a script first.", "warning")
        return redirect(url_for("script"))

    # Check if editing step is completed and get the edited script
    edited_script = ""
    try:
        if not current_session.edit_options.is_complete:
            flash("Please complete the editing step first.", "warning")
            return redirect(url_for("edit"))

        # Get the edited script from edit_options
        edited_script = current_session.edit_options.edited_script
    except (AttributeError, TypeError):
        # Handle case where edit_options is not an EditOptions object
        flash("Please complete the editing step first.", "warning")
        return redirect(url_for("edit"))

    # If no edited script is available, create one from script sections
    if not edited_script:
        edited_script = ""
        for section in current_session.script_sections:
            edited_script += f"**[{section.get('title', '')}]**\n\n"
            edited_script += f"{section.get('content', '')}\n\n"

    # Ensure shorts_options is a ShortsOptions object
    try:
        # Try to access an attribute to verify it's a ShortsOptions object
        _ = current_session.shorts_options.shorts_count
    except (AttributeError, TypeError):
        # If it fails, convert to a ShortsOptions object
        logger.warning(
            "Converting shorts_options from old format to new format in short_video route"
        )
        # Check if we have any old-format shorts data
        shorts_data = session.get("shorts", {})

        # Create a new ShortsOptions object
        from backend.session.shorts_options import ShortsOptions

        current_session.shorts_options = ShortsOptions(
            shorts_count=int(shorts_data.get("shorts_count", 3)),
            shorts_duration=int(shorts_data.get("shorts_duration", 30)),
            shorts_focus=shorts_data.get("shorts_focus", []),
            generated_shorts=[{"content": s} for s in shorts_data.get("generated_shorts", [])],
            is_complete=bool(shorts_data),
        )
        session["script_session"] = current_session

    # Check if web search is skipped
    is_web_search_skipped = not current_session.use_web_search

    if request.method == "POST":
        # Save shorts generation options
        shorts_count = int(request.form.get("shorts_count", "3"))
        shorts_duration = int(request.form.get("shorts_duration", "30"))
        shorts_focus = request.form.getlist("shorts_focus[]")
        generated_shorts = request.form.getlist("generated_shorts[]")

        # Save to session
        current_session.shorts_options.shorts_count = shorts_count
        current_session.shorts_options.shorts_duration = shorts_duration
        current_session.shorts_options.shorts_focus = shorts_focus
        current_session.shorts_options.generated_shorts = [{"content": s} for s in generated_shorts]
        current_session.shorts_options.is_complete = True
        session["script_session"] = current_session

        # Also save to regular session for backward compatibility
        session["shorts"] = {
            "shorts_count": shorts_count,
            "shorts_duration": shorts_duration,
            "shorts_focus": shorts_focus,
            "generated_shorts": generated_shorts,
        }

        # Proceed to completion
        flash("Congratulations! You've completed the YouTube Script Generator wizard.", "success")
        return redirect(url_for("index"))

    # Debug logging
    logger.debug(f"Edited script length: {len(edited_script)}")
    logger.debug(f"Edited script preview: {edited_script[:100]}...")

    return render_template(
        "short_video.html",
        step=6 if is_web_search_skipped else 7,
        total_steps=len(WIZARD_STEPS) - 1,
        edited_script=edited_script,
        script_session=current_session,
        shorts_count=current_session.shorts_options.shorts_count,
        shorts_duration=current_session.shorts_options.shorts_duration,
        shorts_focus=current_session.shorts_options.shorts_focus,
        generated_shorts=current_session.shorts_options.get_shorts_data(),
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
    # Check if the user has a valid script_session
    if "script_session" not in session:
        return jsonify({"error": "Missing session data. Please complete the previous steps."}), 400

    current_session = session["script_session"]

    # Check if user has completed the plan step
    if not current_session.plan:
        return jsonify({"error": "Missing plan data. Please complete the planning step."}), 400

    # Parse the request
    try:
        data = request.get_json()
        section_index = int(data.get("section_index", -1))

        if section_index < 0:
            return jsonify({"error": "Invalid section index."}), 400
    except Exception as e:
        logger.error(f"Error parsing request: {str(e)}")
        return jsonify({"error": f"Invalid request: {str(e)}"}), 400

    # Get required data from script_session
    topic = current_session.topic
    plan_sections = current_session.plan.sections if current_session.plan else []

    # Convert plan to the format expected by the agent
    plan = {
        "title": current_session.video_title,
        "target_audience": current_session.video_audience,
        "duration": current_session.video_duration,
        "sections": [
            {"name": section.name, "key_message": section.key_message, "points": section.points}
            for section in plan_sections
        ],
    }

    # Get references
    references = []
    if current_session.selected_search_results and current_session.web_search_results:
        for result in current_session.web_search_results:
            if result.id in current_session.selected_search_results:
                references.append(
                    {"title": result.title, "url": result.url, "summary": result.snippet}
                )

    # Additional context
    additional_context = current_session.additional_context

    # Validate plan and section index
    if not plan_sections or section_index >= len(plan_sections):
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
    # Check if the user has a valid script_session
    if "script_session" not in session:
        return jsonify({"error": "Missing session data. Please complete the previous steps."}), 400

    current_session = session["script_session"]

    # Check if user has completed the plan step
    if not current_session.plan:
        return jsonify({"error": "Missing plan data. Please complete the planning step."}), 400

    # Get required data from script_session
    topic = current_session.topic
    plan_sections = current_session.plan.sections if current_session.plan else []

    # Convert plan to the format expected by the agent
    plan = {
        "title": current_session.video_title,
        "target_audience": current_session.video_audience,
        "duration": current_session.video_duration,
        "sections": [
            {"name": section.name, "key_message": section.key_message, "points": section.points}
            for section in plan_sections
        ],
    }

    # Get references
    references = []
    if current_session.selected_search_results and current_session.web_search_results:
        for result in current_session.web_search_results:
            if result.id in current_session.selected_search_results:
                references.append(
                    {"title": result.title, "url": result.url, "summary": result.snippet}
                )

    # Additional context
    additional_context = current_session.additional_context

    # Validate plan
    if not plan_sections:
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


@app.route("/api/edit-script", methods=["POST"])
def edit_script():
    """API endpoint to edit the script."""
    if "script_session" not in session:
        return jsonify({"error": "No session data found. Please start over."}), 400

    current_session = session["script_session"]

    if not current_session.script_sections:
        return jsonify({"error": "No script sections found. Please generate a script first."}), 400

    # Get data from request
    data = request.get_json()
    edit_options = data.get("edit_options", [])
    additional_instructions = data.get("additional_instructions", "")

    # Get the combined script
    combined_script = ""
    for section in current_session.script_sections:
        combined_script += f"**[{section.get('title', '')}]**\n\n"
        combined_script += f"{section.get('content', '')}\n\n"

    # Use the script editing agent to generate the edited script
    agent = ScriptEditingAgent()
    edited_script = agent.edit_script(combined_script, edit_options, additional_instructions)

    # Save the edited script and options to session
    try:
        # Try to access as an EditOptions object
        current_session.edit_options.edit_options = edit_options
        current_session.edit_options.additional_instructions = additional_instructions
        current_session.edit_options.edited_script = edited_script
        current_session.edit_options.is_complete = True
    except (AttributeError, TypeError):
        # If it fails, create a new EditOptions object
        logger.warning("Converting edit_options from old format to new format")
        current_session.edit_options = EditOptions(
            edit_options=edit_options,
            additional_instructions=additional_instructions,
            edited_script=edited_script,
            is_complete=True,
        )

    session["script_session"] = current_session

    # Also save to regular session for backward compatibility
    session["edit"] = {
        "edit_options": edit_options,
        "additional_instructions": additional_instructions,
        "edited_script": edited_script,
    }

    return jsonify({"edited_script": edited_script})


@app.route("/api/generate-shorts", methods=["POST"])
def generate_shorts():
    """API endpoint to generate YouTube Shorts from the main script."""
    if "script_session" not in session:
        return jsonify({"error": "No session data found. Please start over."}), 400

    current_session = session["script_session"]

    # Check if we have an edited script
    try:
        # Try to access edited_script as an attribute of edit_options
        if not current_session.edit_options.edited_script:
            return jsonify(
                {"error": "No edited script found. Please complete the edit step first."}
            ), 400
        edited_script = current_session.edit_options.edited_script
    except (AttributeError, TypeError):
        # If edit_options is not an EditOptions object
        return jsonify(
            {"error": "Edit options not properly set up. Please complete the edit step first."}
        ), 400

    # Ensure shorts_options is a ShortsOptions object
    try:
        # Try to access an attribute to verify it's a ShortsOptions object
        _ = current_session.shorts_options.shorts_count
    except (AttributeError, TypeError):
        # If it fails, create a new ShortsOptions object
        logger.warning(
            "Converting shorts_options from old format to new format in generate_shorts API"
        )
        from backend.session.shorts_options import ShortsOptions

        current_session.shorts_options = ShortsOptions()
        session["script_session"] = current_session

    # Get data from request
    data = request.get_json()
    shorts_count = int(data.get("shorts_count", 3))
    shorts_duration = int(data.get("shorts_duration", 30))
    shorts_focus = data.get("shorts_focus", [])

    try:
        # For demo purposes, generate simple shorts
        script = edited_script
        generated_shorts = []

        # Extract sections from the script
        sections = []
        section_pattern = r"\*\*\[(.*?)\]\*\*\s*\n\n(.*?)(?=\n\n\*\*\[|\Z)"
        matches = re.findall(section_pattern, script, re.DOTALL)

        if matches:
            for title, content in matches:
                sections.append({"title": title, "content": content.strip()})

        # If no sections found, split by paragraphs
        if not sections and script:
            paragraphs = [p for p in script.split("\n\n") if p.strip()]
            for i, paragraph in enumerate(paragraphs[:shorts_count]):
                sections.append({"title": f"Short {i + 1}", "content": paragraph.strip()})

        # Take the first few sections based on count
        for i, section in enumerate(sections[:shorts_count]):
            content = section["content"]
            # Trim content to roughly match the requested duration
            words_per_second = 3  # Average speaking rate
            max_words = shorts_duration * words_per_second
            words = content.split()

            if len(words) > max_words:
                content = " ".join(words[:max_words]) + "..."

            generated_shorts.append(
                {
                    "title": f"Short {i + 1}: {section['title']}",
                    "content": content,
                    "duration": shorts_duration,
                }
            )

        # Save to session
        current_session.shorts_options.shorts_count = shorts_count
        current_session.shorts_options.shorts_duration = shorts_duration
        current_session.shorts_options.shorts_focus = shorts_focus
        current_session.shorts_options.generated_shorts = generated_shorts
        session["script_session"] = current_session

        return jsonify({"shorts": generated_shorts})

    except Exception as e:
        return jsonify({"error": f"Error generating shorts: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
