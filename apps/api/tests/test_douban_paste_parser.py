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


def test_free_text_extracts_multiple_reviewable_candidates():
    result = parse_douban_paste(
        "最近读完了《思考，快与慢》，还想读 Poor Charlie's Almanack。"
        "另一本是 黄金时代 作者王小波。"
    )

    assert [row.title for row in result.rows] == [
        "思考，快与慢",
        "Poor Charlie's Almanack",
        "黄金时代",
    ]
    assert result.rows[0].status == "read"
    assert result.rows[1].status == "want"
    assert result.rows[2].authors == ["王小波"]
    assert all(row.confidence < 0.95 for row in result.rows)


def test_messy_slash_and_plain_english_lines_do_not_collapse_to_one_row():
    result = parse_douban_paste(
        "思考，快与慢 / Daniel Kahneman / 2012 / 中信 / 读过 2024-01-02 / 9分\n"
        "random nav footer ###\n"
        "Poor Charlie's Almanack Charles T. Munger want 2025-04-01"
    )

    assert [row.title for row in result.rows] == [
        "思考，快与慢",
        "Poor Charlie's Almanack",
    ]
    assert result.rows[0].authors == ["Daniel Kahneman"]
    assert result.rows[0].status == "read"
    assert result.rows[0].read_date == "2024-01-02"
    assert result.rows[0].rating == 9.0
    assert result.rows[1].authors == ["Charles T. Munger"]
    assert result.rows[1].status == "want"
    assert result.rows[1].marked_date == "2025-04-01"


def test_one_title_per_line_extracts_each_title_as_low_confidence_candidate():
    result = parse_douban_paste("思考，快与慢\nPoor Charlie's Almanack\n黄金时代\n")

    assert [row.title for row in result.rows] == [
        "思考，快与慢",
        "Poor Charlie's Almanack",
        "黄金时代",
    ]
    assert all(row.confidence < 0.5 for row in result.rows)
    assert all("missing_status" in row.warnings for row in result.rows)


def test_realistic_douban_profile_copy_extracts_entries_across_status_sections():
    raw = """
我在读的书(20)
读书主页 书评 笔记 在读 想读 读过 作者 豆列 书单 设置 | 豆瓣主页
按时间排序 · 按评价排序 · 按标题排序1-15 / 20 grid
list

Common Stocks and Uncommon Profits and Other Writings
Philip A. Fisher / Wiley / 1996-9-19 / GBP 19.99
2026-05-02 在读 标签: 芒格荐书

修改    删除
纸质版 98.34元 加入购书单

我想读的书(75)

软件设计的哲学
[美]约翰·奥斯特豪特（John Ousterhout） / 茹炳晟 / 人民邮电出版社 / 2024-11 / 69.80元
2026-05-03 想读 标签: vibecoding

修改    删除

我读过的书(26)

The Almanack of Naval Ravikant : A Guide to Wealth and Happiness
Naval Ravikant、Eric Jorgenson / Magrathea Publishing / 2020-9-8 / USD 12.84
2026-04-19 读过
个人长评内容已脱敏。

修改    删除
"""

    result = parse_douban_paste(raw)

    assert [row.title for row in result.rows] == [
        "Common Stocks and Uncommon Profits and Other Writings",
        "软件设计的哲学",
        "The Almanack of Naval Ravikant : A Guide to Wealth and Happiness",
    ]
    assert [row.status for row in result.rows] == ["reading", "want", "read"]
    assert result.rows[0].marked_date == "2026-05-02"
    assert result.rows[1].marked_date == "2026-05-03"
    assert result.rows[2].read_date == "2026-04-19"
    assert result.rows[0].tags == ["芒格荐书"]
    assert result.rows[1].tags == ["vibecoding"]
    assert result.rows[0].authors == ["Philip A. Fisher"]
    assert result.rows[2].authors == ["Naval Ravikant", "Eric Jorgenson"]
