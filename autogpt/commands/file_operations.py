"""File operations for AutoGPT"""
import os
import os.path
from pathlib import Path
from typing import Generator, List

# Set a dedicated folder for file I/O
WORKING_DIRECTORY = Path(os.getcwd()) / "auto_gpt_workspace"

# Create the directory if it doesn't exist
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)

LOG_FILE = "file_logger.txt"
LOG_FILE_PATH = WORKING_DIRECTORY / LOG_FILE
WORKING_DIRECTORY = str(WORKING_DIRECTORY)


def check_duplicate_operation(operation: str, filename: str) -> bool:
    """Check if the operation has already been performed on the given file

    Args:
        operation (str): The operation to check for
        filename (str): The name of the file to check for

    Returns:
        bool: True if the operation has already been performed on the file
    """
    log_content = read_file(LOG_FILE)
    log_entry = f"{operation}: {filename}\n"
    return log_entry in log_content


def log_operation(operation: str, filename: str) -> None:
    """Log the file operation to the file_logger.txt

    Args:
        operation (str): The operation to log
        filename (str): The name of the file the operation was performed on
    """
    log_entry = f"{operation}: {filename}\n"

    # Create the log file if it doesn't exist
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("File Operation Logger ")

    append_to_file(LOG_FILE, log_entry)


def safe_join(base: str, *paths) -> str:
    """Join one or more path components intelligently.

    Args:
        base (str): The base path
        *paths (str): The paths to join to the base path

    Returns:
        str: The joined path
    """
    new_path = os.path.join(base, *paths)
    norm_new_path = os.path.normpath(new_path)

    if os.path.commonprefix([base, norm_new_path]) != base:
        raise ValueError("Attempted to access outside of working directory.")

    return norm_new_path


def split_file(
    content: str, max_length: int = 4000, overlap: int = 0
) -> Generator[str, None, None]:
    """
    Split text into chunks of a specified maximum length with a specified overlap
    between chunks.

    :param content: The input text to be split into chunks
    :param max_length: The maximum length of each chunk,
        default is 4000 (about 1k token)
    :param overlap: The number of overlapping characters between chunks,
        default is no overlap
    :return: A generator yielding chunks of text
    """
    start = 0
    content_length = len(content)

    while start < content_length:
        end = start + max_length
        if end + overlap < content_length:
            chunk = content[start : end + overlap]
        else:
            chunk = content[start:content_length]
        yield chunk
        start += max_length - overlap


def read_file(filename: str) -> str:
    """Read a file and return the contents

    Args:
        filename (str): The name of the file to read

    Returns:
        str: The contents of the file
    """
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error: {str(e)}"


def ingest_file(
    filename: str, memory, max_length: int = 4000, overlap: int = 200
) -> None:
    """
    Ingest a file by reading its content, splitting it into chunks with a specified
    maximum length and overlap, and adding the chunks to the memory storage.

    :param filename: The name of the file to ingest
    :param memory: An object with an add() method to store the chunks in memory
    :param max_length: The maximum length of each chunk, default is 4000
    :param overlap: The number of overlapping characters between chunks, default is 200
    """
    try:
        print(f"Working with file {filename}")
        content = read_file(filename)
        content_length = len(content)
        print(f"File length: {content_length} characters")

        chunks = list(split_file(content, max_length=max_length, overlap=overlap))

        num_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            print(f"Ingesting chunk {i + 1} / {num_chunks} into memory")
            memory_to_add = (
                f"Filename: {filename}\n" f"Content part#{i + 1}/{num_chunks}: {chunk}"
            )

            memory.add(memory_to_add)

        print(f"Done ingesting {num_chunks} chunks from {filename}.")
    except Exception as e:
        print(f"Error while ingesting file '{filename}': {str(e)}")


def write_to_file(filename: str, text: str) -> str:
    """Write text to a file

    Args:
        filename (str): The name of the file to write to
        text (str): The text to write to the file

    Returns:
        str: A message indicating success or failure
    """
    if check_duplicate_operation("write", filename):
        return "Error: File has already been updated."
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        log_operation("write", filename)
        return "File written to successfully."
    except Exception as e:
        return f"Error: {str(e)}"


def append_to_file(filename: str, text: str) -> str:
    """Append text to a file

    Args:
        filename (str): The name of the file to append to
        text (str): The text to append to the file

    Returns:
        str: A message indicating success or failure
    """
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        with open(filepath, "a") as f:
            f.write(text)
        log_operation("append", filename)
        return "Text appended successfully."
    except Exception as e:
        return f"Error: {str(e)}"


def delete_file(filename: str) -> str:
    """Delete a file

    Args:
        filename (str): The name of the file to delete

    Returns:
        str: A message indicating success or failure
    """
    if check_duplicate_operation("delete", filename):
        return "Error: File has already been deleted."
    try:
        filepath = safe_join(WORKING_DIRECTORY, filename)
        os.remove(filepath)
        log_operation("delete", filename)
        return "File deleted successfully."
    except Exception as e:
        return f"Error: {str(e)}"


def search_files(directory: str) -> List[str]:
    """Search for files in a directory

    Args:
        directory (str): The directory to search in

    Returns:
        List[str]: A list of files found in the directory
    """
    found_files = []

    if directory in {"", "/"}:
        search_directory = WORKING_DIRECTORY
    else:
        search_directory = safe_join(WORKING_DIRECTORY, directory)

    for root, _, files in os.walk(search_directory):
        for file in files:
            if file.startswith("."):
                continue
            relative_path = os.path.relpath(os.path.join(root, file), WORKING_DIRECTORY)
            found_files.append(relative_path)

    return found_files

def edit_line(filename, line_numbers, action, old_text=None, new_text=None, debug=True):
    """
    Insert, modify, or delete one or more lines of a file.

    Args:
        filename (str): The name of the file to be edited.
        line_numbers (int or list): The line number(s) of the line(s) to be edited. If 'start' is provided, the line number is assumed to be 1.
        action (str): The action to be taken on the line. Must be one of 'insert', 'modify', or 'delete'.
        new_text (str): The new text to insert or replace the old text with. Required for 'insert' and 'modify' actions.
        old_text (str): The old text to be replaced. Required for 'modify' action.
        debug (bool): Whether to output a diff of the old and new content of the file after the edit has been made.

    Returns:
        str: A message indicating success or failure.
    """

    actions = ['add', 'insert', 'modify', 'replace', 'delete']

    filepath = safe_join(WORKING_DIRECTORY, filename)
    if not os.path.isfile(filepath):
        return f"Error: File '{filepath}' does not exist."

    if not isinstance(line_numbers, str):
        return "Error: Invalid line number(s) provided."

    if action not in actions:
        return f"Error: Invalid action. Must be one of {actions}."

    if action in ['add', 'replace', 'insert', 'modify'] and new_text is None:
        return f"Error: new_text must be provided for 'add', 'insert' and 'modify' actions."

    if action in ['replace', 'modify'] and old_text is None:
        return "Error: old_text must be provided for 'modify' action."

    try:
        if "," in line_numbers:
            line_numbers = list(map(int, line_numbers.split(",")))
        else:
            line_numbers = [int(line_numbers)]
    except ValueError:
        return "Error: Invalid line number(s) format. Must be an int or a list of ints."

    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    original_lines = lines.copy()

    for line_number in line_numbers:
        if line_number < 1 or line_number > len(lines):
            return f"Error: Line number {line_number} is out of range."

        if action in  ['add', 'insert']:
            lines.insert(line_number - 1, new_text + '\n')
        elif action in ['replace', 'modify']:
            if old_text not in lines[line_number - 1]:
                return f"Error: old_text '{old_text}' not found on line {line_number} '{lines[line_number - 1]}'."
            lines[line_number - 1] = lines[line_number - 1].replace(old_text, new_text)
        elif action == 'delete':
            lines.pop(line_number - 1)

    with open(filepath + '.bak', 'w') as backup:
        backup.writelines(original_lines)

    with open(filepath, 'w') as f:
        f.writelines(lines)

    if debug:
        with open(filepath, 'r') as f:
            new_lines = f.readlines()

        diff = difflib.unified_diff(original_lines, new_lines, lineterm='')
        print("\n".join(list(diff)))

    return f"File: {filename}, Action: {action.capitalize()}, Result: {'Success.' if original_lines != lines else 'No changes made'}"
