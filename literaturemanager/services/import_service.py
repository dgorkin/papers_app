"""Paper import service coordinating PDF extraction and API lookups."""

import logging
import os
from typing import Optional

from ..models.paper_repository import Paper, PaperRepository
from .metadata import (
    PaperMetadata,
    extract_doi_from_pdf,
    extract_metadata_from_pdf_text,
    fetch_metadata_by_doi,
    fetch_metadata_by_pmid,
)

logger = logging.getLogger(__name__)


class ImportResult:
    """Result of a paper import operation."""

    def __init__(self, paper: Optional[Paper] = None, error: str = "",
                 skipped: bool = False, message: str = ""):
        self.paper = paper
        self.error = error
        self.skipped = skipped
        self.message = message

    @property
    def success(self) -> bool:
        return self.paper is not None and not self.error


class ImportService:
    """Coordinates importing papers from various sources."""

    def __init__(self, repo: PaperRepository):
        self.repo = repo

    def import_pdf(self, pdf_path: str, default_status_id: Optional[int] = None) -> ImportResult:
        """Import a paper from a PDF file.

        Workflow:
        1. Extract DOI from PDF
        2. If DOI found: query CrossRef for metadata, resolve PMID
        3. If no DOI: fall back to PDF text extraction (title, authors from font heuristics)
        4. Check for duplicate (by DOI or PMID if available)
        5. Insert into database
        """
        if not os.path.isfile(pdf_path):
            return ImportResult(error=f"File not found: {pdf_path}")

        if not pdf_path.lower().endswith(".pdf"):
            return ImportResult(error=f"Not a PDF file: {pdf_path}")

        doi = extract_doi_from_pdf(pdf_path)
        metadata: Optional[PaperMetadata] = None
        extraction_method = "none"

        if doi:
            # Check for duplicate by DOI
            existing = self.repo.find_by_doi(doi)
            if existing:
                return ImportResult(
                    skipped=True,
                    message=f"Paper already in library (DOI: {doi})",
                    paper=existing,
                )

            metadata = fetch_metadata_by_doi(doi)
            if metadata:
                extraction_method = "crossref"

                # Also check by PMID if we resolved one
                if metadata.pmid:
                    existing = self.repo.find_by_pmid(metadata.pmid)
                    if existing:
                        # Update existing with PDF path if it doesn't have one
                        if not existing.pdf_path:
                            existing.pdf_path = pdf_path
                            self.repo.update_paper(existing)
                        return ImportResult(
                            skipped=True,
                            message=f"Paper already in library (PMID: {metadata.pmid})",
                            paper=existing,
                        )

        if not metadata:
            # Fallback to PDF text extraction
            fallback = extract_metadata_from_pdf_text(pdf_path)
            metadata = PaperMetadata(
                title=fallback.title or os.path.splitext(os.path.basename(pdf_path))[0],
                authors=fallback.authors,
                doi=doi,
            )
            extraction_method = "pdf_text" if fallback.title else "filename"

        paper = Paper(
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
            journal=metadata.journal,
            doi=metadata.doi,
            pmid=metadata.pmid,
            abstract=metadata.abstract,
            pdf_path=os.path.abspath(pdf_path),
            status_id=default_status_id,
            priority="None",
        )
        paper.id = self.repo.add_paper(paper)

        msg = f"Imported via {extraction_method}"
        if extraction_method == "filename":
            msg += " (no metadata found — manual editing recommended)"

        return ImportResult(paper=paper, message=msg)

    def import_by_pmid(self, pmid: str, default_status_id: Optional[int] = None) -> ImportResult:
        """Import a paper by PubMed ID.

        Queries PubMed E-utilities for metadata and inserts into the database.
        """
        pmid = pmid.strip()
        if not pmid:
            return ImportResult(error="PMID is empty")

        # Check for duplicate
        existing = self.repo.find_by_pmid(pmid)
        if existing:
            return ImportResult(
                skipped=True,
                message=f"Paper already in library (PMID: {pmid})",
                paper=existing,
            )

        metadata = fetch_metadata_by_pmid(pmid)
        if not metadata:
            return ImportResult(error=f"Could not fetch metadata for PMID {pmid}")

        paper = Paper(
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
            journal=metadata.journal,
            doi=metadata.doi,
            pmid=metadata.pmid,
            abstract=metadata.abstract,
            status_id=default_status_id,
            priority="None",
        )
        paper.id = self.repo.add_paper(paper)
        return ImportResult(paper=paper, message="Imported from PubMed")

    def import_by_doi(self, doi: str, default_status_id: Optional[int] = None) -> ImportResult:
        """Import a paper by DOI.

        Queries CrossRef for metadata and inserts into the database.
        """
        doi = doi.strip()
        if not doi:
            return ImportResult(error="DOI is empty")

        existing = self.repo.find_by_doi(doi)
        if existing:
            return ImportResult(
                skipped=True,
                message=f"Paper already in library (DOI: {doi})",
                paper=existing,
            )

        metadata = fetch_metadata_by_doi(doi)
        if not metadata:
            return ImportResult(error=f"Could not fetch metadata for DOI {doi}")

        paper = Paper(
            title=metadata.title,
            authors=metadata.authors,
            year=metadata.year,
            journal=metadata.journal,
            doi=metadata.doi,
            pmid=metadata.pmid,
            abstract=metadata.abstract,
            status_id=default_status_id,
            priority="None",
        )
        paper.id = self.repo.add_paper(paper)
        return ImportResult(paper=paper, message="Imported from CrossRef")

    def import_folder(self, folder_path: str,
                      default_status_id: Optional[int] = None) -> list[ImportResult]:
        """Import all PDFs from a directory (non-recursive)."""
        results = []
        if not os.path.isdir(folder_path):
            return [ImportResult(error=f"Directory not found: {folder_path}")]

        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                full_path = os.path.join(folder_path, filename)
                result = self.import_pdf(full_path, default_status_id)
                results.append(result)
        return results
