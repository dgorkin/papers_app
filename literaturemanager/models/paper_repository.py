"""Repository pattern for paper CRUD operations."""

from dataclasses import dataclass, field
from typing import Optional
from .database import Database


@dataclass
class Paper:
    """Data class representing a paper."""
    id: Optional[int] = None
    title: str = ""
    authors: str = ""
    year: Optional[int] = None
    journal: str = ""
    doi: Optional[str] = None
    pmid: Optional[str] = None
    abstract: str = ""
    pdf_path: Optional[str] = None
    status_id: Optional[int] = None
    status_name: str = ""
    status_color: str = ""
    priority: str = "None"
    notes: str = ""
    date_added: str = ""
    date_modified: str = ""
    tags: list = field(default_factory=list)


@dataclass
class Tag:
    """Data class representing a tag."""
    id: Optional[int] = None
    name: str = ""
    color: str = "#4a86c8"


@dataclass
class Status:
    """Data class representing a status."""
    id: Optional[int] = None
    name: str = ""
    color: str = "#888888"
    sort_order: int = 0


class PaperRepository:
    """Handles all paper-related database operations."""

    def __init__(self, db: Database):
        self.db = db

    def add_paper(self, paper: Paper) -> int:
        """Insert a new paper and return its ID."""
        cursor = self.db.execute(
            """INSERT INTO papers
               (title, authors, year, journal, doi, pmid, abstract,
                pdf_path, status_id, priority, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (paper.title, paper.authors, paper.year, paper.journal,
             paper.doi, paper.pmid, paper.abstract, paper.pdf_path,
             paper.status_id, paper.priority, paper.notes),
        )
        self.db.commit()
        return cursor.lastrowid

    def update_paper(self, paper: Paper):
        """Update an existing paper."""
        self.db.execute(
            """UPDATE papers SET
               title=?, authors=?, year=?, journal=?, doi=?, pmid=?,
               abstract=?, pdf_path=?, status_id=?, priority=?, notes=?,
               date_modified=datetime('now')
               WHERE id=?""",
            (paper.title, paper.authors, paper.year, paper.journal,
             paper.doi, paper.pmid, paper.abstract, paper.pdf_path,
             paper.status_id, paper.priority, paper.notes, paper.id),
        )
        self.db.commit()

    def delete_paper(self, paper_id: int):
        """Delete a paper by ID."""
        self.db.execute("DELETE FROM papers WHERE id=?", (paper_id,))
        self.db.commit()

    def delete_papers(self, paper_ids: list[int]):
        """Delete multiple papers by ID."""
        placeholders = ",".join("?" for _ in paper_ids)
        self.db.execute(
            f"DELETE FROM papers WHERE id IN ({placeholders})", paper_ids
        )
        self.db.commit()

    def get_paper(self, paper_id: int) -> Optional[Paper]:
        """Get a single paper by ID."""
        row = self.db.execute(
            """SELECT p.*, s.name as status_name, s.color as status_color
               FROM papers p
               LEFT JOIN statuses s ON p.status_id = s.id
               WHERE p.id=?""",
            (paper_id,),
        ).fetchone()
        if not row:
            return None
        paper = self._row_to_paper(row)
        paper.tags = self.get_paper_tags(paper_id)
        return paper

    def get_all_papers(self) -> list[Paper]:
        """Get all papers with their status info."""
        rows = self.db.execute(
            """SELECT p.*, s.name as status_name, s.color as status_color
               FROM papers p
               LEFT JOIN statuses s ON p.status_id = s.id
               ORDER BY p.date_added DESC"""
        ).fetchall()
        papers = []
        for row in rows:
            paper = self._row_to_paper(row)
            paper.tags = self.get_paper_tags(paper.id)
            papers.append(paper)
        return papers

    def find_by_doi(self, doi: str) -> Optional[Paper]:
        """Find a paper by DOI."""
        row = self.db.execute(
            """SELECT p.*, s.name as status_name, s.color as status_color
               FROM papers p
               LEFT JOIN statuses s ON p.status_id = s.id
               WHERE p.doi=?""",
            (doi,),
        ).fetchone()
        if not row:
            return None
        paper = self._row_to_paper(row)
        paper.tags = self.get_paper_tags(paper.id)
        return paper

    def find_by_pmid(self, pmid: str) -> Optional[Paper]:
        """Find a paper by PMID."""
        row = self.db.execute(
            """SELECT p.*, s.name as status_name, s.color as status_color
               FROM papers p
               LEFT JOIN statuses s ON p.status_id = s.id
               WHERE p.pmid=?""",
            (pmid,),
        ).fetchone()
        if not row:
            return None
        paper = self._row_to_paper(row)
        paper.tags = self.get_paper_tags(paper.id)
        return paper

    def get_paper_tags(self, paper_id: int) -> list[Tag]:
        """Get all tags for a paper."""
        rows = self.db.execute(
            """SELECT t.id, t.name, t.color FROM tags t
               JOIN paper_tags pt ON t.id = pt.tag_id
               WHERE pt.paper_id=?
               ORDER BY t.name""",
            (paper_id,),
        ).fetchall()
        return [Tag(id=r["id"], name=r["name"], color=r["color"]) for r in rows]

    def set_paper_tags(self, paper_id: int, tag_ids: list[int]):
        """Replace all tags for a paper."""
        self.db.execute("DELETE FROM paper_tags WHERE paper_id=?", (paper_id,))
        for tag_id in tag_ids:
            self.db.execute(
                "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)",
                (paper_id, tag_id),
            )
        self.db.commit()

    def add_tag_to_paper(self, paper_id: int, tag_id: int):
        """Add a single tag to a paper."""
        self.db.execute(
            "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)",
            (paper_id, tag_id),
        )
        self.db.commit()

    def update_paper_status(self, paper_id: int, status_id: Optional[int]):
        """Update a paper's status."""
        self.db.execute(
            "UPDATE papers SET status_id=?, date_modified=datetime('now') WHERE id=?",
            (status_id, paper_id),
        )
        self.db.commit()

    def update_paper_priority(self, paper_id: int, priority: str):
        """Update a paper's priority."""
        self.db.execute(
            "UPDATE papers SET priority=?, date_modified=datetime('now') WHERE id=?",
            (priority, paper_id),
        )
        self.db.commit()

    def _row_to_paper(self, row) -> Paper:
        """Convert a database row to a Paper object."""
        return Paper(
            id=row["id"],
            title=row["title"],
            authors=row["authors"],
            year=row["year"],
            journal=row["journal"],
            doi=row["doi"],
            pmid=row["pmid"],
            abstract=row["abstract"],
            pdf_path=row["pdf_path"],
            status_id=row["status_id"],
            status_name=row["status_name"] or "",
            status_color=row["status_color"] or "",
            priority=row["priority"],
            notes=row["notes"],
            date_added=row["date_added"],
            date_modified=row["date_modified"],
        )


class TagRepository:
    """Handles tag CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def get_all(self) -> list[Tag]:
        rows = self.db.execute(
            "SELECT * FROM tags ORDER BY name"
        ).fetchall()
        return [Tag(id=r["id"], name=r["name"], color=r["color"]) for r in rows]

    def add(self, name: str, color: str = "#4a86c8") -> int:
        cursor = self.db.execute(
            "INSERT INTO tags (name, color) VALUES (?, ?)", (name, color)
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, tag_id: int, name: str, color: str):
        self.db.execute(
            "UPDATE tags SET name=?, color=? WHERE id=?",
            (name, color, tag_id),
        )
        self.db.commit()

    def delete(self, tag_id: int):
        self.db.execute("DELETE FROM tags WHERE id=?", (tag_id,))
        self.db.commit()

    def find_by_name(self, name: str) -> Optional[Tag]:
        row = self.db.execute(
            "SELECT * FROM tags WHERE name=?", (name,)
        ).fetchone()
        if row:
            return Tag(id=row["id"], name=row["name"], color=row["color"])
        return None


class StatusRepository:
    """Handles status CRUD operations."""

    def __init__(self, db: Database):
        self.db = db

    def get_all(self) -> list[Status]:
        rows = self.db.execute(
            "SELECT * FROM statuses ORDER BY sort_order"
        ).fetchall()
        return [
            Status(id=r["id"], name=r["name"], color=r["color"],
                   sort_order=r["sort_order"])
            for r in rows
        ]

    def add(self, name: str, color: str = "#888888") -> int:
        max_order = self.db.execute(
            "SELECT COALESCE(MAX(sort_order), -1) FROM statuses"
        ).fetchone()[0]
        cursor = self.db.execute(
            "INSERT INTO statuses (name, color, sort_order) VALUES (?, ?, ?)",
            (name, color, max_order + 1),
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, status_id: int, name: str, color: str):
        self.db.execute(
            "UPDATE statuses SET name=?, color=? WHERE id=?",
            (name, color, status_id),
        )
        self.db.commit()

    def delete(self, status_id: int):
        self.db.execute("DELETE FROM statuses WHERE id=?", (status_id,))
        self.db.commit()
