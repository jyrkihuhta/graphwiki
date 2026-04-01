"""Unit tests for meshwiki.utils."""

from meshwiki.utils import slugify


class TestSlugify:
    def test_normal_input(self):
        assert slugify("Hello World") == "hello-world"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_special_characters(self):
        assert slugify("Hello World!") == "hello-world"

    def test_leading_hyphens(self):
        assert slugify("---hello world---") == "hello-world"

    def test_trailing_hyphens(self):
        assert slugify("hello world---") == "hello-world"

    def test_underscores_replaced(self):
        assert slugify("hello_world") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_mixed_separators(self):
        assert slugify("hello_world-test") == "hello-world-test"

    def test_consecutive_hyphens(self):
        assert slugify("hello--world") == "hello-world"

    def test_alphanumeric_only(self):
        assert slugify("abc123") == "abc123"

    def test_special_chars_stripped(self):
        assert slugify("a@b#c$d%") == "abcd"
