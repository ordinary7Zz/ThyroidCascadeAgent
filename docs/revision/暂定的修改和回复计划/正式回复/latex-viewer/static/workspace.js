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

  function pdfUrl(lang) {
    return `/pdf/${lang}?t=${Date.now()}`;
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
  }

  editor.addEventListener("input", () => {
    editorDirty = editor.value !== savedContent;
    btnSave.disabled = !editorDirty;
    document.querySelectorAll(`.file-item[data-path="${CSS.escape(currentPath || "")}"]`).forEach((el) => {
      el.classList.toggle("dirty", editorDirty);
    });
  });

  editor.addEventListener("keydown", (e) => {
    if (e.key === "s" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      saveFile();
    }
    if (e.key === "Tab") {
      e.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      editor.value = editor.value.slice(0, start) + "  " + editor.value.slice(end);
      editor.selectionStart = editor.selectionEnd = start + 2;
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

  function clampPreview(w) {
    const ws = workspaceEl.getBoundingClientRect().width;
    const side = parsePx("--sidebar-w", 240);
    const minEditor = 180;
    const minPreview = 260;
    const maxPreview = Math.max(minPreview, ws - side - minEditor - 20);
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

  function dragColumn(handle, onDelta) {
    handle.addEventListener("mousedown", (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      handle.classList.add("dragging");
      document.body.classList.add("is-resizing");
      const startX = e.clientX;
      const startSidebar = parsePx("--sidebar-w", 240);
      const startPreview = parsePx("--preview-w", 400);
      const startLog = parsePx("--log-h", 140);

      function onMove(ev) {
        const dx = ev.clientX - startX;
        onDelta(dx, { startSidebar, startPreview, startLog });
      }
      function onUp() {
        handle.classList.remove("dragging");
        document.body.classList.remove("is-resizing");
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

  dragColumn(document.getElementById("resizePreview"), (dx, s) => {
    const next = clampPreview(s.startPreview - dx);
    setLayout(s.startSidebar, next, s.startLog);
  });

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

  loadFileList().then(() => setProjectLang("en"));
  refreshPdf();
  setInterval(poll, 1500);
  poll();
})();
