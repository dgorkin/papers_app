"""Dark and light theme stylesheets for the application."""

DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item:selected {
    background-color: #313244;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
}
QMenu::item:selected {
    background-color: #313244;
}
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    spacing: 4px;
    padding: 4px;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #585b70;
}
QPushButton#primary {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #74c7ec;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
    border: 1px solid #89b4fa;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}
QComboBox:hover {
    border: 1px solid #89b4fa;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QTableView {
    background-color: #1e1e2e;
    alternate-background-color: #181825;
    color: #cdd6f4;
    gridline-color: #313244;
    border: 1px solid #313244;
    border-radius: 6px;
    selection-background-color: #313244;
    selection-color: #cdd6f4;
}
QTableView::item {
    padding: 6px;
}
QTableView::item:selected {
    background-color: #313244;
}
QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    border: none;
    border-right: 1px solid #313244;
    border-bottom: 1px solid #313244;
    padding: 8px 6px;
    font-weight: bold;
}
QHeaderView::section:hover {
    background-color: #313244;
}
QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #1e1e2e;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
    width: 0px;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    border: 1px solid #313244;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-bottom-color: #1e1e2e;
}
QLabel#sectionHeader {
    font-size: 15px;
    font-weight: bold;
    color: #89b4fa;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
}
QSplitter::handle {
    background-color: #313244;
}
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px;
}
"""

LIGHT_THEME = """
QMainWindow, QDialog {
    background-color: #eff1f5;
    color: #4c4f69;
}
QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QMenuBar {
    background-color: #e6e9ef;
    color: #4c4f69;
    border-bottom: 1px solid #ccd0da;
}
QMenuBar::item:selected {
    background-color: #ccd0da;
}
QMenu {
    background-color: #eff1f5;
    color: #4c4f69;
    border: 1px solid #ccd0da;
}
QMenu::item:selected {
    background-color: #ccd0da;
}
QToolBar {
    background-color: #e6e9ef;
    border-bottom: 1px solid #ccd0da;
    spacing: 4px;
    padding: 4px;
}
QPushButton {
    background-color: #ccd0da;
    color: #4c4f69;
    border: 1px solid #bcc0cc;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 20px;
}
QPushButton:hover {
    background-color: #bcc0cc;
}
QPushButton:pressed {
    background-color: #acb0be;
}
QPushButton:disabled {
    background-color: #e6e9ef;
    color: #acb0be;
}
QPushButton#primary {
    background-color: #1e66f5;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#primary:hover {
    background-color: #2a7aed;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #1e66f5;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
    border: 1px solid #1e66f5;
}
QComboBox {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}
QComboBox:hover {
    border: 1px solid #1e66f5;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #4c4f69;
    selection-background-color: #ccd0da;
    border: 1px solid #ccd0da;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QTableView {
    background-color: #ffffff;
    alternate-background-color: #e6e9ef;
    color: #4c4f69;
    gridline-color: #ccd0da;
    border: 1px solid #ccd0da;
    border-radius: 6px;
    selection-background-color: #ccd0da;
    selection-color: #4c4f69;
}
QTableView::item {
    padding: 6px;
}
QTableView::item:selected {
    background-color: #ccd0da;
}
QHeaderView::section {
    background-color: #e6e9ef;
    color: #5c5f77;
    border: none;
    border-right: 1px solid #ccd0da;
    border-bottom: 1px solid #ccd0da;
    padding: 8px 6px;
    font-weight: bold;
}
QHeaderView::section:hover {
    background-color: #ccd0da;
}
QScrollBar:vertical {
    background-color: #eff1f5;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #bcc0cc;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #acb0be;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #eff1f5;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #bcc0cc;
    border-radius: 5px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #acb0be;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
    width: 0px;
}
QGroupBox {
    border: 1px solid #ccd0da;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QTabWidget::pane {
    border: 1px solid #ccd0da;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #e6e9ef;
    color: #5c5f77;
    border: 1px solid #ccd0da;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: #eff1f5;
    color: #4c4f69;
    border-bottom-color: #eff1f5;
}
QLabel#sectionHeader {
    font-size: 15px;
    font-weight: bold;
    color: #1e66f5;
}
QStatusBar {
    background-color: #e6e9ef;
    color: #5c5f77;
    border-top: 1px solid #ccd0da;
}
QSplitter::handle {
    background-color: #ccd0da;
}
QToolTip {
    background-color: #ffffff;
    color: #4c4f69;
    border: 1px solid #ccd0da;
    border-radius: 4px;
    padding: 4px;
}
"""


def get_theme(name: str) -> str:
    """Return the stylesheet for the given theme name."""
    if name == "light":
        return LIGHT_THEME
    return DARK_THEME
