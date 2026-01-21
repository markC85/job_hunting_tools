import pyperclip
import json
import datetime
import logging
import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials


class ColorFormatter(logging.Formatter):
    """
    Custom logging formatter to add colors based on log level
    """
    RESET = "\033[0m"
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[33m",  # Yellow
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[31m",  # Red
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)

def start_logger(level: str = "DEBUG") -> logging.Logger:
    """
    This will start the logger for the application

    Args:
        level (str): The logging level to use

    Returns:
        logging.Logger: The configured logger
    """
    # set logger data
    LOG = logging.getLogger(__name__)
    LOG.setLevel(level)

    # Attach the handler to your logger
    if not LOG.hasHandlers():
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # THIS IS THE KEY: use ColorFormatter, not plain Formatter
        formatter = ColorFormatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)

        LOG.addHandler(ch)

    return LOG

def log_google_sheet_data(
        creds_path: str,
        scopes: list,
        sheet_name: str,
        data: list,
        tab_name: None | str = None) -> None:
    """
    This will log data to a google sheet

    Args:
        creds_path (str): The path to the service account credentials JSON file
        scopes (list): The list of scopes to use for the authentication
        sheet_name (str): The name of the google sheet to update
        data (list): The data to append to the google sheet
        tab_name (str | None): The name of the tab to update, if None, the first tab will be used
    """
    client = authenticate_google_sheets(creds_path, scopes)
    update_google_sheet(client, sheet_name, data, tab_name)

    LOG.info(f"Google sheet '{sheet_name}' updated successfully.")

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

def write_json_file(position: str, company_name: str, json_file_path: Path) -> None:
    """
    This will write a JSON file in a directory given
    """
    # get the text from the clipboard
    job_description = pyperclip.paste()

    # build json data structure
    job_data = {
        "job_description": job_description,
        "position_name": position,
        "company_name": company_name,
        "date_applied": datetime.datetime.now().isoformat(),
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

def log_job_applied_for(company_name: str, position: str) -> None:
    """
    This will log a job information I need to keep track of
    what a job is asking for as requirements for future details.

    Args:
        company_name (str): The name of the company the job is for
        position (str): The position name of the job
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
        jsong_name =  f"{file_name.replace(" ", "_").lower()}_{new_file_index:03d}_job_description.json"

    json_file_path = path_structure / jsong_name

    write_json_file(position, company_name, json_file_path)

    LOG.info(f"Job description saved!\nFile: {jsong_name}\nPath: {path_structure}")


if __name__ == "__main__":
    # start the logger
    LOG = start_logger()

    # save the information for the job add
    company_name = "Artificial Core"
    position = "3D Character Animator"
    log_job_applied_for(company_name, position)

    # update google sheet with job application info
    today = datetime.date.today().strftime("%m/%d/%Y").lstrip("0").replace("/0", "/")
    website = "https://artificialcore.com/"
    #website = "N/A"

    job_email = "jobs@artificialcore.com"

    #location = "On Site"
    #location = "Hybrid"
    location = "Remote"
    #location = "N/A"

    work_location = "Athens, Attica, Greece| Kyiv, Kyiv City, Ukraine| Amsterdam, North Holland, Netherlands"

    industry = "Game Development"
    #industry = "Film"
    #industry = "TV"
    date = today

    data = [
        [
            position,
            company_name,
            website,
            job_email,
            location,
            work_location,
            industry,
            date
        ],
    ]

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_path = r"D:\storage\programming\python\job_hunting_tools\credentials\update-project-484819-d526e259cada.json"
    sheet_name = "Job log"
    tab_name = "Jobs Applied For"

    #log_google_sheet_data(creds_path,scopes,sheet_name,data,tab_name)