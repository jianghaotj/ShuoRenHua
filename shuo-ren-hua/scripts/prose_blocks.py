"""A conservative Markdown subset, with character (not byte) source positions.

This is not a CommonMark implementation. Unsupported HTML, front matter and
math are isolated and reported as coverage gaps, never treated as prose.
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field


PARSER_VERSION = "conservative-markdown-2.0"
HAN_COUNT_VERSION = "cjk-ranges-15.1-v1"
# Explicit ranges, including extensions A-I and compatibility ideographs.
HAN_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
              (0x20000, 0x2A6DF), (0x2A700, 0x2B73F), (0x2B740, 0x2B81F),
              (0x2B820, 0x2CEAF), (0x2CEB0, 0x2EBEF), (0x2EBF0, 0x2EE5F),
              (0x2F800, 0x2FA1F), (0x30000, 0x3134F), (0x31350, 0x323AF))


def han_count(value: str) -> int:
    return sum(any(lo <= ord(c) <= hi for lo, hi in HAN_RANGES) for c in value)


class SourceMap:
    def __init__(self, text: str):
        self.text = text
        self.lines = [0] + [m.end() for m in re.finditer("\n", text)]

    def point(self, offset: int) -> dict:
        index = bisect.bisect_right(self.lines, offset) - 1
        return {"offset": offset, "line": index + 1, "column": offset - self.lines[index] + 1}

    def location(self, start: int, end: int) -> dict:
        return {"start": self.point(start), "end": self.point(end)}


@dataclass
class Block:
    kind: str
    text: str
    positions: list[int]
    section: str
    after_structure: bool = False

    def span(self, start: int = 0, end: int | None = None) -> tuple[int, int]:
        end = len(self.text) if end is None else end
        return self.positions[start], self.positions[end - 1] + 1


@dataclass
class Parsed:
    blocks: list[Block] = field(default_factory=list)
    protected: list[dict] = field(default_factory=list)
    gaps: list[dict] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)


@dataclass
class Line:
    raw: str
    start: int
    content: str
    content_start: int
    quoted: bool


def _line(raw: str, start: int) -> Line:
    value = raw.rstrip("\r\n")
    prefix = re.match(r"^ {0,3}(?:> ?)+", value)
    cut = prefix.end() if prefix else 0
    return Line(raw, start, value[cut:], start + cut, bool(prefix))


def _table_cells(value: str) -> list[tuple[int, int]]:
    """Split only unescaped pipes outside matching inline code runs."""
    separators = []
    code_run = 0
    i = 0
    while i < len(value):
        if value[i] == "\\":
            i += 2
            continue
        if value[i] == "`":
            end = i + 1
            while end < len(value) and value[end] == "`":
                end += 1
            length = end - i
            if not code_run:
                code_run = length
            elif code_run == length:
                code_run = 0
            i = end
            continue
        if value[i] == "|" and not code_run:
            separators.append(i)
        i += 1
    if not separators:
        return []
    cuts = [-1] + separators + [len(value)]
    cells = [(a + 1, b) for a, b in zip(cuts, cuts[1:])]
    if cells and not value[cells[0][0]:cells[0][1]].strip():
        cells.pop(0)
    if cells and not value[cells[-1][0]:cells[-1][1]].strip():
        cells.pop()
    return cells


def _table_separator(value: str) -> bool:
    cells = _table_cells(value)
    return bool(cells) and all(re.fullmatch(r"\s*:?-+:?\s*", value[a:b]) for a, b in cells)


def _balanced(value: str, start: int, opening: str, closing: str) -> int | None:
    depth = 1
    i = start + 1
    while i < len(value):
        if value[i] == "\\":
            i += 2
            continue
        if value[i] == opening:
            depth += 1
        elif value[i] == closing:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _inline(value: str, positions: list[int], result: Parsed, source: SourceMap) -> str:
    chars = list(value)

    def mask(a: int, b: int, kind: str | None = None, gap: bool = False):
        if b <= a:
            return
        if kind:
            item = {"kind": kind, "location": source.location(positions[a], positions[b - 1] + 1)}
            (result.gaps if gap else result.protected).append(item)
        chars[a:b] = " " * (b - a)

    def cite(a: int, b: int, target: str, kind: str):
        result.citations.append({"target": target, "kind": kind,
                                 "location": source.location(positions[a], positions[b - 1] + 1)})

    i = 0
    while i < len(value):
        if chars[i] == " " and value[i] != " ":
            i += 1
            continue
        if value[i] == "\\" and i + 1 < len(value):
            if value[i:i + 2] in ("\\(", "\\["):
                closing = "\\)" if value[i + 1] == "(" else "\\]"
                end = value.find(closing, i + 2)
                end = len(value) if end < 0 else end + 2
                mask(i, end, "math_inline", True)
                i = end
                continue
            mask(i, i + 1)
            i += 2
            continue
        if value[i] == "`":
            run = re.match(r"`+", value[i:]).group()
            closing = re.search(r"(?<!`)" + re.escape(run) + r"(?!`)", value[i + len(run):])
            if closing:
                end = i + len(run) + closing.end()
                mask(i, end, "inline_code")
                i = end
                continue
        if value[i] == "$":
            # Deliberately broad isolation. Currency and unmatched dollars remain gaps.
            run = "$$" if value.startswith("$$", i) else "$"
            end = value.find(run, i + len(run))
            end = len(value) if end < 0 else end + len(run)
            mask(i, end, "math_or_dollar_delimiter", True)
            i = end
            continue
        if value.startswith("<!--", i):
            end = value.find("-->", i + 4)
            end = len(value) if end < 0 else end + 3
            mask(i, end, "html_comment", True)
            i = end
            continue
        if value[i] == "<":
            end = value.find(">", i + 1)
            if end >= 0:
                inner = value[i + 1:end]
                if re.match(r"(?:https?://|mailto:)", inner) or re.fullmatch(r"[^ <>@]+@[^ <>@]+", inner):
                    cite(i, end + 1, inner, "autolink")
                    mask(i, end + 1, "url_target")
                else:
                    mask(i, end + 1, "html_inline", True)
                i = end + 1
                continue
        if value[i] == "[":
            close = _balanced(value, i, "[", "]")
            if close is not None:
                if value[i + 1:close].startswith("^"):
                    cite(i, close + 1, value[i + 1:close], "footnote_marker")
                    mask(i, close + 1, "citation_marker")
                    i = close + 1
                    continue
                tail = close + 1
                if tail < len(value) and value[tail] == "(":
                    end = _balanced(value, tail, "(", ")")
                    if end is not None:
                        destination = value[tail + 1:end].strip()
                        target = re.match(r"<([^>]+)>|([^\s]+)", destination)
                        if target:
                            cite(tail + 1, end, target.group(1) or target.group(2), "link")
                        mask(i, i + 1)
                        mask(close, end + 1, "link_destination")
                        if i and value[i - 1] == "!":
                            mask(i - 1, i)
                        i += 1  # Label stays prose and may contain inline code/emphasis.
                        continue
                if tail < len(value) and value[tail] == "[":
                    end = value.find("]", tail + 1)
                    if end >= 0:
                        ref = value[tail + 1:end] or value[i + 1:close]
                        cite(tail, end + 1, "ref:" + ref.casefold(), "reference_link")
                        mask(i, i + 1)
                        mask(close, end + 1, "reference_target")
                        i += 1
                        continue
                # Shortcut references are ambiguous without a full resolver.
                result.gaps.append({"kind": "unresolved_bracket_or_shortcut_reference",
                                    "location": source.location(positions[i], positions[close] + 1)})
        url = re.match(r"https?://[^\s<>，。！？；、）\]\"']+", value[i:])
        if url:
            end = i + url.end()
            cite(i, end, url.group().rstrip(".,;:!?"), "bare_url")
            mask(i, end, "url_target")
            i = end
            continue
        if value[i] in "*_~" or value[i] in "\r\n":
            mask(i, i + 1)
        i += 1
    return "".join(chars)


def parse_markdown(text: str) -> Parsed:
    result = Parsed()
    source = SourceMap(text)
    lines = []
    cursor = 0
    for raw in text.splitlines(keepends=True):
        lines.append(_line(raw, cursor))
        cursor += len(raw)
    section = ""
    previous_kind = ""
    list_indent: int | None = None

    def region(kind: str, a: int, b: int, gap: bool = False):
        item = {"kind": kind, "location": source.location(lines[a].start,
                lines[b - 1].start + len(lines[b - 1].raw))}
        (result.gaps if gap else result.protected).append(item)

    def add(kind: str, segments: list[tuple[str, int]], boundary: bool = False):
        nonlocal previous_kind
        if not segments:
            return
        value = ""
        positions = []
        for part, start in segments:
            if positions:
                value += " "
                positions.append(positions[-1] + 1)
            value += part
            positions.extend(range(start, start + len(part)))
        if not positions:
            return
        clean = _inline(value, positions, result, source)
        if clean.strip():
            result.blocks.append(Block(kind, clean, positions, section, boundary))
        previous_kind = kind

    def special(index: int) -> bool:
        value = lines[index].content
        return bool(re.match(r"^\s*(?:#{1,6}\s|`{3,}|~{3,}|[-+*]\s|\d+[.)]\s|<[/!A-Za-z]|\$\$|\\\[|\[[^\]]+\]:)", value)
                    or re.fullmatch(r"\s*(?:[-*_]\s*){3,}", value)
                    or (index + 1 < len(lines) and _table_separator(lines[index + 1].content)))

    i = 0
    while i < len(lines):
        line = lines[i]
        value = line.content
        if not value.strip():
            i += 1
            continue
        if i == 0 and value.strip() in ("---", "+++"):
            delimiter = value.strip()
            j = i + 1
            while j < len(lines) and lines[j].content.strip() not in (delimiter, "..."):
                j += 1
            j = min(j + 1, len(lines))
            region("front_matter", i, j, True)
            previous_kind, i = "front_matter", j
            continue
        marker = re.match(r"^(\s*)(?:[-+*]|\d+[.)])\s+", value)
        fence_value = value[marker.end():] if marker else value
        fence = re.match(r"^\s*(`{3,}|~{3,})(.*)$", fence_value)
        if fence and not (fence.group(1)[0] == "`" and "`" in fence.group(2)):
            delimiter = fence.group(1)
            j = i + 1
            while j < len(lines):
                close = re.fullmatch(r"\s*(" + re.escape(delimiter[0]) + r"{" + str(len(delimiter)) + r",})\s*", lines[j].content)
                if close:
                    break
                j += 1
            closed = j < len(lines)
            j = min(j + 1, len(lines))
            region("fenced_code" if closed else "unclosed_fenced_code", i, j)
            previous_kind, i = "code", j
            continue
        if re.match(r"^\s*(?:\$\$|\\\[)", value):
            delimiter = "$$" if value.lstrip().startswith("$$") else "\\]"
            opening_size = 2
            if delimiter in value.lstrip()[opening_size:]:
                j = i + 1
            else:
                j = i + 1
                while j < len(lines) and delimiter not in lines[j].content:
                    j += 1
                j = min(j + 1, len(lines))
            region("math_block", i, j, True)
            previous_kind, i = "math", j
            continue
        html = re.match(r"^\s*<(?:!--|/?[A-Za-z][A-Za-z0-9-]*(?:\s|>|/))", value)
        if html:
            tag_match = re.match(r"^\s*<([A-Za-z][A-Za-z0-9-]*)", value)
            closing = "-->" if "<!--" in value else ("</" + tag_match.group(1) if tag_match else None)
            raw_block = "<!--" in value or bool(tag_match and tag_match.group(1).lower() in {"script", "style", "pre", "textarea"})
            j = i + 1
            if not (closing and closing.lower() in value.lower()):
                while j < len(lines) and (raw_block or lines[j].content.strip()):
                    current = lines[j].content
                    j += 1
                    if closing and closing.lower() in current.lower():
                        break
            region("html_block", i, j, True)
            previous_kind, i = "html", j
            continue
        reference = re.match(r"^\s{0,3}\[([^\]]+)\]:\s*(.*)$", value)
        if reference:
            target_match = re.match(r"<?([^ >\s]+)>?", reference.group(2))
            label = reference.group(1)
            result.citations.append({"target": ("^" + label[1:]) if label.startswith("^") else "ref:" + label.casefold(),
                                     "kind": "reference_definition",
                                     "location": source.location(line.content_start, line.content_start + len(value))})
            if target_match and not label.startswith("^"):
                result.citations.append({"target": target_match.group(1), "kind": "reference_destination",
                                         "location": source.location(line.content_start + reference.start(2), line.content_start + len(value))})
            region("footnote_definition" if label.startswith("^") else "reference_definition", i, i + 1, label.startswith("^"))
            previous_kind, i = "reference", i + 1
            continue
        if i + 1 < len(lines) and _table_separator(lines[i + 1].content) and _table_cells(value):
            j = i
            while j < len(lines) and _table_cells(lines[j].content):
                if j == i + 1:
                    region("table_separator", j, j + 1)
                else:
                    for a, b in _table_cells(lines[j].content):
                        add("table_cell", [(lines[j].content[a:b], lines[j].content_start + a)])
                j += 1
            previous_kind, i, list_indent = "table", j, None
            continue
        heading = re.match(r"^ {0,3}#{1,6}\s+(.*?)(?:\s+#+\s*)?$", value)
        if heading:
            section = heading.group(1).strip()
            add("heading", [(heading.group(1), line.content_start + heading.start(1))])
            previous_kind, i, list_indent = "heading", i + 1, None
            continue
        if i + 1 < len(lines) and re.fullmatch(r" {0,3}(?:=+|-+)\s*", lines[i + 1].content):
            section = value.strip()
            add("heading", [(value, line.content_start)])
            previous_kind, i, list_indent = "heading", i + 2, None
            continue
        if re.fullmatch(r"\s*(?:[-*_]\s*){3,}", value):
            region("thematic_break", i, i + 1)
            previous_kind, i, list_indent = "thematic_break", i + 1, None
            continue
        indent = len(value) - len(value.lstrip(" "))
        if marker:
            list_indent = marker.end()
            kind, cut = "list_item", marker.end()
        elif list_indent is not None and indent >= list_indent + 4:
            j = i + 1
            while j < len(lines) and (not lines[j].content.strip() or len(lines[j].content) - len(lines[j].content.lstrip(" ")) >= list_indent + 4):
                j += 1
            region("list_indented_code", i, j)
            previous_kind, i = "code", j
            continue
        elif list_indent is not None and indent >= list_indent:
            kind, cut = "list_item", min(indent, list_indent)
        elif (indent >= 4 or value.startswith("\t")) and list_indent is None:
            j = i + 1
            while j < len(lines) and (not lines[j].content.strip() or lines[j].content.startswith(("    ", "\t"))):
                j += 1
            region("indented_code", i, j)
            previous_kind, i = "code", j
            continue
        else:
            kind, cut, list_indent = ("quote" if line.quoted else "paragraph"), 0, None
        boundary = previous_kind in {"heading", "table", "list_item", "code", "quote", "html", "math", "thematic_break", "front_matter"}
        segments = [(value[cut:], line.content_start + cut)]
        j = i + 1
        while j < len(lines) and lines[j].content.strip() and not special(j):
            next_line = lines[j]
            if next_line.quoted != line.quoted:
                break
            next_indent = len(next_line.content) - len(next_line.content.lstrip(" "))
            if kind == "list_item" and next_indent >= (list_indent or 0) + 4:
                break
            if kind != "list_item" and next_indent >= 4:
                break
            # Lazy continuations belong to a list item until a real block boundary.
            next_cut = min(next_indent, list_indent or 0) if kind == "list_item" else 0
            segments.append((next_line.content[next_cut:], next_line.content_start + next_cut))
            j += 1
        add(kind, segments, boundary if kind in ("paragraph", "quote") else False)
        i = j
    return result
