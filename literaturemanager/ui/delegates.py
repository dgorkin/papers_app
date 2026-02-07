"""Custom delegates for rendering cells in the papers table."""

from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from .paper_table_model import PRIORITY_COLORS


class BadgeDelegate(QStyledItemDelegate):
    """Renders text as a colored badge/chip."""

    def __init__(self, color_map: dict[str, str] | None = None, parent=None):
        super().__init__(parent)
        self._color_map = color_map or {}

    def set_color_map(self, color_map: dict[str, str]):
        self._color_map = color_map

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw selection background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        color_hex = self._color_map.get(text, "#6c7086")
        bg_color = QColor(color_hex)
        bg_color.setAlpha(50)
        text_color = QColor(color_hex)

        # Calculate badge rect
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(text) + 16
        text_height = fm.height() + 6
        badge_rect = QRect(
            option.rect.x() + 6,
            option.rect.y() + (option.rect.height() - text_height) // 2,
            text_width,
            text_height,
        )

        # Draw badge background
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 4, 4)

        # Draw text
        painter.setPen(QPen(text_color))
        font = painter.font()
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        fm = option.fontMetrics
        w = fm.horizontalAdvance(text) + 28
        h = fm.height() + 16
        return QSize(max(w, 80), max(h, 32))


class TagsDelegate(QStyledItemDelegate):
    """Renders comma-separated tags as colored chips."""

    def __init__(self, tag_colors: dict[str, str] | None = None, parent=None):
        super().__init__(parent)
        self._tag_colors = tag_colors or {}

    def set_tag_colors(self, tag_colors: dict[str, str]):
        self._tag_colors = tag_colors

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        tags = [t.strip() for t in text.split(",") if t.strip()]
        x = option.rect.x() + 4
        y = option.rect.y() + (option.rect.height() - 22) // 2
        fm = painter.fontMetrics()

        for tag in tags:
            color_hex = self._tag_colors.get(tag, "#4a86c8")
            bg = QColor(color_hex)
            bg.setAlpha(50)
            fg = QColor(color_hex)

            w = fm.horizontalAdvance(tag) + 12
            badge = QRect(x, y, w, 22)

            if badge.right() > option.rect.right() - 4:
                # Draw "..." if we run out of space
                painter.setPen(QPen(QColor("#6c7086")))
                painter.drawText(QRect(x, y, 30, 22), Qt.AlignmentFlag.AlignCenter, "...")
                break

            painter.setBrush(bg)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(badge, 3, 3)

            font = painter.font()
            font.setPointSize(font.pointSize() - 1)
            painter.setFont(font)
            painter.setPen(QPen(fg))
            painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, tag)

            x += w + 4

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        return QSize(200, 32)


class PriorityDelegate(BadgeDelegate):
    """Specialized badge delegate for priority column."""

    def __init__(self, parent=None):
        super().__init__(color_map=PRIORITY_COLORS, parent=parent)
