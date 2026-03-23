from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from markitdown import MarkItDown


@dataclass
class ParsedSection:
    section_type: str | None
    heading: str | None
    order: int
    text: str


def extract_text_from_file(path: str) -> str:
    """Extract normalized text from a file path.

    Uses markitdown, which supports PDFs and many other file types.
    """
    md = MarkItDown()
    result = md.convert(path)
    # markitdown returns Markdown; we store it as raw_text for now.
    return (result.text_content or "").strip()


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def naive_split_into_sections(markdown_text: str) -> list[ParsedSection]:
    """Best-effort sectioning based on Markdown headings.

    This is intentionally naive for MVP. It gives you:
      - stable anchors for citations
      - a place to attach claims

    Later upgrades: use a PDF-aware sectioner + page mapping.
    """
    lines = markdown_text.splitlines()
    sections: list[ParsedSection] = []

    cur_heading = None
    cur_level = None
    buf: list[str] = []

    def flush(order: int):
        nonlocal buf, cur_heading
        text = "\n".join(buf).strip()
        if text:
            sections.append(
                ParsedSection(
                    section_type=_infer_section_type(cur_heading),
                    heading=cur_heading,
                    order=order,
                    text=text,
                )
            )
        buf = []

    order = 0
    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            flush(order)
            order += 1
            cur_level = len(m.group(1))
            cur_heading = m.group(2).strip()
            continue
        buf.append(line)

    flush(order)
    return sections


def _infer_section_type(heading: str | None) -> str | None:
    if not heading:
        return None
    h = heading.lower()
    if "abstract" in h:
        return "abstract"
    if "introduction" in h or "background" in h:
        return "introduction"
    if "method" in h or "materials" in h:
        return "methods"
    if "result" in h:
        return "results"
    if "discussion" in h:
        return "discussion"
    if "conclusion" in h:
        return "conclusion"
    return "other"
