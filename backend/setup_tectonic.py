"""Download the latest Tectonic release for this OS/arch into the user data dir (idempotent).

  python setup_tectonic.py     # prints {"ok", "path", "version"} (plus "error" on failure) as the last stdout line

Windows: %APPDATA%/career-tailor/tectonic/tectonic.exe, others: ~/.local/share/career-tailor/tectonic/tectonic.
"""
import io, json, os, pathlib, platform, stat, subprocess, sys, tarfile, urllib.request, zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from render import data_dir, exe_name

API = "https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest"


def target_triple():
    m = platform.machine().lower()
    arm = m in ("arm64", "aarch64")
    if sys.platform == "win32":
        return "aarch64-pc-windows-msvc" if arm else "x86_64-pc-windows-msvc"
    if sys.platform == "darwin":
        return "aarch64-apple-darwin" if arm else "x86_64-apple-darwin"
    return "aarch64-unknown-linux-musl" if arm else "x86_64-unknown-linux-gnu"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "career-tailor", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def version_of(exe):
    r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, errors="replace", timeout=30)
    return (r.stdout or r.stderr).strip()


def setup():
    dest = data_dir() / exe_name()
    if dest.is_file():
        try:
            return {"ok": True, "path": str(dest), "version": version_of(dest)}
        except Exception:
            pass  # broken install: fall through and re-download
    rel = json.loads(get(API))
    tri = target_triple()
    # prefer the exact triple; on linux x86_64 fall back to musl
    names = [a for a in rel["assets"] if tri in a["name"] and a["name"].endswith((".zip", ".tar.gz"))]
    if not names and tri.endswith("linux-gnu"):
        names = [a for a in rel["assets"] if tri.replace("gnu", "musl") in a["name"] and a["name"].endswith(".tar.gz")]
    if not names:
        raise RuntimeError(f"no Tectonic release asset for {tri} in {rel.get('tag_name')}; install it manually and put it on PATH")
    asset = names[0]
    blob = get(asset["browser_download_url"])
    data_dir().mkdir(parents=True, exist_ok=True)
    if asset["name"].endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            member = next(n for n in z.namelist() if pathlib.PurePosixPath(n).name == exe_name())
            dest.write_bytes(z.read(member))
    else:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as t:
            member = next(m for m in t.getmembers() if m.isfile() and pathlib.PurePosixPath(m.name).name == exe_name())
            dest.write_bytes(t.extractfile(member).read())
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return {"ok": True, "path": str(dest), "version": version_of(dest) or rel.get("tag_name", "")}


if __name__ == "__main__":
    try:
        res = setup()
    except Exception as ex:
        res = {"ok": False, "path": "", "version": "", "error": f"{type(ex).__name__}: {ex}"}
    print(json.dumps(res))
    sys.exit(0 if res["ok"] else 1)
