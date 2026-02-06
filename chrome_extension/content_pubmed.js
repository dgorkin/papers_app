// Content script for PubMed pages.
// Extracts the PMID from the current page URL or page content.

(function () {
  "use strict";

  function extractPmid() {
    // Try URL: pubmed.ncbi.nlm.nih.gov/12345678/
    const urlMatch = window.location.pathname.match(/\/(\d{6,10})\/?/);
    if (urlMatch) {
      return urlMatch[1];
    }

    // Try the meta tag
    const metaPmid = document.querySelector('meta[name="citation_pmid"]');
    if (metaPmid) {
      return metaPmid.getAttribute("content");
    }

    // Try the PMID display element on the page
    const pmidEl = document.querySelector(".current-id");
    if (pmidEl) {
      const text = pmidEl.textContent.trim();
      const match = text.match(/\d{6,10}/);
      if (match) return match[0];
    }

    return null;
  }

  // Expose to popup via messaging
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "GET_PAPER_INFO") {
      const pmid = extractPmid();
      sendResponse({
        source: "pubmed",
        pmid: pmid,
        doi: null,
        title: document.title,
      });
    }
    return true; // keep channel open for async
  });
})();
