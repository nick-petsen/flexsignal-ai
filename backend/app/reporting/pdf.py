from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 54
RIGHT_MARGIN = 54
TOP_MARGIN = 54
BOTTOM_MARGIN = 54
BODY_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
TITLE_SIZE = 16
HEADING_SIZE = 12
BODY_SIZE = 9
LINE_HEIGHT = 12
PARAGRAPH_GAP = 6
SECTION_GAP = 10
MAX_CHARS_PER_LINE = 94


def render_report_markdown_pdf_bytes(
    markdown_text: str,
    *,
    title: str | None = None,
) -> bytes:
    """Render caller-provided Markdown text into simple PDF bytes."""
    if not isinstance(markdown_text, str):
        raise TypeError("markdown_text must be a string")

    output = BytesIO()
    pdf = canvas.Canvas(
        output,
        pagesize=A4,
        pageCompression=0,
        invariant=1,
    )
    renderer = _PdfMarkdownRenderer(pdf)

    document_title = _resolve_title(markdown_text, title=title)
    renderer.add_title(document_title)
    for block in _parse_markdown(markdown_text):
        renderer.add_block(block)
    renderer.finish()
    return output.getvalue()


class _PdfMarkdownRenderer:
    def __init__(self, pdf: canvas.Canvas) -> None:
        self._pdf = pdf
        self._y = PAGE_HEIGHT - TOP_MARGIN

    def add_title(self, value: str) -> None:
        self._draw_wrapped(
            value,
            font_name=BOLD_FONT,
            font_size=TITLE_SIZE,
            line_height=18,
        )
        self._move_down(SECTION_GAP)

    def add_block(self, block: tuple[str, str]) -> None:
        kind, text = block
        if not text:
            self._move_down(PARAGRAPH_GAP)
            return

        if kind == "heading":
            self._move_down(SECTION_GAP)
            self._draw_wrapped(
                text,
                font_name=BOLD_FONT,
                font_size=HEADING_SIZE,
                line_height=14,
            )
            self._move_down(PARAGRAPH_GAP)
            return

        if kind == "subheading":
            self._move_down(PARAGRAPH_GAP)
            self._draw_wrapped(
                text,
                font_name=BOLD_FONT,
                font_size=BODY_SIZE,
                line_height=LINE_HEIGHT,
            )
            self._move_down(PARAGRAPH_GAP)
            return

        prefix = "- " if kind == "bullet" else ""
        self._draw_wrapped(
            text,
            prefix=prefix,
            font_name=BODY_FONT,
            font_size=BODY_SIZE,
            line_height=LINE_HEIGHT,
        )
        self._move_down(PARAGRAPH_GAP)

    def finish(self) -> None:
        self._pdf.showPage()
        self._pdf.save()

    def _draw_wrapped(
        self,
        text: str,
        *,
        font_name: str,
        font_size: int,
        line_height: int,
        prefix: str = "",
    ) -> None:
        width = MAX_CHARS_PER_LINE - len(prefix)
        lines = wrap(text, width=max(width, 24)) or [""]
        for index, line in enumerate(lines):
            line_prefix = prefix if index == 0 else "  " if prefix else ""
            self._draw_line(
                f"{line_prefix}{line}",
                font_name=font_name,
                font_size=font_size,
                line_height=line_height,
            )

    def _draw_line(
        self,
        text: str,
        *,
        font_name: str,
        font_size: int,
        line_height: int,
    ) -> None:
        if self._y < BOTTOM_MARGIN + line_height:
            self._pdf.showPage()
            self._y = PAGE_HEIGHT - TOP_MARGIN
        self._pdf.setFont(font_name, font_size)
        self._pdf.drawString(LEFT_MARGIN, self._y, text)
        self._y -= line_height

    def _move_down(self, amount: int) -> None:
        self._y -= amount
        if self._y < BOTTOM_MARGIN:
            self._pdf.showPage()
            self._y = PAGE_HEIGHT - TOP_MARGIN


def _resolve_title(markdown_text: str, *, title: str | None) -> str:
    if title and title.strip():
        return _plain_text(title)
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            return _plain_text(line[2:])
    return "FlexSignal AI report summary"


def _parse_markdown(markdown_text: str) -> Iterable[tuple[str, str]]:
    in_table = False
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            in_table = False
            yield "blank", ""
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            in_table = False
            yield "heading", _plain_text(line[3:])
            continue
        if line.startswith("### "):
            in_table = False
            yield "subheading", _plain_text(line[4:])
            continue
        if line.startswith("- "):
            in_table = False
            yield "bullet", _plain_text(line[2:])
            continue
        if _is_table_separator(line):
            continue
        if _is_table_row(line):
            cells = _table_cells(line)
            if cells == ["Field", "Value"]:
                in_table = True
                continue
            if len(cells) >= 2:
                in_table = True
                yield "bullet", f"{cells[0]}: {cells[1]}"
                continue
        kind = "bullet" if in_table else "paragraph"
        yield kind, _plain_text(line)


def _is_table_separator(line: str) -> bool:
    value = line.replace("|", "").replace("-", "").replace(":", "").strip()
    return not value and "|" in line and "-" in line


def _is_table_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|") and line.count("|") >= 2


def _table_cells(line: str) -> list[str]:
    return [_plain_text(cell.strip()) for cell in line.strip("|").split("|")]


def _plain_text(value: str) -> str:
    return (
        value.replace("\\|", "|")
        .replace("**", "")
        .replace("`", "")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )
