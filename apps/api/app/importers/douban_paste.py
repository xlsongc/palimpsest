from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class DoubanParsedRow:
    row_index: int
    raw_fragment: str
    title: str
    status: str | None = None
    authors: list[str] = field(default_factory=list)
    rating: float | None = None
    comment: str | None = None
    tags: list[str] = field(default_factory=list)
    read_date: str | None = None
    marked_date: str | None = None
    douban_url: str | None = None
    confidence: float = 0.95
    warnings: list[str] = field(default_factory=list)


@dataclass
class DoubanParseResult:
    rows: list[DoubanParsedRow]
    warnings: list[str] = field(default_factory=list)


_STATUS_PATTERN = re.compile(r"(我读过这本书|我想读这本书|我在读这本书)\s*(\d{4}-\d{2}-\d{2})?")
_RATING_PATTERN = re.compile(r"豆瓣评分:\s*([\d.]+)")
_AUTHOR_PATTERN = re.compile(r"作者:\s*(.+)")
_TAG_PATTERN = re.compile(r"标签:\s*(.+)")
_COMMENT_PATTERN = re.compile(r"评论:\s*(.+)")
_COMPACT_BOOK_LINE_PATTERN = re.compile(r"^(?P<title>.+?)\s*(?P<date>\d{4}-\d{2}-\d{2})$")

_NOISE_PATTERNS = [
    re.compile(r"^\s*赞\s+回复\s*$"),
    re.compile(r"^\s*加载更多"),
    re.compile(r"^(我的读书|豆瓣读书搜索|书名 作者 ISBN|搜索|按时间排序|按评分排序|按标题排序|grid|list|读书主页|已读|在读|想读|广告位招租|联系我们|---)"),
    re.compile(r"^\d+-\d+\s*/\s*\d+"),
]


def _is_noise(line: str) -> bool:
    stripped = line.strip()
    # Don't treat blank lines as noise - they preserve block structure
    if not stripped:
        return False
    for pat in _NOISE_PATTERNS:
        if pat.search(stripped):
            return True
    return False


def _split_blocks(raw_input: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in raw_input.split("\n"):
        if re.match(r"^\s*赞\s+回复\s*$", line.strip()):
            if current:
                # Strip trailing blank lines from block
                while current and not current[-1].strip():
                    current.pop()
                if current:
                    blocks.append("\n".join(current))
                current = []
            continue
        if _is_noise(line):
            continue
        current.append(line)
    if current:
        # Strip trailing blank lines
        while current and not current[-1].strip():
            current.pop()
        if current:
            blocks.append("\n".join(current))
    return blocks


def _infer_compact_page_status(raw_input: str) -> str | None:
    if "我读过的书" in raw_input:
        return "read"
    if "我想读的书" in raw_input:
        return "want"
    if "我在读的书" in raw_input:
        return "reading"
    return None


def _parse_compact_page_rows(raw_input: str) -> list[DoubanParsedRow]:
    status = _infer_compact_page_status(raw_input)
    if status is None:
        return []

    rows: list[DoubanParsedRow] = []
    for line in raw_input.splitlines():
        raw_fragment = line.strip()
        if not raw_fragment or _is_noise(raw_fragment):
            continue
        if raw_fragment.startswith(("我读过的书", "我想读的书", "我在读的书")):
            continue

        match = _COMPACT_BOOK_LINE_PATTERN.match(raw_fragment)
        if not match:
            continue

        title = match.group("title").strip()
        date = match.group("date")
        warnings: list[str] = []
        confidence = 0.95
        if "..." in title:
            warnings.append("title_truncated")
            confidence = 0.9

        rows.append(
            DoubanParsedRow(
                row_index=len(rows),
                raw_fragment=raw_fragment,
                title=title,
                status=status,
                read_date=date if status == "read" else None,
                marked_date=date if status in {"reading", "want"} else None,
                confidence=confidence,
                warnings=warnings,
            )
        )

    return rows


def _parse_block(block: str) -> DoubanParsedRow | None:
    # Use stripped version for field extraction
    lines_for_parsing = [l for l in block.strip().split("\n") if l.strip()]
    if not lines_for_parsing:
        return None

    title = lines_for_parsing[0].strip()
    if not title:
        return None

    status = None
    read_date = None
    marked_date = None
    authors: list[str] = []
    rating = None
    tags: list[str] = []
    comment = None

    for line in lines_for_parsing:
        m = _STATUS_PATTERN.search(line)
        if m:
            status_map = {"我读过这本书": "read", "我想读这本书": "want", "我在读这本书": "reading"}
            status = status_map.get(m.group(1))
            if m.group(2):
                if status == "want":
                    marked_date = m.group(2)
                else:
                    read_date = m.group(2)

        m = _RATING_PATTERN.search(line)
        if m:
            try:
                rating = float(m.group(1))
            except ValueError:
                pass

        m = _AUTHOR_PATTERN.search(line)
        if m:
            authors = [a.strip() for a in m.group(1).split(",")]

        m = _TAG_PATTERN.search(line)
        if m:
            tags = [t.strip() for t in m.group(1).split("、")]

        m = _COMMENT_PATTERN.search(line)
        if m:
            comment = m.group(1).strip()

    warnings: list[str] = []
    confidence = 0.95

    if rating is None:
        warnings.append("missing_rating")
        confidence = min(confidence, 0.9)
    if not authors:
        warnings.append("missing_authors")
        confidence = min(confidence, 0.9)
    if status is None:
        warnings.append("missing_status")
        confidence = min(confidence, 0.3)

    if confidence < 0.5:
        warnings.append("low_confidence")

    return DoubanParsedRow(
        row_index=0,
        raw_fragment=block.strip(),
        title=title,
        status=status,
        authors=authors,
        rating=rating,
        comment=comment,
        tags=tags,
        read_date=read_date,
        marked_date=marked_date,
        confidence=confidence,
        warnings=warnings,
    )


def parse_douban_paste(raw_input: str) -> DoubanParseResult:
    if not raw_input or not raw_input.strip():
        return DoubanParseResult(rows=[], warnings=["empty_input"])

    compact_rows = _parse_compact_page_rows(raw_input)
    if compact_rows:
        return DoubanParseResult(rows=compact_rows)

    blocks = _split_blocks(raw_input)
    rows: list[DoubanParsedRow] = []
    global_warnings: list[str] = []

    for block in blocks:
        row = _parse_block(block)
        if row is not None:
            row.row_index = len(rows)
            rows.append(row)

    if not rows:
        global_warnings.append("no_books_found")

    return DoubanParseResult(rows=rows, warnings=global_warnings)
