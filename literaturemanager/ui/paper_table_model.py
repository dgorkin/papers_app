"""Qt table model for displaying papers in the main view."""

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QColor

from ..models.paper_repository import Paper

COLUMNS = ["Title", "Authors", "Year", "Journal", "PMID", "Tags", "Status", "Priority"]
PRIORITY_COLORS = {
    "High": "#f38ba8",
    "Medium": "#fab387",
    "Low": "#a6e3a1",
    "None": "#6c7086",
}


class PaperTableModel(QAbstractTableModel):
    """Model backing the main papers table view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._papers: list[Paper] = []

    def set_papers(self, papers: list[Paper]):
        """Replace the entire data set."""
        self.beginResetModel()
        self._papers = papers
        self.endResetModel()

    def get_paper(self, row: int) -> Paper:
        return self._papers[row]

    def get_paper_by_id(self, paper_id: int) -> Paper | None:
        for p in self._papers:
            if p.id == paper_id:
                return p
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._papers)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        paper = self._papers[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return paper.title
            elif col == 1:
                return paper.authors
            elif col == 2:
                return str(paper.year) if paper.year else ""
            elif col == 3:
                return paper.journal
            elif col == 4:
                return paper.pmid or ""
            elif col == 5:
                return ", ".join(t.name for t in paper.tags)
            elif col == 6:
                return paper.status_name
            elif col == 7:
                return paper.priority

        elif role == Qt.ItemDataRole.UserRole:
            # Store full paper for sorting/filtering
            if col == 2:
                return paper.year or 0
            elif col == 5:
                return ",".join(t.name for t in paper.tags)
            elif col == 7:
                order = {"High": 0, "Medium": 1, "Low": 2, "None": 3}
                return order.get(paper.priority, 3)
            return self.data(index, Qt.ItemDataRole.DisplayRole)

        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 7:
                color = PRIORITY_COLORS.get(paper.priority, "#6c7086")
                return QColor(color)

        elif role == Qt.ItemDataRole.BackgroundRole:
            if col == 6 and paper.status_color:
                c = QColor(paper.status_color)
                c.setAlpha(40)
                return c

        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == 0:
                return paper.title
            elif col == 1:
                return paper.authors

        # Store the paper ID in a custom role for easy retrieval
        if role == Qt.ItemDataRole.UserRole + 1:
            return paper.id

        return None

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        """Sort by column."""
        self.beginResetModel()
        reverse = order == Qt.SortOrder.DescendingOrder
        key_funcs = {
            0: lambda p: (p.title or "").lower(),
            1: lambda p: (p.authors or "").lower(),
            2: lambda p: p.year or 0,
            3: lambda p: (p.journal or "").lower(),
            4: lambda p: p.pmid or "",
            5: lambda p: ",".join(t.name for t in p.tags).lower(),
            6: lambda p: (p.status_name or "").lower(),
            7: lambda p: {"High": 0, "Medium": 1, "Low": 2, "None": 3}.get(p.priority, 3),
        }
        key = key_funcs.get(column, lambda p: "")
        self._papers.sort(key=key, reverse=reverse)
        self.endResetModel()


class PaperFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering papers by search text, tags, status, and priority."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self._filter_tags: set[str] = set()
        self._filter_status: str = ""
        self._filter_priority: str = ""

    def set_search_text(self, text: str):
        self._search_text = text.lower().strip()
        self.invalidateFilter()

    def set_tag_filter(self, tags: set[str]):
        self._filter_tags = tags
        self.invalidateFilter()

    def set_status_filter(self, status: str):
        self._filter_status = status
        self.invalidateFilter()

    def set_priority_filter(self, priority: str):
        self._filter_priority = priority
        self.invalidateFilter()

    def clear_filters(self):
        self._search_text = ""
        self._filter_tags = set()
        self._filter_status = ""
        self._filter_priority = ""
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        if not isinstance(model, PaperTableModel):
            return True

        paper = model.get_paper(source_row)

        # Text search across all fields
        if self._search_text:
            searchable = " ".join([
                paper.title or "",
                paper.authors or "",
                str(paper.year) if paper.year else "",
                paper.journal or "",
                paper.pmid or "",
                paper.doi or "",
                ",".join(t.name for t in paper.tags),
                paper.status_name or "",
                paper.priority or "",
                paper.abstract or "",
                paper.notes or "",
            ]).lower()
            if self._search_text not in searchable:
                return False

        # Tag filter (paper must have ALL selected tags)
        if self._filter_tags:
            paper_tag_names = {t.name for t in paper.tags}
            if not self._filter_tags.issubset(paper_tag_names):
                return False

        # Status filter
        if self._filter_status and paper.status_name != self._filter_status:
            return False

        # Priority filter
        if self._filter_priority and paper.priority != self._filter_priority:
            return False

        return True
