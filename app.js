const ELEMENT_COLORS = {
  C: "#3a3834",
  H: "#d9d2c5",
  O: "#c9434b",
  N: "#2f6fb0",
  S: "#c99b21",
  P: "#d27a23",
  F: "#54a46f",
  Cl: "#4f9f63",
  Br: "#9b5d39",
  I: "#6d4a88",
  X: "#7a746a",
};

const VIEWER_PRESETS = {
  ballstick: {
    name: "Ball-stick",
    atomScale: 1,
    bondScale: 1,
    bondAlpha: 0.78,
    ringAlpha: 0.13,
    label: true,
  },
  spacefill: {
    name: "Space-fill",
    atomScale: 1.72,
    bondScale: 0.44,
    bondAlpha: 0.42,
    ringAlpha: 0.07,
    label: false,
  },
  wire: {
    name: "Wire",
    atomScale: 0.34,
    bondScale: 0.56,
    bondAlpha: 0.9,
    ringAlpha: 0.1,
    label: true,
  },
};

const SAMPLES = [
  {
    id: "aspirin",
    type: "molecule",
    name: "Aspirin lead review",
    shortName: "Aspirin",
    subtitle: "COX scaffold · oral small molecule",
    formula: "C9H8O4",
    smiles: "CC(=O)OC1=CC=CC=C1C(=O)O",
    notes:
      "乙酰水杨酸包含芳香环、酯键与羧酸；Agent 可围绕这个抗炎 lead scaffold 组织性质分析、风险判断和类似物设计。",
    selection: "Aspirin · anti-inflammatory scaffold",
    confidence: "curated example",
    properties: {
      MW: "180.16",
      logP: "1.2",
      HBA: "3",
      HBD: "1",
      TPSA: "63.6",
      pKa: "3.5",
    },
    atoms: [
      { e: "C", x: -2.8, y: -0.2, z: 0.2 },
      { e: "C", x: -1.6, y: -0.2, z: 0.0 },
      { e: "O", x: -1.0, y: 0.8, z: -0.15 },
      { e: "O", x: -1.0, y: -1.25, z: 0.1 },
      { e: "C", x: 0.2, y: -1.1, z: -0.1 },
      { e: "C", x: 0.8, y: 0.0, z: 0.2 },
      { e: "C", x: 0.2, y: 1.1, z: -0.2 },
      { e: "C", x: 0.85, y: 2.2, z: 0.0 },
      { e: "C", x: 2.1, y: 2.2, z: 0.15 },
      { e: "C", x: 2.75, y: 1.1, z: -0.1 },
      { e: "C", x: 2.1, y: 0.0, z: 0.05 },
      { e: "C", x: 3.35, y: -0.05, z: 0.1 },
      { e: "O", x: 4.05, y: 0.9, z: -0.1 },
      { e: "O", x: 3.85, y: -1.15, z: 0.15 },
    ],
    bonds: [
      [0, 1, 1],
      [1, 2, 2],
      [1, 3, 1],
      [3, 4, 1],
      [4, 5, 1],
      [5, 6, 2],
      [6, 7, 1],
      [7, 8, 2],
      [8, 9, 1],
      [9, 10, 2],
      [10, 5, 1],
      [10, 11, 1],
      [11, 12, 2],
      [11, 13, 1],
    ],
    rings: [[5, 6, 7, 8, 9, 10]],
    prompts: [
      "解释这个分子的药物样性质",
      "优化这个分子的水溶性并解释风险",
      "给我 3 个可合成的类似物方向",
    ],
  },
  {
    id: "caffeine",
    type: "molecule",
    name: "Caffeine interaction map",
    shortName: "Caffeine",
    subtitle: "xanthine core · CNS stimulant",
    formula: "C8H10N4O2",
    smiles: "CN1C=NC2=C1C(=O)N(C)C(=O)N2C",
    notes:
      "咖啡因展示含氮杂环和两个羰基，适合演示自然语言问答、官能团识别和性质解释。",
    selection: "Caffeine · xanthine alkaloid",
    confidence: "curated example",
    properties: {
      MW: "194.19",
      logP: "-0.1",
      HBA: "6",
      HBD: "0",
      TPSA: "61.8",
      pKa: "0.6",
    },
    atoms: [
      { e: "C", x: -3.0, y: -0.25, z: 0.08 },
      { e: "N", x: -1.8, y: 0.0, z: 0.16 },
      { e: "C", x: -1.18, y: -1.05, z: -0.12 },
      { e: "N", x: 0.08, y: -0.92, z: 0.04 },
      { e: "C", x: 0.66, y: 0.04, z: 0.18 },
      { e: "C", x: -0.12, y: 1.08, z: -0.08 },
      { e: "C", x: 0.58, y: 2.18, z: 0.1 },
      { e: "O", x: 0.1, y: 3.28, z: -0.08 },
      { e: "N", x: 1.88, y: 2.04, z: -0.16 },
      { e: "C", x: 2.64, y: 3.16, z: 0.04 },
      { e: "C", x: 2.48, y: 0.88, z: 0.13 },
      { e: "O", x: 3.72, y: 0.86, z: -0.08 },
      { e: "N", x: 1.9, y: -0.24, z: -0.1 },
      { e: "C", x: 2.72, y: -1.34, z: 0.1 },
    ],
    bonds: [
      [0, 1, 1],
      [1, 2, 1],
      [2, 3, 2],
      [3, 4, 1],
      [4, 5, 2],
      [5, 1, 1],
      [5, 6, 1],
      [6, 7, 2],
      [6, 8, 1],
      [8, 9, 1],
      [8, 10, 1],
      [10, 11, 2],
      [10, 12, 1],
      [12, 13, 1],
      [12, 4, 1],
    ],
    rings: [
      [1, 2, 3, 4, 5],
      [4, 5, 6, 8, 10, 12],
    ],
    prompts: [
      "识别咖啡因的关键官能团",
      "解释它为什么容易穿过血脑屏障",
      "设计一个降低 CNS 暴露的类似物",
    ],
  },
  {
    id: "trpcage",
    type: "protein",
    name: "Trp-cage mini protein",
    shortName: "Trp-cage",
    subtitle: "20 aa · folding benchmark",
    formula: "NLYIQWLKDGGPSSGRPPPS",
    sequence: "NLYIQWLKDGGPSSGRPPPS",
    notes:
      "Trp-cage 是小型折叠蛋白示例，可用于检查螺旋、转角、疏水核心和自然语言突变建议。",
    selection: "Trp-cage · compact folding motif",
    confidence: "sequence heuristic",
    properties: {
      Length: "20 aa",
      pI: "8.7",
      Charge: "+1",
      Helix: "38%",
      GRAVY: "-0.46",
      Risk: "Low",
    },
    prompts: [
      "找出这个小蛋白的稳定性热点",
      "建议 3 个提高热稳定性的突变",
      "解释疏水核心和表面电荷分布",
    ],
  },
  {
    id: "binder",
    type: "protein",
    name: "De novo binder concept",
    shortName: "Binder",
    subtitle: "64 aa · interface design",
    formula: "EQLRAELAAKYEELARKGVPDAAQKAFDEAMKQLSEKGLDVLKQKNAEELKKQGIDAL",
    sequence: "EQLRAELAAKYEELARKGVPDAAQKAFDEAMKQLSEKGLDVLKQKNAEELKKQGIDAL",
    notes:
      "这个概念蛋白用于演示 LLM Agent 如何把自然语言目标转成界面设计、突变组合与实验验证计划。",
    selection: "De novo binder · alpha-rich interface",
    confidence: "generated scaffold heuristic",
    properties: {
      Length: "64 aa",
      pI: "5.2",
      Charge: "-6",
      Helix: "72%",
      GRAVY: "-0.32",
      Risk: "Medium",
    },
    prompts: [
      "为这个 binder 设计界面突变",
      "生成一份实验验证计划",
      "降低聚集风险并保留结合界面",
    ],
  },
];

const state = {
  activeId: "aspirin",
  activeMode: "structure",
  activeTab: "properties",
  viewerStyle: "ballstick",
  showLabels: true,
  isAnimating: true,
  angleX: -0.24,
  angleY: 0.42,
  zoom: 1,
  toolCalls: [],
  candidates: [],
  artifacts: [],
  skills: [],
  workflowTemplates: [],
  workflowRuns: [],
  workspaceFiles: [],
  chat: [],
  runtime: {
    useApi: false,
    endpoint: "",
    model: "your-model-name",
    key: "",
    toolMode: "native",
  },
  pointer: {
    down: false,
    x: 0,
    y: 0,
  },
};

const els = {};
let canvas;
let ctx;
let rafId;
const structureGeometryCache = new WeakMap();

document.addEventListener("DOMContentLoaded", () => {
  bindElements();
  renderSampleList();
  selectSample("aspirin", { silent: true });
  bindEvents();
  resizeCanvas();
  requestAnimationFrame(drawLoop);
  loadWorkbenchMetadata();
  addSystemMessage("Molemo WorkBench 已加载。选择示例、导入本地文件，或直接提出研究问题。");
});

function bindElements() {
  [
    "sampleList",
    "activeTitle",
    "activeType",
    "viewerLabel",
    "selectionReadout",
    "confidenceReadout",
    "propertyGrid",
    "structureNotes",
    "sequenceBlock",
    "toolTrace",
    "workflowList",
    "artifactList",
    "skillList",
    "designList",
    "chatLog",
    "commandForm",
    "commandInput",
    "promptChips",
    "runDefaultPrompt",
    "resetWorkspace",
    "loadSmiles",
    "loadFasta",
    "loadStructure",
    "workspaceFiles",
    "saveWorkspaceFiles",
    "workspaceFileList",
    "workspaceFileCount",
    "structureInput",
    "toggleMotion",
    "toggleLabels",
    "zoomIn",
    "zoomOut",
    "exportReport",
    "toolCallCount",
    "candidateCount",
    "skillCount",
    "runtimeModeLabel",
    "localStatusText",
    "apiSettings",
    "settingsDialog",
    "useApiRuntime",
    "apiEndpoint",
    "apiModel",
    "apiKey",
    "toolMode",
    "saveSettings",
    "agentRuntimeState",
    "apiBadge",
    "planWorkflow",
    "workflowDialog",
    "workflowTemplate",
    "workflowDescription",
    "workflowFields",
    "createWorkflowPlan",
  ].forEach((id) => {
    els[id] = document.getElementById(id);
  });

  canvas = document.getElementById("structureCanvas");
  ctx = canvas.getContext("2d");
}

function bindEvents() {
  window.addEventListener("resize", resizeCanvas);

  els.commandForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const command = els.commandInput.value.trim();
    if (!command) return;
    els.commandInput.value = "";
    runAgent(command);
  });

  els.runDefaultPrompt.addEventListener("click", () => {
    const sample = getActiveSample();
    runAgent(sample.prompts[0]);
  });

  els.resetWorkspace.addEventListener("click", () => {
    state.toolCalls = [];
    state.candidates = [];
    state.artifacts = [];
    state.chat = [];
    selectSample("aspirin", { silent: true });
    addSystemMessage("工作区已重置。");
    renderAll();
  });

  els.loadSmiles.addEventListener("click", () => {
    const value = els.structureInput.value.trim();
    if (!value) return;
    loadCustomMolecule(value);
  });

  els.loadFasta.addEventListener("click", () => {
    const value = els.structureInput.value.trim();
    if (!value) return;
    loadCustomProtein(value);
  });

  els.loadStructure.addEventListener("click", () => {
    const value = els.structureInput.value.trim();
    if (!value) return;
    loadProteinStructure(value);
  });

  els.saveWorkspaceFiles.addEventListener("click", saveSelectedWorkspaceFiles);

  els.toggleMotion.addEventListener("click", () => {
    state.isAnimating = !state.isAnimating;
  });

  els.toggleLabels.addEventListener("click", () => {
    state.showLabels = !state.showLabels;
  });

  els.zoomIn.addEventListener("click", () => {
    state.zoom = Math.min(1.8, state.zoom + 0.12);
  });

  els.zoomOut.addEventListener("click", () => {
    state.zoom = Math.max(0.58, state.zoom - 0.12);
  });

  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeMode = button.dataset.mode;
      renderSegments();
      renderDesigns();
      if (button.dataset.mode === "design") switchTab("designs");
      if (button.dataset.mode === "risk") runAgent("总结当前结构的主要风险和下一步验证");
    });
  });

  document.querySelectorAll(".viewer-style").forEach((button) => {
    button.addEventListener("click", () => {
      state.viewerStyle = button.dataset.style;
      renderViewerStyles();
      renderHeader();
    });
  });

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  els.exportReport.addEventListener("click", exportReport);

  els.apiSettings.addEventListener("click", () => {
    els.useApiRuntime.checked = state.runtime.useApi;
    els.apiEndpoint.value = state.runtime.endpoint;
    els.apiModel.value = state.runtime.model;
    els.apiKey.value = state.runtime.key;
    els.toolMode.value = state.runtime.toolMode;
    els.settingsDialog.showModal();
  });

  els.saveSettings.addEventListener("click", (event) => {
    event.preventDefault();
    state.runtime.useApi = els.useApiRuntime.checked;
    state.runtime.endpoint = els.apiEndpoint.value.trim();
    state.runtime.model = els.apiModel.value.trim() || "your-model-name";
    state.runtime.key = els.apiKey.value.trim();
    state.runtime.toolMode = els.toolMode.value;
    els.settingsDialog.close();
    renderRuntime();
    addSystemMessage(
      state.runtime.useApi
        ? "第三方模型已启用；下一次命令将由本地 Agent 调度 skills，并把必要上下文转发给该 provider。"
        : "已切回本地 skill runtime。",
    );
  });

  els.planWorkflow.addEventListener("click", openWorkflowDialog);
  els.workflowTemplate.addEventListener("change", renderWorkflowFields);
  els.createWorkflowPlan.addEventListener("click", createWorkflowPlan);

  canvas.addEventListener("pointerdown", (event) => {
    state.pointer.down = true;
    state.pointer.x = event.clientX;
    state.pointer.y = event.clientY;
    canvas.setPointerCapture(event.pointerId);
  });

  canvas.addEventListener("pointermove", (event) => {
    if (!state.pointer.down) return;
    const dx = event.clientX - state.pointer.x;
    const dy = event.clientY - state.pointer.y;
    state.angleY += dx * 0.008;
    state.angleX += dy * 0.008;
    state.pointer.x = event.clientX;
    state.pointer.y = event.clientY;
  });

  canvas.addEventListener("pointerup", (event) => {
    state.pointer.down = false;
    canvas.releasePointerCapture(event.pointerId);
  });

  canvas.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      state.zoom = clamp(state.zoom - event.deltaY * 0.001, 0.58, 1.8);
    },
    { passive: false },
  );
}

function renderSampleList() {
  els.sampleList.innerHTML = "";
  SAMPLES.forEach((sample) => {
    const button = document.createElement("button");
    button.className = "sample-button";
    button.dataset.id = sample.id;
    button.dataset.type = sample.type;
    button.innerHTML = `
      <span class="sample-icon">${sample.type === "protein" ? "P" : "M"}</span>
      <span class="sample-main">
        <strong>${escapeHtml(sample.shortName)}</strong>
        <span>${escapeHtml(sample.subtitle)}</span>
      </span>
    `;
    button.addEventListener("click", () => selectSample(sample.id));
    els.sampleList.appendChild(button);
  });
}

function selectSample(id, options = {}) {
  const sample = SAMPLES.find((item) => item.id === id);
  if (!sample) return;
  state.activeId = id;
  state.zoom = 1;
  state.angleX = sample.type === "protein" ? -0.38 : -0.24;
  state.angleY = sample.type === "protein" ? 0.18 : 0.42;
  if (!options.keepDesigns) state.candidates = initialCandidates(sample);
  if (!options.silent) addSystemMessage(`已加载 ${sample.shortName}。`);
  renderAll();
}

function renderAll() {
  renderHeader();
  renderProperties();
  renderPromptChips();
  renderSampleActiveState();
  renderToolTrace();
  renderWorkflowRuns();
  renderArtifacts();
  renderSkills();
  renderWorkspaceFiles();
  renderDesigns();
  renderChat();
  renderMetrics();
  renderRuntime();
  renderSegments();
  renderViewerStyles();
}

function renderHeader() {
  const sample = getActiveSample();
  els.activeTitle.textContent = sample.name;
  els.activeType.textContent = sample.type === "protein" ? "Protein" : "Molecule";
  els.activeType.style.background = sample.type === "protein" ? "var(--amber-soft)" : "var(--teal-soft)";
  els.activeType.style.color = sample.type === "protein" ? "var(--amber)" : "var(--teal)";
  const preset = VIEWER_PRESETS[state.viewerStyle] || VIEWER_PRESETS.ballstick;
  els.viewerLabel.textContent = sample.structure?.atoms?.length
    ? `${preset.name} atom-level protein structure`
    : sample.type === "protein"
      ? "protein ribbon and residue field"
      : `${preset.name} molecular view`;
  els.selectionReadout.textContent = sample.selection;
  els.confidenceReadout.textContent = sample.confidence;
  els.structureInput.value = sample.pdbId || sample.smiles || sample.sequence || "";
}

function renderProperties() {
  const sample = getActiveSample();
  els.propertyGrid.innerHTML = "";
  Object.entries(sample.properties).forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "property-card";
    card.innerHTML = `<span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong>`;
    els.propertyGrid.appendChild(card);
  });
  els.structureNotes.textContent = sample.notes;

  if (sample.type === "protein") {
    const sequence = sample.sequence || "";
    els.sequenceBlock.innerHTML = `
      <span>Sequence</span>
      <div class="sequence-text">${formatSequence(sequence)}${sequence.length > 2000 ? " …" : ""}</div>
    `;
    els.sequenceBlock.style.display = "block";
  } else {
    els.sequenceBlock.innerHTML = `
      <span>SMILES</span>
      <div class="sequence-text">${escapeHtml(sample.smiles || "")}</div>
    `;
    els.sequenceBlock.style.display = "block";
  }
}

function renderPromptChips() {
  const sample = getActiveSample();
  els.promptChips.innerHTML = "";
  sample.prompts.forEach((prompt) => {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.type = "button";
    chip.textContent = prompt;
    chip.addEventListener("click", () => runAgent(prompt));
    els.promptChips.appendChild(chip);
  });
}

function renderSampleActiveState() {
  document.querySelectorAll(".sample-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.id === state.activeId);
  });
}

function renderSegments() {
  document.querySelectorAll(".segment").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.mode === state.activeMode);
  });
}

function renderViewerStyles() {
  document.querySelectorAll(".viewer-style").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.style === state.viewerStyle);
  });
}

function switchTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === tab);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.remove("is-active");
  });
  document.getElementById(`${tab}Panel`).classList.add("is-active");
}

function renderToolTrace() {
  els.toolTrace.innerHTML = "";
  if (!state.toolCalls.length) {
    const empty = document.createElement("div");
    empty.className = "tool-call";
    empty.innerHTML =
      "<span>No tool calls yet</span><p>运行自然语言命令后，这里会显示 Agent 规划和工具调用轨迹。</p>";
    els.toolTrace.appendChild(empty);
    return;
  }

  state.toolCalls
    .slice()
    .reverse()
    .forEach((call) => {
      const item = document.createElement("article");
      item.className = "tool-call";
      item.innerHTML = `
        <header>
          <code>${escapeHtml(call.name)}</code>
          <span>${escapeHtml(call.status || "completed")} · ${escapeHtml(call.time || "")}</span>
        </header>
        <p>${escapeHtml(call.summary)}</p>
        <code>${escapeHtml(JSON.stringify(call.args))}</code>
      `;
      els.toolTrace.appendChild(item);
    });
}

function renderArtifacts() {
  els.artifactList.innerHTML = "";
  if (!state.artifacts.length) {
    els.artifactList.innerHTML =
      '<div class="artifact-card"><span>No artifacts yet</span><p>结构、序列比对和性质图会作为可检查产物显示在这里。</p></div>';
    return;
  }

  state.artifacts
    .slice()
    .reverse()
    .forEach((artifact) => {
      const card = document.createElement("article");
      card.className = "artifact-card";
      const title = escapeHtml(artifact.title || artifact.type || "Artifact");
      if (["molecule", "protein-sequence", "protein-structure"].includes(artifact.type)) {
        const sample = artifact.data || {};
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(artifact.type)}</span></header>
          <p>${escapeHtml(sample.selection || sample.notes || "Viewer-ready scientific artifact")}</p>
          <button class="secondary-button artifact-open" type="button">在${artifact.type === "protein-sequence" ? "序列" : "结构"}视图打开</button>
        `;
        card.querySelector(".artifact-open").addEventListener("click", () => {
          if (!sample.type) return;
          upsertCustomSample(sample);
          selectSample(sample.id, { keepDesigns: true });
          switchTab("properties");
        });
      } else if (artifact.type === "database-record") {
        const data = artifact.data || {};
        const fields = databaseRecordFields(data);
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(data.source || "database")}</span></header>
          <div class="record-grid">
            ${fields.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
          </div>
          ${safeExternalUrl(data.source_url) ? `<a class="source-link" href="${escapeHtml(data.source_url)}" target="_blank" rel="noreferrer">打开官方记录</a>` : ""}
        `;
      } else if (artifact.type === "fastq-qc") {
        const data = artifact.data || {};
        const quality = data.per_cycle_quality || [];
        const minQuality = Math.min(...quality, 0);
        const maxQuality = Math.max(...quality, 40);
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(data.sampled ? "sampled" : "complete")}</span></header>
          <div class="qc-metrics">
            ${[
              ["Reads", data.reads_analyzed],
              ["Mean Q", data.mean_quality],
              ["Q30", `${data.q30_percent}%`],
              ["GC", `${data.gc_percent}%`],
            ].map(([label, value]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
          </div>
          <div class="cycle-chart" aria-label="Mean quality by sequencing cycle">
            ${quality.map((value, index) => `<i title="Cycle ${index + 1}: Q${value}" style="height:${clamp(((Number(value) - minQuality) / Math.max(1, maxQuality - minQuality)) * 100, 3, 100)}%"></i>`).join("")}
          </div>
          <p>${escapeHtml(`${data.mean_read_length} bp mean length · Q20 ${data.q20_percent}% · N ${data.n_percent}% · ${data.quality_encoding}`)}</p>
        `;
      } else if (artifact.type === "sequence-alignment") {
        const data = artifact.data || {};
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(`${data.identity || 0}% identity`)}</span></header>
          <div class="alignment-view">
            <code>${escapeHtml(data.labelA || "A")} ${escapeHtml(data.sequenceA || "")}</code>
            <code class="alignment-markers">${escapeHtml(" ".repeat(String(data.labelA || "A").length + 1) + (data.markers || ""))}</code>
            <code>${escapeHtml(data.labelB || "B")} ${escapeHtml(data.sequenceB || "")}</code>
          </div>
        `;
      } else if (artifact.type === "bar-chart") {
        const data = artifact.data || {};
        const values = data.values || [];
        const max = Math.max(...values.map((value) => Math.abs(Number(value))), 1);
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(data.unit || "values")}</span></header>
          <div class="bar-chart">
            ${(data.labels || [])
              .map((label, index) => {
                const value = Number(values[index] || 0);
                return `<div class="bar-row"><span>${escapeHtml(label)}</span><div><i style="width:${Math.max(2, (Math.abs(value) / max) * 100)}%"></i></div><strong>${escapeHtml(value)}</strong></div>`;
              })
              .join("")}
          </div>
        `;
      } else if (artifact.type === "sequence-track") {
        const data = artifact.data || {};
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(`${(data.sequence || "").length} aa`)}</span></header>
          <div class="sequence-track">
            ${(data.sequence || "")
              .split("")
              .map((aa, index) => {
                const value = Number((data.values || [])[index] || 0);
                const level = Math.round(((value + 4.5) / 9) * 100);
                return `<span title="${escapeHtml(`${index + 1} ${aa}: ${value}`)}" style="--track:${clamp(level, 0, 100)}%">${escapeHtml(aa)}</span>`;
              })
              .join("")}
          </div>
        `;
      } else {
        card.innerHTML = `<header><strong>${title}</strong><span>${escapeHtml(artifact.type || "artifact")}</span></header>`;
      }
      els.artifactList.appendChild(card);
    });
}

function renderSkills() {
  els.skillList.innerHTML = "";
  if (!state.skills.length) {
    els.skillList.innerHTML =
      '<div class="skill-card"><span>Local service offline</span><p>启动本地服务后会自动发现 skills。</p></div>';
    return;
  }
  state.skills.forEach((skill) => {
    const card = document.createElement("article");
    card.className = "skill-card";
    card.innerHTML = `
      <header><strong>${escapeHtml(skill.title)}</strong><span>${escapeHtml(skill.kind)}</span></header>
      <p>${escapeHtml(skill.description)}</p>
      <div class="skill-tools">${(skill.tools || []).map((tool) => `<code>${escapeHtml(tool.name)}</code>`).join("")}</div>
    `;
    els.skillList.appendChild(card);
  });
}

function renderWorkflowRuns() {
  els.workflowList.innerHTML = "";
  if (!state.workflowRuns.length) {
    els.workflowList.innerHTML =
      '<div class="workflow-empty"><span>No guided runs</span><p>制定计划后，可在这里审阅步骤并批准执行。</p></div>';
    return;
  }

  state.workflowRuns
    .slice()
    .slice(0, 8)
    .forEach((run) => {
      const item = document.createElement("article");
      item.className = "workflow-run";
      const steps = (run.steps || [])
        .map(
          (step, index) => `
            <li>
              <span>${index + 1}</span>
              <div><strong>${escapeHtml(step.title || step.tool)}</strong><code>${escapeHtml(step.tool || "")}</code></div>
              <small class="workflow-step-status ${escapeHtml(step.status || "pending")}">${escapeHtml(workflowStatusLabel(step.status))}</small>
            </li>`,
        )
        .join("");
      item.innerHTML = `
        <header>
          <div><strong>${escapeHtml(run.title || "Guided workflow")}</strong><small>${escapeHtml(run.objective || run.description || "")}</small></div>
          <span class="workflow-status ${escapeHtml(run.status || "pending_approval")}">${escapeHtml(workflowStatusLabel(run.status))}</span>
        </header>
        <ol>${steps}</ol>
        ${run.error ? `<p class="workflow-error">${escapeHtml(run.error)}</p>` : ""}
        ${
          run.status === "pending_approval"
            ? '<div class="workflow-actions"><button class="secondary-button workflow-cancel" type="button">取消</button><button class="primary-button workflow-approve" type="button">批准并运行</button></div>'
            : ""
        }
      `;
      item.querySelector(".workflow-approve")?.addEventListener("click", () => approveWorkflow(run.id));
      item.querySelector(".workflow-cancel")?.addEventListener("click", () => cancelWorkflow(run.id));
      els.workflowList.appendChild(item);
    });
}

function workflowStatusLabel(status) {
  return (
    {
      pending_approval: "待审批",
      pending: "等待",
      running: "运行中",
      completed: "已完成",
      failed: "失败",
      error: "失败",
      skipped: "跳过",
      cancelled: "已取消",
    }[status] || status || "等待"
  );
}

function renderWorkspaceFiles() {
  els.workspaceFileList.innerHTML = "";
  els.workspaceFileCount.textContent = `${state.workspaceFiles.length} files`;
  state.workspaceFiles.slice(0, 5).forEach((file) => {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "workspace-file";
    row.innerHTML = `<span>${escapeHtml(file.path)}</span><small>${escapeHtml(formatBytes(file.size))}</small>`;
    row.addEventListener("click", () => {
      if (/\.(pdb|cif|mmcif)$/i.test(file.path)) {
        executeLocalTool("structure_parse_workspace", { path: file.path }, { openSample: true });
      } else if (/\.(fastq|fq)$/i.test(file.path)) {
        executeLocalTool("ngs_fastq_qc", { path: file.path }, { openArtifacts: true });
      } else {
        runAgent(`读取 workspace 文件 ${file.path}，判断内容并建议下一步分析`);
      }
    });
    els.workspaceFileList.appendChild(row);
  });
}

function renderDesigns() {
  els.designList.innerHTML = "";
  if (!state.candidates.length) {
    const empty = document.createElement("div");
    empty.className = "candidate-card";
    empty.innerHTML = "<span>No candidates</span><p>让 Agent 执行“设计”“优化”或“突变”任务后会生成候选方案。</p>";
    els.designList.appendChild(empty);
    return;
  }

  state.candidates.forEach((candidate) => {
    const card = document.createElement("article");
    card.className = "candidate-card";
    card.innerHTML = `
      <header>
        <strong>${escapeHtml(candidate.name)}</strong>
        <span class="risk-badge ${candidate.risk}">${escapeHtml(candidate.riskLabel)}</span>
      </header>
      <p>${escapeHtml(candidate.summary)}</p>
      <div class="candidate-score" aria-label="score ${candidate.score}">
        <span style="width: ${candidate.score}%"></span>
      </div>
      <div class="candidate-meta">
        ${candidate.tags.map((tag) => `<code>${escapeHtml(tag)}</code>`).join("")}
      </div>
    `;
    els.designList.appendChild(card);
  });
  els.candidateCount.textContent = String(state.candidates.length);
}

function renderChat() {
  els.chatLog.innerHTML = "";
  state.chat.forEach((message) => {
    const item = document.createElement("article");
    item.className = `chat-message ${message.role}`;
    item.innerHTML = `
      ${message.role === "system" ? "" : `<strong>${message.role === "user" ? "You" : "molemo Agent"}</strong>`}
      <p>${escapeHtml(message.text)}</p>
    `;
    els.chatLog.appendChild(item);
  });
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function renderMetrics() {
  els.toolCallCount.textContent = String(state.toolCalls.length);
  els.candidateCount.textContent = String(state.candidates.length);
  els.skillCount.textContent = String(state.skills.length);
}

function renderRuntime() {
  const useApi = state.runtime.useApi && state.runtime.endpoint;
  els.runtimeModeLabel.textContent = useApi ? "API" : "Local";
  els.agentRuntimeState.textContent = useApi
    ? `${state.runtime.model} · ${state.runtime.toolMode}`
    : "Local scientific skill runtime";
  els.apiBadge.textContent = useApi ? "Provider enabled" : "Local only";
  els.apiBadge.style.background = useApi ? "var(--green-soft)" : "var(--amber-soft)";
  els.apiBadge.style.color = useApi ? "var(--green)" : "var(--amber)";
}

function openWorkflowDialog() {
  if (!state.workflowTemplates.length) {
    addSystemMessage("本地工作流目录尚未加载。");
    return;
  }
  const preferred = defaultWorkflowTemplate(getActiveSample());
  els.workflowTemplate.innerHTML = state.workflowTemplates
    .map(
      (template) =>
        `<option value="${escapeHtml(template.id)}" ${template.id === preferred ? "selected" : ""}>${escapeHtml(template.title)}</option>`,
    )
    .join("");
  renderWorkflowFields();
  els.workflowDialog.showModal();
}

function renderWorkflowFields() {
  const template = state.workflowTemplates.find((item) => item.id === els.workflowTemplate.value);
  els.workflowFields.innerHTML = "";
  if (!template) return;
  els.workflowDescription.textContent = template.description || "";
  (template.fields || []).forEach((field) => {
    const wrapper = document.createElement("label");
    wrapper.className = "workflow-field";
    const label = document.createElement("span");
    label.textContent = field.label || field.name;
    const control = createWorkflowControl(template.id, field);
    wrapper.append(label, control);
    els.workflowFields.appendChild(wrapper);
  });
}

function createWorkflowControl(templateId, field) {
  let control;
  if (field.type === "textarea") {
    control = document.createElement("textarea");
    control.rows = Number(field.rows || 4);
  } else if (field.type === "select") {
    control = document.createElement("select");
    (field.options || []).forEach((option) => {
      const item = document.createElement("option");
      item.value = option.value;
      item.textContent = option.label;
      control.appendChild(item);
    });
  } else {
    control = document.createElement("input");
    control.type = field.type === "number" ? "number" : "text";
    if (field.min !== undefined) control.min = field.min;
    if (field.max !== undefined) control.max = field.max;
  }
  control.dataset.workflowField = field.name;
  control.required = Boolean(field.required);
  control.placeholder = field.placeholder || "";
  control.value = workflowFieldDefault(templateId, field);
  return control;
}

function workflowFieldDefault(templateId, field) {
  const sample = getActiveSample();
  if (field.name === "smiles") return sample.smiles || "";
  if (field.name === "sequence" || field.name === "sequence_a") return sample.sequence || "";
  if (field.name === "pdb_id") return sample.pdbId || "";
  if (field.name === "source") {
    if (templateId === "protein-structure-review") return sample.metadata?.sourcePath ? "workspace" : "rcsb";
    return field.options?.[0]?.value || field.value || "";
  }
  if (field.name === "path") return sample.metadata?.sourcePath || "";
  if (field.name === "query") return sample.metadata?.accession || sample.shortName || "";
  return field.value === undefined ? "" : String(field.value);
}

function defaultWorkflowTemplate(sample) {
  if (sample.type === "molecule") return "molecule-profile";
  if (sample.structure?.atoms?.length) return "protein-structure-review";
  return "protein-sequence-review";
}

async function createWorkflowPlan() {
  const template = state.workflowTemplates.find((item) => item.id === els.workflowTemplate.value);
  if (!template) return;
  const inputs = {};
  for (const control of els.workflowFields.querySelectorAll("[data-workflow-field]")) {
    if (!control.checkValidity()) {
      control.reportValidity();
      return;
    }
    inputs[control.dataset.workflowField] = control.type === "number" ? Number(control.value) : control.value.trim();
  }
  els.createWorkflowPlan.disabled = true;
  try {
    const response = await fetch(pipelineEndpoint("/api/workflows/plan"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        template_id: template.id,
        inputs,
        objective: `${getActiveSample().name}: ${template.description}`,
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    upsertWorkflowRun(data.run);
    mergeArtifacts(data.run.artifacts || []);
    els.workflowDialog.close();
    switchTab("agent");
    addSystemMessage(`已创建“${data.run.title}”计划，等待研究者批准。`);
    renderAll();
  } catch (error) {
    addSystemMessage(`计划创建失败：${error.message}`);
  } finally {
    els.createWorkflowPlan.disabled = false;
  }
}

async function approveWorkflow(runId) {
  const run = state.workflowRuns.find((item) => item.id === runId);
  if (!run || run.status !== "pending_approval") return;
  run.status = "running";
  renderWorkflowRuns();
  try {
    const response = await fetch(pipelineEndpoint(`/api/runs/${encodeURIComponent(runId)}/approve`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    upsertWorkflowRun(data.run);
    mergeAgentTrace(data.run.trace || []);
    mergeArtifacts(data.run.artifacts || []);
    addSystemMessage(
      data.run.status === "completed"
        ? `“${data.run.title}”已完成，结果已进入可检查 artifacts。`
        : `“${data.run.title}”运行失败：${data.run.error || "未知错误"}`,
    );
  } catch (error) {
    run.status = "pending_approval";
    addSystemMessage(`工作流启动失败：${error.message}`);
  }
  renderAll();
}

async function cancelWorkflow(runId) {
  try {
    const response = await fetch(pipelineEndpoint(`/api/runs/${encodeURIComponent(runId)}/cancel`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    upsertWorkflowRun(data.run);
    addSystemMessage(`已取消“${data.run.title}”。`);
    renderAll();
  } catch (error) {
    addSystemMessage(`取消失败：${error.message}`);
  }
}

function upsertWorkflowRun(run) {
  if (!run?.id) return;
  const index = state.workflowRuns.findIndex((item) => item.id === run.id);
  if (index >= 0) state.workflowRuns.splice(index, 1, { ...state.workflowRuns[index], ...run });
  else state.workflowRuns.unshift(run);
}

async function runAgent(command) {
  const sample = getActiveSample();
  state.chat.push({ role: "user", text: command });
  renderChat();
  switchTab("agent");

  const result = await tryWorkbenchAgent(command, sample);
  if (result?.message) {
    mergeAgentTrace(result.trace || []);
    mergeArtifacts(result.artifacts || []);
    state.chat.push({ role: "agent", text: result.message });
    if (result.artifacts?.length) switchTab("artifacts");
    renderAll();
    return;
  }

  if (result?.error) {
    addSystemMessage(`本地 Agent 返回错误：${result.error}`);
    if (state.runtime.useApi) {
      const localResult = await tryWorkbenchAgent(command, sample, { forceLocal: true });
      if (localResult?.message) {
        mergeAgentTrace(localResult.trace || []);
        mergeArtifacts(localResult.artifacts || []);
        state.chat.push({ role: "agent", text: localResult.message });
        renderAll();
        return;
      }
    }
  }

  addSystemMessage("本地服务不可用，已降级为浏览器内置演示流程。");
  const intent = detectIntent(command, sample);
  addToolCall("agent.plan", { intent, target: sample.shortName }, `将自然语言任务路由到 ${intent} 工作流。`);
  await runLocalWorkflow(command, sample, intent);
}

async function runLocalWorkflow(command, sample, intent) {
  await pause(180);
  addToolCall(
    sample.type === "protein" ? "structure.parse_fasta" : "chem.parse_smiles",
    { input: sample.sequence || sample.smiles || sample.formula },
    sample.type === "protein" ? "解析序列并估计二级结构倾向。" : "解析 SMILES 并识别官能团与环系统。",
  );

  await pause(180);
  addToolCall(
    sample.type === "protein" ? "protein.annotate_motifs" : "chem.estimate_properties",
    { properties: sample.properties },
    sample.type === "protein" ? "标注螺旋、带电残基与潜在界面热点。" : "估算药物样性质、极性表面积和可优化位点。",
  );

  if (intent === "design" || intent === "risk") {
    await pause(180);
    const generated = sample.type === "protein" ? proteinCandidates(sample, command) : moleculeCandidates(sample, command);
    state.candidates = generated;
    addToolCall(
      sample.type === "protein" ? "design.propose_mutations" : "design.propose_analogs",
      { count: generated.length, constraints: inferConstraints(command) },
      sample.type === "protein" ? "生成可验证突变组合并标记聚集风险。" : "生成类似物方向并保留核心 scaffold。",
    );
    switchTab("designs");
  }

  await pause(120);
  const response = composeAgentResponse(command, sample, intent);
  state.chat.push({ role: "agent", text: response });
  renderAll();
}

async function tryWorkbenchAgent(command, sample, options = {}) {
  const useProvider = state.runtime.useApi && state.runtime.endpoint && !options.forceLocal;
  const payload = {
    message: command,
    history: state.chat.slice(0, -1).map((item) => ({
      role: item.role === "agent" ? "assistant" : item.role,
      content: item.text,
    })),
    context: {
      type: sample.type,
      name: sample.name,
      smiles: sample.smiles,
      sequence: sample.sequence,
      pdb_id: sample.pdbId,
      path: sample.metadata?.sourcePath,
      properties: sample.properties,
      notes: sample.notes,
    },
    provider: useProvider
      ? {
          endpoint: state.runtime.endpoint,
          model: state.runtime.model,
          key: state.runtime.key,
          tool_mode: state.runtime.toolMode,
          temperature: 0.2,
        }
      : {},
  };

  try {
    const response = await fetch(pipelineEndpoint("/api/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) return { error: data?.error || `HTTP ${response.status}` };
    return data;
  } catch (error) {
    console.warn("Local agent runtime failed", error);
    return null;
  }
}

function mergeAgentTrace(trace) {
  trace.forEach((call) => {
    state.toolCalls.push({
      name: call.name || "skill",
      skill: call.skill || "",
      args: call.args || {},
      summary: call.summary || "Skill completed.",
      status: call.status || "completed",
      durationMs: call.duration_ms || 0,
      time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
    });
  });
}

function mergeArtifacts(artifacts) {
  artifacts.forEach((artifact) => {
    if (artifact.type === "workflow-plan" && artifact.data?.id) {
      const existing = state.workflowRuns.find((item) => item.id === artifact.data.id);
      if (existing) {
        existing.status = artifact.data.status || existing.status;
      } else {
        upsertWorkflowRun({
          ...artifact.data,
          description: "Agent proposed workflow",
          trace: [],
          artifacts: [artifact],
        });
      }
    }
    const index = state.artifacts.findIndex((item) => item.id === artifact.id);
    if (index >= 0) state.artifacts.splice(index, 1, artifact);
    else state.artifacts.push(artifact);
  });
}

function addToolCall(name, args, summary) {
  state.toolCalls.push({
    name,
    args,
    summary,
    time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
  });
  renderToolTrace();
  renderMetrics();
}

function addSystemMessage(text) {
  state.chat.push({ role: "system", text });
  renderChat();
}

function detectIntent(command, sample) {
  const text = command.toLowerCase();
  if (/design|optimi[sz]e|analog|类似物|优化|设计|突变|mutation|binder|稳定|solubility|水溶/.test(text)) {
    return "design";
  }
  if (/risk|毒|admet|聚集|风险|验证|实验|plan|protocol/.test(text)) {
    return "risk";
  }
  if (/官能团|function|property|性质|解释|why|为什么/.test(text)) {
    return "analysis";
  }
  return sample.type === "protein" ? "protein_analysis" : "molecule_analysis";
}

function inferConstraints(command) {
  const constraints = [];
  if (/水溶|solubility|polar/i.test(command)) constraints.push("increase polarity");
  if (/稳定|thermal|stability/i.test(command)) constraints.push("increase stability");
  if (/聚集|aggregation/i.test(command)) constraints.push("lower aggregation");
  if (/合成|synthetic|synthesis/i.test(command)) constraints.push("synthetic accessibility");
  return constraints.length ? constraints : ["retain core activity", "prefer conservative changes"];
}

function composeAgentResponse(command, sample, intent) {
  if (sample.type === "protein") {
    if (intent === "design") {
      return `${sample.shortName} 的设计重点是保留疏水核心，同时把表面不稳定或易聚集位点换成更温和的带电/极性残基。我建议先做 3 组小批量突变，随后用表达量、SEC、DSF 和目标结合实验验证。`;
    }
    if (intent === "risk") {
      return `主要风险是局部疏水斑块、过强电荷偏置和螺旋束边缘的构象松动。下一步应把突变方案和实验读数绑定：表达量筛掉不可折叠设计，DSF 看稳定性，BLI/SPR 看结合是否保留。`;
    }
    return `${sample.shortName} 的序列特征提示其可能以 α 螺旋或紧凑折叠为主。Agent 已标注带电残基、疏水核心和候选界面位置；这些是序列层面的假设，可继续要求“设计突变”“降低聚集”或“生成实验计划”。`;
  }

  if (intent === "design") {
    return `${sample.shortName} 的 scaffold 可以保留核心识别元素，同时在外围做小步改造。当前候选优先提高可溶性或降低暴露风险，并避免一次引入过多立体和电子变化。`;
  }
  if (intent === "risk") {
    return `当前结构的风险应从酸碱性、极性表面积、潜在代谢软点和选择性开始看。建议先做 ADME 快筛，再用目标活性实验确认改造没有破坏核心作用。`;
  }
  return `${sample.shortName} 的关键结构已经解析：Agent 识别了核心环系统、供受体模式和可修饰外围位点。你可以继续要求优化水溶性、设计类似物或生成验证计划。`;
}

function initialCandidates(sample) {
  if (sample.type === "protein") return proteinCandidates(sample, "");
  return moleculeCandidates(sample, "");
}

function moleculeCandidates(sample, command) {
  const solubility = /水溶|solubility|polar/i.test(command);
  const cns = /cns|血脑|brain/i.test(command);
  return [
    {
      name: solubility ? "Polar edge analog" : "Conservative bioisostere",
      risk: "low",
      riskLabel: "Low",
      score: solubility ? 82 : 76,
      summary: solubility
        ? "在外围引入轻量极性取代，目标是提升溶解度，同时保留核心识别几何。"
        : "用温和电子等排变化保留 scaffold，适合作为第一轮 SAR 对照。",
      tags: [sample.smiles || sample.formula, solubility ? "TPSA +12" : "core retained", "1-step SAR"],
    },
    {
      name: cns ? "Reduced CNS exposure" : "Metabolic soft-spot shield",
      risk: "medium",
      riskLabel: "Medium",
      score: cns ? 73 : 69,
      summary: cns
        ? "提高极性并降低被动扩散倾向，用于减少中枢暴露。"
        : "在疑似代谢软点附近加入小型保护取代，但需要确认活性不受影响。",
      tags: [cns ? "logD down" : "microsome follow-up", "ADME screen", "activity check"],
    },
    {
      name: "Exploratory vector scan",
      risk: "high",
      riskLabel: "High",
      score: 52,
      summary: "沿可修饰向量扫描更大取代基，信息量高，但合成与选择性风险也更高。",
      tags: ["vector scan", "selectivity risk", "make 3 only"],
    },
  ];
}

function proteinCandidates(sample, command) {
  const stability = /稳定|thermal|stability/i.test(command);
  const aggregation = /聚集|aggregation/i.test(command);
  const base = sample.sequence || sample.formula;
  return [
    {
      name: stability ? "Helix cap stabilization" : "Interface charge tuning",
      risk: "low",
      riskLabel: "Low",
      score: stability ? 84 : 78,
      summary: stability
        ? "在螺旋端加入更友好的 cap 残基，降低局部解折叠概率。"
        : "微调界面附近电荷，提升结合方向性并保留整体折叠。",
      tags: [suggestMutation(base, 4, stability ? "S" : "E"), suggestMutation(base, 11, "K"), "DSF + binding"],
    },
    {
      name: aggregation ? "Surface patch cleanup" : "Hydrophobic core packing",
      risk: "medium",
      riskLabel: "Medium",
      score: aggregation ? 81 : 70,
      summary: aggregation
        ? "把暴露疏水斑块改成带电或极性残基，优先降低 SEC 聚集峰。"
        : "轻微加强核心 packing，但需要小心避免降低表达量。",
      tags: [suggestMutation(base, 18, aggregation ? "D" : "L"), suggestMutation(base, 27, "A"), "SEC required"],
    },
    {
      name: "Affinity exploratory pair",
      risk: "high",
      riskLabel: "High",
      score: 58,
      summary: "成对突变可能提高结合，但有破坏折叠或增加非特异相互作用的风险。",
      tags: [suggestMutation(base, 33, "Y"), suggestMutation(base, 42, "R"), "BLI/SPR gate"],
    },
  ];
}

function suggestMutation(sequence, index, to) {
  if (!sequence) return `X${index}${to}`;
  const pos = Math.min(Math.max(index, 1), sequence.length);
  return `${sequence[pos - 1]}${pos}${to}`;
}

async function loadCustomMolecule(smiles) {
  addToolCall("chem.pipeline_request", { smiles }, "请求本地 RDKit 数据管线解析 SMILES。");
  const result = await fetchPipelineSample("molecule", { smiles });
  if (result.sample) {
    upsertCustomSample(result.sample);
    selectSample(result.sample.id);
    addToolCall(
      "chem.rdkit_parse",
      {
        canonicalSmiles: result.sample.metadata?.canonicalSmiles || result.sample.smiles,
        atoms: result.sample.atoms?.length || 0,
        bonds: result.sample.bonds?.length || 0,
      },
      "RDKit 已返回真实分子 graph、键级、环系统和描述符。",
    );
    return;
  }

  if (!result.unavailable) {
    addSystemMessage(`SMILES 解析失败：${result.error || "未知错误"}`);
    return;
  }

  const custom = buildCustomMolecule(smiles);
  upsertCustomSample(custom);
  selectSample(custom.id);
  addToolCall("chem.import_smiles_fallback", { smiles }, "未连接本地管线，已降级为浏览器启发式结构视图。");
  addSystemMessage("本地 RDKit 管线不可用。运行 server.py 后可启用真实 SMILES 解析。");
}

async function loadCustomProtein(sequence) {
  addToolCall("protein.pipeline_request", { length: sequence.length }, "请求本地序列数据管线解析 FASTA。");
  const result = await fetchPipelineSample("protein", { sequence });
  if (result.sample) {
    upsertCustomSample(result.sample);
    selectSample(result.sample.id);
    addToolCall(
      "protein.sequence_parse",
      {
        length: result.sample.sequence?.length || 0,
        source: result.sample.metadata?.source || "local_sequence_pipeline",
      },
      "序列管线已返回清洗后的 FASTA、组成和蛋白性质统计。",
    );
    return;
  }

  if (!result.unavailable) {
    addSystemMessage(`FASTA 解析失败：${result.error || "未知错误"}`);
    return;
  }

  const fallbackSequence = cleanProteinInput(sequence);
  if (!fallbackSequence) {
    addSystemMessage("FASTA 解析失败：没有找到有效氨基酸序列。");
    return;
  }
  const custom = buildCustomProtein(fallbackSequence);
  upsertCustomSample(custom);
  selectSample(custom.id);
  addToolCall("protein.import_fasta_fallback", { length: fallbackSequence.length }, "未连接本地管线，已降级为浏览器序列草图。");
  addSystemMessage("本地序列管线不可用。运行 server.py 后可启用真实 FASTA 统计。");
}

async function loadProteinStructure(value) {
  const cleaned = String(value || "").trim();
  if (/^[0-9][A-Za-z0-9]{3}$/.test(cleaned)) {
    await executeLocalTool("structure_fetch_pdb", { pdb_id: cleaned.toUpperCase() }, { openSample: true });
    return;
  }
  if (/\.(pdb|cif|mmcif)$/i.test(cleaned)) {
    await executeLocalTool("structure_parse_workspace", { path: cleaned }, { openSample: true });
    return;
  }
  addSystemMessage("请输入四位 PDB ID，或先导入 workspace 后填写 .pdb/.cif/.mmcif 文件名。");
}

async function executeLocalTool(name, arguments, options = {}) {
  addToolCall(name, arguments, "正在执行本地 scientific skill…");
  try {
    const response = await fetch(pipelineEndpoint("/api/tools/call"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, arguments }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || `HTTP ${response.status}`);
    const latest = state.toolCalls[state.toolCalls.length - 1];
    latest.summary = result.summary || "Skill completed.";
    latest.status = "completed";
    latest.durationMs = result.duration_ms || 0;
    mergeArtifacts(result.artifacts || []);
    const sampleArtifact = (result.artifacts || []).find((artifact) => artifact.data?.type);
    if (options.openSample && sampleArtifact) {
      upsertCustomSample(sampleArtifact.data);
      selectSample(sampleArtifact.data.id, { keepDesigns: true });
      switchTab("properties");
    } else if (options.openArtifacts || result.artifacts?.length) {
      switchTab("artifacts");
    }
    addSystemMessage(result.summary || `${name} 已完成。`);
    renderAll();
    return result;
  } catch (error) {
    const latest = state.toolCalls[state.toolCalls.length - 1];
    latest.status = "error";
    latest.summary = error.message;
    addSystemMessage(`${name} 失败：${error.message}`);
    renderAll();
    return null;
  }
}

async function fetchPipelineSample(kind, payload) {
  try {
    const response = await fetch(pipelineEndpoint(`/api/${kind}`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      return {
        error: data?.error || `Pipeline request failed with ${response.status}`,
        code: data?.code || "pipeline_error",
        unavailable: false,
      };
    }
    return { sample: data.sample, unavailable: false };
  } catch (error) {
    return { error: error.message, unavailable: true };
  }
}

async function loadWorkbenchMetadata() {
  try {
    const [healthResponse, skillsResponse, workspaceResponse, workflowsResponse, runsResponse] = await Promise.all([
      fetch(pipelineEndpoint("/api/health")),
      fetch(pipelineEndpoint("/api/skills")),
      fetch(pipelineEndpoint("/api/workspace")),
      fetch(pipelineEndpoint("/api/workflows")),
      fetch(pipelineEndpoint("/api/runs")),
    ]);
    if (!healthResponse.ok || !skillsResponse.ok || !workspaceResponse.ok || !workflowsResponse.ok || !runsResponse.ok) {
      throw new Error("Local metadata request failed");
    }
    const [health, skills, workspace, workflows, runs] = await Promise.all([
      healthResponse.json(),
      skillsResponse.json(),
      workspaceResponse.json(),
      workflowsResponse.json(),
      runsResponse.json(),
    ]);
    state.skills = skills.skills || [];
    state.workspaceFiles = workspace.files || [];
    state.workflowTemplates = workflows.workflows || [];
    state.workflowRuns = runs.runs || [];
    els.localStatusText.textContent = `${health.skills || state.skills.length} skills · local agent ready`;
    renderSkills();
    renderWorkspaceFiles();
    renderWorkflowRuns();
    renderMetrics();
  } catch (error) {
    els.localStatusText.textContent = "本地服务未启动";
    renderSkills();
  }
}

async function saveSelectedWorkspaceFiles() {
  const files = Array.from(els.workspaceFiles.files || []);
  if (!files.length) {
    addSystemMessage("请先选择要导入的本地科学文件。");
    return;
  }
  let saved = 0;
  for (const file of files) {
    if (file.size > 20 * 1024 * 1024) {
      addSystemMessage(`${file.name} 超过 20 MB workspace 上传限制，未导入。`);
      continue;
    }
    try {
      const response = await fetch(pipelineEndpoint("/api/workspace/write"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: file.name, content: await file.text() }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
      saved += 1;
    } catch (error) {
      addSystemMessage(`${file.name} 导入失败：${error.message}`);
    }
  }
  els.workspaceFiles.value = "";
  await refreshWorkspaceFiles();
  if (saved) addSystemMessage(`已将 ${saved} 个文件导入受控 workspace；Agent 现在可以按需读取。`);
}

async function refreshWorkspaceFiles() {
  try {
    const response = await fetch(pipelineEndpoint("/api/workspace"));
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    state.workspaceFiles = data.files || [];
    renderWorkspaceFiles();
  } catch (error) {
    addSystemMessage(`无法刷新 workspace：${error.message}`);
  }
}

function pipelineEndpoint(path) {
  if (window.location.protocol === "http:" || window.location.protocol === "https:") {
    return path;
  }
  return `http://127.0.0.1:8765${path}`;
}

function upsertCustomSample(sample) {
  const index = SAMPLES.findIndex((item) => item.id === sample.id);
  if (index >= 0) SAMPLES.splice(index, 1, sample);
  else SAMPLES.push(sample);
  renderSampleList();
}

function buildCustomMolecule(smiles) {
  const atoms = [];
  const bonds = [];
  const tokens = tokenizeSmiles(smiles);
  const ring = /[1-9]/.test(smiles) || /c/.test(smiles);
  const count = Math.max(3, Math.min(tokens.length, 34));
  for (let i = 0; i < count; i += 1) {
    const angle = ring ? (Math.PI * 2 * i) / count : i * 0.85;
    const radius = ring ? 2.25 + (i % 2) * 0.22 : 0;
    atoms.push({
      e: normalizeElement(tokens[i] || "C"),
      x: ring ? Math.cos(angle) * radius : (i - count / 2) * 0.56,
      y: ring ? Math.sin(angle) * radius : Math.sin(i * 0.85) * 1.1,
      z: ring ? Math.sin(angle * 2) * 0.25 : Math.cos(i * 0.7) * 0.3,
    });
    if (i > 0) bonds.push([i - 1, i, i % 3 === 0 ? 2 : 1]);
  }
  if (ring && count > 4) bonds.push([count - 1, 0, 1]);

  return {
    id: "custom-molecule",
    type: "molecule",
    name: "Custom molecule",
    shortName: "Custom",
    subtitle: "imported SMILES · browser fallback",
    formula: estimateFormula(tokens),
    smiles,
    notes: "这是浏览器降级模式生成的快速结构草图；启动本地 server.py 后会优先使用 RDKit 真实解析。",
    selection: "Custom molecule · imported workspace",
    confidence: "browser fallback",
    properties: estimateMoleculeProperties(tokens, smiles),
    atoms,
    bonds,
    rings: ring && count > 4 ? [Array.from({ length: count }, (_, index) => index)] : [],
    prompts: [
      "解释这个分子的关键官能团",
      "优化这个分子的水溶性并解释风险",
      "生成 3 个下一轮设计方向",
    ],
  };
}

function buildCustomProtein(sequence) {
  sequence = cleanProteinInput(sequence);
  const length = sequence.length;
  return {
    id: "custom-protein",
    type: "protein",
    name: "Custom protein",
    shortName: "Custom protein",
    subtitle: `${length} aa · imported FASTA`,
    formula: sequence,
    sequence,
    notes: "这是浏览器降级模式生成的序列结构草图；启动本地 server.py 后会优先使用真实 FASTA 统计管线。",
    selection: "Custom protein · imported workspace",
    confidence: "browser fallback",
    properties: estimateProteinProperties(sequence),
    prompts: [
      "找出这个蛋白的稳定性热点",
      "建议 3 个突变并说明实验验证",
      "降低聚集风险并保留功能界面",
    ],
  };
}

function cleanProteinInput(raw) {
  return String(raw)
    .split(/\r?\n/)
    .filter((line) => !line.trim().startsWith(">"))
    .join("")
    .toUpperCase()
    .replace(/[^ACDEFGHIKLMNPQRSTVWY]/g, "");
}

function tokenizeSmiles(smiles) {
  return smiles.match(/Cl|Br|[BCNOFPSI]|c|n|o|s/g) || ["C", "C", "O"];
}

function normalizeElement(token) {
  if (!token) return "C";
  const normalized = token[0].toUpperCase() + (token.length > 1 ? token.slice(1).toLowerCase() : "");
  return ELEMENT_COLORS[normalized] ? normalized : normalized[0];
}

function estimateFormula(tokens) {
  const counts = tokens.reduce((acc, token) => {
    const element = normalizeElement(token);
    acc[element] = (acc[element] || 0) + 1;
    return acc;
  }, {});
  return Object.entries(counts)
    .map(([element, count]) => `${element}${count > 1 ? count : ""}`)
    .join("");
}

function estimateMoleculeProperties(tokens, smiles) {
  const heavy = tokens.length;
  const hetero = tokens.filter((token) => /N|O|S|P|n|o|s/i.test(token)).length;
  const oxygen = tokens.filter((token) => /O|o/.test(token)).length;
  const nitrogen = tokens.filter((token) => /N|n/.test(token)).length;
  return {
    MW: String(Math.round(heavy * 13.7 + hetero * 4.8)),
    logP: (1.8 + (heavy - hetero) * 0.08 - hetero * 0.18).toFixed(1),
    HBA: String(oxygen + nitrogen),
    HBD: String(Math.min(oxygen + nitrogen, Math.max(0, (smiles.match(/\[?NH|OH/g) || []).length))),
    TPSA: String(Math.round((oxygen + nitrogen) * 17.2)),
    Rings: String((smiles.match(/[1-9]/g) || []).length / 2 || (/[c]/.test(smiles) ? 1 : 0)),
  };
}

function estimateProteinProperties(sequence) {
  const charged = (sequence.match(/[DEKRH]/g) || []).length;
  const hydrophobic = (sequence.match(/[AILMFWYV]/g) || []).length;
  const acidic = (sequence.match(/[DE]/g) || []).length;
  const basic = (sequence.match(/[KRH]/g) || []).length;
  return {
    Length: `${sequence.length} aa`,
    pI: (7 + (basic - acidic) * 0.08).toFixed(1),
    Charge: `${basic - acidic > 0 ? "+" : ""}${basic - acidic}`,
    Helix: `${Math.round(((sequence.match(/[AEKLQR]/g) || []).length / sequence.length) * 100)}%`,
    GRAVY: ((hydrophobic / sequence.length) * 1.8 - 0.9).toFixed(2),
    Risk: charged > sequence.length * 0.42 ? "Medium" : "Low",
  };
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(320, Math.floor(rect.width * dpr));
  canvas.height = Math.max(260, Math.floor(rect.height * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function drawLoop() {
  if (state.isAnimating && !state.pointer.down) {
    state.angleY += 0.004;
  }
  drawScene();
  rafId = requestAnimationFrame(drawLoop);
}

function drawScene() {
  const sample = getActiveSample();
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);

  drawGridOverlay(width, height);
  if (sample.structure?.atoms?.length) drawProteinStructure(sample, width, height);
  else if (sample.type === "protein") drawProtein(sample, width, height);
  else drawMolecule(sample, width, height);
}

function drawGridOverlay(width, height) {
  ctx.save();
  ctx.globalAlpha = 0.2;
  ctx.strokeStyle = "#cfc4b5";
  ctx.lineWidth = 1;
  const cx = width / 2;
  const cy = height / 2;
  ctx.beginPath();
  ctx.moveTo(cx - 110, cy);
  ctx.lineTo(cx + 110, cy);
  ctx.moveTo(cx, cy - 110);
  ctx.lineTo(cx, cy + 110);
  ctx.stroke();
  ctx.restore();
}

function drawMolecule(sample, width, height) {
  const atoms = sample.atoms || buildCustomMolecule(sample.smiles || "CCO").atoms;
  const bonds = sample.bonds || [];
  const preset = VIEWER_PRESETS[state.viewerStyle] || VIEWER_PRESETS.ballstick;
  const scale = Math.min(width, height) * 0.125 * state.zoom;
  const projected = atoms.map((atom, index) => ({
    ...project(atom.x, atom.y, atom.z, width, height, scale),
    atom,
    index,
  }));
  const depths = projected.map((point) => point.z);
  const minZ = Math.min(...depths);
  const maxZ = Math.max(...depths);
  const rangeZ = Math.max(0.001, maxZ - minZ);
  projected.forEach((point) => {
    point.depth = (point.z - minZ) / rangeZ;
  });

  ctx.save();
  drawMoleculeGround(projected);
  drawRingFaces(sample.rings || [], projected, preset);
  ctx.lineCap = "round";
  bonds
    .map(([a, b, order]) => ({
      pa: projected[a],
      pb: projected[b],
      order,
      depth: ((projected[a]?.depth || 0) + (projected[b]?.depth || 0)) / 2,
    }))
    .filter((bond) => bond.pa && bond.pb)
    .sort((a, b) => a.depth - b.depth)
    .forEach((bond) => drawModernBond(bond.pa, bond.pb, bond.order, bond.depth, preset));

  projected
    .slice()
    .sort((a, b) => a.depth - b.depth)
    .forEach((point) => {
      const element = point.atom.e || "C";
      const radius = modernAtomRadius(element, point.depth, preset);
      drawModernAtom(element, point.x, point.y, radius, point.depth, preset);
      if (state.showLabels && preset.label && (element !== "C" || state.viewerStyle === "wire")) {
        drawLabel(element, point.x, point.y, radius);
      }
    });
  ctx.restore();

  drawLegend(sample.type);
}

function drawMoleculeGround(points) {
  if (!points.length || state.viewerStyle === "wire") return;
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const maxY = Math.max(...ys);
  ctx.save();
  ctx.fillStyle = "rgba(36, 35, 33, 0.08)";
  ctx.beginPath();
  ctx.ellipse((minX + maxX) / 2 + 10, maxY + 24, Math.max(60, (maxX - minX) * 0.42), 18, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawRingFaces(rings, projected, preset) {
  if (!rings.length || state.viewerStyle === "spacefill") return;
  ctx.save();
  rings.forEach((ring) => {
    const points = ring.map((index) => projected[index]).filter(Boolean);
    if (points.length < 5) return;
    const depth = points.reduce((sum, point) => sum + point.depth, 0) / points.length;
    ctx.beginPath();
    points.forEach((point, index) => {
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.closePath();
    ctx.fillStyle = `rgba(20, 125, 114, ${preset.ringAlpha * (0.7 + depth * 0.6)})`;
    ctx.strokeStyle = `rgba(20, 125, 114, ${0.18 + depth * 0.18})`;
    ctx.lineWidth = 1.2;
    ctx.fill();
    ctx.stroke();

    const center = centroid(points);
    ctx.beginPath();
    points.forEach((point, index) => {
      const x = center.x + (point.x - center.x) * 0.54;
      const y = center.y + (point.y - center.y) * 0.54;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.setLineDash([3, 6]);
    ctx.strokeStyle = `rgba(182, 106, 25, ${0.22 + depth * 0.16})`;
    ctx.stroke();
    ctx.setLineDash([]);
  });
  ctx.restore();
}

function drawModernBond(pa, pb, order, depth, preset) {
  if (state.viewerStyle === "spacefill") {
    ctx.globalAlpha = 0.32;
  }
  const isAromatic = Math.abs(order - 1.5) < 0.01;
  const offsets = order === 3 ? [-5, 0, 5] : order === 2 ? [-3.4, 3.4] : [0];
  const widthBase = state.viewerStyle === "wire" ? 2.2 : 4.4;
  const width = widthBase * preset.bondScale * (0.74 + depth * 0.38);
  offsets.forEach((offset) => {
    const normal = normalizedNormal(pa, pb, offset * preset.bondScale);
    ctx.beginPath();
    ctx.strokeStyle = `rgba(36, 35, 33, ${preset.bondAlpha * (0.58 + depth * 0.42)})`;
    ctx.lineWidth = Math.max(1.2, width);
    ctx.moveTo(pa.x + normal.x, pa.y + normal.y);
    ctx.lineTo(pb.x + normal.x, pb.y + normal.y);
    ctx.stroke();

    if (state.viewerStyle !== "wire") {
      ctx.beginPath();
      ctx.strokeStyle = `rgba(255, 253, 248, ${0.22 + depth * 0.18})`;
      ctx.lineWidth = Math.max(0.8, width * 0.26);
      ctx.moveTo(pa.x + normal.x, pa.y + normal.y - width * 0.22);
      ctx.lineTo(pb.x + normal.x, pb.y + normal.y - width * 0.22);
      ctx.stroke();
    }
  });
  if (isAromatic && state.viewerStyle !== "spacefill") {
    const normal = normalizedNormal(pa, pb, 4.2 * preset.bondScale);
    ctx.save();
    ctx.setLineDash([4, 5]);
    ctx.beginPath();
    ctx.strokeStyle = `rgba(182, 106, 25, ${0.45 + depth * 0.18})`;
    ctx.lineWidth = Math.max(1, width * 0.42);
    ctx.moveTo(pa.x + normal.x, pa.y + normal.y);
    ctx.lineTo(pb.x + normal.x, pb.y + normal.y);
    ctx.stroke();
    ctx.restore();
  }
  ctx.globalAlpha = 1;
}

function drawModernAtom(element, x, y, radius, depth, preset) {
  const base = ELEMENT_COLORS[element] || ELEMENT_COLORS.X;
  const fogged = mixHex(base, "#f6efe4", (1 - depth) * 0.3);
  const light = mixHex(fogged, "#ffffff", state.viewerStyle === "wire" ? 0.32 : 0.58);
  const dark = mixHex(fogged, "#151412", 0.22);
  const alpha = state.viewerStyle === "wire" ? 0.82 : 0.96;

  if (state.viewerStyle !== "wire") {
    ctx.beginPath();
    ctx.fillStyle = `rgba(36, 35, 33, ${0.1 + depth * 0.08})`;
    ctx.ellipse(x + radius * 0.24, y + radius * 0.38, radius * 0.88, radius * 0.38, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  const gradient = ctx.createRadialGradient(
    x - radius * 0.35,
    y - radius * 0.42,
    Math.max(1, radius * 0.08),
    x,
    y,
    radius,
  );
  gradient.addColorStop(0, light);
  gradient.addColorStop(0.48, fogged);
  gradient.addColorStop(1, dark);

  ctx.beginPath();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = gradient;
  ctx.strokeStyle = `rgba(255, 253, 248, ${0.58 + depth * 0.22})`;
  ctx.lineWidth = state.viewerStyle === "wire" ? 1.2 : 2;
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.globalAlpha = 1;

  if (state.viewerStyle === "spacefill") {
    ctx.beginPath();
    ctx.strokeStyle = `rgba(36, 35, 33, ${0.08 + depth * 0.1})`;
    ctx.lineWidth = 1;
    ctx.arc(x, y, radius * 1.03, 0, Math.PI * 2);
    ctx.stroke();
  }
}

function modernAtomRadius(element, depth, preset) {
  const base = atomRadius(element) * preset.atomScale;
  const wireMinimum = state.viewerStyle === "wire" ? 4.2 : 0;
  return Math.max(wireMinimum, base * (0.82 + depth * 0.26));
}

function drawProtein(sample, width, height) {
  const sequence = sample.sequence || sample.formula || "";
  const residues = proteinResidues(sequence);
  const scale = Math.min(width, height) * 0.08 * state.zoom;
  const points = residues.map((residue) => ({
    ...project(residue.x, residue.y, residue.z, width, height, scale),
    residue,
  }));

  ctx.save();
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  for (let i = 1; i < points.length; i += 1) {
    const prev = points[i - 1];
    const current = points[i];
    const residue = current.residue;
    ctx.beginPath();
    ctx.strokeStyle = residueColor(residue.aa);
    ctx.lineWidth = 10 + Math.max(-2, current.z * 1.4);
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(current.x, current.y);
    ctx.stroke();

    ctx.beginPath();
    ctx.strokeStyle = "rgba(255,255,255,0.58)";
    ctx.lineWidth = 2;
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(current.x, current.y);
    ctx.stroke();
  }

  points
    .filter((_, index) => index % Math.max(3, Math.floor(points.length / 18)) === 0)
    .forEach((point) => {
      ctx.beginPath();
      ctx.fillStyle = residueColor(point.residue.aa);
      ctx.strokeStyle = "#fffaf0";
      ctx.lineWidth = 2;
      ctx.arc(point.x, point.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      if (state.showLabels) drawLabel(`${point.residue.aa}${point.residue.index}`, point.x, point.y, 8);
    });
  ctx.restore();

  drawProteinSurface(points);
  drawLegend(sample.type);
}

function drawProteinStructure(sample, width, height) {
  const geometry = normalizedStructureGeometry(sample);
  const preset = VIEWER_PRESETS[state.viewerStyle] || VIEWER_PRESETS.ballstick;
  const scale = Math.min(width, height) * 0.38 * state.zoom;
  const chainColors = ["#147d72", "#b66a19", "#2f6fb0", "#b2455c", "#407a3b", "#6d4a88"];

  ctx.save();
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  geometry.backbone.forEach((chain, chainIndex) => {
    const points = chain.points.map((point) => ({
      ...project(point.x, point.y, point.z, width, height, scale),
      point,
    }));
    if (points.length < 2) return;
    ctx.beginPath();
    points.forEach((point, index) => {
      if (index === 0) ctx.moveTo(point.x, point.y);
      else ctx.lineTo(point.x, point.y);
    });
    ctx.strokeStyle = chainColors[chainIndex % chainColors.length];
    ctx.globalAlpha = state.viewerStyle === "spacefill" ? 0.35 : 0.82;
    ctx.lineWidth = state.viewerStyle === "wire" ? 2.2 : 5.5;
    ctx.stroke();
    ctx.globalAlpha = 1;

    if (state.showLabels && points.length) {
      const step = Math.max(10, Math.floor(points.length / 8));
      points.filter((_, index) => index % step === 0).forEach((point) => {
        drawLabel(`${chain.chain}:${point.point.aa}${point.point.resSeq}`, point.x, point.y, 3);
      });
    }
  });

  const projectedAtoms = geometry.atoms.map((atom) => ({
    ...project(atom.x, atom.y, atom.z, width, height, scale),
    atom,
  }));
  const stride = state.viewerStyle === "wire" ? Math.max(1, Math.ceil(projectedAtoms.length / 4000)) : 1;
  projectedAtoms
    .filter((point, index) => point.atom.hetero || index % stride === 0)
    .sort((a, b) => a.z - b.z)
    .forEach((point) => {
      const hetero = point.atom.hetero;
      const radius = hetero ? 4.8 : state.viewerStyle === "spacefill" ? 3.8 : state.viewerStyle === "wire" ? 1.25 : 2.25;
      ctx.beginPath();
      ctx.fillStyle = ELEMENT_COLORS[point.atom.e] || ELEMENT_COLORS.X;
      ctx.globalAlpha = hetero ? 0.98 : state.viewerStyle === "wire" ? 0.5 : 0.72;
      ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
      ctx.fill();
      if (hetero) {
        ctx.strokeStyle = "rgba(255,255,255,0.8)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });
  ctx.globalAlpha = 1;
  ctx.restore();
  drawLegend("molecule");
}

function normalizedStructureGeometry(sample) {
  if (structureGeometryCache.has(sample)) return structureGeometryCache.get(sample);
  const atoms = sample.structure?.atoms || [];
  const xs = atoms.map((atom) => Number(atom.x));
  const ys = atoms.map((atom) => Number(atom.y));
  const zs = atoms.map((atom) => Number(atom.z));
  const center = {
    x: (Math.min(...xs) + Math.max(...xs)) / 2,
    y: (Math.min(...ys) + Math.max(...ys)) / 2,
    z: (Math.min(...zs) + Math.max(...zs)) / 2,
  };
  const span = Math.max(
    Math.max(...xs) - Math.min(...xs),
    Math.max(...ys) - Math.min(...ys),
    Math.max(...zs) - Math.min(...zs),
    1,
  );
  const normalizePoint = (point) => ({
    ...point,
    x: ((Number(point.x) - center.x) * 2) / span,
    y: ((Number(point.y) - center.y) * 2) / span,
    z: ((Number(point.z) - center.z) * 2) / span,
  });
  const geometry = {
    atoms: atoms.map(normalizePoint),
    backbone: (sample.structure?.backbone || []).map((chain) => ({
      chain: chain.chain,
      points: (chain.points || []).map(normalizePoint),
    })),
  };
  structureGeometryCache.set(sample, geometry);
  return geometry;
}

function proteinResidues(sequence) {
  const residues = [];
  const length = Math.max(sequence.length, 1);
  for (let i = 0; i < length; i += 1) {
    const t = i / Math.max(1, length - 1);
    const helixAngle = i * 0.72;
    const curve = Math.sin(t * Math.PI * 2) * 0.8;
    residues.push({
      aa: sequence[i] || "X",
      index: i + 1,
      x: (t - 0.5) * 9.6,
      y: Math.sin(helixAngle) * 1.4 + curve,
      z: Math.cos(helixAngle) * 1.1 + Math.sin(t * Math.PI * 4) * 0.4,
    });
  }
  return residues;
}

function drawProteinSurface(points) {
  if (!points.length) return;
  ctx.save();
  ctx.globalAlpha = 0.14;
  ctx.fillStyle = "#147d72";
  ctx.beginPath();
  points.forEach((point, index) => {
    const y = point.y - 26 - Math.sin(index * 0.4) * 8;
    if (index === 0) ctx.moveTo(point.x, y);
    else ctx.lineTo(point.x, y);
  });
  points
    .slice()
    .reverse()
    .forEach((point, index) => {
      const y = point.y + 28 + Math.cos(index * 0.4) * 7;
      ctx.lineTo(point.x, y);
    });
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

function drawLegend(type) {
  const entries =
    type === "protein"
      ? [
          ["hydrophobic", "#b66a19"],
          ["charged", "#2f6fb0"],
          ["polar", "#147d72"],
        ]
      : [
          ["C", ELEMENT_COLORS.C],
          ["O", ELEMENT_COLORS.O],
          ["N", ELEMENT_COLORS.N],
          ["S/P", ELEMENT_COLORS.S],
        ];
  const x = 18;
  let y = 20;
  ctx.save();
  ctx.font = "12px ui-sans-serif, system-ui";
  entries.forEach(([label, color]) => {
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#4e4942";
    ctx.fillText(label, x + 12, y + 4);
    y += 20;
  });
  ctx.restore();
}

function project(x, y, z, width, height, scale) {
  const cosY = Math.cos(state.angleY);
  const sinY = Math.sin(state.angleY);
  const cosX = Math.cos(state.angleX);
  const sinX = Math.sin(state.angleX);
  const x1 = x * cosY - z * sinY;
  const z1 = x * sinY + z * cosY;
  const y1 = y * cosX - z1 * sinX;
  const z2 = y * sinX + z1 * cosX;
  const perspective = 1 / (1 + z2 * 0.04);
  return {
    x: width / 2 + x1 * scale * perspective,
    y: height / 2 + y1 * scale * perspective,
    z: z2,
  };
}

function normalizedNormal(a, b, distance) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const length = Math.hypot(dx, dy) || 1;
  return {
    x: (-dy / length) * distance,
    y: (dx / length) * distance,
  };
}

function centroid(points) {
  return points.reduce(
    (acc, point) => ({
      x: acc.x + point.x / points.length,
      y: acc.y + point.y / points.length,
    }),
    { x: 0, y: 0 },
  );
}

function mixHex(from, to, amount) {
  const a = hexToRgb(from);
  const b = hexToRgb(to);
  const mix = (start, end) => Math.round(start + (end - start) * clamp(amount, 0, 1));
  return `rgb(${mix(a.r, b.r)}, ${mix(a.g, b.g)}, ${mix(a.b, b.b)})`;
}

function hexToRgb(hex) {
  const clean = hex.replace("#", "");
  const value = Number.parseInt(clean.length === 3 ? clean.replace(/(.)/g, "$1$1") : clean, 16);
  return {
    r: (value >> 16) & 255,
    g: (value >> 8) & 255,
    b: value & 255,
  };
}

function atomRadius(element) {
  if (element === "H") return 8;
  if (element === "C") return 13;
  if (element === "O" || element === "N") return 14;
  return 15;
}

function residueColor(aa) {
  if (/^[AILMFWYV]$/.test(aa)) return "#b66a19";
  if (/^[DEKRH]$/.test(aa)) return "#2f6fb0";
  if (/^[STNQCGP]$/.test(aa)) return "#147d72";
  return "#7a746a";
}

function drawHighlight(x, y, radius) {
  ctx.beginPath();
  ctx.fillStyle = "rgba(255, 255, 255, 0.46)";
  ctx.arc(x - radius * 0.32, y - radius * 0.36, radius * 0.28, 0, Math.PI * 2);
  ctx.fill();
}

function drawLabel(text, x, y, radius) {
  ctx.save();
  ctx.font = "700 11px ui-sans-serif, system-ui";
  const width = ctx.measureText(text).width + 10;
  const lx = x + radius + 5;
  const ly = y - radius - 5;
  ctx.fillStyle = "rgba(255, 253, 248, 0.92)";
  ctx.strokeStyle = "#d8d0c4";
  roundRect(ctx, lx, ly - 15, width, 20, 5);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#242321";
  ctx.fillText(text, lx + 5, ly - 1);
  ctx.restore();
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.arcTo(x + width, y, x + width, y + height, radius);
  context.arcTo(x + width, y + height, x, y + height, radius);
  context.arcTo(x, y + height, x, y, radius);
  context.arcTo(x, y, x + width, y, radius);
  context.closePath();
}

function exportReport() {
  const sample = getActiveSample();
  const report = {
    exportedAt: new Date().toISOString(),
    sample,
    toolCalls: state.toolCalls,
    artifacts: state.artifacts,
    candidates: state.candidates,
    chat: state.chat,
    runtime: {
      mode: state.runtime.useApi ? "third-party-provider" : "local",
      model: state.runtime.useApi ? state.runtime.model : "local-skill-runtime",
      toolMode: state.runtime.toolMode,
    },
    skills: state.skills.map((skill) => ({ id: skill.id, kind: skill.kind })),
    workflowRuns: state.workflowRuns,
    workspaceFiles: state.workspaceFiles,
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `molemo-${sample.shortName.toLowerCase().replace(/\s+/g, "-")}-report.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function getActiveSample() {
  return SAMPLES.find((item) => item.id === state.activeId) || SAMPLES[0];
}

function formatSequence(sequence) {
  return escapeHtml(String(sequence || "").slice(0, 2000).replace(/(.{10})/g, "$1 ").trim());
}

function databaseRecordFields(data) {
  if (data.source === "PubChem") {
    return [
      ["CID", data.cid],
      ["Formula", data.formula],
      ["MW", data.molecular_weight],
      ["XLogP", data.xlogp],
      ["HBA / HBD", `${data.hba ?? "–"} / ${data.hbd ?? "–"}`],
      ["TPSA", data.tpsa],
    ].filter(([, value]) => value !== undefined && value !== null && value !== "");
  }
  return [
    ["Accession", data.accession],
    ["Protein", data.protein_name],
    ["Organism", data.organism],
    ["Length", data.length ? `${data.length} aa` : ""],
    ["Reviewed", data.reviewed ? "Yes" : "No"],
    ["PDB links", (data.pdb_ids || []).slice(0, 6).join(", ") || "None"],
  ].filter(([, value]) => value !== undefined && value !== null && value !== "");
}

function safeExternalUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return url.protocol === "https:" && ["pubchem.ncbi.nlm.nih.gov", "www.uniprot.org", "www.rcsb.org"].includes(url.hostname);
  } catch {
    return false;
  }
}

function formatBytes(bytes) {
  const value = Number(bytes || 0);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function pause(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
