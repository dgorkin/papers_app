// Content script for journal article pages.
// Extracts DOI from meta tags commonly used by publishers.

(function () {
  "use strict";

  function extractDoi() {
    // Common meta tag names for DOI
    const doiSelectors = [
      'meta[name="citation_doi"]',
      'meta[name="dc.identifier"][scheme="doi"]',
      'meta[name="DC.Identifier"][scheme="doi"]',
      'meta[name="dc.Identifier"]',
      'meta[property="citation_doi"]',
      'meta[name="DOI"]',
      'meta[name="doi"]',
      'meta[name="prism.doi"]',
    ];

    for (const selector of doiSelectors) {
      const el = document.querySelector(selector);
      if (el) {
        let content = el.getAttribute("content") || "";
        // Normalize: strip URL prefix if present
        content = content.replace(/^https?:\/\/doi\.org\//, "").trim();
        if (content && content.startsWith("10.")) {
          return content;
        }
      }
    }

    // Fallback: look for a DOI link in the page
    const doiLinks = document.querySelectorAll('a[href*="doi.org/10."]');
    if (doiLinks.length > 0) {
      const href = doiLinks[0].getAttribute("href");
      const match = href.match(/(10\.\d{4,9}\/[^\s&"]+)/);
      if (match) return match[1];
    }

    return null;
  }

  function extractPmid() {
    // Some journal pages include a PMID meta tag
    const meta = document.querySelector('meta[name="citation_pmid"]');
    if (meta) {
      return meta.getAttribute("content");
    }
    return null;
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "GET_PAPER_INFO") {
      const doi = extractDoi();
      const pmid = extractPmid();
      sendResponse({
        source: "journal",
        doi: doi,
        pmid: pmid,
        title: document.title,
      });
    }
    return true;
  });
})();
