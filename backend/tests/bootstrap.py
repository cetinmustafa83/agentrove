import os
import tempfile
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="agentrove-tests-"))

os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-chars"
os.environ["SESSION_SECRET_KEY"] = "test-session-key-with-at-least-32-chars"
os.environ["ENVIRONMENT"] = "testing"
os.environ["BLOCK_DISPOSABLE_EMAILS"] = "false"
os.environ["REQUIRE_EMAIL_VERIFICATION"] = "false"
os.environ["REGISTRATION_DISABLED"] = "false"
os.environ["MAIL_PASSWORD"] = ""
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DIR / 'test.db'}"
os.environ["STORAGE_PATH"] = str(TEST_DIR / "storage")
