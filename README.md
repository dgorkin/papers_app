# Literature Manager

A desktop application for organizing scientific papers, with a companion Chrome extension for adding papers directly from PubMed and journal websites.

## Features

- **Paper table** with sortable columns: Title, Authors, Year, Journal, PMID, Tags, Status, Priority
- **Search** across all metadata fields simultaneously
- **Filter** by Tags, Status, and Priority
- **Import papers** via:
  - Drag-and-drop PDF files
  - Bulk import from a folder
  - PubMed ID (PMID) lookup
  - DOI lookup
  - Chrome extension (from PubMed or journal article pages)
- **Automatic metadata extraction**: DOI from PDFs → CrossRef API → PubMed resolution
- **Tags**: User-defined, multi-select, colored chips
- **Status**: User-defined statuses (defaults: In Queue, Reading, Read, Discard)
- **Priority**: High, Medium, Low, None with visual indicators
- **Detail panel**: Double-click to view/edit all fields
- **Context menu**: Right-click for quick status/priority/tag changes
- **Bulk operations**: Select multiple papers to apply changes
- **CSV export** of the current filtered view
- **Dark and light themes**
- **Chrome extension** with offline queuing

## Tech Stack

- **Python 3.10+** with **PyQt6** for the GUI
- **SQLite** for local database storage
- **Flask** for the local API server (Chrome extension integration)
- **PyMuPDF** for PDF text extraction
- **CrossRef API** and **PubMed E-utilities** for metadata
- **Chrome Extension** (Manifest V3)

## Setup

### Prerequisites

- Python 3.10 or later
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python run.py
# or
python -m literaturemanager
```

### Build Standalone Executable

**Windows:**
```
build.bat
```

**Linux/macOS:**
```bash
./build.sh
```

The executable will be in `dist/LiteratureManager/`.

## Chrome Extension

### Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top right)
3. Click **Load unpacked**
4. Select the `chrome_extension/` directory from this project

### Usage

1. Make sure the Literature Manager desktop app is running
2. Navigate to a PubMed article page or a journal article page
3. Click the Literature Manager extension icon in the toolbar
4. Click **Add to Library**

The extension will extract the PMID (from PubMed) or DOI (from journal pages) and send it to the desktop app. If the app is not running, papers are queued in the extension's local storage and synced automatically when the app comes online.

### API Port

The default API port is `52525`. You can change it in the extension popup or in the desktop app under Tools → Settings.

## Project Structure

```
papers_app/
├── literaturemanager/          # Main Python package
│   ├── __main__.py             # Entry point
│   ├── api/
│   │   └── server.py           # Local Flask API server
│   ├── models/
│   │   ├── database.py         # SQLite schema and connection
│   │   └── paper_repository.py # CRUD operations
│   ├── services/
│   │   ├── config.py           # JSON config management
│   │   ├── import_service.py   # Paper import orchestration
│   │   └── metadata.py         # CrossRef, PubMed, PDF extraction
│   └── ui/
│       ├── delegates.py        # Custom table cell renderers
│       ├── detail_panel.py     # Paper detail/edit panel
│       ├── dialogs.py          # Tag/Status management dialogs
│       ├── main_window.py      # Main application window
│       ├── paper_table_model.py# Qt table model and filter proxy
│       └── themes.py           # Dark and light stylesheets
├── chrome_extension/           # Chrome extension (Manifest V3)
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── content_pubmed.js
│   ├── content_journal.js
│   └── icons/
├── tests/
├── run.py                      # Convenience run script
├── requirements.txt
├── literaturemanager.spec      # PyInstaller spec
├── build.bat                   # Windows build script
└── build.sh                    # Linux/macOS build script
```

## Database

SQLite database stored at:
- **Windows**: `%APPDATA%/LiteratureManager/library.db`
- **Linux/macOS**: `~/.literaturemanager/library.db`

### Schema

- `papers` — Paper metadata (title, authors, year, journal, DOI, PMID, abstract, PDF path, status, priority, notes, timestamps)
- `tags` — User-defined tags with colors
- `paper_tags` — Many-to-many junction table
- `statuses` — User-defined statuses with colors and sort order

## Design Notes

- **Metadata extraction is best-effort.** CrossRef works well for recent papers with embedded DOIs, but older PDFs often lack DOIs entirely. The app falls back to PDF text heuristics and allows manual editing of all fields.
- **The local HTTP server** must be running for the Chrome extension to work. The extension queues additions in `chrome.storage` and flushes them when the app comes online.
- **SQLite is single-machine.** For multi-machine sync (e.g., lab desktop + laptop), you would need to add a sync layer or switch to a shared database. The current design is optimized for single-machine use.
