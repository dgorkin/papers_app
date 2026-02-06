"""Tests for the import service."""

import os
import tempfile
import unittest
from unittest.mock import patch

from literaturemanager.models.database import Database
from literaturemanager.models.paper_repository import Paper, PaperRepository
from literaturemanager.services.import_service import ImportService
from literaturemanager.services.metadata import PaperMetadata


class TestImportService(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.db = Database(self.tmpfile.name)
        self.db.connect()
        self.repo = PaperRepository(self.db)
        self.service = ImportService(self.repo)

    def tearDown(self):
        self.db.close()
        os.unlink(self.tmpfile.name)

    @patch("literaturemanager.services.import_service.fetch_metadata_by_pmid")
    def test_import_by_pmid(self, mock_fetch):
        mock_fetch.return_value = PaperMetadata(
            title="Mocked Paper",
            authors="Author One",
            year=2024,
            journal="Mock Journal",
            doi="10.9999/mock",
            pmid="11111111",
        )

        result = self.service.import_by_pmid("11111111")
        self.assertTrue(result.success)
        self.assertEqual(result.paper.title, "Mocked Paper")
        self.assertEqual(result.paper.pmid, "11111111")

    @patch("literaturemanager.services.import_service.fetch_metadata_by_pmid")
    def test_duplicate_pmid_skipped(self, mock_fetch):
        mock_fetch.return_value = PaperMetadata(
            title="First Import", pmid="22222222"
        )
        self.service.import_by_pmid("22222222")

        result = self.service.import_by_pmid("22222222")
        self.assertTrue(result.skipped)

    @patch("literaturemanager.services.import_service.fetch_metadata_by_doi")
    def test_import_by_doi(self, mock_fetch):
        mock_fetch.return_value = PaperMetadata(
            title="DOI Paper",
            authors="DOI Author",
            year=2023,
            journal="DOI Journal",
            doi="10.1234/doi.test",
        )

        result = self.service.import_by_doi("10.1234/doi.test")
        self.assertTrue(result.success)
        self.assertEqual(result.paper.title, "DOI Paper")

    def test_import_empty_pmid(self):
        result = self.service.import_by_pmid("")
        self.assertFalse(result.success)
        self.assertIn("empty", result.error.lower())

    def test_import_nonexistent_pdf(self):
        result = self.service.import_pdf("/nonexistent/path.pdf")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error.lower())


if __name__ == "__main__":
    unittest.main()
