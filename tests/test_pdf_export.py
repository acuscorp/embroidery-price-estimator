import unittest

from exports.pdf_export import build_simple_pdf


class PdfExportTests(unittest.TestCase):
    def test_long_design_lists_are_paginated(self):
        pdf = build_simple_pdf(
            [f"Renglon {index}" for index in range(81)],
            (b"image-bytes", 100, 100),
        )
        self.assertEqual(pdf.count(b"/Type /Page "), 3)
        self.assertIn(b"/Count 3", pdf)


if __name__ == "__main__":
    unittest.main()
