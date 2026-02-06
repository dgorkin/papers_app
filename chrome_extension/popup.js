// Popup script: manages the "Add to Library" workflow.
// - Checks if the desktop app is running
// - Extracts paper info from the current tab via content scripts
// - Sends the paper to the desktop app's local API
// - Queues additions in chrome.storage if the app is offline

(function () {
  "use strict";

  const statusEl = document.getElementById("appStatus");
  const paperInfoEl = document.getElementById("paperInfo");
  const paperDetailEl = document.getElementById("paperDetail");
  const addBtn = document.getElementById("addBtn");
  const messageEl = document.getElementById("message");
  const portInput = document.getElementById("portInput");
  const queueInfoEl = document.getElementById("queueInfo");

  let currentPaper = null;
  let apiPort = 52525;
  let appOnline = false;

  // Load saved port
  chrome.storage.local.get(["apiPort"], (result) => {
    if (result.apiPort) {
      apiPort = result.apiPort;
      portInput.value = apiPort;
    }
    init();
  });

  portInput.addEventListener("change", () => {
    apiPort = parseInt(portInput.value, 10) || 52525;
    chrome.storage.local.set({ apiPort });
    checkAppStatus();
  });

  function getApiBase() {
    return `http://127.0.0.1:${apiPort}`;
  }

  async function init() {
    await checkAppStatus();
    await detectPaper();
    await updateQueueInfo();
  }

  async function checkAppStatus() {
    try {
      const resp = await fetch(`${getApiBase()}/api/status`, {
        signal: AbortSignal.timeout(3000),
      });
      if (resp.ok) {
        appOnline = true;
        statusEl.innerHTML = '<span class="dot green"></span><span>App is running</span>';
        // Try to flush any queued items
        await flushQueue();
        return;
      }
    } catch (e) {
      // App not running
    }
    appOnline = false;
    statusEl.innerHTML =
      '<span class="dot red"></span><span>App is not running (will queue)</span>';
  }

  async function detectPaper() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.id) return;

      const response = await chrome.tabs.sendMessage(tab.id, { type: "GET_PAPER_INFO" });
      if (response && (response.pmid || response.doi)) {
        currentPaper = response;
        paperInfoEl.style.display = "block";

        let detail = "";
        if (response.pmid) detail += `PMID: ${response.pmid}`;
        if (response.doi) {
          if (detail) detail += " | ";
          detail += `DOI: ${response.doi}`;
        }
        paperDetailEl.textContent = detail;
        addBtn.disabled = false;
      } else {
        paperInfoEl.style.display = "block";
        paperDetailEl.textContent = "No PMID or DOI detected on this page.";
        addBtn.disabled = true;
      }
    } catch (e) {
      // Content script might not be injected on this page
      paperInfoEl.style.display = "block";
      paperDetailEl.textContent = "Not a supported page (PubMed or journal article).";
      addBtn.disabled = true;
    }
  }

  addBtn.addEventListener("click", async () => {
    if (!currentPaper) return;

    addBtn.disabled = true;
    addBtn.textContent = "Adding...";
    showMessage("", "");

    const payload = {};
    if (currentPaper.pmid) payload.pmid = currentPaper.pmid;
    else if (currentPaper.doi) payload.doi = currentPaper.doi;

    if (appOnline) {
      await sendToApp(payload);
    } else {
      await queuePaper(payload);
      showMessage("Queued for when app comes online", "info");
      addBtn.textContent = "Add to Library";
      addBtn.disabled = false;
    }

    await updateQueueInfo();
  });

  async function sendToApp(payload) {
    try {
      const resp = await fetch(`${getApiBase()}/api/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(15000),
      });
      const data = await resp.json();

      if (data.success) {
        if (data.skipped) {
          showMessage("Already in your library", "info");
        } else {
          const title = data.paper?.title || "Paper";
          showMessage(`Added: ${title}`, "success");
        }
      } else {
        showMessage(data.message || "Failed to add", "error");
      }
    } catch (e) {
      // App went offline — queue instead
      await queuePaper(payload);
      showMessage("App unreachable — queued for later", "info");
    }

    addBtn.textContent = "Add to Library";
    addBtn.disabled = false;
  }

  async function queuePaper(payload) {
    const result = await chrome.storage.local.get(["queue"]);
    const queue = result.queue || [];
    payload._timestamp = Date.now();
    queue.push(payload);
    await chrome.storage.local.set({ queue });
  }

  async function flushQueue() {
    const result = await chrome.storage.local.get(["queue"]);
    const queue = result.queue || [];
    if (queue.length === 0) return;

    const remaining = [];
    for (const item of queue) {
      try {
        const resp = await fetch(`${getApiBase()}/api/add`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(item),
          signal: AbortSignal.timeout(10000),
        });
        if (!resp.ok) {
          remaining.push(item);
        }
      } catch (e) {
        remaining.push(item);
        break; // Stop if app goes offline mid-flush
      }
    }
    await chrome.storage.local.set({ queue: remaining });
  }

  async function updateQueueInfo() {
    const result = await chrome.storage.local.get(["queue"]);
    const queue = result.queue || [];
    if (queue.length > 0) {
      queueInfoEl.textContent = `${queue.length} paper(s) queued for sync`;
    } else {
      queueInfoEl.textContent = "";
    }
  }

  function showMessage(text, type) {
    messageEl.textContent = text;
    messageEl.className = "message";
    if (type) messageEl.classList.add(type);
  }
})();
