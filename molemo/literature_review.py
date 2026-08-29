"""Bounded Europe PMC search and evidence-map persistence."""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from .bio_clients import ExternalDataError, get_json
from .workspace_utils import WORKSPACE_ROOT


EUROPE_PMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPE_PMC_SITE = "https://europepmc.org"
MAX_QUERY_CHARS = 300
MAX_RESULTS = 25
MAX_ABSTRACT_CHARS = 2400
MIN_YEAR = 1900


class LiteratureReviewError(ValueError):
    """Raised when a literature review query or response is invalid."""


def normalize_literature_inputs(
    query: str,
    start_year: int | str | None = None,
    end_year: int | str | None = None,
    max_results: int | str = 15,
    include_preprints: bool | str = False,
    require_abstract: bool | str = True,
) -> dict[str, Any]:
    cleaned_query = re.sub(r"\s+", " ", str(query or "")).strip()
    if not cleaned_query or len(cleaned_query) > MAX_QUERY_CHARS:
        raise LiteratureReviewError(f"Literature query must contain between 1 and {MAX_QUERY_CHARS} characters.")
    if any(ord(char) < 32 for char in cleaned_query):
        raise LiteratureReviewError("Literature query contains unsupported control characters.")
    if re.search(r"\bsort_(?:date|cited)\s*:", cleaned_query, re.I):
        raise LiteratureReviewError("Sort directives are not accepted; reviews preserve Europe PMC relevance order.")
    current_year = datetime.now(timezone.utc).year
    start = _optional_year(start_year, "start_year", current_year)
    end = _optional_year(end_year, "end_year", current_year)
    if start and end and start > end:
        raise LiteratureReviewError("start_year must be less than or equal to end_year.")
    try:
        bounded_results = int(max_results)
    except (TypeError, ValueError) as exc:
        raise LiteratureReviewError("max_results must be an integer.") from exc
    if not 1 <= bounded_results <= MAX_RESULTS:
        raise LiteratureReviewError(f"max_results must be between 1 and {MAX_RESULTS}.")
    include_preprints_bool = _boolean(include_preprints)
    require_abstract_bool = _boolean(require_abstract)
    exact_query = _build_query(
        cleaned_query,
        start,
        end,
        include_preprints_bool,
        require_abstract_bool,
    )
    return {
        "query": cleaned_query,
        "exact_query": exact_query,
        "start_year": start,
        "end_year": end,
        "max_results": bounded_results,
        "include_preprints": include_preprints_bool,
        "require_abstract": require_abstract_bool,
        "sort": "Europe PMC relevance",
        "search_url": f"{EUROPE_PMC_SITE}/search?query={quote(exact_query, safe='')}",
    }


def preflight_literature_review(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_literature_inputs(**arguments)
    payload = _search(normalized, page_size=1)
    hit_count = _integer(payload.get("hitCount"))
    if hit_count == 0:
        raise LiteratureReviewError("Europe PMC returned no publications for the approved query and filters.")
    warnings = [
        "Europe PMC relevance ordering is not a study-quality rating.",
        "The review uses publication metadata and abstracts; it is not a full-text systematic review.",
    ]
    return {
        "ready": True,
        "source": "Europe PMC",
        "source_url": "https://europepmc.org/",
        **normalized,
        "hit_count": hit_count,
        "warnings": warnings,
        "summary": f"Europe PMC found {hit_count:,} records; the approved run will collect the first {normalized['max_results']} by relevance.",
    }


def search_literature_preview(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_literature_inputs(**arguments)
    normalized["max_results"] = min(normalized["max_results"], 10)
    payload = _search(normalized, page_size=normalized["max_results"])
    return parse_literature_payload(payload, normalized, persisted=False)


def collect_literature_review(**arguments: Any) -> dict[str, Any]:
    preflight = preflight_literature_review(**arguments)
    normalized = {key: preflight[key] for key in (
        "query",
        "exact_query",
        "start_year",
        "end_year",
        "max_results",
        "include_preprints",
        "require_abstract",
        "sort",
        "search_url",
    )}
    payload = _search(normalized, page_size=normalized["max_results"])
    result = parse_literature_payload(payload, normalized, persisted=True)
    _persist_review(result)
    return result


def parse_literature_payload(
    payload: dict[str, Any],
    normalized: dict[str, Any],
    *,
    persisted: bool,
) -> dict[str, Any]:
    raw_results = ((payload.get("resultList") or {}).get("result")) or []
    if not isinstance(raw_results, list):
        raise LiteratureReviewError("Europe PMC returned an unexpected result list.")
    papers = []
    for rank, raw in enumerate(raw_results[: int(normalized["max_results"])], 1):
        if not isinstance(raw, dict) or not raw.get("id") or not raw.get("title"):
            continue
        papers.append(_normalize_paper(raw, rank))
    if not papers:
        raise LiteratureReviewError("Europe PMC returned no usable publication metadata.")

    type_counts = Counter(item["study_type"] for item in papers)
    year_counts = Counter(str(item["year"]) for item in papers if item["year"])
    language_counts = Counter(item["language"] for item in papers if item["language"])
    abstracts = sum(1 for item in papers if item["abstract"])
    open_access = sum(1 for item in papers if item["open_access"])
    preprints = sum(1 for item in papers if item["preprint"])
    result = {
        "analysis_id": f"literature-review-{uuid.uuid4().hex[:12]}" if persisted else "literature-preview",
        "method": "Europe PMC metadata and abstract evidence map",
        "source": "Europe PMC",
        "source_url": "https://europepmc.org/",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        **normalized,
        "hit_count": _integer(payload.get("hitCount")),
        "returned_count": len(papers),
        "abstract_count": abstracts,
        "open_access_count": open_access,
        "preprint_count": preprints,
        "study_type_counts": [
            {"label": label, "count": count}
            for label, count in sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "year_counts": [
            {"year": int(year), "count": count}
            for year, count in sorted(year_counts.items(), reverse=True)
        ],
        "language_counts": dict(sorted(language_counts.items())),
        "papers": papers,
        "outputs": {},
        "caveats": [
            "Search results are ordered by Europe PMC relevance, not by study quality or certainty.",
            "Citation counts are shown only as bibliographic context and are not used to rank or grade evidence.",
            "This evidence map uses metadata and abstracts; claims requiring critical appraisal must be checked against full text and study methods.",
            "The approved query, date window, abstract requirement, preprint policy, and result limit constrain recall and precision.",
        ],
    }
    result["summary"] = (
        f"Mapped {len(papers)} of {result['hit_count']:,} Europe PMC records for '{normalized['query']}'; "
        f"{abstracts} include abstracts, {open_access} are marked open access, and {preprints} are preprints."
    )
    return result


def _normalize_paper(raw: dict[str, Any], rank: int) -> dict[str, Any]:
    source = str(raw.get("source") or "").upper()
    identifier = str(raw.get("id") or "")
    pmid = str(raw.get("pmid") or "")
    pmcid = str(raw.get("pmcid") or "")
    doi = str(raw.get("doi") or "")
    pub_types = [
        str(item).strip()
        for item in ((raw.get("pubTypeList") or {}).get("pubType") or [])
        if str(item).strip()
    ]
    abstract = _clean_markup(str(raw.get("abstractText") or ""))
    if len(abstract) > MAX_ABSTRACT_CHARS:
        abstract = abstract[:MAX_ABSTRACT_CHARS].rsplit(" ", 1)[0] + "..."
    keywords = [
        str(item).strip()
        for item in ((raw.get("keywordList") or {}).get("keyword") or [])
        if str(item).strip()
    ][:10]
    journal = str((((raw.get("journalInfo") or {}).get("journal") or {}).get("title")) or "")
    year = _integer(raw.get("pubYear") or ((raw.get("journalInfo") or {}).get("yearOfPublication")))
    preprint = source == "PPR" or any("preprint" in item.casefold() for item in pub_types)
    return {
        "rank": rank,
        "id": identifier,
        "source_code": source,
        "pmid": pmid or None,
        "pmcid": pmcid or None,
        "doi": doi or None,
        "title": _clean_markup(str(raw.get("title") or "")),
        "authors": str(raw.get("authorString") or ""),
        "journal": journal,
        "year": year or None,
        "first_publication_date": str(raw.get("firstPublicationDate") or ""),
        "publication_status": str(raw.get("publicationStatus") or ""),
        "language": str(raw.get("language") or ""),
        "publication_types": pub_types,
        "study_type": _study_type(pub_types, preprint),
        "abstract": abstract,
        "keywords": keywords,
        "open_access": str(raw.get("isOpenAccess") or "N").upper() == "Y",
        "in_pmc": str(raw.get("inPMC") or "N").upper() == "Y",
        "has_pdf": str(raw.get("hasPDF") or "N").upper() == "Y",
        "preprint": preprint,
        "cited_by_count": _integer(raw.get("citedByCount")),
        "selection_basis": "Matched the approved Europe PMC query and filters; retained in source relevance order.",
        "url": f"{EUROPE_PMC_SITE}/article/{source}/{quote(identifier, safe='')}",
    }


def _search(normalized: dict[str, Any], page_size: int) -> dict[str, Any]:
    parameters = {
        "query": normalized["exact_query"],
        "format": "json",
        "pageSize": max(1, min(int(page_size), MAX_RESULTS)),
        "resultType": "core",
        "synonym": "false",
    }
    url = f"{EUROPE_PMC_API}?{urlencode(parameters)}"
    try:
        payload = get_json(url)
    except ExternalDataError as exc:
        raise LiteratureReviewError(str(exc)) from exc
    if "hitCount" not in payload or "resultList" not in payload:
        raise LiteratureReviewError("Europe PMC returned an unexpected response shape.")
    return payload


def _build_query(
    query: str,
    start_year: int | None,
    end_year: int | None,
    include_preprints: bool,
    require_abstract: bool,
) -> str:
    clauses = [f"({query})"]
    if start_year or end_year:
        start = start_year or MIN_YEAR
        end = end_year or datetime.now(timezone.utc).year
        clauses.append(f"FIRST_PDATE:[{start}-01-01 TO {end}-12-31]")
    if require_abstract:
        clauses.append("HAS_ABSTRACT:Y")
    if not include_preprints:
        clauses.append("NOT SRC:PPR")
    return " AND ".join(clauses)


def _study_type(publication_types: list[str], preprint: bool) -> str:
    if preprint:
        return "Preprint"
    joined = " ".join(publication_types).casefold()
    if "meta-analysis" in joined or "systematic review" in joined:
        return "Systematic review / meta-analysis"
    if "randomized controlled trial" in joined:
        return "Randomized controlled trial"
    if "clinical trial" in joined:
        return "Clinical trial"
    if "review" in joined:
        return "Review"
    if "journal article" in joined or "research-article" in joined:
        return "Research article"
    return publication_types[0] if publication_types else "Other"


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "papers": f"{relative_root}/papers.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="literature-review-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_papers(output / "papers.tsv", result["papers"])
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
            "filters": {
                "start_year": result["start_year"],
                "end_year": result["end_year"],
                "include_preprints": result["include_preprints"],
                "require_abstract": result["require_abstract"],
                "max_results": result["max_results"],
            },
            "files": ["papers.tsv", "report.json", "run_manifest.json", "summary.md"],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise LiteratureReviewError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_papers(path: Path, papers: list[dict[str, Any]]) -> None:
    fields = [
        "rank",
        "source_code",
        "id",
        "pmid",
        "pmcid",
        "doi",
        "title",
        "authors",
        "journal",
        "year",
        "study_type",
        "publication_types",
        "open_access",
        "preprint",
        "cited_by_count",
        "url",
        "abstract",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for paper in papers:
            row = {key: paper.get(key) for key in fields}
            row["publication_types"] = "; ".join(paper["publication_types"])
            writer.writerow(row)


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Literature evidence map",
        "",
        f"Query: `{result['exact_query']}`",
        "",
        result["summary"],
        "",
        "| Rank | Year | Study type | Publication |",
        "| ---: | ---: | --- | --- |",
    ]
    for paper in result["papers"]:
        identifier = paper.get("pmid") or paper.get("pmcid") or paper["id"]
        title = str(paper["title"]).replace("|", "\\|")
        lines.append(f"| {paper['rank']} | {paper.get('year') or ''} | {paper['study_type']} | [{title}]({paper['url']}) ({identifier}) |")
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _optional_year(value: Any, label: str, current_year: int) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        year = int(value)
    except (TypeError, ValueError) as exc:
        raise LiteratureReviewError(f"{label} must be a four-digit year.") from exc
    if not MIN_YEAR <= year <= current_year + 1:
        raise LiteratureReviewError(f"{label} must be between {MIN_YEAR} and {current_year + 1}.")
    return year


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().casefold() in {"1", "true", "yes", "y"}


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _clean_markup(value: str) -> str:
    decoded = html.unescape(value)
    without_tags = re.sub(r"<[^>]+>", "", decoded)
    return re.sub(r"\s+", " ", without_tags).strip()
