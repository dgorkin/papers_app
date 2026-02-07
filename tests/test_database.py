"""Tests for the JSON store and repository layer."""

import json
import os
import shutil
import tempfile
import unittest

from literaturemanager.models.json_store import JsonStore, LockError
from literaturemanager.models.paper_repository import (
    Paper,
    PaperRepository,
    StatusRepository,
    TagRepository,
)


class TestJsonStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = JsonStore(self.tmpdir)
        self.store.connect()

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_library_file(self):
        lib_path = os.path.join(self.tmpdir, "library.json")
        self.assertTrue(os.path.exists(lib_path))

    def test_default_statuses(self):
        repo = StatusRepository(self.store)
        statuses = repo.get_all()
        names = [s.name for s in statuses]
        self.assertIn("In Queue", names)
        self.assertIn("Reading", names)
        self.assertIn("Read", names)
        self.assertIn("Discard", names)

    def test_json_schema(self):
        lib_path = os.path.join(self.tmpdir, "library.json")
        with open(lib_path, "r") as f:
            data = json.load(f)
        self.assertIn("papers", data)
        self.assertIn("tags", data)
        self.assertIn("statuses", data)
        self.assertIn("last_modified", data)
        self.assertIsInstance(data["papers"], list)
        self.assertIsInstance(data["tags"], list)
        self.assertIsInstance(data["statuses"], list)

    def test_lock_file_created(self):
        lock_path = os.path.join(self.tmpdir, "library.lock")
        self.assertTrue(os.path.exists(lock_path))

    def test_lock_file_removed_on_close(self):
        lock_path = os.path.join(self.tmpdir, "library.lock")
        self.store.close()
        self.assertFalse(os.path.exists(lock_path))

    def test_lock_prevents_second_instance(self):
        store2 = JsonStore(self.tmpdir)
        with self.assertRaises(LockError):
            store2.connect()

    def test_lock_error_contains_info(self):
        store2 = JsonStore(self.tmpdir)
        try:
            store2.connect()
            self.fail("Expected LockError")
        except LockError as e:
            self.assertIn("hostname", e.lock_info)
            self.assertIn("pid", e.lock_info)
            self.assertIn("locked_at", e.lock_info)

    def test_data_persists_across_reopen(self):
        repo = PaperRepository(self.store)
        repo.add_paper(Paper(title="Persistent Paper"))
        self.store.close()

        store2 = JsonStore(self.tmpdir)
        store2.connect()
        repo2 = PaperRepository(store2)
        papers = repo2.get_all_papers()
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].title, "Persistent Paper")
        store2.close()


class TestPaperRepository(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = JsonStore(self.tmpdir)
        self.store.connect()
        self.repo = PaperRepository(self.store)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

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
        tag_repo = TagRepository(self.store)
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

    def test_status_resolved_on_paper(self):
        status_repo = StatusRepository(self.store)
        statuses = status_repo.get_all()
        first_status = statuses[0]

        paper = Paper(title="Status Paper", status_id=first_status.id)
        pid = self.repo.add_paper(paper)
        retrieved = self.repo.get_paper(pid)
        self.assertEqual(retrieved.status_name, first_status.name)
        self.assertEqual(retrieved.status_color, first_status.color)

    def test_add_tag_to_paper(self):
        tag_repo = TagRepository(self.store)
        t1 = tag_repo.add("tag1")
        t2 = tag_repo.add("tag2")

        pid = self.repo.add_paper(Paper(title="Multi-tag"))
        self.repo.add_tag_to_paper(pid, t1)
        self.repo.add_tag_to_paper(pid, t2)
        # Adding same tag again should not duplicate
        self.repo.add_tag_to_paper(pid, t1)

        tags = self.repo.get_paper_tags(pid)
        self.assertEqual(len(tags), 2)


class TestTagRepository(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = JsonStore(self.tmpdir)
        self.store.connect()
        self.repo = TagRepository(self.store)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

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

    def test_delete_tag_removes_from_papers(self):
        paper_repo = PaperRepository(self.store)
        tag_id = self.repo.add("removable")
        pid = paper_repo.add_paper(Paper(title="Test"))
        paper_repo.set_paper_tags(pid, [tag_id])
        self.repo.delete(tag_id)
        tags = paper_repo.get_paper_tags(pid)
        self.assertEqual(len(tags), 0)

    def test_duplicate_tag_name_raises(self):
        self.repo.add("unique_tag")
        with self.assertRaises(ValueError):
            self.repo.add("unique_tag")


class TestStatusRepository(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = JsonStore(self.tmpdir)
        self.store.connect()
        self.repo = StatusRepository(self.store)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

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

    def test_delete_status_clears_paper_reference(self):
        paper_repo = PaperRepository(self.store)
        sid = self.repo.add("Temporary")
        pid = paper_repo.add_paper(Paper(title="Test", status_id=sid))
        self.repo.delete(sid)
        paper = paper_repo.get_paper(pid)
        self.assertIsNone(paper.status_id)


if __name__ == "__main__":
    unittest.main()
