import json
import datetime
import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from job_hunting_tools.src.logger_setup import start_logger

LOG = start_logger()

def log_google_sheet_data(
        creds_path: str,
        scopes: list,
        sheet_name: str,
        data: list,
        tab_name: None | str = None) -> str:
    """
    This will log data to a google sheet

    Args:
        creds_path (str): The path to the service account credentials JSON file
        scopes (list): The list of scopes to use for the authentication
        sheet_name (str): The name of the google sheet to update
        data (list): The data to append to the google sheet
        tab_name (str | None): The name of the tab to update, if None, the first tab will be used

    Returns:
        msg (str): The message to log if the action worked out
    """
    client = authenticate_google_sheets(creds_path, scopes)

    try:
        update_google_sheet(client, sheet_name, data, tab_name)
        msg = f"Google sheet '{sheet_name}' updated successfully."
    except Exception as e:
        msg = f"An error occurred while updating the google sheet: {e}"

    LOG.info(msg)

    return msg

def authenticate_google_sheets(creds_path: str, scopes: list) -> gspread.Client:
    """
    This will authenticate the google sheets API using a service account

    Args:
        creds_path (str): The path to the service account credentials JSON file
        scopes (list): The list of scopes to use for the authentication

    Returns:
        gspread.Client: The authenticated gspread client
    """
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)

    return gspread.authorize(creds)

def update_google_sheet(
        google_client: gspread.Client,
        sheet_name: str,
        data: list,
        tab_name: None | str = None) -> None:
    """
    This will update a google sheet with the job information

    Args:
        google_client (gspread.Client): The authenticated gspread client
        data (list): The data to append to the google sheet
        sheet_name (str): The name of the google sheet to update
        tab_name (str | None): The name of the tab to update, if None, the first tab will be used
    """
    spreadsheet = google_client.open(sheet_name)
    if tab_name:
        sheet = spreadsheet.worksheet("Jobs Applied For")
    else:
        sheet = spreadsheet.get_worksheet(0)

    # insert a blank for first
    sheet.insert_row([], index=2)

    # add data to the sheet
    sheet.append_rows(
        data,
        table_range="A2",
    )

def write_json_file(position: str, company_name: str, json_file_path: Path, job_description: str, resume_used_path: str) -> None:
    """
    This will write a JSON file in a directory given

    Args:
        position (str): The position name of the job
        company_name (str): The name of the company the job is for
        json_file_path (Path): The path to the JSON file to write
        job_description (str): The job description text
        resume_used_path (str): The path to the resume used for the job application
    """

    # build json data structure
    job_data = {
        "job_description": job_description,
        "position_name": position,
        "company_name": company_name,
        "date_applied": datetime.datetime.now().isoformat(),
        "resume_used_path": resume_used_path,
    }

    # write the JSON file
    with json_file_path.open("w", encoding="utf-8") as f:
        json.dump(job_data, f, ensure_ascii=False, indent=4)

def create_folder_structure(company_name: str, job_root_path: str = r"D:\storage\documents\job_hunting\companies_applied_for", ) -> Path:
    """
    This will create the folder structure for the job application

    Args:
        company_name (str): The name of the company the job is for
        job_root_path (str): The root path where the job folders will be created
    """
    # standardize the company name to remove spaces and make lowercase
    company_name = company_name.replace(" ", "_").lower()

    # create the root path object
    root_path = Path(job_root_path)

    # create the company folder path
    company_folder_path = root_path / company_name

    # create the company folder if it does not exist
    company_folder_path.mkdir(parents=True, exist_ok=True)

    return company_folder_path

def copy_file_to_path(source_path: Path, destination_path: Path) -> None:
    """
    This will copy a file to a destination path

    Args:
        source_path (Path): The path to the source file
        destination_path (Path): The path to the destination folder
    """
    if not source_path.exists():
        LOG.error(f"Source file does not exist: {source_path}")
        return

    with source_path.open("rb") as src_file:
        with destination_path.open("wb") as dest_file:
            dest_file.write(src_file.read())

    LOG.debug(f"Copied file from {source_path} to {destination_path}")

def log_job_applied_for(company_name: str, position: str, job_description: str, resume_used_path: str) -> str:
    """
    This will log a job information I need to keep track of
    what a job is asking for as requirements for future details.

    Args:
        company_name (str): The name of the company the job is for
        position (str): The position name of the job
        job_description (str): The job description text
        resume_used_path (str): The path to the resume used for the job application

    Returns:
        msg (str): The message to log if the action worked out
    """
    # create the folder structure for the job applying for
    path_structure = create_folder_structure(company_name)

    # create a new JSON file with the information highlighted
    file_name = f"{company_name}_{position}"
    jsong_name = f"{file_name.replace(" ", "_").lower()}_{1:03d}_job_description.json"

    if (path_structure / jsong_name).exists():
        LOG.debug(f"Job description file already exists!\nFile: {jsong_name}\nPath: {path_structure}")
        files = [file for file in path_structure.iterdir() if file.is_file()]
        new_file_index = 1
        for file in files:
            if file.name.startswith(file_name.replace(" ", "_").lower()+"_"):
                new_file_index += 1
        jsong_name = f"{file_name.replace(' ', '_').lower()}_{new_file_index:03d}_job_description.json"

    json_file_path = path_structure / jsong_name

    try:
        write_json_file(position, company_name, json_file_path, job_description, resume_used_path)
        msg = f"Job description saved!\nFile: {jsong_name}\nPath: {path_structure}"
    except Exception as e:
        msg = f"Failed to save job description file.\nError: {e}"
        LOG.error(msg)

    LOG.info(msg)

    # copy the file to the location path
    scr_path = Path(resume_used_path)
    destination_path = Path(path_structure) / scr_path.name
    copy_file_to_path(scr_path, destination_path)

    return msg