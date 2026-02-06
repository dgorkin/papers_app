"""Tests for metadata extraction (offline-safe, testing parsing logic)."""

import unittest

from literaturemanager.services.metadata import (
    DOI_REGEX,
    PaperMetadata,
    _parse_pubmed_xml,
)


class TestDoiRegex(unittest.TestCase):
    def test_standard_doi(self):
        text = "doi: 10.1038/nature12373"
        match = DOI_REGEX.search(text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "10.1038/nature12373")

    def test_doi_with_url(self):
        text = "https://doi.org/10.1016/j.cell.2021.01.001"
        match = DOI_REGEX.search(text)
        self.assertIsNotNone(match)
        self.assertTrue(match.group(1).startswith("10.1016"))

    def test_doi_complex(self):
        text = "DOI 10.1002/(SICI)1097-0258(19980815)17:15"
        match = DOI_REGEX.search(text)
        self.assertIsNotNone(match)

    def test_no_doi(self):
        text = "This is a normal paragraph with no DOI."
        match = DOI_REGEX.search(text)
        self.assertIsNone(match)


SAMPLE_PUBMED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <Article>
        <ArticleTitle>Sample Title for Testing</ArticleTitle>
        <AuthorList>
          <Author>
            <LastName>Smith</LastName>
            <ForeName>John A</ForeName>
          </Author>
          <Author>
            <LastName>Doe</LastName>
            <ForeName>Jane</ForeName>
          </Author>
        </AuthorList>
        <Journal>
          <Title>Journal of Testing</Title>
          <ISOAbbreviation>J Test</ISOAbbreviation>
          <JournalIssue>
            <PubDate>
              <Year>2023</Year>
            </PubDate>
          </JournalIssue>
        </Journal>
        <Abstract>
          <AbstractText>This is the abstract of the paper.</AbstractText>
        </Abstract>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="pubmed">12345678</ArticleId>
        <ArticleId IdType="doi">10.1234/test.2023</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestPubmedXmlParsing(unittest.TestCase):
    def test_parse_full_article(self):
        meta = _parse_pubmed_xml(SAMPLE_PUBMED_XML, "12345678")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.title, "Sample Title for Testing")
        self.assertEqual(meta.authors, "John A Smith, Jane Doe")
        self.assertEqual(meta.year, 2023)
        self.assertEqual(meta.journal, "Journal of Testing")
        self.assertEqual(meta.doi, "10.1234/test.2023")
        self.assertEqual(meta.pmid, "12345678")
        self.assertIn("abstract", meta.abstract.lower())

    def test_parse_empty_xml(self):
        meta = _parse_pubmed_xml("<PubmedArticleSet></PubmedArticleSet>", "000")
        self.assertIsNone(meta)

    def test_parse_invalid_xml(self):
        meta = _parse_pubmed_xml("not xml at all", "000")
        self.assertIsNone(meta)


if __name__ == "__main__":
    unittest.main()
