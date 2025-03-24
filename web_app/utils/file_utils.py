import os
import uuid

from backend.session.reference_file import ReferenceFile
from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}


def allowed_file(filename) -> bool:
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(filename: str) -> str:
    """Generate a unique filename."""
    file_name = secure_filename(filename)
    unique_filename = f"{uuid.uuid4().hex}_{file_name}"
    return unique_filename


def generate_secure_filename(filename: str) -> str:
    """Generate a secure filename."""
    return secure_filename(filename)


def save_files(files: list, upload_folder: str) -> list[ReferenceFile]:
    """Save files to the upload folder."""
    uploaded_files = []
    for file in files:
        if not (file and file.filename and allowed_file(file.filename)):
            continue

        # Generate a unique filename to prevent collisions
        filename = generate_secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Read file content
        try:
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")
        except:
            # For binary files that can't be decoded as text
            content = f"Binary file: {filename}"

        # Create and store ReferenceFile object
        uploaded_files.append(
            ReferenceFile(
                filename=filename,
                content=content,
                original_name=filename,
                stored_name=unique_filename,
            )
        )

    return uploaded_files


def remove_files(
    files_to_delete: list, uploaded_files: list[ReferenceFile], upload_folder: str
) -> list[ReferenceFile]:
    """Remove files from the uploaded files"""
    if not files_to_delete:
        return uploaded_files

    remaining_files = []
    for file in uploaded_files:
        if file.stored_name in files_to_delete or file.filename in files_to_delete:
            try:
                file_path = os.path.join(upload_folder, file.stored_name)
                os.remove(file_path)
            except (OSError, FileNotFoundError):
                pass
        else:
            remaining_files.append(file)

    return remaining_files
