# 路线图

[English](ROADMAP.md) | 简体中文

Molemo 由两个相连产品组成：**Molemo WorkBench** 是可审计的本地 Agent runtime；**Molemo** 是把代码、科学文件、对话、审批和 artifacts 放在同一编辑器中的桌面体验。

## 当前已验证

- WorkBench：26 个 skills、50 个工具、23 类带审批边界的 workflow 模板。
- 分子、蛋白、公共证据、bulk RNA、单细胞、processed VCF 与有界本地序列工作流。
- 从 paired FASTQ 到 BAM/BAI、coverage 和候选 VCF 的确定性 DNA 案例。
- 覆盖 RDKit、蛋白序列、BWA/samtools/bcftools、PyDESeq2 与 Scanpy 的五个真实案例。
- Molemo 编辑器 MVP：连接本机 WorkBench 的中英文 VS Code/Cursor 扩展。

## 下一阶段能力主线

1. **生产级 WGS/WES：**版本化参考 bundle、区间与分片、生产 QC/caller、注释、队列验证、重试、provenance 和可扩展执行。
2. **FASTQ 到表达矩阵：**reads QC、trimming 规范、比对或伪比对、基因/转录本定量、MultiQC 式审阅，再进入现有矩阵工作流。
3. **宏基因组：**分类、适用时的组装/binning、功能注释、污染控制和数据库版本化。
4. **蛋白组：**raw MS 导入、搜索参数、肽段/蛋白 FDR、标记或无标记定量，以及可检查的谱图与证据表。
5. **病理：**分块 WSI/DICOM viewer、标注、模型 overlay、provenance 和有界本地推理。
6. **Molemo 桌面版：**把已验证扩展打入 Molemo 品牌 Code-OSS，增加科学编辑器、独立 artifact 标签页、环境管理和终端感知的管线控制。

每条主线只有在具备可复现实例、审批边界、typed artifacts、持久化 provenance、自动化测试与 benchmark 后，才会标记为“已实现”。
