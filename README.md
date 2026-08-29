# Molemo WorkBench

Molemo WorkBench 把生命科学问题连接到可检查的本地证据。用户可以接入自己的 OpenAI-compatible 模型；模型负责理解问题和选择工具，分子解析、蛋白序列计算、文件读取、管线执行与可视化则在本机通过注册 skills 完成。每次运行保留工具参数、状态、摘要和 artifact，使结论能够被回看、导出和评测。

当前仓库是这一主线的可运行首版，也是 `Molemo_Bench v0` 的参考实现。它借鉴了 Rosalind Workbench 将问题、工具、viewer 和证据放在同一工作区的产品范式，但不依赖 GPT-Rosalind，也不与 OpenAI Rosalind 项目关联。

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

页面默认使用本地 skill runtime。要使用第三方模型，在右上角 API 设置中填写完整的 Chat Completions endpoint、模型名和 API key：

- `Native tool calling`：模型通过 OpenAI-compatible tools 自主选择本地 skills。
- `Grounded chat`：本地先计算当前分子或蛋白上下文，再发送给不支持 tools 的兼容模型。

API key 只在当前页面内存与单次本地请求中使用，不保存到文件，也不会进入导出的运行记录。

## 已实现的闭环

1. 从自然语言研究问题进入本地 Agent。
2. Agent 发现并调用 `skills/` 下的结构化工具。
3. RDKit、序列算法或受控 workspace 在本机生成结果。
4. 前端把结果呈现为分子结构、蛋白序列、比对或性质图 artifact。
5. 工具 trace、结论、候选设计和 artifact 可导出为 JSON。
6. `Molemo_Bench v0` 对工具正确性、trace 完整性和 artifact 生成进行回归评测。

首版包含 6 个 skills、8 个工具：研究路由、分子分析、蛋白分析、序列比对、科学可视化和受控 workspace。新增 skill 只需加入 `SKILL.md`、`skill.json` 与 handler，服务会自动发现。

## 评测与测试

```bash
python bench.py
python -m unittest discover -s tests -v
```

基准任务位于 `benchmarks/tasks.jsonl`。它是对 Molemo 工具链的过程评测，不代表模型在完整生命科学研究中的总体能力。

## 能力边界

当前版本已覆盖中心化 Chat、第三方模型接入、本地科学工具、分子 viewer、序列与比对 artifact、受控文件工作区和可审计运行记录。PDB/mmCIF 原子级蛋白结构、公共数据库检索、BLAST/HMMER、完整 NGS、病理切片和实验采购尚未实现，不能把序列启发式图当作真实三维结构。

详细范围见 [能力矩阵](docs/CAPABILITY_MATRIX.md) 和 [架构说明](docs/ARCHITECTURE.md)。公开参照为 [Rosalind Workbench](https://learn.chatgpt.com/blog/rosalind-workbench) 与 [OpenAI Life Science Research plugin](https://github.com/openai/plugins/tree/main/plugins/life-science-research)。

## License

MIT
