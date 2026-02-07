"""Entry point for the Literature Manager application."""

import logging
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from .api.server import ApiServer
from .models.json_store import JsonStore, LockError
from .services.config import Config
from .services.import_service import ImportService
from .models.paper_repository import PaperRepository
from .ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Literature Manager")
    app.setOrganizationName("LiteratureManager")

    # Initialize config
    config = Config()

    # Initialize JSON store with lock file protection
    library_dir = config.get_library_dir()
    store = JsonStore(library_dir)
    try:
        store.connect()
    except LockError as e:
        QMessageBox.critical(
            None,
            "Library Locked",
            str(e),
        )
        sys.exit(1)

    # Create main window
    window = MainWindow(store, config)

    # Set up the API server callback
    import_service = ImportService(PaperRepository(store))

    def api_add_callback(data: dict) -> dict:
        pmid = data.get("pmid")
        doi = data.get("doi")

        if pmid:
            result = import_service.import_by_pmid(pmid)
        elif doi:
            result = import_service.import_by_doi(doi)
        else:
            return {"success": False, "message": "No pmid or doi provided"}

        if result.success:
            # Signal the main window to refresh (thread-safe via signal)
            window.paper_added_externally.emit(data)
            return {
                "success": True,
                "message": result.message,
                "paper": {
                    "id": result.paper.id,
                    "title": result.paper.title,
                    "authors": result.paper.authors,
                },
            }
        elif result.skipped:
            return {
                "success": True,
                "message": result.message,
                "skipped": True,
            }
        else:
            return {"success": False, "message": result.error}

    # Start local API server
    api_port = config.get("api_port", 52525)
    if config.get("api_enabled", True):
        api_server = ApiServer(api_port, api_add_callback)
        api_server.start()
        logger.info("Local API server running on http://127.0.0.1:%d", api_port)
    else:
        api_server = None

    window.show()
    window.status_bar.showMessage(
        f"Ready — API server on port {api_port}" if api_server else "Ready"
    )

    exit_code = app.exec()

    # Cleanup
    if api_server:
        api_server.stop()
    store.close()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
