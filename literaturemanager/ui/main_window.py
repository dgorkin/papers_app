"""Main application window."""

import csv
import logging
import os
from functools import partial
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QTableView,
    QHeaderView,
)

from ..models.database import Database
from ..models.paper_repository import (
    Paper,
    PaperRepository,
    StatusRepository,
    Tag,
    TagRepository,
)
from ..services.config import Config
from ..services.import_service import ImportService
from .delegates import BadgeDelegate, PriorityDelegate, TagsDelegate
from .detail_panel import DetailPanel
from .dialogs import (
    AddByDoiDialog,
    AddByPmidDialog,
    SettingsDialog,
    StatusManagerDialog,
    TagManagerDialog,
)
from .paper_table_model import PaperFilterProxyModel, PaperTableModel
from .themes import get_theme

logger = logging.getLogger(__name__)


class ImportWorker(QThread):
    """Background thread for importing papers."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished_import = pyqtSignal(list)  # list of ImportResult

    def __init__(self, import_fn, parent=None):
        super().__init__(parent)
        self._import_fn = import_fn

    def run(self):
        results = self._import_fn()
        if not isinstance(results, list):
            results = [results]
        self.finished_import.emit(results)


class MainWindow(QMainWindow):
    """Main application window with paper table, filters, and detail panel."""

    paper_added_externally = pyqtSignal(dict)

    def __init__(self, db: Database, config: Config, parent=None):
        super().__init__(parent)
        self.db = db
        self.config = config
        self.paper_repo = PaperRepository(db)
        self.tag_repo = TagRepository(db)
        self.status_repo = StatusRepository(db)
        self.import_service = ImportService(self.paper_repo)

        self.setWindowTitle("Literature Manager")
        self.setMinimumSize(900, 600)
        self.resize(
            config.get("window_width", 1200),
            config.get("window_height", 800),
        )

        self.setAcceptDrops(True)
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._apply_theme()
        self._refresh_data()

        # External add signal (from API server)
        self.paper_added_externally.connect(self._handle_external_add)

    # ── UI Setup ──────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter: left (table + filters) | right (detail panel)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Left pane
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(8, 8, 4, 8)

        # Search bar
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search across all fields...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_edit, 1)
        left_layout.addLayout(search_row)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        filter_row.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(120)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.status_filter)

        filter_row.addWidget(QLabel("Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.setMinimumWidth(100)
        self.priority_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.priority_filter)

        filter_row.addWidget(QLabel("Tags:"))
        self.tag_filter = QComboBox()
        self.tag_filter.setMinimumWidth(120)
        self.tag_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.tag_filter)

        self.clear_filter_btn = QPushButton("Clear Filters")
        self.clear_filter_btn.clicked.connect(self._clear_filters)
        filter_row.addWidget(self.clear_filter_btn)

        filter_row.addStretch()

        self.count_label = QLabel()
        filter_row.addWidget(self.count_label)

        left_layout.addLayout(filter_row)

        # Table
        self.table_model = PaperTableModel()
        self.proxy_model = PaperFilterProxyModel()
        self.proxy_model.setSourceModel(self.table_model)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Authors
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Tags
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 180)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 90)

        # Delegates
        self.status_delegate = BadgeDelegate(parent=self.table)
        self.table.setItemDelegateForColumn(6, self.status_delegate)
        self.priority_delegate = PriorityDelegate(parent=self.table)
        self.table.setItemDelegateForColumn(7, self.priority_delegate)
        self.tags_delegate = TagsDelegate(parent=self.table)
        self.table.setItemDelegateForColumn(5, self.tags_delegate)

        left_layout.addWidget(self.table)
        self.splitter.addWidget(left_pane)

        # Right pane: detail panel (hidden by default)
        statuses = self.status_repo.get_all()
        self.detail_panel = DetailPanel(
            self.paper_repo, self.tag_repo, statuses
        )
        self.detail_panel.paper_updated.connect(self._on_paper_updated)
        self.detail_panel.closed.connect(self._hide_detail)
        self.detail_panel.hide()
        self.splitter.addWidget(self.detail_panel)
        self.splitter.setSizes([800, 400])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        add_pdf = QAction("Add PDF(s)...", self)
        add_pdf.setShortcut(QKeySequence("Ctrl+O"))
        add_pdf.triggered.connect(self._add_pdfs)
        file_menu.addAction(add_pdf)

        add_folder = QAction("Add Folder...", self)
        add_folder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        add_folder.triggered.connect(self._add_folder)
        file_menu.addAction(add_folder)

        add_pmid = QAction("Add by PMID...", self)
        add_pmid.setShortcut(QKeySequence("Ctrl+P"))
        add_pmid.triggered.connect(self._add_by_pmid)
        file_menu.addAction(add_pmid)

        add_doi = QAction("Add by DOI...", self)
        add_doi.setShortcut(QKeySequence("Ctrl+D"))
        add_doi.triggered.connect(self._add_by_doi)
        file_menu.addAction(add_doi)

        file_menu.addSeparator()

        export_csv = QAction("Export to CSV...", self)
        export_csv.setShortcut(QKeySequence("Ctrl+E"))
        export_csv.triggered.connect(self._export_csv)
        file_menu.addAction(export_csv)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        delete_action = QAction("Delete Selected", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self._delete_selected)
        edit_menu.addAction(delete_action)

        select_all = QAction("Select All", self)
        select_all.setShortcut(QKeySequence("Ctrl+A"))
        select_all.triggered.connect(self.table.selectAll)
        edit_menu.addAction(select_all)

        # Library menu
        lib_menu = menubar.addMenu("&Library")

        manage_tags = QAction("Manage Tags...", self)
        manage_tags.triggered.connect(self._manage_tags)
        lib_menu.addAction(manage_tags)

        manage_statuses = QAction("Manage Statuses...", self)
        manage_statuses.triggered.connect(self._manage_statuses)
        lib_menu.addAction(manage_statuses)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.theme_action = QAction("Switch to Light Theme", self)
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_pdf_btn = QPushButton("Add PDF(s)")
        add_pdf_btn.clicked.connect(self._add_pdfs)
        toolbar.addWidget(add_pdf_btn)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        toolbar.addWidget(add_folder_btn)

        add_pmid_btn = QPushButton("Add by PMID")
        add_pmid_btn.clicked.connect(self._add_by_pmid)
        toolbar.addWidget(add_pmid_btn)

        add_doi_btn = QPushButton("Add by DOI")
        add_doi_btn.clicked.connect(self._add_by_doi)
        toolbar.addWidget(add_doi_btn)

        toolbar.addSeparator()

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(export_btn)

    # ── Theme ─────────────────────────────────────────────────────

    def _apply_theme(self):
        theme = self.config.get("theme", "dark")
        self.setStyleSheet(get_theme(theme))
        self._update_theme_label()
        self._update_delegates()

    def _toggle_theme(self):
        current = self.config.get("theme", "dark")
        new_theme = "light" if current == "dark" else "dark"
        self.config.set("theme", new_theme)
        self._apply_theme()

    def _update_theme_label(self):
        current = self.config.get("theme", "dark")
        if current == "dark":
            self.theme_action.setText("Switch to Light Theme")
        else:
            self.theme_action.setText("Switch to Dark Theme")

    def _update_delegates(self):
        """Update delegate color maps from database."""
        statuses = self.status_repo.get_all()
        status_colors = {s.name: s.color for s in statuses}
        self.status_delegate.set_color_map(status_colors)

        tags = self.tag_repo.get_all()
        tag_colors = {t.name: t.color for t in tags}
        self.tags_delegate.set_tag_colors(tag_colors)

    # ── Data Loading ──────────────────────────────────────────────

    def _refresh_data(self):
        """Reload all papers from the database and update the UI."""
        papers = self.paper_repo.get_all_papers()
        self.table_model.set_papers(papers)
        self._refresh_filter_combos()
        self._update_delegates()
        self._update_count()

    def _refresh_filter_combos(self):
        """Refresh the filter dropdown contents."""
        # Status filter
        current_status = self.status_filter.currentText()
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("All Statuses")
        for s in self.status_repo.get_all():
            self.status_filter.addItem(s.name)
        idx = self.status_filter.findText(current_status)
        if idx >= 0:
            self.status_filter.setCurrentIndex(idx)
        self.status_filter.blockSignals(False)

        # Priority filter
        current_priority = self.priority_filter.currentText()
        self.priority_filter.blockSignals(True)
        self.priority_filter.clear()
        self.priority_filter.addItem("All Priorities")
        for p in ["High", "Medium", "Low", "None"]:
            self.priority_filter.addItem(p)
        idx = self.priority_filter.findText(current_priority)
        if idx >= 0:
            self.priority_filter.setCurrentIndex(idx)
        self.priority_filter.blockSignals(False)

        # Tag filter
        current_tag = self.tag_filter.currentText()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        for t in self.tag_repo.get_all():
            self.tag_filter.addItem(t.name)
        idx = self.tag_filter.findText(current_tag)
        if idx >= 0:
            self.tag_filter.setCurrentIndex(idx)
        self.tag_filter.blockSignals(False)

    def _update_count(self):
        visible = self.proxy_model.rowCount()
        total = self.table_model.rowCount()
        if visible == total:
            self.count_label.setText(f"{total} papers")
        else:
            self.count_label.setText(f"{visible} / {total} papers")

    # ── Filtering ─────────────────────────────────────────────────

    def _on_search_changed(self, text: str):
        self.proxy_model.set_search_text(text)
        self._update_count()

    def _on_filter_changed(self):
        status = self.status_filter.currentText()
        if status == "All Statuses":
            status = ""
        self.proxy_model.set_status_filter(status)

        priority = self.priority_filter.currentText()
        if priority == "All Priorities":
            priority = ""
        self.proxy_model.set_priority_filter(priority)

        tag = self.tag_filter.currentText()
        if tag == "All Tags":
            self.proxy_model.set_tag_filter(set())
        else:
            self.proxy_model.set_tag_filter({tag})

        self._update_count()

    def _clear_filters(self):
        self.search_edit.clear()
        self.status_filter.setCurrentIndex(0)
        self.priority_filter.setCurrentIndex(0)
        self.tag_filter.setCurrentIndex(0)
        self.proxy_model.clear_filters()
        self._update_count()

    # ── Paper Interaction ─────────────────────────────────────────

    def _on_double_click(self, index):
        source_index = self.proxy_model.mapToSource(index)
        paper = self.table_model.get_paper(source_index.row())
        if paper:
            self._show_detail(paper)

    def _show_detail(self, paper: Paper):
        full = self.paper_repo.get_paper(paper.id)
        if full:
            all_tags = self.tag_repo.get_all()
            self.detail_panel.load_paper(full, all_tags)
            self.detail_panel.refresh_statuses(self.status_repo.get_all())
            self.detail_panel.show()

    def _hide_detail(self):
        self.detail_panel.hide()

    def _on_paper_updated(self, paper_id: int):
        self._refresh_data()
        self.status_bar.showMessage("Paper updated", 3000)

    # ── Context Menu ──────────────────────────────────────────────

    def _get_selected_paper_ids(self) -> list[int]:
        """Get paper IDs of all currently selected rows."""
        ids = []
        for index in self.table.selectionModel().selectedRows():
            source_index = self.proxy_model.mapToSource(index)
            paper = self.table_model.get_paper(source_index.row())
            if paper:
                ids.append(paper.id)
        return ids

    def _show_context_menu(self, pos):
        paper_ids = self._get_selected_paper_ids()
        if not paper_ids:
            return

        menu = QMenu(self)
        count = len(paper_ids)
        label = f"({count} papers)" if count > 1 else ""

        # Status submenu
        status_menu = menu.addMenu(f"Set Status {label}")
        status_menu.addAction("(None)", lambda: self._bulk_set_status(paper_ids, None))
        for s in self.status_repo.get_all():
            status_menu.addAction(
                s.name,
                partial(self._bulk_set_status, paper_ids, s.id),
            )

        # Priority submenu
        priority_menu = menu.addMenu(f"Set Priority {label}")
        for p in ["High", "Medium", "Low", "None"]:
            priority_menu.addAction(
                p, partial(self._bulk_set_priority, paper_ids, p)
            )

        # Tags submenu
        tags_menu = menu.addMenu(f"Add Tag {label}")
        for t in self.tag_repo.get_all():
            tags_menu.addAction(
                t.name,
                partial(self._bulk_add_tag, paper_ids, t.id),
            )

        menu.addSeparator()

        # Open detail
        if count == 1:
            paper = self.paper_repo.get_paper(paper_ids[0])
            if paper:
                menu.addAction("View/Edit Details", lambda: self._show_detail(paper))
                if paper.pdf_path and os.path.isfile(paper.pdf_path):
                    menu.addAction("Open PDF", lambda: self._open_pdf(paper.pdf_path))

        menu.addSeparator()
        menu.addAction("Delete", lambda: self._delete_papers(paper_ids))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _bulk_set_status(self, paper_ids: list[int], status_id: Optional[int]):
        for pid in paper_ids:
            self.paper_repo.update_paper_status(pid, status_id)
        self._refresh_data()
        self.status_bar.showMessage(f"Status updated for {len(paper_ids)} paper(s)", 3000)

    def _bulk_set_priority(self, paper_ids: list[int], priority: str):
        for pid in paper_ids:
            self.paper_repo.update_paper_priority(pid, priority)
        self._refresh_data()
        self.status_bar.showMessage(f"Priority updated for {len(paper_ids)} paper(s)", 3000)

    def _bulk_add_tag(self, paper_ids: list[int], tag_id: int):
        for pid in paper_ids:
            self.paper_repo.add_tag_to_paper(pid, tag_id)
        self._refresh_data()
        self.status_bar.showMessage(f"Tag added to {len(paper_ids)} paper(s)", 3000)

    def _open_pdf(self, path: str):
        import subprocess
        import sys
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    # ── Import Actions ────────────────────────────────────────────

    def _add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if not files:
            return
        self._run_import(lambda: [self.import_service.import_pdf(f) for f in files])

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        self._run_import(lambda: self.import_service.import_folder(folder))

    def _add_by_pmid(self):
        dlg = AddByPmidDialog(self)
        if dlg.exec() == AddByPmidDialog.DialogCode.Accepted:
            pmid = dlg.get_pmid()
            if pmid:
                self._run_import(lambda: self.import_service.import_by_pmid(pmid))

    def _add_by_doi(self):
        dlg = AddByDoiDialog(self)
        if dlg.exec() == AddByDoiDialog.DialogCode.Accepted:
            doi = dlg.get_doi()
            if doi:
                self._run_import(lambda: self.import_service.import_by_doi(doi))

    def _run_import(self, import_fn):
        """Run an import function in a background thread."""
        self.status_bar.showMessage("Importing...")
        self._worker = ImportWorker(import_fn)
        self._worker.finished_import.connect(self._on_import_done)
        self._worker.start()

    def _on_import_done(self, results):
        self._refresh_data()
        successes = sum(1 for r in results if r.success)
        skips = sum(1 for r in results if r.skipped)
        errors = sum(1 for r in results if r.error)

        parts = []
        if successes:
            parts.append(f"{successes} imported")
        if skips:
            parts.append(f"{skips} skipped (duplicates)")
        if errors:
            parts.append(f"{errors} failed")

        msg = "Import complete: " + ", ".join(parts) if parts else "Nothing to import"
        self.status_bar.showMessage(msg, 10000)

        # Show errors in detail if any
        if errors:
            error_msgs = [r.error for r in results if r.error]
            QMessageBox.warning(
                self, "Import Errors",
                "Some papers failed to import:\n\n" + "\n".join(error_msgs[:10]),
            )

    # ── Drag and Drop ─────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        pdf_paths = []
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith(".pdf"):
                pdf_paths.append(path)
            elif os.path.isdir(path):
                for f in os.listdir(path):
                    if f.lower().endswith(".pdf"):
                        pdf_paths.append(os.path.join(path, f))

        if pdf_paths:
            self._run_import(
                lambda: [self.import_service.import_pdf(p) for p in pdf_paths]
            )

    # ── Delete ────────────────────────────────────────────────────

    def _delete_selected(self):
        ids = self._get_selected_paper_ids()
        if ids:
            self._delete_papers(ids)

    def _delete_papers(self, paper_ids: list[int]):
        count = len(paper_ids)
        reply = QMessageBox.question(
            self,
            "Delete Papers",
            f"Delete {count} paper(s) from the library? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.paper_repo.delete_papers(paper_ids)
            self._hide_detail()
            self._refresh_data()
            self.status_bar.showMessage(f"Deleted {count} paper(s)", 3000)

    # ── Export ────────────────────────────────────────────────────

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "papers.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Title", "Authors", "Year", "Journal", "DOI", "PMID",
                    "Tags", "Status", "Priority", "Abstract", "Notes", "PDF Path",
                ])
                # Export visible (filtered) rows
                for row in range(self.proxy_model.rowCount()):
                    source_index = self.proxy_model.mapToSource(
                        self.proxy_model.index(row, 0)
                    )
                    paper = self.table_model.get_paper(source_index.row())
                    writer.writerow([
                        paper.title,
                        paper.authors,
                        paper.year or "",
                        paper.journal,
                        paper.doi or "",
                        paper.pmid or "",
                        "; ".join(t.name for t in paper.tags),
                        paper.status_name,
                        paper.priority,
                        paper.abstract,
                        paper.notes,
                        paper.pdf_path or "",
                    ])
            self.status_bar.showMessage(f"Exported to {path}", 5000)
        except OSError as e:
            QMessageBox.warning(self, "Export Error", str(e))

    # ── Manage Tags / Statuses ────────────────────────────────────

    def _manage_tags(self):
        dlg = TagManagerDialog(self.tag_repo, self)
        dlg.exec()
        self._refresh_data()

    def _manage_statuses(self):
        dlg = StatusManagerDialog(self.status_repo, self)
        dlg.exec()
        self._refresh_data()
        self.detail_panel.refresh_statuses(self.status_repo.get_all())

    # ── Settings ──────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        dlg.exec()

    # ── External API adds ─────────────────────────────────────────

    def _handle_external_add(self, data: dict):
        """Handle a paper add request from the local API server."""
        pmid = data.get("pmid")
        doi = data.get("doi")

        if pmid:
            result = self.import_service.import_by_pmid(pmid)
        elif doi:
            result = self.import_service.import_by_doi(doi)
        else:
            return

        self._refresh_data()
        if result.success:
            self.status_bar.showMessage(
                f"Added via Chrome extension: {result.paper.title[:60]}", 5000
            )
        elif result.skipped:
            self.status_bar.showMessage(f"Already in library: {result.message}", 5000)
        else:
            self.status_bar.showMessage(f"Extension add failed: {result.error}", 5000)

    # ── Window Events ─────────────────────────────────────────────

    def closeEvent(self, event):
        self.config.set("window_width", self.width())
        self.config.set("window_height", self.height())
        event.accept()
