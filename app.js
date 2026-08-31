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

const LANGUAGE_STORAGE_KEY = "molemo-language";

const UI_TEXT = {
  "zh-CN": {
    newAnalysis: "新建分析",
    data: "数据",
    resetWorkspace: "重置工作区",
    import: "导入",
    localFiles: "本地文件",
    chooseFiles: "选择 FASTA、H5AD/10x、HMM、PDB、FASTQ、VCF 或表格",
    importWorkspace: "导入本地工作区",
    toolCalls: "工具调用",
    candidateDesigns: "候选设计",
    loadedSkills: "已加载 Skills",
    currentMode: "当前模式",
    viewMode: "视图模式",
    structure: "结构",
    design: "设计",
    risk: "风险",
    language: "语言",
    model: "模型",
    modelSettings: "模型设置",
    export: "导出",
    run: "运行",
    site: "位点",
    global: "全局",
    structureScope: "结构范围",
    predictionEvidence: "预测结构证据视图",
    viewerStyle: "分子显示风格",
    toggleMotion: "暂停或继续旋转",
    toggleLabels: "显示或隐藏标签",
    zoomIn: "放大",
    zoomOut: "缩小",
    structureCanvas: "分子与蛋白质结构可视化",
    currentSelection: "当前选择",
    source: "来源",
    inspector: "检查器",
    results: "结果",
    tools: "工具",
    structureNotes: "结构注释",
    conversation: "对话",
    agentConsole: "自然语言 Agent",
    connecting: "连接中",
    questionPlaceholder: "提出一个生命科学问题…",
    send: "发送",
    connectLlm: "连接第三方 LLM",
    close: "关闭",
    enableOwnApi: "启用自带 OpenAI-compatible API",
    keyMemoryOnly: "仅保存在本页内存中",
    groundedMode: "Grounded chat（兼容不支持 tools 的模型）",
    apiNote: "Key 仅经本地服务转发给所选 provider，不写入文件。Native 模式允许模型选择 skills；Grounded 模式先在本地计算当前结构，再把必要结果发给模型。",
    cancel: "取消",
    save: "保存",
    createAnalysisPlan: "制定分析计划",
    workflow: "工作流",
    approvalNote: "计划创建后不会自动执行；请在“运行”页审阅并批准。",
    createPendingPlan: "创建待审批计划",
    workspaceReady: "研究工作区已就绪。",
    workspaceReset: "工作区已重置。",
    sampleLoaded: "已加载 {name}。",
    providerEnabledMessage: "第三方模型已启用；下一次命令将由本地 Agent 调度 skills，并把必要上下文转发给该 provider。",
    localRuntimeMessage: "已切回本地 skill runtime。",
    noToolCallsTitle: "运行记录",
    noToolCalls: "尚无工具调用。",
    noArtifactsTitle: "暂无结果",
    noArtifacts: "结构、序列比对和性质图会作为可检查产物显示在这里。",
    openStructureView: "在结构视图打开",
    openSequenceView: "在序列视图打开",
    officialRecord: "官方记录",
    openOfficialRecord: "打开官方记录",
    similarityCaution: "相似性命中是相关性证据，不单独证明共享功能或生物活性。",
    localServiceDisconnected: "本地服务未连接。",
    analysisPlans: "分析计划",
    noRuns: "尚无运行。",
    approveAndRun: "批准并运行",
    preflightReady: "预检已就绪",
    inputsValidated: "输入已验证。",
    statusPendingApproval: "待审批",
    statusPending: "等待",
    statusRunning: "运行中",
    statusCompleted: "已完成",
    statusFailed: "失败",
    statusSkipped: "跳过",
    statusCancelled: "已取消",
    files: "{count} 个文件",
    readWorkspaceFile: "读取 workspace 文件 {path}，判断内容并建议下一步分析",
    noCandidatesTitle: "候选设计",
    noCandidates: "尚无候选。",
    localScientificRuntime: "本地 scientific skill runtime",
    providerEnabled: "Provider 已启用",
    localOnly: "仅本地",
    workflowCatalogUnavailable: "本地工作流目录尚未加载。",
    localAgentReady: "{count} skills · 本地 Agent 就绪",
    localServiceStopped: "本地服务未启动",
    riskPrompt: "总结当前结构的主要风险和下一步验证",
  },
  en: {
    newAnalysis: "New analysis",
    data: "Data",
    resetWorkspace: "Reset workspace",
    import: "Import",
    localFiles: "Local files",
    chooseFiles: "Choose FASTA, H5AD/10x, HMM, PDB, FASTQ, VCF, or tabular data",
    importWorkspace: "Import to workspace",
    toolCalls: "Tool calls",
    candidateDesigns: "Candidate designs",
    loadedSkills: "Loaded skills",
    currentMode: "Current mode",
    viewMode: "View mode",
    structure: "Structure",
    design: "Design",
    risk: "Risk",
    language: "Language",
    model: "Model",
    modelSettings: "Model settings",
    export: "Export",
    run: "Run",
    site: "Site",
    global: "Global",
    structureScope: "Structure scope",
    predictionEvidence: "Predicted structure evidence",
    viewerStyle: "Molecular display style",
    toggleMotion: "Pause or resume rotation",
    toggleLabels: "Show or hide labels",
    zoomIn: "Zoom in",
    zoomOut: "Zoom out",
    structureCanvas: "Molecule and protein structure visualization",
    currentSelection: "Current selection",
    source: "Source",
    inspector: "Inspector",
    results: "Results",
    tools: "Tools",
    structureNotes: "Structure notes",
    conversation: "Conversation",
    agentConsole: "Natural-language Agent",
    connecting: "Connecting",
    questionPlaceholder: "Ask a life-science question...",
    send: "Send",
    connectLlm: "Connect a third-party LLM",
    close: "Close",
    enableOwnApi: "Use your own OpenAI-compatible API",
    keyMemoryOnly: "Kept in this page's memory only",
    groundedMode: "Grounded chat (for models without tool calling)",
    apiNote: "The key is forwarded only by the local service to the selected provider and is never written to disk. Native mode lets the model select skills; Grounded mode computes locally before sending the required results to the model.",
    cancel: "Cancel",
    save: "Save",
    createAnalysisPlan: "Create analysis plan",
    workflow: "Workflow",
    approvalNote: "Creating a plan does not run it. Review and approve it on the Run tab.",
    createPendingPlan: "Create plan for approval",
    workspaceReady: "Research workspace is ready.",
    workspaceReset: "Workspace reset.",
    sampleLoaded: "Loaded {name}.",
    providerEnabledMessage: "The third-party model is enabled. The local Agent will orchestrate skills and forward only the required context on the next command.",
    localRuntimeMessage: "Switched back to the local skill runtime.",
    noToolCallsTitle: "Run history",
    noToolCalls: "No tool calls yet.",
    noArtifactsTitle: "No results yet",
    noArtifacts: "Inspectable structure, alignment, and property artifacts will appear here.",
    openStructureView: "Open in structure view",
    openSequenceView: "Open in sequence view",
    officialRecord: "Official record",
    openOfficialRecord: "Open official record",
    similarityCaution: "Similarity hits support relatedness, but do not by themselves prove shared function or activity.",
    localServiceDisconnected: "Local service is not connected.",
    analysisPlans: "Analysis plans",
    noRuns: "No runs yet.",
    approveAndRun: "Approve and run",
    preflightReady: "Preflight ready",
    inputsValidated: "Inputs validated.",
    statusPendingApproval: "Pending approval",
    statusPending: "Pending",
    statusRunning: "Running",
    statusCompleted: "Completed",
    statusFailed: "Failed",
    statusSkipped: "Skipped",
    statusCancelled: "Cancelled",
    files: "{count} files",
    readWorkspaceFile: "Read workspace file {path}, identify its contents, and suggest the next analysis",
    noCandidatesTitle: "Candidate designs",
    noCandidates: "No candidates yet.",
    localScientificRuntime: "Local scientific skill runtime",
    providerEnabled: "Provider enabled",
    localOnly: "Local only",
    workflowCatalogUnavailable: "The local workflow catalog has not loaded.",
    localAgentReady: "{count} skills · local Agent ready",
    localServiceStopped: "Local service is not running",
    riskPrompt: "Summarize the main structural risks and the next validation steps",
  },
};

const WORKFLOW_TEXT_EN = {
  "molecule-profile": ["Molecule property profile", "Parse SMILES, calculate molecular descriptors, and generate a property chart."],
  "protein-sequence-review": ["Protein sequence review", "Calculate sequence properties and generate a residue-level hydropathy track."],
  "protein-structure-review": ["Protein structure review", "Load an RCSB experimental structure, AlphaFold DB prediction, or local atomic coordinates."],
  "protein-variant-structure-review": ["Protein variant structure site", "Locate a protein substitution in an experimental structure and review nearby residues and heteroatom groups."],
  "fastq-qc-review": ["FASTQ quality review", "Stream reads to calculate quality, GC, N, and per-cycle metrics."],
  "paired-end-dna-variant-calling": ["Paired-end DNA variant calling", "Preflight paired FASTQ files and a small reference, then create BAM/BAI, coverage, and a candidate VCF after approval."],
  "bulk-rnaseq-differential-expression": ["Bulk RNA-seq differential expression", "Preflight a raw count matrix and sample design, then run PyDESeq2 after approval."],
  "single-cell-exploratory-analysis": ["Single-cell RNA-seq exploration", "Preflight CSV/TSV, AnnData, or 10x raw counts, then run Scanpy QC, optional Scrublet, UMAP, Leiden, and marker ranking."],
  "gene-set-functional-analysis": ["Human gene-set functional analysis", "Confirm human gene mappings, then run Reactome enrichment and a STRING functional network after approval."],
  "target-evidence-review": ["Target evidence comparison", "Resolve a disease and candidate targets, then compare Open Targets genetic, clinical, expression, and literature evidence."],
  "target-ligand-bioactivity-review": ["Target-ligand bioactivity review", "Collect ChEMBL small-molecule activity for an exact UniProt target while retaining assay, endpoint, and publication context."],
  "literature-evidence-review": ["Literature evidence review", "Collect Europe PMC metadata and abstracts with an explicit query to build a traceable evidence map."],
  "public-omics-dataset-discovery": ["Public omics dataset discovery", "Find NCBI GEO Series with an explicit query and review design, sample size, assay type, and available data."],
  "geo-series-matrix-import": ["GEO Series Matrix import", "Preflight an official Series Matrix for an exact GSE, then import expression values, sample annotations, and structural QC."],
  "variant-evidence-review": ["Human variant evidence review", "Resolve one simple variant, then organize ClinVar, Ensembl VEP, and gnomAD v4 evidence after approval."],
  "clinical-trial-landscape-review": ["Clinical trial landscape", "Search ClinicalTrials.gov with explicit condition, intervention, and status filters to build a traceable translational landscape."],
  "clinical-trial-results-review": ["Clinical trial results review", "Preflight an exact NCT record, then organize posted participant flow, baseline, outcomes, and adverse events."],
  "vcf-cohort-review": ["Multi-sample VCF review", "Preflight a workspace VCF and sample metadata, then summarize variants, low-frequency calls, sample QC, and longitudinal trajectories."],
  "protein-family-conservation-review": ["Protein family site conservation", "Preflight a protein FASTA and exact reference site, then run MAFFT and review site conservation."],
  "pairwise-alignment-review": ["Pairwise sequence alignment", "Run a global protein sequence alignment and return an inspectable result."],
  "sequence-similarity-search": ["Local sequence similarity search", "Use NCBI BLAST+ to search a workspace FASTA database for related protein or nucleotide sequences."],
  "hmmer-profile-search": ["HMMER protein family search", "Preflight a local amino-acid profile HMM and protein FASTA, then run hmmsearch and organize domain coordinates."],
  "database-record-review": ["Public database record", "Retrieve a PubChem compound or UniProtKB protein record."],
};

const WORKFLOW_OPTION_EN = {
  "本地 workspace": "Local workspace",
  "不运行": "Do not run",
  "运行并保留预测细胞": "Run and retain predicted cells",
  "保留，仅标记": "Retain and flag",
  "批准后排除": "Exclude after approval",
  "排除": "Exclude",
  "包含": "Include",
  "仅当前疾病": "Current disease only",
  "包含 ontology descendants": "Include ontology descendants",
  "排除预印本": "Exclude preprints",
  "包含预印本": "Include preprints",
  "仅保留有摘要记录": "Require an abstract",
  "允许无摘要记录": "Allow records without abstracts",
  "单细胞 RNA-seq": "Single-cell RNA-seq",
  "表达芯片": "Expression microarray",
  "甲基化": "Methylation",
  "全部 GEO Series": "All GEO Series",
  "全部状态": "All statuses",
  "活跃 / 招募相关": "Active / recruiting-related",
  "已完成": "Completed",
  "干预性研究": "Interventional studies",
  "全部研究": "All studies",
  "仅 PASS / 未过滤": "PASS / unfiltered only",
  "包含非 PASS": "Include non-PASS records",
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
    notesEn:
      "Acetylsalicylic acid combines an aromatic ring, ester, and carboxylic acid. The Agent can organize property review, risk assessment, and analogue design around this anti-inflammatory scaffold.",
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
    promptsEn: [
      "Explain this molecule's drug-like properties",
      "Improve its aqueous solubility and explain the risks",
      "Propose three synthetically tractable analogue directions",
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
    notesEn:
      "Caffeine illustrates a nitrogen-rich fused heterocycle with two carbonyls, useful for natural-language interrogation, functional-group review, and property interpretation.",
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
    promptsEn: [
      "Identify caffeine's key functional groups",
      "Explain why it readily crosses the blood-brain barrier",
      "Design an analogue with lower CNS exposure",
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
    notesEn:
      "Trp-cage is a compact folding example for inspecting helices, turns, the hydrophobic core, and natural-language mutation proposals.",
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
    promptsEn: [
      "Find stability hotspots in this mini-protein",
      "Suggest three mutations to improve thermal stability",
      "Explain the hydrophobic core and surface charge distribution",
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
    notesEn:
      "This concept protein shows how an LLM Agent can turn a natural-language objective into interface designs, mutation sets, and an experimental validation plan.",
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
    promptsEn: [
      "Design interface mutations for this binder",
      "Generate an experimental validation plan",
      "Reduce aggregation risk while retaining the binding interface",
    ],
  },
];

const state = {
  language: initialLanguage(),
  activeId: "aspirin",
  activeMode: "structure",
  activeTab: "properties",
  viewerStyle: "ballstick",
  structureScope: "global",
  structureEvidenceMode: "structure",
  paeHover: null,
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
  localService: {
    loaded: false,
    connected: false,
    skillCount: 0,
  },
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
const paeCanvasCache = new WeakMap();

document.addEventListener("DOMContentLoaded", () => {
  bindElements();
  applyStaticTranslations();
  renderSampleList();
  selectSample("aspirin", { silent: true });
  bindEvents();
  resizeCanvas();
  requestAnimationFrame(drawLoop);
  loadWorkbenchMetadata();
  addUiMessage("workspaceReady");
});

function initialLanguage() {
  const saved = window.localStorage?.getItem(LANGUAGE_STORAGE_KEY);
  if (saved === "en" || saved === "zh-CN") return saved;
  return String(window.navigator?.language || "").toLowerCase().startsWith("zh") ? "zh-CN" : "en";
}

function ui(key, values = {}) {
  const dictionary = UI_TEXT[state.language] || UI_TEXT.en;
  const fallback = UI_TEXT.en[key] || key;
  return String(dictionary[key] || fallback).replace(/\{(\w+)\}/g, (_, name) => String(values[name] ?? `{${name}}`));
}

function localized(zh, en) {
  return state.language === "en" ? en : zh;
}

function localizedSampleValue(sample, key) {
  if (state.language === "en" && sample[`${key}En`] !== undefined) return sample[`${key}En`];
  return sample[key];
}

function localizedPrompts(sample) {
  return state.language === "en" && sample.promptsEn?.length ? sample.promptsEn : sample.prompts || [];
}

function workflowText(template, index) {
  if (state.language === "en") return WORKFLOW_TEXT_EN[template.id]?.[index] || template[index === 0 ? "title" : "description"] || "";
  return template[index === 0 ? "title" : "description"] || "";
}

function workflowRunText(run, index) {
  if (state.language === "en" && WORKFLOW_TEXT_EN[run.template_id]) return WORKFLOW_TEXT_EN[run.template_id][index];
  return index === 0 ? run.title || "Guided workflow" : run.objective || run.description || "";
}

function containsHan(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
}

function humanize(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function localizedWorkflowField(field) {
  if (state.language !== "en" || !containsHan(field.label)) return field.label || humanize(field.name);
  return humanize(field.name);
}

function localizedWorkflowOption(option) {
  if (state.language !== "en" || !containsHan(option.label)) return option.label;
  return WORKFLOW_OPTION_EN[option.label] || humanize(option.value);
}

function applyStaticTranslations() {
  document.documentElement.lang = state.language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = ui(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.title = ui(element.dataset.i18nTitle);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
    element.setAttribute("aria-label", ui(element.dataset.i18nAria));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = ui(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-language]").forEach((button) => {
    const active = button.dataset.language === state.language;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function setLanguage(language) {
  if (!UI_TEXT[language] || language === state.language) return;
  state.language = language;
  window.localStorage?.setItem(LANGUAGE_STORAGE_KEY, language);
  applyStaticTranslations();
  renderSampleList();
  state.candidates = initialCandidates(getActiveSample());
  renderAll();
  if (els.workflowDialog?.open) openWorkflowDialog();
}

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
    "loadAlphaFold",
    "structureEvidenceModes",
    "structureScopeModes",
    "viewerStyleControls",
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
    runAgent(localizedPrompts(sample)[0]);
  });

  els.resetWorkspace.addEventListener("click", () => {
    state.toolCalls = [];
    state.candidates = [];
    state.artifacts = [];
    state.chat = [];
    selectSample("aspirin", { silent: true });
    addUiMessage("workspaceReset");
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

  els.loadAlphaFold.addEventListener("click", () => {
    const value = els.structureInput.value.trim();
    if (!value) return;
    loadAlphaFoldStructure(value);
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
      if (button.dataset.mode === "risk") runAgent(ui("riskPrompt"));
    });
  });

  document.querySelectorAll("[data-language]").forEach((button) => {
    button.addEventListener("click", () => setLanguage(button.dataset.language));
  });

  document.querySelectorAll(".viewer-style").forEach((button) => {
    button.addEventListener("click", () => {
      state.viewerStyle = button.dataset.style;
      renderViewerStyles();
      renderHeader();
    });
  });

  document.querySelectorAll(".viewer-evidence").forEach((button) => {
    button.addEventListener("click", () => {
      state.structureEvidenceMode = button.dataset.evidenceMode;
      state.paeHover = null;
      renderStructureEvidenceModes();
      renderStructureScopeModes();
      renderHeader();
    });
  });

  document.querySelectorAll(".viewer-scope").forEach((button) => {
    button.addEventListener("click", () => {
      state.structureScope = button.dataset.structureScope;
      state.zoom = 1;
      renderStructureScopeModes();
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
    addUiMessage(state.runtime.useApi ? "providerEnabledMessage" : "localRuntimeMessage");
  });

  els.planWorkflow.addEventListener("click", openWorkflowDialog);
  els.workflowTemplate.addEventListener("change", renderWorkflowFields);
  els.createWorkflowPlan.addEventListener("click", createWorkflowPlan);

  canvas.addEventListener("pointerdown", (event) => {
    if (isPaeMode()) {
      updatePaeHover(event);
      return;
    }
    state.pointer.down = true;
    state.pointer.x = event.clientX;
    state.pointer.y = event.clientY;
    canvas.setPointerCapture(event.pointerId);
  });

  canvas.addEventListener("pointermove", (event) => {
    if (isPaeMode()) {
      updatePaeHover(event);
      return;
    }
    if (!state.pointer.down) return;
    const dx = event.clientX - state.pointer.x;
    const dy = event.clientY - state.pointer.y;
    state.angleY += dx * 0.008;
    state.angleX += dy * 0.008;
    state.pointer.x = event.clientX;
    state.pointer.y = event.clientY;
  });

  canvas.addEventListener("pointerup", (event) => {
    if (isPaeMode()) return;
    state.pointer.down = false;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
  });

  canvas.addEventListener("pointerleave", () => {
    if (!isPaeMode()) return;
    state.paeHover = null;
    renderHeader();
  });

  canvas.addEventListener(
    "wheel",
    (event) => {
      if (isPaeMode()) return;
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
        <span>${escapeHtml(localizedSampleValue(sample, "subtitle"))}</span>
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
  state.structureScope = sample.structure?.focus ? "site" : "global";
  state.structureEvidenceMode = "structure";
  state.paeHover = null;
  state.angleX = sample.type === "protein" ? -0.38 : -0.24;
  state.angleY = sample.type === "protein" ? 0.18 : 0.42;
  if (!options.keepDesigns) state.candidates = initialCandidates(sample);
  if (!options.silent) addSystemMessage(ui("sampleLoaded", { name: sample.shortName }));
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
  renderLocalStatus();
  renderSegments();
  renderViewerStyles();
  renderStructureEvidenceModes();
  renderStructureScopeModes();
}

function renderHeader() {
  const sample = getActiveSample();
  els.activeTitle.textContent = sample.name;
  els.activeType.textContent = sample.type === "protein" ? "Protein" : "Molecule";
  els.activeType.style.removeProperty("background");
  els.activeType.style.removeProperty("color");
  const preset = VIEWER_PRESETS[state.viewerStyle] || VIEWER_PRESETS.ballstick;
  if (isPaeMode(sample)) {
    const pae = sample.structure.pae;
    els.viewerLabel.textContent = "AlphaFold predicted aligned error";
    if (state.paeHover) {
      const hover = state.paeHover;
      els.selectionReadout.textContent = `${formatPaeRange(hover.rowStart, hover.rowEnd)} scored · ${formatPaeRange(hover.columnStart, hover.columnEnd)} aligned · ${hover.value.toFixed(2)} Å`;
      els.confidenceReadout.textContent = `PAE ${hover.value.toFixed(2)} Å · max ${Number(pae.max_error).toFixed(2)} Å`;
    } else {
      els.selectionReadout.textContent = `${pae.residue_count} residues · ${pae.matrix_size} × ${pae.matrix_size} display bins`;
      els.confidenceReadout.textContent = `PAE 0–${Number(pae.max_error).toFixed(2)} Å · AlphaFold DB`;
    }
  } else {
    const focus = sample.structure?.focus;
    els.viewerLabel.textContent = focus && state.structureScope === "site"
      ? `${focus.variant} experimental site context`
      : sample.structure?.atoms?.length
        ? sample.metadata?.coordinateType === "predicted"
          ? `${preset.name} AlphaFold prediction · pLDDT`
          : `${preset.name} atom-level protein structure`
        : sample.type === "protein"
          ? "protein ribbon and residue field"
          : `${preset.name} molecular view`;
    els.selectionReadout.textContent = focus
      ? `${sample.pdbId} · ${focus.chain}:${focus.observed_residue}${focus.author_residue_number} · ${focus.structure_allele} allele`
      : sample.selection;
    els.confidenceReadout.textContent = focus
      ? `${focus.contact_count} contacts ≤ ${Number(focus.contact_cutoff_angstrom).toFixed(2)} Å · author numbering`
      : sample.confidence;
  }
  els.structureInput.value = sample.metadata?.accession || sample.pdbId || sample.smiles || sample.sequence || "";
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
  els.structureNotes.textContent = localizedSampleValue(sample, "notes");

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
  localizedPrompts(sample).forEach((prompt) => {
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

function renderStructureEvidenceModes() {
  const sample = getActiveSample();
  const hasPae = Boolean(sample.structure?.pae?.matrix?.length);
  if (!hasPae) state.structureEvidenceMode = "structure";
  els.structureEvidenceModes.hidden = !hasPae;
  document.querySelectorAll(".viewer-evidence").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.evidenceMode === state.structureEvidenceMode);
  });
  const paeMode = hasPae && state.structureEvidenceMode === "pae";
  els.viewerStyleControls.hidden = paeMode;
  for (const control of [els.toggleMotion, els.toggleLabels, els.zoomIn, els.zoomOut]) {
    control.hidden = paeMode;
  }
  canvas.classList.toggle("is-pae", paeMode);
}

function renderStructureScopeModes() {
  const hasFocus = Boolean(getActiveSample().structure?.focus);
  if (!hasFocus) state.structureScope = "global";
  els.structureScopeModes.hidden = !hasFocus || isPaeMode();
  document.querySelectorAll(".viewer-scope").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.structureScope === state.structureScope);
  });
}

function isPaeMode(sample = getActiveSample()) {
  return state.structureEvidenceMode === "pae" && Boolean(sample.structure?.pae?.matrix?.length);
}

function formatPaeRange(start, end) {
  return start === end ? `residue ${start}` : `residues ${start}–${end}`;
}

function switchTab(tab) {
  state.activeTab = tab;
  const documentView = ["agent", "artifacts", "skills"].includes(tab);
  document.querySelector(".workbench")?.classList.toggle("is-document-view", documentView);
  document.querySelector(".workspace")?.classList.toggle("is-document-view", documentView);
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
    empty.innerHTML = `<span>${escapeHtml(ui("noToolCallsTitle"))}</span><p>${escapeHtml(ui("noToolCalls"))}</p>`;
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
    els.artifactList.innerHTML = `<div class="artifact-card"><span>${escapeHtml(ui("noArtifactsTitle"))}</span><p>${escapeHtml(ui("noArtifacts"))}</p></div>`;
    return;
  }

  state.artifacts
    .slice()
    .reverse()
    .forEach((artifact) => {
      const card = document.createElement("article");
      card.className = "artifact-card";
      const rawTitle = artifact.title || artifact.type || "Artifact";
      const title = escapeHtml(state.language === "en" && containsHan(rawTitle) ? humanize(artifact.type) : rawTitle);
      if (["molecule", "protein-sequence", "protein-structure"].includes(artifact.type)) {
        const sample = artifact.data || {};
        const sourceUrl = safeExternalUrl(sample.metadata?.source_url);
        const paeUrl = safeExternalUrl(sample.metadata?.pae_url);
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(artifact.type)}</span></header>
          <p>${escapeHtml(state.language === "en" && containsHan(sample.selection || sample.notes) ? "Viewer-ready scientific artifact" : sample.selection || sample.notes || "Viewer-ready scientific artifact")}</p>
          <button class="secondary-button artifact-open" type="button">${escapeHtml(ui(artifact.type === "protein-sequence" ? "openSequenceView" : "openStructureView"))}</button>
          ${sourceUrl || paeUrl ? `<div class="artifact-source-links">
            ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">${escapeHtml(ui("officialRecord"))}</a>` : ""}
            ${paeUrl ? `<a class="source-link" href="${escapeHtml(paeUrl)}" target="_blank" rel="noreferrer">PAE</a>` : ""}
          </div>` : ""}
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
          ${safeExternalUrl(data.source_url) ? `<a class="source-link" href="${escapeHtml(data.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(ui("openOfficialRecord"))}</a>` : ""}
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
      } else if (artifact.type === "dna-variant-calling-preflight") {
        card.classList.add("dna-variant-artifact");
        card.innerHTML = renderDnaVariantPreflight(title, artifact.data || {});
      } else if (artifact.type === "dna-variant-calling") {
        card.classList.add("dna-variant-artifact");
        card.innerHTML = renderDnaVariantCalling(title, artifact.data || {});
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
      } else if (artifact.type === "protein-conservation-preflight") {
        card.classList.add("protein-conservation-artifact");
        card.innerHTML = renderProteinConservationPreflight(title, artifact.data || {});
      } else if (artifact.type === "protein-conservation-review") {
        card.classList.add("protein-conservation-artifact");
        card.innerHTML = renderProteinConservationReview(title, artifact.data || {});
      } else if (artifact.type === "sequence-search") {
        const data = artifact.data || {};
        const hits = data.hits || [];
        card.innerHTML = `
          <header><strong>${title}</strong><span>${escapeHtml(`${data.program || "blast"} · ${data.task || "default"}`)}</span></header>
          <div class="search-overview">
            ${[
              ["Query", `${data.query_length || 0} ${data.program === "blastn" ? "nt" : "aa"}`],
              ["Database", `${data.database_sequences || 0} sequences`],
              ["Hits", data.hit_count || 0],
              ["Engine", `${data.engine || "NCBI BLAST+"} ${data.version || ""}`.trim()],
            ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
          </div>
          <p class="search-database">${escapeHtml(data.database_path || "Workspace FASTA")}</p>
          <div class="search-hits">
            ${hits.length ? hits.map((hit, index) => `
              <details class="search-hit" ${index === 0 ? "open" : ""}>
                <summary>
                  <span class="search-hit-name"><strong>${escapeHtml(hit.title || hit.id || `Hit ${index + 1}`)}</strong><small>${escapeHtml(hit.accession || hit.id || "")}</small></span>
                  <span class="search-hit-stats">
                    <span><b>${escapeHtml(hit.identity_percent || 0)}%</b> identity</span>
                    <span><b>${escapeHtml(hit.query_coverage_percent || 0)}%</b> coverage</span>
                    <span><b>${escapeHtml(formatScientific(hit.evalue))}</b> E-value</span>
                    <span><b>${escapeHtml(hit.bit_score || 0)}</b> bit score</span>
                  </span>
                </summary>
                <div class="search-alignment">
                  <code>Query ${escapeHtml(hit.query_from || 0)}  ${escapeHtml(hit.query_alignment || "")}  ${escapeHtml(hit.query_to || 0)}</code>
                  <code class="alignment-markers">${escapeHtml(" ".repeat(9) + (hit.midline || ""))}</code>
                  <code>Hit  ${escapeHtml(hit.hit_from || 0)}  ${escapeHtml(hit.hit_alignment || "")}  ${escapeHtml(hit.hit_to || 0)}</code>
                </div>
              </details>
            `).join("") : '<p class="search-empty">No hits passed the selected E-value threshold.</p>'}
          </div>
          <p>${escapeHtml(ui("similarityCaution"))}</p>
        `;
      } else if (artifact.type === "hmmer-profile-preflight") {
        card.innerHTML = renderHmmerProfilePreflight(title, artifact.data || {});
      } else if (artifact.type === "hmmer-profile-search") {
        card.classList.add("hmmer-profile-artifact");
        card.innerHTML = renderHmmerProfileSearch(title, artifact.data || {});
      } else if (artifact.type === "rnaseq-preflight") {
        card.innerHTML = renderRnaseqPreflight(title, artifact.data || {});
      } else if (artifact.type === "transcriptomics-de") {
        card.innerHTML = renderTranscriptomicsResult(title, artifact.data || {});
      } else if (artifact.type === "single-cell-preflight") {
        card.innerHTML = renderSingleCellPreflight(title, artifact.data || {});
      } else if (artifact.type === "single-cell-analysis") {
        const data = artifact.data || {};
        card.classList.add("single-cell-analysis-artifact");
        card.innerHTML = renderSingleCellAnalysis(title, data);
        bindSingleCellControls(card, data);
      } else if (artifact.type === "functional-analysis-preflight") {
        card.innerHTML = renderFunctionalAnalysisPreflight(title, artifact.data || {});
      } else if (artifact.type === "functional-analysis") {
        card.classList.add("functional-analysis-artifact");
        card.innerHTML = renderFunctionalAnalysis(title, artifact.data || {});
      } else if (artifact.type === "target-evidence-preflight") {
        card.innerHTML = renderTargetEvidencePreflight(title, artifact.data || {});
      } else if (artifact.type === "target-evidence-review") {
        card.classList.add("target-evidence-artifact");
        card.innerHTML = renderTargetEvidenceReview(title, artifact.data || {});
      } else if (artifact.type === "chembl-bioactivity-preflight") {
        card.classList.add("chembl-bioactivity-artifact");
        card.innerHTML = renderChemblBioactivityPreflight(title, artifact.data || {});
      } else if (artifact.type === "chembl-bioactivity-review") {
        const data = artifact.data || {};
        card.classList.add("chembl-bioactivity-artifact");
        card.innerHTML = renderChemblBioactivityReview(title, data);
        bindChemblBioactivityActions(card);
      } else if (artifact.type === "variant-structure-preflight") {
        const data = artifact.data || {};
        card.classList.add("variant-structure-artifact");
        card.innerHTML = renderVariantStructureReview(title, data, true);
        bindVariantStructureActions(card, data);
      } else if (artifact.type === "variant-structure-review") {
        const data = artifact.data || {};
        card.classList.add("variant-structure-artifact");
        card.innerHTML = renderVariantStructureReview(title, data, false);
        bindVariantStructureActions(card, data);
      } else if (["geo-dataset-preview", "geo-dataset-landscape"].includes(artifact.type)) {
        const data = artifact.data || {};
        card.classList.add("geo-dataset-artifact");
        card.innerHTML = renderGeoDatasetLandscape(title, data, artifact.type === "geo-dataset-preview");
        bindGeoDatasetActions(card);
      } else if (["geo-series-matrix-preflight", "geo-series-matrix-import"].includes(artifact.type)) {
        const data = artifact.data || {};
        card.classList.add("geo-dataset-artifact", "geo-matrix-artifact");
        card.innerHTML = renderGeoSeriesMatrix(title, data, artifact.type === "geo-series-matrix-preflight");
        bindGeoSeriesMatrixActions(card);
      } else if (artifact.type === "literature-evidence-map") {
        card.classList.add("literature-evidence-artifact");
        card.innerHTML = renderLiteratureEvidenceMap(title, artifact.data || {});
      } else if (artifact.type === "clinical-trial-landscape") {
        card.classList.add("clinical-trials-artifact");
        card.innerHTML = renderClinicalTrialLandscape(title, artifact.data || {});
      } else if (artifact.type === "clinical-trial-results-preflight") {
        card.innerHTML = renderClinicalTrialResultsPreflight(title, artifact.data || {});
      } else if (artifact.type === "clinical-trial-results") {
        card.classList.add("clinical-results-artifact");
        card.innerHTML = renderClinicalTrialResults(title, artifact.data || {});
      } else if (artifact.type === "vcf-cohort-preflight") {
        card.innerHTML = renderVcfCohortPreflight(title, artifact.data || {});
      } else if (artifact.type === "vcf-cohort-review") {
        card.classList.add("vcf-cohort-artifact");
        card.innerHTML = renderVcfCohortReview(title, artifact.data || {});
      } else if (artifact.type === "variant-evidence-preflight") {
        card.innerHTML = renderVariantEvidencePreflight(title, artifact.data || {});
      } else if (artifact.type === "variant-evidence-review") {
        card.classList.add("variant-evidence-artifact");
        card.innerHTML = renderVariantEvidenceReview(title, artifact.data || {});
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

function renderProteinConservationPreflight(title, data) {
  const reference = data.reference || {};
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${data.engine || "MAFFT"} ${data.version || ""}`.trim())}</span></header>
    <div class="conservation-reference-line">
      <span>Reference</span>
      <code>${escapeHtml(reference.id || data.inputs?.reference_id || "")}</code>
      <strong>${escapeHtml(reference.site || data.inputs?.site || "")}</strong>
    </div>
    <div class="conservation-metrics conservation-preflight-metrics">
      ${[
        ["Sequences", data.sequence_count || 0],
        ["Residues", Number(data.total_residues || 0).toLocaleString("en-US")],
        ["Reference length", `${reference.length || 0} aa`],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="conservation-input-list">
      ${(data.records || []).map((record) => `<div><code>${escapeHtml(record.id)}</code><span>${escapeHtml(`${record.length || 0} aa`)}</span></div>`).join("")}
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Confirm the sequence set, exact reference ID and site before execution.")}</p>
  `;
}

function renderProteinConservationReview(title, data) {
  const site = data.site || {};
  const display = data.display || {};
  const bins = data.conservation_track?.bins || [];
  const sequences = data.sequences || [];
  const sequenceById = new Map(sequences.map((sequence) => [sequence.id, sequence]));
  const matching = site.matching_sequence_count || 0;
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${data.engine || "MAFFT"} ${data.version || ""}`.trim())}</span></header>
    <div class="conservation-reference-line">
      <span>Reference</span>
      <code>${escapeHtml(site.reference_id || data.inputs?.reference_id || "")}</code>
      <strong>${escapeHtml(site.label || data.inputs?.site || "")}</strong>
    </div>
    <div class="conservation-metrics">
      ${[
        ["Sequences", data.sequence_count || 0],
        ["Alignment", `${data.alignment_length || 0} columns`],
        ["Site column", site.alignment_column || 0],
        ["Site consensus", `${site.consensus_residue || "-"} · ${matching}/${data.sequence_count || 0}`],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <section class="conservation-section">
      <header><strong>Alignment overview</strong><span>mean consensus support per ${escapeHtml(data.conservation_track?.bin_size || 1)} column bin</span></header>
      <div class="conservation-track" role="img" aria-label="Alignment-wide consensus support; reference site is marked">
        ${bins.map((bin) => `<i class="${bin.contains_site ? "is-site" : ""}" style="--support:${clamp(Number(bin.mean_consensus_support || 0) * 100, 2, 100)}%" title="Columns ${escapeHtml(bin.start_column)}–${escapeHtml(bin.end_column)} · support ${escapeHtml(formatPercent(bin.mean_consensus_support))}"></i>`).join("")}
      </div>
      <div class="conservation-track-axis"><span>1</span><span>${escapeHtml(data.alignment_length || 0)}</span></div>
    </section>
    <section class="conservation-section">
      <header><strong>Reference-site window</strong><span>columns ${escapeHtml(display.start_column || 0)}–${escapeHtml(display.end_column || 0)}</span></header>
      <div class="conservation-alignment-scroll">
        <div class="conservation-alignment">
          ${(display.sequences || []).map((sequence) => `<div class="conservation-alignment-row">
            <code class="conservation-sequence-id">${escapeHtml(sequence.id)}</code>
            <code class="conservation-sequence">${renderConservationSequence(sequence.aligned_sequence || "", display.consensus || "", display.site_offset)}</code>
          </div>`).join("")}
          <div class="conservation-alignment-row is-consensus">
            <code class="conservation-sequence-id">Consensus</code>
            <code class="conservation-sequence">${renderConservationSequence(display.consensus || "", display.consensus || "", display.site_offset)}</code>
          </div>
        </div>
      </div>
    </section>
    <section class="conservation-section">
      <header><strong>Site observations</strong><span>${escapeHtml(formatPercent(site.consensus_support))} support · ${escapeHtml(formatPercent(site.occupancy))} occupancy</span></header>
      <div class="conservation-observations">
        ${(site.observations || []).map((observation) => {
          const sequence = sequenceById.get(observation.sequence_id) || {};
          return `<div>
            <code>${escapeHtml(observation.sequence_id)}</code>
            <strong>${escapeHtml(observation.residue || "-")}</strong>
            <span>${escapeHtml(formatPercent(sequence.identity_to_reference))} identity</span>
            <small>${escapeHtml(conservationStatusLabel(observation.status))}</small>
          </div>`;
        }).join("")}
      </div>
    </section>
    <div class="conservation-footer">
      <code>${escapeHtml(data.outputs?.alignment || "")}</code>
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Conservation describes only the approved input sequence set.")}</p>
    </div>
  `;
}

function renderConservationSequence(sequence, consensus, siteOffset) {
  return String(sequence || "")
    .split("")
    .map((residue, index) => {
      const classes = [];
      if (index === Number(siteOffset)) classes.push("is-site");
      if (residue !== "-" && consensus[index] && residue !== consensus[index]) classes.push("is-mismatch");
      return `<span class="${classes.join(" ")}">${escapeHtml(residue)}</span>`;
    })
    .join("");
}

function conservationStatusLabel(status) {
  return ({ match: "match", substitution: "substitution", gap: "gap", unknown: "unknown" })[status] || status || "";
}

function renderHmmerProfilePreflight(title, data) {
  const thresholds = data.thresholds || {};
  const models = data.models || [];
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${data.engine || "HMMER"} ${data.version || ""}`.trim())}</span></header>
    <div class="hmmer-input-line">
      <span>Profile</span>
      <code>${escapeHtml(data.hmm_path || "")}</code>
      <small>${escapeHtml(data.database_path || "")}</small>
    </div>
    <div class="hmmer-metrics">
      ${[
        ["Models", data.model_count || 0],
        ["Sequences", data.sequence_count || 0],
        ["Residues", Number(data.residue_count || 0).toLocaleString("en-US")],
        ["Max hits", thresholds.max_hits || 0],
        ["Engine", data.version || "n/a"],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="hmmer-model-list">
      ${models.map((model) => `<div><strong>${escapeHtml(model.name)}</strong><span>${escapeHtml(`${model.length} aa · ${model.accession || "no accession"}`)}</span></div>`).join("")}
    </div>
    <div class="hmmer-filter-line">
      <span>Sequence E ≤ ${escapeHtml(formatScientific(thresholds.sequence_evalue))}</span>
      <span>Domain c-E ≤ ${escapeHtml(formatScientific(thresholds.domain_evalue))}</span>
      <span>${escapeHtml(thresholds.threads || 1)} thread(s)</span>
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Review the profile, database and thresholds before execution.")}</p>
  `;
}

function renderHmmerProfileSearch(title, data) {
  const hits = data.hits || [];
  const domains = data.domains || [];
  const inputs = data.inputs || {};
  return `
    <header><strong>${title}</strong><span>${escapeHtml(formatTimestamp(data.retrieved_at))}</span></header>
    <div class="hmmer-input-line">
      <span>HMMER ${escapeHtml(data.version || "3")}</span>
      <code>${escapeHtml(inputs.hmm_path || "")}</code>
      <small>${escapeHtml(inputs.database_path || "")}</small>
    </div>
    <div class="hmmer-metrics">
      ${[
        ["Models", data.model_count || 0],
        ["Sequences", data.database_sequence_count || 0],
        ["Residues", Number(data.database_residue_count || 0).toLocaleString("en-US")],
        ["Hits", data.reported_hit_count || 0],
        ["Domains", data.reported_domain_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="hmmer-filter-line">
      <span>Sequence E ≤ ${escapeHtml(formatScientific(inputs.evalue))}</span>
      <span>Domain c-E ≤ ${escapeHtml(formatScientific(inputs.domain_evalue))}</span>
      <span>Top ${escapeHtml(inputs.max_hits || 0)} profile-target pairs</span>
    </div>
    <section class="hmmer-section">
      <header><strong>Domain architecture</strong><span>target alignment coordinates</span></header>
      <div class="hmmer-architectures">
        ${hits.slice(0, 25).map((hit) => renderHmmerArchitecture(hit)).join("") || '<p class="hmmer-empty">No profile-target hits met the approved reporting thresholds.</p>'}
      </div>
    </section>
    <section class="hmmer-section">
      <header><strong>Reported domains</strong><span>conditional and independent E-values</span></header>
      <div class="hmmer-domain-table">
        <div><b>Target / model</b><b>Target span</b><b>HMM span</b><b>c-Evalue</b><b>i-Evalue</b><b>Score</b><b>Acc</b></div>
        ${domains.slice(0, 100).map((domain) => `<div>
          <strong>${escapeHtml(domain.target_name)}<small>${escapeHtml(domain.query_name)}</small></strong>
          <code>${escapeHtml(`${domain.alignment_from}–${domain.alignment_to}`)}</code>
          <code>${escapeHtml(`${domain.hmm_from}–${domain.hmm_to}`)}</code>
          <span>${escapeHtml(formatScientific(domain.conditional_evalue))}</span>
          <span>${escapeHtml(formatScientific(domain.independent_evalue))}</span>
          <span>${escapeHtml(domain.domain_score)}</span>
          <span>${escapeHtml(domain.accuracy)}</span>
        </div>`).join("")}
      </div>
    </section>
    <div class="hmmer-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "HMMER profile matches require profile, search-space and functional review.")}</p>
      <div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>
    </div>
  `;
}

function renderHmmerArchitecture(hit) {
  const length = Math.max(1, Number(hit.target_length || 1));
  const domains = hit.domains || [];
  return `
    <article class="hmmer-architecture">
      <div class="hmmer-target-name">
        <strong>${escapeHtml(hit.target_name || "Target")}</strong>
        <small>${escapeHtml(`${length} aa · ${hit.target_description || ""}`)}</small>
      </div>
      <div class="hmmer-track-wrap">
        <div class="hmmer-domain-track">
          ${domains.map((domain) => {
            const left = clamp(((Number(domain.alignment_from || 1) - 1) / length) * 100, 0, 100);
            const width = clamp(((Number(domain.alignment_to || 1) - Number(domain.alignment_from || 1) + 1) / length) * 100, 1, 100 - left);
            const title = `${domain.query_name} · target ${domain.alignment_from}–${domain.alignment_to} · HMM ${domain.hmm_from}–${domain.hmm_to} · i-E ${formatScientific(domain.independent_evalue)}`;
            return `<i style="left:${left}%;width:${width}%" title="${escapeHtml(title)}"><span>${escapeHtml(domain.query_name)}</span></i>`;
          }).join("")}
        </div>
        <div class="hmmer-track-axis"><span>1</span><span>${escapeHtml(length)}</span></div>
      </div>
      <div class="hmmer-hit-stats">
        <strong>${escapeHtml(formatScientific(hit.full_evalue))}</strong>
        <span>${escapeHtml(hit.full_score)} bits · ${escapeHtml(hit.domain_count)} domain(s)</span>
      </div>
    </article>
  `;
}

function renderTargetEvidencePreflight(title, data) {
  const disease = data.disease || {};
  const targets = data.targets || [];
  return `
    <header><strong>${title}</strong><span>entity resolution</span></header>
    <div class="target-preflight-entity">
      <span>Disease</span>
      <strong>${escapeHtml(disease.name || disease.query || "n/a")}</strong>
      <code>${escapeHtml(disease.id || "")}</code>
    </div>
    <div class="target-resolved-list">
      ${targets.map((target) => `
        <div><span>${escapeHtml(target.query || target.symbol)}</span><strong>${escapeHtml(target.symbol || target.name)}</strong><code>${escapeHtml(target.id)}</code></div>
      `).join("")}
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Entities resolved. Review them before execution.")}</p>
  `;
}

function renderChemblBioactivityPreflight(title, data) {
  const target = data.target || {};
  const retrieval = data.retrieval || {};
  const inputs = data.inputs || {};
  const database = data.database || {};
  const targetUrl = safeExternalUrl(target.url) ? target.url : "";
  return `
    <header><strong>${title}</strong><span>${escapeHtml(database.version || "ChEMBL")}</span></header>
    <div class="chembl-target-line">
      <span>Target</span>
      <strong>${escapeHtml(target.pref_name || "n/a")}</strong>
      <code>${escapeHtml([target.accession, target.target_chembl_id].filter(Boolean).join(" · "))}</code>
    </div>
    <div class="chembl-metrics">
      ${[
        ["Source matches", Number(retrieval.source_total_count || 0).toLocaleString("en-US")],
        ["Preview activities", retrieval.reported_activities || 0],
        ["Compounds", retrieval.reported_compounds || 0],
        ["Confidence", "9 · direct"],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="chembl-filter-line">
      <span>${escapeHtml(chemblAssayScopeLabel(inputs.assay_scope))}</span>
      <span>pChEMBL ≥ ${escapeHtml(inputs.min_pchembl)}</span>
      <span>Approved max ${escapeHtml(data.requested_max_activities || inputs.max_activities || 0)}</span>
      <span>${escapeHtml(database.release_date || "release date unavailable")}</span>
    </div>
    <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "pChEMBL is not a probability or lead-quality score.")}</p>
    ${targetUrl ? `<a class="source-link" href="${escapeHtml(targetUrl)}" target="_blank" rel="noreferrer">Open ChEMBL target</a>` : ""}
  `;
}

function renderChemblBioactivityReview(title, data) {
  const target = data.target || {};
  const retrieval = data.retrieval || {};
  const inputs = data.inputs || {};
  const database = data.database || {};
  const compounds = data.compounds || [];
  const activities = data.activities || [];
  const targetUrl = safeExternalUrl(target.url) ? target.url : "";
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${database.version || "ChEMBL"} · ${formatTimestamp(data.retrieved_at)}`)}</span></header>
    <div class="chembl-target-line">
      <span>Target</span>
      <strong>${escapeHtml(target.pref_name || "n/a")}</strong>
      <code>${escapeHtml([target.accession, target.target_chembl_id, target.organism].filter(Boolean).join(" · "))}</code>
    </div>
    <div class="chembl-metrics">
      ${[
        ["Activities", retrieval.reported_activities || activities.length],
        ["Compounds", retrieval.reported_compounds || compounds.length],
        ["Source matches", Number(retrieval.source_total_count || 0).toLocaleString("en-US")],
        ["Confidence", "9 · direct"],
        ["Min pChEMBL", inputs.min_pchembl],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="chembl-filter-line">
      <span>${escapeHtml(chemblAssayScopeLabel(inputs.assay_scope))}</span>
      <span>${retrieval.truncated ? "Bounded potency-ordered sample" : "Complete filtered set"}</span>
      <span>${escapeHtml(database.release_date || "release date unavailable")}</span>
    </div>
    <section class="chembl-section">
      <header><strong>Compounds</strong><span>grouped within retrieved evidence</span></header>
      <div class="chembl-table-scroll">
        <table class="chembl-compound-table">
          <thead><tr><th>Rank</th><th>Compound</th><th>Max pChEMBL</th><th>Endpoints</th><th>Rows</th><th>Structure</th></tr></thead>
          <tbody>${compounds.slice(0, 50).map((compound) => `<tr>
            <td>${escapeHtml(compound.rank)}</td>
            <th scope="row"><a href="${escapeHtml(safeExternalUrl(compound.url) || "#")}" target="_blank" rel="noreferrer">${escapeHtml(compound.name || compound.molecule_chembl_id)}</a><small>${escapeHtml(compound.molecule_chembl_id)}</small></th>
            <td><strong>${escapeHtml(compound.max_pchembl)}</strong></td>
            <td>${escapeHtml((compound.endpoint_types || []).join(", ") || "n/a")}</td>
            <td>${escapeHtml(compound.retrieved_activity_count || 0)}</td>
            <td><button class="secondary-button chembl-open-structure" type="button" data-smiles="${escapeHtml(compound.canonical_smiles || "")}" title="${escapeHtml(ui("openStructureView"))}">${escapeHtml(localized("打开", "Open"))}</button></td>
          </tr>`).join("") || '<tr><td colspan="6">No compounds passed the approved filters.</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    <section class="chembl-section">
      <header><strong>Activity evidence</strong><span>endpoint and assay context retained</span></header>
      <div class="chembl-table-scroll">
        <table class="chembl-activity-table">
          <thead><tr><th>Rank</th><th>Compound</th><th>pChEMBL</th><th>Measurement</th><th>Assay</th><th>Format</th><th>Document</th></tr></thead>
          <tbody>${activities.map((activity) => `<tr>
            <td>${escapeHtml(activity.rank)}</td>
            <th scope="row"><a href="${escapeHtml(safeExternalUrl(activity.molecule_url) || "#")}" target="_blank" rel="noreferrer">${escapeHtml(activity.molecule_name || activity.molecule_chembl_id)}</a><small>${escapeHtml(activity.molecule_chembl_id)}</small></th>
            <td><strong>${escapeHtml(activity.pchembl_value)}</strong></td>
            <td><span>${escapeHtml(activity.standard_type || "n/a")}</span><small>${escapeHtml([activity.standard_relation, activity.standard_value, activity.standard_units].filter(Boolean).join(" "))}</small></td>
            <td><a href="${escapeHtml(safeExternalUrl(activity.assay_url) || "#")}" target="_blank" rel="noreferrer">${escapeHtml(activity.assay_chembl_id)}</a><small>${escapeHtml(activity.assay_type_label || activity.assay_type || "")}</small></td>
            <td><span>${escapeHtml(activity.bao_label || activity.bao_format || "n/a")}</span><small title="${escapeHtml(activity.assay_description || "")}">${escapeHtml(activity.assay_description || "")}</small></td>
            <td><span>${escapeHtml(activity.document_chembl_id || "n/a")}</span><small>${escapeHtml([activity.document_journal, activity.document_year].filter(Boolean).join(" · "))}</small></td>
          </tr>`).join("") || '<tr><td colspan="7">No activity records passed the approved filters.</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    <div class="target-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[2] || "Confidence score 9 does not prove direct physical binding or assay quality.")}</p>
      <div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>
      ${targetUrl ? `<a class="source-link" href="${escapeHtml(targetUrl)}" target="_blank" rel="noreferrer">Open ChEMBL target</a>` : ""}
    </div>
  `;
}

function chemblAssayScopeLabel(scope) {
  return ({ binding: "Binding", functional: "Functional", binding_functional: "Binding + functional" })[scope] || "Binding + functional";
}

function bindChemblBioactivityActions(card) {
  card.querySelectorAll(".chembl-open-structure").forEach((button) => {
    button.addEventListener("click", async () => {
      const smiles = String(button.dataset.smiles || "");
      if (!smiles) return;
      button.disabled = true;
      try {
        await loadCustomMolecule(smiles);
        switchTab("properties");
      } finally {
        button.disabled = false;
      }
    });
  });
}

function renderVariantStructureReview(title, data, preview = false) {
  const entry = data.entry || {};
  const site = data.site || {};
  const proteinContacts = site.protein_contacts || [];
  const heteroContacts = site.hetero_contacts || [];
  const rawSourceUrl = data.source_url || entry.source_url || "";
  const sourceUrl = safeExternalUrl(rawSourceUrl) ? rawSourceUrl : "";
  return `
    <header><strong>${title}</strong><span>${escapeHtml(preview ? "preflight" : formatTimestamp(data.retrieved_at))}</span></header>
    <div class="variant-structure-site">
      <span>Author residue</span>
      <strong>${escapeHtml(`${site.chain || "?"}:${site.observed_residue || "?"}${site.author_residue_number || "?"}`)}</strong>
      <code>${escapeHtml(`${entry.pdb_id || "PDB"} · ${site.variant || "variant"} · ${site.structure_allele || "unresolved"} allele`)}</code>
    </div>
    <div class="variant-structure-metrics">
      ${[
        ["Resolution", entry.resolution_angstrom ? `${entry.resolution_angstrom} Å` : "n/a"],
        ["Nonlocal protein", site.nonlocal_protein_contact_count ?? site.protein_contact_count ?? 0],
        ["Hetero groups", site.hetero_contact_count || 0],
        ["Cutoff", `${Number(site.contact_cutoff_angstrom || 0).toFixed(2)} Å`],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="variant-structure-entry-line">
      <span>${escapeHtml((entry.methods || []).join(", ") || "experimental coordinates")}</span>
      <span>${escapeHtml(entry.release_date || "release date unavailable")}</span>
      <span>first coordinate model</span>
    </div>
    <section class="variant-structure-section">
      <header><strong>Coordinate groups near the site</strong><span>nearest heavy-atom pair</span></header>
      <div class="variant-structure-contact-list">
        ${heteroContacts.slice(0, 25).map((contact) => `<div>
          <strong>${escapeHtml(contact.instance_id)}</strong>
          <code>${escapeHtml(`${contact.focus_atom} · ${contact.contact_atom}`)}</code>
          <span>${escapeHtml(`${Number(contact.min_distance_angstrom).toFixed(3)} Å${contact.short_contact_below_2_1_angstrom ? " · short contact" : ""}`)}</span>
        </div>`).join("") || "<p>No coordinate hetero group falls within the approved cutoff.</p>"}
      </div>
    </section>
    <section class="variant-structure-section">
      <header><strong>Protein environment</strong><span>author residue numbering</span></header>
      <div class="variant-structure-protein-list">
        ${proteinContacts.slice(0, 40).map((contact) => `<span><strong>${escapeHtml(`${contact.chain}:${contact.residue}${contact.resSeq}`)}</strong><code>${escapeHtml(`${contact.focus_atom}–${contact.contact_atom}`)}</code><b>${escapeHtml(`${Number(contact.min_distance_angstrom).toFixed(3)} Å${contact.sequence_relation === "sequence-adjacent" ? " · adjacent" : ""}`)}</b></span>`).join("") || "<p>No protein residue falls within the approved cutoff.</p>"}
      </div>
    </section>
    <div class="variant-structure-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Geometric proximity in one deposited model is not a functional or energetic conclusion.")}</p>
      ${preview ? "" : `<div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>`}
      <div class="variant-structure-actions">
        ${data.sample ? `<button class="secondary-button variant-structure-open" type="button">${escapeHtml(localized("在位点视图打开", "Open in site view"))}</button>` : ""}
        ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open RCSB entry</a>` : ""}
      </div>
    </div>
  `;
}

function bindVariantStructureActions(card, data) {
  card.querySelector(".variant-structure-open")?.addEventListener("click", () => {
    const sample = data.sample;
    if (!sample?.type) return;
    upsertCustomSample(sample);
    selectSample(sample.id, { keepDesigns: true });
    state.structureScope = "site";
    switchTab("properties");
    renderAll();
  });
}

function renderFunctionalAnalysisPreflight(title, data) {
  const organism = data.organism || {};
  const mappings = data.mappings || [];
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${organism.name || "Homo sapiens"} · ${organism.taxon_id || 9606}`)}</span></header>
    <div class="functional-preflight-summary">
      <div><span>Input</span><strong>${escapeHtml((data.input_terms || []).length)}</strong></div>
      <div><span>Mapped</span><strong>${escapeHtml(data.mapped_count || 0)}</strong></div>
      <div><span>Unmapped</span><strong>${escapeHtml((data.unmapped_terms || []).length)}</strong></div>
      <div><span>STRING score</span><strong>${escapeHtml(data.parameters?.required_score || 400)}</strong></div>
      <div><span>FDR</span><strong>${escapeHtml(data.parameters?.fdr_threshold || 0.05)}</strong></div>
    </div>
    <div class="functional-mapping-list">
      ${mappings.map((mapping) => `
        <div>
          <code>${escapeHtml(mapping.query)}</code>
          <strong>${escapeHtml(mapping.preferred_name)}</strong>
          <span>${escapeHtml(mapping.string_id)}</span>
        </div>
      `).join("")}
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Review organism, mappings and thresholds before approval.")}</p>
  `;
}

function renderFunctionalAnalysis(title, data) {
  const reactome = data.reactome || {};
  const network = data.network || {};
  const ppi = data.ppi_enrichment || {};
  const enrichment = data.string_enrichment || {};
  const pathways = reactome.pathways || [];
  const terms = enrichment.terms || [];
  const sources = (data.sources || []).filter((source) => safeExternalUrl(source.url));
  return `
    <header><strong>${title}</strong><span>${escapeHtml(formatTimestamp(data.retrieved_at))}</span></header>
    <div class="functional-metrics">
      ${[
        ["Input", (data.input_terms || []).length],
        ["Mapped", data.mapped_count || 0],
        ["Reactome", reactome.significant_count || 0],
        ["Edges", network.available === false ? "n/a" : network.edge_count || 0],
        ["PPI P", ppi.available === false ? "n/a" : formatScientific(ppi.p_value)],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="functional-analysis-grid">
      <section class="functional-network-section">
        <header><strong>STRING functional network</strong><span>${escapeHtml(`score ≥ ${network.required_score || 400}`)}</span></header>
        ${renderFunctionalNetwork(network.nodes || [], network.edges || [])}
      </section>
      <section class="functional-pathway-section">
        <header><strong>Reactome pathways</strong><span>${escapeHtml(`${reactome.significant_count || 0} at FDR ≤ ${data.parameters?.fdr_threshold || 0.05}`)}</span></header>
        <div class="functional-pathways">
          ${pathways.map((pathway) => renderFunctionalPathway(pathway, pathways)).join("") || '<p>No Reactome pathways returned.</p>'}
        </div>
      </section>
    </div>
    <section class="functional-enrichment-section">
      <header><strong>STRING enrichment</strong><span>${escapeHtml(`${enrichment.significant_count || 0} significant terms`)}</span></header>
        ${enrichment.available === false ? '<p class="functional-source-warning">STRING enrichment was unavailable for this run.</p>' : ""}
        <div class="functional-enrichment-table">
        <div><b>Category</b><b>Term</b><b>Genes</b><b>FDR</b></div>
        ${terms.slice(0, 20).map((term) => `<div>
          <code>${escapeHtml(term.category || "")}</code>
          <span title="${escapeHtml(term.description || term.term)}">${escapeHtml(term.description || term.term)}</span>
          <strong>${escapeHtml(term.input_gene_count || 0)}</strong>
          <code>${escapeHtml(formatScientific(term.fdr))}</code>
        </div>`).join("")}
      </div>
    </section>
    <div class="functional-analysis-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Enrichment and association networks are hypothesis-generating evidence.")}</p>
      <div class="functional-source-links">
        ${sources.map((source) => `<a class="source-link" href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.name)}</a>`).join("")}
        ${safeExternalUrl(network.source_url) ? `<a class="source-link" href="${escapeHtml(network.source_url)}" target="_blank" rel="noreferrer">Open network in STRING</a>` : ""}
      </div>
      <div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>
    </div>
  `;
}

function renderFunctionalNetwork(nodes, edges) {
  const visibleNodes = nodes.slice(0, 18);
  if (!visibleNodes.length) return '<p class="functional-network-empty">No STRING proteins were returned.</p>';
  const positions = functionalNetworkPositions(visibleNodes);
  const visibleIds = new Set(visibleNodes.map((node) => node.id));
  const visibleEdges = edges.filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target));
  return `
    <div class="functional-network" role="img" aria-label="STRING functional association network with ${visibleNodes.length} proteins and ${visibleEdges.length} visible edges">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        ${visibleEdges.map((edge) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return "";
          return `<line x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}" style="--edge:${clamp(Number(edge.score) || 0, 0.08, 1)}" />`;
        }).join("")}
      </svg>
      ${visibleNodes.map((node) => {
        const position = positions.get(node.id);
        return `<span class="functional-node" style="left:${position.x}%;top:${position.y}%" title="${escapeHtml(`${node.name} · degree ${node.degree} · ${node.annotation || "No annotation returned"}`)}"><b>${escapeHtml(node.name)}</b><small>${escapeHtml(node.degree)}</small></span>`;
      }).join("")}
      <small class="functional-network-count">${escapeHtml(`showing ${visibleNodes.length}/${nodes.length} proteins`)}</small>
    </div>
  `;
}

function functionalNetworkPositions(nodes) {
  const positions = new Map();
  const count = nodes.length;
  if (count === 1) {
    positions.set(nodes[0].id, { x: 50, y: 50 });
    return positions;
  }
  nodes.forEach((node, index) => {
    const angle = -Math.PI / 2 + (index / count) * Math.PI * 2;
    const radiusX = count <= 8 ? 34 : index % 2 === 0 ? 35 : 25;
    const radiusY = count <= 8 ? 35 : index % 2 === 0 ? 36 : 26;
    positions.set(node.id, {
      x: Number((50 + Math.cos(angle) * radiusX).toFixed(2)),
      y: Number((50 + Math.sin(angle) * radiusY).toFixed(2)),
    });
  });
  return positions;
}

function renderFunctionalPathway(pathway, pathways) {
  const fdrValue = (value) => {
    const numeric = Number(value);
    return Number.isFinite(numeric) && numeric >= 0 ? Math.max(numeric, Number.MIN_VALUE) : 1;
  };
  const scores = pathways.map((item) => -Math.log10(fdrValue(item.fdr)));
  const maxScore = Math.max(...scores, 1);
  const score = -Math.log10(fdrValue(pathway.fdr));
  const width = clamp((score / maxScore) * 100, 2, 100);
  const url = safeExternalUrl(pathway.url) ? pathway.url : "";
  return `<div class="functional-pathway-row">
    <div>
      ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(pathway.name)}</a>` : `<strong>${escapeHtml(pathway.name)}</strong>`}
      <span>${escapeHtml(`${pathway.entities_found || 0}/${pathway.entities_total || 0} entities`)}</span>
    </div>
    <i><b style="width:${width}%"></b></i>
    <code>${escapeHtml(formatScientific(pathway.fdr))}</code>
  </div>`;
}

function renderTargetEvidenceReview(title, data) {
  const disease = data.disease || {};
  const candidates = data.candidates || [];
  const lanes = data.evidence_lanes || [];
  const sourceUrl = safeExternalUrl(data.source_url) ? data.source_url : "";
  return `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(data.source || "Open Targets")}</span>
    </header>
    <div class="target-review-heading">
      <div><span>Disease</span><strong>${escapeHtml(disease.name || "n/a")}</strong><code>${escapeHtml(disease.id || "")}</code></div>
      <div><span>Candidates</span><strong>${escapeHtml(candidates.length)}</strong></div>
      <div><span>Evidence scope</span><strong>${data.include_indirect ? "Ontology descendants" : "Direct disease"}</strong></div>
      <div><span>Retrieved</span><strong>${escapeHtml(formatTimestamp(data.retrieved_at))}</strong></div>
    </div>
    <div class="target-evidence-scroll">
      <table class="target-evidence-table">
        <thead><tr>
          <th scope="col">Rank</th>
          <th scope="col">Target</th>
          <th scope="col">Association</th>
          ${lanes.map((lane) => `<th scope="col">${escapeHtml(lane.label)}</th>`).join("")}
        </tr></thead>
        <tbody>
          ${candidates.map((candidate) => `<tr>
            <td>${escapeHtml(candidate.rank)}</td>
            <th scope="row"><a href="${escapeHtml(candidate.target_url)}" target="_blank" rel="noreferrer">${escapeHtml(candidate.symbol)}</a><small>${escapeHtml(candidate.name || "")}</small></th>
            <td>${targetEvidenceScore(candidate.association_score, "association")}</td>
            ${lanes.map((lane) => `<td>${targetEvidenceScore((candidate.datatype_score_map || {})[lane.id] || 0, lane.id)}</td>`).join("")}
          </tr>`).join("")}
        </tbody>
      </table>
    </div>
    <div class="target-evidence-details">
      ${candidates.map((candidate, index) => renderTargetEvidenceDetail(candidate, index === 0)).join("")}
    </div>
    <div class="target-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Association scores are ranking signals, not confidence values.")}</p>
      <div class="target-output-paths">
        ${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}
      </div>
      ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open Targets source</a>` : ""}
    </div>
  `;
}

function targetEvidenceScore(value, lane) {
  const score = clamp(Number(value) || 0, 0, 1);
  const className = String(lane || "").replace(/[^a-z0-9_-]/gi, "");
  return `<span class="target-score ${escapeHtml(className)}" style="--score:${score * 100}%"><i></i><b>${formatDecimal(score, 3)}</b></span>`;
}

function renderTargetEvidenceDetail(candidate, open) {
  const modalities = (candidate.tractability?.approved_modalities || []).map(targetModalityLabel);
  const drugs = candidate.drugs || [];
  const pathways = candidate.pathways || [];
  const safety = candidate.safety_liabilities || [];
  const publications = candidate.publications || [];
  return `
    <details ${open ? "open" : ""}>
      <summary><strong>${escapeHtml(candidate.symbol)}</strong><span>${drugs.length} clinical ${drugs.length === 1 ? "drug" : "drugs"} · ${modalities.length ? escapeHtml(modalities.join(", ")) : "no approved modality returned"}</span></summary>
      <div class="target-detail-grid">
        <section><span>Clinical precedence</span><p>${drugs.length ? drugs.map((drug) => `<a href="${escapeHtml(drug.url)}" target="_blank" rel="noreferrer">${escapeHtml(drug.name)}</a><small>${escapeHtml([drug.stage, drug.type].filter(Boolean).join(" · "))}</small>`).join("") : "No disease-specific clinical evidence returned."}</p></section>
        <section><span>Pathways</span><p>${pathways.length ? pathways.map((pathway) => `<b>${escapeHtml(pathway.name)}</b>`).join("") : "No pathway annotation returned."}</p></section>
        <section><span>Safety liabilities</span><p>${safety.length ? safety.map((item) => `<b>${escapeHtml(item.event)}</b>`).join("") : "No liability annotation returned."}</p></section>
        <section><span>Publications</span><p>${publications.length ? publications.map((id) => publicationLink(id)).join("") : "No publication IDs in the bounded evidence sample."}</p></section>
      </div>
    </details>
  `;
}

function targetModalityLabel(value) {
  return ({ AB: "antibody", SM: "small molecule", PR: "other protein", OC: "oligonucleotide" })[value] || value;
}

function publicationLink(identifier) {
  const id = String(identifier || "");
  if (/^\d+$/.test(id)) {
    return `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(id)}/" target="_blank" rel="noreferrer">PMID ${escapeHtml(id)}</a>`;
  }
  return `<b>${escapeHtml(id)}</b>`;
}

function formatTimestamp(value) {
  const date = new Date(value || "");
  if (Number.isNaN(date.getTime())) return "n/a";
  return date.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function renderGeoDatasetLandscape(title, data, preview) {
  const datasets = data.datasets || [];
  const sourceUrl = safeExternalUrl(data.search_url) ? data.search_url : "";
  const assayCounts = data.assay_type_counts || [];
  const organismCounts = data.organism_counts || [];
  return `
    <header><strong>${title}</strong><span>${preview ? "Preview" : escapeHtml(data.source || "NCBI GEO")}</span></header>
    <div class="geo-query">
      <span>Exact query</span>
      <code>${escapeHtml(data.exact_query || data.query || "")}</code>
    </div>
    <div class="geo-metrics">
      ${[
        ["Matches", Number(data.hit_count || 0).toLocaleString("en-US")],
        ["Mapped", data.returned_count || datasets.length],
        ["GEO samples", Number(data.total_samples || 0).toLocaleString("en-US")],
        ["Publications", data.publication_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="geo-filters">
      <span>${escapeHtml(data.organism || "Any organism")}</span>
      <span>${escapeHtml(data.assay_label || data.assay_scope || "All assays")}</span>
      <span>samples ≥ ${escapeHtml(data.min_samples || 1)}</span>
      <span>${escapeHtml(data.sort || "NCBI relevance")}</span>
    </div>
    <div class="geo-distributions">
      <section>
        <header><strong>Assay metadata</strong><span>${assayCounts.length} types</span></header>
        ${renderGeoCountRows(assayCounts)}
      </section>
      <section>
        <header><strong>Organisms</strong><span>${organismCounts.length} values</span></header>
        ${renderGeoCountRows(organismCounts)}
      </section>
    </div>
    <div class="geo-datasets">
      ${datasets.map((dataset) => renderGeoDataset(dataset, false)).join("")}
    </div>
    <div class="geo-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "GEO inclusion does not establish dataset quality or fitness for purpose.")}</p>
      ${Object.keys(data.outputs || {}).length ? `<div class="target-output-paths">${Object.entries(data.outputs).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>` : ""}
      ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open exact query in NCBI GEO</a>` : ""}
    </div>
  `;
}

function renderGeoCountRows(rows) {
  return `<div class="geo-count-list">${rows.slice(0, 6).map((item) => `<div><span>${escapeHtml(item.label)}</span><b>${escapeHtml(item.count)}</b></div>`).join("") || "<p>No metadata returned.</p>"}</div>`;
}

function renderGeoSeriesMatrix(title, data, preflight) {
  const sourceUrl = safeExternalUrl(data.download_url || data.source_url) ? (data.download_url || data.source_url) : "";
  const metrics = data.matrix_metrics || {};
  const samples = data.sample_summaries || [];
  const metadata = data.metadata_summaries || [];
  const available = data.available_files || [];
  if (preflight) {
    return `
      <header><strong>${title}</strong><span>${data.ready ? "Ready for approval" : "Selection required"}</span></header>
      <div class="geo-query"><span>GEO source</span><code>${escapeHtml(data.matrix_file || data.accession || "")}</code></div>
      <div class="geo-metrics">
        ${[
          ["Series", data.accession || "n/a"],
          ["Matrices", available.length],
          ["Compressed", data.compressed_bytes ? formatBytes(data.compressed_bytes) : "unknown"],
          ["Local limit", formatBytes(data.limits?.compressed_bytes || 0)],
        ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
      </div>
      <div class="geo-matrix-files">${available.map((file) => `<code>${escapeHtml(file)}</code>`).join("")}</div>
      <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Series Matrix values are submitter-processed measurements.")}</p>
      ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open official matrix source</a>` : ""}
    `;
  }
  return `
    <header><strong>${title}</strong><span>${escapeHtml(data.source || "NCBI GEO")}</span></header>
    <div class="geo-query"><span>Source file</span><code>${escapeHtml(data.matrix_file || "")}</code></div>
    <div class="geo-metrics">
      ${[
        ["Features", Number(data.feature_count || 0).toLocaleString("en-US")],
        ["Samples", Number(data.sample_count || 0).toLocaleString("en-US")],
        ["Missing", formatPercent(metrics.missing_fraction || 0)],
        ["Source", formatBytes(data.compressed_bytes || 0)],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="geo-filters">
      <span>${escapeHtml(data.accession || "GEO Series")}</span>
      <span>${escapeHtml((data.series_type || []).join("; ") || "Series Matrix")}</span>
      <span>${formatPercent(metrics.integer_fraction || 0)} integer-valued</span>
      <span>processed values</span>
    </div>
    <section class="geo-matrix-section">
      <header><strong>Sample QC</strong><span>${samples.length} samples</span></header>
      <div class="geo-matrix-table-wrap">
        <table class="geo-matrix-table">
          <thead><tr><th>Sample</th><th>Title / source</th><th>Missing</th><th>Median</th><th>IQR</th></tr></thead>
          <tbody>${samples.slice(0, 40).map((sample) => `<tr>
            <th><code>${escapeHtml(sample.sample)}</code></th>
            <td>${escapeHtml(sample.title || sample.source || "No title")}</td>
            <td>${escapeHtml(formatPercent(sample.missing_fraction || 0))}</td>
            <td><code>${escapeHtml(sample.median == null ? "n/a" : formatDecimal(sample.median, 3))}</code></td>
            <td><code>${escapeHtml(sample.q1 == null || sample.q3 == null ? "n/a" : `${formatDecimal(sample.q1, 3)} – ${formatDecimal(sample.q3, 3)}`)}</code></td>
          </tr>`).join("")}</tbody>
        </table>
      </div>
      ${samples.length > 40 ? `<p class="geo-matrix-more">${escapeHtml(samples.length - 40)} additional samples remain in the exported tables.</p>` : ""}
    </section>
    <section class="geo-matrix-section">
      <header><strong>Sample metadata</strong><span>${metadata.length} fields</span></header>
      <div class="geo-count-list">${metadata.slice(0, 10).map((field) => `<div><span>${escapeHtml(field.field.replaceAll("_", " "))}</span><b>${escapeHtml(field.unique_count)}</b></div>`).join("")}</div>
    </section>
    <p class="geo-handoff">${escapeHtml(data.analysis_handoff || "Confirm study design before analysis.")}</p>
    <div class="geo-actions">
      <button class="secondary-button" type="button" data-geo-matrix-review="${escapeHtml(data.accession || "")}">${escapeHtml(localized("审阅分组", "Review grouping"))}</button>
      ${sourceUrl ? `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Official source</a>` : ""}
    </div>
    <div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>
    <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Processed values are not raw counts.")}</p>
  `;
}

function bindGeoSeriesMatrixActions(card) {
  card.querySelectorAll("[data-geo-matrix-review]").forEach((button) => {
    button.addEventListener("click", () => {
      const accession = button.dataset.geoMatrixReview || "GEO Series";
      els.commandInput.value = localized(
        `基于已导入的 ${accession} Series Matrix，审阅样本分组、独立重复、配对、批次、数值变换和适合的描述性分析`,
        `Using the imported ${accession} Series Matrix, review sample groups, independent replicates, pairing, batches, value transformations, and suitable descriptive analyses`,
      );
      els.commandInput.focus();
    });
  });
}

function renderGeoDataset(dataset, open) {
  const recordUrl = safeExternalUrl(dataset.url) ? dataset.url : "";
  const downloadUrl = safeExternalUrl(dataset.download_url) ? dataset.download_url : "";
  const assay = (dataset.dataset_types || []).join("; ") || "Assay not specified";
  const organism = (dataset.organisms || []).join("; ") || "Organism not specified";
  const files = (dataset.supplementary_file_types || []).join(", ") || "none reported";
  return `
    <details ${open ? "open" : ""}>
      <summary>
        <span class="geo-rank">${escapeHtml(dataset.rank)}</span>
        <span class="geo-dataset-title">
          <strong>${recordUrl ? `<a href="${escapeHtml(recordUrl)}" target="_blank" rel="noreferrer">${escapeHtml(dataset.accession)}</a>` : escapeHtml(dataset.accession)}</strong>
          <small>${escapeHtml(dataset.title)}</small>
        </span>
        <span class="geo-sample-count"><b>${escapeHtml(dataset.n_samples || 0)}</b> samples</span>
        <span class="geo-release-date">${escapeHtml(dataset.release_date || "No date")}</span>
      </summary>
      <div class="geo-dataset-body">
        <div class="geo-dataset-meta">
          <span>${escapeHtml(organism)}</span>
          <span>${escapeHtml(assay)}</span>
          <span>${escapeHtml((dataset.platform_accessions || []).join(", ") || "No platform accession")}</span>
          <span>Supplementary: ${escapeHtml(files)}${dataset.geo2r_available ? " · GEO2R available" : ""}</span>
        </div>
        <p>${escapeHtml(dataset.summary || "No study summary returned.")}</p>
        ${(dataset.sample_examples || []).length ? `<div class="geo-sample-examples"><span>Sample examples</span>${dataset.sample_examples.map((sample) => `<code>${escapeHtml(sample.accession || "GSM")} · ${escapeHtml(sample.title || "")}</code>`).join("")}</div>` : ""}
        <p class="geo-handoff">${escapeHtml(dataset.analysis_handoff || "Inspect study design and data files before local analysis.")}</p>
        <div class="geo-actions">
          <button class="secondary-button" type="button" data-geo-review="${escapeHtml(dataset.accession)}">${escapeHtml(localized("审阅设计", "Review design"))}</button>
          <button class="secondary-button" type="button" data-geo-import="${escapeHtml(dataset.accession)}">${escapeHtml(localized("导入矩阵", "Import matrix"))}</button>
          ${recordUrl ? `<a href="${escapeHtml(recordUrl)}" target="_blank" rel="noreferrer">GEO record</a>` : ""}
          ${downloadUrl ? `<a href="${escapeHtml(downloadUrl)}" target="_blank" rel="noreferrer">Download directory</a>` : ""}
          ${(dataset.pubmed_ids || []).slice(0, 4).map((pmid) => `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(pmid)}/" target="_blank" rel="noreferrer">PMID ${escapeHtml(pmid)}</a>`).join("")}
          ${dataset.bioproject ? `<a href="https://www.ncbi.nlm.nih.gov/bioproject/${escapeHtml(dataset.bioproject)}" target="_blank" rel="noreferrer">${escapeHtml(dataset.bioproject)}</a>` : ""}
        </div>
      </div>
    </details>
  `;
}

function bindGeoDatasetActions(card) {
  card.querySelectorAll("[data-geo-review]").forEach((button) => {
    button.addEventListener("click", () => {
      const accession = button.dataset.geoReview || "GEO Series";
      els.commandInput.value = localized(
        `审阅 ${accession} 的研究设计、样本分组、可用矩阵和适合的本地分析路径`,
        `Review the study design, sample groups, available matrices, and suitable local analysis path for ${accession}`,
      );
      els.commandInput.focus();
    });
  });
  card.querySelectorAll("[data-geo-import]").forEach((button) => {
    button.addEventListener("click", () => {
      const accession = button.dataset.geoImport || "GEO Series";
      els.commandInput.value = localized(
        `导入 ${accession} 的官方 GEO Series Matrix 到本地工作区`,
        `Import the official GEO Series Matrix for ${accession} into the local workspace`,
      );
      els.commandInput.focus();
    });
  });
}

function renderLiteratureEvidenceMap(title, data) {
  const papers = data.papers || [];
  const typeCounts = data.study_type_counts || [];
  const yearCounts = data.year_counts || [];
  const sourceUrl = safeExternalUrl(data.search_url) ? data.search_url : "";
  return `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(data.source || "Europe PMC")}</span>
    </header>
    <div class="literature-query">
      <span>Approved query</span>
      <code>${escapeHtml(data.exact_query || data.query || "")}</code>
    </div>
    <div class="literature-metrics">
      ${[
        ["Matches", Number(data.hit_count || 0).toLocaleString("en-US")],
        ["Mapped", data.returned_count || papers.length],
        ["With abstract", data.abstract_count || 0],
        ["Open access", data.open_access_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="literature-filters">
      <span>${escapeHtml([data.start_year, data.end_year].filter(Boolean).join("–") || "All years")}</span>
      <span>${data.include_preprints ? "Preprints included" : "Preprints excluded"}</span>
      <span>${data.require_abstract ? "Abstract required" : "Abstract optional"}</span>
      <span>${escapeHtml(data.sort || "Source relevance")}</span>
    </div>
    <div class="literature-map">
      <section>
        <header><strong>Study types</strong><span>source metadata</span></header>
        <div class="literature-type-list">
          ${typeCounts.map((item) => `<div><span>${escapeHtml(item.label)}</span><b>${escapeHtml(item.count)}</b></div>`).join("") || "<p>No publication types returned.</p>"}
        </div>
      </section>
      <section>
        <header><strong>Publication years</strong><span>mapped set</span></header>
        <div class="literature-year-list">
          ${yearCounts.slice(0, 10).map((item) => `<span><b>${escapeHtml(item.year)}</b><i style="--count:${Math.max(1, Number(item.count || 0))}"></i><small>${escapeHtml(item.count)}</small></span>`).join("") || "<p>No year metadata returned.</p>"}
        </div>
      </section>
    </div>
    <div class="literature-papers">
      ${papers.map((paper) => renderLiteraturePaper(paper, false)).join("")}
    </div>
    <div class="literature-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Source relevance does not establish study quality.")}</p>
      ${Object.keys(data.outputs || {}).length ? `<div class="target-output-paths">${Object.entries(data.outputs).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>` : ""}
      ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open approved query in Europe PMC</a>` : ""}
    </div>
  `;
}

function renderLiteraturePaper(paper, open) {
  const paperUrl = safeExternalUrl(paper.url) ? paper.url : "";
  const identifiers = [];
  if (paper.pmid) identifiers.push(`<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(paper.pmid)}/" target="_blank" rel="noreferrer">PMID ${escapeHtml(paper.pmid)}</a>`);
  if (paper.pmcid) identifiers.push(`<a href="https://europepmc.org/article/PMC/${escapeHtml(paper.pmcid)}" target="_blank" rel="noreferrer">${escapeHtml(paper.pmcid)}</a>`);
  if (paper.doi) identifiers.push(`<a href="https://doi.org/${escapeHtml(paper.doi)}" target="_blank" rel="noreferrer">DOI</a>`);
  return `
    <details ${open ? "open" : ""}>
      <summary>
        <span class="literature-rank">${escapeHtml(paper.rank)}</span>
        <span class="literature-paper-title"><strong>${escapeHtml(paper.title)}</strong><small>${escapeHtml([paper.journal, paper.year].filter(Boolean).join(" · "))}</small></span>
        <span class="literature-study-type">${escapeHtml(paper.study_type || "Publication")}</span>
      </summary>
      <div class="literature-paper-body">
        <div class="literature-paper-meta">
          <span>${escapeHtml(paper.authors || "Authors unavailable")}</span>
          <span>${identifiers.join("") || escapeHtml(`${paper.source_code || ""}:${paper.id || ""}`)}</span>
          <span>${paper.open_access ? "Open access" : "Access status not open"} · cited by ${escapeHtml(paper.cited_by_count || 0)} <small>(context only)</small></span>
        </div>
        <div class="literature-paper-types">${(paper.publication_types || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>
        <p class="literature-abstract">${escapeHtml(paper.abstract || "No abstract returned for this record.")}</p>
        <div class="literature-paper-links">
          ${paperUrl ? `<a href="${escapeHtml(paperUrl)}" target="_blank" rel="noreferrer">Europe PMC record</a>` : ""}
          ${(paper.keywords || []).slice(0, 6).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
        </div>
      </div>
    </details>
  `;
}

function renderClinicalTrialLandscape(title, data) {
  const studies = data.studies || [];
  const statusCounts = data.status_counts || [];
  const phaseCounts = data.phase_counts || [];
  const sourceUrl = safeExternalUrl(data.search_url) ? data.search_url : "";
  return `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(data.source || "ClinicalTrials.gov")}</span>
    </header>
    <div class="trial-query">
      <span>Approved query</span>
      <strong>${escapeHtml(data.condition || "n/a")}</strong>
      <code>${escapeHtml(data.intervention || "Any intervention")}</code>
    </div>
    <div class="trial-metrics">
      ${[
        ["Matches", Number(data.hit_count || 0).toLocaleString("en-US")],
        ["Mapped", data.returned_count || studies.length],
        ["Posted results", data.results_available_count || 0],
        ["Countries", data.country_count ?? (data.country_counts || []).length],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="trial-filters">
      <span>${escapeHtml(formatTrialLabel(data.status_scope || "all"))} status</span>
      <span>${escapeHtml(formatTrialLabel(data.study_scope || "all"))} studies</span>
      <span>${escapeHtml(data.source_order || "Source order")}</span>
      <span>${escapeHtml(formatTimestamp(data.retrieved_at))}</span>
    </div>
    <div class="trial-distributions">
      <section>
        <header><strong>Status</strong><span>mapped set</span></header>
        <div>${statusCounts.map((item) => `<p><span>${escapeHtml(formatTrialLabel(item.label))}</span><b>${escapeHtml(item.count)}</b></p>`).join("") || "<p>No status metadata.</p>"}</div>
      </section>
      <section>
        <header><strong>Phase</strong><span>mapped set</span></header>
        <div>${phaseCounts.map((item) => `<p><span>${escapeHtml(formatTrialLabel(item.label))}</span><b>${escapeHtml(item.count)}</b></p>`).join("") || "<p>No phase metadata.</p>"}</div>
      </section>
    </div>
    <div class="trial-records">
      ${studies.map((study, index) => renderClinicalTrialRecord(study, index === 0)).join("")}
    </div>
    <div class="trial-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Registry metadata does not establish efficacy or safety.")}</p>
      ${Object.keys(data.outputs || {}).length ? `<div class="target-output-paths">${Object.entries(data.outputs).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>` : ""}
      ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open approved query in ClinicalTrials.gov</a>` : ""}
    </div>
  `;
}

function renderClinicalTrialRecord(study, open) {
  const studyUrl = safeExternalUrl(study.url) ? study.url : "";
  const interventions = study.interventions || [];
  const outcomes = study.primary_outcomes || [];
  const publications = study.publications || [];
  const eligibility = study.eligibility || {};
  const design = study.design || {};
  const dates = study.dates || {};
  return `
    <details ${open ? "open" : ""}>
      <summary>
        <span class="trial-rank">${escapeHtml(study.rank)}</span>
        <span class="trial-title"><strong>${escapeHtml(study.title || study.nct_id)}</strong><small>${escapeHtml(study.nct_id || "")}${study.has_results ? " · posted results" : ""}</small></span>
        <span class="trial-status">${escapeHtml(formatTrialLabel(study.status || "unknown"))}</span>
      </summary>
      <div class="trial-body">
        <div class="trial-meta">
          <span><b>Phase</b>${escapeHtml((study.phases || []).map(formatTrialLabel).join(", ") || "n/a")}</span>
          <span><b>Enrollment</b>${escapeHtml(`${study.enrollment || 0} ${formatTrialLabel(study.enrollment_type || "")}`.trim())}</span>
          <span><b>Sponsor</b>${escapeHtml(study.sponsor || "Not returned")}</span>
          <span><b>Countries</b>${escapeHtml((study.countries || []).join(", ") || "Not returned")}</span>
        </div>
        <div class="trial-design-line">${escapeHtml([design.allocation, design.intervention_model, design.masking, design.primary_purpose].filter(Boolean).map(formatTrialLabel).join(" · ") || formatTrialLabel(study.study_type || ""))}</div>
        <section>
          <span>Interventions</span>
          <p>${interventions.map((item) => `<b>${escapeHtml(item.name)}</b><small>${escapeHtml(formatTrialLabel(item.type))}</small>`).join("") || "No intervention metadata returned."}</p>
        </section>
        <section>
          <span>Registered primary outcomes</span>
          <p>${outcomes.map((item) => `<b>${escapeHtml(item.measure)}</b><small>${escapeHtml(item.time_frame || "Time frame not returned")}</small>`).join("") || "No primary outcome metadata returned."}</p>
        </section>
        <div class="trial-footline">
          <span>${escapeHtml([eligibility.sex, eligibility.minimum_age && `from ${eligibility.minimum_age}`, eligibility.maximum_age && `to ${eligibility.maximum_age}`].filter(Boolean).join(" · ") || "Eligibility summary unavailable")}</span>
          <span>${escapeHtml([dates.start && `start ${dates.start}`, dates.primary_completion && `primary completion ${dates.primary_completion}`, dates.last_updated && `updated ${dates.last_updated}`].filter(Boolean).join(" · "))}</span>
        </div>
        <div class="trial-links">
          ${studyUrl ? `<a href="${escapeHtml(studyUrl)}" target="_blank" rel="noreferrer">${escapeHtml(study.nct_id)} official record</a>` : ""}
          ${publications.filter((item) => item.pmid).slice(0, 6).map((item) => `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(item.pmid)}/" target="_blank" rel="noreferrer">PMID ${escapeHtml(item.pmid)}</a>`).join("")}
        </div>
      </div>
    </details>
  `;
}

function renderClinicalTrialResultsPreflight(title, data) {
  const study = data.study || {};
  const sourceUrl = safeExternalUrl(data.source_url) ? data.source_url : "";
  return `
    <header><strong>${title}</strong><span>posted results preflight</span></header>
    <div class="clinical-results-identity">
      <div><span>NCT ID</span><strong>${escapeHtml(data.nct_id || study.nct_id || "n/a")}</strong></div>
      <div><span>Status</span><strong>${escapeHtml(formatTrialLabel(study.status || "unknown"))}</strong></div>
      <div><span>Phase</span><strong>${escapeHtml((study.phases || []).map(formatTrialLabel).join(", ") || "n/a")}</strong></div>
      <div><span>Sponsor</span><strong>${escapeHtml(study.sponsor || "Not returned")}</strong></div>
    </div>
    <p class="clinical-results-title">${escapeHtml(study.title || data.nct_id || "Clinical trial")}</p>
    <div class="clinical-results-counts">
      ${[
        ["Primary", data.primary_outcome_count || 0],
        ["Secondary", data.secondary_outcome_count || 0],
        ["Serious AE terms", data.serious_event_term_count || 0],
        ["Publications", data.publication_count || 0],
        ["Documents", data.document_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Posted registry tables are not an independent efficacy or safety conclusion.")}</p>
    ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open ${escapeHtml(data.nct_id || "record")} in ClinicalTrials.gov</a>` : ""}
  `;
}

function renderClinicalTrialResults(title, data) {
  const study = data.study || {};
  const flow = data.participant_flow || {};
  const baseline = data.baseline || {};
  const outcomes = (data.outcomes || []).slice(0, 40);
  const adverse = data.adverse_events || {};
  const documents = data.documents || [];
  const publications = data.publications || [];
  const sourceUrl = safeExternalUrl(data.source_url) ? data.source_url : "";
  const firstPeriod = (flow.periods || [])[0] || {};
  const started = (firstPeriod.milestones || []).find((item) => /STARTED|ENROLLED/.test(String(item.type || "").toUpperCase()));
  const completed = (firstPeriod.milestones || []).find((item) => /COMPLETED/.test(String(item.type || "").toUpperCase()));
  return `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(formatTimestamp(data.retrieved_at))}</span>
    </header>
    <div class="clinical-results-heading">
      <div><span>Exact record</span><strong>${escapeHtml(data.nct_id || study.nct_id || "n/a")}</strong></div>
      <p>${escapeHtml(study.title || "Clinical trial")}</p>
      <span>${escapeHtml(formatTrialLabel(study.status || "unknown"))}</span>
    </div>
    <div class="clinical-results-counts">
      ${[
        ["Enrollment", study.enrollment || 0],
        ["Primary", data.primary_outcome_count || 0],
        ["Secondary", data.secondary_outcome_count || 0],
        ["Analyses", data.analysis_count || 0],
        ["Serious AE terms", adverse.serious_event_term_count || 0],
        ["Publications", publications.length],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="clinical-results-meta">
      <span>${escapeHtml((study.phases || []).map(formatTrialLabel).join(", ") || formatTrialLabel(study.study_type || "Study"))}</span>
      <span>${escapeHtml(study.sponsor || "Sponsor not returned")}</span>
      <span>${escapeHtml([study.design?.allocation, study.design?.intervention_model, study.design?.masking].filter(Boolean).map(formatTrialLabel).join(" · ") || "Design not returned")}</span>
      <span>${escapeHtml(study.dates?.results_first_posted ? `Results posted ${study.dates.results_first_posted}` : "Results date not returned")}</span>
    </div>
    <section class="clinical-results-section">
      <header><strong>Participant flow</strong><span>${escapeHtml(firstPeriod.title || "First reported period")}</span></header>
      <div class="clinical-flow-list">
        ${(flow.groups || []).map((group) => `
          <div>
            <strong>${escapeHtml(group.title || group.id)}</strong>
            <span>Started <b>${escapeHtml(flowSubjects(started, group.id))}</b></span>
            <span>Completed <b>${escapeHtml(flowSubjects(completed, group.id))}</b></span>
          </div>
        `).join("") || "<p>No participant-flow groups returned.</p>"}
      </div>
    </section>
    <details class="clinical-results-section clinical-baseline">
      <summary><strong>Baseline characteristics</strong><span>${escapeHtml(`${baseline.measure_count || (baseline.measures || []).length} measures`)}</span></summary>
      <div class="clinical-measure-list">
        ${(baseline.measures || []).slice(0, 12).map((measure, index) => renderClinicalResultMeasure(measure, index === 0, "baseline")).join("") || "<p>No baseline measures returned.</p>"}
      </div>
    </details>
    <section class="clinical-results-section">
      <header><strong>Outcome measures</strong><span>source order · submitted statistics</span></header>
      <div class="clinical-measure-list">
        ${outcomes.map((measure, index) => renderClinicalResultMeasure(measure, measure.type === "PRIMARY" && index < 2, "outcome")).join("") || "<p>No outcome measures returned.</p>"}
      </div>
      ${Number(data.outcome_count || outcomes.length) > outcomes.length ? `<p class="clinical-results-note">Showing ${outcomes.length} of ${escapeHtml(data.outcome_count)} measures. Complete rows are in the persisted outputs.</p>` : ""}
    </section>
    <section class="clinical-results-section">
      <header><strong>Adverse events</strong><span>${escapeHtml(adverse.time_frame || "Time frame not returned")}</span></header>
      <div class="clinical-ae-groups">
        ${(adverse.groups || []).map((group) => `
          <div><strong>${escapeHtml(group.title || group.id)}</strong><span>Deaths ${escapeHtml(group.deaths_affected)}/${escapeHtml(group.deaths_at_risk)}</span><span>Serious ${escapeHtml(group.serious_affected)}/${escapeHtml(group.serious_at_risk)}</span><span>Other ${escapeHtml(group.other_affected)}/${escapeHtml(group.other_at_risk)}</span></div>
        `).join("") || "<p>No adverse-event group totals returned.</p>"}
      </div>
      ${renderAdverseEventTerms("Serious event terms", adverse.serious_events || [], adverse.serious_event_term_count || 0)}
      ${renderAdverseEventTerms("Other event terms", adverse.other_events || [], adverse.other_event_term_count || 0)}
    </section>
    <section class="clinical-results-section clinical-source-files">
      <header><strong>Source files and publications</strong><span>critical appraisal inputs</span></header>
      <div class="clinical-source-links">
        ${documents.filter((item) => safeExternalUrl(item.url)).map((item) => `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.label || item.filename)}</a>`).join("")}
        ${publications.filter((item) => item.pmid && safeExternalUrl(item.url)).slice(0, 20).map((item) => `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">PMID ${escapeHtml(item.pmid)}</a>`).join("")}
      </div>
    </section>
    <div class="trial-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "No independent efficacy or safety conclusion was generated.")}</p>
      ${Object.keys(data.outputs || {}).length ? `<div class="target-output-paths">${Object.entries(data.outputs).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>` : ""}
      ${sourceUrl ? `<a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open exact record in ClinicalTrials.gov</a>` : ""}
    </div>
  `;
}

function flowSubjects(milestone, groupId) {
  const value = (milestone?.values || []).find((item) => item.group_id === groupId);
  return value ? value.subjects : "n/a";
}

function renderClinicalResultMeasure(measure, open, context) {
  const rows = measure.rows || [];
  const analyses = measure.analyses || [];
  return `
    <details class="clinical-measure" ${open ? "open" : ""}>
      <summary>
        <span>${escapeHtml(formatTrialLabel(measure.type || context))}</span>
        <strong>${escapeHtml(measure.title || "Measure")}</strong>
        <small>${escapeHtml(measure.time_frame || measure.unit || "")}</small>
      </summary>
      <div class="clinical-measure-body">
        <div class="clinical-measure-meta">${escapeHtml([measure.param_type, measure.dispersion_type, measure.unit].filter(Boolean).map(formatTrialLabel).join(" · ") || "Submitted values")}</div>
        ${measure.description ? `<p>${escapeHtml(measure.description)}</p>` : ""}
        ${rows.map((row) => `
          <div class="clinical-result-row">
            <strong>${escapeHtml(row.label || "Result")}</strong>
            <div>${(row.values || []).map((value) => `
              <span><small>${escapeHtml(value.group || value.group_id)}</small><b>${escapeHtml(value.value || "n/a")}${value.spread ? ` · ${escapeHtml(value.spread)}` : ""}</b>${value.lower_limit || value.upper_limit ? `<em>${escapeHtml(`${value.lower_limit || "?"} to ${value.upper_limit || "?"}`)}</em>` : ""}</span>
            `).join("")}</div>
          </div>
        `).join("") || "<p>No result rows returned.</p>"}
        ${analyses.map((analysis) => `
          <div class="clinical-analysis">
            <strong>${escapeHtml(analysis.groups.join(" vs ") || "Submitted analysis")}</strong>
            <span>${escapeHtml([analysis.parameter && `${formatTrialLabel(analysis.parameter)} ${analysis.parameter_value}`, analysis.p_value && `p ${analysis.p_value}`, analysis.ci_lower || analysis.ci_upper ? `${analysis.ci_percent || ""}% CI ${analysis.ci_lower || "?"} to ${analysis.ci_upper || "?"}` : ""].filter(Boolean).join(" · "))}</span>
            <small>${escapeHtml(analysis.method || "Method not returned")}</small>
          </div>
        `).join("")}
      </div>
    </details>
  `;
}

function renderAdverseEventTerms(title, events, total) {
  const shown = events.slice(0, 30);
  return `
    <details class="clinical-ae-terms">
      <summary><strong>${escapeHtml(title)}</strong><span>${escapeHtml(total)} terms</span></summary>
      <div>
        ${shown.map((event) => `<p><strong>${escapeHtml(event.term || "Event")}</strong><span>${escapeHtml(event.organ_system || "")}</span><small>${(event.stats || []).map((item) => `${escapeHtml(item.group)} ${escapeHtml(item.affected)}/${escapeHtml(item.at_risk)}`).join(" · ")}</small></p>`).join("") || "<p>No terms returned.</p>"}
      </div>
      ${Number(total) > shown.length ? `<small class="clinical-results-note">Showing ${shown.length} terms in source order; complete rows are in the persisted outputs.</small>` : ""}
    </details>
  `;
}

function formatTrialLabel(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function renderVariantEvidencePreflight(title, data) {
  const variant = data.variant || {};
  const classification = variant.germline_classification || {};
  const location = (variant.locations || []).find((item) => item.assembly === "GRCh38") || {};
  return `
    <header><strong>${title}</strong><span>allele resolution</span></header>
    <div class="variant-identity">
      <div><span>ClinVar</span><strong>${escapeHtml(variant.accession || variant.variation_id || "n/a")}</strong></div>
      <div><span>Allele</span><code>${escapeHtml(variant.hgvs_c || variant.canonical_spdi || "n/a")}</code></div>
      <div><span>Gene</span><strong>${escapeHtml((variant.gene_symbols || []).join(", ") || "n/a")}</strong></div>
      <div><span>GRCh38</span><code>${escapeHtml(location.chromosome ? `${location.chromosome}:${location.start}` : "n/a")}</code></div>
    </div>
    <div class="variant-preflight-classification">
      <span>ClinVar aggregate germline assertion</span>
      <strong>${escapeHtml(classification.description || "Not provided")}</strong>
      <small>${escapeHtml(classification.review_status || "Review status not provided")}</small>
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "Confirm the allele, transcript, and assembly before approval.")}</p>
  `;
}

function renderVariantEvidenceReview(title, data) {
  const variant = data.variant || {};
  const classification = variant.germline_classification || {};
  const vep = data.vep || {};
  const gnomad = data.gnomad || {};
  const transcripts = vep.transcripts || [];
  const populations = gnomad.populations || [];
  const maxPopulationAf = Math.max(...populations.map((item) => Number(item.allele_frequency) || 0), 0.000001);
  const sourceLinks = (data.sources || [])
    .filter((source) => safeExternalUrl(source.url))
    .map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.name)}</a>`)
    .join("");
  return `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(formatTimestamp(data.retrieved_at))}</span>
    </header>
    <div class="variant-query-line">
      <span>Resolved allele</span>
      <code>${escapeHtml(variant.hgvs_c || variant.canonical_spdi || data.query || "")}</code>
      <small>${escapeHtml([variant.accession, (variant.dbsnp_ids || []).join(", ")].filter(Boolean).join(" · "))}</small>
    </div>
    <div class="variant-evidence-lanes">
      <section>
        <header><strong>ClinVar</strong><span>submitted interpretation</span></header>
        <div class="variant-primary-value">${escapeHtml(classification.description || "Not provided")}</div>
        <dl>
          <div><dt>Review status</dt><dd>${escapeHtml(classification.review_status || "Not provided")}</dd></div>
          <div><dt>Last evaluated</dt><dd>${escapeHtml(classification.last_evaluated || "Not provided")}</dd></div>
          <div><dt>Submissions</dt><dd>${escapeHtml(`${variant.supporting_submission_counts?.scv || 0} SCV · ${variant.supporting_submission_counts?.rcv || 0} RCV`)}</dd></div>
        </dl>
        <div class="variant-traits">
          ${(classification.traits || []).slice(0, 6).map((trait) => `<span>${escapeHtml(trait.name)}</span>`).join("") || "<span>No condition scope returned.</span>"}
        </div>
      </section>
      <section>
        <header><strong>Ensembl VEP</strong><span>computed annotation</span></header>
        <div class="variant-primary-value">${escapeHtml((vep.most_severe_consequence || "Not returned").replaceAll("_", " "))}</div>
        <dl>
          <div><dt>Assembly</dt><dd>${escapeHtml(vep.assembly || "n/a")}</dd></div>
          <div><dt>Class</dt><dd>${escapeHtml(vep.variant_class || "n/a")}</dd></div>
          <div><dt>Transcripts</dt><dd>${escapeHtml(vep.transcript_count || transcripts.length)}</dd></div>
        </dl>
        <div class="variant-prediction-note">SIFT and PolyPhen remain computational context.</div>
      </section>
      <section>
        <header><strong>gnomAD v4</strong><span>population observation</span></header>
        <div class="variant-primary-value">${gnomad.available ? escapeHtml(formatVariantFrequency(gnomad.allele_frequency)) : "Not returned"}</div>
        ${gnomad.available ? `<dl>
          <div><dt>Allele count</dt><dd>${escapeHtml(Number(gnomad.ac || 0).toLocaleString("en-US"))}</dd></div>
          <div><dt>Allele number</dt><dd>${escapeHtml(Number(gnomad.an || 0).toLocaleString("en-US"))}</dd></div>
          <div><dt>Homozygotes</dt><dd>${escapeHtml(gnomad.homozygote_count || 0)}</dd></div>
        </dl>` : `<p>${escapeHtml(gnomad.reason || "No population record was available.")}</p>`}
        ${(gnomad.filters || []).length ? `<div class="variant-filter-note">Filter: ${escapeHtml(gnomad.filters.join(", "))}</div>` : ""}
      </section>
    </div>
    <section class="variant-transcripts">
      <header><strong>Transcript consequences</strong><span>MANE and canonical first</span></header>
      <div class="variant-table-scroll">
        <table>
          <thead><tr><th>Transcript</th><th>Gene</th><th>Consequence</th><th>Protein</th><th>Prediction</th></tr></thead>
          <tbody>${transcripts.map((item) => `<tr>
            <th><code>${escapeHtml(item.transcript_id)}</code><small>${item.mane_select ? `MANE ${escapeHtml(item.mane_select)}` : item.canonical ? "Canonical" : ""}</small></th>
            <td>${escapeHtml(item.gene_symbol || item.gene_id || "")}</td>
            <td>${escapeHtml((item.consequences || []).join(", ").replaceAll("_", " "))}<small>${escapeHtml(item.impact || "")}</small></td>
            <td><code>${escapeHtml(item.hgvsp || item.amino_acids || "n/a")}</code></td>
            <td>${escapeHtml(variantPredictionLabel(item))}</td>
          </tr>`).join("") || '<tr><td colspan="5">No transcript consequences returned.</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    ${gnomad.available ? `<section class="variant-populations">
      <header><strong>Population frequency context</strong><span>not a cross-population ranking</span></header>
      <div>${populations.map((item) => `<span>
        <b>${escapeHtml(item.label)}</b>
        <i style="--frequency:${Math.max(1, (Number(item.allele_frequency || 0) / maxPopulationAf) * 100)}%"></i>
        <code>${escapeHtml(formatVariantFrequency(item.allele_frequency))}</code>
      </span>`).join("")}</div>
    </section>` : ""}
    <div class="variant-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "This evidence review is not a diagnosis or clinical classification.")}</p>
      <div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>
      <div class="variant-source-links">${sourceLinks}</div>
    </div>
  `;
}

function formatVariantFrequency(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "n/a";
  if (number === 0) return "0";
  if (number < 0.0001) return number.toExponential(2);
  return number.toPrecision(4);
}

function variantPredictionLabel(item) {
  const parts = [];
  if (item.sift?.prediction) parts.push(`SIFT ${item.sift.prediction}`);
  if (item.polyphen?.prediction) parts.push(`PolyPhen ${item.polyphen.prediction}`);
  return parts.join(" · ") || "Not returned";
}

function renderVcfCohortPreflight(title, data) {
  const thresholds = data.thresholds || {};
  return `
    <header><strong>${title}</strong><span>VCF input validation</span></header>
    <div class="vcf-input-line">
      <span>${escapeHtml(data.fileformat || "VCF")}</span>
      <code>${escapeHtml(data.vcf_path || "")}</code>
      <small>${escapeHtml(data.metadata_path || "No longitudinal metadata")}</small>
    </div>
    <div class="vcf-metrics">
      ${[
        ["Samples", data.sample_count || 0],
        ["Subjects", data.subject_count || 0],
        ["Records", data.record_count || 0],
        ["ALT alleles", data.allele_count || 0],
        ["Included calls", data.included_call_count || 0],
        ["Low-frequency", data.low_frequency_call_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="vcf-filter-line">
      <span>VAF ≥ ${escapeHtml(formatVaf(thresholds.min_vaf))}</span>
      <span>DP ≥ ${escapeHtml(thresholds.min_depth ?? 0)}</span>
      <span>${thresholds.include_filtered ? "Including non-PASS records" : "PASS / unfiltered records only"}</span>
      <span>${escapeHtml((data.annotation_sources || []).join(", ") || "No CSQ/ANN annotation")}</span>
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || "VCF calls remain dependent on the upstream assay and caller.")}</p>
  `;
}

function renderDnaVariantPreflight(title, data) {
  const inputs = data.inputs || {};
  const reads = data.reads || {};
  const reference = data.reference || {};
  const tools = Object.entries(data.toolchain?.tools || {});
  return `
    <header><strong>${title}</strong><span>${escapeHtml(localized("输入与工具链预检", "input and toolchain preflight"))}</span></header>
    <div class="vcf-input-line">
      <span>${escapeHtml(inputs.sample_id || "sample")}</span>
      <code>${escapeHtml(`${inputs.read1_path || ""} + ${inputs.read2_path || ""}`)}</code>
      <small>${escapeHtml(inputs.reference_path || "")}</small>
    </div>
    <div class="vcf-metrics">
      ${[
        [localized("Read pairs", "Read pairs"), reads.read_pairs || 0],
        [localized("平均读长", "Mean read length"), `${reads.read1?.mean_read_length || 0} bp`],
        [localized("参考碱基", "Reference bases"), Number(reference.total_bases || 0).toLocaleString("en-US")],
        [localized("Contigs", "Contigs"), reference.contig_count || 0],
        [localized("Ploidy", "Ploidy"), inputs.ploidy || 2],
        [localized("线程", "Threads"), inputs.threads || 1],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="dna-toolchain">
      ${tools.map(([name, item]) => `<span class="${item.available ? "available" : "missing"}"><b>${escapeHtml(name)}</b><code>${escapeHtml(item.version || localized("不可用", "unavailable"))}</code></span>`).join("")}
    </div>
    <p class="evidence-caveat">${escapeHtml((data.warnings || [])[0] || localized("此有界流程不是生产级人类 WGS/WES。", "This bounded workflow is not production human WGS/WES."))}</p>
  `;
}

function renderDnaVariantCalling(title, data) {
  const alignment = data.alignment || {};
  const coverage = data.coverage || {};
  const variants = data.variants || [];
  return `
    <header><strong>${title}</strong><span>${escapeHtml(formatTimestamp(data.created_at))}</span></header>
    <div class="vcf-input-line">
      <span>${escapeHtml(data.inputs?.sample_id || "sample")}</span>
      <code>${escapeHtml(data.inputs?.reference_path || "")}</code>
      <small>${escapeHtml(`${data.toolchain?.tools?.bwa?.version || "BWA"} · samtools ${data.toolchain?.tools?.samtools?.version || ""} · bcftools ${data.toolchain?.tools?.bcftools?.version || ""}`)}</small>
    </div>
    <div class="vcf-metrics">
      ${[
        [localized("Read pairs", "Read pairs"), data.reads?.read_pairs || 0],
        [localized("映射率", "Mapped"), `${Number(alignment.mapped_percent || 0).toFixed(1)}%`],
        [localized("Proper pairs", "Proper pairs"), `${Number(alignment.properly_paired_percent || 0).toFixed(1)}%`],
        [localized("覆盖参考", "Reference covered"), `${Number(coverage.covered_percent || 0).toFixed(1)}%`],
        [localized("平均深度", "Mean depth"), `${Number(coverage.mean_depth || 0).toFixed(2)}x`],
        [localized("候选变异", "Candidates"), data.variant_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <section class="vcf-section">
      <header><strong>${escapeHtml(localized("管线阶段", "Pipeline stages"))}</strong><span>BWA-MEM / samtools / bcftools</span></header>
      <div class="dna-stage-list">
        ${(data.stages || []).map((stage) => `<div><strong>${escapeHtml(stage.name || stage.stage || "stage")}</strong><code>${escapeHtml(stage.engine || stage.command || stage.tool || "")}</code><span>${escapeHtml(`${Number(stage.duration_ms || 0).toFixed(0)} ms`)}</span></div>`).join("")}
      </div>
    </section>
    <section class="vcf-section">
      <header><strong>${escapeHtml(localized("候选变异", "Candidate variants"))}</strong><span>${escapeHtml(localized("未过滤研究结果", "unfiltered research output"))}</span></header>
      <div class="dna-variant-table">
        <div><b>Variant</b><b>GT</b><b>DP</b><b>AD</b><b>VAF</b><b>QUAL</b></div>
        ${variants.map((variant) => `<div>
          <strong>${escapeHtml(`${variant.chrom}:${variant.pos} ${variant.ref}>${variant.alt}`)}</strong>
          <code>${escapeHtml(variant.genotype || "./.")}</code>
          <span>${escapeHtml(variant.depth ?? "n/a")}</span>
          <span>${escapeHtml(`${variant.ref_depth ?? "?"},${variant.alt_depth ?? "?"}`)}</span>
          <span>${escapeHtml(formatVaf(variant.vaf))}</span>
          <span>${escapeHtml(variant.quality ?? "n/a")}</span>
        </div>`).join("") || `<p class="vcf-empty">${escapeHtml(localized("没有输出候选变异。", "No candidate variants were emitted."))}</p>`}
      </div>
    </section>
    <div class="dna-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span><b>${escapeHtml(label.replaceAll("_", " "))}</b><code>${escapeHtml(path)}</code></span>`).join("")}</div>
    <p class="evidence-caveat">${escapeHtml(data.analysis_handoff || (data.caveats || [])[0] || localized("候选 VCF 需要独立过滤与验证。", "The candidate VCF requires independent filtering and validation."))}</p>
  `;
}

function renderVcfCohortReview(title, data) {
  const thresholds = data.thresholds || {};
  const sampleQc = data.sample_qc || [];
  const matrix = data.mutation_matrix || {};
  const trajectories = data.trajectories || [];
  const lowFrequency = (data.calls || [])
    .filter((call) => call.included && Number(call.vaf) < Number(thresholds.low_frequency_boundary ?? 0.05))
    .sort((a, b) => Number(a.vaf) - Number(b.vaf));
  return `
    <header>
      <strong>${title}</strong>
      <span>${escapeHtml(formatTimestamp(data.retrieved_at))}</span>
    </header>
    <div class="vcf-input-line">
      <span>${escapeHtml(data.header?.fileformat || "VCF")}</span>
      <code>${escapeHtml(data.inputs?.vcf_path || "")}</code>
      <small>${escapeHtml(data.header?.reference || "Reference not declared")}</small>
    </div>
    <div class="vcf-metrics">
      ${[
        ["Samples", data.sample_count || 0],
        ["Subjects", data.subject_count || 0],
        ["ALT alleles", data.allele_count || 0],
        ["Included calls", data.included_call_count || 0],
        ["Low-frequency", data.low_frequency_call_count || 0],
        ["Recurrent", data.recurrent_variant_count || 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="vcf-filter-line">
      <span>VAF ≥ ${escapeHtml(formatVaf(thresholds.min_vaf))}</span>
      <span>DP ≥ ${escapeHtml(thresholds.min_depth ?? 0)}</span>
      <span>${thresholds.include_filtered ? "Non-PASS included" : "Non-PASS excluded"}</span>
      <span>Low frequency &lt; ${escapeHtml(formatVaf(thresholds.low_frequency_boundary))}</span>
    </div>
    <section class="vcf-section">
      <header><strong>Sample QC</strong><span>observed and qualifying calls</span></header>
      <div class="vcf-sample-qc">
        <div><b>Sample</b><b>Subject / timepoint</b><b>Mean DP</b><b>Observed</b><b>Included</b></div>
        ${sampleQc.map((sample) => `<div>
          <strong>${escapeHtml(sample.sample)}</strong>
          <span>${escapeHtml(`${sample.subject} · ${sample.timepoint}`)}</span>
          <span>${escapeHtml(sample.mean_depth ?? "n/a")}</span>
          <span>${escapeHtml(sample.observed_calls || 0)}</span>
          <span>${escapeHtml(sample.included_calls || 0)}</span>
        </div>`).join("")}
      </div>
    </section>
    <section class="vcf-section">
      <header><strong>Variant landscape</strong><span>top qualifying variants · VAF intensity</span></header>
      ${renderVcfMutationMatrix(matrix)}
      <div class="vcf-matrix-legend"><span><i class="included"></i>Included</span><span><i class="excluded"></i>Observed, excluded</span><span><i></i>Not observed</span></div>
    </section>
    <section class="vcf-section">
      <header><strong>Low-frequency calls</strong><span>included below ${escapeHtml(formatVaf(thresholds.low_frequency_boundary))}</span></header>
      <div class="vcf-call-table">
        <div><b>Variant</b><b>Sample</b><b>VAF</b><b>DP</b></div>
        ${lowFrequency.slice(0, 30).map((call) => `<div>
          <strong>${escapeHtml([call.gene, call.variant_id].filter(Boolean).join(" · "))}</strong>
          <span>${escapeHtml(`${call.subject} · ${call.timepoint}`)}</span>
          <span>${escapeHtml(formatVaf(call.vaf))}</span>
          <span>${escapeHtml(call.depth ?? "n/a")}</span>
        </div>`).join("") || '<p class="vcf-empty">No calls meet the approved low-frequency definition.</p>'}
      </div>
    </section>
    ${trajectories.length ? `<section class="vcf-section">
      <header><strong>Longitudinal trajectories</strong><span>observed VAF · per-series scale</span></header>
      <div class="vcf-trajectories">
        ${trajectories.slice(0, 12).map((trajectory) => renderVcfTrajectory(trajectory)).join("")}
      </div>
    </section>` : ""}
    <div class="vcf-review-footer">
      <p class="evidence-caveat">${escapeHtml((data.caveats || [])[0] || "Processed VCF calls require upstream assay and caller review.")}</p>
      <div class="target-output-paths">${Object.entries(data.outputs || {}).map(([label, path]) => `<span>${escapeHtml(label.replaceAll("_", " "))}<code>${escapeHtml(path)}</code></span>`).join("")}</div>
    </div>
  `;
}

function renderVcfMutationMatrix(matrix) {
  const samples = matrix.samples || [];
  const variants = matrix.variants || [];
  if (!samples.length || !variants.length) return '<p class="vcf-empty">No calls met the approved filters.</p>';
  return `
    <div class="vcf-matrix-scroll">
      <div class="vcf-matrix" style="--vcf-samples:${samples.length}">
        <span></span>
        ${samples.map((sample) => `<small title="${escapeHtml(sample)}">${escapeHtml(shortSampleLabel(sample))}</small>`).join("")}
        ${variants.map((variant) => `
          <strong title="${escapeHtml(`${variant.gene || "Unannotated"} · ${variant.variant_id}`)}"><b>${escapeHtml(variant.gene || "Unannotated")}</b><small>${escapeHtml(variant.hgvsp || variant.variant_id)}</small></strong>
          ${(variant.values || []).map((value, index) => {
            const className = value.included ? "included" : value.observed ? "excluded" : "empty";
            return `<i class="${className}" style="--vcf-fill:${vcfCellFill(value)}" title="${escapeHtml(`${samples[index]} · ${variant.variant_id} · ${value.observed ? `VAF ${formatVaf(value.vaf)} · ${value.status}` : "not observed"}`)}"></i>`;
          }).join("")}
        `).join("")}
      </div>
    </div>
  `;
}

function renderVcfTrajectory(trajectory) {
  const points = trajectory.points || [];
  const observed = points.filter((point) => Number.isFinite(Number(point.vaf)));
  const maximum = Math.max(0.1, ...observed.map((point) => Number(point.vaf)));
  const coordinates = points.map((point, index) => {
    const x = points.length > 1 ? 16 + (index / (points.length - 1)) * 268 : 150;
    const y = Number.isFinite(Number(point.vaf)) ? 70 - (Number(point.vaf) / maximum) * 54 : null;
    return { ...point, x, y };
  });
  const lineSegments = [];
  let segment = [];
  coordinates.forEach((point) => {
    if (point.y === null) {
      if (segment.length > 1) lineSegments.push(segment);
      segment = [];
      return;
    }
    segment.push(point);
  });
  if (segment.length > 1) lineSegments.push(segment);
  return `
    <article class="vcf-trajectory">
      <header><strong>${escapeHtml([trajectory.gene, trajectory.variant_id].filter(Boolean).join(" · "))}</strong><span>${escapeHtml(trajectory.subject)}</span></header>
      <svg viewBox="0 0 300 84" role="img" aria-label="${escapeHtml(`${trajectory.subject} ${trajectory.variant_id} VAF trajectory`)}">
        <line x1="16" y1="70" x2="284" y2="70"></line>
        <line x1="16" y1="16" x2="16" y2="70"></line>
        ${lineSegments.map((items) => `<polyline points="${items.map((point) => `${point.x},${point.y}`).join(" ")}"></polyline>`).join("")}
        ${coordinates.filter((point) => point.y !== null).map((point) => `<circle cx="${point.x}" cy="${point.y}" r="3"><title>${escapeHtml(`${point.sample} · ${point.timepoint} · VAF ${formatVaf(point.vaf)} · DP ${point.depth ?? "n/a"}`)}</title></circle>`).join("")}
      </svg>
      <div class="vcf-trajectory-labels">${points.map((point) => `<span>${escapeHtml(point.timepoint)}</span>`).join("")}</div>
      <small>0–${escapeHtml(formatVaf(maximum))} VAF</small>
    </article>
  `;
}

function formatVaf(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "n/a";
  return `${(number * 100).toFixed(number < 0.01 ? 2 : 1).replace(/\.0$/, "")}%`;
}

function shortSampleLabel(value) {
  const text = String(value || "");
  return text.length > 10 ? `${text.slice(0, 8)}…` : text;
}

function vcfCellFill(value) {
  if (!value?.observed) return "#f4f2ed";
  if (!value.included) return "#d8d0c4";
  return mixHex("#dce9e6", "#147d72", clamp(Number(value.vaf || 0) * 2.5, 0.12, 1));
}

function renderRnaseqPreflight(title, data) {
  const contrast = data.contrast || {};
  return `
    <header><strong>${title}</strong><span>input validation</span></header>
    <div class="rnaseq-metrics">
      ${[
        ["Samples", data.samples || 0],
        ["Genes", data.genes || 0],
        ["Tested", data.genes_after_filter || 0],
        ["Design", data.design_formula || "n/a"],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="rnaseq-design">
      <code>${escapeHtml(`${contrast.test || "test"} vs ${contrast.reference || "reference"}`)}</code>
      <span>${escapeHtml(data.count_matrix_path || "")}</span>
      <span>${escapeHtml(data.metadata_path || "")}</span>
    </div>
    ${renderSampleQc(data.sample_qc || [])}
    ${(data.warnings || []).map((warning) => `<p class="rnaseq-warning">${escapeHtml(warning)}</p>`).join("")}
  `;
}

function renderTranscriptomicsResult(title, data) {
  const contrast = data.contrast || {};
  const pca = data.pca || {};
  const pcaPoints = pca.points || [];
  const conditions = Array.from(new Set(pcaPoints.map((point) => point.condition)));
  const xValues = pcaPoints.map((point) => Number(point.pc1) || 0);
  const yValues = pcaPoints.map((point) => Number(point.pc2) || 0);
  const xMin = Math.min(...xValues, -1);
  const xMax = Math.max(...xValues, 1);
  const yMin = Math.min(...yValues, -1);
  const yMax = Math.max(...yValues, 1);
  const volcanoPoints = (data.volcano?.points || [])
    .filter((point) => Number.isFinite(Number(point.log2_fold_change)))
    .slice(0, 1000);
  const volcanoX = Math.max(1, ...volcanoPoints.map((point) => Math.abs(Number(point.log2_fold_change))));
  const volcanoY = Math.max(1, percentile(volcanoPoints.map((point) => Number(point.neg_log10_padj) || 0), 0.9));
  const heatmap = data.heatmap || {};
  const heatmapSamples = heatmap.samples || [];
  const heatmapGenes = heatmap.genes || [];
  const topGenes = (data.top_genes || []).slice(0, 10);
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${data.method || "PyDESeq2"} ${data.method_version || ""}`.trim())}</span></header>
    <div class="rnaseq-metrics">
      ${[
        ["Samples", data.samples || 0],
        ["Genes tested", data.genes_tested || 0],
        ["Significant", data.significant_genes || 0],
        ["Up / down", `${data.upregulated || 0} / ${data.downregulated || 0}`],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="rnaseq-design">
      <code>${escapeHtml(data.design_formula || "~condition")}</code>
      <span>${escapeHtml(`${contrast.test || "test"} vs ${contrast.reference || "reference"}`)}</span>
      <span>${escapeHtml(`FDR ${data.thresholds?.fdr ?? "n/a"} · |log2FC| ${data.thresholds?.absolute_log2_fold_change ?? "n/a"}`)}</span>
    </div>
    ${renderSampleQc(data.sample_qc || [])}
    <section class="rnaseq-section">
      <header><strong>Sample PCA</strong><span>${escapeHtml(`PC1 ${pca.variance_explained?.[0] || 0}% · PC2 ${pca.variance_explained?.[1] || 0}%`)}</span></header>
      <div class="rnaseq-legend">
        ${conditions.map((condition, index) => `<span><i class="condition-${index % 6}"></i>${escapeHtml(condition)}</span>`).join("")}
      </div>
      <div class="pca-plot" aria-label="PCA of log normalized counts">
        <span class="plot-axis plot-axis-x"></span><span class="plot-axis plot-axis-y"></span>
        ${pcaPoints.map((point) => {
          const conditionIndex = Math.max(0, conditions.indexOf(point.condition));
          return `<i class="pca-point condition-${conditionIndex % 6}" title="${escapeHtml(`${point.sample} · ${point.condition} · PC1 ${point.pc1}, PC2 ${point.pc2}`)}" style="--x:${normalizePlot(point.pc1, xMin, xMax)}%;--y:${100 - normalizePlot(point.pc2, yMin, yMax)}%"></i>`;
        }).join("")}
      </div>
    </section>
    <section class="rnaseq-section">
      <header><strong>Volcano</strong><span>${escapeHtml(`${data.volcano?.shown || 0} / ${data.volcano?.total || 0} genes`)}</span></header>
      <div class="volcano-plot" aria-label="Differential-expression volcano plot">
        <span class="plot-axis plot-axis-x"></span><span class="plot-axis plot-axis-y"></span>
        ${volcanoPoints.map((point) => {
          const status = ["up", "down"].includes(point.status) ? point.status : "not-significant";
          const x = ((Number(point.log2_fold_change) + volcanoX) / (volcanoX * 2)) * 100;
          const y = (Math.min(Number(point.neg_log10_padj) || 0, volcanoY) / volcanoY) * 100;
          return `<i class="volcano-point ${status}" title="${escapeHtml(`${point.gene_id} · log2FC ${Number(point.log2_fold_change).toFixed(2)} · padj ${formatScientific(point.padj)}`)}" style="--x:${clamp(x, 1, 99)}%;--y:${100 - clamp(y, 1, 99)}%"></i>`;
        }).join("")}
      </div>
      <div class="volcano-key"><span><i class="up"></i>Up</span><span><i class="down"></i>Down</span><span><i></i>Not significant</span></div>
    </section>
    <section class="rnaseq-section">
      <header><strong>Top-gene heatmap</strong><span>${escapeHtml(heatmap.scale || "z-score")}</span></header>
      <div class="heatmap-scroll">
        <div class="heatmap-grid" style="--sample-count:${Math.max(1, heatmapSamples.length)}">
          <span></span>${heatmapSamples.map((sample) => `<small title="${escapeHtml(sample)}">${escapeHtml(sample.slice(0, 4))}</small>`).join("")}
          ${heatmapGenes.map((gene, rowIndex) => `
            <strong title="${escapeHtml(gene)}">${escapeHtml(gene)}</strong>
            ${(heatmap.values?.[rowIndex] || []).map((value) => `<i class="heat-cell" title="${escapeHtml(`${gene} · z ${value}`)}" style="--heat:${heatmapColor(value)}"></i>`).join("")}
          `).join("")}
        </div>
      </div>
    </section>
    <section class="rnaseq-section">
      <header><strong>Ranked genes</strong><span>adjusted p-value</span></header>
      <div class="gene-table">
        <div><b>Gene</b><b>log2FC</b><b>padj</b><b>Status</b></div>
        ${topGenes.map((gene) => `<div><strong>${escapeHtml(gene.gene_id)}</strong><span>${escapeHtml(formatDecimal(gene.log2_fold_change, 2))}</span><span>${escapeHtml(formatScientific(gene.padj))}</span><span class="gene-status ${escapeHtml(gene.status)}">${escapeHtml(gene.status)}</span></div>`).join("")}
      </div>
    </section>
    <div class="rnaseq-outputs">
      <strong>Saved outputs</strong>
      ${Object.values(data.outputs || {}).map((path) => `<code>${escapeHtml(path)}</code>`).join("")}
    </div>
    ${(data.warnings || []).length ? `<details class="rnaseq-notes"><summary>${escapeHtml(`${data.warnings.length} analysis note(s)`)}</summary>${data.warnings.map((warning) => `<p>${escapeHtml(warning)}</p>`).join("")}</details>` : ""}
    <p>${escapeHtml(data.caveats?.[0] || "Differential expression requires study-design review and biological validation.")}</p>
  `;
}

function renderSampleQc(rows) {
  if (!rows.length) return "";
  return `
    <div class="sample-qc-table">
      <div><b>Sample</b><b>Condition</b><b>Library</b><b>Detected</b></div>
      ${rows.slice(0, 20).map((row) => `<div><strong title="${escapeHtml(row.sample)}">${escapeHtml(row.sample)}</strong><span>${escapeHtml(row.condition)}</span><span>${escapeHtml(Number(row.library_size || 0).toLocaleString())}</span><span>${escapeHtml(row.detected_genes || 0)}</span></div>`).join("")}
    </div>
  `;
}

const SINGLE_CELL_COLORS = ["#176f68", "#b06d27", "#6f5d9a", "#3f7144", "#9c4253", "#36789a", "#8b6c3f", "#58606d"];

function renderSingleCellPreflight(title, data) {
  const parameters = data.parameters || {};
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`Scanpy ${data.toolchain?.scanpy_version || "unavailable"}`)}</span></header>
    <div class="single-cell-input-line">
      <span>${escapeHtml(`${data.input_format || "table"} · ${data.count_layer || "X"}`)}</span><code>${escapeHtml(data.count_matrix_path || "")}</code>
      ${data.metadata_path ? `<small>${escapeHtml(data.metadata_path)}</small>` : `<small>${escapeHtml(`${(data.input_files || []).length} input file(s)`)}</small>`}
    </div>
    <div class="single-cell-metrics">
      ${[
        ["Cells", Number(data.cells || 0).toLocaleString("en-US")],
        ["Genes", Number(data.genes || 0).toLocaleString("en-US")],
        ["Cells retained", Number(data.cells_after_filter || 0).toLocaleString("en-US")],
        ["Genes retained", Number(data.genes_after_filter || 0).toLocaleString("en-US")],
        ["Sparsity", `${data.sparsity_percent || 0}%`],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="single-cell-thresholds">
      <span>≥ ${escapeHtml(parameters.min_genes || 0)} genes / cell</span>
      <span>≥ ${escapeHtml(parameters.min_cells || 0)} cells / gene</span>
      <span>MT ≤ ${escapeHtml(parameters.max_mito_percent ?? 100)}%</span>
      <span>${escapeHtml(parameters.n_neighbors || 0)} neighbors</span>
      <span>Leiden ${escapeHtml(parameters.leiden_resolution || 1)}</span>
      <span>${parameters.run_scrublet ? escapeHtml(`Scrublet · ${parameters.doublet_batch_key || "all cells"} · expected ${formatDecimal(Number(parameters.expected_doublet_rate || 0) * 100, 1)}%${parameters.exclude_predicted_doublets ? " · exclude" : " · retain"}`) : "Scrublet off"}</span>
    </div>
    ${(data.metadata?.categorical_columns || []).length ? `<div class="single-cell-metadata">${data.metadata.categorical_columns.map((field) => `<span><strong>${escapeHtml(field.column)}</strong>${escapeHtml(`${field.levels} levels`)}</span>`).join("")}</div>` : ""}
    ${(data.warnings || []).map((warning) => `<p class="single-cell-warning">${escapeHtml(warning)}</p>`).join("")}
  `;
}

function renderSingleCellAnalysis(title, data) {
  const points = data.embedding?.points || [];
  const qcPoints = data.qc?.points || [];
  const xValues = points.map((point) => Number(point.umap_1) || 0);
  const yValues = points.map((point) => Number(point.umap_2) || 0);
  const xMin = Math.min(...xValues, -1);
  const xMax = Math.max(...xValues, 1);
  const yMin = Math.min(...yValues, -1);
  const yMax = Math.max(...yValues, 1);
  const qcX = qcPoints.map((point) => Number(point.total_counts) || 0);
  const qcY = qcPoints.map((point) => Number(point.n_genes_by_counts) || 0);
  const qcXMin = Math.min(...qcX, 0);
  const qcXMax = Math.max(...qcX, 1);
  const qcYMin = Math.min(...qcY, 0);
  const qcYMax = Math.max(...qcY, 1);
  const metadataFields = (data.metadata_fields || []).filter((field) => {
    const levels = new Set(points.map((point) => String(point[field] ?? "")).filter(Boolean));
    return levels.size > 1 && levels.size <= 30;
  });
  const colorKeys = ["cluster", ...(data.doublet?.enabled ? ["predicted_doublet"] : []), ...metadataFields];
  const markerPlot = data.marker_dotplot || {};
  const markerGenes = (markerPlot.genes || []).slice(0, 24);
  const markerClusters = markerPlot.clusters || [];
  const markerValues = markerPlot.values || [];
  const maximumMarkerMean = Math.max(1, ...markerValues.map((value) => Number(value.mean) || 0));
  const topMarkers = (data.markers || []).slice(0, 40);
  return `
    <header><strong>${title}</strong><span>${escapeHtml(`${data.method || "Scanpy"} ${data.method_version || ""}`.trim())}</span></header>
    <div class="single-cell-metrics">
      ${[
        ["Cells retained", `${Number(data.cells_retained || 0).toLocaleString("en-US")} / ${Number(data.cells_input || 0).toLocaleString("en-US")}`],
        ["Genes retained", `${Number(data.genes_retained || 0).toLocaleString("en-US")} / ${Number(data.genes_input || 0).toLocaleString("en-US")}`],
        ["HVG", Number(data.highly_variable_genes || 0).toLocaleString("en-US")],
        ["Clusters", data.clusters || 0],
        ["Doublets", data.doublet?.enabled ? `${data.doublet.predicted || 0}${data.doublet.excluded ? ` / ${data.doublet.excluded} excluded` : " predicted"}` : "not run"],
        ["Seed", data.random_seed ?? 0],
      ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}
    </div>
    <div class="single-cell-method-line">
      <span>${escapeHtml(`${data.input_format || "raw"} · ${data.count_layer || "X"}`)}</span><i></i><span>QC</span>${data.doublet?.enabled ? `<i></i><span>${escapeHtml(`Scrublet ${data.doublet.excluded ? "exclude" : "score"}`)}</span>` : ""}<i></i><span>CP10k + log1p</span><i></i><span>HVG / PCA</span><i></i><span>Neighbors / UMAP / Leiden</span>
    </div>
    <section class="single-cell-section">
      <header><div><strong>Cell embedding</strong><span>${escapeHtml(`UMAP · ${data.embedding?.shown || 0} / ${data.embedding?.total || 0} cells`)}</span></div><div class="single-cell-color-control" role="group" aria-label="Color cell embedding">${colorKeys.map((key, index) => `<button type="button" data-single-cell-color="${escapeHtml(key)}" class="${index === 0 ? "is-active" : ""}">${escapeHtml(key)}</button>`).join("")}</div></header>
      <div class="single-cell-legend" aria-live="polite"></div>
      <div class="single-cell-umap" aria-label="UMAP embedding of retained cells">
        ${points.map((point, index) => `<i class="single-cell-umap-point" data-point-index="${index}" title="${escapeHtml(`${point.cell_id} · cluster ${point.cluster}`)}" style="--x:${normalizePlot(point.umap_1, xMin, xMax)}%;--y:${100 - normalizePlot(point.umap_2, yMin, yMax)}%;--point-color:${SINGLE_CELL_COLORS[Number(point.cluster || 0) % SINGLE_CELL_COLORS.length]}"></i>`).join("")}
        <span class="single-cell-axis-x">UMAP 1</span><span class="single-cell-axis-y">UMAP 2</span>
      </div>
    </section>
    <section class="single-cell-section single-cell-qc-section">
      <header><div><strong>Cell QC</strong><span>${escapeHtml(`${data.qc?.shown || 0} / ${data.qc?.total || 0} cells`)}</span></div><div class="single-cell-qc-key"><span><i></i>Retained</span><span><i></i>Excluded</span></div></header>
      <div class="single-cell-qc-plot" aria-label="Cell library size and detected genes">
        ${qcPoints.map((point) => `<i class="${point.retained ? "retained" : "excluded"}" title="${escapeHtml(`${point.cell_id} · ${point.total_counts} counts · ${point.n_genes_by_counts} genes · MT ${formatDecimal(point.pct_counts_mt, 2)}%`)}" style="--x:${normalizePlot(point.total_counts, qcXMin, qcXMax)}%;--y:${100 - normalizePlot(point.n_genes_by_counts, qcYMin, qcYMax)}%"></i>`).join("")}
        <span class="single-cell-axis-x">Total counts</span><span class="single-cell-axis-y">Detected genes</span>
      </div>
    </section>
    <section class="single-cell-section">
      <header><div><strong>Leiden clusters</strong><span>${escapeHtml(`resolution ${data.parameters?.leiden_resolution ?? "n/a"}`)}</span></div></header>
      <div class="single-cell-cluster-table">
        <div><b>Cluster</b><b>Cells</b><b>Share</b><b>Top markers</b></div>
        ${(data.cluster_summary || []).map((cluster) => `<div><strong><i style="--cluster-color:${SINGLE_CELL_COLORS[Number(cluster.cluster || 0) % SINGLE_CELL_COLORS.length]}"></i>${escapeHtml(cluster.cluster)}</strong><span>${escapeHtml(cluster.cells)}</span><span>${escapeHtml(`${cluster.percent}%`)}</span><span title="${escapeHtml(cluster.top_markers || "")}">${escapeHtml(cluster.top_markers || "No marker ranking")}</span></div>`).join("")}
      </div>
    </section>
    ${markerGenes.length ? `<section class="single-cell-section"><header><div><strong>Marker expression</strong><span>${escapeHtml(markerPlot.scale || "mean log1p CP10k")}</span></div></header><div class="single-cell-dotplot-scroll"><div class="single-cell-dotplot" style="--marker-count:${markerGenes.length}"><span></span>${markerGenes.map((gene) => `<b title="${escapeHtml(gene)}">${escapeHtml(gene)}</b>`).join("")}${markerClusters.map((cluster) => `<strong>${escapeHtml(cluster)}</strong>${markerGenes.map((gene) => { const value = markerValues.find((item) => String(item.cluster) === String(cluster) && item.gene === gene) || {}; const fraction = Number(value.fraction) || 0; const mean = Number(value.mean) || 0; return `<i title="${escapeHtml(`Cluster ${cluster} · ${gene} · ${formatDecimal(fraction * 100, 1)}% expressed · mean ${formatDecimal(mean, 2)}`)}" style="--dot-size:${4 + fraction * 13}px;--dot-color:${mixHex("#ddd9d0", "#176f68", mean / maximumMarkerMean)}"></i>`; }).join("")}`).join("")}</div></div></section>` : ""}
    <section class="single-cell-section">
      <header><div><strong>Cluster marker ranking</strong><span>Wilcoxon · cluster vs rest</span></div></header>
      <div class="single-cell-marker-table">
        <div><b>Cluster</b><b>Gene</b><b>logFC</b><b>adj. p</b><b>Detected</b></div>
        ${topMarkers.map((marker) => `<div><strong>${escapeHtml(marker.cluster)}</strong><span>${escapeHtml(marker.gene)}</span><span>${escapeHtml(formatDecimal(marker.logfoldchange, 2))}</span><span>${escapeHtml(formatScientific(marker.pvalue_adj))}</span><span>${escapeHtml(`${formatDecimal(Number(marker.pct_cluster || 0) * 100, 1)}% / ${formatDecimal(Number(marker.pct_rest || 0) * 100, 1)}%`)}</span></div>`).join("")}
      </div>
    </section>
    <div class="single-cell-outputs"><strong>Saved outputs</strong>${Object.values(data.outputs || {}).map((path) => `<code>${escapeHtml(path)}</code>`).join("")}</div>
    ${(data.warnings || []).length ? `<details class="single-cell-notes"><summary>${escapeHtml(`${data.warnings.length} analysis note(s)`)}</summary>${data.warnings.map((warning) => `<p>${escapeHtml(warning)}</p>`).join("")}</details>` : ""}
    <p class="evidence-caveat">${escapeHtml(data.caveats?.[0] || "Clusters and UMAP coordinates are exploratory and do not establish cell identity.")}</p>
  `;
}

function bindSingleCellControls(card, data) {
  const points = data.embedding?.points || [];
  const buttons = Array.from(card.querySelectorAll("[data-single-cell-color]"));
  const plotPoints = Array.from(card.querySelectorAll(".single-cell-umap-point"));
  const legend = card.querySelector(".single-cell-legend");
  function update(key) {
    const categories = Array.from(new Set(points.map((point) => String(point[key] ?? "unknown")))).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    const colorByValue = new Map(categories.map((value, index) => [value, SINGLE_CELL_COLORS[index % SINGLE_CELL_COLORS.length]]));
    plotPoints.forEach((element, index) => {
      const point = points[index] || {};
      const value = String(point[key] ?? "unknown");
      element.style.setProperty("--point-color", colorByValue.get(value));
      element.title = `${point.cell_id || "cell"} · ${key} ${value}`;
    });
    buttons.forEach((button) => button.classList.toggle("is-active", button.dataset.singleCellColor === key));
    if (legend) legend.innerHTML = categories.map((value) => `<span><i style="--legend-color:${colorByValue.get(value)}"></i>${escapeHtml(value)}</span>`).join("");
  }
  buttons.forEach((button) => button.addEventListener("click", () => update(button.dataset.singleCellColor)));
  update("cluster");
}

function renderSkills() {
  els.skillList.innerHTML = "";
  if (!state.skills.length) {
    els.skillList.innerHTML = `<div class="skill-card"><span>Skills</span><p>${escapeHtml(ui("localServiceDisconnected"))}</p></div>`;
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
    els.workflowList.innerHTML = `<div class="workflow-empty"><span>${escapeHtml(ui("analysisPlans"))}</span><p>${escapeHtml(ui("noRuns"))}</p></div>`;
    return;
  }

  state.workflowRuns
    .slice()
    .slice(0, 5)
    .forEach((run) => {
      const item = document.createElement("article");
      item.className = "workflow-run";
      const preflight = run.preflight || null;
      const steps = (run.steps || [])
        .map(
          (step, index) => `
            <li>
              <span>${index + 1}</span>
              <div><strong>${escapeHtml(state.language === "en" && containsHan(step.title) ? humanize(step.tool) : step.title || step.tool)}</strong><code>${escapeHtml(step.tool || "")}</code></div>
              <small class="workflow-step-status ${escapeHtml(step.status || "pending")}">${escapeHtml(workflowStatusLabel(step.status))}</small>
            </li>`,
        )
        .join("");
      item.innerHTML = `
        <header>
          <div><strong>${escapeHtml(workflowRunText(run, 0))}</strong><small>${escapeHtml(workflowRunText(run, 1))}</small></div>
          <span class="workflow-status ${escapeHtml(run.status || "pending_approval")}">${escapeHtml(workflowStatusLabel(run.status))}</span>
        </header>
        ${preflight ? renderWorkflowPreflight(preflight) : ""}
        <ol>${steps}</ol>
        ${run.error ? `<p class="workflow-error">${escapeHtml(run.error)}</p>` : ""}
        ${
          run.status === "pending_approval"
            ? `<div class="workflow-actions"><button class="secondary-button workflow-cancel" type="button">${escapeHtml(ui("cancel"))}</button><button class="primary-button workflow-approve" type="button">${escapeHtml(ui("approveAndRun"))}</button></div>`
            : ""
        }
      `;
      item.querySelector(".workflow-approve")?.addEventListener("click", () => approveWorkflow(run.id));
      item.querySelector(".workflow-cancel")?.addEventListener("click", () => cancelWorkflow(run.id));
      els.workflowList.appendChild(item);
    });
}

function renderWorkflowPreflight(preflight) {
  let detail = "";
  if (preflight.disease && preflight.targets) {
    detail = `${preflight.disease.name} · ${(preflight.targets || []).map((target) => target.symbol).join(", ")}`;
  } else if (preflight.exact_query && preflight.hit_count !== undefined) {
    detail = `${preflight.organism ? `${preflight.organism} · ` : ""}${preflight.exact_query} · ${Number(preflight.hit_count || 0).toLocaleString("en-US")} matches`;
  } else if (preflight.variant?.accession) {
    detail = `${preflight.variant.accession} · ${preflight.variant.hgvs_c || preflight.variant.canonical_spdi || preflight.query}`;
  } else if (preflight.condition && preflight.hit_count !== undefined) {
    detail = `${preflight.condition}${preflight.intervention ? ` · ${preflight.intervention}` : ""} · ${Number(preflight.hit_count || 0).toLocaleString("en-US")} studies`;
  } else if (preflight.study?.nct_id || preflight.nct_id) {
    detail = `${preflight.study?.nct_id || preflight.nct_id} · ${preflight.primary_outcome_count || 0} primary outcomes · ${preflight.serious_event_term_count || 0} serious AE terms`;
  } else if (preflight.vcf_path) {
    detail = `${preflight.vcf_path} · ${preflight.sample_count || 0} samples · ${preflight.record_count || 0} records`;
  } else if (preflight.inputs?.read1_path && preflight.reads?.read_pairs !== undefined) {
    detail = `${preflight.inputs.read1_path} + ${preflight.inputs.read2_path} · ${preflight.reads.read_pairs || 0} read pairs · ${preflight.reference?.total_bases || 0} reference bases`;
  } else if (preflight.hmm_path) {
    detail = `${preflight.hmm_path} · ${preflight.model_count || 0} models · ${preflight.sequence_count || 0} sequences`;
  } else if (preflight.inputs?.fasta_path && preflight.reference?.site) {
    detail = `${preflight.inputs.fasta_path} · ${preflight.sequence_count || 0} sequences · ${preflight.reference.id}:${preflight.reference.site}`;
  } else if (preflight.input_mode === "cell_by_gene_raw_counts") {
    detail = `${preflight.count_matrix_path} · ${preflight.input_format || "table"} / ${preflight.count_layer || "X"} · ${preflight.cells_after_filter || 0} cells · ${preflight.genes_after_filter || 0} genes`;
  } else if (preflight.mappings && preflight.organism?.taxon_id) {
    detail = `${preflight.organism.name || "Homo sapiens"} · ${preflight.mapped_count || 0}/${(preflight.input_terms || []).length} STRING mappings · score ≥ ${preflight.parameters?.required_score || 400}`;
  } else if (preflight.design_formula || preflight.contrast) {
    detail = `${preflight.design_formula || ""} · ${preflight.contrast?.test || "test"} vs ${preflight.contrast?.reference || "reference"}`;
  } else if (preflight.entry?.pdb_id && preflight.site?.variant) {
    detail = `${preflight.entry.pdb_id} · ${preflight.site.chain}:${preflight.site.observed_residue}${preflight.site.author_residue_number} · ${preflight.site.structure_allele} allele · ${preflight.site.contact_count || 0} contacts`;
  }
  const summary = state.language === "en" && containsHan(preflight.summary) ? ui("inputsValidated") : preflight.summary || ui("inputsValidated");
  return `<div class="workflow-preflight"><strong>${escapeHtml(ui("preflightReady"))}</strong><span>${escapeHtml(summary)}</span>${detail ? `<code>${escapeHtml(detail)}</code>` : ""}</div>`;
}

function workflowStatusLabel(status) {
  return (
    {
      pending_approval: ui("statusPendingApproval"),
      pending: ui("statusPending"),
      running: ui("statusRunning"),
      completed: ui("statusCompleted"),
      failed: ui("statusFailed"),
      error: ui("statusFailed"),
      skipped: ui("statusSkipped"),
      cancelled: ui("statusCancelled"),
    }[status] || status || ui("statusPending")
  );
}

function renderWorkspaceFiles() {
  els.workspaceFileList.innerHTML = "";
  els.workspaceFileCount.textContent = ui("files", { count: state.workspaceFiles.length });
  state.workspaceFiles.slice(0, 10).forEach((file) => {
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
        runAgent(ui("readWorkspaceFile", { path: file.path }));
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
    empty.innerHTML = `<span>${escapeHtml(ui("noCandidatesTitle"))}</span><p>${escapeHtml(ui("noCandidates"))}</p>`;
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
    const text = message.i18nKey ? ui(message.i18nKey, message.values) : message.text;
    item.innerHTML = `
      ${message.role === "system" ? "" : `<strong>${message.role === "user" ? "You" : "molemo Agent"}</strong>`}
      <p>${escapeHtml(text)}</p>
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
    : ui("localScientificRuntime");
  els.apiBadge.textContent = useApi ? ui("providerEnabled") : ui("localOnly");
  els.apiBadge.style.background = useApi ? "var(--green-soft)" : "var(--amber-soft)";
  els.apiBadge.style.color = useApi ? "var(--green)" : "var(--amber)";
}

function renderLocalStatus() {
  if (!state.localService.loaded) {
    els.localStatusText.textContent = ui("connecting");
    return;
  }
  els.localStatusText.textContent = state.localService.connected
    ? ui("localAgentReady", { count: state.localService.skillCount })
    : ui("localServiceStopped");
}

function openWorkflowDialog() {
  if (!state.workflowTemplates.length) {
    addUiMessage("workflowCatalogUnavailable");
    return;
  }
  const preferred = defaultWorkflowTemplate(getActiveSample());
  els.workflowTemplate.innerHTML = state.workflowTemplates
    .map(
      (template) =>
        `<option value="${escapeHtml(template.id)}" ${template.id === preferred ? "selected" : ""}>${escapeHtml(workflowText(template, 0))}</option>`,
    )
    .join("");
  renderWorkflowFields();
  if (!els.workflowDialog.open) els.workflowDialog.showModal();
}

function renderWorkflowFields() {
  const template = state.workflowTemplates.find((item) => item.id === els.workflowTemplate.value);
  els.workflowFields.innerHTML = "";
  if (!template) return;
  els.workflowDescription.textContent = workflowText(template, 1);
  (template.fields || []).forEach((field) => {
    const wrapper = document.createElement("label");
    wrapper.className = "workflow-field";
    wrapper.dataset.workflowFieldWrapper = field.name;
    const label = document.createElement("span");
    label.textContent = localizedWorkflowField(field);
    const control = createWorkflowControl(template.id, field);
    wrapper.append(label, control);
    els.workflowFields.appendChild(wrapper);
  });
  if (template.id === "protein-structure-review") {
    const source = els.workflowFields.querySelector('[data-workflow-field="source"]');
    source?.addEventListener("change", updateStructureWorkflowFields);
    updateStructureWorkflowFields();
  }
}

function updateStructureWorkflowFields() {
  const source = els.workflowFields.querySelector('[data-workflow-field="source"]')?.value || "rcsb";
  const visibleField = { rcsb: "pdb_id", alphafold: "uniprot_accession", workspace: "path" }[source];
  for (const name of ["pdb_id", "uniprot_accession", "path"]) {
    const wrapper = els.workflowFields.querySelector(`[data-workflow-field-wrapper="${name}"]`);
    if (wrapper) wrapper.hidden = name !== visibleField;
  }
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
      item.textContent = localizedWorkflowOption(option);
      control.appendChild(item);
    });
  } else {
    control = document.createElement("input");
    control.type = field.type === "number" ? "number" : "text";
    if (field.min !== undefined) control.min = field.min;
    if (field.max !== undefined) control.max = field.max;
    if (field.step !== undefined) control.step = field.step;
  }
  control.dataset.workflowField = field.name;
  control.required = Boolean(field.required);
  control.placeholder = field.placeholder || "";
  control.value = workflowFieldDefault(templateId, field);
  return control;
}

function workflowFieldDefault(templateId, field) {
  const sample = getActiveSample();
  if (templateId === "protein-family-conservation-review" && field.name === "fasta_path") return "examples/ras_family.faa";
  if (templateId === "protein-family-conservation-review" && field.name === "reference_id") return "P01116|KRAS";
  if (templateId === "protein-family-conservation-review" && field.name === "site") return "G12C";
  if (templateId === "protein-variant-structure-review" && field.name === "pdb_id") return sample.pdbId || "6OIM";
  if (templateId === "protein-variant-structure-review" && field.name === "chain") return sample.structure?.focus?.chain || "A";
  if (templateId === "protein-variant-structure-review" && field.name === "variant") return sample.structure?.focus?.variant || sample.metadata?.variant || "G12C";
  if (templateId === "gene-set-functional-analysis" && field.name === "genes") return "TP53, MDM2, ATM, CDKN1A";
  if (templateId === "target-evidence-review" && field.name === "disease") return "asthma";
  if (templateId === "target-evidence-review" && field.name === "candidates") return "IL4R, TSLP, IL6R, JAK1";
  if (templateId === "target-ligand-bioactivity-review" && field.name === "accession") return sample.metadata?.accession || "P00533";
  if (templateId === "literature-evidence-review" && field.name === "query") return "(IL4R OR TSLP) AND asthma";
  if (templateId === "variant-evidence-review" && field.name === "variant") return "NM_000518.5:c.20A>T";
  if (templateId === "clinical-trial-landscape-review" && field.name === "condition") return "asthma";
  if (templateId === "clinical-trial-landscape-review" && field.name === "intervention") return "dupilumab";
  if (templateId === "clinical-trial-results-review" && field.name === "nct_id") return "NCT02414854";
  if (templateId === "vcf-cohort-review" && field.name === "vcf_path") return "examples/ctdna_variants.vcf";
  if (templateId === "vcf-cohort-review" && field.name === "metadata_path") return "examples/ctdna_metadata.csv";
  if (templateId === "paired-end-dna-variant-calling" && field.name === "read1_path") return "examples/dna_variant_R1.fastq";
  if (templateId === "paired-end-dna-variant-calling" && field.name === "read2_path") return "examples/dna_variant_R2.fastq";
  if (templateId === "paired-end-dna-variant-calling" && field.name === "reference_path") return "examples/dna_variant_reference.fa";
  if (templateId === "hmmer-profile-search" && field.name === "hmm_path") return "examples/ubiquitin_demo.hmm";
  if (templateId === "hmmer-profile-search" && field.name === "database_path") return "examples/hmmer_targets.faa";
  if (templateId === "single-cell-exploratory-analysis" && field.name === "count_matrix_path") return "examples/single_cell_demo.h5ad";
  if (templateId === "single-cell-exploratory-analysis" && field.name === "metadata_path") return "";
  if (templateId === "single-cell-exploratory-analysis" && field.name === "count_layer") return "counts";
  if (field.name === "smiles") return sample.smiles || "";
  if (field.name === "sequence" || field.name === "sequence_a") return sample.sequence || "";
  if (field.name === "pdb_id") return sample.pdbId || "";
  if (field.name === "uniprot_accession") return sample.metadata?.accession || "";
  if (field.name === "source") {
    if (templateId === "protein-structure-review") {
      if (sample.metadata?.coordinateType === "predicted") return "alphafold";
      return sample.metadata?.sourcePath || sample.metadata?.path ? "workspace" : "rcsb";
    }
    return field.options?.[0]?.value || field.value || "";
  }
  if (field.name === "path") return sample.metadata?.sourcePath || sample.metadata?.path || "";
  if (field.name === "query") return sample.metadata?.accession || sample.shortName || "";
  if (field.type === "select") return field.options?.[0]?.value || field.value || "";
  return field.value === undefined ? "" : String(field.value);
}

function defaultWorkflowTemplate(sample) {
  if (sample.type === "molecule") return "molecule-profile";
  if (sample.structure?.focus) return "protein-variant-structure-review";
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
        objective: `${getActiveSample().name}: ${workflowText(template, 1)}`,
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    upsertWorkflowRun(data.run);
    mergeArtifacts(data.run.artifacts || []);
    els.workflowDialog.close();
    switchTab("agent");
    addSystemMessage(localized(
      `已创建“${data.run.title}”计划，等待研究者批准。`,
      `Created “${workflowRunText(data.run, 0)}” for researcher approval.`,
    ));
    renderAll();
  } catch (error) {
    addSystemMessage(localized(`计划创建失败：${error.message}`, `Could not create the plan: ${error.message}`));
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
    await refreshWorkspaceFiles();
    addSystemMessage(
      data.run.status === "completed"
        ? localized(
          `“${data.run.title}”已完成，结果已进入可检查 artifacts。`,
          `“${workflowRunText(data.run, 0)}” completed. Its results are available as inspectable artifacts.`,
        )
        : localized(
          `“${data.run.title}”运行失败：${data.run.error || "未知错误"}`,
          `“${workflowRunText(data.run, 0)}” failed: ${data.run.error || "unknown error"}`,
        ),
    );
  } catch (error) {
    run.status = "pending_approval";
    addSystemMessage(localized(`工作流启动失败：${error.message}`, `Could not start the workflow: ${error.message}`));
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
    addSystemMessage(localized(`已取消“${data.run.title}”。`, `Cancelled “${workflowRunText(data.run, 0)}”.`));
    renderAll();
  } catch (error) {
    addSystemMessage(localized(`取消失败：${error.message}`, `Could not cancel the workflow: ${error.message}`));
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
    addSystemMessage(localized(`本地 Agent 返回错误：${result.error}`, `The local Agent returned an error: ${result.error}`));
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

  addSystemMessage(localized(
    "本地服务不可用，已降级为浏览器内置演示流程。",
    "The local service is unavailable. Using the in-browser demonstration workflow.",
  ));
  const intent = detectIntent(command, sample);
  addToolCall(
    "agent.plan",
    { intent, target: sample.shortName },
    localized(`将自然语言任务路由到 ${intent} 工作流。`, `Routed the natural-language task to the ${intent} workflow.`),
  );
  await runLocalWorkflow(command, sample, intent);
}

async function runLocalWorkflow(command, sample, intent) {
  await pause(180);
  addToolCall(
    sample.type === "protein" ? "structure.parse_fasta" : "chem.parse_smiles",
    { input: sample.sequence || sample.smiles || sample.formula },
    sample.type === "protein"
      ? localized("解析序列并估计二级结构倾向。", "Parsed the sequence and estimated secondary-structure propensity.")
      : localized("解析 SMILES 并识别官能团与环系统。", "Parsed SMILES and identified functional groups and ring systems."),
  );

  await pause(180);
  addToolCall(
    sample.type === "protein" ? "protein.annotate_motifs" : "chem.estimate_properties",
    { properties: sample.properties },
    sample.type === "protein"
      ? localized("标注螺旋、带电残基与潜在界面热点。", "Annotated helices, charged residues, and potential interface hotspots.")
      : localized("估算药物样性质、极性表面积和可优化位点。", "Estimated drug-like properties, polar surface area, and modifiable sites."),
  );

  if (intent === "design" || intent === "risk") {
    await pause(180);
    const generated = sample.type === "protein" ? proteinCandidates(sample, command) : moleculeCandidates(sample, command);
    state.candidates = generated;
    addToolCall(
      sample.type === "protein" ? "design.propose_mutations" : "design.propose_analogs",
      { count: generated.length, constraints: inferConstraints(command) },
      sample.type === "protein"
        ? localized("生成可验证突变组合并标记聚集风险。", "Generated testable mutation sets and flagged aggregation risk.")
        : localized("生成类似物方向并保留核心 scaffold。", "Generated analogue directions while retaining the core scaffold."),
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
      notes: localizedSampleValue(sample, "notes"),
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
      time: new Date().toLocaleTimeString(state.language, { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
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
    time: new Date().toLocaleTimeString(state.language, { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
  });
  renderToolTrace();
  renderMetrics();
}

function addSystemMessage(text) {
  state.chat.push({ role: "system", text });
  renderChat();
}

function addUiMessage(key, values = {}) {
  state.chat.push({ role: "system", i18nKey: key, values });
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
      return localized(
        `${sample.shortName} 的设计重点是保留疏水核心，同时把表面不稳定或易聚集位点换成更温和的带电/极性残基。我建议先做 3 组小批量突变，随后用表达量、SEC、DSF 和目标结合实验验证。`,
        `The design priority for ${sample.shortName} is to preserve the hydrophobic core while replacing unstable or aggregation-prone surface sites with milder charged or polar residues. Start with three small mutation sets, then validate expression, SEC, DSF, and target binding.`,
      );
    }
    if (intent === "risk") {
      return localized(
        "主要风险是局部疏水斑块、过强电荷偏置和螺旋束边缘的构象松动。下一步应把突变方案和实验读数绑定：表达量筛掉不可折叠设计，DSF 看稳定性，BLI/SPR 看结合是否保留。",
        "The main risks are local hydrophobic patches, excessive charge bias, and conformational loosening at helix-bundle edges. Link each mutation set to measurements: expression to reject non-folders, DSF for stability, and BLI/SPR to confirm retained binding.",
      );
    }
    return localized(
      `${sample.shortName} 的序列特征提示其可能以 α 螺旋或紧凑折叠为主。Agent 已标注带电残基、疏水核心和候选界面位置；这些是序列层面的假设，可继续要求“设计突变”“降低聚集”或“生成实验计划”。`,
      `The sequence features of ${sample.shortName} suggest an alpha-helical or compact fold. The Agent marked charged residues, the hydrophobic core, and candidate interface positions. These are sequence-level hypotheses that can be followed by mutation design, aggregation reduction, or an experimental plan.`,
    );
  }

  if (intent === "design") {
    return localized(
      `${sample.shortName} 的 scaffold 可以保留核心识别元素，同时在外围做小步改造。当前候选优先提高可溶性或降低暴露风险，并避免一次引入过多立体和电子变化。`,
      `The ${sample.shortName} scaffold can retain its core recognition elements while making small peripheral changes. The current candidates prioritize solubility or lower exposure risk without introducing too many steric and electronic changes at once.`,
    );
  }
  if (intent === "risk") {
    return localized(
      "当前结构的风险应从酸碱性、极性表面积、潜在代谢软点和选择性开始看。建议先做 ADME 快筛，再用目标活性实验确认改造没有破坏核心作用。",
      "Start the risk review with ionization, polar surface area, potential metabolic soft spots, and selectivity. Run a focused ADME screen, then confirm with a target activity assay that the change did not disrupt the core interaction.",
    );
  }
  return localized(
    `${sample.shortName} 的关键结构已经解析：Agent 识别了核心环系统、供受体模式和可修饰外围位点。你可以继续要求优化水溶性、设计类似物或生成验证计划。`,
    `The key structural features of ${sample.shortName} are parsed. The Agent identified the core ring system, donor-acceptor pattern, and modifiable peripheral sites. Next steps can include solubility optimization, analogue design, or a validation plan.`,
  );
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
        ? localized("在外围引入轻量极性取代，目标是提升溶解度，同时保留核心识别几何。", "Add a light polar substituent at the periphery to improve solubility while preserving core recognition geometry.")
        : localized("用温和电子等排变化保留 scaffold，适合作为第一轮 SAR 对照。", "Use a conservative bioisosteric change that preserves the scaffold as a first-round SAR control."),
      tags: [sample.smiles || sample.formula, solubility ? "TPSA +12" : "core retained", "1-step SAR"],
    },
    {
      name: cns ? "Reduced CNS exposure" : "Metabolic soft-spot shield",
      risk: "medium",
      riskLabel: "Medium",
      score: cns ? 73 : 69,
      summary: cns
        ? localized("提高极性并降低被动扩散倾向，用于减少中枢暴露。", "Increase polarity and reduce passive diffusion to lower CNS exposure.")
        : localized("在疑似代谢软点附近加入小型保护取代，但需要确认活性不受影响。", "Add a small shielding substituent near a suspected metabolic soft spot, then confirm retained activity."),
      tags: [cns ? "logD down" : "microsome follow-up", "ADME screen", "activity check"],
    },
    {
      name: "Exploratory vector scan",
      risk: "high",
      riskLabel: "High",
      score: 52,
      summary: localized("沿可修饰向量扫描更大取代基，信息量高，但合成与选择性风险也更高。", "Scan larger substituents along a modifiable vector. This is informative but carries higher synthesis and selectivity risk."),
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
        ? localized("在螺旋端加入更友好的 cap 残基，降低局部解折叠概率。", "Add a favorable helix-cap residue to reduce local unfolding.")
        : localized("微调界面附近电荷，提升结合方向性并保留整体折叠。", "Tune charge near the interface to improve binding orientation while preserving the fold."),
      tags: [suggestMutation(base, 4, stability ? "S" : "E"), suggestMutation(base, 11, "K"), "DSF + binding"],
    },
    {
      name: aggregation ? "Surface patch cleanup" : "Hydrophobic core packing",
      risk: "medium",
      riskLabel: "Medium",
      score: aggregation ? 81 : 70,
      summary: aggregation
        ? localized("把暴露疏水斑块改成带电或极性残基，优先降低 SEC 聚集峰。", "Replace an exposed hydrophobic patch with charged or polar residues to reduce the SEC aggregation peak.")
        : localized("轻微加强核心 packing，但需要小心避免降低表达量。", "Tighten core packing conservatively while monitoring expression."),
      tags: [suggestMutation(base, 18, aggregation ? "D" : "L"), suggestMutation(base, 27, "A"), "SEC required"],
    },
    {
      name: "Affinity exploratory pair",
      risk: "high",
      riskLabel: "High",
      score: 58,
      summary: localized("成对突变可能提高结合，但有破坏折叠或增加非特异相互作用的风险。", "A mutation pair may improve binding but risks disrupting the fold or increasing nonspecific interactions."),
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
  addToolCall("chem.pipeline_request", { smiles }, localized("请求本地 RDKit 数据管线解析 SMILES。", "Requested SMILES parsing from the local RDKit pipeline."));
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
      localized("RDKit 已返回真实分子 graph、键级、环系统和描述符。", "RDKit returned a molecular graph, bond orders, ring systems, and descriptors."),
    );
    return;
  }

  if (!result.unavailable) {
    addSystemMessage(localized(`SMILES 解析失败：${result.error || "未知错误"}`, `SMILES parsing failed: ${result.error || "unknown error"}`));
    return;
  }

  const custom = buildCustomMolecule(smiles);
  upsertCustomSample(custom);
  selectSample(custom.id);
  addToolCall("chem.import_smiles_fallback", { smiles }, localized("未连接本地管线，已降级为浏览器启发式结构视图。", "The local pipeline is disconnected. Using the browser heuristic structure view."));
  addSystemMessage(localized("本地 RDKit 管线不可用。运行 server.py 后可启用真实 SMILES 解析。", "The local RDKit pipeline is unavailable. Run server.py to enable RDKit SMILES parsing."));
}

async function loadCustomProtein(sequence) {
  addToolCall("protein.pipeline_request", { length: sequence.length }, localized("请求本地序列数据管线解析 FASTA。", "Requested FASTA parsing from the local sequence pipeline."));
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
      localized("序列管线已返回清洗后的 FASTA、组成和蛋白性质统计。", "The sequence pipeline returned cleaned FASTA, composition, and protein property statistics."),
    );
    return;
  }

  if (!result.unavailable) {
    addSystemMessage(localized(`FASTA 解析失败：${result.error || "未知错误"}`, `FASTA parsing failed: ${result.error || "unknown error"}`));
    return;
  }

  const fallbackSequence = cleanProteinInput(sequence);
  if (!fallbackSequence) {
    addSystemMessage(localized("FASTA 解析失败：没有找到有效氨基酸序列。", "FASTA parsing failed: no valid amino-acid sequence was found."));
    return;
  }
  const custom = buildCustomProtein(fallbackSequence);
  upsertCustomSample(custom);
  selectSample(custom.id);
  addToolCall("protein.import_fasta_fallback", { length: fallbackSequence.length }, localized("未连接本地管线，已降级为浏览器序列草图。", "The local pipeline is disconnected. Using the browser sequence sketch."));
  addSystemMessage(localized("本地序列管线不可用。运行 server.py 后可启用真实 FASTA 统计。", "The local sequence pipeline is unavailable. Run server.py to enable FASTA statistics."));
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
  addSystemMessage(localized("请输入四位 PDB ID，或先导入 workspace 后填写 .pdb/.cif/.mmcif 文件名。", "Enter a four-character PDB ID, or import a workspace and enter a .pdb/.cif/.mmcif path."));
}

async function loadAlphaFoldStructure(value) {
  const cleaned = String(value || "").trim().toUpperCase();
  if (!/^[A-Z0-9]{6,10}(?:-\d+)?$/.test(cleaned)) {
    addSystemMessage(localized("请输入 UniProt accession，例如 P04637。", "Enter a UniProt accession, for example P04637."));
    return;
  }
  await executeLocalTool("structure_fetch_alphafold", { accession: cleaned }, { openSample: true });
}

async function executeLocalTool(name, arguments, options = {}) {
  addToolCall(name, arguments, localized("正在执行本地 scientific skill…", "Running the local scientific skill..."));
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
    addSystemMessage(result.summary || localized(`${name} 已完成。`, `${name} completed.`));
    renderAll();
    return result;
  } catch (error) {
    const latest = state.toolCalls[state.toolCalls.length - 1];
    latest.status = "error";
    latest.summary = error.message;
    addSystemMessage(localized(`${name} 失败：${error.message}`, `${name} failed: ${error.message}`));
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
    state.localService = {
      loaded: true,
      connected: true,
      skillCount: health.skills || state.skills.length,
    };
    state.workflowRuns
      .slice(0, 5)
      .reverse()
      .forEach((run) => mergeArtifacts(run.artifacts || []));
    renderLocalStatus();
    renderSkills();
    renderWorkspaceFiles();
    renderWorkflowRuns();
    renderArtifacts();
    renderMetrics();
  } catch (error) {
    state.localService = { loaded: true, connected: false, skillCount: 0 };
    renderLocalStatus();
    renderSkills();
  }
}

async function saveSelectedWorkspaceFiles() {
  const files = Array.from(els.workspaceFiles.files || []);
  if (!files.length) {
    addSystemMessage(localized("请先选择要导入的本地科学文件。", "Choose local scientific files to import first."));
    return;
  }
  let saved = 0;
  for (const file of files) {
    if (file.size > 20 * 1024 * 1024) {
      addSystemMessage(localized(`${file.name} 超过 20 MB workspace 上传限制，未导入。`, `${file.name} exceeds the 20 MB workspace upload limit and was not imported.`));
      continue;
    }
    try {
      const response = await fetch(
        `${pipelineEndpoint("/api/workspace/upload")}?path=${encodeURIComponent(file.name)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/octet-stream" },
          body: await file.arrayBuffer(),
        },
      );
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
      saved += 1;
    } catch (error) {
      addSystemMessage(localized(`${file.name} 导入失败：${error.message}`, `Could not import ${file.name}: ${error.message}`));
    }
  }
  els.workspaceFiles.value = "";
  await refreshWorkspaceFiles();
  if (saved) addSystemMessage(localized(`已将 ${saved} 个文件导入受控 workspace；Agent 现在可以按需读取。`, `Imported ${saved} file(s) into the controlled workspace. The Agent can now read them as needed.`));
}

async function refreshWorkspaceFiles() {
  try {
    const response = await fetch(pipelineEndpoint("/api/workspace"));
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    state.workspaceFiles = data.files || [];
    renderWorkspaceFiles();
  } catch (error) {
    addSystemMessage(localized(`无法刷新 workspace：${error.message}`, `Could not refresh the workspace: ${error.message}`));
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
    notesEn: "This quick structure sketch comes from the browser fallback. Start the local server.py to use RDKit parsing instead.",
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
    promptsEn: [
      "Explain this molecule's key functional groups",
      "Improve its aqueous solubility and explain the risks",
      "Generate three directions for the next design round",
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
    notesEn: "This sequence sketch comes from the browser fallback. Start the local server.py to use the FASTA statistics pipeline instead.",
    selection: "Custom protein · imported workspace",
    confidence: "browser fallback",
    properties: estimateProteinProperties(sequence),
    prompts: [
      "找出这个蛋白的稳定性热点",
      "建议 3 个突变并说明实验验证",
      "降低聚集风险并保留功能界面",
    ],
    promptsEn: [
      "Find stability hotspots in this protein",
      "Suggest three mutations and their experimental validation",
      "Reduce aggregation risk while retaining the functional interface",
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
  if (state.isAnimating && !state.pointer.down && !isPaeMode()) {
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

  if (isPaeMode(sample)) {
    drawPaeMatrix(sample, width, height);
    return;
  }
  drawGridOverlay(width, height);
  if (sample.structure?.atoms?.length) drawProteinStructure(sample, width, height);
  else if (sample.type === "protein") drawProtein(sample, width, height);
  else drawMolecule(sample, width, height);
}

function drawPaeMatrix(sample, width, height) {
  const pae = sample.structure?.pae;
  if (!pae?.matrix?.length) return;
  const plot = paePlotGeometry(width, height);
  const image = cachedPaeCanvas(sample);
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(image, plot.x, plot.y, plot.size, plot.size);
  ctx.strokeStyle = "#888178";
  ctx.lineWidth = 1;
  ctx.strokeRect(plot.x + 0.5, plot.y + 0.5, plot.size - 1, plot.size - 1);

  const middleResidue = Math.ceil(Number(pae.residue_count) / 2);
  const middle = plot.x + plot.size / 2;
  ctx.fillStyle = "#625d56";
  ctx.font = "11px ui-sans-serif, system-ui";
  ctx.textAlign = "left";
  ctx.fillText("Scored residue ↓", plot.x, Math.max(13, plot.y - 10));
  ctx.fillText("1", plot.x, plot.y + plot.size + 17);
  ctx.textAlign = "center";
  ctx.fillText(String(middleResidue), middle, plot.y + plot.size + 17);
  ctx.fillText("Aligned residue →", middle, plot.y + plot.size + 35);
  ctx.textAlign = "right";
  ctx.fillText(String(pae.residue_count), plot.x + plot.size, plot.y + plot.size + 17);

  drawPaeColorScale(plot, Number(pae.max_error));
  if (state.paeHover) {
    const cell = plot.size / Number(pae.matrix_size);
    ctx.strokeStyle = "#20201e";
    ctx.lineWidth = Math.max(1, Math.min(3, cell));
    ctx.strokeRect(
      plot.x + state.paeHover.column * cell,
      plot.y + state.paeHover.row * cell,
      Math.max(1, cell),
      Math.max(1, cell),
    );
  }
  ctx.restore();
}

function paePlotGeometry(width, height) {
  const compact = width < 520 || height < 390;
  const margins = compact
    ? { top: 32, right: 18, bottom: 52, left: 18 }
    : { top: 42, right: 110, bottom: 54, left: 44 };
  const size = Math.max(96, Math.min(width - margins.left - margins.right, height - margins.top - margins.bottom));
  const x = margins.left + Math.max(0, (width - margins.left - margins.right - size) / 2);
  const y = margins.top + Math.max(0, (height - margins.top - margins.bottom - size) / 2);
  return { x, y, size, compact, width, height };
}

function cachedPaeCanvas(sample) {
  if (paeCanvasCache.has(sample)) return paeCanvasCache.get(sample);
  const pae = sample.structure.pae;
  const matrix = pae.matrix;
  const size = matrix.length;
  const offscreen = document.createElement("canvas");
  offscreen.width = size;
  offscreen.height = size;
  const offscreenContext = offscreen.getContext("2d");
  const pixels = offscreenContext.createImageData(size, size);
  const maximum = Math.max(1, Number(pae.max_error));
  for (let row = 0; row < size; row += 1) {
    for (let column = 0; column < size; column += 1) {
      const color = paeRgb(Number(matrix[row][column]), maximum);
      const index = (row * size + column) * 4;
      pixels.data[index] = color[0];
      pixels.data[index + 1] = color[1];
      pixels.data[index + 2] = color[2];
      pixels.data[index + 3] = 255;
    }
  }
  offscreenContext.putImageData(pixels, 0, 0);
  paeCanvasCache.set(sample, offscreen);
  return offscreen;
}

function paeRgb(value, maximum) {
  const t = clamp(Number(value) / Math.max(1, maximum), 0, 1);
  const low = [10, 91, 76];
  const high = [241, 246, 218];
  return low.map((channel, index) => Math.round(channel + (high[index] - channel) * t));
}

function drawPaeColorScale(plot, maximum) {
  const width = plot.compact ? Math.min(116, plot.size * 0.42) : 82;
  const height = 8;
  const x = plot.compact ? plot.x + plot.size - width : plot.x + plot.size + 20;
  const y = plot.compact ? Math.max(16, plot.y - 19) : plot.y + 4;
  for (let index = 0; index < width; index += 1) {
    const color = paeRgb(index, Math.max(1, width - 1));
    ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
    ctx.fillRect(x + index, y, 1, height);
  }
  ctx.strokeStyle = "#9b958b";
  ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, width - 1, height - 1);
  ctx.fillStyle = "#625d56";
  ctx.font = "10px ui-sans-serif, system-ui";
  ctx.textAlign = "left";
  ctx.fillText("0 Å", x, y + 20);
  ctx.textAlign = "right";
  ctx.fillText(`${maximum.toFixed(2)} Å`, x + width, y + 20);
}

function updatePaeHover(event) {
  const sample = getActiveSample();
  const pae = sample.structure?.pae;
  if (!pae?.matrix?.length) return;
  const rect = canvas.getBoundingClientRect();
  const plot = paePlotGeometry(canvas.clientWidth, canvas.clientHeight);
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  if (x < plot.x || x >= plot.x + plot.size || y < plot.y || y >= plot.y + plot.size) {
    if (state.paeHover) {
      state.paeHover = null;
      renderHeader();
    }
    return;
  }
  const size = Number(pae.matrix_size);
  const column = clamp(Math.floor(((x - plot.x) / plot.size) * size), 0, size - 1);
  const row = clamp(Math.floor(((y - plot.y) / plot.size) * size), 0, size - 1);
  const binSize = Number(pae.bin_size || 1);
  state.paeHover = {
    row,
    column,
    rowStart: row * binSize + 1,
    rowEnd: Math.min(Number(pae.residue_count), (row + 1) * binSize),
    columnStart: column * binSize + 1,
    columnEnd: Math.min(Number(pae.residue_count), (column + 1) * binSize),
    value: Number(pae.matrix[row][column]),
  };
  renderHeader();
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
  const predicted = sample.metadata?.coordinateType === "predicted";

  ctx.save();
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  geometry.contacts.forEach((contact) => {
    const start = project(contact.focus.x, contact.focus.y, contact.focus.z, width, height, scale);
    const end = project(contact.other.x, contact.other.y, contact.other.z, width, height, scale);
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = contact.kind === "hetero" ? "rgba(178, 69, 92, 0.78)" : "rgba(20, 125, 114, 0.58)";
    ctx.lineWidth = contact.kind === "hetero" ? 1.8 : 1.2;
    ctx.stroke();
    ctx.restore();
  });
  geometry.backbone.forEach((chain, chainIndex) => {
    const points = chain.points.map((point) => ({
      ...project(point.x, point.y, point.z, width, height, scale),
      point,
    }));
    if (points.length < 2) return;
    ctx.globalAlpha = state.viewerStyle === "spacefill" ? 0.35 : 0.82;
    ctx.lineWidth = state.viewerStyle === "wire" ? 2.2 : 5.5;
    if (predicted) {
      for (let index = 1; index < points.length; index += 1) {
        if (points[index].point.sourceIndex - points[index - 1].point.sourceIndex > 1) continue;
        ctx.beginPath();
        ctx.moveTo(points[index - 1].x, points[index - 1].y);
        ctx.lineTo(points[index].x, points[index].y);
        ctx.strokeStyle = plddtColor(points[index].point.bfactor);
        ctx.stroke();
      }
    } else {
      for (let index = 1; index < points.length; index += 1) {
        if (points[index].point.sourceIndex - points[index - 1].point.sourceIndex > 1) continue;
        ctx.beginPath();
        ctx.moveTo(points[index - 1].x, points[index - 1].y);
        ctx.lineTo(points[index].x, points[index].y);
        ctx.strokeStyle = chainColors[chainIndex % chainColors.length];
        ctx.stroke();
      }
    }
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
      const radius = point.atom.isFocus
        ? 6.8
        : hetero && point.atom.isContact
          ? 5.4
          : hetero
            ? 4.8
            : point.atom.isContact
              ? 3.4
              : state.viewerStyle === "spacefill"
                ? 3.8
                : state.viewerStyle === "wire"
                  ? 1.25
                  : 2.25;
      ctx.beginPath();
      ctx.fillStyle = point.atom.isFocus
        ? "#b2455c"
        : point.atom.isContact && !hetero
          ? "#147d72"
          : predicted && !hetero
            ? plddtColor(point.atom.bfactor)
            : ELEMENT_COLORS[point.atom.e] || ELEMENT_COLORS.X;
      ctx.globalAlpha = point.atom.isFocus || point.atom.isContact || hetero ? 0.98 : state.viewerStyle === "wire" ? 0.5 : 0.72;
      ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
      ctx.fill();
      if (hetero || point.atom.isFocus || point.atom.isContact) {
        ctx.strokeStyle = point.atom.isFocus ? "#672a3a" : "rgba(255,255,255,0.86)";
        ctx.lineWidth = point.atom.isFocus ? 1.8 : 1;
        ctx.stroke();
      }
    });
  ctx.globalAlpha = 1;
  if (state.showLabels && sample.structure?.focus) {
    drawVariantStructureLabels(projectedAtoms, sample.structure.focus);
  }
  ctx.restore();
  drawLegend(predicted ? "plddt" : "molecule");
}

function plddtColor(value) {
  const score = Number(value);
  if (score >= 90) return "#0053d6";
  if (score >= 70) return "#65cbf3";
  if (score >= 50) return "#ffdb13";
  return "#ff7d45";
}

function normalizedStructureGeometry(sample) {
  const cache = structureGeometryCache.get(sample) || {};
  const scope = sample.structure?.focus ? state.structureScope : "global";
  if (cache[scope]) return cache[scope];
  const allAtoms = sample.structure?.atoms || [];
  const focus = sample.structure?.focus || null;
  const focusKey = focus
    ? structureResidueKey({ chain: focus.chain, resSeq: focus.author_residue_number, residue: focus.observed_residue, hetero: false })
    : "";
  const contactKinds = new Map(
    (focus?.contacts || []).map((contact) => [structureResidueKey({ ...contact, hetero: contact.kind === "hetero" }), contact.kind]),
  );
  const permittedKeys = new Set([focusKey, ...contactKinds.keys()].filter(Boolean));
  const scopedAtoms = scope === "site"
    ? allAtoms.filter((atom) => permittedKeys.has(structureResidueKey(atom)))
    : allAtoms;
  const atoms = scopedAtoms.length ? scopedAtoms : allAtoms;
  const xs = atoms.map((atom) => Number(atom.x));
  const ys = atoms.map((atom) => Number(atom.y));
  const zs = atoms.map((atom) => Number(atom.z));
  const focusAtoms = focusKey ? allAtoms.filter((atom) => structureResidueKey(atom) === focusKey) : [];
  const centerAtoms = scope === "site" && focusAtoms.length ? focusAtoms : atoms;
  const center = {
    x: scope === "site"
      ? centerAtoms.reduce((sum, atom) => sum + Number(atom.x), 0) / Math.max(1, centerAtoms.length)
      : (Math.min(...xs) + Math.max(...xs)) / 2,
    y: scope === "site"
      ? centerAtoms.reduce((sum, atom) => sum + Number(atom.y), 0) / Math.max(1, centerAtoms.length)
      : (Math.min(...ys) + Math.max(...ys)) / 2,
    z: scope === "site"
      ? centerAtoms.reduce((sum, atom) => sum + Number(atom.z), 0) / Math.max(1, centerAtoms.length)
      : (Math.min(...zs) + Math.max(...zs)) / 2,
  };
  const span = Math.max(
    Math.max(...xs) - Math.min(...xs),
    Math.max(...ys) - Math.min(...ys),
    Math.max(...zs) - Math.min(...zs),
    scope === "site" ? 8 : 1,
  );
  const normalizePoint = (point) => ({
    ...point,
    x: ((Number(point.x) - center.x) * 2) / span,
    y: ((Number(point.y) - center.y) * 2) / span,
    z: ((Number(point.z) - center.z) * 2) / span,
  });
  const geometry = {
    atoms: atoms.map((atom) => {
      const key = structureResidueKey(atom);
      return {
        ...normalizePoint(atom),
        isFocus: key === focusKey,
        isContact: contactKinds.has(key),
        contactKind: contactKinds.get(key) || "",
      };
    }),
    backbone: (sample.structure?.backbone || []).map((chain) => ({
      chain: chain.chain,
      points: (chain.points || [])
        .map((point, sourceIndex) => ({ ...point, sourceIndex }))
        .filter((point) => scope !== "site" || permittedKeys.has(structureResidueKey({ ...point, chain: chain.chain, hetero: false })))
        .map(normalizePoint),
    })).filter((chain) => chain.points.length),
    contacts: (focus?.contacts || []).map((contact) => ({
      kind: contact.kind,
      distance: contact.min_distance_angstrom,
      focus: normalizePoint({ x: contact.focus_xyz?.[0], y: contact.focus_xyz?.[1], z: contact.focus_xyz?.[2] }),
      other: normalizePoint({ x: contact.contact_xyz?.[0], y: contact.contact_xyz?.[1], z: contact.contact_xyz?.[2] }),
    })),
  };
  cache[scope] = geometry;
  structureGeometryCache.set(sample, cache);
  return geometry;
}

function structureResidueKey(atom) {
  return `${atom.hetero ? "H" : "P"}|${atom.chain || "_"}|${atom.resSeq || ""}|${atom.residue || ""}`;
}

function drawVariantStructureLabels(projectedAtoms, focus) {
  const focusAtoms = projectedAtoms.filter((point) => point.atom.isFocus);
  const focusPoint = focusAtoms.find((point) => String(point.atom.name).toUpperCase() === "CA") || focusAtoms[0];
  if (focusPoint) drawLabel(`${focus.variant} · ${focus.chain}:${focus.author_residue_number}`, focusPoint.x, focusPoint.y, 7);
  const groups = new Map();
  projectedAtoms.filter((point) => point.atom.hetero && point.atom.isContact).forEach((point) => {
    const key = structureResidueKey(point.atom);
    const group = groups.get(key) || { points: [], label: `${point.atom.residue}:${point.atom.chain}:${point.atom.resSeq}` };
    group.points.push(point);
    groups.set(key, group);
  });
  Array.from(groups.values()).slice(0, 6).forEach((group) => {
    const x = group.points.reduce((sum, point) => sum + point.x, 0) / group.points.length;
    const y = group.points.reduce((sum, point) => sum + point.y, 0) / group.points.length;
    drawLabel(group.label, x, y, 5);
  });
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
      : type === "plddt"
        ? [
            ["pLDDT > 90", "#0053d6"],
            ["70–90", "#65cbf3"],
            ["50–70", "#ffdb13"],
            ["< 50", "#ff7d45"],
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
    return url.protocol === "https:" && [
      "pubchem.ncbi.nlm.nih.gov",
      "www.uniprot.org",
      "www.rcsb.org",
      "platform.opentargets.org",
      "pubmed.ncbi.nlm.nih.gov",
      "europepmc.org",
      "doi.org",
      "www.ncbi.nlm.nih.gov",
      "ftp.ncbi.nlm.nih.gov",
      "rest.ensembl.org",
      "gnomad.broadinstitute.org",
      "clinicaltrials.gov",
      "cdn.clinicaltrials.gov",
    ].includes(url.hostname);
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

function formatScientific(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "n/a";
  if (number === 0) return "0";
  return number.toExponential(2).replace("e+", "e");
}

function formatPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "n/a";
  return `${(numeric * 100).toFixed(numeric === 0 || numeric === 1 ? 0 : 1)}%`;
}

function formatDecimal(value, digits = 2) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : "n/a";
}

function normalizePlot(value, min, max) {
  const range = Math.max(Number(max) - Number(min), 1e-9);
  return clamp(((Number(value) - Number(min)) / range) * 84 + 8, 8, 92);
}

function percentile(values, proportion) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return 0;
  return sorted[Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * proportion))];
}

function heatmapColor(value) {
  const bounded = clamp(Number(value) || 0, -3, 3) / 3;
  const base = bounded >= 0 ? [184, 74, 74] : [54, 120, 154];
  const intensity = Math.abs(bounded);
  const mixed = base.map((channel) => Math.round(250 + (channel - 250) * intensity));
  return `rgb(${mixed.join(",")})`;
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
