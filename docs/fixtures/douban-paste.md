# Douban Paste Fixtures: Assumptions

## Source Format

These fixtures represent text copied from Douban reading list pages by selecting and copying in a browser. The format is **plain text**, not HTML, because most users copy visible rendered content rather than raw DOM.

## Two Distinct Formats

Based on representative copied-page samples, there are two different paste formats:

### Format A: List Page

The most common paste format. When copying from a reading list page (想读/读过/在读), the content is minimal:

```
我想读的书(71)

读书主页 书评 笔记 在读 想读 读过 作者 豆列 书单 设置 | 豆瓣主页

按时间排序 · 按评分排序 · 按标题排序1-30 / 71

grid

list

怎样选择成长股2026-05-02

Showstopper! the Breakneck Race to Create Windows NT and the N...2026-04-27
```

Key characteristics:
- **Title + Date only** (e.g., `书名YYYY-MM-DD` or `书名 YYYY-MM-DD`)
- **No metadata block** (no author, publisher, ISBN, etc.)
- **No status markers** (status implied by page context)
- **No ratings or tags** in list view
- **Navigation chrome** present: page header, sort options, pagination
- **Truncated titles** with `...`
- **Private entries** marked with `(不公开)`
- **Date format**: Always `YYYY-MM-DD`, may have space before date

### Format B: Detail/Review Page (Synthetic Fixtures)

When copying from a book detail page or review view, more metadata is visible:

```
思考，快与慢
作者: [美] 丹尼尔·卡尼曼
出版社: 中信出版社
出版年: 2012-7
页数: 418
定价: 69.00元
装帧: 平装
ISBN: 9787508633557
豆瓣评分: 8.1

我读过这本书 2019-03-15
标签: 心理学、认知、决策
评论: 重新理解了直觉和理性的关系。
```

Key characteristics:
- **Full metadata block** (author, publisher, ISBN, etc.)
- **Explicit status markers** (`我读过这本书`, `我想读这本书`)
- **Tags and comments** visible
- **Douban platform rating** present

## List Page Parser Rules

For Format A (the real-world format), the parser must:

1. **Detect page context**: Extract status from page title
   - `想读的书(N)` → status: `want`, date field: `marked_date`
   - `读过的书(N)` → status: `read`, date field: `read_date`
   - `在读的书(N)` → status: `reading`, date field: `read_date`

2. **Parse book entries**: Match pattern `TITLE + DATE`
   - Date regex: `YYYY-MM-DD`
   - May have optional space between title and date
   - Title may end with `...` (truncated) or `(不公开)` (private)

3. **Filter noise**: Skip non-book lines
   - Navigation: `读书主页`, `书评`, `笔记`, etc.
   - Sort/view controls: `按时间排序`, `grid`, `list`
   - Pagination: `<前页 1 2 3 后页>`
   - Page indicators: `1-30 / 71`
   - User profile: `sample_user`
   - Empty lines

4. **Handle edge cases**:
   - Books with same title in different languages (e.g., `从0到1` and `Zero to One`)
   - Same date for multiple books (batch import)
   - Titles containing numbers (e.g., `1453`, `算法导论（原书第2版）`)

## Status Markers (Format B only)

| Marker | Status | Date field |
|--------|--------|------------|
| `我读过这本书` | `read` | `read_date` |
| `我想读这本书` | `want` | `marked_date` |
| `我在读这本书` | `reading` | `read_date` (started) |

## Confidence Scoring Assumptions

| Condition | Confidence |
|-----------|------------|
| List page format: title + date extracted | 0.95 |
| List page format: truncated title (`...`) | 0.9 |
| Detail page format: all core fields present | 0.95 |
| Detail page: missing rating | 0.9 |
| Detail page: missing status marker | 0.3 |
| Any format: no date extracted | 0.5 |

## Warning Types

| Warning | Meaning |
|---------|---------|
| `title_truncated` | Title ends with `...`, full title unknown |
| `missing_rating` | No douban rating extracted |
| `missing_isbn` | No ISBN in source text |
| `missing_status` | No read/want/reading marker found |
| `missing_authors` | No author line detected |
| `missing_date` | No date extracted |
| `low_confidence` | Overall confidence below threshold |

## Open Questions

These need user input or real sample verification:

1. **HTML paste**: Do users ever paste raw HTML? If so, we need HTML fixtures.
2. **Douban URL presence**: When does a pasted block include the book URL?
3. **Rating format**: Does Douban ever show half-stars in pasted text?
4. **Date format variance**: Are dates always `YYYY-MM-DD` or can they be `YYYY年M月D日`?
5. **Tag separator**: Is `、` always the separator, or can it be `,` or spaces?
6. **Multi-author format**: How are multiple authors separated?
7. **Edition info**: Does `(第X版)` appear in the title or as a separate field?
8. **Detail page paste**: Does anyone paste the detailed metadata block format?

## Confirmed Observations

1. **Primary format is list page**: Users paste from 想读/读过/在读 list views, not detail pages.
2. **Format is title + date**: Minimal metadata in list view.
3. **Status from page context**: Page title indicates status (想读的书, 读过的书).
4. **Navigation chrome included**: Header, sort options, pagination lines are pasted.
5. **Bilingual entries**: Users may have same book in Chinese and English (e.g., `从0到1` and `Zero to One`).
6. **Truncated titles**: Long titles show `...` in list view.
7. **Private entries**: Some entries marked `(不公开)`.

## Fixture Inventory

### Format A: List Page

| File | Rows | Purpose |
|------|------|---------|
| `want_list_page_raw.txt` | 30 | Representative want list page paste |
| `want_list_page_expected.json` | 30 | Expected parse of want list |
| `read_list_page_raw.txt` | 26 | Representative read list page paste |
| `read_list_page_expected.json` | 26 | Expected parse of read list |

### Format B: Detail Page (Synthetic Fixtures)

| File | Rows | Purpose |
|------|------|---------|
| `read_list_raw.txt` | 5 | Clean read list with full metadata |
| `read_list_expected.json` | 5 | Expected parse of detailed read list |
| `want_list_raw.txt` | 4 | Clean want list with full metadata |
| `want_list_expected.json` | 4 | Expected parse of detailed want list |
| `mixed_noisy_raw.txt` | 6 valid + noise | Mixed statuses, UI noise, edge cases |
| `mixed_noisy_expected.json` | 6 | Expected parse with warnings |
