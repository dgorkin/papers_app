"""Application dialogs for tag management, status management, PMID input, etc."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..models.paper_repository import StatusRepository, TagRepository


class TagManagerDialog(QDialog):
    """Dialog for managing tags (create, rename, recolor, delete)."""

    def __init__(self, tag_repo: TagRepository, parent=None):
        super().__init__(parent)
        self.tag_repo = tag_repo
        self.setWindowTitle("Manage Tags")
        self.setMinimumSize(400, 500)
        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tag_list = QListWidget()
        layout.addWidget(self.tag_list)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Tag")
        self.add_btn.clicked.connect(self._add_tag)
        btn_row.addWidget(self.add_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename_tag)
        btn_row.addWidget(self.rename_btn)

        self.color_btn = QPushButton("Change Color")
        self.color_btn.clicked.connect(self._change_color)
        btn_row.addWidget(self.color_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_tag)
        btn_row.addWidget(self.delete_btn)

        layout.addLayout(btn_row)

        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(self.accept)
        layout.addWidget(close_btn)

    def _refresh(self):
        self.tag_list.clear()
        for tag in self.tag_repo.get_all():
            item = QListWidgetItem(tag.name)
            item.setData(Qt.ItemDataRole.UserRole, tag.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, tag.color)
            item.setForeground(QColor(tag.color))
            self.tag_list.addItem(item)

    def _add_tag(self):
        name, ok = QInputDialog.getText(self, "New Tag", "Tag name:")
        if ok and name.strip():
            color = QColorDialog.getColor(QColor("#4a86c8"), self, "Tag Color")
            if color.isValid():
                try:
                    self.tag_repo.add(name.strip(), color.name())
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
                self._refresh()

    def _rename_tag(self):
        item = self.tag_list.currentItem()
        if not item:
            return
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Tag", "New name:", text=old_name)
        if ok and new_name.strip():
            color = item.data(Qt.ItemDataRole.UserRole + 1)
            try:
                self.tag_repo.update(tag_id, new_name.strip(), color)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
            self._refresh()

    def _change_color(self):
        item = self.tag_list.currentItem()
        if not item:
            return
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        old_color = item.data(Qt.ItemDataRole.UserRole + 1)
        color = QColorDialog.getColor(QColor(old_color), self, "Tag Color")
        if color.isValid():
            self.tag_repo.update(tag_id, item.text(), color.name())
            self._refresh()

    def _delete_tag(self):
        item = self.tag_list.currentItem()
        if not item:
            return
        reply = QMessageBox.question(
            self, "Delete Tag",
            f"Delete tag '{item.text()}'? This will remove it from all papers.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tag_repo.delete(item.data(Qt.ItemDataRole.UserRole))
            self._refresh()


class StatusManagerDialog(QDialog):
    """Dialog for managing statuses (create, rename, recolor, delete)."""

    def __init__(self, status_repo: StatusRepository, parent=None):
        super().__init__(parent)
        self.status_repo = status_repo
        self.setWindowTitle("Manage Statuses")
        self.setMinimumSize(400, 400)
        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.status_list = QListWidget()
        layout.addWidget(self.status_list)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Status")
        self.add_btn.clicked.connect(self._add_status)
        btn_row.addWidget(self.add_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename_status)
        btn_row.addWidget(self.rename_btn)

        self.color_btn = QPushButton("Change Color")
        self.color_btn.clicked.connect(self._change_color)
        btn_row.addWidget(self.color_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_status)
        btn_row.addWidget(self.delete_btn)

        layout.addLayout(btn_row)

        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(self.accept)
        layout.addWidget(close_btn)

    def _refresh(self):
        self.status_list.clear()
        for status in self.status_repo.get_all():
            item = QListWidgetItem(status.name)
            item.setData(Qt.ItemDataRole.UserRole, status.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, status.color)
            item.setForeground(QColor(status.color))
            self.status_list.addItem(item)

    def _add_status(self):
        name, ok = QInputDialog.getText(self, "New Status", "Status name:")
        if ok and name.strip():
            color = QColorDialog.getColor(QColor("#888888"), self, "Status Color")
            if color.isValid():
                try:
                    self.status_repo.add(name.strip(), color.name())
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
                self._refresh()

    def _rename_status(self):
        item = self.status_list.currentItem()
        if not item:
            return
        status_id = item.data(Qt.ItemDataRole.UserRole)
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Status", "New name:", text=old_name)
        if ok and new_name.strip():
            color = item.data(Qt.ItemDataRole.UserRole + 1)
            try:
                self.status_repo.update(status_id, new_name.strip(), color)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
            self._refresh()

    def _change_color(self):
        item = self.status_list.currentItem()
        if not item:
            return
        status_id = item.data(Qt.ItemDataRole.UserRole)
        old_color = item.data(Qt.ItemDataRole.UserRole + 1)
        color = QColorDialog.getColor(QColor(old_color), self, "Status Color")
        if color.isValid():
            self.status_repo.update(status_id, item.text(), color.name())
            self._refresh()

    def _delete_status(self):
        item = self.status_list.currentItem()
        if not item:
            return
        reply = QMessageBox.question(
            self, "Delete Status",
            f"Delete status '{item.text()}'? Papers with this status will have it cleared.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.status_repo.delete(item.data(Qt.ItemDataRole.UserRole))
            self._refresh()


class AddByPmidDialog(QDialog):
    """Dialog for adding a paper by PMID."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Paper by PMID")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.pmid_edit = QLineEdit()
        self.pmid_edit.setPlaceholderText("Enter PubMed ID (e.g. 12345678)")
        form.addRow("PMID:", self.pmid_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_pmid(self) -> str:
        return self.pmid_edit.text().strip()


class AddByDoiDialog(QDialog):
    """Dialog for adding a paper by DOI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Paper by DOI")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.doi_edit = QLineEdit()
        self.doi_edit.setPlaceholderText("Enter DOI (e.g. 10.1234/example)")
        form.addRow("DOI:", self.doi_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_doi(self) -> str:
        return self.doi_edit.text().strip()


class SettingsDialog(QDialog):
    """Application settings dialog."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.config.get("api_port", 52525))
        form.addRow("API Port:", self.port_spin)

        layout.addLayout(form)

        note = QLabel(
            "Note: Changes to the API port require restarting the application."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        self.config.set("api_port", self.port_spin.value())
        self.accept()
