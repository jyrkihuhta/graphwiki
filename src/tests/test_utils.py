"""Tests for meshwiki.utils."""

from meshwiki.utils import slugify


class TestSlugify:
    def test_basic_lowercase(self):
        assert slugify("Hello World!") == "hello-world"

    def test_empty_string(self):
        assert slugify("") == ""

    def test_special_characters(self):
        assert slugify("Hello@World#Test") == "helloworldtest"

    def test_leading_trailing_hyphens(self):
        assert slugify("---hello world---") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello  world  test") == "hello-world-test"

    def test_underscores(self):
        assert slugify("hello_world_test") == "hello-world-test"

    def test_mixed_spaces_and_underscores(self):
        assert slugify("hello_world test") == "hello-world-test"

    def test_collapse_multiple_hyphens(self):
        assert slugify("hello---world") == "hello-world"

    def test_alphanumeric_preserved(self):
        assert slugify("test123") == "test123"

    def test_numbers_and_hyphens(self):
        assert slugify("test-123-page") == "test-123-page"

    def test_only_special_characters(self):
        assert slugify("@#$%") == ""

    def test_leading_numbers(self):
        assert slugify("123Hello") == "123hello"
