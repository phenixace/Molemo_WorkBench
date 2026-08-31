# Molemo 案例展示

简体中文 | [English](README.md)

这些案例用小型、确定性的输入验证 Molemo WorkBench 的真实代码路径，不替代生产队列验证。

```bash
python -m molemo.showcase
python -m molemo.showcase --full
```

快速模式验证咖啡因分子图、Trp-cage 蛋白画像，以及经过审批的 paired-end FASTQ 到 BAM/VCF 工作流。完整模式还会实际执行 PyDESeq2 bulk RNA-seq 和 Scanpy 单细胞流程。机器可读报告写入 `reports/showcase.json`。

合成 DNA 案例包含 80 对 reads 和一个位于 `molemo_demo_reference:1201 A>C` 的杂合真值变异。通过条件是精确恢复该等位基因为 `0/1`，并保留 BAM、BAI、VCF、coverage、变异表、输入输出哈希和运行 manifest。

生产级人类 WGS/WES、宏基因组、蛋白组、病理切片和 FASTQ 到表达定量仍是独立路线。这里的 demo caller 明确限制在小型参考，不进行临床解释。
