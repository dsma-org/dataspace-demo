from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os, tempfile, shutil, time, tarfile
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path

HERE = os.path.dirname(__file__)
BASE_DIR = os.path.join(HERE, "content_to_share")
os.makedirs(BASE_DIR, exist_ok=True)

def safe_join(base, relpath):
    relpath = relpath.lstrip('/')
    full = os.path.normpath(os.path.join(base, relpath))
    if not full.startswith(base):
        return None
    return full

class Handler(BaseHTTPRequestHandler):
    server_version = "MiniSenderTAR/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if 'file' not in qs or not qs['file']:
            self.send_response(400); self.end_headers()
            self.wfile.write(b"Missing ?file=<relative_path>")
            return

        rel = unquote(qs['file'][0]).strip()
        full = safe_join(BASE_DIR, rel)
        if not full or not os.path.exists(full):
            self.send_response(404); self.end_headers()
            self.wfile.write(b"File not found")
            return
        if os.path.isdir(full):
            self.send_response(400); self.end_headers()
            self.wfile.write(b"Directories not allowed. Provide a single file.")
            return

        ts = time.strftime("%Y%m%d-%H%M%S")
        tmpdir = tempfile.mkdtemp(prefix="tar1-")
        tar_path = os.path.join(tmpdir, f"onefile-{ts}.tar")
        try:
            with tarfile.open(tar_path, "w") as tf:
                arcname = Path(full).name  # nur Basename im TAR
                tf.add(full, arcname=arcname)

            size = os.path.getsize(tar_path)
            self.send_response(200)
            self.send_header("Content-Type", "application/x-tar")
            self.send_header("Content-Disposition", f'attachment; filename="content_{ts}.tar"')
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with open(tar_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def log_message(self, fmt, *args):
        return

if __name__ == "__main__":
    host, port = "", 8000
    ThreadingHTTPServer((host, port), Handler).serve_forever()
