# Architecture

## Main line

```text
research question
  -> local Agent
  -> direct registered skill
     or guided plan -> researcher approval -> ordered registered skills
  -> local data or computation
  -> typed artifact and tool trace
  -> inspectable conclusion and next analysis
```

## Components

`server.py` is the local boundary. It serves the workbench and exposes molecule, protein, chat, skills, tool-call, workspace, workflow-plan and run-approval endpoints.

`agent_runtime.py` implements the OpenAI-compatible Chat Completions tool loop. Provider credentials are accepted only in the request body, forwarded once, and omitted from results and logs. Native mode lets the provider choose tools; grounded mode precomputes active scientific context for providers without tool support.

`skill_runtime.py` discovers every `skills/*/skill.json`, loads its declared handler, exports compatible function schemas and normalizes execution metadata. A tool can declare `agent_callable: false`; it remains available to approved workflows but is absent from third-party model schemas and rejected by direct tool calls. Oversized GEO dataset and Series Matrix, alignment, experimental variant-structure, ChEMBL, literature and clinical-trial results are compacted for model context by removing display matrices, viewer coordinates, duplicate artifacts and long structure/description fields while retaining exact source evidence. `SKILL.md` keeps each workflow usable as a standalone Codex/ChatGPT skill.

`workflow_runtime.py` turns twenty-two supported research workflows into concrete, persisted plans. A new run starts as `pending_approval` with an empty trace. GEO public dataset discovery, GEO Series Matrix import, protein MSA/site conservation, experimental variant-structure, bulk and single-cell RNA-seq, ChEMBL target-bioactivity, human gene-set functional analysis, VCF cohort, HMMER profile search, target-evidence, literature, clinical-trial landscape, exact clinical-trial results and variant-evidence plans additionally run bounded preflight before they can be created. Approval is available only through the local run API, which moves the run through `running`, `completed` or `failed` while recording each tool result. The Agent-facing guided-workflows skill can list, create and inspect plans but exposes no approval tool.

`workspace_utils.py` confines file access to `workspace/`, limits text size and accepts only supported scientific text formats. Agent tools can list and read files. Writes occur only through an explicit UI upload or an approved bounded pipeline output.

`bio_clients.py` is the outbound data boundary. It accepts only HTTPS requests to fixed NCBI, ChEMBL, Europe PMC, ClinicalTrials.gov, ClinVar/NLM, Ensembl, gnomAD, PubChem, UniProt, RCSB, AlphaFold DB, Open Targets, Reactome and STRING hosts, and applies request/response limits. Redirect targets are revalidated against the same allowlist; binary transfers are bounded before and during body reads. NCBI E-utilities requests are serialized at no more than three requests per second when no API key is used. AlphaFold retrieval selects the exact requested UniProt accession and accepts model downloads only from the official versioned PDB file path. STRING v12 uses a constrained no-shell `curl` GET transport because its CDN challenges Python HTTP clients; encoded identifiers are supplied through standard input rather than process arguments, and requests remain serialized, time-bounded and size-bounded.

`geo_dataset_discovery.py` converts a topic, optional exact organism, assay scope and minimum sample count into an inspectable NCBI GEO DataSets query restricted to Series records. Preview returns at most eight source-ordered records. Approved collection normalizes GSE accessions, titles, organisms, sample counts, assay types, dates, summaries, bounded sample examples, linked PubMed IDs and official download locations, then atomically publishes two TSV tables, a JSON report, manifest and Markdown summary under `workspace/analyses/`. It does not download expression matrices, evaluate batch compatibility, rank study quality or run downstream statistics.

`geo_series_matrix.py` is the separate GEO data-transfer boundary. It accepts one exact GSE accession, lists only the accession's official Series Matrix directory, and requires an exact filename when multiple platform matrices exist. Preflight records the selected file and compressed size. Approved execution downloads at most 32 MiB of gzip data, streams at most 160 MiB uncompressed, validates sample/feature uniqueness, numeric cells and fixed dimension/cell limits, excludes contact metadata, and atomically publishes the original gzip, matrix TSV, sample metadata TSV, QC report, manifest and summary. Submitter-processed values remain explicitly incompatible with the raw-count PyDESeq2 workflow.

`functional_analysis.py` is the human gene-set boundary. Preflight accepts two to fifty unique identifiers, fixes the organism to Homo sapiens, resolves STRING identifiers, exposes unmapped terms and records the approved STRING confidence, FDR, term limit and Reactome disease-pathway setting. Approved execution keeps Reactome overrepresentation and STRING enrichment statistics separate, preserves the v12 functional-association edges and PPI-enrichment result, and atomically publishes four TSV tables, a JSON report, manifest, artifact index and Markdown summary. It does not treat FDR as a truth probability, infer causality, treat genes as replicates or claim that a STRING edge is a direct physical interaction.

`literature_review.py` builds an explicit Europe PMC query from the user's terms and approved filters, performs a bounded `core` metadata search, preserves source relevance order, and normalizes identifiers, publication types, access state and abstracts. Preview is capped at ten records for Agent synthesis. Approved collection atomically publishes `papers.tsv`, a full JSON report, manifest and Markdown summary under `workspace/analyses/`. It records citation counts only as bibliographic context and performs no quality grading from them.

`target_evidence.py` resolves disease and target entities through the Open Targets GraphQL API, keeps candidate sets bounded, and normalizes association scores, evidence types, tractability, pathways, safety liabilities, clinical precedence and publication IDs. The preflight is read-only. Approved execution atomically publishes a TSV comparison, full JSON report, manifest and Markdown summary under `workspace/analyses/`; it never converts the association score into a probability or custom confidence value.

`chembl_bioactivity.py` resolves one exact UniProt accession to one ChEMBL `SINGLE PROTEIN` target, then retrieves a bounded potency-ordered sample of standardized binding and/or functional activities. It retains only target confidence score 9 with direct relationship type `D`, non-duplicate valid rows with canonical SMILES, while preserving pChEMBL, endpoint relation/value/unit, assay class, BAO format, assay description and source document. Approved execution atomically publishes activity and compound TSVs, a JSON report, manifest and Markdown summary under `workspace/analyses/`. Confidence score 9 is treated as a target-assignment field, not proof of direct physical binding or assay quality; mixed endpoints are not collapsed and potency is not converted into selectivity, mechanism, developability, safety or efficacy claims.

`variant_evidence.py` resolves a versioned RefSeq HGVS, rsID or ClinVar identifier to one simple allele. Ambiguous rsIDs, haplotypes and complex records stop during preflight. Approved execution retrieves ClinVar aggregate assertions, Ensembl VEP transcript consequences and gnomAD v4 population observations, keeps those evidence lanes separate, and atomically publishes a TSV evidence table, JSON report, manifest and Markdown summary under `workspace/analyses/`. It performs no de novo ACMG/AMP classification.

`vcf_cohort.py` validates a bounded uncompressed VCF 4.x file and optional exact-match sample metadata from the workspace. It preserves REF/ALT order, handles multiallelic `GT`, `AD`, `DP` and allele-specific `AF`, reproduces `CSQ/ANN` annotations, and separates observed calls from calls excluded by FILTER, depth or VAF. Approved execution atomically publishes variant, call, sample-QC and trajectory TSVs plus JSON, manifest, Markdown and input SHA-256 hashes under `workspace/analyses/`. It does not perform raw-read calling, somatic/germline classification, driver inference, treatment-response assessment or clinical interpretation.

`hmmer_search.py` validates bounded HMMER3 amino-acid profile files and protein FASTA databases from the workspace, including model identity, alphabet, sequence count, total residues, thresholds and local HMMER version. Approved execution invokes `hmmsearch` without a shell under fixed CPU, timeout and output limits, parses the official 22-field `domtblout` layout, preserves profile/target/domain coordinates, E-values, scores, bias and accuracy, and atomically publishes hit/domain TSVs, a stable source `domtblout`, JSON, manifest, Markdown and input SHA-256 hashes. It does not build profiles, download Pfam, run `hmmscan`, search remote databases or infer function from a match.

`clinical_trials.py` builds a bounded ClinicalTrials.gov API v2 query from an approved condition, optional intervention, status scope and study scope. Preview is capped at ten source-ordered records. Approved collection normalizes NCT IDs, status, phase, sponsor, design, registered endpoints, eligibility, dates, countries, posted-results availability and linked publications, then atomically publishes `trials.tsv`, a JSON report, manifest and Markdown summary under `workspace/analyses/`. It does not treat registry metadata as efficacy or safety evidence.

`clinical_trial_results.py` retrieves one exact NCT record only after posted tabular results are confirmed. It keeps participant-flow, baseline and outcome group mappings separate, preserves submitted units, denominators, p-values and confidence intervals, and captures adverse-event totals, protocol/SAP documents and linked publications in source order. Approved execution atomically publishes five TSV tables, a JSON report, manifest and Markdown summary under `workspace/analyses/`. It does not reanalyze participant-level data or calculate a custom effect, safety, certainty or quality score.

`structure_io.py` parses the first PDB/mmCIF model, preserves B-factors, derives chain sequences and ligands, and produces a bounded atom-level viewer representation. Only the AlphaFold handler interprets those values as pLDDT and labels the artifact as predicted; RCSB and local structures retain distinct coordinate semantics. AlphaFold PAE retrieval is an optional evidence channel: the parser requires a bounded square matrix matching the model residue count, preserves scored-residue versus aligned-residue direction, and mean-downsamples contiguous residue blocks to at most 384 display bins. A PAE failure leaves the coordinate artifact available with an explicit caveat, while `compact_tool_result` omits the matrix from third-party model context. `ngs_qc.py` streams workspace FASTQ files and calculates Phred+33, Q20/Q30, GC, N, read-length and per-cycle statistics.

`variant_structure.py` resolves one experimental RCSB entry, exact author chain and one-letter substitution. It requires the observed residue to match the reference or alternate amino acid, computes minimum heavy-atom distances from that residue to other polymer residues and coordinate hetero groups, and annotates a bounded site/global viewer sample. Approved execution atomically publishes contact and ligand-instance TSVs, JSON, manifest and Markdown under `workspace/analyses/`. It does not infer residue-number mappings, covalent connectivity, binding energy, functional effect, pathogenicity or clinical actionability.

`multiple_alignment.py` validates a bounded workspace protein FASTA, one exact reference identifier and a positive position or one-letter substitution. Approved execution invokes project-pinned MAFFT 7.526 without a shell, with one thread, fixed timeout and output limits; it verifies that residues and input order are preserved, maps the reference position to one alignment column, and calculates unweighted consensus support, identity, occupancy, gaps and entropy. It atomically publishes the alignment, conservation and site-observation tables, JSON report, manifest and Markdown summary under `workspace/analyses/`. The workflow does not establish orthology, correct for phylogeny, or infer function, pathogenicity or mutational effect.

`transcriptomics.py` is the bulk RNA-seq boundary. It accepts workspace CSV/TSV raw integer counts and sample metadata, enforces exact sample matching, replication, estimable contrast and bounded dimensions, then invokes `tools/run_pydeseq2.py` without a shell only after workflow approval. The runner fixes CPU use, writes into a temporary directory, and atomically publishes differential-expression tables, normalized counts, package versions, manifest and summary under `workspace/analyses/`.

`single_cell.py` is the processed single-cell boundary. It resolves bounded cell-by-gene CSV/TSV, AnnData `.h5ad`, 10x H5 and standard compressed or uncompressed 10x MTX inputs. `tools/single_cell_io.py` is shared by preflight and execution, validates the selected raw-count matrix, preserves AnnData observations, and exactly joins optional external cell metadata. Preflight runs in the isolated Scanpy runtime and records input format, selected count layer and all 10x component paths. After approval, `tools/run_scanpy.py` applies cell/gene QC, optional whole-dataset or batch-aware Scrublet scoring, CP10k/log1p normalization, highly variable genes, PCA, neighbors, UMAP, Leiden clusters and descriptive Wilcoxon markers with fixed CPU and random-seed settings. Scrublet predictions are retained by default and may be excluded only by a separate approved input. The runner atomically publishes TSV tables, `.h5ad`, package versions, source hashes, thresholds, exclusion decisions, manifest and summary under `workspace/analyses/`. It performs no cell-type naming, ambient-RNA correction, batch integration, trajectory inference or donor-aware differential expression.

`sequence_search.py` is the local NCBI BLAST+ boundary. It accepts only workspace FASTA databases, validates sequence alphabets and file size, caps query length, hits, threads and runtime, executes without a shell in a disposable hidden directory, disables BLAST usage reporting, parses JSON output and removes temporary database files after each run.

The frontend renders typed artifacts rather than arbitrary model HTML. Its primary layout keeps the research conversation beside the active evidence viewer. Data and design tabs retain the structure viewer; run, result and skill tabs switch to an unframed, full-height document surface for dense inspection. This keeps visual output reviewable and prevents provider responses from injecting executable UI.

## Extending the workbench

Add a skill directory containing:

```text
skills/new-skill/
├── SKILL.md
├── agents/openai.yaml
├── skill.json
└── scripts/handler.py
```

`skill.json` declares tool names, descriptions, JSON schemas and handler references. A handler receives JSON arguments and returns a JSON object. Return `artifacts` when the frontend should visualize a result.

New multi-step or mutating pipelines must use the workflow approval boundary, a bounded working directory, explicit resource limits and a resumable run identifier before they are exposed to an LLM.
