# Molemo WorkBench

Molemo WorkBench 把生命科学问题连接到可检查的本地证据。用户可以接入自己的 OpenAI-compatible 模型；模型负责理解问题和选择工具，分子解析、蛋白序列计算、文件读取、管线执行与可视化则在本机通过注册 skills 完成。每次运行保留工具参数、状态、摘要和 artifact，使结论能够被回看、导出和评测。

当前仓库是这一主线的可运行参考实现，也是 `Molemo_Bench v0.20`。它借鉴了 Rosalind Workbench 将问题、计划、工具、viewer 和证据放在同一工作区的产品范式，但不依赖 GPT-Rosalind，也不与 OpenAI Rosalind 项目关联。前端采用克制的研究会话与证据双栏；进入运行、结果或工具页后，右侧切换为整高文档视图，不把科学工作流做成展示型仪表盘。

## 运行

推荐使用带 RDKit 的 conda 环境：

```bash
/opt/miniconda3/bin/python server.py
```

然后打开 [http://127.0.0.1:8765](http://127.0.0.1:8765)。也可以创建独立环境：

```bash
conda env create -f environment.yml
conda activate molemo-bench
python server.py
```

环境中的 `blast`、`hmmer` 与 `mafft` 来自 Bioconda；本地搜索与比对分别遵循 [NCBI BLAST+ manual](https://www.ncbi.nlm.nih.gov/books/NBK279691/)、[HMMER User's Guide](https://eddylab.org/software/hmmer/CURRENT/Userguide.pdf) 与 [MAFFT official documentation](https://mafft.cbrc.jp/alignment/software/)。Bulk RNA-seq 差异表达使用 [PyDESeq2](https://pydeseq2.readthedocs.io/en/stable/)；单细胞探索分析遵循 [Scanpy preprocessing and clustering](https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering.html) 主流程，可按审批运行 [Scanpy Scrublet](https://scanpy.readthedocs.io/en/stable/api/generated/scanpy.pp.scrublet.html)。靶点-配体活性证据来自 [ChEMBL Data Web Services](https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services)；人类基因集分析使用 [Reactome Analysis Service](https://reactome.org/dev/analysis/) 与 [STRING API v12](https://string-db.org/help/api/)；文献元数据与摘要来自 [Europe PMC REST API](https://europepmc.org/RestfulWebService)；临床试验登记信息来自 [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-about-studies/learn-about-api)；变异证据来自 [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/docs/access/)、[Ensembl VEP](https://rest.ensembl.org/documentation/info/vep_hgvs_get) 与 [gnomAD](https://gnomad.broadinstitute.org/)。仓库会优先发现项目级 `.molemo-tools` 运行时，因此不要求修改 conda `base`。

页面默认使用本地 skill runtime。要使用第三方模型，在右上角 API 设置中填写完整的 Chat Completions endpoint、模型名和 API key：

- `Native tool calling`：模型通过 OpenAI-compatible tools 自主选择本地 skills。
- `Grounded chat`：本地先计算当前分子或蛋白上下文，再发送给不支持 tools 的兼容模型。

API key 只在当前页面内存与单次本地请求中使用，不保存到文件，也不会进入导出的运行记录。

## 已实现的闭环

1. 从自然语言研究问题进入本地 Agent。
2. 单步任务可直接调用结构化科学工具；多步任务先生成具体计划。
3. 研究者在“运行”页检查输入、工具和步骤，明确批准后才开始执行。
4. RDKit、ChEMBL、NCBI BLAST+、HMMER、MAFFT、PyDESeq2、Scanpy/Leiden、Reactome、STRING、VCF 4.x 解析、序列算法、Europe PMC、ClinVar、Ensembl、gnomAD、其他公共数据库或受控 workspace 按计划生成来源明确的结果。
5. 前端把结果呈现为蛋白家族多序列比对与参考位点保守性文档、实验蛋白变体位点与局部接触文档、ChEMBL 靶点-配体活性文档、人类基因集通路/网络、文献 evidence map、临床试验版图或单项 posted-results 文档、多样本 VCF 变异景观与轨迹、HMMER domain architecture、单细胞 UMAP/QC/marker 文档、靶点证据矩阵、变异证据文档、分子结构、RCSB 实验结构、可切换 pLDDT 三维模型与 PAE 矩阵的 AlphaFold 预测结构、序列、BLAST 命中与比对、FASTQ QC、PCA、volcano、heatmap 或性质图 artifact。
6. 工具 trace、计划状态、结论、候选设计和 artifact 可导出为 JSON。
7. `Molemo_Bench v0.20` 对工具正确性、审批边界、trace 完整性和 artifact 生成进行回归评测。

当前包含 23 个 skills、44 个工具和二十类 guided workflow。新增的主线是：从蛋白 FASTA 出发，以一个精确参考序列和位点运行 MAFFT 多序列比对，在同一工作区审阅全长保守性、局部 alignment、逐序列位点观察，再与实验结构位点文档并列检查。

人类基因集功能分析接受 2–50 个唯一基因或蛋白标识符。创建计划时先固定物种为 Homo sapiens（NCBI taxon 9606），展示 STRING 映射、未映射项、功能网络置信阈值、FDR 和 Reactome 疾病通路设置；研究者批准后，才执行 Reactome overrepresentation、STRING enrichment、functional association network 与 PPI enrichment，并保存四张 TSV、JSON、manifest、artifact index 和摘要。Reactome 与 STRING 的统计保持分离，不合成为自定义分数；FDR 不是通路为真的概率，STRING 边也不必然代表直接物理互作。

文献工作流保留批准后的精确 Europe PMC 检索式、年份窗口、摘要与预印本过滤、来源相关性顺序、PMID/PMCID/DOI、文献类型和有界摘要。即时 preview 最多向 Agent 提供十篇可引用记录；完整 evidence map 最多收集二十五篇，并保存论文表、JSON 报告、manifest 和摘要。相关性排序与引用次数都不被当作质量分数，当前也不声称完成全文风险偏倚评价、系统综述筛选或 meta-analysis。

靶点证据工作流接受一个疾病和最多八个候选靶点。创建计划时先把疾病解析为 EFO/MONDO 记录、把靶点解析为 Ensembl Gene ID；研究者批准后，才查询并保存 Open Targets 原始 association score、分证据类型得分、tractability、pathway、safety liability、临床药物和文献来源。结果使用原始 association score 排序，不另造综合分，并明确提示该分数不是概率、置信度或因果结论。

靶点-配体活性工作流接受一个精确 UniProt accession，并在审批前解析到唯一的 ChEMBL `SINGLE PROTEIN` 靶点。批准后收集有界的 binding/functional 标准活性，保留 pChEMBL、IC50/Ki/Kd/EC50 等端点、关系、值、单位、BAO 格式、测定说明、文献和 canonical SMILES；用户可将候选结构直接交给本地 RDKit viewer。只保留 ChEMBL 靶点置信分 9 和 direct 关系，但这不证明直接物理结合或实验质量；混合端点不能直接互换，排序也不证明选择性、机制、ADME、安全性或疗效。

蛋白变体结构工作流接受一个实验 PDB 条目、精确 author chain 和 `G12C` 形式的蛋白替换。审批前确认该 author residue 是参考或替代氨基酸；批准后保存位点附近蛋白残基与坐标异原子组的最短重原子距离、原子对、结构元数据和来源。viewer 可在局部位点与全局结构间切换。距离只表示首个沉积模型中的几何邻近；HETATM 不自动等同于抑制剂，短接触也不单独证明共价、亲和力、机制、功能影响或致病性。

蛋白家族保守性工作流接受 workspace 内 3–100 条蛋白序列、一个精确 FASTA reference ID，以及参考位置或 `G12C` 形式的替换。审批前确认输入规模、参考残基与 MAFFT 版本；批准后以单线程 `--auto --amino` 运行并保存 alignment、逐列统计、位点观察、JSON、manifest 和摘要。界面只突出参考位点、全长保守性与局部 alignment，不把结果包装成综合分。序列等权统计不包含系统发育校正，也不证明功能重要性、结构等价、致病性或突变效应。

变异证据工作流接受一个版本化 RefSeq HGVS、rsID、ClinVar Variation ID 或 VCV accession。审批前解析到单个 ClinVar 简单等位基因；多等位 rsID、haplotype 和复杂记录会停止并要求精确 HGVS。批准后分别保留 ClinVar aggregate assertion、review status 与疾病范围，Ensembl VEP 的 MANE/canonical 转录本后果和计算预测，以及 gnomAD v4 的 AC、AN、homozygote count、filters 与人群频率。三条证据通道不合成为自定义致病性或 ACMG/AMP 分数，结果也不作为诊断或治疗建议。

临床试验版图接受一个疾病、可选干预、状态范围和研究类型。即时 preview 最多返回十条 ClinicalTrials.gov 记录；研究者批准后最多收集三十条，并保存 NCT ID、状态、phase、sponsor、设计、登记终点、结果可用性、关联 PMID、国家、日期、TSV、JSON 报告、manifest 和摘要。给定一个精确 NCT ID 时，独立的结果审阅工作流先验证 posted tabular results，批准后再按来源顺序保存 participant flow、baseline、outcome values、submitted statistical analyses、adverse events、protocol/SAP 和关联论文。它不重算个体数据，也不生成自定义疗效、安全性、确定性或研究质量分数。

多样本 VCF 工作流接受 workspace 内的文本 VCF 4.x 和可选样本信息表。审批前验证样本、记录、ALT、`CSQ/ANN`、深度、VAF 与 FILTER 规则；批准后保存 variant、sample-call、sample-QC、trajectory 表、JSON、manifest 和摘要，并生成可检查的变异矩阵、低频调用和受试者纵向轨迹。示例 `examples/ctdna_variants.vcf` 与 `examples/ctdna_metadata.csv` 是完全合成数据。该流程不把 VAF 当肿瘤比例，不判定 somatic/germline、driver、耐药、治疗推荐或临床可行动性。

HMMER 工作流接受 workspace 内的 HMMER3 amino-acid profile 和蛋白 FASTA。审批前验证 profile 名称、长度、模型数、数据库序列与总残基、HMMER 版本、序列 E-value 与 domain conditional E-value 阈值；批准后用固定的 `hmmsearch` 参数保存 profile-target hit、domain 坐标、conditional/independent E-value、`domtblout`、JSON、manifest、输入哈希和摘要，并生成线性 domain architecture。示例 profile 与目标序列完全合成。E-value 依赖搜索空间和 profile；命中不单独证明功能、机制、活性、定位或表型，当前也不下载或版本化 Pfam 等外部 profile 库。

单细胞工作流接受 workspace 内的 cell-by-gene CSV/TSV、AnnData `.h5ad`、10x H5 或标准压缩/未压缩 MTX；AnnData 可明确选择保存 raw counts 的 layer，外部 cell metadata 仍要求 ID 精确匹配。审批前用与执行相同的加载器检查原始非负整数计数、维度、稀疏度、MT- 基因、过滤后规模、metadata levels 和本地版本。批准后以固定随机种子执行 QC、可选的整体或分批 Scrublet、CP10k、log1p、HVG、PCA、neighbors、UMAP、Leiden 和 cluster-vs-rest Wilcoxon marker 排名。Scrublet 默认关闭；开启后默认只保存 score、prediction 与自动阈值，只有计划中单独批准才排除预测细胞。结果保留输入格式、count layer、全部 10x 组件哈希、doublet 决定、cell/gene QC、embedding、marker、cluster summary、`.h5ad`、manifest 和摘要。合成示例包含 90 个细胞和三个已知群，只用于回归验证；Scrublet prediction、cluster、UMAP 和按细胞计算的 marker p-value 都不等同于细胞身份或样本级推断。

Agent 可以调用有界的蛋白多序列比对、实验变体结构、ChEMBL、文献和临床试验 preview，以及其他已注册预检、列出和创建计划；MAFFT 完整执行和其他批准后执行工具都不暴露给第三方模型。公共数据库访问固定官方域名，不需要用户 API key；页面中的第三方 LLM key 仍由用户自己提供。

## 评测与测试

```bash
python bench.py
python -m unittest discover -s tests -v
```

基准任务位于 `benchmarks/tasks.jsonl`。它是对 Molemo 工具链的过程评测，不代表模型在完整生命科学研究中的总体能力。

## 能力边界

AlphaFold 结构可在同一 viewer 内切换 pLDDT 三维模型与方向化 PAE 矩阵；矩阵按连续残基区间有界降采样，悬停或触摸返回 scored/aligned 残基范围和 Å 误差。该视图帮助检查相对位置置信度，不自动划分结构域或推断相互作用。

当前版本已覆盖中心化 Chat、第三方模型接入、研究者审批、本地科学工具、蛋白家族 MAFFT 比对与参考位点保守性、实验蛋白变体位点与局部接触审阅、ChEMBL 靶点-配体活性证据、人类基因集 Reactome/STRING 功能分析、可引用文献 evidence map、ClinicalTrials.gov 临床试验版图与单项 posted-results 审阅、processed 多样本 VCF 技术审阅、HMMER profile-to-sequence domain 搜索、CSV/AnnData/10x single-cell raw counts 的 QC、可选 Scrublet、UMAP、Leiden 与 marker 探索、候选靶点证据比较、单个简单人类变异的多源证据审阅、分子 viewer、RCSB 实验坐标、AlphaFold DB 预测坐标与 pLDDT、公共数据库检索、本地 FASTA 数据库上的 BLASTP/BLASTN、FASTQ QC、raw-count bulk RNA-seq 差异表达、受控文件工作区和可审计运行记录。guided workflow 当前同步执行二十类固定模板，不是任意 shell 管线。多序列保守性只处理有界蛋白 FASTA、一个精确参考 ID 与位点，不做系统发育推断或变异效应预测；实验变体结构能力只处理一个 PDB 首模型、一个 author chain 和无插入码的单氨基酸替换，不做结构叠合、能量计算或共价连接判定。其余边界包括：ChEMBL 不执行跨端点 SAR 建模；单细胞不覆盖自动 cell typing 或 donor-aware pseudobulk；HMMER 不覆盖 `hmmscan`、profile 构建或远程大库；VCF 不覆盖 raw-read calling、CNV/SV 或临床解释；临床试验不执行个体数据重分析、跨试验比较或 meta-analysis；仍未实现病理切片和实验采购。

详细范围见 [能力矩阵](docs/CAPABILITY_MATRIX.md) 和 [架构说明](docs/ARCHITECTURE.md)。公开参照为 [OpenAI Rosalind](https://openai.com/rosalind/) 与 [OpenAI Life Science Research plugin](https://github.com/openai/plugins/tree/main/plugins/life-science-research)。

## License

MIT
