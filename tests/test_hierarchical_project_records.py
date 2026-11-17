"""Tests for hierarchical numbering-aware project record detection.

Validates the 12 mandatory project scenarios (A through L):
A: 1 project with 10 numbered description steps -> 1 project record, 10 description items.
B: 2 genuine numbered projects, each with 4 numbered description steps -> 2 project records.
C: 4 genuine projects numbered 1–4 -> 4 distinct project records.
D: Description numbering restarting at 1 inside every project -> 2 project records without false splits.
E: Numbered description lines extracted as bold PDF Title elements -> boldness/Title alone never creates a new project.
F: Numbered description steps spanning pages -> 1 project record preserved across pages.
G: Project title and description merged into one extraction element -> title and description cleanly separated.
H: Nested numbering such as 1, 1.1, 1.2, 2 -> 2 projects with sub-bullets aggregated.
I: Project descriptions with short noun phrases -> grouped as description, not separate projects.
J: Project headings containing action verbs -> recognized as sequential project headings.
K: Abdul Shukoor extraction fixture -> 23 projects detected, 10 Param Info projects sequential with descriptions attached.
L: Full API pipeline test (`/api/v1/resume/sections` and `/api/v1/resume/schema`) -> 1 project with all 4 steps in description.
"""
import json
import os
import pytest
from fastapi.testclient import TestClient
from local_api.app import app
from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionBlock, SectionRequest
from local_api.services.resume_sections import detect_sections
from local_api.services.resume_structure import entry_groups
from local_api.services.project_fields import project_fields
from local_api.schemas.mapping import ReviewedSchemaMappingRequest
from local_api.services.schema_mapping import map_schema
from local_api.services.project_hierarchy import (
    is_project_description_step,
    detect_project_records,
    resolve_ambiguous_project_span
)

ABDUL_FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "real_resumes", "Abdul Shukoor.extraction.json"
)


def _make_fixture(lines, types=None, pages=None, bboxes=None, bolds=None):
    elements, blocks = [], []
    for i, t in enumerate(lines):
        el_t = types[i] if types and i < len(types) else ('Title' if i == 0 else 'ListItem')
        pg = pages[i] if pages and i < len(pages) else 1
        bold = bolds[i] if bolds and i < len(bolds) else (i == 0)
        bbox = bboxes[i] if bboxes and i < len(bboxes) else [0.1, 0.05 + i * 0.04, 0.85, 0.08 + i * 0.04]
        meta = {'pdf_source_lines': [{'start': 0, 'end': len(t), 'bbox': bbox, 'bold': bold}]}
        elements.append(ExtractedElement(type=el_t, text=t, page_number=pg, metadata=meta))
        blocks.append(SectionBlock(
            source_element_index=i, start=0, end=len(t), text=t,
            page_number=pg, assignment='semantic', lane='source', reason='fixture'
        ))
    return elements, blocks


def test_scenario_a_one_project_ten_numbered_description_steps():
    """Scenario A: One project with 10 numbered description steps -> 1 project record, 10 description items."""
    lines = [
        "Project 1: Search Engine Infrastructure",
        "1. Designed query parsing and tokenization pipeline in C++.",
        "2. Built inverted indexer with dynamic delta-encoded posting lists.",
        "3. Implemented BM25 relevance scoring algorithm for rank ordering.",
        "4. Optimized memory usage by 30% through zero-copy buffer pools.",
        "5. Added prefix search and fuzzy matching using Levenshtein automata.",
        "6. Handled real-time document mutations and concurrent garbage collection.",
        "7. Integrated with Apache ZooKeeper for distributed consensus.",
        "8. Deployed multi-node cluster across AWS EC2 instances with Terraform.",
        "9. Configured Prometheus metrics and Grafana dashboards for cluster alerts.",
        "10. Authored comprehensive architectural specifications and runbooks."
    ]
    elements, blocks = _make_fixture(lines)
    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 1, f"Expected 1 project record, got {len(groups)}"

    indices = groups[0]['block_indices']
    assert indices == list(range(len(lines))), "All source spans must be retained"

    title, description = project_fields([blocks[i] for i in indices], elements)
    assert title == "Search Engine Infrastructure"
    assert description is not None

    desc_lines = [line.strip() for line in description.splitlines() if line.strip()]
    assert len(desc_lines) == 10, f"Expected 10 description statements, got {len(desc_lines)}"
    for n in range(1, 11):
        assert any(l.startswith(f"{n}.") for l in desc_lines), f"Missing numbered step {n} in description"


def test_scenario_b_two_numbered_projects_each_four_steps():
    """Scenario B: 2 genuine numbered projects, each with 4 numbered description steps -> 2 project records."""
    lines = [
        "Project 1: Cloud Storage Service",
        "1. Designed blob store with multi-part upload protocol.",
        "2. Implemented erasure coding for disaster resilience.",
        "3. Automated disk compaction and garbage collection.",
        "4. Sharded metadata database across three availability zones.",
        "Project 2: Machine Learning Serving Gateway",
        "1. Containerized PyTorch models with TensorRT optimization.",
        "2. Built dynamic request batching queue with Redis.",
        "3. Implemented canary rollout deployment in Kubernetes.",
        "4. Reduced 99th percentile inference latency to under 15ms."
    ]
    elements, blocks = _make_fixture(lines)
    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 2, f"Expected exactly 2 project records, got {len(groups)}"

    t1, d1 = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    t2, d2 = project_fields([blocks[i] for i in groups[1]['block_indices']], elements)
    assert "Cloud Storage Service" in t1
    assert "Machine Learning Serving Gateway" in t2
    assert d1 and all(f"{n}." in d1 for n in range(1, 5))
    assert d2 and all(f"{n}." in d2 for n in range(1, 5))


def test_scenario_c_four_genuine_projects_numbered_1_to_4():
    """Scenario C: 4 genuine projects numbered 1–4 -> 4 distinct project records."""
    titles = [
        "Distributed KV Storage",
        "High-Throughput Message Queue",
        "Automated Machine Learning Pipeline",
        "API Gateway & Service Mesh"
    ]
    lines = [f"{i+1}. {title}" for i, title in enumerate(titles)]
    bolds = [True] * len(lines)
    types = ['Title'] * len(lines)
    elements, blocks = _make_fixture(lines, types=types, bolds=bolds)

    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 4, f"Expected 4 distinct project records, got {len(groups)}"

    for k, g in enumerate(groups):
        t, d = project_fields([blocks[i] for i in g['block_indices']], elements)
        assert titles[k].lower() in t.lower(), f"Project {k+1} title mismatch: {t!r} vs {titles[k]!r}"


def test_scenario_d_description_numbering_restarting_at_1():
    """Scenario D: Description numbering restarting at 1 inside every project -> 2 project records."""
    lines = [
        "1. E-Commerce Platform",
        "1. Designed reactive checkout frontend with TypeScript.",
        "2. Integrated Stripe Payment Intents and webhooks.",
        "2. Real-Time Telemetry Dashboard",
        "1. Ingested OpenTelemetry trace data into ClickHouse.",
        "2. Built interactive dashboard panels for latency metrics."
    ]
    types = ['Title', 'ListItem', 'ListItem', 'Title', 'ListItem', 'ListItem']
    bolds = [True, False, False, True, False, False]
    elements, blocks = _make_fixture(lines, types=types, bolds=bolds)

    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 2, f"Expected 2 project records, got {len(groups)}"

    t1, d1 = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    t2, d2 = project_fields([blocks[i] for i in groups[1]['block_indices']], elements)
    assert "E-Commerce Platform" in t1
    assert "1. Designed" in d1 and "2. Integrated" in d1
    assert "Real-Time Telemetry Dashboard" in t2
    assert "1. Ingested" in d2 and "2. Built" in d2


def test_scenario_e_numbered_description_lines_as_bold_title_elements():
    """Scenario E: Numbered description lines extracted as bold PDF Title elements -> must not create new projects."""
    lines = [
        "Project 1: Mobile Banking App",
        "1. Implemented biometric FaceID authentication in Swift.",
        "2. Built offline SQLite ledger synchronization protocol.",
        "3. Integrated zero-knowledge proof for fraud prevention."
    ]
    # Extraction artifact: Unstructured extracted every numbered bullet as bold Title!
    types = ['Title', 'Title', 'Title', 'Title']
    bolds = [True, True, True, True]
    elements, blocks = _make_fixture(lines, types=types, bolds=bolds)

    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 1, f"Expected 1 project record despite bold/Title elements, got {len(groups)}"

    t, d = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    assert "Mobile Banking App" in t
    assert "1. Implemented" in d
    assert "2. Built" in d
    assert "3. Integrated" in d


def test_scenario_f_description_spanning_two_pages():
    """Scenario F: Description spanning two pages -> 1 project record preserved across pages."""
    lines = [
        "Project 1: Cloud Migration Initiative",
        "1. Audited on-premises VM inventory and resource utilization.",
        "2. Built containerization specs with Dockerfiles.",
        "3. Automated AWS VPC peering and transit gateway routing.",
        "4. Migrated 40 relational databases to Amazon Aurora PostgreSQL.",
        "5. Cut over traffic using Route53 weighted DNS records."
    ]
    pages = [1, 1, 1, 2, 2, 2]
    elements, blocks = _make_fixture(lines, pages=pages)

    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 1, f"Expected 1 project record spanning pages, got {len(groups)}"

    indices = groups[0]['block_indices']
    assert len(indices) == len(lines), "All blocks across both pages must belong to the project"

    title, description = project_fields([blocks[i] for i in indices], elements)
    assert title == "Cloud Migration Initiative"
    assert "1. Audited" in description
    assert "4. Migrated" in description
    assert "5. Cut over" in description


def test_scenario_g_merged_title_and_description_in_one_element():
    """Scenario G: Project title and description merged into one extraction element."""
    lines = [
        "Project 1: Search Console Infrastructure. Designed query parsing and inverted indexer with delta encoding."
    ]
    elements, blocks = _make_fixture(lines, types=['Title'], bolds=[True])
    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 1

    title, description = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    assert "Search Console Infrastructure" in title
    assert description and "Designed query parsing and inverted indexer" in description


def test_scenario_h_nested_numbering_sub_bullets():
    """Scenario H: Nested numbering such as 1, 1.1, 1.2, 2 -> 2 projects with nested sub-bullets."""
    lines = [
        "1. Identity Provider Service",
        "1.1. Implemented OAuth2 and OIDC authorization code flow.",
        "1.2. Added WebAuthn hardware token authentication support.",
        "2. Billing Gateway Service",
        "2.1. Integrated Stripe webhook listeners with idempotency keys.",
        "2.2. Automated tax calculation using TaxJar REST endpoints."
    ]
    types = ['Title', 'ListItem', 'ListItem', 'Title', 'ListItem', 'ListItem']
    bolds = [True, False, False, True, False, False]
    elements, blocks = _make_fixture(lines, types=types, bolds=bolds)

    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 2, f"Expected 2 projects, got {len(groups)}"

    t1, d1 = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    t2, d2 = project_fields([blocks[i] for i in groups[1]['block_indices']], elements)
    assert "Identity Provider Service" in t1
    assert "1.1." in d1 and "1.2." in d1
    assert "Billing Gateway Service" in t2
    assert "2.1." in d2 and "2.2." in d2


def test_scenario_i_short_noun_phrase_descriptions():
    """Scenario I: Project descriptions with short noun phrases under a project header."""
    lines = [
        "Project: Edge Gateway Acceleration",
        "1. Database migration.",
        "2. Monitoring dashboards.",
        "3. Alert routing rules."
    ]
    elements, blocks = _make_fixture(lines)
    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 1, f"Expected 1 project record, got {len(groups)}"

    t, d = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    assert "Edge Gateway Acceleration" in t
    assert "Database migration" in d
    assert "Monitoring dashboards" in d
    assert "Alert routing rules" in d


def test_scenario_j_project_headings_with_action_verbs():
    """Scenario J: Project headings containing action verbs (e.g. '10. Created Power pages...')."""
    lines = [
        "9. Copilot Bot Assistant",
        "1. Integrated LLM completions with Azure OpenAI endpoints.",
        "10. Created Power pages for enterprise client portal",
        "1. Built data modeling schema in Microsoft Dataverse."
    ]
    elements, blocks = _make_fixture(lines)
    groups = entry_groups(blocks, 'projects', elements)
    assert len(groups) == 2, f"Expected 2 projects, got {len(groups)}"

    t1, d1 = project_fields([blocks[i] for i in groups[0]['block_indices']], elements)
    t2, d2 = project_fields([blocks[i] for i in groups[1]['block_indices']], elements)
    assert "Copilot Bot Assistant" in t1
    assert "Created Power pages" in t2


def test_scenario_k_abdul_shukoor_fixture_end_to_end():
    """Scenario K: Abdul Shukoor extraction fixture end-to-end verification."""
    assert os.path.exists(ABDUL_FIXTURE_PATH), f"Fixture not found: {ABDUL_FIXTURE_PATH}"
    with open(ABDUL_FIXTURE_PATH) as f:
        raw_data = json.load(f)
    raw_elements = raw_data if isinstance(raw_data, list) else raw_data['elements']
    elements = [ExtractedElement(**e) for e in raw_elements]

    req = SectionRequest(elements=elements)
    res = detect_sections(req)
    proj_sec = next(s for s in res.sections if s.category == 'projects')

    # Hierarchical detection must detect all 23 projects in Abdul Shukoor
    assert len(proj_sec.entries) == 23, f"Expected 23 project entries in Abdul Shukoor, got {len(proj_sec.entries)}"

    # Top 10 Param Info projects must have sequential titles and descriptions attached
    first_10 = proj_sec.entries[:10]
    expected_top_10 = [
        "Government Relations Kiosk Automation",
        "MOBARO Results Data Processing Automation",
        "Risk Assessment Framework",
        "Arabic Contract Automation Solution",
        "IT Loan Devices Tracking System",
        "Email-Driven Data Extraction & Excel Automation",
        "Machine Availability & RPA Alerting Framework",
        "Access Governance & Environment Management",
        "Copilot",
        "Created Power pages",
    ]
    for i, exp in enumerate(expected_top_10):
        t, d = project_fields([proj_sec.blocks[idx] for idx in first_10[i].block_indices], elements)
        assert exp.lower() in t.lower(), f"Project {i+1} mismatch: {t!r} vs {exp!r}"


def test_scenario_l_full_api_pipeline_numbered_steps():
    """Scenario L: Full API pipeline test (/api/v1/resume/sections and /api/v1/resume/schema)."""
    client = TestClient(app)
    payload = {
        'elements': [
            {'type': 'Title', 'text': 'PROJECTS', 'page_number': 1, 'metadata': {}},
            {'type': 'Title', 'text': 'Project 1: Search Engine Infrastructure', 'page_number': 1, 'metadata': {}},
            {'type': 'ListItem', 'text': '1. Designed query parsing in C++.', 'page_number': 1, 'metadata': {}},
            {'type': 'ListItem', 'text': '2. Built inverted indexer with delta encoding.', 'page_number': 1, 'metadata': {}},
            {'type': 'ListItem', 'text': '3. Implemented BM25 ranking algorithm.', 'page_number': 1, 'metadata': {}},
            {'type': 'ListItem', 'text': '4. Optimized memory usage by 30%.', 'page_number': 1, 'metadata': {}}
        ]
    }

    # 1. Test /api/v1/resume/sections/local
    res = client.post('/api/v1/resume/sections/local', json=payload)
    assert res.status_code == 200, f"Section endpoint failed: {res.text}"
    sec_data = res.json()
    proj_sec = next(s for s in sec_data['sections'] if s['category'] == 'projects')

    # Must be exactly 1 entry and exactly 1 logical block in UI
    assert len(proj_sec['entries']) == 1, f"Expected 1 project entry, got {len(proj_sec['entries'])}"
    assert len(proj_sec.get('logical_blocks', [])) == 1, f"Expected 1 logical block, got {len(proj_sec.get('logical_blocks', []))}"

    # 2. Test /api/v1/resume/schema
    schema_req = {'elements': payload['elements'], 'sections': sec_data}
    schema_res = client.post('/api/v1/resume/schema', json=schema_req)
    assert schema_res.status_code == 200, f"Schema endpoint failed: {schema_res.text}"
    sdata = schema_res.json()
    projects = sdata['data']['projects']

    # Must be exactly 1 project record with all 4 numbered steps in description
    assert len(projects) == 1, f"Expected 1 schema project record, got {len(projects)}"
    assert projects[0]['name'] == 'Search Engine Infrastructure'
    desc = projects[0]['description']
    assert desc is not None
    assert "1. Designed query parsing in C++." in desc
    assert "2. Built inverted indexer with delta encoding." in desc
    assert "3. Implemented BM25 ranking algorithm." in desc
    assert "4. Optimized memory usage by 30%." in desc


def test_llm_fallback_ambiguous_span_resolution():
    """Verify LLM fallback classifications: NEW_PROJECT, PROJECT_DESCRIPTION_CONTINUATION, UNRESOLVED."""
    assert resolve_ambiguous_project_span("1. Built scalable microservices.") == 'PROJECT_DESCRIPTION_CONTINUATION'
    assert resolve_ambiguous_project_span("Project 1: Distributed Storage") == 'NEW_PROJECT'
    assert resolve_ambiguous_project_span("Uncertain ambiguous fragment xyz") in {'UNRESOLVED', 'PROJECT_DESCRIPTION_CONTINUATION'}
