import os
import base64
import tempfile
import unittest
from src.file_parser import parse_uploaded_file, format_bytes


class FileUploadTests(unittest.TestCase):

    def test_format_bytes(self):
        self.assertEqual(format_bytes(500), "500 B")
        self.assertEqual(format_bytes(2048), "2.0 KB")
        self.assertEqual(format_bytes(1048576 * 3), "3.0 MB")

    def test_parse_python_code_file(self):
        code = "def add(a, b):\n    return a + b\n\nprint(add(2, 3))"
        b64 = base64.b64encode(code.encode("utf-8")).decode("utf-8")
        result = parse_uploaded_file("calculator.py", base64_data=b64)

        self.assertTrue(result["success"])
        self.assertEqual(result["filename"], "calculator.py")
        self.assertEqual(result["badge_type"], "CODE")
        self.assertIn("def add", result["text"])
        self.assertGreater(result["word_count"], 0)

    def test_parse_markdown_document(self):
        md_text = "# Project Roadmap\n- Phase 1: Architecture\n- Phase 2: Implementation"
        result = parse_uploaded_file("roadmap.md", raw_text=md_text)

        self.assertTrue(result["success"])
        self.assertEqual(result["badge_type"], "DOC")
        self.assertIn("Project Roadmap", result["text"])
        self.assertEqual(result["word_count"], 8)

    def test_parse_pdf_document(self):
        import fitz
        doc = fitz.open()
        page1 = doc.new_page()
        page1.insert_text((50, 72), "NOVAX Executive Intelligence Briefing")
        page2 = doc.new_page()
        page2.insert_text((50, 72), "Section 2: High Performance Architecture")
        pdf_bytes = doc.tobytes()
        doc.close()

        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        result = parse_uploaded_file("executive_report.pdf", base64_data=b64)

        self.assertTrue(result["success"])
        self.assertEqual(result["badge_type"], "PDF")
        self.assertEqual(result["page_count"], 2)
        self.assertIn("NOVAX Executive Intelligence Briefing", result["text"])
        self.assertIn("Section 2: High Performance Architecture", result["text"])

    def test_parse_data_csv(self):
        csv_text = "id,name,role\n1,Alex,Lead\n2,Taylor,Engineer"
        result = parse_uploaded_file("team.csv", raw_text=csv_text)

        self.assertTrue(result["success"])
        self.assertEqual(result["badge_type"], "DATA")
        self.assertIn("Taylor", result["text"])


if __name__ == "__main__":
    unittest.main()
