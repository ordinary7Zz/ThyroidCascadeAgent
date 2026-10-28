(() => {
  const DEFAULT_FILES = {
    en: "generated/body_en.tex",
    zh: "generated/body_zh.tex",
  };

  let currentLang = "en";
  let currentPath = null;
  let editorDirty = false;
  let savedContent = "";
  let splitPdf = false;
  let lastPdfMtime = { en: null, zh: null };

  const editor = document.getElementById("editor");
  const pathLabel = document.getElementById("openPath");
  const fileTree = document.getElementById("fileTree");
  const statusEl = document.getElementById("status");
  const statusText = document.getElementById("statusText");
  const logEl = document.getElementById("log");
  const btnBuild = document.getElementById("btnBuild");
  const btnSave = document.getElementById("btnSave");
  const pdfEn = document.getElementById("pdfEn");
  const pdfZh = document.getElementById("pdfZh");
  const previewBody = document.getElementById("previewBody");
  const lineGutter = document.getElementById("lineGutter");
  const notesList = document.getElementById("notesList");
  const noteCountEl = document.getElementById("noteCount");
  const noteRoundBadge = document.getElementById("noteRoundBadge");
  const noteDialog = document.getElementById("noteDialog");
  const noteForm = document.getElementById("noteForm");
  const noteDialogMeta = document.getElementById("noteDialogMeta");
  const noteDialogQuote = document.getElementById("noteDialogQuote");
  const noteDialogText = document.getElementById("noteDialogText");
  const btnAddNote = document.getElementById("btnAddNote");
  const btnCloseRound = document.getElementById("btnCloseRound");
  const closeRoundDialog = document.getElementById("closeRoundDialog");
  const closeRoundForm = document.getElementById("closeRoundForm");
  const closeRoundFields = document.getElementById("closeRoundFields");
  const closeRoundPaste = document.getElementById("closeRoundPaste");

  let reviewNotes = {
    schema_version: 1,
    round_id: null,
    updated_at: null,
    comments: [],
  };
  let pendingCommentRange = null;
  let activeCommentId = null;
  let gutterLineCount = 0;
  let reviewNotesApiOk = true;

  /** 注释只打在英文稿；中文项目仅用于阅读对照。 */
  function commentsAllowedForCurrentFile() {
    if (currentLang !== "en") return false;
    if (!currentPath) return false;
    if (/body_zh|REVIEWER_RESPONSE_ZH/i.test(currentPath)) return false;
    return true;
  }

  function syncCommentUiState() {
    const allowed = reviewNotesApiOk && commentsAllowedForCurrentFile();
    btnAddNote.disabled = !allowed;
    btnAddNote.title = allowed
      ? "为选区添加注释 (Ctrl+Alt+M)"
      : currentLang !== "en"
        ? "中文模式仅阅读；请切到 English 对英文稿加注释"
        : "请先打开英文 TeX 文件";
    document.getElementById("editorPane").classList.toggle("comments-off", currentLang !== "en");
    const hasNotes = reviewNotes.comments.length > 0;
    btnCloseRound.disabled = !reviewNotesApiOk || !hasNotes;
  }

  function indexToLineCol(text, index) {
    const slice = text.slice(0, index);
    const parts = slice.split("\n");
    return { line: parts.length, ch: parts[parts.length - 1].length + 1 };
  }

  function lineColToIndex(text, line, ch) {
    const lines = text.split("\n");
    let index = 0;
    for (let i = 0; i < line - 1 && i < lines.length; i++) {
      index += lines[i].length + 1;
    }
    if (line - 1 < lines.length) {
      index += Math.min(lines[line - 1].length, Math.max(0, ch - 1));
    }
    return index;
  }

  function captureSelectionRange() {
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    if (start === end) return null;
    const text = editor.value;
    return {
      start: indexToLineCol(text, start),
      end: indexToLineCol(text, end),
      selected_text: text.slice(start, end),
    };
  }

  function commentedLinesForPath(path) {
    const set = new Set();
    for (const c of reviewNotes.comments) {
      if (c.path !== path) continue;
      const a = c.range.start.line;
      const b = c.range.end.line;
      for (let ln = a; ln <= b; ln++) set.add(ln);
    }
    return set;
  }

  function updateLineGutter() {
    const text = editor.value;
    const lines = text.split("\n");
    const count = Math.max(1, lines.length);
    const noted = currentPath ? commentedLinesForPath(currentPath) : new Set();
    let activeLines = new Set();
    if (activeCommentId && currentPath) {
      const ac = reviewNotes.comments.find((x) => x.id === activeCommentId);
      if (ac && ac.path === currentPath) {
        for (let ln = ac.range.start.line; ln <= ac.range.end.line; ln++) {
          activeLines.add(ln);
        }
      }
    }
    let inner = lineGutter.querySelector(".line-gutter-inner");
    if (!inner) {
      inner = document.createElement("div");
      inner.className = "line-gutter-inner";
      lineGutter.appendChild(inner);
    }
    if (count !== gutterLineCount) {
      gutterLineCount = count;
      inner.innerHTML = "";
      for (let i = 1; i <= count; i++) {
        const span = document.createElement("span");
        span.className = "ln";
        span.dataset.line = String(i);
        span.textContent = String(i);
        inner.appendChild(span);
      }
    }
    inner.querySelectorAll(".ln").forEach((el) => {
      const ln = Number(el.dataset.line);
      el.classList.toggle("has-note", noted.has(ln));
      el.classList.toggle("active", activeLines.has(ln));
    });
  }

  function syncGutterScroll() {
    const inner = lineGutter.querySelector(".line-gutter-inner");
    if (inner) inner.style.transform = `translateY(${-editor.scrollTop}px)`;
  }

  function formatRoundLabel(roundId) {
    if (!roundId) return "轮次 —";
    try {
      const d = new Date(roundId);
      if (!Number.isNaN(d.getTime())) {
        return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
      }
    } catch {
      /* ignore */
    }
    return String(roundId).slice(0, 16);
  }

  function renderNotesList() {
    const items = reviewNotes.comments;
    noteCountEl.textContent = String(items.length);
    noteRoundBadge.textContent = formatRoundLabel(reviewNotes.round_id);
    noteRoundBadge.title = reviewNotes.round_id
      ? `round_id: ${reviewNotes.round_id}`
      : "尚未开始本轮（添加首条注释时自动生成）";

    notesList.innerHTML = "";
    if (!items.length) {
      notesList.innerHTML = '<p class="notes-empty">选中文本后点「添加注释」或 Ctrl+Alt+M</p>';
      return;
    }
    for (const c of items) {
      const card = document.createElement("div");
      card.className = "note-card";
      if (c.path !== currentPath) card.classList.add("other-file");
      if (c.id === activeCommentId) card.classList.add("active");
      const loc = `L${c.range.start.line}${c.range.start.line !== c.range.end.line ? "–" + c.range.end.line : ""}`;
      card.innerHTML = `
        <div class="note-card-head">
          <span>${c.path} · ${loc}</span>
          <button type="button" class="note-del" title="删除">×</button>
        </div>
        <p class="note-body"></p>
        <div class="note-snippet"></div>`;
      card.querySelector(".note-body").textContent = c.note;
      card.querySelector(".note-snippet").textContent = c.selected_text.replace(/\s+/g, " ").slice(0, 120);
      card.querySelector(".note-del").addEventListener("click", (ev) => {
        ev.stopPropagation();
        deleteComment(c.id);
      });
      card.addEventListener("click", () => focusComment(c));
      notesList.appendChild(card);
    }
  }

  async function loadReviewNotes() {
    const r = await fetch("/api/review-notes/current");
    if (!r.ok) return;
    const data = await r.json();
    if (data && Array.isArray(data.comments)) {
      reviewNotes = {
        schema_version: 1,
        round_id: data.round_id ?? null,
        updated_at: data.updated_at ?? null,
        comments: data.comments,
      };
    }
    renderNotesList();
    updateLineGutter();
  }

  async function saveReviewNotes() {
    reviewNotes.schema_version = 1;
    reviewNotes.updated_at = new Date().toISOString();
    const r = await fetch("/api/review-notes/current", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reviewNotes),
    });
    if (!r.ok) {
      let detail = String(r.status);
      try {
        const t = await r.text();
        if (t) detail += ` — ${t.replace(/\s+/g, " ").slice(0, 160)}`;
      } catch {
        /* ignore */
      }
      const hint =
        r.status === 404
          ? "\n\n当前运行的 latex-viewer 可能是旧进程（没有注释 API）。请在 latex-viewer 目录重新执行 python3 app.py 后硬刷新页面。"
          : "";
      alert(`注释保存失败（${detail}）${hint}`);
      return false;
    }
    renderNotesList();
    updateLineGutter();
    return true;
  }

  async function ensureReviewNotesApi() {
    try {
      const r = await fetch("/api/review-notes/current");
      if (r.ok) {
        reviewNotesApiOk = true;
        syncCommentUiState();
        return true;
      }
      if (r.status === 404) {
        reviewNotesApiOk = false;
        statusText.textContent = "注释 API 不可用 — 请重启 python3 app.py";
        statusEl.className = "status err";
        syncCommentUiState();
      }
    } catch {
      /* poll will show connection error */
    }
    return false;
  }

  function focusComment(c) {
    activeCommentId = c.id;
    if (c.path !== currentPath) {
      openFile(c.path, true).then(() => {
        jumpToCommentRange(c);
        renderNotesList();
        updateLineGutter();
      });
      return;
    }
    jumpToCommentRange(c);
    renderNotesList();
    updateLineGutter();
  }

  function jumpToCommentRange(c) {
    const text = editor.value;
    const from = lineColToIndex(text, c.range.start.line, c.range.start.ch);
    const to = lineColToIndex(text, c.range.end.line, c.range.end.ch);
    editor.focus();
    editor.setSelectionRange(from, to);
    const lineHeight = parseFloat(getComputedStyle(editor).lineHeight) || 18;
    const linesBefore = c.range.start.line - 1;
    editor.scrollTop = Math.max(0, linesBefore * lineHeight - editor.clientHeight * 0.3);
    syncGutterScroll();
  }

  async function deleteComment(id) {
    if (!confirm("删除这条注释？")) return;
    reviewNotes.comments = reviewNotes.comments.filter((x) => x.id !== id);
    if (activeCommentId === id) activeCommentId = null;
    if (!reviewNotes.comments.length) reviewNotes.round_id = null;
    await saveReviewNotes();
  }

  function openNoteDialog() {
    if (!commentsAllowedForCurrentFile()) {
      if (currentLang !== "en") return;
      alert("请切换到 English 项目并打开英文 TeX 后再添加注释。");
      return;
    }
    if (!currentPath) {
      alert("请先打开一个 TeX 文件");
      return;
    }
    pendingCommentRange = captureSelectionRange();
    if (!pendingCommentRange) {
      alert("请先选中要注释的文本");
      return;
    }
    const loc = `L${pendingCommentRange.start.line}:${pendingCommentRange.start.ch}–${pendingCommentRange.end.line}:${pendingCommentRange.end.ch}`;
    noteDialogMeta.textContent = `${currentPath} · ${loc}`;
    noteDialogQuote.textContent = pendingCommentRange.selected_text;
    noteDialogText.value = "";
    noteDialog.showModal();
    noteDialogText.focus();
  }

  async function submitNoteDialog() {
    if (!pendingCommentRange || !currentPath) return;
    const note = noteDialogText.value.trim();
    if (!note) return;
    if (!reviewNotes.round_id) {
      reviewNotes.round_id = new Date().toISOString();
    }
    const entry = {
      id: `c${Date.now()}`,
      path: currentPath,
      range: {
        start: { ...pendingCommentRange.start },
        end: { ...pendingCommentRange.end },
      },
      selected_text: pendingCommentRange.selected_text,
      note,
      created_at: new Date().toISOString(),
    };
    reviewNotes.comments.push(entry);
    activeCommentId = entry.id;
    if (!(await saveReviewNotes())) {
      reviewNotes.comments.pop();
      activeCommentId = null;
      return;
    }
    pendingCommentRange = null;
    noteDialog.close();
  }

  function buildCloseRoundForm() {
    closeRoundFields.innerHTML = "";
    closeRoundPaste.value = "";
    for (const c of reviewNotes.comments) {
      const row = document.createElement("div");
      row.className = "close-round-row";
      row.dataset.commentId = c.id;
      const loc = `L${c.range.start.line}`;
      row.innerHTML = `
        <div class="close-round-row-head"><code>${c.id}</code> · ${c.path} · ${loc}</div>
        <div class="close-round-note">${escapeHtml(c.note)}</div>
        <label>状态
          <select class="close-action">
            <option value="applied" selected>已修改 (applied)</option>
            <option value="partial">部分修改 (partial)</option>
            <option value="skipped">跳过 (skipped)</option>
          </select>
        </label>
        <label>改动说明
          <textarea class="close-summary" rows="2" placeholder="粘贴 AI 给出的 summary…"></textarea>
        </label>`;
      closeRoundFields.appendChild(row);
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function collectCloseEntriesFromForm() {
    const entries = [];
    for (const c of reviewNotes.comments) {
      const row = closeRoundFields.querySelector(`[data-comment-id="${CSS.escape(c.id)}"]`);
      if (!row) continue;
      entries.push({
        comment_id: c.id,
        path: c.path,
        note: c.note,
        action: row.querySelector(".close-action").value,
        summary: row.querySelector(".close-summary").value.trim(),
      });
    }
    return entries;
  }

  function openCloseRoundDialog() {
    if (!reviewNotes.comments.length) return;
    buildCloseRoundForm();
    closeRoundDialog.showModal();
  }

  async function submitCloseRound(ev) {
    ev.preventDefault();
    let entries;
    const pasted = closeRoundPaste.value.trim();
    if (pasted) {
      try {
        const data = JSON.parse(pasted);
        entries = data.entries;
        if (!Array.isArray(entries)) throw new Error("missing entries array");
      } catch (e) {
        alert(`JSON 无效：${e.message || e}`);
        return;
      }
    } else {
      entries = collectCloseEntriesFromForm();
    }
    const r = await fetch("/api/review-notes/close", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries }),
    });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) {
      alert(`收尾失败：${body.error || r.status}`);
      return;
    }
    closeRoundDialog.close();
    activeCommentId = null;
    await loadReviewNotes();
    syncCommentUiState();
    alert(`已写入 history（round ${body.round_id || "—"}），current 已清空。`);
  }

  /** PDF open params: hide thumbnail/nav pane so preview uses full iframe width. */
  function pdfUrl(lang) {
    const q = `/pdf/${lang}?t=${Date.now()}`;
    return `${q}#navpanes=0&pagemode=none&view=FitH`;
  }

  const pdfEnCell = document.getElementById("pdfEnCell");
  const pdfZhCell = document.getElementById("pdfZhCell");

  function refreshPdf() {
    pdfEn.src = pdfUrl("en");
    pdfZh.src = pdfUrl("zh");
    if (splitPdf) {
      pdfEnCell.style.display = "flex";
      pdfZhCell.style.display = "flex";
    } else {
      pdfEnCell.style.display = currentLang === "en" ? "flex" : "none";
      pdfZhCell.style.display = currentLang === "zh" ? "flex" : "none";
    }
  }

  function setProjectLang(lang) {
    currentLang = lang;
    document.querySelectorAll("[data-project-lang]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.projectLang === lang);
    });
    document.querySelectorAll("[data-pdf-lang]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.pdfLang === lang);
    });
    refreshPdf();
    openFile(DEFAULT_FILES[lang], false);
    syncCommentUiState();
  }

  async function loadFileList() {
    const r = await fetch("/api/files");
    const data = await r.json();
    renderTree(data.files || []);
  }

  function renderTree(files) {
    const sections = {
      en: { title: "English", items: [] },
      zh: { title: "中文", items: [] },
      shared: { title: "共用样式", items: [] },
    };
    for (const f of files) {
      const key = sections[f.lang] ? f.lang : "shared";
      sections[key].items.push(f);
    }
    fileTree.innerHTML = "";
    for (const key of ["en", "zh", "shared"]) {
      const sec = sections[key];
      if (!sec.items.length) continue;
      const wrap = document.createElement("div");
      wrap.className = "file-section";
      wrap.innerHTML = `<div class="file-section-title">${sec.title}</div>`;
      for (const f of sec.items) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "file-item";
        btn.dataset.path = f.path;
        btn.textContent = f.path;
        if (f.path === currentPath) btn.classList.add("active");
        if (f.path === currentPath && editorDirty) btn.classList.add("dirty");
        btn.addEventListener("click", () => openFile(f.path, true));
        wrap.appendChild(btn);
      }
      fileTree.appendChild(wrap);
    }
  }

  async function openFile(path, confirmDiscard) {
    if (confirmDiscard && editorDirty) {
      if (!confirm("当前文件未保存，是否放弃修改？")) return;
    }
    const r = await fetch(`/api/file?path=${encodeURIComponent(path)}`);
    if (!r.ok) {
      alert("无法打开文件");
      return;
    }
    const data = await r.json();
    currentPath = data.path;
    savedContent = data.content;
    editor.value = data.content;
    editorDirty = false;
    pathLabel.textContent = data.path;
    btnSave.disabled = true;
    document.querySelectorAll(".file-item").forEach((el) => {
      el.classList.toggle("active", el.dataset.path === currentPath);
      el.classList.remove("dirty");
    });
    updateLineGutter();
    syncGutterScroll();
    syncCommentUiState();
  }

  editor.addEventListener("input", () => {
    editorDirty = editor.value !== savedContent;
    btnSave.disabled = !editorDirty;
    document.querySelectorAll(`.file-item[data-path="${CSS.escape(currentPath || "")}"]`).forEach((el) => {
      el.classList.toggle("dirty", editorDirty);
    });
    updateLineGutter();
  });

  editor.addEventListener("scroll", syncGutterScroll);

  editor.addEventListener("keydown", (e) => {
    if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      saveFile();
    }
    if (e.key === "m" && e.ctrlKey && e.altKey) {
      e.preventDefault();
      openNoteDialog();
    }
    if (e.key === "Tab") {
      e.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      editor.value = editor.value.slice(0, start) + "  " + editor.value.slice(end);
      editor.selectionStart = editor.selectionEnd = start + 2;
      updateLineGutter();
    }
  });

  btnAddNote.addEventListener("click", openNoteDialog);
  noteForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitNoteDialog();
  });
  document.getElementById("noteDialogCancel").addEventListener("click", () => {
    pendingCommentRange = null;
    noteDialog.close();
  });
  btnCloseRound.addEventListener("click", openCloseRoundDialog);
  closeRoundForm.addEventListener("submit", submitCloseRound);
  document.getElementById("closeRoundCancel").addEventListener("click", () => closeRoundDialog.close());

  async function saveFile() {
    if (!currentPath || !editorDirty) return;
    btnSave.disabled = true;
    const r = await fetch("/api/file", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: currentPath, content: editor.value }),
    });
    if (!r.ok) {
      alert("保存失败");
      btnSave.disabled = false;
      return;
    }
    savedContent = editor.value;
    editorDirty = false;
    await loadFileList();
  }

  async function fetchStatus() {
    const r = await fetch("/api/status");
    return r.json();
  }

  async function fetchLog() {
    const r = await fetch("/api/log");
    logEl.textContent = await r.text();
    logEl.scrollTop = logEl.scrollHeight;
  }

  function setStatus(s) {
    statusEl.className = "status " + (s.building ? "busy" : s.ok ? "ok" : "err");
    if (s.building) statusText.textContent = "编译中…";
    else if (!s.ok) statusText.textContent = "编译失败 — 见下方日志";
    else if (s.needs_rebuild) statusText.textContent = "TeX 已变更，等待自动编译…";
    else {
      const t = s.last_build ? new Date(s.last_build * 1000).toLocaleString() : "—";
      statusText.textContent = "就绪 · " + t;
    }
    btnBuild.disabled = s.building;
  }

  async function poll() {
    try {
      const s = await fetchStatus();
      setStatus(s);
      if (!s.building) {
        for (const lang of ["en", "zh"]) {
          const mt = s.pdf_mtime[lang];
          if (mt && mt !== lastPdfMtime[lang]) {
            lastPdfMtime[lang] = mt;
            refreshPdf();
          }
        }
      }
      await fetchLog();
    } catch {
      statusText.textContent = "无法连接服务";
    }
  }

  btnBuild.addEventListener("click", async () => {
    if (editorDirty) await saveFile();
    btnBuild.disabled = true;
    await fetch("/api/build", { method: "POST" });
    await poll();
  });

  btnSave.addEventListener("click", saveFile);

  document.querySelectorAll("[data-project-lang]").forEach((btn) => {
    btn.addEventListener("click", () => setProjectLang(btn.dataset.projectLang));
  });

  document.querySelectorAll("[data-pdf-lang]").forEach((btn) => {
    btn.addEventListener("click", () => {
      currentLang = btn.dataset.pdfLang;
      document.querySelectorAll("[data-pdf-lang]").forEach((b) => {
        b.classList.toggle("active", b.dataset.pdfLang === currentLang);
      });
      refreshPdf();
    });
  });

  document.getElementById("btnSplitPdf").addEventListener("click", () => {
    splitPdf = !splitPdf;
    previewBody.classList.toggle("split", splitPdf);
    document.getElementById("btnSplitPdf").classList.toggle("active", splitPdf);
    refreshPdf();
  });

  document.getElementById("logToggle").addEventListener("click", () => {
    document.getElementById("logDrawer").classList.toggle("collapsed");
  });

  const LAYOUT_KEY = "reviewer-workspace-layout-v1";
  const root = document.documentElement;
  const workspaceEl = document.getElementById("workspace");
  const editorPane = document.getElementById("editorPane");

  function parsePx(varName, fallback) {
    const raw = getComputedStyle(root).getPropertyValue(varName).trim();
    const n = parseFloat(raw);
    if (Number.isFinite(n)) return n;
    return fallback;
  }

  function setLayout(sidebarW, previewW, logH) {
    root.style.setProperty("--sidebar-w", `${Math.round(sidebarW)}px`);
    root.style.setProperty("--preview-w", `${Math.round(previewW)}px`);
    root.style.setProperty("--log-h", `${Math.round(logH)}px`);
  }

  function previewClampRange(sidebarW, workspaceWidth) {
    const ws = workspaceWidth ?? workspaceEl.getBoundingClientRect().width;
    const side = sidebarW ?? parsePx("--sidebar-w", 240);
    const minEditor = 180;
    const minPreview = 260;
    const maxPreview = Math.max(minPreview, ws - side - minEditor - 20);
    return { minPreview, maxPreview };
  }

  function clampPreview(w, sidebarW, workspaceWidth) {
    const { minPreview, maxPreview } = previewClampRange(sidebarW, workspaceWidth);
    return Math.min(maxPreview, Math.max(minPreview, w));
  }

  function loadLayout() {
    try {
      const saved = JSON.parse(localStorage.getItem(LAYOUT_KEY) || "null");
      if (saved && typeof saved === "object") {
        setLayout(
          saved.sidebarW ?? 240,
          clampPreview(saved.previewW ?? workspaceEl.clientWidth * 0.5),
          saved.logH ?? 140
        );
        return;
      }
    } catch {
      /* ignore */
    }
    const ws = workspaceEl.getBoundingClientRect().width;
    setLayout(240, clampPreview(ws * 0.52), 140);
  }

  function saveLayout() {
    localStorage.setItem(
      LAYOUT_KEY,
      JSON.stringify({
        sidebarW: parsePx("--sidebar-w", 240),
        previewW: parsePx("--preview-w", 400),
        logH: parsePx("--log-h", 140),
      })
    );
  }

  function dragColumn(handle, onDelta, options = {}) {
    const { suspendPdf = false } = options;
    handle.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      handle.classList.add("dragging");
      document.body.classList.add("is-resizing");
      if (suspendPdf) document.body.classList.add("is-resizing-pdf");
      const startX = e.clientX;
      const startSidebar = parsePx("--sidebar-w", 240);
      const startPreview = parsePx("--preview-w", 400);
      const startLog = parsePx("--log-h", 140);
      const workspaceWidth = workspaceEl.getBoundingClientRect().width;
      let rafId = 0;
      let pendingDx = 0;

      function applyDelta() {
        rafId = 0;
        onDelta(pendingDx, {
          startSidebar,
          startPreview,
          startLog,
          workspaceWidth,
        });
      }

      function onMove(ev) {
        pendingDx = ev.clientX - startX;
        if (!rafId) rafId = requestAnimationFrame(applyDelta);
      }
      function onUp() {
        if (rafId) {
          cancelAnimationFrame(rafId);
          applyDelta();
        }
        handle.classList.remove("dragging");
        document.body.classList.remove("is-resizing");
        document.body.classList.remove("is-resizing-pdf");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        saveLayout();
      }
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  }

  dragColumn(
    document.getElementById("resizeSidebar"),
    (dx, s) => {
      const next = Math.min(420, Math.max(140, s.startSidebar + dx));
      setLayout(next, s.startPreview, s.startLog);
    }
  );

  dragColumn(
    document.getElementById("resizePreview"),
    (dx, s) => {
      const next = clampPreview(s.startPreview - dx, s.startSidebar, s.workspaceWidth);
      root.style.setProperty("--preview-w", `${Math.round(next)}px`);
    },
    { suspendPdf: true }
  );

  const logResize = document.getElementById("resizeLog");
  logResize.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    logResize.classList.add("dragging");
    document.body.classList.add("is-resizing-row");
    const startY = e.clientY;
    const startH = parsePx("--log-h", 140);

    function onMove(ev) {
      const next = startH - (ev.clientY - startY);
      const maxH = Math.min(window.innerHeight * 0.7, 600);
      root.style.setProperty("--log-h", `${Math.min(maxH, Math.max(80, next))}px`);
      document.getElementById("logDrawer").classList.remove("collapsed");
    }
    function onUp() {
      logResize.classList.remove("dragging");
      document.body.classList.remove("is-resizing-row");
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      saveLayout();
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  });

  window.addEventListener("resize", () => {
    const pw = parsePx("--preview-w", 400);
    setLayout(parsePx("--sidebar-w", 240), clampPreview(pw), parsePx("--log-h", 140));
  });

  loadLayout();

  loadReviewNotes();
  ensureReviewNotesApi();
  loadFileList().then(() => setProjectLang("en"));
  refreshPdf();
  setInterval(poll, 1500);
  poll();
})();
