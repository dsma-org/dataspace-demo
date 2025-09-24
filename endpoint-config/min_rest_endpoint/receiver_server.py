from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os, time, io, tarfile, tempfile, shutil
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(__file__)
BASE_DIR = os.path.join(HERE, "content_to_receive")
os.makedirs(BASE_DIR, exist_ok=True)

# --- helpers -----------------------------------------------------------------
def _read_chunked_to_file(rfile, out_path):
    with open(out_path, "wb") as f:
        while True:
            line = rfile.readline()
            if not line:
                break
            line = line.strip()
            if b";" in line:
                line = line.split(b";", 1)[0]
            try:
                size = int(line, 16)
            except ValueError:
                break
            if size == 0:
                while True:
                    trailer = rfile.readline()
                    if not trailer or trailer in (b"\r\n", b"\n"):
                        break
                break
            chunk = rfile.read(size)
            f.write(chunk)
            _ = rfile.read(2)  # CRLF

def _read_body_to_tempfile(handler):
    tmpdir = tempfile.mkdtemp(prefix="recv-")
    tmpfile = os.path.join(tmpdir, "payload.bin")
    te = (handler.headers.get('Transfer-Encoding') or "").lower()
    if "chunked" in te:
        _read_chunked_to_file(handler.rfile, tmpfile)
    else:
        try:
            length = int(handler.headers.get('Content-Length', 0))
        except ValueError:
            length = 0
        with open(tmpfile, "wb") as f:
            if length > 0:
                remaining = length
                bufsize = 1024 * 1024
                while remaining > 0:
                    chunk = handler.rfile.read(min(bufsize, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            else:
                shutil.copyfileobj(handler.rfile, f)
    return tmpdir, tmpfile

def _is_tar_file(path):
    try:
        with tarfile.open(path, mode="r:*") as tf:
            _ = tf.getmembers()
        return True
    except tarfile.TarError:
        return False

# --- handler -----------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "MiniRecv/1.6"

    def do_PUT(self):
        if not self.path.startswith("/receive"):
            self.send_response(404); self.end_headers(); return

        tmpdir, tmpfile = _read_body_to_tempfile(self)
        try:
            if os.path.getsize(tmpfile) == 0:
                self.send_response(400); self.end_headers()
                self.wfile.write(b"No content received"); return

            ts = time.strftime('%Y-%m-%d--%H-%M-%S')
            target_tar = os.path.join(BASE_DIR, f"content-{ts}.tar")

            if _is_tar_file(tmpfile):
                # TAR -> unveraendert speichern
                shutil.move(tmpfile, target_tar)
            else:
                # kein TAR -> Dateiname MUSS in URL stehen
                parsed = urlparse(self.path)
                path_tail = parsed.path[len("/receive"):].lstrip('/')
                qs_name = (parse_qs(parsed.query).get('name') or [None])[0]
                inner_name = (path_tail or (qs_name.lstrip('/') if qs_name else None))
                if not inner_name:
                    self.send_response(400); self.end_headers()
                    self.wfile.write(b"Missing filename: use /receive/<name> or ?name=<name> when sending non-TAR")
                    return

                with open(tmpfile, "rb") as fsrc:
                    data = fsrc.read()
                info = tarfile.TarInfo(name=inner_name)
                info.size = len(data)
                info.mtime = int(time.time())
                with tarfile.open(target_tar, "w") as tf:
                    tf.addfile(info, io.BytesIO(data))

            self.send_response(201); self.end_headers()
            self.wfile.write(f"Stored TAR at {target_tar}".encode())

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def do_POST(self):
        self.do_PUT()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "POST, PUT, OPTIONS, HEAD")
        self.end_headers()

    def log_message(self, *args, **kwargs):
        return

if __name__ == "__main__":
    host, port = "", 9000
    ThreadingHTTPServer((host, port), Handler).serve_forever()
