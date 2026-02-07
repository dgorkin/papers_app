"""JSON file-based data store for Literature Manager.

Replaces SQLite with a single JSON file. The full dataset is loaded into
memory on startup and written back on every modification. A lock file
prevents the application from being opened on two machines simultaneously.
"""

import json
import logging
import os
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LockError(Exception):
    """Raised when the library lock file is held by another instance."""

    def __init__(self, lock_info: dict):
        self.lock_info = lock_info
        machine = lock_info.get("hostname", "unknown")
        pid = lock_info.get("pid", "?")
        locked_at = lock_info.get("locked_at", "unknown time")
        super().__init__(
            f"Library is locked by another instance.\n\n"
            f"Machine: {machine}\n"
            f"PID: {pid}\n"
            f"Locked at: {locked_at}\n\n"
            f"If you are sure no other instance is running, delete the file:\n"
            f"  {lock_info.get('lock_path', 'library.lock')}"
        )


def get_default_library_dir() -> str:
    """Get the default library directory, preferring OneDrive if available."""
    home = Path.home()

    # Check common OneDrive paths
    onedrive_candidates = []
    if os.name == "nt":
        # Windows: check environment variable first
        onedrive_env = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
        if onedrive_env:
            onedrive_candidates.append(Path(onedrive_env))
        onedrive_candidates.extend([
            home / "OneDrive",
            home / "OneDrive - Personal",
        ])
    else:
        # macOS / Linux
        onedrive_candidates.extend([
            home / "OneDrive",
            home / "OneDrive - Personal",
        ])

    for candidate in onedrive_candidates:
        if candidate.is_dir():
            lib_dir = candidate / "LiteratureManager"
            return str(lib_dir)

    # Fallback: app data directory
    if os.name == "nt":
        app_data = os.environ.get("APPDATA", str(home))
        return os.path.join(app_data, "LiteratureManager")
    else:
        return os.path.join(str(home), ".literaturemanager")


# Empty library structure with default statuses
_EMPTY_LIBRARY = {
    "papers": [],
    "tags": [],
    "statuses": [
        {"id": 1, "name": "In Queue", "color": "#5bc0de", "sort_order": 0},
        {"id": 2, "name": "Reading", "color": "#f0ad4e", "sort_order": 1},
        {"id": 3, "name": "Read", "color": "#5cb85c", "sort_order": 2},
        {"id": 4, "name": "Discard", "color": "#d9534f", "sort_order": 3},
    ],
    "last_modified": "",
}


class JsonStore:
    """JSON file-based data store with lock file protection.

    Loads the entire dataset into memory on startup and writes back to
    the JSON file on every modification via ``save()``.
    """

    def __init__(self, library_dir: Optional[str] = None):
        self.library_dir = library_dir or get_default_library_dir()
        self.library_path = os.path.join(self.library_dir, "library.json")
        self.lock_path = os.path.join(self.library_dir, "library.lock")
        self._data: dict[str, Any] = {}
        self._locked = False

    # ── Lifecycle ──────────────────────────────────────────────────

    def connect(self):
        """Acquire the lock, create the directory if needed, and load data."""
        os.makedirs(self.library_dir, exist_ok=True)
        self._acquire_lock()
        self._load()

    def close(self):
        """Release the lock file."""
        self._release_lock()

    # ── Lock file ─────────────────────────────────────────────────

    def _acquire_lock(self):
        """Create a lock file. Raises LockError if one already exists."""
        if os.path.exists(self.lock_path):
            try:
                with open(self.lock_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                info["lock_path"] = self.lock_path
                raise LockError(info)
            except (json.JSONDecodeError, OSError):
                # Corrupt lock file — remove and proceed
                logger.warning("Removing corrupt lock file: %s", self.lock_path)
                os.remove(self.lock_path)

        info = {
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "platform": platform.system(),
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.lock_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
        self._locked = True
        logger.info("Lock acquired: %s", self.lock_path)

    def _release_lock(self):
        """Remove the lock file if we created it."""
        if self._locked and os.path.exists(self.lock_path):
            try:
                os.remove(self.lock_path)
                logger.info("Lock released: %s", self.lock_path)
            except OSError as e:
                logger.warning("Could not remove lock file: %s", e)
            self._locked = False

    # ── Load / Save ───────────────────────────────────────────────

    def _load(self):
        """Load data from the JSON file, or initialize with defaults."""
        if os.path.exists(self.library_path):
            try:
                with open(self.library_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info("Loaded library from %s", self.library_path)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load library: %s — starting fresh", e)
                self._data = json.loads(json.dumps(_EMPTY_LIBRARY))
        else:
            self._data = json.loads(json.dumps(_EMPTY_LIBRARY))
            self.save()
            logger.info("Created new library at %s", self.library_path)

    def save(self):
        """Write the full dataset back to the JSON file."""
        self._data["last_modified"] = datetime.now(timezone.utc).isoformat()
        with open(self.library_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ── Data access ───────────────────────────────────────────────

    @property
    def papers(self) -> list[dict]:
        return self._data.setdefault("papers", [])

    @property
    def tags(self) -> list[dict]:
        return self._data.setdefault("tags", [])

    @property
    def statuses(self) -> list[dict]:
        return self._data.setdefault("statuses", [])

    # ── ID generation ─────────────────────────────────────────────

    def next_paper_id(self) -> int:
        if not self.papers:
            return 1
        return max(p["id"] for p in self.papers) + 1

    def next_tag_id(self) -> int:
        if not self.tags:
            return 1
        return max(t["id"] for t in self.tags) + 1

    def next_status_id(self) -> int:
        if not self.statuses:
            return 1
        return max(s["id"] for s in self.statuses) + 1
