"""Tests for the refactored prompt formatting and the Pydantic AI config layer."""

import os
import sys
import unittest

# Ensure the backend package is importable when tests run from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import highlight as hlt


class TestGeneratePrompt(unittest.TestCase):
    def test_title_prompt_contains_content(self):
        prompt = hlt.generate_prompt(content="Sample body text", prompt_name="title")
        self.assertIn("Sample body text", prompt)

    def test_subtitle_requires_additional_content(self):
        with self.assertRaises(ValueError):
            hlt.generate_prompt(content="body", prompt_name="subtitle")

    def test_subtitle_includes_title(self):
        prompt = hlt.generate_prompt(
            content="body text",
            prompt_name="subtitle",
            additional_content="A Great Title",
        )
        self.assertIn("A Great Title", prompt)
        self.assertIn("body text", prompt)

    def test_objective_includes_examples(self):
        prompt = hlt.generate_prompt(content="body", prompt_name="objective")
        # The objective template embeds two example texts plus the content.
        self.assertIn("body", prompt)

    def test_unknown_prompt_raises(self):
        with self.assertRaises(ValueError):
            hlt.generate_prompt(content="body", prompt_name="does_not_exist")


class TestAgentConfig(unittest.TestCase):
    def test_resolve_config_uses_overrides(self):
        from app.agent import resolve_config

        cfg = resolve_config(
            api_key="user-key", base_url="https://example.test", model="gpt-x"
        )
        self.assertEqual(cfg.api_key, "user-key")
        self.assertEqual(cfg.base_url, "https://example.test")
        self.assertEqual(cfg.model, "gpt-x")

    def test_resolve_config_falls_back_to_settings(self):
        from app.agent import resolve_config
        from app.config import get_settings

        settings = get_settings()
        cfg = resolve_config()
        self.assertEqual(cfg.base_url, settings.openai_base_url)
        self.assertEqual(cfg.model, settings.openai_model)


if __name__ == "__main__":
    unittest.main()
