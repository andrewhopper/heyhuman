"""Start the local HeyHuman server (SQLite, fresh temp DB) for browser tests.

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 3f9b2e64-8d17-4c05-a6e9-1b7d4c2f8a30
import os
import sys
import tempfile
from pathlib import Path

PORT = sys.argv[1] if len(sys.argv) > 1 else "8787"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "local"))
os.environ.update(HEYHUMAN_STORE="sqlite", HEYHUMAN_PUBLISH="none")
from serve import main  # noqa: E402

main(["--host", "127.0.0.1", "--port", PORT, "--db", str(Path(tempfile.mkdtemp()) / "h.db"), "--public-url", f"http://localhost:{PORT}"])
