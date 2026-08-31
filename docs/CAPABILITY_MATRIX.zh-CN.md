# 能力矩阵

[English](CAPABILITY_MATRIX.md) | 简体中文

Molemo WorkBench 的目标不是复制某个专用模型，而是实现同一类可审计研究闭环：从问题出发，连接本地数据与科学工具，在同一工作区检查结果，并保留下一步决策需要的上下文。

| 研究能力 | Molemo WorkBench v0.22 | 当前边界 |
| --- | --- | --- |
| Chat 研究工作区 | 已实现 | 中英文对话、本地 trace 与当前证据上下文 |
| 用户自带模型 API | 已实现 | OpenAI-compatible Chat Completions；native tools 或 grounded mode；key 不落盘 |
| 本地 skill 编排 | 已实现 | `molemo/` 包、自动发现、schema 约束的 Python handlers |
| Guided plan 与研究者审批 | 已实现 | 二十三类固定模板；Agent 可提出和检查，只有本地 UI 可以批准执行 |
| 小分子结构 | 已实现 | RDKit SMILES graph、环、键级与核心 descriptors |
| 蛋白序列分析 | 已实现 | FASTA 清理、序列性质、疏水性与 pairwise alignment |
| 多序列比对 | 已实现 | 有界 MAFFT 蛋白 MSA、保守性轨道与精确参考位点窗口；不做系统发育校正 |
| 科学 artifacts | 已实现 | GEO 版图/Matrix QC、DNA 比对/coverage/候选 VCF、结构、序列、BLAST、HMMER、MAFFT、通路/网络、文献、临床试验、VCF、单细胞、PCA、volcano、heatmap 等 typed artifacts |
| 本地文件工作区 | 已实现 | 显式上传、Agent 只读、路径限制；批准后的 pipeline 可以写入有界输出 |
| 可审计运行记录 | 已实现 | 计划输入、逐步状态、工具参数、时间、摘要、对话与 artifacts |
| 过程评测 | 已实现 | v0.22 确定性测试覆盖真实 BWA/samtools/bcftools、BLAST+、HMMER、MAFFT、PyDESeq2、Scanpy、路由、审批、provenance 与 artifacts |
| 原子级蛋白结构 | 已实现 | RCSB 实验结构、AlphaFold pLDDT/PAE、local PDB/mmCIF 首模型；不自动推断结构域 |
| 公共生物数据库 | 已实现 | 固定官方域名的 GEO、ChEMBL、Europe PMC、ClinicalTrials.gov、ClinVar、VEP、gnomAD、PubChem、UniProt、RCSB、AlphaFold、Open Targets、Reactome 与 STRING |
| 公共组学数据集发现 | 已实现 | 按主题、物种、assay 与样本量检索 GEO Series，保留精确 query、来源排序与 provenance；发现阶段不下载矩阵或评分数据集 |
| GEO Series Matrix 导入 | 已实现 | 精确 GSE 与官方文件；审批后的有界 gzip 下载、数值/维度验证、联系信息省略、矩阵/QC/provenance；不当作 raw counts |
| 人类基因集功能分析 | 已实现 | 2–50 个标识符；STRING mapping、Reactome overrepresentation、STRING enrichment 与网络；不推断因果或直接物理互作 |
| 靶点证据比较 | 已实现 | 疾病与最多八个靶点；Open Targets association、tractability、pathway、safety、临床药物和文献；不自造置信分 |
| 靶点-配体活性 | 已实现 | 精确 UniProt 到 ChEMBL single-protein target，保留 pChEMBL、endpoint、assay 与来源；不跨 endpoint 合成 potency 或推断疗效 |
| 蛋白变体结构上下文 | 已实现 | 精确 PDB author chain/residue 与单氨基酸替换；首模型重原子邻近；不判定共价、能量、功能或致病性 |
| 文献证据审阅 | 已实现 | Europe PMC preview 与批准后的 evidence map；保留 query、过滤、标识符与有界摘要；不做全文系统综述或 meta-analysis |
| 人类变异证据 | 已实现 | 单个简单等位基因的 ClinVar、VEP 与 gnomAD 通道；不支持 haplotype/SV、诊断或 de novo ACMG/AMP 分类 |
| 多样本 VCF 审阅 | 已实现 | 有界 VCF 4.x 与可选纵向 metadata；ALT-aware AD/AF、QC、矩阵与轨迹；不做 raw calling、somatic/germline 或临床解释 |
| 临床试验版图 | 已实现 | ClinicalTrials.gov 登记 metadata、NCT、endpoint、results availability 与文献；不从登记信息推断疗效或安全性 |
| 单项临床试验结果 | 已实现 | 精确 NCT 的 participant flow、baseline、outcomes、submitted statistics、AE 与文件；不重分析 IPD 或跨试验合成 |
| BLAST/HMMER | 已实现 | 本地 bounded BLASTP/BLASTN 与 HMMER3 `hmmsearch`，保存 alignment/domain/provenance；不自动下载大型 profile 或远程数据库 |
| 单细胞 RNA-seq 探索 | 已实现 | raw-count CSV/TSV、AnnData layer、10x H5/MTX，QC、可选 Scrublet、UMAP、Leiden、marker 与 `.h5ad`；不自动命名细胞或做 donor-aware pseudobulk |
| 有界 DNA reads 到变异 | 已实现 | paired FASTQ 与小型 FASTA 参考；审批后运行 BWA-MEM、排序/索引 BAM、samtools QC/coverage 与 bcftools 候选 VCF；只完成合成真值验证，不包含生产参考、重校准、队列 calling、注释或临床解释 |
| 生产级 WGS/WES | 规划中 | 仍需参考 bundle、区间处理、可扩展执行、生产 caller/QC 规范、注释、队列验证和运行监控 |
| FASTQ 到表达矩阵 | 规划中 | 当前 bulk 与单细胞从 count matrix 开始，尚无 trimming、比对/伪比对或基因/转录本定量 |
| 宏基因组 | 规划中 | 尚无分类、组装、binning 或功能注释管线 |
| 蛋白组 | 规划中 | 尚无 raw MS 搜索、鉴定、FDR 控制或定量管线 |
| 病理切片 | 规划中 | 尚无 WSI/DICOM viewer |
| 实验验证与采购 | 规划中 | 可以讨论验证设计，但不连接供应商或实验室系统 |
| 云端协作与托管执行 | 规划中 | 当前为本地单用户服务；GitHub Pages 只能托管静态界面 |

该表只描述可观察、可验证的产品行为。可见按钮、占位符或尚未通过测试的开发代码不计为已实现能力。
