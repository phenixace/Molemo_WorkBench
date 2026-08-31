# Molemo WorkBench

English | [简体中文](README.zh-CN.md)

Molemo WorkBench connects a life-science question, a user-provided LLM API, local scientific tools, and inspectable evidence in one workspace. The Agent interprets the question and selects registered tools; local skills perform data retrieval, molecular and protein computation, bounded pipelines, and visualization. Every run retains its inputs, researcher approval, tool trace, results, and artifacts for review, export, and evaluation.

This repository is the runnable reference implementation for that workflow and for `Molemo_Bench v0.22`. It follows the product pattern of Rosalind Workbench without depending on GPT-Rosalind or claiming affiliation with OpenAI's Rosalind project. The interface is deliberately restrained: research conversation on the left, active evidence or a full-height result document on the right.

## Run locally

Use the existing conda environment when it already contains RDKit:

```bash
/opt/miniconda3/bin/python server.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). A dedicated environment can also be created:

```bash
conda env create -f environment.yml
conda activate molemo-bench
python server.py
```

The server, benchmark launcher, and scientific runtime now live in a conventional Python package. `server.py` and `bench.py` at the repository root are compatibility entry points; `python -m molemo` is also supported.

## Model connection

Molemo works locally without a third-party model. To connect one, open the model settings and provide a complete OpenAI-compatible Chat Completions endpoint, model name, and your own API key.

- **Native tool calling** lets the provider choose from the Agent-callable local skills.
- **Grounded chat** computes the active molecular or protein context locally before sending it to a provider without tool support.

The key is kept only in page memory and the current local request. It is not written to disk or included in exported run records. Public NCBI and other supported scientific databases do not require a user API key.

## Research loop

1. Start from a natural-language biological question.
2. Run a bounded read-only tool directly, or create a concrete guided plan.
3. Inspect inputs, assumptions, tools, and steps before execution.
4. Approve mutating or multi-step work only in the local WorkBench.
5. Review typed scientific artifacts, provenance, caveats, and saved outputs.
6. Continue from the result into the next biological question or analysis.

The stable build currently registers **26 skills, 50 tools, and 23 guided workflows**.

## Implemented capabilities

### Molecules and proteins

- RDKit-backed SMILES parsing, atom/bond graphs, rings, descriptors, and molecule visualization.
- Protein FASTA normalization, sequence properties, hydropathy, and pairwise alignment.
- Local BLASTP/BLASTN against bounded workspace FASTA databases.
- HMMER profile-to-sequence domain search.
- MAFFT protein-family alignment and exact reference-site conservation review.
- RCSB experimental structures, AlphaFold DB models with pLDDT and directional PAE, and local PDB/mmCIF parsing.
- Experimental variant-site and local heavy-atom contact review.

### Evidence and public data

- NCBI GEO Series discovery by topic, organism, assay type, and sample count.
- Approval-gated import of an exact official GEO Series Matrix with structural QC, minimized sample metadata, source hash, and explicit processed-value semantics.
- ChEMBL target-ligand bioactivity, Open Targets target evidence, Reactome/STRING functional analysis, Europe PMC literature maps, ClinicalTrials.gov landscapes and posted results, and ClinVar/VEP/gnomAD variant evidence.

### Sequencing and local analysis

- Streaming FASTQ quality control.
- Approval-gated paired-end DNA alignment and candidate calling with BWA-MEM, samtools, and bcftools; BAM/BAI, coverage, VCF, tabular calls, hashes, and manifests remain inspectable.
- Raw-count bulk RNA-seq differential expression with PyDESeq2.
- Raw-count CSV/TSV, AnnData, and 10x single-cell exploration with Scanpy, optional Scrublet, UMAP, Leiden, and marker ranking.
- Bounded processed multi-sample VCF review with depth/VAF rules, mutation matrices, and longitudinal trajectories.
- Constrained workspace uploads, approval-gated execution, saved manifests, and auditable run history.

GEO Series Matrix values remain submitter-processed measurements. Molemo never assumes they are raw counts, TPM, CPM, or log2 values, and it does not send them directly to PyDESeq2. Experimental groups, biological replication, platform annotation, normalization, and batch structure remain researcher decisions.

## Repository layout

```text
molemo/             Python application, Agent, clients, and workflow runtime
skills/             Auto-discovered scientific skill manifests and handlers
tools/              Isolated analysis runners
tests/              Unit and workflow-boundary tests
benchmarks/         Deterministic Molemo_Bench tasks
workspace/examples/ Versioned synthetic and small reference fixtures
showcase/           English and Simplified Chinese runnable case guide
docs/               English and Simplified Chinese technical documentation
server.py           Compatibility server launcher
bench.py            Compatibility benchmark launcher
```

## Evaluation

```bash
python bench.py
python -m unittest discover -s tests -v
```

The committed v0.22 baseline passes 146 tests and 39/39 deterministic benchmark tasks. The benchmark evaluates tool correctness, approval boundaries, trace completeness, provenance, and artifact generation; it is not a claim about general life-science model intelligence.

## Runnable showcase

```bash
python -m molemo.showcase
python -m molemo.showcase --full
```

The quick showcase runs caffeine, Trp-cage, and the paired-end DNA truth set. Full mode also executes the real PyDESeq2 and Scanpy examples and writes `reports/showcase.json`. See the [showcase guide](showcase/README.md) for expected signals and scientific boundaries.

## Current boundaries

Molemo is a local research workbench, not a clinical system. It does not provide diagnostic or treatment recommendations, execute arbitrary shell commands from a model, infer causality from database scores, or convert exploratory outputs into biological truth claims.

The current NGS surface includes FASTQ QC, a bounded paired-end FASTQ-to-BAM/VCF demonstration, count-matrix analysis, processed VCF review, and supported single-cell inputs. The DNA example uses a small synthetic reference and emits unfiltered research candidates; it is not a production or clinical caller. Production FASTQ-to-expression, human WGS/WES, metagenomics, proteomics, pathology slides, laboratory automation, procurement, hosted collaboration, and a cloud execution backend remain outside the stable release. GitHub Pages can host only the static interface; the Python API requires a separate runtime.

See the [capability matrix](docs/CAPABILITY_MATRIX.md), [roadmap](docs/ROADMAP.md), and [architecture](docs/ARCHITECTURE.md) for the exact scope. Public references include [OpenAI Rosalind](https://openai.com/rosalind/), the [OpenAI Life Science Research plugin](https://github.com/openai/plugins/tree/main/plugins/life-science-research), [NCBI GEO programmatic access](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html), and the [GEO download instructions](https://www.ncbi.nlm.nih.gov/geo/info/download.html).

## License

MIT
