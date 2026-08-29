"""Human gene-set pathway enrichment and functional association review."""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from bio_clients import ExternalDataError, post_form_json_array, post_text_json
from workspace_utils import WORKSPACE_ROOT


REACTOME_ANALYSIS_URL = "https://reactome.org/AnalysisService/identifiers/projection"
REACTOME_DETAIL_URL = "https://reactome.org/content/detail"
STRING_API_ROOT = "https://version-12-0.string-db.org/api/json"
STRING_WEB_ROOT = "https://string-db.org/cgi/network"
STRING_VERSION = "12.0"
HUMAN_TAXON_ID = 9606
MAX_TERMS = 50
TERM_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
MAPPING_CACHE_SECONDS = 5 * 60
_MAPPING_CACHE: dict[tuple[str, ...], tuple[float, list[dict[str, Any]]]] = {}
_MAPPING_CACHE_LOCK = threading.Lock()


class FunctionalAnalysisError(ValueError):
    """Raised when gene-set inputs or public database responses are invalid."""


def parse_gene_terms(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw_terms = [str(item).strip() for item in value]
    else:
        text = str(value or "").strip()
        raw_terms = re.split(r"[,;，、\n\r\t]+", text)
        if len(raw_terms) == 1 and " " in text:
            raw_terms = text.split()
    terms = [term.strip() for term in raw_terms if term.strip()]
    if len(terms) < 2:
        raise FunctionalAnalysisError("At least two gene or protein identifiers are required.")
    if len(terms) > MAX_TERMS:
        raise FunctionalAnalysisError(f"Gene-set analysis is limited to {MAX_TERMS} identifiers.")
    for term in terms:
        if not TERM_PATTERN.fullmatch(term):
            raise FunctionalAnalysisError(f"Unsupported gene or protein identifier: {term}")
    folded = [term.casefold() for term in terms]
    if len(folded) != len(set(folded)):
        raise FunctionalAnalysisError("Gene or protein identifiers must be unique.")
    return terms


def normalize_parameters(
    *,
    required_score: Any = 400,
    fdr_threshold: Any = 0.05,
    max_terms: Any = 20,
    include_disease_pathways: Any = False,
) -> dict[str, Any]:
    try:
        score = int(required_score)
    except (TypeError, ValueError) as exc:
        raise FunctionalAnalysisError("STRING required score must be an integer.") from exc
    if not 150 <= score <= 900:
        raise FunctionalAnalysisError("STRING required score must be between 150 and 900.")
    try:
        fdr = float(fdr_threshold)
    except (TypeError, ValueError) as exc:
        raise FunctionalAnalysisError("FDR threshold must be numeric.") from exc
    if not 0.0001 <= fdr <= 0.25:
        raise FunctionalAnalysisError("FDR threshold must be between 0.0001 and 0.25.")
    try:
        limit = int(max_terms)
    except (TypeError, ValueError) as exc:
        raise FunctionalAnalysisError("Maximum reported terms must be an integer.") from exc
    if not 5 <= limit <= 50:
        raise FunctionalAnalysisError("Maximum reported terms must be between 5 and 50.")
    include_disease = (
        str(include_disease_pathways).strip().lower() in {"1", "true", "yes", "on"}
        if isinstance(include_disease_pathways, str)
        else bool(include_disease_pathways)
    )
    return {
        "required_score": score,
        "fdr_threshold": round(fdr, 6),
        "max_terms": limit,
        "include_disease_pathways": include_disease,
    }


def preflight_functional_analysis(
    genes: str | list[str],
    required_score: Any = 400,
    fdr_threshold: Any = 0.05,
    max_terms: Any = 20,
    include_disease_pathways: Any = False,
) -> dict[str, Any]:
    terms = parse_gene_terms(genes)
    parameters = normalize_parameters(
        required_score=required_score,
        fdr_threshold=fdr_threshold,
        max_terms=max_terms,
        include_disease_pathways=include_disease_pathways,
    )
    mappings = _map_string_identifiers(terms)
    mapped_ids = list(dict.fromkeys(item["string_id"] for item in mappings))
    if len(mapped_ids) < 2:
        raise FunctionalAnalysisError(
            "STRING must map at least two unique human proteins before network analysis can run."
        )
    mapped_queries = {str(item["query"]).casefold() for item in mappings}
    unmapped = [term for term in terms if term.casefold() not in mapped_queries]
    warnings = [
        "This workflow currently uses Homo sapiens (NCBI taxon 9606); review every identifier mapping before approval.",
        "Reactome overrepresentation depends on list construction and reference coverage; enrichment is not causal evidence.",
        "STRING functional associations are not necessarily direct physical interactions.",
    ]
    if unmapped:
        warnings.insert(
            1,
            f"STRING did not map {len(unmapped)} input identifier(s): {', '.join(unmapped)}. Reactome will still receive the full list.",
        )
    return {
        "ready": True,
        "organism": {"name": "Homo sapiens", "taxon_id": HUMAN_TAXON_ID},
        "input_terms": terms,
        "mappings": mappings,
        "mapped_count": len(mapped_ids),
        "unmapped_terms": unmapped,
        "parameters": parameters,
        "sources": [
            {"name": "Reactome Analysis Service", "url": "https://reactome.org/dev/analysis/"},
            {"name": f"STRING v{STRING_VERSION}", "url": "https://string-db.org/help/api/"},
        ],
        "warnings": warnings,
        "summary": (
            f"Mapped {len(mapped_ids)} of {len(terms)} human identifiers to unique STRING proteins; "
            "Reactome will analyze the complete input list."
        ),
    }


def run_functional_analysis(
    genes: str | list[str],
    required_score: Any = 400,
    fdr_threshold: Any = 0.05,
    max_terms: Any = 20,
    include_disease_pathways: Any = False,
) -> dict[str, Any]:
    preflight = preflight_functional_analysis(
        genes=genes,
        required_score=required_score,
        fdr_threshold=fdr_threshold,
        max_terms=max_terms,
        include_disease_pathways=include_disease_pathways,
    )
    parameters = preflight["parameters"]
    string_ids = list(dict.fromkeys(item["string_id"] for item in preflight["mappings"]))
    reactome_payload = _reactome_analysis(
        preflight["input_terms"], parameters["include_disease_pathways"]
    )
    string_warnings = []
    network_payload, network_available = _optional_string_call(
        "network",
        {
            "identifiers": "\r".join(string_ids),
            "species": HUMAN_TAXON_ID,
            "required_score": parameters["required_score"],
            "network_type": "functional",
            "add_nodes": 0,
        },
        string_warnings,
    )
    ppi_payload, ppi_available = _optional_string_call(
        "ppi_enrichment",
        {"identifiers": "\r".join(string_ids), "species": HUMAN_TAXON_ID},
        string_warnings,
    )
    enrichment_payload, enrichment_available = _optional_string_call(
        "enrichment",
        {"identifiers": "\r".join(string_ids), "species": HUMAN_TAXON_ID},
        string_warnings,
    )

    reactome = parse_reactome_payload(reactome_payload, parameters)
    nodes, edges = parse_string_network(network_payload, preflight["mappings"])
    ppi = parse_string_ppi_enrichment(ppi_payload)
    enrichment = parse_string_enrichment(enrichment_payload, parameters)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    analysis_id = f"functional-analysis-{uuid.uuid4().hex[:12]}"
    result = {
        "analysis_id": analysis_id,
        "method": "Reactome overrepresentation and STRING functional association analysis",
        "retrieved_at": retrieved_at,
        "organism": preflight["organism"],
        "input_terms": preflight["input_terms"],
        "mappings": preflight["mappings"],
        "mapped_count": preflight["mapped_count"],
        "unmapped_terms": preflight["unmapped_terms"],
        "parameters": parameters,
        "reactome": reactome,
        "string_enrichment": {**enrichment, "available": enrichment_available},
        "network": {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "available": network_available,
            "required_score": parameters["required_score"],
            "network_type": "functional",
            "source_url": _string_network_url(preflight["mappings"]),
        },
        "ppi_enrichment": {**ppi, "available": ppi_available},
        "sources": preflight["sources"],
        "source_warnings": string_warnings,
        "caveats": [
            *string_warnings,
            "Overrepresentation results depend on how the input list and reference universe were constructed; they do not establish mechanism or causality.",
            "FDR is a multiple-testing correction, not the probability that a pathway or term is true.",
            "STRING edges are functional associations assembled from multiple evidence channels and are not necessarily direct physical interactions.",
            "Database and literature coverage can bias results toward well-studied genes and pathways.",
            "Genes in a set are not biological replicates; do not use enrichment rows as replicate-level statistical evidence.",
        ],
        "outputs": {},
    }
    significant_pathways = reactome["significant_count"]
    significant_terms = enrichment["significant_count"]
    enrichment_text = (
        f"and {significant_terms} STRING terms at FDR <= {parameters['fdr_threshold']}"
        if enrichment_available
        else "while STRING enrichment was unavailable"
    )
    network_text = (
        f"The functional network contains {len(nodes)} proteins and {len(edges)} associations."
        if network_available
        else "The STRING network endpoint was unavailable; mapped proteins were retained without edges."
    )
    result["summary"] = (
        f"Mapped {result['mapped_count']} of {len(result['input_terms'])} inputs; "
        f"found {significant_pathways} Reactome pathways {enrichment_text}. {network_text}"
    )
    _persist_analysis(result)
    return result


def parse_reactome_payload(payload: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    rows = []
    threshold = float(parameters["fdr_threshold"])
    include_disease = bool(parameters["include_disease_pathways"])
    for raw in payload.get("pathways") or []:
        if not isinstance(raw, dict) or not raw.get("stId"):
            continue
        in_disease = bool(raw.get("inDisease"))
        if in_disease and not include_disease:
            continue
        species = raw.get("species") or {}
        if str(species.get("taxId") or "") != str(HUMAN_TAXON_ID):
            continue
        entities = raw.get("entities") or {}
        fdr = _number(entities.get("fdr"), default=1.0)
        rows.append(
            {
                "id": str(raw["stId"]),
                "name": str(raw.get("name") or raw["stId"]),
                "entities_found": _integer(entities.get("found")),
                "entities_total": _integer(entities.get("total")),
                "p_value": _number(entities.get("pValue"), default=1.0),
                "fdr": fdr,
                "in_disease": in_disease,
                "url": f"{REACTOME_DETAIL_URL}/{quote(str(raw['stId']), safe='-')}",
            }
        )
    rows.sort(key=lambda item: (item["fdr"], item["p_value"], item["name"]))
    significant = [item for item in rows if item["fdr"] <= threshold]
    displayed = significant[: int(parameters["max_terms"])]
    if not displayed:
        displayed = rows[: min(5, int(parameters["max_terms"]))]
    summary = payload.get("summary") or {}
    return {
        "token": str(summary.get("token") or ""),
        "analysis_type": str(summary.get("type") or "OVERREPRESENTATION"),
        "pathways_found": _integer(payload.get("pathwaysFound")),
        "identifiers_not_found": _integer(payload.get("identifiersNotFound")),
        "significant_count": len(significant),
        "pathways": displayed,
        "source_url": "https://reactome.org/PathwayBrowser/",
    }


def parse_string_network(
    payload: list[Any], mappings: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes_by_id = {
        item["string_id"]: {
            "id": item["string_id"],
            "name": item["preferred_name"],
            "query": item["query"],
            "annotation": item.get("annotation") or "",
            "degree": 0,
        }
        for item in mappings
    }
    edges = []
    seen = set()
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        source = str(raw.get("stringId_A") or "")
        target = str(raw.get("stringId_B") or "")
        if not source or not target or source == target:
            continue
        key = tuple(sorted((source, target)))
        if key in seen:
            continue
        seen.add(key)
        for identifier, preferred_key in ((source, "preferredName_A"), (target, "preferredName_B")):
            nodes_by_id.setdefault(
                identifier,
                {
                    "id": identifier,
                    "name": str(raw.get(preferred_key) or identifier),
                    "query": "",
                    "annotation": "",
                    "degree": 0,
                },
            )
            nodes_by_id[identifier]["degree"] += 1
        edges.append(
            {
                "source": source,
                "target": target,
                "source_name": str(raw.get("preferredName_A") or nodes_by_id[source]["name"]),
                "target_name": str(raw.get("preferredName_B") or nodes_by_id[target]["name"]),
                "score": _number(raw.get("score")),
                "evidence": {
                    "neighborhood": _number(raw.get("nscore")),
                    "fusion": _number(raw.get("fscore")),
                    "experiments": _number(raw.get("escore")),
                    "databases": _number(raw.get("dscore")),
                    "textmining": _number(raw.get("tscore")),
                },
            }
        )
    edges.sort(key=lambda item: (-item["score"], item["source_name"], item["target_name"]))
    nodes = sorted(nodes_by_id.values(), key=lambda item: (-item["degree"], item["name"]))
    return nodes, edges


def parse_string_ppi_enrichment(payload: list[Any]) -> dict[str, Any]:
    raw = next((item for item in payload if isinstance(item, dict)), {})
    return {
        "nodes": _integer(raw.get("number_of_nodes")),
        "edges": _integer(raw.get("number_of_edges")),
        "expected_edges": _integer(raw.get("expected_number_of_edges")),
        "average_degree": _number(raw.get("average_node_degree")),
        "clustering_coefficient": _number(raw.get("local_clustering_coefficient")),
        "p_value": _number(raw.get("p_value"), default=1.0),
    }


def parse_string_enrichment(payload: list[Any], parameters: dict[str, Any]) -> dict[str, Any]:
    rows = []
    threshold = float(parameters["fdr_threshold"])
    for raw in payload:
        if not isinstance(raw, dict) or not raw.get("term"):
            continue
        rows.append(
            {
                "category": str(raw.get("category") or ""),
                "term": str(raw["term"]),
                "description": str(raw.get("description") or raw["term"]),
                "genes": [str(item) for item in raw.get("preferredNames") or []],
                "input_gene_count": _integer(raw.get("number_of_genes")),
                "background_gene_count": _integer(raw.get("number_of_genes_in_background")),
                "p_value": _number(raw.get("p_value"), default=1.0),
                "fdr": _number(raw.get("fdr"), default=1.0),
            }
        )
    rows.sort(key=lambda item: (item["fdr"], item["p_value"], item["description"]))
    significant = [item for item in rows if item["fdr"] <= threshold]
    displayed = significant[: int(parameters["max_terms"])]
    if not displayed:
        displayed = rows[: min(5, int(parameters["max_terms"]))]
    return {"significant_count": len(significant), "terms": displayed}


def _map_string_identifiers(terms: list[str]) -> list[dict[str, Any]]:
    cache_key = tuple(terms)
    now = time.monotonic()
    with _MAPPING_CACHE_LOCK:
        cached = _MAPPING_CACHE.get(cache_key)
        if cached and now - cached[0] <= MAPPING_CACHE_SECONDS:
            return [dict(item) for item in cached[1]]
    payload = _string_call(
        "get_string_ids",
        {
            "identifiers": "\r".join(terms),
            "species": HUMAN_TAXON_ID,
            "limit": 1,
        },
    )
    by_index: dict[int, dict[str, Any]] = {}
    for raw in payload:
        if not isinstance(raw, dict) or not raw.get("stringId"):
            continue
        index = _integer(raw.get("queryIndex"), default=-1)
        if 0 <= index < len(terms) and index not in by_index:
            by_index[index] = {
                "query": terms[index],
                "string_id": str(raw["stringId"]),
                "preferred_name": str(raw.get("preferredName") or terms[index]),
                "annotation": str(raw.get("annotation") or ""),
            }
    mappings = [by_index[index] for index in sorted(by_index)]
    with _MAPPING_CACHE_LOCK:
        if len(_MAPPING_CACHE) >= 32:
            oldest_key = min(_MAPPING_CACHE, key=lambda key: _MAPPING_CACHE[key][0])
            _MAPPING_CACHE.pop(oldest_key, None)
        _MAPPING_CACHE[cache_key] = (now, [dict(item) for item in mappings])
    return mappings


def _reactome_analysis(terms: list[str], include_disease: bool) -> dict[str, Any]:
    url = (
        f"{REACTOME_ANALYSIS_URL}?pageSize=1000&page=1&includeDisease="
        f"{'true' if include_disease else 'false'}"
    )
    try:
        return post_text_json(url, "#Genes\n" + "\n".join(terms))
    except ExternalDataError as exc:
        raise FunctionalAnalysisError(str(exc)) from exc


def _string_call(endpoint: str, fields: dict[str, Any]) -> list[Any]:
    request_fields = {**fields, "caller_identity": "Molemo_WorkBench"}
    try:
        return post_form_json_array(f"{STRING_API_ROOT}/{endpoint}", request_fields)
    except ExternalDataError as exc:
        raise FunctionalAnalysisError(str(exc)) from exc


def _optional_string_call(
    endpoint: str,
    fields: dict[str, Any],
    warnings: list[str],
) -> tuple[list[Any], bool]:
    try:
        return _string_call(endpoint, fields), True
    except FunctionalAnalysisError as exc:
        warnings.append(f"STRING {endpoint} was unavailable during this run: {exc}")
        return [], False


def _string_network_url(mappings: list[dict[str, Any]]) -> str:
    names = "\r".join(item["preferred_name"] for item in mappings)
    return f"{STRING_WEB_ROOT}?identifiers={quote(names, safe='')}&species={HUMAN_TAXON_ID}"


def _persist_analysis(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    files = [
        "reactome_pathways.tsv",
        "string_enrichment.tsv",
        "string_nodes.tsv",
        "string_edges.tsv",
        "report.json",
        "run_manifest.json",
        "artifact_index.json",
        "summary.md",
    ]
    result["output_root"] = relative_root
    result["outputs"] = {
        "reactome_pathways": f"{relative_root}/reactome_pathways.tsv",
        "string_enrichment": f"{relative_root}/string_enrichment.tsv",
        "string_nodes": f"{relative_root}/string_nodes.tsv",
        "string_edges": f"{relative_root}/string_edges.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "artifact_index": f"{relative_root}/artifact_index.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="functional-analysis-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_tsv(output / "reactome_pathways.tsv", result["reactome"]["pathways"])
        _write_tsv(output / "string_enrichment.tsv", result["string_enrichment"]["terms"], lists=True)
        _write_tsv(output / "string_nodes.tsv", result["network"]["nodes"])
        _write_tsv(output / "string_edges.tsv", result["network"]["edges"], objects=True)
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "retrieved_at": result["retrieved_at"],
            "organism": result["organism"],
            "input_terms": result["input_terms"],
            "mapped_string_ids": [item["string_id"] for item in result["mappings"]],
            "parameters": result["parameters"],
            "sources": result["sources"],
            "api_versions": {"STRING": STRING_VERSION, "Reactome": "Analysis Service"},
            "files": files,
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        artifact_index = {
            "analysis_id": result["analysis_id"],
            "artifact_type": "functional-analysis",
            "primary": "report.json",
            "tables": files[:4],
            "summary": "summary.md",
        }
        (output / "artifact_index.json").write_text(
            json.dumps(artifact_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise FunctionalAnalysisError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_tsv(path: Path, rows: list[dict[str, Any]], *, lists: bool = False, objects: bool = False) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for raw in rows:
            row = dict(raw)
            if lists:
                row = {key: "; ".join(value) if isinstance(value, list) else value for key, value in row.items()}
            if objects:
                row = {
                    key: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    if isinstance(value, dict)
                    else value
                    for key, value in row.items()
                }
            writer.writerow(row)


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Human gene-set functional analysis",
        "",
        result["summary"],
        "",
        "## Reactome pathways",
        "",
        "| Pathway | Entities found | FDR |",
        "| --- | ---: | ---: |",
    ]
    for pathway in result["reactome"]["pathways"]:
        lines.append(f"| {pathway['name']} | {pathway['entities_found']} | {pathway['fdr']:.3g} |")
    lines.extend(["", "## STRING functional terms", "", "| Category | Term | Genes | FDR |", "| --- | --- | ---: | ---: |"])
    for term in result["string_enrichment"]["terms"]:
        lines.append(
            f"| {term['category']} | {term['description']} | {term['input_gene_count']} | {term['fdr']:.3g} |"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.extend(["", "Sources: Reactome Analysis Service; STRING v12.0", ""])
    return "\n".join(lines)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _integer(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
