import sys
import os
import configparser

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont
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
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
)


# =========================================================
# Configuration
# =========================================================

# config.ini is always stored beside this script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.ini")

REPEAT_OPTIONS = [
    "None",
    "Every day",
    "Every week",
    "Every other week",
    "Every month",
    "Every year"
]


# =========================================================
# Event Dialog
# =========================================================

class EventDialog(QDialog):
    """
    Dialog for creating a calendar event.

    Includes:
        Date
        Time
        Repeat
        Title
        Description
        Save
        Cancel
    """

    def __init__(self, selected_date, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add Event")
        self.setModal(True)
        self.resize(450, 430)

        self.setup_ui(selected_date)

    def setup_ui(self, selected_date):
        """Create the event input widgets."""

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
        self.description_edit.setMinimumHeight(120)

        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        # Save and Cancel
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

        self.button_box.accepted.connect(
            self.validate_and_accept
        )

        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        """Validate the event title."""

        if not self.title_edit.text().strip():
            QMessageBox.warning(
                self,
                "Missing Title",
                "Please enter an event title.",
            )

            self.title_edit.setFocus()
            return

        self.accept()

    def get_event_data(self):
        """Return the event data as a dictionary."""

        return {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": self.time_edit.time().toString("HH:mm"),
            "repeat": self.repeat_combo.currentText(),
            "title": self.title_edit.text().strip(),
            "description": self.description_edit.toPlainText(),
        }


# =========================================================
# Main Calendar Application
# =========================================================

class CalendarApp(QMainWindow):
    """
    Calendar application with:

        - Month navigation
        - Day selection
        - Today highlighting
        - Event creation
        - Selected-day event panel
        - Event persistence
        - Light and dark themes
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Calendar")
        self.resize(850, 750)

        # Current displayed month.
        self.current_date = QDate.currentDate()

        # Currently selected day.
        self.selected_date = QDate.currentDate()

        # Event collection.
        self.events = []

        # Calendar date -> button.
        self.day_buttons = {}

        # Current theme.
        self.dark_mode = False

        # Load persisted events.
        self.load_events()

        # Build UI.
        self.setup_ui()

        # Populate calendar and event panel.
        self.update_calendar()

        # Apply light theme.
        self.apply_stylesheet()

    # =====================================================
    # Main UI
    # =====================================================

    def setup_ui(self):
        """Create the main window panels."""

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # -------------------------------------------------
        # TOP PANEL
        # -------------------------------------------------

        self.top_panel = QWidget(self)
        self.top_panel.setObjectName("topPanel")

        top_layout = QHBoxLayout(self.top_panel)

        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(10)

        # Previous month.
        self.previous_button = QPushButton("<")
        self.previous_button.setFixedSize(45, 40)
        self.previous_button.setToolTip("Previous month")

        self.previous_button.clicked.connect(
            self.previous_month
        )

        # Month/year label.
        self.month_label = QLabel()

        self.month_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.month_label.setFont(
            QFont("Arial", 16, QFont.Weight.Bold)
        )

        self.month_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        # Next month.
        self.next_button = QPushButton(">")
        self.next_button.setFixedSize(45, 40)
        self.next_button.setToolTip("Next month")

        self.next_button.clicked.connect(
            self.next_month
        )

        # Theme toggle.
        self.theme_button = QPushButton("☾ Dark Mode")
        self.theme_button.setMinimumSize(120, 40)

        self.theme_button.setToolTip(
            "Switch between light and dark mode"
        )

        self.theme_button.clicked.connect(
            self.toggle_theme
        )

        top_layout.addWidget(self.previous_button)
        top_layout.addWidget(self.month_label, 1)
        top_layout.addWidget(self.next_button)
        top_layout.addWidget(self.theme_button)

        main_layout.addWidget(self.top_panel)

        # -------------------------------------------------
        # CALENDAR PANEL
        # -------------------------------------------------

        self.calendar_panel = QWidget(self)
        self.calendar_panel.setObjectName("calendarPanel")

        calendar_layout = QVBoxLayout(self.calendar_panel)

        calendar_layout.setContentsMargins(10, 10, 10, 10)
        calendar_layout.setSpacing(8)

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

            label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            label.setFont(
                QFont("Arial", 10, QFont.Weight.Bold)
            )

            weekday_layout.addWidget(
                label,
                0,
                column,
            )

        calendar_layout.addLayout(weekday_layout)

        # Calendar grid.
        self.calendar_grid = QGridLayout()

        self.calendar_grid.setSpacing(5)

        self.calendar_grid.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        calendar_layout.addLayout(self.calendar_grid)

        main_layout.addWidget(self.calendar_panel)

        # -------------------------------------------------
        # SELECTED-DAY EVENT PANEL
        # -------------------------------------------------

        self.event_panel = QWidget(self)
        self.event_panel.setObjectName("eventPanel")

        event_panel_layout = QVBoxLayout(self.event_panel)

        event_panel_layout.setContentsMargins(
            15,
            12,
            15,
            12,
        )

        event_panel_layout.setSpacing(8)

        # Selected-day title.
        self.event_panel_title = QLabel()

        self.event_panel_title.setFont(
            QFont("Arial", 12, QFont.Weight.Bold)
        )

        event_panel_layout.addWidget(
            self.event_panel_title
        )

        # Event count.
        self.event_count_label = QLabel()

        event_panel_layout.addWidget(
            self.event_count_label
        )

        # Event list.
        self.event_list = QListWidget()

        self.event_list.setMinimumHeight(120)
        self.event_list.setMaximumHeight(220)

        self.event_list.setSelectionMode(
            QListWidget.SelectionMode.NoSelection
        )

        self.event_list.setWordWrap(True)

        event_panel_layout.addWidget(
            self.event_list
        )

        main_layout.addWidget(self.event_panel)

        # -------------------------------------------------
        # BOTTOM PANEL
        # -------------------------------------------------

        self.bottom_panel = QWidget(self)
        self.bottom_panel.setObjectName("bottomPanel")

        bottom_layout = QHBoxLayout(self.bottom_panel)

        bottom_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        bottom_layout.addStretch()

        self.add_event_button = QPushButton("Add Event")

        self.add_event_button.setObjectName(
            "addEventButton"
        )

        self.add_event_button.setMinimumSize(
            160,
            45,
        )

        self.add_event_button.clicked.connect(
            self.add_event
        )

        bottom_layout.addWidget(
            self.add_event_button
        )

        bottom_layout.addStretch()

        main_layout.addWidget(self.bottom_panel)

    # =====================================================
    # Light / Dark Theme
    # =====================================================

    def toggle_theme(self):
        """Toggle between light mode and dark mode."""

        self.dark_mode = not self.dark_mode

        if self.dark_mode:
            self.theme_button.setText("☀ Light Mode")
        else:
            self.theme_button.setText("☾ Dark Mode")

        self.apply_stylesheet()

        # Reapply calendar button styling.
        for button in self.day_buttons.values():

            button.style().unpolish(button)
            button.style().polish(button)

    def apply_stylesheet(self):
        """
        Apply the supplied light stylesheet or its dark-mode
        equivalent.

        Dropdown popup text is explicitly styled to remain
        readable in both themes.
        """

        if not self.dark_mode:

            # -------------------------------------------------
            # LIGHT MODE
            # -------------------------------------------------

            self.setStyleSheet(
                """
                QMainWindow {
                    background-color: #f4f6f8;
                }

                QWidget#topPanel,
                QWidget#calendarPanel,
                QWidget#bottomPanel,
                QWidget#eventPanel {
                    background-color: #ffffff;
                    border-radius: 10px;
                }

                /* Generic text */

                QLabel,
                QLineEdit,
                QTextEdit,
                QDateEdit,
                QTimeEdit,
                QComboBox {
                    color: #263238;
                }

                /* Dropdown popup */

                QComboBox QAbstractItemView,
                QComboBox QAbstractItemView::item {
                    background-color: white;
                    color: #263238;
                }

                QComboBox QAbstractItemView::item:selected {
                    background-color: #2878d0;
                    color: white;
                }

                /* Push buttons */

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

                /* Calendar day cells */

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

                /* Add Event button */

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

                /* Event list */

                QListWidget {
                    background-color: #f8fafc;
                    color: #263238;
                    border: 1px solid #e0e5eb;
                    border-radius: 6px;
                    padding: 5px;
                }

                QListWidget::item {
                    background-color: #ffffff;
                    color: #263238;
                    padding: 8px;
                    border-bottom: 1px solid #e0e5eb;
                }

                /* Dialog */

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

        else:

            # -------------------------------------------------
            # DARK MODE
            # -------------------------------------------------

            self.setStyleSheet(
                """
                QMainWindow {
                    background-color: #171a21;
                }

                QWidget#topPanel,
                QWidget#calendarPanel,
                QWidget#bottomPanel,
                QWidget#eventPanel {
                    background-color: #232833;
                    border-radius: 10px;
                }

                /* Generic text */

                QLabel,
                QLineEdit,
                QTextEdit,
                QDateEdit,
                QTimeEdit,
                QComboBox {
                    color: #e6edf3;
                }

                /* Dropdown popup */

                QComboBox QAbstractItemView,
                QComboBox QAbstractItemView::item {
                    background-color: #2b3240;
                    color: #e6edf3;
                }

                QComboBox QAbstractItemView::item:selected {
                    background-color: #2878d0;
                    color: white;
                }

                /* Push buttons */

                QPushButton {
                    background-color: #343d4c;
                    color: #e6edf3;
                    border: 1px solid #465164;
                    border-radius: 6px;
                    padding: 6px;
                    font-size: 11pt;
                }

                QPushButton:hover {
                    background-color: #414d60;
                }

                QPushButton:pressed {
                    background-color: #28313f;
                }

                /* Calendar day cells */

                QPushButton#dayButton {
                    background-color: #2b3240;
                    border: 1px solid #414b5d;
                    border-radius: 6px;
                    color: #e6edf3;
                    font-size: 11pt;
                }

                QPushButton#dayButton:hover {
                    background-color: #39465a;
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
                    background-color: #20252d;
                    color: #626b78;
                    border: 1px solid #303742;
                }

                /* Add Event button */

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

                /* Event list */

                QListWidget {
                    background-color: #1c222c;
                    color: #e6edf3;
                    border: 1px solid #414b5d;
                    border-radius: 6px;
                    padding: 5px;
                }

                QListWidget::item {
                    background-color: #2b3240;
                    color: #e6edf3;
                    padding: 8px;
                    border-bottom: 1px solid #414b5d;
                }

                /* Dialog */

                QDialog {
                    background-color: #232833;
                }

                QLineEdit,
                QTextEdit,
                QDateEdit,
                QTimeEdit,
                QComboBox {
                    background-color: #2b3240;
                    color: #e6edf3;
                    border: 1px solid #465164;
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

    # =====================================================
    # Month Navigation
    # =====================================================

    def previous_month(self):
        """Navigate to the previous month."""

        self.current_date = self.current_date.addMonths(-1)

        self.update_calendar()

    def next_month(self):
        """Navigate to the next month."""

        self.current_date = self.current_date.addMonths(1)

        self.update_calendar()

    # =====================================================
    # Calendar Rendering
    # =====================================================

    def update_calendar(self):
        """
        Rebuild the calendar grid.

        Uses QDate to correctly handle month lengths,
        leap years, and month navigation.
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

        year = self.current_date.year()
        month = self.current_date.month()

        first_day = QDate(year, month, 1)

        days_in_month = first_day.daysInMonth()

        # Qt:
        # Monday = 1
        # Sunday = 7
        #
        # Convert to:
        # Sunday = 0
        # Monday = 1
        # ...
        # Saturday = 6

        first_weekday = first_day.dayOfWeek() % 7

        # -------------------------------------------------
        # Create day buttons
        # -------------------------------------------------

        for day in range(1, days_in_month + 1):

            current_day = QDate(
                year,
                month,
                day,
            )

            button = QPushButton(str(day))

            button.setObjectName("dayButton")

            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            button.setMinimumSize(
                65,
                55,
            )

            button.setProperty(
                "today",
                current_day == QDate.currentDate(),
            )

            button.setProperty(
                "selected",
                current_day == self.selected_date,
            )

            day_events = self.get_events_for_date(
                current_day
            )

            button.setProperty(
                "hasEvents",
                bool(day_events),
            )

            # Show an event marker.
            if day_events:

                button.setText(
                    f"{day} •"
                )

                titles = "\n".join(
                    event["title"]
                    for event in day_events
                )

                button.setToolTip(
                    f"Events:\n{titles}"
                )

            else:

                button.setToolTip(
                    current_day.toString(
                        "dddd, MMMM d, yyyy"
                    )
                )

            # Connect the day button.
            button.clicked.connect(
                lambda checked=False, d=current_day:
                self.select_day(d)
            )

            # Sunday-first calendar position.
            position = first_weekday + day - 1

            row = position // 7
            column = position % 7

            self.calendar_grid.addWidget(
                button,
                row,
                column,
            )

            self.day_buttons[current_day] = button

            # Apply dynamic stylesheet properties.
            button.style().unpolish(button)
            button.style().polish(button)

        # Allow the calendar to expand.
        for row in range(6):

            self.calendar_grid.setRowStretch(
                row,
                1,
            )

        for column in range(7):

            self.calendar_grid.setColumnStretch(
                column,
                1,
            )

        self.calendar_grid.invalidate()
        self.calendar_grid.activate()

        # Update the selected-day event panel.
        self.update_event_panel()

    # =====================================================
    # Day Selection
    # =====================================================

    def select_day(self, selected_date):
        """Select a day and update the calendar and event list."""

        self.selected_date = selected_date

        # If the selected date belongs to another month,
        # navigate to that month.
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

        else:

            # Update selected button.
            for date_value, button in self.day_buttons.items():

                button.setProperty(
                    "selected",
                    date_value == selected_date,
                )

                button.style().unpolish(button)
                button.style().polish(button)

            self.update_event_panel()

    # =====================================================
    # Selected-Day Event Panel
    # =====================================================

    def update_event_panel(self):
        """
        Display all events occurring on the selected date.

        This includes recurring events.
        """

        self.event_list.clear()

        selected_date_text = self.selected_date.toString(
            "dddd, MMMM d, yyyy"
        )

        self.event_panel_title.setText(
            f"Events for {selected_date_text}"
        )

        day_events = self.get_events_for_date(
            self.selected_date
        )

        event_count = len(day_events)

        if event_count == 0:

            self.event_count_label.setText(
                "No events scheduled."
            )

            item = QListWidgetItem(
                "No events for this day."
            )

            item.setFlags(
                Qt.ItemFlag.NoItemFlags
            )

            self.event_list.addItem(item)

            return

        self.event_count_label.setText(
            f"{event_count} event"
            + ("s" if event_count != 1 else "")
        )

        # Sort by time.
        day_events.sort(
            key=lambda event: event.get("time", "09:00")
        )

        for event in day_events:

            title = event.get(
                "title",
                "Untitled",
            )

            time_text = event.get(
                "time",
                "09:00",
            )

            repeat = event.get(
                "repeat",
                "None",
            )

            description = event.get(
                "description",
                "",
            )

            # Event list entry.
            item_text = (
                f"{time_text}  |  {title}"
            )

            if repeat != "None":

                item_text += (
                    f"\nRepeat: {repeat}"
                )

            if description.strip():

                item_text += (
                    f"\n{description.strip()}"
                )

            item = QListWidgetItem(
                item_text
            )

            item.setToolTip(
                f"{title}\n"
                f"Time: {time_text}\n"
                f"Repeat: {repeat}\n"
                f"Description: {description}"
            )

            self.event_list.addItem(item)

    # =====================================================
    # Add Event
    # =====================================================

    def add_event(self):
        """Open the event dialog and save a new event."""

        dialog = EventDialog(
            self.selected_date,
            self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        event_data = dialog.get_event_data()

        event_data["id"] = self.get_next_event_id()

        # Add event to memory.
        self.events.append(event_data)

        # Save immediately.
        if not self.save_events():

            # Roll back the event if saving failed.
            self.events.pop()

            return

        # Select the event's date.
        event_date = QDate.fromString(
            event_data["date"],
            "yyyy-MM-dd",
        )

        self.selected_date = event_date

        # Navigate to the event's month.
        self.current_date = QDate(
            event_date.year(),
            event_date.month(),
            1,
        )

        # Rebuild calendar and event panel.
        self.update_calendar()

    # =====================================================
    # Event ID Generation
    # =====================================================

    def get_next_event_id(self):
        """
        Generate a unique event section name.

        Example:
            event_1
            event_2
            event_3
        """

        existing_ids = []

        for event in self.events:

            event_id = event.get(
                "id",
                "",
            )

            if event_id.startswith("event_"):

                try:

                    number = int(
                        event_id.split("_", 1)[1]
                    )

                    existing_ids.append(number)

                except ValueError:
                    pass

        next_number = max(
            existing_ids,
            default=0,
        ) + 1

        return f"event_{next_number}"

    # =====================================================
    # Load Events
    # =====================================================

    def load_events(self):
        """
        Load events from config.ini.

        Each event is stored in its own section.
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

                # Validate date.
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

                # Validate recurrence.
                if event["repeat"] not in REPEAT_OPTIONS:

                    event["repeat"] = "None"

                self.events.append(event)

        except (
            OSError,
            configparser.Error,
        ) as error:

            QMessageBox.warning(
                self,
                "Load Error",
                f"Could not load events:\n{error}",
            )

    # =====================================================
    # Save Events
    # =====================================================

    def save_events(self):
        """
        Save every event to config.ini.

        Uses a temporary file and os.replace() to avoid
        leaving a partially written configuration file.
        """

        config = configparser.ConfigParser()

        for event in self.events:

            section = event.get(
                "id",
                "",
            )

            if not section:
                continue

            config[section] = {
                "date": event["date"],
                "time": event["time"],
                "repeat": event["repeat"],
                "title": event["title"],
                "description": event["description"],
            }

        temporary_file = CONFIG_FILE + ".tmp"

        try:

            with open(
                temporary_file,
                "w",
                encoding="utf-8",
            ) as file:

                config.write(file)

            # Replace the existing configuration file.
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

            # Remove temporary file if possible.
            try:

                if os.path.exists(temporary_file):

                    os.remove(temporary_file)

            except OSError:
                pass

            return False

    # =====================================================
    # Event Lookup and Recurrence
    # =====================================================

    def get_events_for_date(self, target_date):
        """
        Return all events occurring on target_date.

        Recurrence:
            None
            Every day
            Every week
            Every other week
            Every month
            Every year          # <-- newly supported

        Recurring events continue indefinitely.

        Monthly events occur on the same day number.
        For example, a January 31 event does not occur
        in February because February has no day 31.
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

            # No recurrence.
            if repeat == "None":
                occurs = (target_date == original_date)

            # Daily recurrence.
            elif repeat == "Every day":
                occurs = (target_date >= original_date)

            # Weekly recurrence.
            elif repeat == "Every week":
                occurs = (
                    target_date >= original_date
                    and original_date.daysTo(target_date) % 7 == 0
                )

            # Every two weeks.
            elif repeat == "Every other week":
                occurs = (
                    target_date >= original_date
                    and original_date.daysTo(target_date) % 14 == 0
                )

            # Monthly recurrence.
            elif repeat == "Every month":
                occurs = self.is_monthly_occurrence(original_date, target_date)

            # Yearly recurrence.
            elif repeat == "Every year":
                occurs = self.is_yearly_occurrence(original_date, target_date)

            else:
                occurs = (target_date == original_date)

            if occurs:
                matching_events.append(event)

        return matching_events

    @staticmethod
    def is_monthly_occurrence(original_date, target_date):
        """Determine whether target_date is a monthly occurrence of original_date."""
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

    @staticmethod
    def is_yearly_occurrence(original_date, target_date):
        """Determine whether target_date is a yearly occurrence of original_date."""
        # The event cannot occur before it is created.
        if target_date < original_date:
            return False

        # Must be the same month and day (e.g., Jan 15 each year).
        if (
            target_date.month() != original_date.month()
            or target_date.day() != original_date.day()
        ):
            return False

        # Any later year is a valid occurrence.
        return target_date.year() >= original_date.year()


    # =====================================================
    # Close Event
    # =====================================================

    def closeEvent(self, event):
        """
        Save events before closing.

        Events are already saved immediately after creation,
        but this provides an additional persistence check.
        """

        if self.save_events():

            event.accept()

        else:

            event.ignore()


# =========================================================
# Application Entry Point
# =========================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName(
        "PyQt6 Calendar"
    )

    window = CalendarApp()

    window.show()

    sys.exit(
        app.exec()
    )
