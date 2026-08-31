# 架构

[English](ARCHITECTURE.md) | 简体中文

## 主线

```text
研究问题
  -> 本地 Agent
  -> 直接调用注册 skill
     或 guided plan -> 研究者审批 -> 按顺序执行注册 skills
  -> 本地数据或计算
  -> typed artifact 与工具 trace
  -> 可检查结论与下一步分析
```

## 仓库结构

`molemo/` 是 Python 应用包，包含 Agent、科学客户端、工作流运行时、数据边界和 HTTP 服务。仓库根目录仅保留 `server.py` 与 `bench.py` 两个兼容启动入口，因此原有命令不变，也可以使用 `python -m molemo`。

`skills/` 保存自动发现的 skill manifest、Agent 说明与 handler；`tools/` 保存隔离的分析 runner；`tests/` 覆盖工具正确性、审批边界与 artifact；`benchmarks/` 保存确定性的过程评测；`workspace/` 是唯一允许导入和生成科研文件的区域。

## 运行边界

`molemo/server.py` 提供 molecule、protein、chat、skills、tool call、workspace、workflow plan 和 run approval 接口。静态前端不能绕过本地 API 批准执行。

`molemo/agent_runtime.py` 实现 OpenAI-compatible Chat Completions 工具循环。第三方 endpoint、model 与 key 只存在于当前页面内存和单次本地请求中，不写入运行记录。Native mode 允许模型选择 Agent-callable tools；grounded mode 先在本地计算当前科学上下文。

`molemo/skill_runtime.py` 从 `skills/*/skill.json` 加载 schema 与 handler。标记为 `agent_callable: false` 的执行工具不会出现在第三方模型 schema 中，也不能被模型直接调用；它们只能由研究者批准后的 workflow 执行。发送给模型的 GEO、结构、矩阵、文献和临床结果会先压缩，保留来源与关键边界，省略大型显示数据。

`molemo/workflow_runtime.py` 把二十三类研究流程转为持久化计划。新计划从 `pending_approval` 开始且 trace 为空。paired-end DNA calling、GEO、蛋白保守性、实验变体结构、bulk/single-cell RNA-seq、ChEMBL、人类基因集、VCF、HMMER、靶点证据、文献、临床试验和变异证据等流程会在创建计划时执行有界 preflight。只有本地运行接口能够批准计划。

`molemo/workspace_utils.py` 将路径限制在 `workspace/`，限定文件类型、文本读取和上传大小。Agent 可以列出与读取受支持文件；写入只来自显式上传或批准后的有界 pipeline。

`molemo/bio_clients.py` 是外部数据边界，只允许访问固定的官方科学数据库域名，并限制请求、响应、二进制传输和重定向。无 NCBI API key 时，E-utilities 请求不超过每秒三次。

## 科学数据通道

`molemo/geo_dataset_discovery.py` 将研究主题、物种、assay 和最小样本量转换为可检查的 GEO Series 检索；批准后保存数据集表、样本示例、报告、manifest 与摘要，不下载矩阵或判断研究质量。

`molemo/geo_series_matrix.py` 只接受精确 GSE 和官方 Series Matrix 文件。审批前固定来源与压缩大小；审批后限制压缩/解压大小、样本、特征和矩阵单元，省略联系信息并保存原始 gzip、矩阵、样本元数据、QC、manifest 与摘要。Series Matrix 不被当作 raw counts。

`molemo/transcriptomics.py` 只接受基因级非负整数 raw counts 与精确匹配的样本设计，批准后调用 PyDESeq2。`molemo/single_cell.py` 接受有界 CSV/TSV、AnnData 与标准 10x 输入，批准后调用 Scanpy 完成 QC、可选 Scrublet、归一化、HVG、PCA、neighbors、UMAP、Leiden 和描述性 marker 排名。

`molemo/vcf_cohort.py` 审阅有界 VCF 4.x 和可选样本 metadata，保留 REF/ALT、GT、AD、DP、VAF、FILTER、样本 QC 与轨迹，不做 raw-read calling、somatic/germline 判定或临床解释。

`molemo/dna_variant_calling.py` 在审批前验证同步的 paired FASTQ、有界 FASTA 参考、样本名、资源限制以及本地 BWA/samtools/bcftools 版本。批准后以固定参数、无 shell 的方式把 BWA-MEM 流式接入坐标排序，生成并索引 BAM，记录比对与 coverage，再输出标准化、未过滤的候选 VCF。BAM/BAI、VCF、coverage、变异表、摘要、版本、哈希与 manifest 会原子写入 `workspace/analyses/`。这条通道用于验证小型参考上的系统闭环，不是生产级 WGS/WES 或临床 caller。

蛋白与结构通道由 `sequence_search.py`、`hmmer_search.py`、`multiple_alignment.py`、`structure_io.py` 和 `variant_structure.py` 实现；公共证据通道由 `target_evidence.py`、`chembl_bioactivity.py`、`functional_analysis.py`、`literature_review.py`、`clinical_trials.py`、`clinical_trial_results.py` 和 `variant_evidence.py` 实现。每条通道保留原始标识符、参数、版本、来源和适用边界，不把数据库分数包装成因果或临床结论。

## 前端

前端只渲染 typed artifacts，不渲染模型提供的任意 HTML。主要布局让研究会话与当前证据并列；运行、结果和 skill 页使用无装饰的整高文档表面，方便检查密集数据。中英文切换只改变界面和用户文档，不改变工具 schema、科学标识符、保存文件或运行 provenance。

## 扩展

新增 skill 时使用：

```text
skills/new-skill/
├── SKILL.md
├── agents/openai.yaml
├── skill.json
└── scripts/handler.py
```

新的多步骤或有副作用的 pipeline 必须经过 workflow 审批边界，使用有界工作目录、明确资源限制、可恢复运行标识和可检查 artifact，之后才能暴露给 Agent。
