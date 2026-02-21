from __future__ import annotations

import unittest

from app.story_wrapper import _extract_story_snippets, _is_relevant_to_skill


class StoryWrapperTests(unittest.TestCase):
    def test_extract_filters_noise_and_equation_blocks(self) -> None:
        text = """
        Page 12 Header

        5 + 3 = 8

        A student buys 3 notebooks at $2 each and 1 pencil for $1. What is the total cost?

        Chapter Footer
        """
        snippets = _extract_story_snippets(text)
        self.assertTrue(any("total cost" in snippet.lower() for snippet in snippets))
        self.assertFalse(any("5 + 3 = 8" in snippet for snippet in snippets))

    def test_skill_relevance_filter(self) -> None:
        money_snippet = "A student has 5 dollars and 20 cents and buys a snack."
        geometry_snippet = "A triangle has side lengths 3, 4, and 5."
        self.assertTrue(_is_relevant_to_skill("money", money_snippet))
        self.assertFalse(_is_relevant_to_skill("money", geometry_snippet))


if __name__ == "__main__":
    unittest.main()
