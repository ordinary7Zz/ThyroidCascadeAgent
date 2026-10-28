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
  let pendingLogText = null;
  let findActiveIndex = -1;

  const editor = document.getElementById("editor");
  const editorGutter = document.getElementById("editorGutter");
  const editorHighlight = document.getElementById("editorHighlight");
  const editorScroller = document.getElementById("editorScroller");
  const lineMeasurer = document.getElementById("lineMeasurer");
  const editorPane = document.getElementById("editorPane");
  const editorFind = document.getElementById("editorFind");
  const findInput = document.getElementById("findInput");
  const findStatus = document.getElementById("findStatus");
  const findPrev = document.getElementById("findPrev");
  const findNext = document.getElementById("findNext");
  const findClose = document.getElementById("findClose");
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

  function syncEditorScroll() {
    editorGutter.scrollTop = editorScroller.scrollTop;
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function buildFindHighlightHtml(text, query, activeIndex) {
    const hay = text.toLowerCase();
    const needle = query.toLowerCase();
    if (!needle) return escapeHtml(text);
    let html = "";
    let from = 0;
    while (from <= hay.length) {
      const idx = hay.indexOf(needle, from);
      if (idx === -1) break;
      html += escapeHtml(text.slice(from, idx));
      const slice = text.slice(idx, idx + needle.length);
      const cls = idx === activeIndex ? "find-hit current" : "find-hit";
      html += `<mark class="${cls}">${escapeHtml(slice)}</mark>`;
      from = idx + needle.length;
    }
    html += escapeHtml(text.slice(from));
    return html;
  }

  function refreshEditorHighlight() {
    const text = editor.value;
    const findOpen = !editorFind.classList.contains("hidden");
    const query = findOpen ? findInput.value : "";
    if (findOpen && query) {
      editorHighlight.innerHTML = buildFindHighlightHtml(text, query, findActiveIndex);
    } else {
      editorHighlight.textContent = text;
    }
  }

  function editorContentWidth() {
    const style = getComputedStyle(editor);
    const pad = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
    return Math.max(40, editor.clientWidth - pad);
  }

  function measureWrappedLineHeights(lines) {
    lineMeasurer.style.width = `${editorContentWidth()}px`;
    return lines.map((line) => {
      lineMeasurer.textContent = line.length ? line : " ";
      return lineMeasurer.offsetHeight;
    });
  }

  function updateLineNumbers() {
    const lines = editor.value.split("\n");
    const lineCount = Math.max(1, lines.length);
    const digits = String(lineCount).length;
    editorGutter.style.minWidth = `${Math.max(2.75, 0.55 * 2 + digits * 0.62)}rem`;
    const heights = measureWrappedLineHeights(lines.length ? lines : [""]);
    editorGutter.replaceChildren();
    for (let i = 0; i < lineCount; i += 1) {
      const row = document.createElement("div");
      row.className = "gutter-row";
      row.textContent = String(i + 1);
      row.style.height = `${heights[i] ?? heights[0]}px`;
      editorGutter.appendChild(row);
    }
    syncEditorScroll();
  }

  function refreshEditorSurface() {
    updateLineNumbers();
    refreshEditorHighlight();
  }

  function findHaystack() {
    const query = findInput.value;
    if (!query) return null;
    const text = editor.value;
    return {
      query,
      text,
      hay: text.toLowerCase(),
      needle: query.toLowerCase(),
    };
  }

  function countFindMatches() {
    const ctx = findHaystack();
    if (!ctx) return 0;
    let count = 0;
    let from = 0;
    while (from <= ctx.hay.length) {
      const idx = ctx.hay.indexOf(ctx.needle, from);
      if (idx === -1) break;
      count += 1;
      from = idx + ctx.needle.length || idx + 1;
    }
    return count;
  }

  function scrollEditorToIndex(index) {
    const lineIndex = editor.value.slice(0, index).split("\n").length - 1;
    const lines = editor.value.split("\n");
    const heights = measureWrappedLineHeights(lines);
    const padTop = parseFloat(getComputedStyle(editor).paddingTop) || 0;
    let top = padTop;
    for (let i = 0; i < lineIndex; i += 1) top += heights[i] ?? 0;
    const target = top - editorScroller.clientHeight / 3;
    editorScroller.scrollTop = Math.max(0, target);
    syncEditorScroll();
  }

  function selectFindMatch(index, length) {
    findActiveIndex = index;
    editor.setSelectionRange(index, index + length);
    scrollEditorToIndex(index);
    refreshEditorHighlight();
    updateFindStatus(index);
    if (!editorFind.classList.contains("hidden")) {
      findInput.focus();
    }
  }

  /** 输入关键字时：从文首找第一处，不抢焦点 */
  function findFirstMatch() {
    const ctx = findHaystack();
    if (!ctx || !ctx.needle.length) {
      findActiveIndex = -1;
      refreshEditorHighlight();
      updateFindStatus();
      return;
    }
    const idx = ctx.hay.indexOf(ctx.needle, 0);
    if (idx === -1) {
      findActiveIndex = -1;
      refreshEditorHighlight();
      updateFindStatus();
      findStatus.textContent = "无结果";
      findStatus.classList.add("err");
      return;
    }
    selectFindMatch(idx, ctx.query.length);
  }

  function updateFindStatus(activeIndex) {
    const ctx = findHaystack();
    if (!ctx) {
      findStatus.textContent = "";
      findStatus.classList.remove("err");
      return;
    }
    const total = countFindMatches();
    if (total === 0) {
      findStatus.textContent = "无结果";
      findStatus.classList.add("err");
      return;
    }
    findStatus.classList.remove("err");
    if (typeof activeIndex !== "number") {
      findStatus.textContent = `${total} 处`;
      return;
    }
    let nth = 0;
    let from = 0;
    while (from <= ctx.hay.length) {
      const idx = ctx.hay.indexOf(ctx.needle, from);
      if (idx === -1) break;
      nth += 1;
      if (idx === activeIndex) {
        findStatus.textContent = `${nth}/${total}`;
        return;
      }
      from = idx + ctx.needle.length || idx + 1;
    }
    findStatus.textContent = `${total} 处`;
  }

  function findInEditor(direction) {
    const ctx = findHaystack();
    if (!ctx) {
      updateFindStatus();
      return false;
    }
    const { hay, needle, query } = ctx;
    const len = needle.length;
    if (!len) {
      updateFindStatus();
      return false;
    }

    if (direction === "next") {
      const from = editor.selectionEnd;
      let idx = hay.indexOf(needle, from);
      if (idx === -1) idx = hay.indexOf(needle, 0);
      if (idx === -1) {
        updateFindStatus();
        findStatus.textContent = "无结果";
        findStatus.classList.add("err");
        return false;
      }
      selectFindMatch(idx, query.length);
      return true;
    }

    let from = editor.selectionStart - 1;
    if (from < 0) from = hay.length;
    let idx = hay.lastIndexOf(needle, from);
    if (idx === -1) idx = hay.lastIndexOf(needle);
    if (idx === -1) {
      updateFindStatus();
      findStatus.textContent = "无结果";
      findStatus.classList.add("err");
      return false;
    }
    selectFindMatch(idx, query.length);
    return true;
  }

  function seedFindQuery() {
    if (editor.selectionStart !== editor.selectionEnd) {
      findInput.value = editor.value.slice(editor.selectionStart, editor.selectionEnd);
      return;
    }
    const pos = editor.selectionStart;
    const text = editor.value;
    const before = text.slice(0, pos);
    const after = text.slice(pos);
    const left = before.match(/[\w\\{}_-]+$/)?.[0] || "";
    const right = after.match(/^[\w\\{}_-]+/)?.[0] || "";
    const word = left + right;
    if (word.length >= 2) findInput.value = word;
  }

  function openFindBar() {
    editorFind.classList.remove("hidden");
    seedFindQuery();
    findInput.focus();
    findInput.select();
    if (findInput.value) findFirstMatch();
    else {
      updateFindStatus();
      refreshEditorHighlight();
    }
  }

  function closeFindBar() {
    editorFind.classList.add("hidden");
    findStatus.textContent = "";
    findStatus.classList.remove("err");
    findActiveIndex = -1;
    refreshEditorHighlight();
    editor.focus();
  }

  findNext.addEventListener("click", () => findInEditor("next"));
  findPrev.addEventListener("click", () => findInEditor("prev"));
  findClose.addEventListener("click", closeFindBar);

  findInput.addEventListener("input", () => {
    if (!findInput.value) {
      findActiveIndex = -1;
      refreshEditorHighlight();
      updateFindStatus();
      return;
    }
    findFirstMatch();
  });

  findInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      findInEditor(e.shiftKey ? "prev" : "next");
    } else if (e.key === "Escape") {
      e.preventDefault();
      closeFindBar();
    }
  });

  document.addEventListener("keydown", (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key === "f") {
      if (!editorPane.contains(document.activeElement) && document.activeElement !== findInput) return;
      e.preventDefault();
      if (editorFind.classList.contains("hidden")) openFindBar();
      else {
        findInput.focus();
        findInput.select();
      }
    }
    if (e.key === "F3") {
      if (editorFind.classList.contains("hidden")) return;
      e.preventDefault();
      findInEditor(e.shiftKey ? "prev" : "next");
    }
  });

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
    refreshEditorSurface();
  }

  editorScroller.addEventListener("scroll", syncEditorScroll);

  editor.addEventListener("input", () => {
    editorDirty = editor.value !== savedContent;
    btnSave.disabled = !editorDirty;
    document.querySelectorAll(`.file-item[data-path="${CSS.escape(currentPath || "")}"]`).forEach((el) => {
      el.classList.toggle("dirty", editorDirty);
    });
    refreshEditorSurface();
  });

  editor.addEventListener("keydown", (e) => {
    if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      saveFile();
      return;
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "f") {
      e.preventDefault();
      openFindBar();
      return;
    }
    if (e.key === "Tab") {
      e.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      editor.value = editor.value.slice(0, start) + "  " + editor.value.slice(end);
      editor.selectionStart = editor.selectionEnd = start + 2;
      refreshEditorSurface();
    }
  });

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

  function logHasUserSelection() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return false;
    const node = sel.anchorNode;
    return node && logEl.contains(node);
  }

  function applyLogText(text) {
    const stickBottom =
      logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 24;
    logEl.textContent = text;
    if (stickBottom) logEl.scrollTop = logEl.scrollHeight;
  }

  function flushPendingLog() {
    if (pendingLogText == null || logHasUserSelection()) return;
    const text = pendingLogText;
    pendingLogText = null;
    if (text !== logEl.textContent) applyLogText(text);
  }

  async function fetchLog() {
    const r = await fetch("/api/log");
    const text = await r.text();
    if (text === logEl.textContent) {
      pendingLogText = null;
      return;
    }
    if (logHasUserSelection()) {
      pendingLogText = text;
      return;
    }
    pendingLogText = null;
    applyLogText(text);
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

  dragColumn(document.getElementById("resizeSidebar"), (dx, s) => {
    const next = Math.min(420, Math.max(140, s.startSidebar + dx));
    setLayout(next, s.startPreview, s.startLog);
  });

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
    refreshEditorSurface();
  });

  if (typeof ResizeObserver !== "undefined") {
    const editorLayoutObserver = new ResizeObserver(() => refreshEditorSurface());
    editorLayoutObserver.observe(editor);
  }

  refreshEditorSurface();

  loadLayout();
  loadFileList().then(() => setProjectLang("en"));
  refreshPdf();
  document.addEventListener("selectionchange", flushPendingLog);

  setInterval(poll, 1500);
  poll();
})();
