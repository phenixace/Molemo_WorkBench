"""Bounded NCBI GEO Series discovery with persisted query provenance."""

from __future__ import annotations

import csv
import json
import re
import shutil
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urlparse

from bio_clients import ExternalDataError, get_json
from workspace_utils import WORKSPACE_ROOT


EUTILS_ROOT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
GEO_SITE = "https://www.ncbi.nlm.nih.gov/geo/"
GEO_RECORD = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
MAX_QUERY_CHARS = 240
MAX_RESULTS = 20
MAX_PREVIEW_RESULTS = 8
MAX_SAMPLE_EXAMPLES = 5
MAX_SUMMARY_CHARS = 1400
MAX_SAMPLES = 100000

ASSAY_SCOPES = {
    "all": {"label": "All GEO Series types", "query": ""},
    "rna_seq": {
        "label": "RNA-seq",
        "query": '"Expression profiling by high throughput sequencing"[GTYP]',
    },
    "single_cell": {
        "label": "Single-cell RNA-seq",
        "query": (
            '"Expression profiling by high throughput sequencing"[GTYP] AND '
            '("single cell"[ALL] OR "single-cell"[ALL] OR scRNA[ALL])'
        ),
    },
    "array": {
        "label": "Expression array",
        "query": '"Expression profiling by array"[GTYP]',
    },
    "methylation": {
        "label": "Methylation profiling",
        "query": (
            '("Methylation profiling by high throughput sequencing"[GTYP] OR '
            '"Methylation profiling by array"[GTYP])'
        ),
    },
}


class GeoDatasetError(ValueError):
    """Raised when a GEO discovery query or response is invalid."""


def normalize_geo_dataset_inputs(
    query: str,
    organism: str = "Homo sapiens",
    assay_scope: str = "all",
    min_samples: int | str = 4,
    max_results: int | str = 12,
) -> dict[str, Any]:
    cleaned_query = re.sub(r"\s+", " ", str(query or "")).strip()
    if not cleaned_query or len(cleaned_query) > MAX_QUERY_CHARS:
        raise GeoDatasetError(f"GEO query must contain between 1 and {MAX_QUERY_CHARS} characters.")
    if any(ord(char) < 32 for char in cleaned_query):
        raise GeoDatasetError("GEO query contains unsupported control characters.")
    if re.search(r"\bsort\s*(?:=|:)", cleaned_query, re.I):
        raise GeoDatasetError("Sort directives are not accepted; discovery preserves NCBI relevance order.")

    cleaned_organism = re.sub(r"\s+", " ", str(organism or "")).strip()
    if cleaned_organism and (
        len(cleaned_organism) > 100 or not re.fullmatch(r"[A-Za-z0-9 .'-]+", cleaned_organism)
    ):
        raise GeoDatasetError("organism must be a scientific-name-style value or blank for any organism.")

    scope = str(assay_scope or "all").strip().casefold()
    if scope not in ASSAY_SCOPES:
        raise GeoDatasetError(f"assay_scope must be one of: {', '.join(ASSAY_SCOPES)}.")
    minimum = _bounded_integer(min_samples, "min_samples", 1, MAX_SAMPLES)
    limit = _bounded_integer(max_results, "max_results", 1, MAX_RESULTS)

    clauses = [f"({cleaned_query})", "GSE[ETYP]"]
    if cleaned_organism:
        escaped_organism = cleaned_organism.replace('"', "")
        clauses.append(f'"{escaped_organism}"[ORGN]')
    if ASSAY_SCOPES[scope]["query"]:
        clauses.append(f"({ASSAY_SCOPES[scope]['query']})")
    clauses.append(f"{minimum}:{MAX_SAMPLES}[NSAM]")
    exact_query = " AND ".join(clauses)
    return {
        "query": cleaned_query,
        "exact_query": exact_query,
        "organism": cleaned_organism,
        "assay_scope": scope,
        "assay_label": ASSAY_SCOPES[scope]["label"],
        "min_samples": minimum,
        "max_results": limit,
        "sort": "NCBI GEO relevance",
        "search_url": f"https://www.ncbi.nlm.nih.gov/gds/?term={quote(exact_query, safe='')}",
    }


def preflight_geo_dataset_discovery(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_geo_dataset_inputs(**arguments)
    payload, api_url = _search(normalized, page_size=0)
    search = _search_result(payload)
    hit_count = _integer(search.get("count"))
    if hit_count == 0:
        raise GeoDatasetError("NCBI GEO returned no Series for the exact query and filters.")
    return {
        "ready": True,
        "source": "NCBI GEO",
        "source_url": GEO_SITE,
        **normalized,
        "hit_count": hit_count,
        "query_translation": str(search.get("querytranslation") or ""),
        "search_api_url": api_url,
        "warnings": [
            "NCBI relevance order is not a dataset-quality or fitness-for-purpose rating.",
            "GEO sample counts do not establish the number of independent biological replicates.",
        ],
        "summary": (
            f"NCBI GEO found {hit_count:,} Series; the approved run will map the first "
            f"{normalized['max_results']} by relevance."
        ),
    }


def search_geo_dataset_preview(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_geo_dataset_inputs(**arguments)
    normalized["max_results"] = min(normalized["max_results"], MAX_PREVIEW_RESULTS)
    return _discover(normalized, persisted=False)


def collect_geo_datasets(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_geo_dataset_inputs(**arguments)
    result = _discover(normalized, persisted=True)
    _persist_discovery(result)
    return result


def _discover(normalized: dict[str, Any], *, persisted: bool) -> dict[str, Any]:
    search_payload, search_api_url = _search(normalized, page_size=normalized["max_results"])
    search = _search_result(search_payload)
    hit_count = _integer(search.get("count"))
    ids = [str(value) for value in (search.get("idlist") or []) if str(value).strip()]
    if hit_count == 0 or not ids:
        raise GeoDatasetError("NCBI GEO returned no Series for the exact query and filters.")
    summary_payload, summary_api_url = _summarize(ids)
    return parse_geo_dataset_payload(
        search_payload,
        summary_payload,
        normalized,
        persisted=persisted,
        search_api_url=search_api_url,
        summary_api_url=summary_api_url,
    )


def parse_geo_dataset_payload(
    search_payload: dict[str, Any],
    summary_payload: dict[str, Any],
    normalized: dict[str, Any],
    *,
    persisted: bool,
    search_api_url: str = "",
    summary_api_url: str = "",
) -> dict[str, Any]:
    search = _search_result(search_payload)
    result_block = summary_payload.get("result") or {}
    if not isinstance(result_block, dict):
        raise GeoDatasetError("NCBI GEO returned an unexpected summary response.")
    ids = [str(value) for value in (search.get("idlist") or []) if str(value).strip()]
    datasets = []
    for uid in ids[: int(normalized["max_results"])]:
        raw = result_block.get(uid)
        if not isinstance(raw, dict):
            continue
        dataset = _normalize_dataset(raw, uid, len(datasets) + 1)
        if dataset:
            datasets.append(dataset)
    if not datasets:
        raise GeoDatasetError("NCBI GEO returned no usable Series metadata.")

    assay_counts = Counter(
        assay
        for dataset in datasets
        for assay in (dataset.get("dataset_types") or ["Unspecified"])
    )
    organism_counts = Counter(
        organism
        for dataset in datasets
        for organism in (dataset.get("organisms") or ["Unspecified"])
    )
    supplementary_counts = Counter(
        file_type
        for dataset in datasets
        for file_type in dataset.get("supplementary_file_types", [])
    )
    total_samples = sum(_integer(dataset.get("n_samples")) for dataset in datasets)
    supplementary_count = sum(bool(dataset.get("has_supplementary")) for dataset in datasets)
    publication_count = sum(bool(dataset.get("pubmed_ids")) for dataset in datasets)
    result = {
        "analysis_id": f"geo-datasets-{uuid.uuid4().hex[:12]}" if persisted else "geo-dataset-preview",
        "method": "NCBI GEO Series metadata discovery",
        "source": "NCBI GEO",
        "source_url": GEO_SITE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        **normalized,
        "hit_count": _integer(search.get("count")),
        "returned_count": len(datasets),
        "query_translation": str(search.get("querytranslation") or ""),
        "search_api_url": search_api_url,
        "summary_api_url": summary_api_url,
        "total_samples": total_samples,
        "supplementary_count": supplementary_count,
        "publication_count": publication_count,
        "assay_type_counts": _counter_rows(assay_counts),
        "organism_counts": _counter_rows(organism_counts),
        "supplementary_type_counts": _counter_rows(supplementary_counts),
        "datasets": datasets,
        "outputs": {},
        "caveats": [
            "GEO records contain submitter-provided metadata; inclusion does not establish dataset quality or fitness for the research question.",
            "NCBI relevance order is not a quality ranking, and this workflow does not create a custom dataset score.",
            "The GEO sample count is not necessarily the number of independent biological replicates; inspect study design, subjects, batches, and paired samples.",
            "Supplementary-file presence and extension do not establish that raw counts, normalized matrices, or complete annotations are analysis-ready.",
            "SuperSeries, SubSeries, reused controls, and overlapping cohorts can duplicate biological evidence across records.",
            "This discovery step maps metadata only; it does not download or analyze expression data.",
        ],
    }
    result["summary"] = (
        f"Mapped {len(datasets)} of {result['hit_count']:,} GEO Series for '{normalized['query']}'; "
        f"{supplementary_count} report supplementary files and {publication_count} link publications."
    )
    return result


def _normalize_dataset(raw: dict[str, Any], uid: str, rank: int) -> dict[str, Any] | None:
    accession = str(raw.get("accession") or "").strip().upper()
    if not re.fullmatch(r"GSE\d+", accession):
        return None
    title = _clean_text(raw.get("title"))
    if not title:
        return None
    samples = raw.get("samples") or []
    if not isinstance(samples, list):
        samples = []
    sample_examples = []
    for sample in samples[:MAX_SAMPLE_EXAMPLES]:
        if not isinstance(sample, dict):
            continue
        sample_examples.append(
            {
                "accession": str(sample.get("accession") or "").strip().upper(),
                "title": _clean_text(sample.get("title")),
            }
        )
    organisms = _split_values(raw.get("taxon"))
    dataset_types = _split_values(raw.get("gdstype"))
    supplementary_types = _split_values(raw.get("suppfile"))
    platforms = []
    for value in re.findall(r"(?:GPL)?\d+", str(raw.get("gpl") or ""), re.I):
        accession_value = value.upper()
        if not accession_value.startswith("GPL"):
            accession_value = f"GPL{accession_value}"
        if accession_value not in platforms:
            platforms.append(accession_value)
    pubmed_ids = list(dict.fromkeys(re.findall(r"\d+", _string_value(raw.get("pubmedids")))))
    download_url = _https_ftp_url(str(raw.get("ftplink") or ""))
    geo2r_available = _truthy_source_value(raw.get("geo2r"))
    summary = _clean_text(raw.get("summary"))
    if len(summary) > MAX_SUMMARY_CHARS:
        summary = summary[:MAX_SUMMARY_CHARS].rsplit(" ", 1)[0] + "..."
    n_samples = _integer(raw.get("n_samples")) or len(samples)
    return {
        "rank": rank,
        "uid": uid,
        "accession": accession,
        "title": title,
        "summary": summary,
        "organisms": organisms,
        "dataset_types": dataset_types,
        "n_samples": n_samples,
        "platform_accessions": platforms,
        "release_date": str(raw.get("pdat") or ""),
        "supplementary_file_types": supplementary_types,
        "has_supplementary": bool(supplementary_types or download_url),
        "geo2r_available": geo2r_available,
        "pubmed_ids": pubmed_ids,
        "bioproject": str(raw.get("bioproject") or "").strip(),
        "sample_examples": sample_examples,
        "url": f"{GEO_RECORD}?acc={accession}",
        "download_url": download_url,
        "selection_basis": "Matched the exact GEO query and filters; retained in NCBI relevance order.",
        "analysis_handoff": _analysis_handoff(dataset_types),
    }


def _search(normalized: dict[str, Any], page_size: int) -> tuple[dict[str, Any], str]:
    parameters = {
        "db": "gds",
        "term": normalized["exact_query"],
        "retmode": "json",
        "retmax": max(0, min(int(page_size), MAX_RESULTS)),
        "sort": "relevance",
        "tool": "molemo_workbench",
    }
    url = f"{EUTILS_ROOT}/esearch.fcgi?{urlencode(parameters)}"
    try:
        payload = get_json(url)
    except ExternalDataError as exc:
        raise GeoDatasetError(str(exc)) from exc
    _search_result(payload)
    return payload, url


def _summarize(ids: list[str]) -> tuple[dict[str, Any], str]:
    parameters = {
        "db": "gds",
        "id": ",".join(ids[:MAX_RESULTS]),
        "retmode": "json",
        "version": "2.0",
        "tool": "molemo_workbench",
    }
    url = f"{EUTILS_ROOT}/esummary.fcgi?{urlencode(parameters)}"
    try:
        payload = get_json(url)
    except ExternalDataError as exc:
        raise GeoDatasetError(str(exc)) from exc
    if not isinstance(payload.get("result"), dict):
        raise GeoDatasetError("NCBI GEO returned an unexpected summary response.")
    return payload, url


def _search_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("esearchresult") or {}
    if not isinstance(result, dict) or "count" not in result or "idlist" not in result:
        raise GeoDatasetError("NCBI GEO returned an unexpected search response.")
    return result


def _persist_discovery(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "datasets": f"{relative_root}/datasets.tsv",
        "sample_examples": f"{relative_root}/sample_examples.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="geo-datasets-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_datasets(output / "datasets.tsv", result["datasets"])
        _write_sample_examples(output / "sample_examples.tsv", result["datasets"])
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "source": result["source"],
            "source_url": result["source_url"],
            "retrieved_at": result["retrieved_at"],
            "query": result["query"],
            "exact_query": result["exact_query"],
            "query_translation": result["query_translation"],
            "filters": {
                "organism": result["organism"],
                "assay_scope": result["assay_scope"],
                "min_samples": result["min_samples"],
                "max_results": result["max_results"],
                "sort": result["sort"],
            },
            "api": {
                "database": "gds",
                "search": result["search_api_url"],
                "summary": result["summary_api_url"],
                "authentication": "public NCBI E-utilities; no API key supplied",
            },
            "files": ["datasets.tsv", "sample_examples.tsv", "report.json", "run_manifest.json", "summary.md"],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise GeoDatasetError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_datasets(path: Path, datasets: list[dict[str, Any]]) -> None:
    fields = [
        "rank", "uid", "accession", "title", "organisms", "dataset_types", "n_samples",
        "platform_accessions", "release_date", "supplementary_file_types", "geo2r_available",
        "pubmed_ids", "bioproject", "url", "download_url", "analysis_handoff", "summary",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for dataset in datasets:
            row = {key: dataset.get(key) for key in fields}
            for key in ("organisms", "dataset_types", "platform_accessions", "supplementary_file_types", "pubmed_ids"):
                row[key] = "; ".join(dataset.get(key) or [])
            writer.writerow(row)


def _write_sample_examples(path: Path, datasets: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset_accession", "sample_accession", "sample_title"],
            delimiter="\t",
        )
        writer.writeheader()
        for dataset in datasets:
            for sample in dataset.get("sample_examples", []):
                writer.writerow(
                    {
                        "dataset_accession": dataset["accession"],
                        "sample_accession": sample.get("accession"),
                        "sample_title": sample.get("title"),
                    }
                )


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# GEO Series discovery",
        "",
        f"Query: `{result['exact_query']}`",
        "",
        result["summary"],
        "",
        "| Rank | Series | Samples | Assay | Study |",
        "| ---: | --- | ---: | --- | --- |",
    ]
    for dataset in result["datasets"]:
        title = dataset["title"].replace("|", "\\|")
        assays = "; ".join(dataset["dataset_types"]).replace("|", "\\|")
        lines.append(
            f"| {dataset['rank']} | [{dataset['accession']}]({dataset['url']}) | "
            f"{dataset['n_samples']} | {assays} | {title} |"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _counter_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"label": label, "count": count}
        for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _analysis_handoff(dataset_types: list[str]) -> str:
    joined = " ".join(dataset_types).casefold()
    if "high throughput sequencing" in joined:
        return "Inspect supplementary matrices, sample design, and raw-data links before selecting bulk or single-cell local analysis."
    if "array" in joined:
        return "Inspect platform annotation, normalization state, and sample design before choosing an array-compatible analysis."
    return "Inspect data files, assay processing, sample design, and biological replication before local analysis."


def _split_values(value: Any) -> list[str]:
    text = _string_value(value)
    values = []
    for item in re.split(r"\s*;\s*|\s*\|\s*|\s*,\s*(?=[A-Z])", text):
        cleaned = _clean_text(item)
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return values


def _string_value(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value or "")


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", _string_value(value)).strip()


def _https_ftp_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if parsed.hostname != "ftp.ncbi.nlm.nih.gov" or parsed.scheme not in {"ftp", "https"}:
        return ""
    return f"https://ftp.ncbi.nlm.nih.gov{parsed.path.rstrip('/')}/"


def _truthy_source_value(value: Any) -> bool:
    return str(value or "").strip().casefold() not in {"", "0", "false", "n", "no", "none"}


def _bounded_integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise GeoDatasetError(f"{label} must be an integer.") from exc
    if not minimum <= number <= maximum:
        raise GeoDatasetError(f"{label} must be between {minimum} and {maximum}.")
    return number


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
