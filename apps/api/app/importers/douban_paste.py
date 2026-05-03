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
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_LOOSE_RATING_PATTERN = re.compile(r"(?<!\d)(10(?:\.0)?|[0-9](?:\.\d)?)\s*分")

_NOISE_PATTERNS = [
    re.compile(r"^\s*赞\s+回复\s*$"),
    re.compile(r"^\s*修改\s+删除\s*$"),
    re.compile(r"^\s*加载更多"),
    re.compile(r"^(我的读书|我在读的书|我想读的书|我读过的书|豆瓣读书搜索|书名 作者 ISBN|搜索|按时间排序|按评分排序|按标题排序|grid|list|读书主页|书评|笔记|豆列|书单|设置|已读|在读|想读|广告位招租|联系我们|---)"),
    re.compile(r"^\d+-\d+\s*/\s*\d+"),
    re.compile(r"^(纸质版|加入购书单|去看电子版|<前页|> 我的读书主页|按标签量排序|按首字母排序)"),
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
        if re.match(r"^\s*我(在读|想读|读过)的书\(\d+\)\s*$", line.strip()):
            current = []
            continue
        if re.match(r"^\s*(赞\s+回复|修改\s+删除)\s*$", line.strip()):
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


def _looks_like_structured_douban_paste(raw_input: str) -> bool:
    return any(
        marker in raw_input
        for marker in (
            "我在读的书",
            "我想读的书",
            "我读过的书",
            "我读过这本书",
            "我想读这本书",
            "我在读这本书",
            "修改    删除",
            "赞 回复",
        )
    )


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


def _status_from_loose_text(text: str) -> tuple[str | None, str | None]:
    status = None
    if re.search(r"(我读过这本书|读过|已读|read\b)", text, re.IGNORECASE):
        status = "read"
    elif re.search(r"(我想读这本书|想读|want\b)", text, re.IGNORECASE):
        status = "want"
    elif re.search(r"(我在读这本书|在读|reading\b)", text, re.IGNORECASE):
        status = "reading"

    date_match = _DATE_PATTERN.search(text)
    return status, date_match.group(0) if date_match else None


def _confidence_for_fields(
    status: str | None,
    authors: list[str],
    rating: float | None,
    base: float,
) -> tuple[float, list[str]]:
    warnings: list[str] = []
    confidence = base

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

    return confidence, warnings


def _row_from_candidate(
    raw_fragment: str,
    title: str,
    status: str | None = None,
    authors: list[str] | None = None,
    rating: float | None = None,
    read_date: str | None = None,
    marked_date: str | None = None,
    base_confidence: float = 0.7,
) -> DoubanParsedRow | None:
    title = title.strip(" \t\n\r，。,.、/|")
    if not title or _is_noise(title):
        return None

    authors = [a.strip() for a in authors or [] if a.strip()]
    confidence, warnings = _confidence_for_fields(status, authors, rating, base_confidence)
    return DoubanParsedRow(
        row_index=0,
        raw_fragment=raw_fragment.strip(),
        title=title,
        status=status,
        authors=authors,
        rating=rating,
        read_date=read_date,
        marked_date=marked_date,
        confidence=confidence,
        warnings=warnings,
    )


def _parse_slash_line(line: str) -> DoubanParsedRow | None:
    if "/" not in line:
        return None

    parts = [part.strip() for part in line.split("/") if part.strip()]
    if not parts:
        return None

    title = parts[0]
    status, date = _status_from_loose_text(line)
    read_date = date if status == "read" else None
    marked_date = date if status in {"reading", "want"} else None
    rating = None
    authors: list[str] = []

    rating_match = _LOOSE_RATING_PATTERN.search(line)
    if rating_match:
        rating = float(rating_match.group(1))

    for part in parts[1:]:
        if _DATE_PATTERN.search(part) or _LOOSE_RATING_PATTERN.search(part):
            continue
        if re.search(r"(出版社|出版|中信|上海|北京|读过|想读|在读)", part, re.IGNORECASE):
            continue
        if re.search(r"[A-Za-z]", part) or len(part) <= 12:
            authors = [part]
            break

    return _row_from_candidate(
        line,
        title,
        status=status,
        authors=authors,
        rating=rating,
        read_date=read_date,
        marked_date=marked_date,
        base_confidence=0.78,
    )


def _parse_plain_english_status_line(line: str) -> DoubanParsedRow | None:
    match = re.match(
        r"^(?P<body>.+?)\s+(?P<status>read|reading|want)\s+(?P<date>\d{4}-\d{2}-\d{2})$",
        line.strip(),
        re.IGNORECASE,
    )
    if not match:
        return None

    body = match.group("body").strip()
    status = match.group("status").lower()
    date = match.group("date")
    read_date = date if status == "read" else None
    marked_date = date if status in {"reading", "want"} else None

    title = body
    authors: list[str] = []
    tokens = body.split()
    if len(tokens) >= 5 and re.fullmatch(r"[A-Z][A-Za-z.]*", tokens[-3]) and re.fullmatch(r"[A-Z]\.", tokens[-2]) and re.fullmatch(r"[A-Z][A-Za-z.]*", tokens[-1]):
        authors = [" ".join(tokens[-3:])]
        title = " ".join(tokens[:-3])
    else:
        author_match = re.search(r"\s+([A-Z][A-Za-z.]+(?:\s+[A-Z][A-Za-z.]+)+)$", body)
        if author_match:
            authors = [author_match.group(1).strip()]
            title = body[: author_match.start()].strip()

    return _row_from_candidate(
        line,
        title,
        status=status,
        authors=authors,
        marked_date=marked_date,
        read_date=read_date,
        base_confidence=0.66,
    )


def _parse_simple_title_line(line: str) -> DoubanParsedRow | None:
    stripped = line.strip()
    if not stripped or _is_noise(stripped):
        return None
    if len(stripped) > 80 or re.search(r"[#{}<>]|https?://", stripped):
        return None
    if re.search(r"(nav|footer|header|random|广告)", stripped, re.IGNORECASE):
        return None
    if re.search(r"(作者:|标签:|评论:|豆瓣评分:)", stripped):
        return None
    if _DATE_PATTERN.fullmatch(stripped):
        return None

    return _row_from_candidate(stripped, stripped, base_confidence=0.38)


def _parse_free_text_rows(raw_input: str) -> list[DoubanParsedRow]:
    rows: list[DoubanParsedRow] = []
    seen_titles: set[str] = set()

    def add(row: DoubanParsedRow | None) -> None:
        if row is None or row.title in seen_titles:
            return
        row.row_index = len(rows)
        rows.append(row)
        seen_titles.add(row.title)

    for match in re.finditer(r"(?:读完了?|已读|读过)[^《]{0,8}《([^》]+)》", raw_input):
        add(_row_from_candidate(match.group(0), match.group(1), status="read", base_confidence=0.7))

    for match in re.finditer(
        r"想读\s+([A-Z][A-Za-z0-9'’:.!?,& -]{2,}?)(?=。|，|,|\.|$)",
        raw_input,
    ):
        add(_row_from_candidate(match.group(0), match.group(1), status="want", base_confidence=0.62))

    for match in re.finditer(r"另一本是\s+([^，。]+?)(?:\s+作者\s*([^，。]+))?(?=。|，|$)", raw_input):
        title = match.group(1).strip()
        author = match.group(2).strip() if match.group(2) else ""
        add(
            _row_from_candidate(
                match.group(0),
                title,
                authors=[author] if author else [],
                base_confidence=0.56,
            )
        )

    if rows:
        return rows

    non_noise_lines = [line.strip() for line in raw_input.splitlines() if line.strip() and not _is_noise(line)]
    for line in non_noise_lines:
        add(_parse_slash_line(line))
        add(_parse_plain_english_status_line(line))

    if rows:
        return rows

    if len(non_noise_lines) > 1:
        for line in non_noise_lines:
            add(_parse_simple_title_line(line))

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

        loose_status, loose_date = _status_from_loose_text(line)
        if loose_status:
            status = status or loose_status
            if loose_date:
                if loose_status in {"want", "reading"}:
                    marked_date = marked_date or loose_date
                else:
                    read_date = read_date or loose_date

        m = _RATING_PATTERN.search(line)
        if m:
            try:
                rating = float(m.group(1))
            except ValueError:
                pass

        m = _AUTHOR_PATTERN.search(line)
        if m:
            authors = [a.strip() for a in m.group(1).split(",")]
        elif not authors and "/" in line and not _DATE_PATTERN.search(line):
            first_part = line.split("/")[0].strip()
            if first_part and not _is_noise(first_part):
                authors = [a.strip() for a in re.split(r"[、,，]", first_part) if a.strip()]

        m = _TAG_PATTERN.search(line)
        if m:
            tags = [t.strip() for t in re.split(r"[、,，\s]+", m.group(1)) if t.strip()]

        m = _COMMENT_PATTERN.search(line)
        if m:
            comment = m.group(1).strip()

    confidence, warnings = _confidence_for_fields(status, authors, rating, 0.95)

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

    if rows and (_looks_like_structured_douban_paste(raw_input) or len(rows) > 1):
        return DoubanParseResult(rows=rows, warnings=global_warnings)

    free_text_rows = _parse_free_text_rows(raw_input)
    if free_text_rows:
        return DoubanParseResult(rows=free_text_rows)

    if not rows:
        global_warnings.append("no_books_found")

    return DoubanParseResult(rows=rows, warnings=global_warnings)
