"""Paper detail/edit panel shown when a paper is double-clicked."""

import os
import subprocess
import sys
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models.paper_repository import Paper, PaperRepository, Status, Tag, TagRepository


class DetailPanel(QWidget):
    """Side panel for viewing and editing paper details."""

    paper_updated = pyqtSignal(int)  # paper_id
    closed = pyqtSignal()

    def __init__(self, repo: PaperRepository, tag_repo: TagRepository,
                 statuses: list[Status], parent=None):
        super().__init__(parent)
        self.repo = repo
        self.tag_repo = tag_repo
        self.statuses = statuses
        self.current_paper: Optional[Paper] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header_row = QHBoxLayout()
        self.title_label = QLabel("Paper Details")
        self.title_label.setObjectName("sectionHeader")
        header_row.addWidget(self.title_label)
        header_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._on_close)
        header_row.addWidget(close_btn)
        layout.addLayout(header_row)

        # Form
        form = QFormLayout()
        form.setSpacing(8)

        self.title_edit = QLineEdit()
        form.addRow("Title:", self.title_edit)

        self.authors_edit = QLineEdit()
        form.addRow("Authors:", self.authors_edit)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(0, 2100)
        self.year_spin.setSpecialValueText("")
        form.addRow("Year:", self.year_spin)

        self.journal_edit = QLineEdit()
        form.addRow("Journal:", self.journal_edit)

        self.doi_edit = QLineEdit()
        self.doi_edit.setPlaceholderText("e.g. 10.1234/example")
        form.addRow("DOI:", self.doi_edit)

        self.pmid_edit = QLineEdit()
        self.pmid_edit.setPlaceholderText("e.g. 12345678")
        form.addRow("PMID:", self.pmid_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItem("(None)", None)
        for s in self.statuses:
            self.status_combo.addItem(s.name, s.id)
        form.addRow("Status:", self.status_combo)

        self.priority_combo = QComboBox()
        for p in ["None", "Low", "Medium", "High"]:
            self.priority_combo.addItem(p)
        form.addRow("Priority:", self.priority_combo)

        self.abstract_edit = QTextEdit()
        self.abstract_edit.setMaximumHeight(120)
        form.addRow("Abstract:", self.abstract_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form.addRow("Notes:", self.notes_edit)

        # Tags
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(100)
        form.addRow("Tags:", self.tags_list)

        # PDF path
        pdf_row = QHBoxLayout()
        self.pdf_label = QLabel("No PDF")
        self.pdf_label.setWordWrap(True)
        pdf_row.addWidget(self.pdf_label, 1)
        self.open_pdf_btn = QPushButton("Open PDF")
        self.open_pdf_btn.clicked.connect(self._open_pdf)
        self.open_pdf_btn.setEnabled(False)
        pdf_row.addWidget(self.open_pdf_btn)
        form.addRow("PDF:", pdf_row)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setObjectName("primary")
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def load_paper(self, paper: Paper, all_tags: list[Tag]):
        """Populate the form with paper data."""
        self.current_paper = paper
        self.title_edit.setText(paper.title)
        self.authors_edit.setText(paper.authors)
        self.year_spin.setValue(paper.year or 0)
        self.journal_edit.setText(paper.journal)
        self.doi_edit.setText(paper.doi or "")
        self.pmid_edit.setText(paper.pmid or "")
        self.abstract_edit.setPlainText(paper.abstract)
        self.notes_edit.setPlainText(paper.notes)

        # Status
        idx = 0
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == paper.status_id:
                idx = i
                break
        self.status_combo.setCurrentIndex(idx)

        # Priority
        pidx = self.priority_combo.findText(paper.priority)
        if pidx >= 0:
            self.priority_combo.setCurrentIndex(pidx)

        # Tags checkboxes
        paper_tag_ids = {t.id for t in paper.tags}
        self.tags_list.clear()
        for tag in all_tags:
            item = QListWidgetItem(tag.name)
            item.setData(Qt.ItemDataRole.UserRole, tag.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if tag.id in paper_tag_ids
                else Qt.CheckState.Unchecked
            )
            self.tags_list.addItem(item)

        # PDF
        if paper.pdf_path and os.path.isfile(paper.pdf_path):
            self.pdf_label.setText(os.path.basename(paper.pdf_path))
            self.open_pdf_btn.setEnabled(True)
        else:
            self.pdf_label.setText("No PDF" if not paper.pdf_path else f"(missing) {paper.pdf_path}")
            self.open_pdf_btn.setEnabled(bool(paper.pdf_path and os.path.isfile(paper.pdf_path)))

    def refresh_statuses(self, statuses: list[Status]):
        """Update the status combo box."""
        self.statuses = statuses
        current = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("(None)", None)
        for s in statuses:
            self.status_combo.addItem(s.name, s.id)
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == current:
                self.status_combo.setCurrentIndex(i)
                break

    def _save(self):
        if not self.current_paper:
            return

        self.current_paper.title = self.title_edit.text()
        self.current_paper.authors = self.authors_edit.text()
        self.current_paper.year = self.year_spin.value() or None
        self.current_paper.journal = self.journal_edit.text()
        self.current_paper.doi = self.doi_edit.text() or None
        self.current_paper.pmid = self.pmid_edit.text() or None
        self.current_paper.abstract = self.abstract_edit.toPlainText()
        self.current_paper.notes = self.notes_edit.toPlainText()
        self.current_paper.status_id = self.status_combo.currentData()
        self.current_paper.priority = self.priority_combo.currentText()

        self.repo.update_paper(self.current_paper)

        # Save tags
        selected_tag_ids = []
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_tag_ids.append(item.data(Qt.ItemDataRole.UserRole))
        self.repo.set_paper_tags(self.current_paper.id, selected_tag_ids)

        self.paper_updated.emit(self.current_paper.id)

    def _open_pdf(self):
        if not self.current_paper or not self.current_paper.pdf_path:
            return
        path = self.current_paper.pdf_path
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _on_close(self):
        self.closed.emit()
