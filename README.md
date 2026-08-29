# Molemo WorkBench

Molemo WorkBench 把生命科学问题连接到可检查的本地证据。用户可以接入自己的 OpenAI-compatible 模型；模型负责理解问题和选择工具，分子解析、蛋白序列计算、文件读取、管线执行与可视化则在本机通过注册 skills 完成。每次运行保留工具参数、状态、摘要和 artifact，使结论能够被回看、导出和评测。

当前仓库是这一主线的可运行参考实现，也是 `Molemo_Bench v0.6`。它借鉴了 Rosalind Workbench 将问题、计划、工具、viewer 和证据放在同一工作区的产品范式，但不依赖 GPT-Rosalind，也不与 OpenAI Rosalind 项目关联。前端采用克制的研究会话与证据双栏；进入运行、结果或工具页后，右侧切换为整高文档视图，不把科学工作流做成展示型仪表盘。

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

环境中的 `blast` 来自 [Bioconda](https://bioconda.github.io/recipes/blast/README.html)，本地搜索参数与任务遵循 [NCBI BLAST+ Command Line Applications User Manual](https://www.ncbi.nlm.nih.gov/books/NBK279691/)。Bulk RNA-seq 差异表达使用 [PyDESeq2](https://pydeseq2.readthedocs.io/en/stable/)；仓库会优先发现项目级 `.molemo-tools` 运行时，因此不要求修改 conda `base`。

页面默认使用本地 skill runtime。要使用第三方模型，在右上角 API 设置中填写完整的 Chat Completions endpoint、模型名和 API key：

- `Native tool calling`：模型通过 OpenAI-compatible tools 自主选择本地 skills。
- `Grounded chat`：本地先计算当前分子或蛋白上下文，再发送给不支持 tools 的兼容模型。

API key 只在当前页面内存与单次本地请求中使用，不保存到文件，也不会进入导出的运行记录。

## 已实现的闭环

1. 从自然语言研究问题进入本地 Agent。
2. 单步任务可直接调用结构化科学工具；多步任务先生成具体计划。
3. 研究者在“运行”页检查输入、工具和步骤，明确批准后才开始执行。
4. RDKit、NCBI BLAST+、PyDESeq2、序列算法、公共数据库或受控 workspace 按计划生成来源明确的结果。
5. 前端把结果呈现为分子结构、真实 PDB/mmCIF 蛋白结构、序列、BLAST 命中与比对、FASTQ QC、PCA、volcano、heatmap 或性质图 artifact。
6. 工具 trace、计划状态、结论、候选设计和 artifact 可导出为 JSON。
7. `Molemo_Bench v0.6` 对工具正确性、审批边界、trace 完整性和 artifact 生成进行回归评测。

当前包含 13 个 skills、21 个工具和九类 guided workflow：研究路由、靶点证据比较、分子分析、蛋白分析、双序列比对、本地 BLASTP/BLASTN、bulk RNA-seq 差异表达、科学可视化、受控 workspace、PubChem/UniProt/Open Targets 检索、RCSB PDB 与本地 PDB/mmCIF 结构、FASTQ 质量控制。

靶点证据工作流接受一个疾病和最多八个候选靶点。创建计划时先把疾病解析为 EFO/MONDO 记录、把靶点解析为 Ensembl Gene ID；研究者批准后，才查询并保存 Open Targets 原始 association score、分证据类型得分、tractability、pathway、safety liability、临床药物和文献来源。结果使用原始 association score 排序，不另造综合分，并明确提示该分数不是概率、置信度或因果结论。

Agent 可以调用预检、列出和创建计划，但 BLAST、差异表达与靶点比较执行工具都不暴露给第三方模型。PubChem、UniProt、RCSB 和 Open Targets 访问固定官方域名，不需要用户 API key；页面中的第三方 LLM key 仍由用户自己提供。

## 评测与测试

```bash
python bench.py
python -m unittest discover -s tests -v
```

基准任务位于 `benchmarks/tasks.jsonl`。它是对 Molemo 工具链的过程评测，不代表模型在完整生命科学研究中的总体能力。

## 能力边界

当前版本已覆盖中心化 Chat、第三方模型接入、研究者审批、本地科学工具、候选靶点证据比较、分子 viewer、PDB/mmCIF 原子坐标、公共数据库检索、序列与比对、本地 FASTA 数据库上的 BLASTP/BLASTN、FASTQ QC、raw-count bulk RNA-seq 差异表达、受控文件工作区和可审计运行记录。guided workflow 当前同步执行九类固定模板，不是任意 shell 管线。靶点比较目前限于 Open Targets 公共证据，尚未接入内部实验结果、完整论文综述或自定义加权模型；此外仍未实现 HMMER、远程或大规模 BLAST 数据库、FASTQ 到表达矩阵的 alignment/quantification、单细胞分析、病理切片和实验采购。没有坐标文件时显示的蛋白序列图仍是序列启发式视图。

详细范围见 [能力矩阵](docs/CAPABILITY_MATRIX.md) 和 [架构说明](docs/ARCHITECTURE.md)。公开参照为 [OpenAI Rosalind](https://openai.com/rosalind/) 与 [OpenAI Life Science Research plugin](https://github.com/openai/plugins/tree/main/plugins/life-science-research)。

## License

MIT
