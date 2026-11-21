#!/usr/bin/env python3
"""Intranet viewer: compile LaTeX with XeLaTeX and preview EN/ZH PDFs."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import threading
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file, send_from_directory

BASE = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"

# --- 工程根目录（相对 正式回复/）---
RESPONSE_DIR = BASE / "latex"
MANUSCRIPT_DIR = BASE / "26_Nature_ThyroidAgent"
FIGURES_DIR = BASE / "figures"

PROJECTS: dict[str, dict] = {
    "response": {
        "root": RESPONSE_DIR,
        "label": "审稿回复",
        "figures_texinputs": FIGURES_DIR,
        "editable": {".tex", ".sty"},
        "langs": {
            "en": {
                "main_tex": RESPONSE_DIR / "REVIEWER_RESPONSE_EN.tex",
                "pdf": RESPONSE_DIR / "REVIEWER_RESPONSE_EN.pdf",
            },
            "zh": {
                "main_tex": RESPONSE_DIR / "REVIEWER_RESPONSE_ZH.tex",
                "pdf": RESPONSE_DIR / "REVIEWER_RESPONSE_ZH.pdf",
            },
        },
    },
    "manuscript": {
        "root": MANUSCRIPT_DIR,
        "label": "Nature 主稿",
        "figures_texinputs": None,
        "editable": {".tex", ".sty", ".cls", ".bib"},
        "main_tex": MANUSCRIPT_DIR / "main_v2.tex",
        "pdf": MANUSCRIPT_DIR / "main_v2.pdf",
        "engine": "xelatex",
        "bibtex": True,
    },
}

DEFAULT_PROJECT = "response"
LATEX_DIR = RESPONSE_DIR  # legacy name for response-only paths in messages
LANG_CFG = PROJECTS["response"]["langs"]  # API: en/zh reviewer-response PDFs only

_compile_lock = threading.Lock()
_state = {
    "last_build": None,
    "building": False,
    "log": "",
    "ok": True,
    "hash": {"response": "", "manuscript": ""},
    "ok_project": {"response": True, "manuscript": True},
}


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources_hash(project_id: str) -> str:
    """Fingerprint sources under a project root."""
    cfg = PROJECTS[project_id]
    root: Path = cfg["root"]
    parts: list[str] = [project_id]
    suffixes = cfg.get("editable", {".tex", ".sty"})
    if not root.is_dir():
        return hashlib.sha256(parts[0].encode()).hexdigest()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        rel = path.relative_to(root).as_posix()
        parts.append(rel)
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


def _latex_log_errors(main_tex: Path) -> list[str]:
    log_path = main_tex.with_suffix(".log")
    if not log_path.exists():
        return []
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    err_re = re.compile(
        r"^! |"
        r": Undefined control sequence\.|"
        r": Extra , or forgotten \\endgroup\.|"
        r": You can't use `macro parameter character #'|"
        r"Emergency stop"
    )
    hits: list[str] = []
    for line in text.splitlines():
        if err_re.search(line):
            hits.append(line)
    return hits[:20]


def _texinputs_env(project_id: str) -> dict[str, str]:
    env = os.environ.copy()
    cfg = PROJECTS[project_id]
    root = cfg["root"]
    parts = [".", str(root)]
    fig = cfg.get("figures_texinputs")
    if fig and fig.is_dir():
        parts.append(str(fig))
    env["TEXINPUTS"] = ":".join(parts) + ":"
    env["BIBINPUTS"] = f".:{root}:"
    return env


def compile_response_lang(lang: str, runs: int = 2) -> tuple[bool, str]:
    proj = PROJECTS["response"]
    cfg = proj["langs"][lang]
    main_tex: Path = cfg["main_tex"]
    cwd = proj["root"]
    if not main_tex.exists():
        return False, f"Missing {main_tex}"
    env = _texinputs_env("response")
    logs: list[str] = []
    last_code = 0
    last_log_errors: list[str] = []
    engine = "xelatex"
    for pass_no in range(1, runs + 1):
        code, log = _run(
            [engine, "-interaction=nonstopmode", "-file-line-error", main_tex.name],
            cwd,
            env=env,
        )
        last_code = code
        logs.append(f"=== {engine} pass {pass_no}/{runs} (response/{lang}) exit={code} ===\n{log[-8000:]}")
        last_log_errors = _latex_log_errors(main_tex)
        if last_log_errors:
            logs.append("=== LaTeX errors (.log) ===\n" + "\n".join(last_log_errors))
    pdf_ok = cfg["pdf"].exists() and cfg["pdf"].stat().st_size > 10_000
    ok = last_code == 0 and not last_log_errors and pdf_ok
    logs.append(
        f"=== {'OK' if ok else 'FAILED'} (response/{lang}): pdf_ok={pdf_ok} ===\n"
    )
    return ok, "\n".join(logs)


def compile_manuscript() -> tuple[bool, str]:
    cfg = PROJECTS["manuscript"]
    root: Path = cfg["root"]
    main_tex: Path = cfg["main_tex"]
    pdf: Path = cfg["pdf"]
    if not main_tex.exists():
        return False, f"Missing {main_tex}"
    engine = cfg.get("engine", "xelatex")
    env = _texinputs_env("manuscript")
    stem = main_tex.stem
    logs: list[str] = []
    last_code = 0
    last_log_errors: list[str] = []

    def run_pass(label: str) -> None:
        nonlocal last_code, last_log_errors
        code, log = _run(
            [engine, "-interaction=nonstopmode", "-file-line-error", main_tex.name],
            root,
            env=env,
        )
        last_code = code
        logs.append(f"=== {label} exit={code} ===\n{log[-12000:]}")
        last_log_errors = _latex_log_errors(main_tex)

    run_pass(f"{engine} pass 1")
    aux = main_tex.with_suffix(".aux")
    if cfg.get("bibtex") and aux.exists():
        code, log = _run(["bibtex", stem], root, env=env)
        logs.append(f"=== bibtex exit={code} ===\n{log[-4000:]}")
    run_pass(f"{engine} pass 2")
    run_pass(f"{engine} pass 3")

    pdf_ok = pdf.exists() and pdf.stat().st_size > 50_000
    ok = not last_log_errors and pdf_ok
    logs.append(f"=== {'OK' if ok else 'FAILED'} (manuscript): pdf_ok={pdf_ok} ===\n")
    return ok, "\n".join(logs)


def full_build(reason: str = "manual", *, include_manuscript: bool = True) -> dict:
    with _compile_lock:
        if _state["building"]:
            return {"status": "busy"}
        _state["building"] = True
        _state["log"] = f"Build started ({reason})…\n"
        try:
            all_ok = True
            for lang in ("en", "zh"):
                ok, log = compile_response_lang(lang)
                _state["log"] += "\n" + log
                all_ok = all_ok and ok
            _state["ok_project"]["response"] = all_ok
            _state["hash"]["response"] = _sources_hash("response")

            if include_manuscript and MANUSCRIPT_DIR.is_dir():
                ok_m, log_m = compile_manuscript()
                _state["log"] += "\n" + log_m
                _state["ok_project"]["manuscript"] = ok_m
                _state["hash"]["manuscript"] = _sources_hash("manuscript")
                all_ok = all_ok and ok_m
            elif include_manuscript:
                _state["log"] += "\n=== manuscript: skip (no 26_Nature_ThyroidAgent/) ===\n"

            _state["ok"] = all_ok
            return _finish(all_ok)
        finally:
            _state["building"] = False


def _finish(ok: bool) -> dict:
    _state["last_build"] = time.time()
    return {"status": "ok" if ok else "error", "ok": ok}


def needs_rebuild(project_id: str | None = None) -> bool:
    ids = [project_id] if project_id else list(PROJECTS)
    for pid in ids:
        if PROJECTS[pid]["root"].is_dir():
            if _state["hash"].get(pid) != _sources_hash(pid):
                return True
    return False


def _watcher_loop(poll_seconds: float, include_manuscript: bool) -> None:
    while True:
        time.sleep(poll_seconds)
        if needs_rebuild() and not _state["building"]:
            full_build("auto (sources changed)", include_manuscript=include_manuscript)


def _project_id(raw: str | None) -> str:
    pid = (raw or DEFAULT_PROJECT).strip().lower()
    if pid not in PROJECTS:
        raise ValueError("unknown project")
    return pid


def _safe_latex_path(rel: str, project_id: str) -> Path:
    root = PROJECTS[project_id]["root"].resolve()
    suffixes = PROJECTS[project_id].get("editable", {".tex", ".sty"})
    rel = rel.replace("\\", "/").strip().lstrip("/")
    if ".." in rel.split("/"):
        raise ValueError("invalid path")
    full = (root / rel).resolve()
    if not str(full).startswith(str(root)):
        raise ValueError("path outside project root")
    if full.suffix not in suffixes:
        raise ValueError("file type not allowed")
    return full


def _list_latex_files(project_id: str) -> list[dict]:
    root = PROJECTS[project_id]["root"]
    suffixes = PROJECTS[project_id].get("editable", {".tex", ".sty"})
    items: list[dict] = []
    if not root.is_dir():
        return items
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        rel = path.relative_to(root).as_posix()
        lang = "shared"
        if project_id == "response":
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


def _tex_mtime_summary() -> dict[str, float | None]:
    out: dict[str, float | None] = {"en": None, "zh": None, "manuscript": None}
    rroot = PROJECTS["response"]["root"]
    if rroot.is_dir():
        mtimes: list[float] = []
        sty = rroot / "reviewer_response.sty"
        if sty.exists():
            mtimes.append(sty.stat().st_mtime)
        for path in rroot.rglob("*.tex"):
            mtimes.append(path.stat().st_mtime)
        latest = max(mtimes) if mtimes else None
        out["en"] = out["zh"] = latest
    mroot = PROJECTS["manuscript"]["root"]
    if mroot.is_dir():
        mtimes = [p.stat().st_mtime for p in mroot.rglob("*") if p.is_file() and p.suffix in {".tex", ".bib"}]
        out["manuscript"] = max(mtimes) if mtimes else None
    return out


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(STATIC))

    @app.get("/")
    def index() -> Response:
        return send_from_directory(STATIC, "index.html")

    @app.get("/api/status")
    def status():
        tex_mtime = _tex_mtime_summary()
        ms = PROJECTS["manuscript"]
        ms_pdf = ms.get("pdf")
        pdf_mtime = {
            lang: cfg["pdf"].stat().st_mtime if cfg["pdf"].exists() else None
            for lang, cfg in LANG_CFG.items()
        }
        pdf_mtime["manuscript"] = (
            ms_pdf.stat().st_mtime if ms_pdf and ms_pdf.exists() else None
        )
        return jsonify(
            {
                "building": _state["building"],
                "ok": _state["ok"],
                "last_build": _state["last_build"],
                "needs_rebuild": needs_rebuild(),
                "ok_project": dict(_state["ok_project"]),
                "tex_mtime": tex_mtime,
                "pdf_mtime": pdf_mtime,
                "manuscript_available": MANUSCRIPT_DIR.is_dir(),
            }
        )

    @app.post("/api/build")
    def build():
        result = full_build("api")
        return jsonify(result)

    @app.get("/api/log")
    def log_tail():
        return Response(_state["log"][-50000:], mimetype="text/plain; charset=utf-8")

    def _file_json(project_id: str, rel: str, *, write: str | None = None):
        try:
            pid = _project_id(project_id)
            path = _safe_latex_path(rel, pid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        root = PROJECTS[pid]["root"]
        if write is None:
            if not path.exists():
                # Client still on response project but asked for a manuscript-only path
                if pid == "response":
                    try:
                        alt = _safe_latex_path(rel, "manuscript")
                        if alt.exists():
                            pid, path, root = "manuscript", alt, PROJECTS["manuscript"]["root"]
                    except ValueError:
                        pass
            if not path.exists():
                return (
                    jsonify(
                        {
                            "error": "not found",
                            "project": pid,
                            "path": rel,
                            "resolved": str(path),
                        }
                    ),
                    404,
                )
            return jsonify(
                {
                    "project": pid,
                    "path": path.relative_to(root).as_posix(),
                    "content": path.read_text(encoding="utf-8"),
                    "mtime": path.stat().st_mtime,
                }
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(write, encoding="utf-8")
        return jsonify({"ok": True, "project": pid, "path": path.relative_to(root).as_posix()})

    @app.get("/api/projects/<project_id>/files")
    def list_files_project(project_id: str):
        try:
            pid = _project_id(project_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        root = PROJECTS[pid]["root"]
        return jsonify(
            {
                "project": pid,
                "root": root.name,
                "files": _list_latex_files(pid),
            }
        )

    @app.get("/api/projects/<project_id>/file")
    def read_file_project(project_id: str):
        rel = request.args.get("path", "")
        return _file_json(project_id, rel)

    @app.put("/api/projects/<project_id>/file")
    def write_file_project(project_id: str):
        data = request.get_json(silent=True) or {}
        rel = data.get("path") or request.args.get("path", "")
        content = data.get("content")
        if content is None:
            return jsonify({"error": "missing content"}), 400
        return _file_json(project_id, rel, write=content)

    @app.get("/api/files")
    def list_files():
        return list_files_project(request.args.get("project") or DEFAULT_PROJECT)

    @app.get("/api/file")
    def read_file():
        return read_file_project(request.args.get("project") or DEFAULT_PROJECT)

    @app.put("/api/file")
    def write_file():
        data = request.get_json(silent=True) or {}
        rel = data.get("path") or request.args.get("path", "")
        content = data.get("content")
        if content is None:
            return jsonify({"error": "missing content"}), 400
        pid = data.get("project") or request.args.get("project") or DEFAULT_PROJECT
        return _file_json(pid, rel, write=content)

    @app.get("/pdf/<lang>")
    def pdf(lang: str):
        if lang == "manuscript":
            pdf_path = PROJECTS["manuscript"].get("pdf")
            if not pdf_path or not pdf_path.exists():
                return jsonify({"error": "pdf not found"}), 404
            return send_file(
                pdf_path,
                mimetype="application/pdf",
                as_attachment=False,
                download_name=pdf_path.name,
            )
        cfg = LANG_CFG.get(lang)
        if not cfg or not cfg["pdf"].exists():
            return jsonify({"error": "pdf not found"}), 404
        return send_file(
            cfg["pdf"],
            mimetype="application/pdf",
            as_attachment=False,
            download_name=cfg["pdf"].name,
        )

    @app.after_request
    def _no_cache_static(response):  # noqa: ANN001 — Flask hook signature
        if response.status_code == 200 and request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--poll", type=float, default=3.0, help="auto-rebuild poll seconds")
    parser.add_argument("--no-watch", action="store_true")
    parser.add_argument(
        "--no-manuscript",
        action="store_true",
        help="do not compile 26_Nature_ThyroidAgent in build/watch",
    )
    args = parser.parse_args()
    include_manuscript = not args.no_manuscript

    if not args.no_watch:
        t = threading.Thread(
            target=_watcher_loop,
            args=(args.poll, include_manuscript),
            daemon=True,
        )
        t.start()

    # Block until first build finishes so /api/status ok matches PDFs on first load.
    full_build("startup", include_manuscript=include_manuscript)

    app = create_app()
    ms = MANUSCRIPT_DIR / "main_v2.tex"
    print(f"Reviewer response viewer (TeX-only): http://{args.host}:{args.port}")
    print(f"  manuscript root: {MANUSCRIPT_DIR} ({'OK' if ms.is_file() else 'MISSING main_v2.tex'})")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
