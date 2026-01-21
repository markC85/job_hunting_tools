import datetime
import json
import sys
import webbrowser
from pathlib import Path

from job_hunting_tools.src.job_hunting_tools_backend import (
    log_google_sheet_data,
    log_job_applied_for,
)
from job_hunting_tools.src.logger_setup import start_logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QComboBox,
    QMessageBox,
    QDialog,
    QPlainTextEdit
)

LOG = start_logger()

_app = None
_window = None

class AboutDialog(QDialog):
    def __init__(self, version: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About Job Hunting Tools")
        self.setFixedSize(420, 300)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("<b>Job Hunting Tools</b>")
        version = QLabel(f"Version {version}")

        description = QLabel(
            "Job Hunting Tools is a utility to manage job applications, "
            "presets, and record updates. Built with Python and PySide6. "
            "I got tiered of repeating the process so I started thinking of"
            "ways to automate this process so this is what I built I hope it"
            "helps you out too!"
        )
        description.setWordWrap(True)

        links = QLabel(
            """
            <a href="https://github.com/markC85">GitHub</a><br>
            <a href="https://mark_conrad.artstation.com">Animation Portfolio</a>
            <a href="http://www.linkedin.com/in/markaconrad">Linkedin Profile</a>
            """
        )
        links.setOpenExternalLinks(True)
        links.setTextInteractionFlags(Qt.TextBrowserInteraction)
        links.setCursor(Qt.PointingHandCursor)

        email = QLabel("Email: markconrad.animator@gmail.com")
        email.setTextInteractionFlags(Qt.TextBrowserInteraction)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(description)
        layout.addSpacing(10)
        layout.addWidget(links)
        layout.addWidget(email)
        layout.addStretch()
        layout.addWidget(close_btn)

class MainWindow(QMainWindow):
    """
    Main application window
    """
    def __init__(self):
        super().__init__()

        self.version = "1.0.0"
        self.setWindowTitle(f"Jog Hunting Tools {self.version}")
        self.resize(400, 800)

        self._ui_widgets()
        self._create_menu()
        self._create_connections()

    def _ui_widgets(self) -> None:
        """
        UI fields and layout
        """
        # button style sheets
        button_style = """
            QPushButton {
                background-color: #f39c12;   /* orange */
                color: black;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;   /* darker orange */
            }
            QPushButton:pressed {
                background-color: #d35400;   /* even darker */
            }
        """

        # Scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        # Central widget (required for QMainWindow)
        """central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)"""

        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.update_records_btn = QPushButton("Updated Records")
        self.update_records_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;   /* green */
                color: black;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;   /* darker green */
            }
            QPushButton:pressed {
                background-color: #1e8449;   /* even darker */
            }
        """)
        self.set_date_btn = QPushButton("Set Date to Today")
        self.set_date_btn.setStyleSheet(button_style)
        self.set_google_sheet_credential_path_btn = QPushButton(
            "Set Google Sheet Credential Path"
        )
        self.set_google_sheet_credential_path_btn.setStyleSheet(button_style)

        tool_description = (
            "This tool helps job seekers manage and track their job applications.\n"
        )

        tool_description_label = QLabel(tool_description)
        states_description_label = QLabel("Current Tool Run Success:")
        self.states_lable = QLabel("<< States - you have not run me yet :) >>")

        labels_fields = [
            "Company Name:",
            "Position:",
            "Website:",
            "Job Email:",
            "Work Location:",
            "Company Location:",
            "Industry:",
            "Date:",
            "Google Sheet Credential Path:",
            "Google Sheet Name:",
            "Google Sheet Tab Name:",
            "Job Description:"
        ]

        self.job_description = QPlainTextEdit()
        self.job_description.setPlaceholderText(
            "Paste the job description here…"
        )

        main_layout.addWidget(tool_description_label)

        for label_name in labels_fields:
            label = QLabel(label_name)
            main_layout.addWidget(label)
            if label_name == "Date:":
                self.date_field = QLineEdit()
                self.date_field.setText(
                    f"{datetime.date.today().strftime('%m/%d/%Y').lstrip('0').replace('/0', '/')}"
                )
                main_layout.addWidget(self.date_field)
                main_layout.addWidget(self.set_date_btn)
            elif label_name == "Google Sheet Credential Path:":
                self.google_sheet_credential_path_field = QLineEdit()
                main_layout.addWidget(self.google_sheet_credential_path_field)
                main_layout.addWidget(self.set_google_sheet_credential_path_btn)
            elif label_name == "Work Location:":
                self.work_mode_dropdown = QComboBox()
                self.work_mode_dropdown.addItems(["Onsite", "Hybrid", "Remote"])
                main_layout.addWidget(self.work_mode_dropdown)
            elif label_name == "Job Description:":
                main_layout.addWidget(self.job_description)
            else:
                field = QLineEdit()
                main_layout.addWidget(field)

        main_layout.addWidget(self.update_records_btn)
        main_layout.addWidget(states_description_label)
        main_layout.addWidget(self.states_lable)

        # Set the content widget as the scroll area's widget
        scroll_area.setWidget(content_widget)
        self.setCentralWidget(scroll_area)

    def _create_menu(self) -> None:
        """
        Create the menu bar with File -> Exit
        """

        # Create the menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        tool_menu = menu_bar.addMenu("Tools")
        help_menu = menu_bar.addMenu("Help")

        # tool menu options
        self.cover_letter_generator = QAction("Cover Letter Generator", self)
        self.cover_letter_generator.setStatusTip("Open the Cover Letter Generator Tool")

        # about menu options
        self.about_project = QAction("About", self)
        self.about_project.setStatusTip("About this project")

        # exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Exit the application")

        # save fields presets
        self.save_preset = QAction("Save Preset", self)
        self.save_preset.setShortcut("Ctrl+S")
        self.save_preset.setStatusTip("Save fields preset")

        # load fields presets
        self.load_preset = QAction("Load Preset", self)
        self.load_preset.setShortcut("Ctrl+O")
        self.load_preset.setStatusTip("Load fields preset")

        # Add the action to the File menu
        file_menu.addAction(self.save_preset)
        file_menu.addAction(self.load_preset)
        file_menu.addAction(self.exit_action)

        # Add the action to the About menu
        help_menu.addAction(self.about_project)

        # Add the action to the Tools menu
        tool_menu.addAction(self.cover_letter_generator)

    def _create_connections(self) -> None:
        """
        Connect signals (events) to methods.
        """
        current_date = f"{datetime.date.today().strftime('%m/%d/%Y').lstrip('0').replace('/0', '/')}"

        self.update_records_btn.clicked.connect(self._update_records)
        self.set_google_sheet_credential_path_btn.clicked.connect(self._set_google_sheet_credential_path)
        self.set_date_btn.clicked.connect(lambda: self.date_field.setText(current_date))

        self.save_preset.triggered.connect(self._save_field_presets)
        self.load_preset.triggered.connect(self._load_field_presets)
        self.exit_action.triggered.connect(self.close)

        self.cover_letter_generator.triggered.connect(lambda: webbrowser.open("https://sheetsresume.com/ai-cover-letter-generator"))

        self.about_project.triggered.connect(self._show_about_dialog)

    def _show_about_dialog(self):
        dlg = AboutDialog(self.version, self)
        dlg.exec()

    def _save_field_presets(self) -> None:
        """
        Save the current field presets to a file
        """
        field_data = self._gather_field_information()

        field_data["Work Location"] = self.work_mode_dropdown.currentText()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        with Path(file_path).open("w", encoding="utf-8") as f:
            json.dump(field_data, f, ensure_ascii=False, indent=4)

    def _set_google_sheet_credential_path(self) -> None:
        """
        This will set the google sheet credential path field
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Google Sheet Credential File", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        file_path = file_path.replace("/", "\\")

        self.google_sheet_credential_path_field.setText(file_path)

    def _load_field_presets(self) -> None:
        """
        This will load fields presets from a JSON file
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Preset", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        json_path = Path(file_path)

        try:
            with json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Could not read preset file:\n{e}\nJSON File: {json_path}",
            )
            return

        field_data = {}
        for widget in self.centralWidget().findChildren(QLineEdit):
            label = widget.previousInFocusChain()
            if isinstance(label, QLabel):
                field_data[label.text().strip(":")] = widget

        # Populate fields safely
        for key, widget in field_data.items():
            value = data.get(key, "")
            widget.setText(value)

        # set the dropdowns data
        value = data.get("Work Location")
        index = self.work_mode_dropdown.findText(value)
        if index != -1:
            self.work_mode_dropdown.setCurrentIndex(index)


    def _gather_field_information(self) -> dict:
        """
        Gather all the information from the UI fields

        Returns:
            field_data (dict): A dictionary with all the field names and their values
        """
        field_data = {}
        for widget in self.centralWidget().findChildren(QLineEdit):
            label = widget.previousInFocusChain()
            if isinstance(label, QLabel):
                field_data[label.text().strip(":")] = widget.text()

        return field_data

    def _update_records(self) -> None:
        """
        Update the records for Google Sheets and log the job application
        information based on what is in the current clip board of windows
        """
        field_data = self._gather_field_information()

        company_name = field_data["Company Name"]
        position = field_data["Position"]
        website = field_data["Website"]
        job_email = field_data["Job Email"]
        location = field_data["Company Location"]
        work_location = self.work_mode_dropdown.currentText()
        date = field_data["Date"]
        industry = field_data["Industry"]
        creds_path = field_data["Google Sheet Credential Path"]
        sheet_name = field_data["Google Sheet Name"]
        tab_name = field_data["Google Sheet Tab Name"]
        google_sheet_data = [
            [
                position,
                company_name,
                website,
                job_email,
                location,
                work_location,
                industry,
                date,
            ]
        ]

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        if not creds_path or not sheet_name:
            LOG.error(
                "Google Sheet Credential Path and Sheet Name are required to update records."
            )
            return

        job_description=self.job_description.toPlainText()
        job_log_result = log_job_applied_for(company_name, position, job_description)
        google_sheet_result = log_google_sheet_data(
            creds_path,
            scopes,
            sheet_name,
            google_sheet_data,
            tab_name
        )
        self.states_lable.setText(f"{job_log_result}\n{google_sheet_result}")

def show_ui() -> MainWindow:
    """
    This will show the main UI window for the application

    Returns:
        MainWindow: The main window instance
    """
    global _app, _window

    _app = QApplication.instance() or QApplication(sys.argv)

    if _window:
        LOG.debug("Main window already exists, closing the existing one.")
        _window.close()
        _window.deleteLater()

    _window = MainWindow()
    _window.show()

    return _window

# start the UI
show_ui()
sys.exit(_app.exec())