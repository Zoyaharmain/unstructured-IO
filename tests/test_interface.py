import importlib.util
import unittest
from pathlib import Path
from pdf_hires import partition_pdf


class InterfaceTests(unittest.TestCase):
    def test_legacy_port_is_separate_from_api(self):
        import inspect
        from pdf_hires._vendor.partition.pdf import partition_pdf as legacy
        self.assertIn("pdf_hires/_vendor/partition/pdf.py", inspect.getfile(inspect.unwrap(legacy)))

    def test_no_other_strategies(self):
        for strategy in ['auto', 'fast', 'ocr_only']:
            with self.assertRaisesRegex(ValueError, 'hi_res'):
                partition_pdf('missing.pdf', strategy=strategy)

    def test_no_chunking(self):
        with self.assertRaisesRegex(ValueError, 'Chunking'):
            partition_pdf('missing.pdf', chunking_strategy='by_title')

    def test_actual_pdf_stream(self):
        from io import BytesIO
        from pdf_hires import extract_pdf
        path = Path(__file__).parent / 'fixtures/digital-multipage.pdf'
        settings = dict(languages=['eng'], hi_res_model_name='yolox', metadata_filename='same.pdf',
                        metadata_last_modified='2026-10-15T00:00:00')
        from_file = extract_pdf(file=BytesIO(path.read_bytes()), **settings)
        self.assertTrue(from_file)
        self.assertEqual([e['reading_order'] for e in from_file], list(range(1, len(from_file)+1)))
        self.assertEqual({e['metadata']['page_number'] for e in from_file}, {1, 2})
        self.assertTrue(all(e['metadata'].get('coordinates') for e in from_file))

if __name__ == '__main__':
    unittest.main()
