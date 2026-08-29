import csv
import gzip
import hashlib
import importlib.util
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from bio_clients import ExternalDataError, _AllowlistedRedirectHandler

from agent_runtime import (
    extract_geo_series_matrix_plan,
    local_intent_tools,
    local_workflow_plan,
)
from geo_series_matrix import (
    GeoSeriesMatrixError,
    import_geo_series_matrix,
    normalize_geo_series_matrix_inputs,
    parse_geo_series_matrix,
    parse_matrix_directory_listing,
    preflight_geo_series_matrix,
)
from skill_runtime import SkillRegistry, compact_tool_result
from workflow_runtime import WorkflowManager


LISTING = """<html><body><pre>
<a href="GSE1000_series_matrix.txt.gz">GSE1000_series_matrix.txt.gz</a> 2026-07-06 15:53 1.3M
</pre></body></html>"""

MULTI_LISTING = """<html><body><pre>
<a href="GSE2000-GPL96_series_matrix.txt.gz">GSE2000-GPL96_series_matrix.txt.gz</a>
<a href="GSE2000-GPL97_series_matrix.txt.gz">GSE2000-GPL97_series_matrix.txt.gz</a>
</pre></body></html>"""


def synthetic_matrix(*, bad_value: bool = False) -> bytes:
    value = "bad" if bad_value else "5.5"
    text = "\n".join(
        [
            '!Series_title\t"Synthetic airway study"',
            '!Series_type\t"Expression profiling by array"',
            '!Series_summary\t"Synthetic parser fixture"',
            '!Sample_title\t"Control 1"\t"Control 2"\t"Treated 1"',
            '!Sample_geo_accession\t"GSM1001"\t"GSM1002"\t"GSM1003"',
            '!Sample_source_name_ch1\t"airway"\t"airway"\t"airway"',
            '!Sample_organism_ch1\t"Homo sapiens"\t"Homo sapiens"\t"Homo sapiens"',
            '!Sample_contact_email\t"submitter@example.org"\t"submitter@example.org"\t"submitter@example.org"',
            '!Sample_characteristics_ch1\t"condition: control"\t"condition: control"\t"condition: treated"',
            '!Sample_characteristics_ch1\t"batch: A"\t"batch: B"\t"batch: A"',
            "!series_matrix_table_begin",
            '"ID_REF"\t"GSM1001"\t"GSM1002"\t"GSM1003"',
            '"probe1"\t"1"\t"2"\t"3"',
            f'"probe2"\t"4.5"\t"{value}"\t"6.5"',
            '"probe3"\t"7"\t""\t"9"',
            "!series_matrix_table_end",
            "",
        ]
    )
    return gzip.compress(text.encode("utf-8"))


def ready_preflight() -> dict:
    return {
        "ready": True,
        "source": "NCBI GEO Series Matrix",
        "source_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE1nnn/GSE1000/matrix/",
        "accession": "GSE1000",
        "matrix_file": "GSE1000_series_matrix.txt.gz",
        "available_files": ["GSE1000_series_matrix.txt.gz"],
        "download_url": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE1nnn/GSE1000/matrix/GSE1000_series_matrix.txt.gz",
        "compressed_bytes": len(synthetic_matrix()),
        "content_type": "application/x-gzip",
        "last_modified": "Mon, 06 Jul 2026 19:53:39 GMT",
        "limits": {
            "compressed_bytes": 32 * 1024 * 1024,
            "uncompressed_bytes": 160 * 1024 * 1024,
            "samples": 500,
            "features": 100000,
            "matrix_cells": 12000000,
        },
        "warnings": ["Processed values are not raw counts."],
        "summary": "Validated official Series Matrix source.",
    }


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "geo-series-matrix-import",
            "summary": "Matrix imported.",
            "artifacts": [{"id": "matrix", "type": "geo-series-matrix-import", "data": {}}],
        }


class GeoSeriesMatrixTests(unittest.TestCase):
    def test_external_redirects_are_validated_before_following(self):
        handler = _AllowlistedRedirectHandler()
        request = urllib.request.Request("https://ftp.ncbi.nlm.nih.gov/geo/")
        with self.assertRaises(ExternalDataError):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://example.com/private-matrix.txt.gz",
            )

    def test_normalization_builds_official_range_and_rejects_paths(self):
        result = normalize_geo_series_matrix_inputs("gse1000")
        self.assertEqual(result["accession"], "GSE1000")
        self.assertEqual(
            result["directory_url"],
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE1nnn/GSE1000/matrix/",
        )
        selected = normalize_geo_series_matrix_inputs(
            "GSE2000", "GSE2000-GPL96_series_matrix.txt.gz"
        )
        self.assertEqual(selected["matrix_file"], "GSE2000-GPL96_series_matrix.txt.gz")
        with self.assertRaises(GeoSeriesMatrixError):
            normalize_geo_series_matrix_inputs("GDS1000")
        with self.assertRaises(GeoSeriesMatrixError):
            normalize_geo_series_matrix_inputs("GSE1000", "../GSE1000_series_matrix.txt.gz")

    def test_listing_requires_explicit_platform_when_multiple(self):
        self.assertEqual(
            parse_matrix_directory_listing(LISTING, "GSE1000"),
            ["GSE1000_series_matrix.txt.gz"],
        )
        with patch("geo_series_matrix.get_text", return_value=MULTI_LISTING):
            result = preflight_geo_series_matrix("GSE2000")
        self.assertFalse(result["ready"])
        self.assertEqual(len(result["available_files"]), 2)
        self.assertEqual(result["download_url"], "")

    def test_preflight_selects_one_official_file_and_checks_size(self):
        head = {
            "url": ready_preflight()["download_url"],
            "host": "ftp.ncbi.nlm.nih.gov",
            "content_length": 1385042,
            "content_type": "application/x-gzip",
            "last_modified": "Mon, 06 Jul 2026 19:53:39 GMT",
        }
        with patch("geo_series_matrix.get_text", return_value=LISTING), patch(
            "geo_series_matrix.get_head_metadata", return_value=head
        ):
            result = preflight_geo_series_matrix("GSE1000")
        self.assertTrue(result["ready"])
        self.assertEqual(result["matrix_file"], "GSE1000_series_matrix.txt.gz")
        self.assertEqual(result["compressed_bytes"], 1385042)

    def test_parser_preserves_values_metadata_and_qc(self):
        with tempfile.TemporaryDirectory() as temporary:
            expression = Path(temporary) / "expression.tsv"
            result = parse_geo_series_matrix(synthetic_matrix(), expression)
            with expression.open(encoding="utf-8") as handle:
                rows = list(csv.reader(handle, delimiter="\t"))

        self.assertEqual(result["feature_count"], 3)
        self.assertEqual(result["sample_count"], 3)
        self.assertEqual(result["series_title"], "Synthetic airway study")
        self.assertEqual(result["matrix_metrics"]["missing_values"], 1)
        self.assertAlmostEqual(result["matrix_metrics"]["missing_fraction"], 1 / 9)
        self.assertEqual(rows[0], ["feature_id", "GSM1001", "GSM1002", "GSM1003"])
        self.assertEqual(rows[3], ["probe3", "7", "", "9"])
        self.assertIn("condition: control", result["sample_metadata"][0]["characteristics_ch1"])
        self.assertIn("batch: A", result["sample_metadata"][0]["characteristics_ch1"])
        self.assertNotIn("contact_email", result["sample_metadata_fields"])
        self.assertNotIn("submitter@example.org", json.dumps(result))

    def test_import_persists_original_tables_hash_and_manifest(self):
        payload = synthetic_matrix()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "geo_series_matrix.preflight_geo_series_matrix", return_value=ready_preflight()
        ), patch("geo_series_matrix.get_binary", return_value=payload), patch(
            "geo_series_matrix.WORKSPACE_ROOT", Path(temporary)
        ):
            result = import_geo_series_matrix("GSE1000")
            root = Path(temporary) / result["output_root"]
            report = json.loads((root / "matrix_summary.json").read_text(encoding="utf-8"))
            manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))

        self.assertFalse(result["raw_count_compatible"])
        self.assertEqual(result["source_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(report["feature_count"], 3)
        self.assertEqual(manifest["dimensions"], {"features": 3, "samples": 3})
        self.assertIn("PyDESeq2", result["analysis_handoff"])

    def test_parser_rejects_non_numeric_and_uncompressed_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "bad.tsv"
            with self.assertRaisesRegex(GeoSeriesMatrixError, "non-numeric"):
                parse_geo_series_matrix(synthetic_matrix(bad_value=True), output)
            with patch("geo_series_matrix.MAX_UNCOMPRESSED_BYTES", 80), self.assertRaisesRegex(
                GeoSeriesMatrixError, "uncompressed size"
            ):
                parse_geo_series_matrix(synthetic_matrix(), output)

    def test_agent_routes_preflight_and_approved_import_separately(self):
        request = "导入 GSE1000 Series Matrix 到本地工作区"
        preflight = "预检 GSE1000 的 Series Matrix"
        registry = SkillRegistry()
        exposed = {item["function"]["name"] for item in registry.openai_tools()}

        self.assertEqual(extract_geo_series_matrix_plan(request)["accession"], "GSE1000")
        self.assertEqual(local_workflow_plan(request, {})[0], "geo-series-matrix-import")
        self.assertIsNone(local_workflow_plan(preflight, {}))
        self.assertEqual(local_intent_tools(preflight)[0][0], "geo_series_matrix_preflight")
        self.assertIn("geo_series_matrix_preflight", exposed)
        self.assertNotIn("geo_series_matrix_import", exposed)

    def test_workflow_preflights_then_imports_only_after_approval(self):
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "workflow_runtime.preflight_geo_series_matrix", return_value=ready_preflight()
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "geo-series-matrix-import",
                {"accession": "GSE1000", "matrix_file": ""},
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "geo_series_matrix_import")

    def test_model_compaction_omits_full_matrix_metadata(self):
        payload = synthetic_matrix()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "geo_series_matrix.preflight_geo_series_matrix", return_value=ready_preflight()
        ), patch("geo_series_matrix.get_binary", return_value=payload), patch(
            "geo_series_matrix.WORKSPACE_ROOT", Path(temporary)
        ):
            data = import_geo_series_matrix("GSE1000")
        encoded = compact_tool_result(
            {
                "ok": True,
                "tool": "geo_series_matrix_import",
                "skill": "geo-series-matrix-import",
                "summary": data["summary"],
                "data": data,
                "artifacts": [{"data": data}],
            }
        )
        compact = json.loads(encoded)
        self.assertNotIn("sample_metadata", compact["data"])
        self.assertNotIn("feature_preview", compact["data"])
        self.assertNotIn("artifacts", compact)
        self.assertLessEqual(len(encoded), 24000)

    def test_handler_schema_defaults_are_stable(self):
        path = Path(__file__).parents[1] / "skills" / "geo-series-matrix-import" / "scripts" / "handler.py"
        spec = importlib.util.spec_from_file_location("geo_series_matrix_handler_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module._arguments({"accession": "GSE1000"}),
            {"accession": "GSE1000", "matrix_file": ""},
        )


if __name__ == "__main__":
    unittest.main()
