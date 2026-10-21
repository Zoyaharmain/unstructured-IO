"""Regression tests for resume structural grouping and reading order fixes.

Covers:
1. ANANDKUMAR & PrakashRout: wrapped education lines alternating between lanes
2. Diyara Sinha: 2-column tabular education layout (qualification + college)
3. AdityaSharma: 3-column employment layout (title + bullets + dates)
4. Narendra Reddy Daddanala: multiple dated roles under employment history
5. Ravikanth Pendyala: separate consulting engagements
6. NikitaChaudhary CV: isolated bullet artifacts and wrapped degree lines
"""
import pytest
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock
from local_api.services.record_relationships import degree_families, field_kinds
from local_api.services.resume_structure import (
    entry_groups,
    reviewed_education_groups,
    reviewed_employment_groups,
    employment_start,
)


def _elem(text, page=1, y=0.1, x=0.1, bold=False):
    return ExtractedElement(
        type='NarrativeText',
        text=text,
        page_number=page,
        metadata={
            'pdf_source_lines': [
                {
                    'start': 0,
                    'end': len(text),
                    'bbox': [x, y, x + 0.4, y + 0.015],
                    'bold': bold,
                    'font_size': 10.0,
                }
            ]
        },
    )


def _block(idx, text, lane='left', page=1):
    return SectionBlock(
        source_element_index=idx,
        start=0,
        end=len(text),
        text=text,
        page_number=page,
        lane=lane,
        assignment='semantic',
        reason='source',
        reviewed_by_llm=True,
    )


def test_degree_families_handles_dotted_abbreviations_and_schooling():
    assert degree_families('M. Tech in Biotechnology') == {'master'}
    assert degree_families('B. Tech in Computer Science') == {'bachelor'}
    assert degree_families('Ph. D in Physics') == {'doctorate'}
    assert degree_families('Basic Schooling') == {'secondary'}
    assert degree_families('12th and 10th Grade') == {'higher_secondary', 'secondary'}


def test_education_table_row_alignment():
    """Diyara Sinha pattern: qualification and institution on the same visual row across columns."""
    texts = [
        'M. Tech, Biotechnology',
        'Padmashree Dr. D.Y. Patil University',
        'B. Tech, Biotechnology',
        'ICFAI-Institute of Science & Technology',
        'Basic Schooling',
        'Convent of Jesus & Mary',
    ]
    # pairs on same y: (0, 1) at y=0.20, (2, 3) at y=0.25, (4, 5) at y=0.30
    y_coords = [0.20, 0.20, 0.25, 0.25, 0.30, 0.30]
    x_coords = [0.10, 0.50, 0.10, 0.50, 0.10, 0.50]
    lanes = ['left', 'right', 'left', 'right', 'left', 'right']

    elements = [_elem(t, y=y, x=x) for t, y, x in zip(texts, y_coords, x_coords)]
    blocks = [_block(i, t, lane=l) for i, (t, l) in enumerate(zip(texts, lanes))]

    groups = reviewed_education_groups(blocks, elements)
    assert len(groups) == 3
    assert groups[0]['block_indices'] == [0, 1]
    assert groups[1]['block_indices'] == [2, 3]
    assert groups[2]['block_indices'] == [4, 5]


def test_education_wrapped_degree_and_bullet_artifact():
    """NikitaChaudhary CV & ANANDKUMAR pattern: wrapped lines and bullet artifacts."""
    texts = [
        ' • ',
        '2018 – 2020 | MBA, Finance & Marketing | Bharati Vidyapeeth Institute',
        'Pune | GPA: 8.0',
        '2015 – 2018 | BA, Management | Bhopal School of Social Sciences | 70%',
    ]
    y_coords = [0.10, 0.15, 0.17, 0.22]
    elements = [_elem(t, y=y) for t, y in zip(texts, y_coords)]
    blocks = [
        _block(0, texts[0], lane='wide'),
        _block(1, texts[1], lane='wide'),
        _block(2, texts[2], lane='left'),  # wrapped line in different lane
        _block(3, texts[3], lane='left'),
    ]

    groups = reviewed_education_groups(blocks, elements)
    assert len(groups) == 2
    # The stray bullet block 0 is ignored; block 2 attaches to block 1
    assert groups[0]['block_indices'] == [1, 2]
    assert groups[1]['block_indices'] == [3]


def test_employment_three_column_alignment():
    """AdityaSharma pattern: col1=title/company, col2=bullets, col3=dates."""
    texts = [
        'Senior Data Architect',
        'AT&T Inc.',
        'October 2025 - Present',
        'Proposed migration plan to Azure cloud',
        'Managed 11+ folks as subject lead',
        'Data Engineering Manager',
        'PepsiCo',
        'December 2022 - September 2025',
        'Built data pipelines for SAP migration',
    ]
    # Job 1: title(y=0.10, x=0.06), co(y=0.12, x=0.06), date(y=0.12, x=0.70), bullets(y=0.14..0.16, x=0.30)
    # Job 2: title(y=0.25, x=0.06), co(y=0.27, x=0.06), date(y=0.27, x=0.70), bullets(y=0.29, x=0.30)
    y_coords = [0.10, 0.12, 0.12, 0.14, 0.16, 0.25, 0.27, 0.27, 0.29]
    x_coords = [0.06, 0.06, 0.70, 0.30, 0.30, 0.06, 0.06, 0.70, 0.30]
    lanes = ['left', 'left', 'right', 'wide', 'wide', 'left', 'left', 'right', 'wide']

    elements = [_elem(t, y=y, x=x) for t, y, x in zip(texts, y_coords, x_coords)]
    blocks = [_block(i, t, lane=l) for i, (t, l) in enumerate(zip(texts, lanes))]

    groups = reviewed_employment_groups(blocks, elements)
    assert len(groups) == 2
    assert groups[0]['block_indices'] == [0, 1, 2, 3, 4]
    assert groups[1]['block_indices'] == [5, 6, 7, 8]


def test_employment_bulleted_roles_separate():
    """Narendra Reddy Daddanala pattern: multiple roles with dates under history."""
    texts = [
        'Synechron Technologies (Client: Wells Fargo), Lead Operations Manager, April 2016 – May 2017, Bangalore',
        'Wipro Technologie, Lead Administrator, November 2015 – March 2016, Bangalore',
    ]
    y_coords = [0.50, 0.55]
    elements = [_elem(t, y=y) for t, y in zip(texts, y_coords)]
    blocks = [_block(i, t) for i, t in enumerate(texts)]

    groups = reviewed_employment_groups(blocks, elements)
    assert len(groups) == 2
    assert groups[0]['block_indices'] == [0]
    assert groups[1]['block_indices'] == [1]


def test_employment_consulting_engagements_not_skipped_by_project_title():
    """Ravikanth Pendyala pattern: Project Manager is a job title, not a project description header."""
    texts = [
        'CSI Global  Senior Business Analyst, HSBC APAC | Feb 2025  Present',
        'Role Focus: Business Analysis & Solutions Engineering',
        'Project Manager & QA Lead, UMB Kansas | Dec 2021  Feb 2023',
        'Role Focus: Project Management & QA Leadership',
        'Project Manager | Nov 2017  Nov 2018',
        'Role Focus: Project Delivery & Cards Consulting',
    ]
    y_coords = [0.10, 0.12, 0.25, 0.27, 0.40, 0.42]
    elements = [_elem(t, y=y) for t, y in zip(texts, y_coords)]
    blocks = [_block(i, t) for i, t in enumerate(texts)]

    groups = reviewed_employment_groups(blocks, elements)
    assert len(groups) == 3
    assert groups[0]['block_indices'] == [0, 1]
    assert groups[1]['block_indices'] == [2, 3]
    assert groups[2]['block_indices'] == [4, 5]

