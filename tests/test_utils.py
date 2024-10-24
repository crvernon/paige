import unittest
from unittest.mock import patch
from io import BytesIO
from pathlib import Path

import tiktoken
from pypdf import PdfWriter, PdfReader

import highlight as hlt


class TestGetTokenCount(unittest.TestCase):
    def test_get_token_count_default_model(self):
        text = "This is a test."
        expected_token_count = len(tiktoken.encoding_for_model("gpt-4o").encode(text))
        self.assertEqual(hlt.get_token_count(text), expected_token_count)

    def test_get_token_count_custom_model(self):
        text = "Another test."
        model = "gpt-3.5-turbo"
        expected_token_count = len(tiktoken.encoding_for_model(model).encode(text))
        self.assertEqual(hlt.get_token_count(text, model), expected_token_count)

    def test_get_token_count_empty_text(self):
        text = ""
        expected_token_count = len(tiktoken.encoding_for_model("gpt-4o").encode(text))
        self.assertEqual(hlt.get_token_count(text), expected_token_count)


class TestReadConfig(unittest.TestCase):
    def test_read_config(self):
        config = hlt.read_config(Path(__file__).parent.resolve() / "test-config.toml")
        self.assertDictEqual(
            {
                "llm": {
                    "openai": {
                        "models": [
                            "gpt-4o",
                            "gpt-4",
                            "gpt-3.5-turbo-16k",
                            "gpt-3.5-turbo",
                        ]
                    }
                }
            },
            config,
        )


class TestReadPdf(unittest.TestCase):
    def test_read_pdf_without_reference_indicator(self):
        # Create a sample PDF file using pypdf
        buffer = BytesIO()

        # Create a PDF writer
        writer = PdfWriter()

        # Add a blank page
        writer.add_blank_page(width=612, height=792)

        # Write the PDF to the buffer
        writer.write(buffer)

        # Reset buffer position to the beginning
        buffer.seek(0)

        # Mock the PdfReader's extract_text method to return "Hello World"
        with patch.object(
            PdfReader, "pages", new_callable=unittest.mock.PropertyMock
        ) as mock_pages:
            mock_page = unittest.mock.Mock()
            mock_page.extract_text.return_value = "Hello World"
            mock_pages.return_value = [mock_page]

            # Test with a PDF without the reference indicator
            result = hlt.read_pdf(buffer, reference_indicator="References\n")

            # Validate the content and structure
            self.assertEqual(result["n_pages"], 1)
            self.assertIn("Hello World", result["content"])
            self.assertGreater(result["n_characters"], 0)
            self.assertGreater(result["n_words"], 0)
            self.assertGreater(result["n_tokens"], 0)


class TestReadText(unittest.TestCase):
    def test_read_text(self):
        # Simulate a text file using BytesIO
        sample_text = "Hello World!\nThis is a test file."
        text_file = BytesIO(sample_text.encode("utf-8"))

        result = hlt.read_text(text_file)

        # Assertions to validate the output
        self.assertEqual(result["content"], sample_text)
        self.assertEqual(result["n_pages"], 1)
        self.assertEqual(result["n_characters"], len(sample_text))
        self.assertEqual(result["n_words"], 7)


if __name__ == "__main__":
    unittest.main()
