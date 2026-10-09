"""
Role: Render a structured report to a PDF file.
Description: Takes a title, a subtitle and a list of blocks (headings,
paragraphs, bullets, tables) and writes an A4 PDF with reportlab. The text
content lives in report_text.py so this module stays generic.
Author: Bor
"""
import logging
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle)

log = logging.getLogger(__name__)

TABLE_FONT_SIZE = 8


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        'title': base['Title'],
        'subtitle': ParagraphStyle(
            'subtitle', parent=base['Normal'], fontSize=10,
            textColor=colors.grey, alignment=1, spaceAfter=14),
        'h1': base['Heading2'],
        'h2': base['Heading3'],
        'body': ParagraphStyle(
            'body', parent=base['BodyText'], fontSize=9.5, leading=13),
        'cell': ParagraphStyle(
            'cell', parent=base['BodyText'], fontSize=TABLE_FONT_SIZE,
            leading=10),
    }


def _table(rows: list[list[str]], styles: dict, widths: list[float] | None):
    cells = [[Paragraph(str(c), styles['cell']) for c in row] for row in rows]
    table = Table(cells, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dfe6ee')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table


def _flowables(blocks: list[tuple], styles: dict) -> list:
    flow = []
    for block in blocks:
        kind = block[0]
        if kind in ('h1', 'h2', 'body'):
            flow.append(Paragraph(block[1], styles[kind]))
        elif kind in ('bullets', 'numbered'):
            items = [ListItem(Paragraph(t, styles['body'])) for t in block[1]]
            bullet = 'bullet' if kind == 'bullets' else '1'
            flow.append(
                ListFlowable(items, bulletType=bullet, leftIndent=16))
        elif kind == 'table':
            widths = block[2] if len(block) > 2 else None
            flow.append(_table(block[1], styles, widths))
        else:
            raise ValueError('Unknown block type: %s' % kind)
        flow.append(Spacer(1, 6))
    return flow


def write_report(
        out_path: Path, title: str, subtitle: str, blocks: list[tuple]
        ) -> Path:
    """Write the report to out_path and return the path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4, title=title, author='Bor',
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm)
    story = [Paragraph(title, styles['title']),
             Paragraph(subtitle, styles['subtitle'])]
    story.extend(_flowables(blocks, styles))
    doc.build(story)
    log.info('Wrote %s', out_path)
    return out_path
