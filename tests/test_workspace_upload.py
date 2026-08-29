import unittest

from workspace_utils import WorkspaceError, WORKSPACE_ROOT, write_workspace_file


class WorkspaceUploadTests(unittest.TestCase):
    def test_binary_scientific_upload_preserves_bytes(self):
        relative = "uploads/test-upload.h5ad"
        target = WORKSPACE_ROOT / relative
        payload = b"\x89HDF\r\n\x1a\n\x00molemo"
        try:
            result = write_workspace_file(relative, payload)
            self.assertEqual(result["size"], len(payload))
            self.assertEqual(target.read_bytes(), payload)
        finally:
            target.unlink(missing_ok=True)

    def test_upload_rejects_empty_unsupported_and_non_utf8_text(self):
        with self.assertRaises(WorkspaceError):
            write_workspace_file("uploads/empty.h5ad", b"")
        with self.assertRaises(WorkspaceError):
            write_workspace_file("uploads/data.exe", b"payload")
        with self.assertRaises(WorkspaceError):
            write_workspace_file("uploads/data.csv", b"\xff\xfe")

    def test_upload_rejects_workspace_escape(self):
        with self.assertRaises(WorkspaceError):
            write_workspace_file("../outside.h5ad", b"payload")


if __name__ == "__main__":
    unittest.main()
