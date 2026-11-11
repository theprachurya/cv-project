import os
import tempfile

_d = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_d}/test.db"
os.environ["UPLOAD_DIR"] = _d
os.environ["REPORT_DIR"] = _d
