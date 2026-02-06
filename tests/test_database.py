"""Tests for the database layer."""

import os
import tempfile
import unittest

from literaturemanager.models.database import Database
from literaturemanager.models.paper_repository import (
    Paper,
    PaperRepository,
    StatusRepository,
    TagRepository,
)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.db = Database(self.tmpfile.name)
        self.db.connect()

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmpfile.name)

    def test_tables_created(self):
        tables = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {r["name"] for r in tables}
        self.assertIn("papers", table_names)
        self.assertIn("tags", table_names)
        self.assertIn("paper_tags", table_names)
        self.assertIn("statuses", table_names)

    def test_default_statuses(self):
        repo = StatusRepository(self.db)
        statuses = repo.get_all()
        names = [s.name for s in statuses]
        self.assertIn("In Queue", names)
        self.assertIn("Reading", names)
        self.assertIn("Read", names)
        self.assertIn("Discard", names)


class TestPaperRepository(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.db = Database(self.tmpfile.name)
        self.db.connect()
        self.repo = PaperRepository(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmpfile.name)

    def test_add_and_get_paper(self):
        paper = Paper(
            title="Test Paper",
            authors="John Doe, Jane Smith",
            year=2024,
            journal="Test Journal",
            doi="10.1234/test",
            pmid="12345678",
        )
        paper_id = self.repo.add_paper(paper)
        self.assertIsNotNone(paper_id)

        retrieved = self.repo.get_paper(paper_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Paper")
        self.assertEqual(retrieved.authors, "John Doe, Jane Smith")
        self.assertEqual(retrieved.year, 2024)
        self.assertEqual(retrieved.doi, "10.1234/test")
        self.assertEqual(retrieved.pmid, "12345678")

    def test_update_paper(self):
        paper = Paper(title="Original Title")
        paper.id = self.repo.add_paper(paper)
        paper.title = "Updated Title"
        self.repo.update_paper(paper)
        retrieved = self.repo.get_paper(paper.id)
        self.assertEqual(retrieved.title, "Updated Title")

    def test_delete_paper(self):
        paper = Paper(title="To Delete")
        paper_id = self.repo.add_paper(paper)
        self.repo.delete_paper(paper_id)
        self.assertIsNone(self.repo.get_paper(paper_id))

    def test_find_by_doi(self):
        paper = Paper(title="DOI Paper", doi="10.5555/test")
        self.repo.add_paper(paper)
        found = self.repo.find_by_doi("10.5555/test")
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "DOI Paper")

    def test_find_by_pmid(self):
        paper = Paper(title="PMID Paper", pmid="99999999")
        self.repo.add_paper(paper)
        found = self.repo.find_by_pmid("99999999")
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "PMID Paper")

    def test_priority_values(self):
        for priority in ["High", "Medium", "Low", "None"]:
            paper = Paper(title=f"{priority} paper", priority=priority)
            pid = self.repo.add_paper(paper)
            retrieved = self.repo.get_paper(pid)
            self.assertEqual(retrieved.priority, priority)

    def test_tags(self):
        tag_repo = TagRepository(self.db)
        tag_id = tag_repo.add("neuroscience", "#ff0000")

        paper = Paper(title="Tagged Paper")
        paper_id = self.repo.add_paper(paper)

        self.repo.set_paper_tags(paper_id, [tag_id])
        tags = self.repo.get_paper_tags(paper_id)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].name, "neuroscience")

    def test_delete_papers_bulk(self):
        ids = []
        for i in range(5):
            ids.append(self.repo.add_paper(Paper(title=f"Paper {i}")))
        self.repo.delete_papers(ids[:3])
        remaining = self.repo.get_all_papers()
        self.assertEqual(len(remaining), 2)


class TestTagRepository(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.db = Database(self.tmpfile.name)
        self.db.connect()
        self.repo = TagRepository(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmpfile.name)

    def test_add_and_get_tags(self):
        self.repo.add("epigenetics", "#00ff00")
        self.repo.add("neuroscience", "#ff0000")
        tags = self.repo.get_all()
        self.assertEqual(len(tags), 2)
        names = {t.name for t in tags}
        self.assertIn("epigenetics", names)
        self.assertIn("neuroscience", names)

    def test_rename_tag(self):
        tag_id = self.repo.add("old_name")
        self.repo.update(tag_id, "new_name", "#123456")
        found = self.repo.find_by_name("new_name")
        self.assertIsNotNone(found)
        self.assertEqual(found.color, "#123456")

    def test_delete_tag(self):
        tag_id = self.repo.add("temp")
        self.repo.delete(tag_id)
        self.assertIsNone(self.repo.find_by_name("temp"))


class TestStatusRepository(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.db = Database(self.tmpfile.name)
        self.db.connect()
        self.repo = StatusRepository(self.db)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmpfile.name)

    def test_add_custom_status(self):
        initial_count = len(self.repo.get_all())
        self.repo.add("Reviewing", "#abc123")
        self.assertEqual(len(self.repo.get_all()), initial_count + 1)

    def test_update_status(self):
        statuses = self.repo.get_all()
        sid = statuses[0].id
        self.repo.update(sid, "Renamed", "#999999")
        updated = self.repo.get_all()
        found = [s for s in updated if s.id == sid]
        self.assertEqual(found[0].name, "Renamed")

    def test_delete_status(self):
        sid = self.repo.add("Temp Status")
        initial = len(self.repo.get_all())
        self.repo.delete(sid)
        self.assertEqual(len(self.repo.get_all()), initial - 1)


if __name__ == "__main__":
    unittest.main()
