"""Metadata extraction services for papers.

Supports:
- CrossRef API for DOI-based lookups
- PubMed E-utilities for PMID-based lookups and DOI-to-PMID resolution
- PDF text extraction with DOI regex matching
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

# Timeout for all HTTP requests
REQUEST_TIMEOUT = 15

# Regex to find DOIs in text
DOI_REGEX = re.compile(
    r'\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)',
    re.IGNORECASE,
)


@dataclass
class PaperMetadata:
    """Extracted metadata for a paper."""
    title: str = ""
    authors: str = ""
    year: Optional[int] = None
    journal: str = ""
    doi: Optional[str] = None
    pmid: Optional[str] = None
    abstract: str = ""


def fetch_metadata_by_doi(doi: str) -> Optional[PaperMetadata]:
    """Fetch paper metadata from CrossRef using a DOI.

    Queries https://api.crossref.org/works/{doi} and parses
    the response into a PaperMetadata object.
    """
    try:
        url = f"https://api.crossref.org/works/{doi}"
        headers = {
            "User-Agent": "LiteratureManager/1.0 (mailto:user@example.com)"
        }
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("message", {})

        # Parse authors
        authors_list = data.get("author", [])
        author_names = []
        for a in authors_list:
            given = a.get("given", "")
            family = a.get("family", "")
            if given and family:
                author_names.append(f"{given} {family}")
            elif family:
                author_names.append(family)
        authors = ", ".join(author_names)

        # Parse year
        year = None
        date_parts = data.get("published-print", data.get("published-online", {}))
        if date_parts and "date-parts" in date_parts:
            parts = date_parts["date-parts"]
            if parts and parts[0] and parts[0][0]:
                year = int(parts[0][0])

        # Parse title
        titles = data.get("title", [])
        title = titles[0] if titles else ""

        # Parse journal
        container = data.get("container-title", [])
        journal = container[0] if container else ""

        # Parse abstract (CrossRef sometimes includes it)
        abstract = data.get("abstract", "")
        # Strip JATS XML tags if present
        abstract = re.sub(r"<[^>]+>", "", abstract).strip()

        meta = PaperMetadata(
            title=title,
            authors=authors,
            year=year,
            journal=journal,
            doi=doi,
            abstract=abstract,
        )

        # Try to also resolve the PMID
        pmid = resolve_doi_to_pmid(doi)
        if pmid:
            meta.pmid = pmid

        return meta

    except requests.RequestException as e:
        logger.warning("CrossRef lookup failed for DOI %s: %s", doi, e)
        return None
    except (KeyError, IndexError, ValueError) as e:
        logger.warning("Failed to parse CrossRef response for DOI %s: %s", doi, e)
        return None


def resolve_doi_to_pmid(doi: str) -> Optional[str]:
    """Use PubMed E-utilities to resolve a DOI to a PMID.

    Queries esearch.fcgi with the DOI as a search term.
    """
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": f"{doi}[doi]",
            "retmode": "json",
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        if id_list:
            return id_list[0]
        return None
    except Exception as e:
        logger.warning("DOI-to-PMID resolution failed for %s: %s", doi, e)
        return None


def fetch_metadata_by_pmid(pmid: str) -> Optional[PaperMetadata]:
    """Fetch paper metadata from PubMed E-utilities using a PMID.

    Queries efetch.fcgi with XML output and parses the PubmedArticle element.
    """
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return _parse_pubmed_xml(resp.text, pmid)
    except requests.RequestException as e:
        logger.warning("PubMed lookup failed for PMID %s: %s", pmid, e)
        return None


def _parse_pubmed_xml(xml_text: str, pmid: str) -> Optional[PaperMetadata]:
    """Parse PubMed efetch XML response into PaperMetadata."""
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("Failed to parse PubMed XML: %s", e)
        return None

    article = root.find(".//PubmedArticle")
    if article is None:
        return None

    medline = article.find(".//MedlineCitation")
    if medline is None:
        return None

    art = medline.find(".//Article")
    if art is None:
        return None

    # Title
    title_el = art.find(".//ArticleTitle")
    title = _element_text(title_el)

    # Authors
    author_list = art.find(".//AuthorList")
    author_names = []
    if author_list is not None:
        for author in author_list.findall("Author"):
            last = _element_text(author.find("LastName"))
            fore = _element_text(author.find("ForeName"))
            if last and fore:
                author_names.append(f"{fore} {last}")
            elif last:
                author_names.append(last)
    authors = ", ".join(author_names)

    # Year
    year = None
    pub_date = art.find(".//Journal/JournalIssue/PubDate")
    if pub_date is not None:
        year_el = pub_date.find("Year")
        if year_el is not None and year_el.text:
            try:
                year = int(year_el.text)
            except ValueError:
                pass
        if year is None:
            medline_date = pub_date.find("MedlineDate")
            if medline_date is not None and medline_date.text:
                m = re.search(r'(\d{4})', medline_date.text)
                if m:
                    year = int(m.group(1))

    # Journal
    journal_el = art.find(".//Journal/Title")
    journal = _element_text(journal_el)
    if not journal:
        journal_el = art.find(".//Journal/ISOAbbreviation")
        journal = _element_text(journal_el)

    # Abstract
    abstract_el = art.find(".//Abstract/AbstractText")
    abstract = _element_text(abstract_el)

    # DOI
    doi = None
    for eid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        if eid.get("IdType") == "doi":
            doi = eid.text
            break

    return PaperMetadata(
        title=title,
        authors=authors,
        year=year,
        journal=journal,
        doi=doi,
        pmid=pmid,
        abstract=abstract,
    )


def _element_text(el) -> str:
    """Safely extract text from an XML element, including any tail/children text."""
    if el is None:
        return ""
    # itertext() captures nested inline markup text
    return "".join(el.itertext()).strip()


def extract_doi_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract a DOI from a PDF file.

    Tries two approaches:
    1. Read PDF metadata (XMP / info dict) for a DOI field
    2. Search the first few pages of text for a DOI pattern
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed; cannot extract DOI from PDF.")
        return None

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.warning("Failed to open PDF %s: %s", pdf_path, e)
        return None

    try:
        # Check metadata
        meta = doc.metadata
        if meta:
            for key in ("doi", "subject", "keywords"):
                val = meta.get(key, "") or ""
                match = DOI_REGEX.search(val)
                if match:
                    return match.group(1)

        # Search first 3 pages of text
        pages_to_check = min(3, len(doc))
        for i in range(pages_to_check):
            page = doc[i]
            text = page.get_text()
            match = DOI_REGEX.search(text)
            if match:
                return match.group(1)
    finally:
        doc.close()

    return None


def extract_metadata_from_pdf_text(pdf_path: str) -> PaperMetadata:
    """Fallback: try to extract title/authors from the first page of a PDF.

    This is a best-effort heuristic when no DOI is found.
    """
    meta = PaperMetadata()
    try:
        import fitz
    except ImportError:
        return meta

    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            doc.close()
            return meta

        # Use PDF metadata if available
        pdf_meta = doc.metadata
        if pdf_meta:
            if pdf_meta.get("title"):
                meta.title = pdf_meta["title"].strip()
            if pdf_meta.get("author"):
                meta.authors = pdf_meta["author"].strip()

        # If title not found in metadata, use first large-font text block
        if not meta.title:
            page = doc[0]
            blocks = page.get_text("dict", flags=0).get("blocks", [])
            max_size = 0
            candidate = ""
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 0)
                        text = span.get("text", "").strip()
                        if size > max_size and len(text) > 10:
                            max_size = size
                            candidate = text
            if candidate:
                meta.title = candidate

        doc.close()
    except Exception as e:
        logger.warning("PDF text extraction failed for %s: %s", pdf_path, e)

    return meta
