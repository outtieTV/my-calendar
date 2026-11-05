import sys
import os
import calendar
import configparser

from datetime import date

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QDialog,
    QFormLayout,
    QDateEdit,
    QTimeEdit,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QDialogButtonBox,
    QSizePolicy,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

# Store config.ini in the same directory as this script,
# regardless of the current working directory.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.ini")

REPEAT_OPTIONS = [
    "None",
    "Every day",
    "Every week",
    "Every other week",
    "Every month",
]


# ---------------------------------------------------------
# Event dialog
# ---------------------------------------------------------

class EventDialog(QDialog):
    """
    Dialog for creating or editing a calendar event.

    The date is initialized with the selected calendar day.
    The user can change the date, time, repeat interval,
    title, and description.
    """

    def __init__(self, selected_date, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Event")
        self.setModal(True)
        self.resize(420, 400)

        self.setup_ui(selected_date)

    def setup_ui(self, selected_date):
        """Create and arrange the event input widgets."""

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Date
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("MMMM d, yyyy")
        self.date_edit.setDate(selected_date)

        form_layout.addRow("Date:", self.date_edit)

        # Time
        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(9, 0))

        form_layout.addRow("Time:", self.time_edit)

        # Repeat
        self.repeat_combo = QComboBox(self)
        self.repeat_combo.addItems(REPEAT_OPTIONS)

        form_layout.addRow("Repeat:", self.repeat_combo)

        # Title
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter event title")

        form_layout.addRow("Title:", self.title_edit)

        # Description
        self.description_edit = QTextEdit(self)
        self.description_edit.setPlaceholderText(
            "Enter event description..."
        )
        self.description_edit.setMinimumHeight(100)

        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        # Save and Cancel buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )

        self.button_box.button(
            QDialogButtonBox.StandardButton.Save
        ).setText("Save")

        self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        ).setText("Cancel")

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        """Ensure the event title is not empty before saving."""

        title = self.title_edit.text().strip()

        if not title:
            QMessageBox.warning(
                self,
                "Missing Title",
                "Please enter an event title.",
            )

            self.title_edit.setFocus()
            return

        self.accept()

    def get_event_data(self):
        """Return the entered event information as a dictionary."""

        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": self.time_edit.time().toString("HH:mm"),
            "repeat": self.repeat_combo.currentText(),
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText(),
        }


# ---------------------------------------------------------
# Main calendar application
# ---------------------------------------------------------

class CalendarApp(QMainWindow):
    """
    Main calendar window.

    Features:
        - Month navigation
        - Calendar day selection
        - Today highlighting
        - Event creation
        - Persistent event storage in config.ini
        - Event indicators and tooltips
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Calendar")
        self.resize(700, 600)

        # Current displayed month.
        self.current_date = QDate.currentDate()

        # Active selected date.
        self.selected_date = QDate.currentDate()

        # List containing all loaded and saved events.
        self.events = []

        # Dictionary mapping QDate objects to day buttons.
        self.day_buttons = {}

        # Load saved events before building the calendar.
        self.load_events()

        # Build the main window.
        self.setup_ui()

        # Display the current month.
        self.update_calendar()

        # Apply application styling.
        self.apply_stylesheet()

    # -----------------------------------------------------
    # Main window setup
    # -----------------------------------------------------

    def setup_ui(self):
        """Create the top, middle, and bottom panels."""

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # -------------------------------------------------
        # Top panel: month navigation
        # -------------------------------------------------

        top_panel = QWidget(self)
        top_panel.setObjectName("topPanel")

        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 10, 10, 10)

        self.previous_button = QPushButton("<")
        self.previous_button.setFixedSize(45, 40)
        self.previous_button.setToolTip("Previous month")

        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.month_label.setFont(
            QFont("Arial", 16, QFont.Weight.Bold)
        )

        self.month_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.next_button = QPushButton(">")
        self.next_button.setFixedSize(45, 40)
        self.next_button.setToolTip("Next month")

        self.previous_button.clicked.connect(
            self.previous_month
        )

        self.next_button.clicked.connect(
            self.next_month
        )

        top_layout.addWidget(self.previous_button)
        top_layout.addWidget(self.month_label, 1)
        top_layout.addWidget(self.next_button)

        main_layout.addWidget(top_panel)

        # -------------------------------------------------
        # Middle panel: calendar grid
        # -------------------------------------------------

        calendar_panel = QWidget(self)
        calendar_panel.setObjectName("calendarPanel")

        calendar_layout = QVBoxLayout(calendar_panel)
        calendar_layout.setContentsMargins(10, 10, 10, 10)
        calendar_layout.setSpacing(5)

        # Weekday headings.
        weekday_layout = QGridLayout()
        weekday_layout.setSpacing(5)

        weekdays = [
            "Sun",
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
        ]

        for column, weekday in enumerate(weekdays):
            label = QLabel(weekday)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            label.setFont(
                QFont("Arial", 10, QFont.Weight.Bold)
            )

            weekday_layout.addWidget(label, 0, column)

        calendar_layout.addLayout(weekday_layout)

        # Day buttons are dynamically rebuilt for each month.
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(5)

        calendar_layout.addLayout(self.calendar_grid)

        # Allow the calendar to expand vertically.
        calendar_layout.addStretch()

        main_layout.addWidget(calendar_panel, 1)

        # -------------------------------------------------
        # Bottom panel: add event
        # -------------------------------------------------

        bottom_panel = QWidget(self)
        bottom_panel.setObjectName("bottomPanel")

        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 10, 10, 10)

        bottom_layout.addStretch()

        self.add_event_button = QPushButton("Add Event")
        self.add_event_button.setMinimumSize(150, 45)

        self.add_event_button.clicked.connect(
            self.add_event
        )

        bottom_layout.addWidget(self.add_event_button)

        bottom_layout.addStretch()

        main_layout.addWidget(bottom_panel)

    # -----------------------------------------------------
    # Stylesheet
    # -----------------------------------------------------

    def apply_stylesheet(self):
        """Apply a modern, light‑theme stylesheet with readable dropdown text."""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f4f6f8;
            }

            QWidget#topPanel,
            QWidget#calendarPanel,
            QWidget#bottomPanel {
                background-color: #ffffff;
                border-radius: 10px;
            }

            /* ----- generic text ------------------------------------------------- */
            QLabel,
            QLineEdit,
            QTextEdit,
            QDateEdit,
            QTimeEdit,
            QComboBox {
                color: #263238;            /* dark text on white background */
            }

            /* ----- dropdown list (popup) --------------------------------------- */
            QComboBox QAbstractItemView,
            QComboBox QAbstractItemView::item {
                background-color: white;   /* same as the combo box */
                color: #263238;            /* dark, readable text */
            }

            /* ----- push‑buttons ------------------------------------------------- */
            QPushButton {
                background-color: #e8edf2;
                color: #263238;
                border: 1px solid #d4dce5;
                border-radius: 6px;
                padding: 6px;
                font-size: 11pt;
            }

            QPushButton:hover {
                background-color: #dbe6f2;
            }

            QPushButton:pressed {
                background-color: #c9d8e8;
            }

            /* ----- day cells ---------------------------------------------------- */
            QPushButton#dayButton {
                background-color: #ffffff;
                border: 1px solid #e0e5eb;
                border-radius: 6px;
                color: #263238;
                font-size: 11pt;
            }

            QPushButton#dayButton:hover {
                background-color: #eaf2fb;
                border: 1px solid #7ba7d8;
            }

            QPushButton#dayButton[today="true"] {
                background-color: #2878d0;
                color: white;
                border: 2px solid #155ba0;
                font-weight: bold;
            }

            QPushButton#dayButton[selected="true"] {
                background-color: #f39c35;
                color: white;
                border: 2px solid #d97706;
                font-weight: bold;
            }

            QPushButton#dayButton[today="true"][selected="true"] {
                background-color: #e58a22;
                color: white;
                border: 3px solid #155ba0;
                font-weight: bold;
            }

            QPushButton#dayButton[hasEvents="true"] {
                font-weight: bold;
            }

            QPushButton#dayButton:disabled {
                background-color: #f0f2f4;
                color: #b0b8c0;
                border: 1px solid #e5e8eb;
            }

            QPushButton#addEventButton {
                background-color: #2878d0;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }

            QPushButton#addEventButton:hover {
                background-color: #1c65b4;
            }

            QDialog {
                background-color: #f4f6f8;
            }

            QLineEdit,
            QTextEdit,
            QDateEdit,
            QTimeEdit,
            QComboBox {
                background-color: white;
                border: 1px solid #d4dce5;
                border-radius: 5px;
                padding: 5px;
            }

            QLineEdit:focus,
            QTextEdit:focus,
            QDateEdit:focus,
            QTimeEdit:focus,
            QComboBox:focus {
                border: 1px solid #2878d0;
            }

            QDialogButtonBox QPushButton {
                min-width: 80px;
            }
            """
        )



        self.add_event_button.setObjectName("addEventButton")

    # -----------------------------------------------------
    # Month navigation
    # -----------------------------------------------------

    def previous_month(self):
        """Move the calendar backward by one month."""

        self.current_date = self.current_date.addMonths(-1)

        self.update_calendar()

    def next_month(self):
        """Move the calendar forward by one month."""

        self.current_date = self.current_date.addMonths(1)

        self.update_calendar()

    # -----------------------------------------------------
    # Calendar rebuilding
    # -----------------------------------------------------

    def update_calendar(self):
        """
        Rebuild the calendar grid for the currently displayed
        month.

        QDate is used for month calculations, including leap
        years and varying month lengths.
        """

        self.month_label.setText(
            self.current_date.toString("MMMM yyyy")
        )

        # Remove old day buttons.
        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.day_buttons.clear()

        # Determine the month and year.
        year = self.current_date.year()
        month = self.current_date.month()

        first_day = QDate(year, month, 1)

        # Number of days in the month.
        days_in_month = first_day.daysInMonth()

        # Qt weekday: Monday=1 ... Sunday=7.
        # Convert to Sunday=0 ... Saturday=6.
        first_weekday = first_day.dayOfWeek() % 7

        # -------------------------------------------------
        # Build day buttons
        # -------------------------------------------------

        for day in range(1, days_in_month + 1):

            current_day = QDate(year, month, day)

            button = QPushButton(str(day))

            button.setObjectName("dayButton")

            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            button.setMinimumSize(65, 55)

            button.setProperty("today", False)
            button.setProperty("selected", False)
            button.setProperty("hasEvents", False)

            button.clicked.connect(
                lambda checked=False, d=current_day:
                self.select_day(d)
            )

            # Calendar grid position.
            position = first_weekday + day - 1

            row = position // 7
            column = position % 7

            self.calendar_grid.addWidget(
                button,
                row,
                column,
            )

            self.day_buttons[current_day] = button

            # Highlight today.
            if current_day == QDate.currentDate():
                button.setProperty("today", True)

            # Restore selection when rebuilding the calendar.
            if current_day == self.selected_date:
                button.setProperty("selected", True)

            # Display saved events.
            day_events = self.get_events_for_date(current_day)

            if day_events:
                button.setProperty("hasEvents", True)

                titles = "\n".join(
                    event["title"]
                    for event in day_events
                )

                button.setText(f"{day} •")

                button.setToolTip(
                    f"Events:\n{titles}"
                )

            else:
                button.setToolTip(
                    current_day.toString("dddd, MMMM d, yyyy")
                )

            # Refresh stylesheet properties.
            button.style().unpolish(button)
            button.style().polish(button)

        # Force layout updates.
        self.calendar_grid.invalidate()
        self.calendar_grid.activate()

    # -----------------------------------------------------
    # Day selection
    # -----------------------------------------------------

    def select_day(self, selected_date):
        """Select one date and visually update the grid."""

        self.selected_date = selected_date

        # Update button states.
        for date_value, button in self.day_buttons.items():

            is_selected = date_value == selected_date

            button.setProperty(
                "selected",
                is_selected,
            )

            button.style().unpolish(button)
            button.style().polish(button)

        # If a date in another month was selected, update
        # the displayed month.
        if (
            selected_date.year() != self.current_date.year()
            or selected_date.month() != self.current_date.month()
        ):
            self.current_date = QDate(
                selected_date.year(),
                selected_date.month(),
                1,
            )

            self.update_calendar()

    # -----------------------------------------------------
    # Add event
    # -----------------------------------------------------

    def add_event(self):
        """
        Open the event dialog.

        The selected calendar date is used as the initial
        date in the dialog.
        """

        dialog = EventDialog(
            self.selected_date,
            self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        event_data = dialog.get_event_data()

        # Create a new unique event section.
        event_id = self.get_next_event_id()

        event_data["id"] = event_id

        # Add the event to memory.
        self.events.append(event_data)

        # Persist all events.
        if not self.save_events():
            # Roll back the in-memory addition if saving
            # fails, so memory and disk stay consistent.
            self.events.pop()

            return

        # If the user changed the event date in the dialog,
        # display that month and select the new event date.
        event_date = QDate.fromString(
            event_data["date"],
            "yyyy-MM-dd",
        )

        self.selected_date = event_date

        self.current_date = QDate(
            event_date.year(),
            event_date.month(),
            1,
        )

        self.update_calendar()

    # -----------------------------------------------------
    # Event storage
    # -----------------------------------------------------

    def get_next_event_id(self):
        """
        Return the next available event section name.

        Existing event IDs are retained when loading and
        saving, preventing sections from being overwritten.
        """

        existing_ids = []

        for event in self.events:
            event_id = event.get("id", "")

            if event_id.startswith("event_"):
                try:
                    number = int(event_id.split("_", 1)[1])
                    existing_ids.append(number)
                except ValueError:
                    pass

        next_number = max(existing_ids, default=0) + 1

        return f"event_{next_number}"

    def load_events(self):
        """
        Load events from config.ini.

        Each event is stored in a separate section:

            [event_1]
            date = 2026-11-05
            time = 09:00
            repeat = None
            title = Example
            description = Example description
        """

        self.events = []

        config = configparser.ConfigParser()

        if not os.path.exists(CONFIG_FILE):
            return

        try:
            config.read(
                CONFIG_FILE,
                encoding="utf-8",
            )

            for section in config.sections():

                if not section.startswith("event_"):
                    continue

                event = {
                    "id": section,
                    "date": config.get(
                        section,
                        "date",
                        fallback="",
                    ),
                    "time": config.get(
                        section,
                        "time",
                        fallback="09:00",
                    ),
                    "repeat": config.get(
                        section,
                        "repeat",
                        fallback="None",
                    ),
                    "title": config.get(
                        section,
                        "title",
                        fallback="",
                    ),
                    "description": config.get(
                        section,
                        "description",
                        fallback="",
                ),
                }

                # Validate the date.
                event_date = QDate.fromString(
                    event["date"],
                    "yyyy-MM-dd",
                )

                if not event_date.isValid():
                    continue

                # Validate time.
                event_time = QTime.fromString(
                    event["time"],
                    "HH:mm",
                )

                if not event_time.isValid():
                    event["time"] = "09:00"

                # Validate repeat option.
                if event["repeat"] not in REPEAT_OPTIONS:
                    event["repeat"] = "None"

                self.events.append(event)

        except (OSError, configparser.Error) as error:

            QMessageBox.warning(
                self,
                "Load Error",
                f"Could not load calendar events:\n{error}",
            )

    def save_events(self):
        """
        Save all events to config.ini.

        The configuration file is written to a temporary
        file first and then replaced atomically.
        """

        config = configparser.ConfigParser()

        # Preserve all event sections.
        for event in self.events:

            section = event.get("id")

            if not section:
                continue

            config[section] = {
                "date": event["date"],
                "time": event["time"],
                "repeat": event["repeat"],
                "title": event["title"],
                "description": event["description"],
            }

        # Temporary file in the same directory.
        temporary_file = CONFIG_FILE + ".tmp"

        try:

            with open(
                temporary_file,
                "w",
                encoding="utf-8",
            ) as file:

                config.write(file)

            # Replace config.ini with the complete file.
            os.replace(
                temporary_file,
                CONFIG_FILE,
            )

            return True

        except OSError as error:

            QMessageBox.critical(
                self,
                "Save Error",
                (
                    "Could not save calendar events.\n\n"
                    f"File: {CONFIG_FILE}\n\n"
                    f"Error: {error}"
                ),
            )

            # Remove incomplete temporary file.
            try:
                if os.path.exists(temporary_file):
                    os.remove(temporary_file)
            except OSError:
                pass

            return False

    # -----------------------------------------------------
    # Event lookup
    # -----------------------------------------------------

    def get_events_for_date(self, target_date):
        """
        Return events occurring on a specified date.

        Repeat options are interpreted as:
            None             - Only the original date
            Every day        - Daily
            Every week       - Weekly
            Every other week  - Every 14 days
            Every month      - Same day of each month

        Monthly recurrence skips months that do not contain
        the original day number.
        """

        matching_events = []

        for event in self.events:

            original_date = QDate.fromString(
                event["date"],
                "yyyy-MM-dd",
            )

            if not original_date.isValid():
                continue

            repeat = event.get("repeat", "None")

            if repeat == "None":

                occurs = target_date == original_date

            elif repeat == "Every day":

                occurs = target_date >= original_date

            elif repeat == "Every week":

                occurs = (
                    target_date >= original_date
                    and original_date.daysTo(target_date) % 7 == 0
                )

            elif repeat == "Every other week":

                occurs = (
                    target_date >= original_date
                    and original_date.daysTo(target_date) % 14 == 0
                )

            elif repeat == "Every month":

                occurs = self.is_monthly_occurrence(
                    original_date,
                    target_date,
                )

            else:

                occurs = target_date == original_date

            if occurs:
                matching_events.append(event)

        return matching_events

    @staticmethod
    def is_monthly_occurrence(original_date, target_date):
        """
        Check whether target_date is a valid monthly
        occurrence of original_date.

        For example, an event on January 31 will not
        occur in February because February has no day 31.
        """

        if target_date < original_date:
            return False

        if target_date.day() != original_date.day():
            return False

        month_difference = (
            (target_date.year() - original_date.year()) * 12
            + target_date.month()
            - original_date.month()
        )

        return month_difference >= 0

    # -----------------------------------------------------
    # Application entry point
    # -----------------------------------------------------

    def closeEvent(self, event):
        """
        Ensure all events are persisted before closing.

        Events are already saved when created, but this
        provides an additional safety check.
        """

        if self.save_events():
            event.accept()
        else:
            event.ignore()


# ---------------------------------------------------------
# Run application
# ---------------------------------------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName("PyQt6 Calendar")

    window = CalendarApp()
    window.show()

    sys.exit(app.exec())
