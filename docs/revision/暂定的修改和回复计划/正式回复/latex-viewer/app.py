#!/usr/bin/env python3
"""Intranet viewer: compile LaTeX with XeLaTeX and preview EN/ZH PDFs."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

BASE = Path(__file__).resolve().parents[1]
LATEX_DIR = BASE / "latex"
REVIEW_NOTES_DIR = BASE / "review-notes"
CURRENT_NOTES = REVIEW_NOTES_DIR / "current.json"
HISTORY_NOTES = REVIEW_NOTES_DIR / "history.jsonl"
STATIC = Path(__file__).resolve().parent / "static"

_EMPTY_CURRENT = {
    "schema_version": 1,
    "round_id": None,
    "updated_at": None,
    "comments": [],
}

LANG_CFG = {
    "en": {
        "main_tex": LATEX_DIR / "REVIEWER_RESPONSE_EN.tex",
        "pdf": LATEX_DIR / "REVIEWER_RESPONSE_EN.pdf",
        "label": "English",
    },
    "zh": {
        "main_tex": LATEX_DIR / "REVIEWER_RESPONSE_ZH.tex",
        "pdf": LATEX_DIR / "REVIEWER_RESPONSE_ZH.pdf",
        "label": "中文",
    },
}

_compile_lock = threading.Lock()
_state = {
    "last_build": None,
    "building": False,
    "latex_hash": "",
    "log": "",
    "ok": True,
}


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _latex_sources_hash() -> str:
    """Fingerprint all TeX sources under latex/ (main, generated/, .sty)."""
    parts: list[str] = []
    sty = LATEX_DIR / "reviewer_response.sty"
    if sty.exists():
        parts.append(_file_hash(sty))
    for path in sorted(LATEX_DIR.rglob("*.tex")):
        parts.append(str(path.relative_to(LATEX_DIR)))
        parts.append(_file_hash(path))
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def compile_lang(lang: str, runs: int = 2) -> tuple[bool, str]:
    cfg = LANG_CFG[lang]
    if not cfg["main_tex"].exists():
        return False, f"Missing {cfg['main_tex']}"
    env = os.environ.copy()
    figures = BASE / "figures"
    env["TEXINPUTS"] = f".:{figures}:{LATEX_DIR}:"
    logs: list[str] = []
    ok = True
    for pass_no in range(1, runs + 1):
        code, log = _run(
            [
                "xelatex",
                "-interaction=nonstopmode",
                cfg["main_tex"].name,
            ],
            LATEX_DIR,
            env=env,
        )
        logs.append(f"=== xelatex pass {pass_no} ({lang}) ===\n{log[-12000:]}")
        if code != 0:
            ok = False
            break
    pdf_ok = cfg["pdf"].exists() and cfg["pdf"].stat().st_size > 10_000
    return ok and pdf_ok, "\n".join(logs)


def full_build(reason: str = "manual") -> dict:
    with _compile_lock:
        if _state["building"]:
            return {"status": "busy"}
        _state["building"] = True
        _state["log"] = f"Build started ({reason})…\n"
        try:
            all_ok = True
            for lang in ("en", "zh"):
                ok, log = compile_lang(lang)
                _state["log"] += "\n" + log
                all_ok = all_ok and ok

            _state["latex_hash"] = _latex_sources_hash()
            _state["ok"] = all_ok
            return _finish(all_ok)
        finally:
            _state["building"] = False


def _finish(ok: bool) -> dict:
    _state["last_build"] = time.time()
    return {"status": "ok" if ok else "error", "ok": ok}


def needs_rebuild() -> bool:
    return _state["latex_hash"] != _latex_sources_hash()


def _watcher_loop(poll_seconds: float) -> None:
    while True:
        time.sleep(poll_seconds)
        if needs_rebuild() and not _state["building"]:
            full_build("auto (latex changed)")


_ALLOWED_SUFFIXES = {".tex", ".sty"}


def _safe_latex_path(rel: str) -> Path:
    rel = rel.replace("\\", "/").strip().lstrip("/")
    if ".." in rel.split("/"):
        raise ValueError("invalid path")
    full = (LATEX_DIR / rel).resolve()
    base = LATEX_DIR.resolve()
    if not str(full).startswith(str(base)):
        raise ValueError("path outside latex root")
    if full.suffix not in _ALLOWED_SUFFIXES:
        raise ValueError("file type not allowed")
    return full


def _list_latex_files() -> list[dict]:
    items: list[dict] = []
    for path in sorted(LATEX_DIR.rglob("*")):
        if not path.is_file() or path.suffix not in _ALLOWED_SUFFIXES:
            continue
        rel = path.relative_to(LATEX_DIR).as_posix()
        lang = "shared"
        if "body_en" in rel or rel.endswith("REVIEWER_RESPONSE_EN.tex"):
            lang = "en"
        elif "body_zh" in rel or rel.endswith("REVIEWER_RESPONSE_ZH.tex"):
            lang = "zh"
        items.append(
            {
                "path": rel,
                "name": path.name,
                "lang": lang,
                "size": path.stat().st_size,
                "mtime": path.stat().st_mtime,
            }
        )
    return items


def _ensure_review_notes() -> None:
    REVIEW_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    if not CURRENT_NOTES.exists():
        CURRENT_NOTES.write_text(
            json.dumps(_EMPTY_CURRENT, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if not HISTORY_NOTES.exists():
        HISTORY_NOTES.write_text("", encoding="utf-8")


def _read_current_notes() -> dict:
    _ensure_review_notes()
    try:
        data = json.loads(CURRENT_NOTES.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("comments"), list):
            return data
    except json.JSONDecodeError:
        pass
    return dict(_EMPTY_CURRENT)


def _write_current_notes(data: dict) -> None:
    _ensure_review_notes()
    CURRENT_NOTES.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _round_close_module():
    path = REVIEW_NOTES_DIR / "round_close.py"
    spec = importlib.util.spec_from_file_location("review_round_close", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("round_close.py not found")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tex_mtime_summary() -> dict[str, float | None]:
    mtimes: list[float] = []
    sty = LATEX_DIR / "reviewer_response.sty"
    if sty.exists():
        mtimes.append(sty.stat().st_mtime)
    for path in LATEX_DIR.rglob("*.tex"):
        mtimes.append(path.stat().st_mtime)
    latest = max(mtimes) if mtimes else None
    return {"en": latest, "zh": latest}


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(STATIC))

    @app.get("/")
    def index() -> Response:
        return send_from_directory(STATIC, "index.html")

    @app.get("/api/status")
    def status():
        tex_mtime = _tex_mtime_summary()
        return jsonify(
            {
                "building": _state["building"],
                "ok": _state["ok"],
                "last_build": _state["last_build"],
                "needs_rebuild": needs_rebuild(),
                "tex_mtime": tex_mtime,
                "pdf_mtime": {
                    lang: cfg["pdf"].stat().st_mtime if cfg["pdf"].exists() else None
                    for lang, cfg in LANG_CFG.items()
                },
            }
        )

    @app.post("/api/build")
    def build():
        result = full_build("api")
        return jsonify(result)

    @app.get("/api/log")
    def log_tail():
        return Response(_state["log"][-50000:], mimetype="text/plain; charset=utf-8")

    @app.get("/api/files")
    def list_files():
        return jsonify({"root": "latex", "files": _list_latex_files()})

    @app.get("/api/file")
    def read_file():
        rel = request.args.get("path", "")
        try:
            path = _safe_latex_path(rel)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if not path.exists():
            return jsonify({"error": "not found"}), 404
        return jsonify(
            {
                "path": path.relative_to(LATEX_DIR).as_posix(),
                "content": path.read_text(encoding="utf-8"),
                "mtime": path.stat().st_mtime,
            }
        )

    @app.put("/api/file")
    def write_file():
        data = request.get_json(silent=True) or {}
        rel = data.get("path") or request.args.get("path", "")
        content = data.get("content")
        if content is None:
            return jsonify({"error": "missing content"}), 400
        try:
            path = _safe_latex_path(rel)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return jsonify({"ok": True, "path": path.relative_to(LATEX_DIR).as_posix()})

    @app.get("/api/review-notes/current")
    def get_review_notes_current():
        data = _read_current_notes()
        return jsonify(data)

    @app.put("/api/review-notes/current")
    def put_review_notes_current():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get("comments"), list):
            return jsonify({"error": "expected object with comments[]"}), 400
        if data.get("schema_version") != 1:
            return jsonify({"error": "unsupported schema_version"}), 400
        _write_current_notes(data)
        return jsonify({"ok": True})

    @app.post("/api/review-notes/close")
    def post_review_notes_close():
        data = request.get_json(silent=True) or {}
        entries = data.get("entries")
        if not isinstance(entries, list):
            return jsonify({"error": "expected { entries: [...] }"}), 400
        try:
            rc = _round_close_module()
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 500
        record, err = rc.execute_close(entries, CURRENT_NOTES, HISTORY_NOTES)
        if err:
            return jsonify({"error": err}), 400
        return jsonify({"ok": True, "round_id": record["round_id"], "closed_at": record["closed_at"]})

    @app.get("/api/review-notes/history")
    def get_review_notes_history():
        _ensure_review_notes()
        text = HISTORY_NOTES.read_text(encoding="utf-8")
        return Response(text, mimetype="text/plain; charset=utf-8")

    @app.get("/pdf/<lang>")
    def pdf(lang: str):
        cfg = LANG_CFG.get(lang)
        if not cfg or not cfg["pdf"].exists():
            return jsonify({"error": "pdf not found"}), 404
        return send_file(
            cfg["pdf"],
            mimetype="application/pdf",
            as_attachment=False,
            download_name=cfg["pdf"].name,
        )

    return app


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--poll", type=float, default=3.0, help="auto-rebuild poll seconds")
    parser.add_argument("--no-watch", action="store_true")
    args = parser.parse_args()

    if not args.no_watch:
        t = threading.Thread(target=_watcher_loop, args=(args.poll,), daemon=True)
        t.start()

    threading.Thread(target=lambda: full_build("startup"), daemon=True).start()

    app = create_app()
    print(f"Reviewer response viewer (TeX-only): http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
