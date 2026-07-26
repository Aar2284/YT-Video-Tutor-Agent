import pytest
import os
import tempfile
from app.database import init_db, get_db, DB_PATH


class TestDatabase:
    def test_init_db_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["DB_PATH"] = os.path.join(tmpdir, "test.db")
            # Override DB_PATH for testing
            import app.database as db_module
            original_path = db_module.DB_PATH
            db_module.DB_PATH = os.path.join(tmpdir, "test.db")
            try:
                init_db()
                with get_db() as conn:
                    tables = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                    table_names = [t["name"] for t in tables]
                    assert "users" in table_names
                    assert "videos" in table_names
            finally:
                db_module.DB_PATH = original_path

    def test_get_db_context_manager(self):
        import app.database as db_module
        original_path = db_module.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            db_module.DB_PATH = os.path.join(tmpdir, "test.db")
            try:
                init_db()
                with get_db() as conn:
                    result = conn.execute("SELECT 1").fetchone()
                    assert result[0] == 1
            finally:
                db_module.DB_PATH = original_path
