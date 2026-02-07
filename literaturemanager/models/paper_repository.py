"""Repository pattern for paper CRUD operations using JSON store."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .json_store import JsonStore


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


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class PaperRepository:
    """Handles all paper-related operations against the JSON store."""

    def __init__(self, store: JsonStore):
        self.store = store

    def add_paper(self, paper: Paper) -> int:
        """Insert a new paper and return its ID."""
        now = _now()
        paper_id = self.store.next_paper_id()
        record = {
            "id": paper_id,
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "journal": paper.journal,
            "doi": paper.doi,
            "pmid": paper.pmid,
            "abstract": paper.abstract,
            "pdf_path": paper.pdf_path,
            "status_id": paper.status_id,
            "priority": paper.priority,
            "notes": paper.notes,
            "date_added": now,
            "date_modified": now,
            "tag_ids": [],
        }
        self.store.papers.append(record)
        self.store.save()
        return paper_id

    def update_paper(self, paper: Paper):
        """Update an existing paper."""
        for rec in self.store.papers:
            if rec["id"] == paper.id:
                rec["title"] = paper.title
                rec["authors"] = paper.authors
                rec["year"] = paper.year
                rec["journal"] = paper.journal
                rec["doi"] = paper.doi
                rec["pmid"] = paper.pmid
                rec["abstract"] = paper.abstract
                rec["pdf_path"] = paper.pdf_path
                rec["status_id"] = paper.status_id
                rec["priority"] = paper.priority
                rec["notes"] = paper.notes
                rec["date_modified"] = _now()
                break
        self.store.save()

    def delete_paper(self, paper_id: int):
        """Delete a paper by ID."""
        self.store.papers[:] = [
            p for p in self.store.papers if p["id"] != paper_id
        ]
        self.store.save()

    def delete_papers(self, paper_ids: list[int]):
        """Delete multiple papers by ID."""
        id_set = set(paper_ids)
        self.store.papers[:] = [
            p for p in self.store.papers if p["id"] not in id_set
        ]
        self.store.save()

    def get_paper(self, paper_id: int) -> Optional[Paper]:
        """Get a single paper by ID."""
        for rec in self.store.papers:
            if rec["id"] == paper_id:
                paper = self._record_to_paper(rec)
                paper.tags = self.get_paper_tags(paper_id)
                return paper
        return None

    def get_all_papers(self) -> list[Paper]:
        """Get all papers, sorted by date_added descending."""
        sorted_papers = sorted(
            self.store.papers,
            key=lambda p: p.get("date_added", ""),
            reverse=True,
        )
        papers = []
        for rec in sorted_papers:
            paper = self._record_to_paper(rec)
            paper.tags = self.get_paper_tags(paper.id)
            papers.append(paper)
        return papers

    def find_by_doi(self, doi: str) -> Optional[Paper]:
        """Find a paper by DOI."""
        for rec in self.store.papers:
            if rec.get("doi") == doi:
                paper = self._record_to_paper(rec)
                paper.tags = self.get_paper_tags(paper.id)
                return paper
        return None

    def find_by_pmid(self, pmid: str) -> Optional[Paper]:
        """Find a paper by PMID."""
        for rec in self.store.papers:
            if rec.get("pmid") == pmid:
                paper = self._record_to_paper(rec)
                paper.tags = self.get_paper_tags(paper.id)
                return paper
        return None

    def get_paper_tags(self, paper_id: int) -> list[Tag]:
        """Get all tags for a paper."""
        for rec in self.store.papers:
            if rec["id"] == paper_id:
                tag_ids = rec.get("tag_ids", [])
                tags = []
                for t in self.store.tags:
                    if t["id"] in tag_ids:
                        tags.append(Tag(id=t["id"], name=t["name"], color=t["color"]))
                tags.sort(key=lambda t: t.name)
                return tags
        return []

    def set_paper_tags(self, paper_id: int, tag_ids: list[int]):
        """Replace all tags for a paper."""
        for rec in self.store.papers:
            if rec["id"] == paper_id:
                rec["tag_ids"] = list(tag_ids)
                break
        self.store.save()

    def add_tag_to_paper(self, paper_id: int, tag_id: int):
        """Add a single tag to a paper."""
        for rec in self.store.papers:
            if rec["id"] == paper_id:
                tag_ids = rec.setdefault("tag_ids", [])
                if tag_id not in tag_ids:
                    tag_ids.append(tag_id)
                break
        self.store.save()

    def update_paper_status(self, paper_id: int, status_id: Optional[int]):
        """Update a paper's status."""
        for rec in self.store.papers:
            if rec["id"] == paper_id:
                rec["status_id"] = status_id
                rec["date_modified"] = _now()
                break
        self.store.save()

    def update_paper_priority(self, paper_id: int, priority: str):
        """Update a paper's priority."""
        for rec in self.store.papers:
            if rec["id"] == paper_id:
                rec["priority"] = priority
                rec["date_modified"] = _now()
                break
        self.store.save()

    def _record_to_paper(self, rec: dict) -> Paper:
        """Convert a JSON record to a Paper object, resolving status info."""
        status_name = ""
        status_color = ""
        status_id = rec.get("status_id")
        if status_id is not None:
            for s in self.store.statuses:
                if s["id"] == status_id:
                    status_name = s["name"]
                    status_color = s["color"]
                    break
        return Paper(
            id=rec["id"],
            title=rec.get("title", ""),
            authors=rec.get("authors", ""),
            year=rec.get("year"),
            journal=rec.get("journal", ""),
            doi=rec.get("doi"),
            pmid=rec.get("pmid"),
            abstract=rec.get("abstract", ""),
            pdf_path=rec.get("pdf_path"),
            status_id=status_id,
            status_name=status_name,
            status_color=status_color,
            priority=rec.get("priority", "None"),
            notes=rec.get("notes", ""),
            date_added=rec.get("date_added", ""),
            date_modified=rec.get("date_modified", ""),
        )


class TagRepository:
    """Handles tag CRUD operations."""

    def __init__(self, store: JsonStore):
        self.store = store

    def get_all(self) -> list[Tag]:
        return sorted(
            [Tag(id=t["id"], name=t["name"], color=t["color"]) for t in self.store.tags],
            key=lambda t: t.name,
        )

    def add(self, name: str, color: str = "#4a86c8") -> int:
        # Check uniqueness
        for t in self.store.tags:
            if t["name"] == name:
                raise ValueError(f"Tag '{name}' already exists")
        tag_id = self.store.next_tag_id()
        self.store.tags.append({"id": tag_id, "name": name, "color": color})
        self.store.save()
        return tag_id

    def update(self, tag_id: int, name: str, color: str):
        for t in self.store.tags:
            if t["id"] == tag_id:
                t["name"] = name
                t["color"] = color
                break
        self.store.save()

    def delete(self, tag_id: int):
        self.store.tags[:] = [t for t in self.store.tags if t["id"] != tag_id]
        # Also remove from all papers
        for p in self.store.papers:
            tag_ids = p.get("tag_ids", [])
            if tag_id in tag_ids:
                tag_ids.remove(tag_id)
        self.store.save()

    def find_by_name(self, name: str) -> Optional[Tag]:
        for t in self.store.tags:
            if t["name"] == name:
                return Tag(id=t["id"], name=t["name"], color=t["color"])
        return None


class StatusRepository:
    """Handles status CRUD operations."""

    def __init__(self, store: JsonStore):
        self.store = store

    def get_all(self) -> list[Status]:
        return sorted(
            [
                Status(id=s["id"], name=s["name"], color=s["color"],
                       sort_order=s.get("sort_order", 0))
                for s in self.store.statuses
            ],
            key=lambda s: s.sort_order,
        )

    def add(self, name: str, color: str = "#888888") -> int:
        max_order = max((s.get("sort_order", 0) for s in self.store.statuses), default=-1)
        status_id = self.store.next_status_id()
        self.store.statuses.append({
            "id": status_id,
            "name": name,
            "color": color,
            "sort_order": max_order + 1,
        })
        self.store.save()
        return status_id

    def update(self, status_id: int, name: str, color: str):
        for s in self.store.statuses:
            if s["id"] == status_id:
                s["name"] = name
                s["color"] = color
                break
        self.store.save()

    def delete(self, status_id: int):
        self.store.statuses[:] = [
            s for s in self.store.statuses if s["id"] != status_id
        ]
        # Clear status_id on papers referencing this status
        for p in self.store.papers:
            if p.get("status_id") == status_id:
                p["status_id"] = None
        self.store.save()
