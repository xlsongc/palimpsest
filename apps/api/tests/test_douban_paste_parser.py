import json
from pathlib import Path

import pytest

from app.importers.douban_paste import parse_douban_paste

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "douban_paste"


def _load_fixture_pair(name: str) -> tuple[str, list[dict]]:
    raw = (FIXTURES_DIR / f"{name}_raw.txt").read_text()
    expected = json.loads((FIXTURES_DIR / f"{name}_expected.json").read_text())
    return raw, expected


# --- read list ---

def test_read_list_candidate_count():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    assert len(result.rows) == len(expected)


def test_read_list_titles_match():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.title == exp["title"], f"Expected {exp['title']!r}, got {row.title!r}"


def test_read_list_status_is_read():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    for row in result.rows:
        assert row.status == "read"


def test_read_list_dates_match():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.read_date == exp.get("read_date")


def test_read_list_ratings_match():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.rating == exp.get("rating")


def test_read_list_comments_match():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.comment == exp.get("comment")


def test_read_list_fragments_nonempty():
    raw, expected = _load_fixture_pair("read_list")
    result = parse_douban_paste(raw)
    for row in result.rows:
        assert len(row.raw_fragment) > 0
        assert row.raw_fragment in raw


# --- want list ---

def test_want_list_candidate_count():
    raw, expected = _load_fixture_pair("want_list")
    result = parse_douban_paste(raw)
    assert len(result.rows) == len(expected)


def test_want_list_titles_match():
    raw, expected = _load_fixture_pair("want_list")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.title == exp["title"]


def test_want_list_status_is_want():
    raw, expected = _load_fixture_pair("want_list")
    result = parse_douban_paste(raw)
    for row in result.rows:
        assert row.status == "want"


def test_want_list_marked_dates_match():
    raw, expected = _load_fixture_pair("want_list")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.marked_date == exp.get("marked_date")


# --- mixed noisy ---

def test_mixed_noisy_candidate_count():
    raw, expected = _load_fixture_pair("mixed_noisy")
    result = parse_douban_paste(raw)
    assert len(result.rows) == len(expected)


def test_mixed_noisy_titles_match():
    raw, expected = _load_fixture_pair("mixed_noisy")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.title == exp["title"]


def test_mixed_noisy_statuses_match():
    raw, expected = _load_fixture_pair("mixed_noisy")
    result = parse_douban_paste(raw)
    for row, exp in zip(result.rows, expected):
        assert row.status == exp.get("status")


def test_mixed_noisy_warnings_for_missing_rating():
    raw, expected = _load_fixture_pair("mixed_noisy")
    result = parse_douban_paste(raw)
    # Row 1 (涛动周期论) has no rating
    assert "missing_rating" in result.rows[1].warnings
    # Row 3 (incomplete entry) has missing status
    assert "missing_status" in result.rows[3].warnings


def test_mixed_noisy_low_confidence_incomplete():
    raw, expected = _load_fixture_pair("mixed_noisy")
    result = parse_douban_paste(raw)
    # Row 3 is the incomplete entry
    assert result.rows[3].confidence < 0.5


# --- edge cases ---


@pytest.mark.parametrize(
    ("fixture_name", "expected_status", "date_field"),
    [
        ("read_list_page", "read", "read_date"),
        ("want_list_page", "want", "marked_date"),
    ],
)
def test_compact_page_list_matches_expected_titles_status_and_dates(
    fixture_name: str, expected_status: str, date_field: str
):
    raw, expected = _load_fixture_pair(fixture_name)
    result = parse_douban_paste(raw)

    assert len(result.rows) == len(expected)
    for row, exp in zip(result.rows, expected):
        assert row.title == exp["title"]
        assert row.status == expected_status
        assert getattr(row, date_field) == exp[date_field]
        assert row.raw_fragment == exp["raw_fragment"]
        assert row.raw_fragment in raw


def test_empty_input_returns_no_rows():
    result = parse_douban_paste("")
    assert len(result.rows) == 0
    assert "empty_input" in result.warnings


def test_whitespace_only_returns_no_rows():
    result = parse_douban_paste("   \n\n  ")
    assert len(result.rows) == 0
    assert "empty_input" in result.warnings


def test_noise_only_returns_no_rows():
    result = parse_douban_paste("我的读书\n豆瓣读书搜索\n赞 回复\n加载更多")
    assert len(result.rows) == 0
    assert "no_books_found" in result.warnings
