"""Central test tiers and the default no-provider safety boundary."""
from __future__ import annotations

import pytest


MOCK_PROVIDER_MODULES = {
    "test_flagged_review_resolution.py",
    "test_hierarchical_five_runner.py",
    "test_llm_batch_audit.py",
    "test_llm_section_review.py",
    "test_local_block_inspection.py",
    "test_pipeline200_root_causes.py",
    "test_review_chunking.py",
    "test_single_resume_check.py",
}

API_MODULES = {
    "test_local_api.py",
    "test_text_extraction.py",
    "test_verification_ui.py",
}

API_TESTS = {
    "test_schema_mapping.py::test_real_http_contract_and_validation",
    "test_hierarchical_schema.py::test_query_endpoint_reuses_mapping_and_rejects_invalid_paths",
    "test_section_subschemas.py::test_nested_contract_is_returned_by_http_and_has_discoverable_definition",
    "test_resume_sections.py::test_api_groups_before_optional_manual_verification",
    "test_resume_sections.py::test_missing_local_model_is_clear_unit",
}

SLOW_EXTRACTION_TESTS = {
    "test_interface.py::InterfaceTests::test_actual_pdf_stream",
    "test_local_api.py::test_direct_extraction_parity",
    "test_text_extraction.py::test_pdf_real",
    "test_text_extraction.py::test_scanned_pdf_ocr_real",
    "test_text_extraction.py::test_image_ocr_real",
}


def _matches(item: pytest.Item, tests: set[str]) -> bool:
    relative = item.nodeid.removeprefix("tests/")
    return any(relative == name or relative.startswith(name + "[") for name in tests)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Assign one primary tier based on the operation the test executes."""
    for item in items:
        module = item.path.name
        if item.get_closest_marker("provider"):
            pass
        elif _matches(item, SLOW_EXTRACTION_TESTS):
            item.add_marker(pytest.mark.extraction_slow)
        elif "engine" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.local_model)
        elif module in MOCK_PROVIDER_MODULES:
            item.add_marker(pytest.mark.mock_provider)
        elif module in API_MODULES or _matches(item, API_TESTS):
            item.add_marker(pytest.mark.api_integration)
        else:
            item.add_marker(pytest.mark.unit)
        tiers = {name for name in ("unit", "api_integration", "extraction_slow",
                                   "local_model", "mock_provider", "provider")
                 if item.get_closest_marker(name) is not None}
        if len(tiers) != 1:
            raise pytest.UsageError(f"{item.nodeid} must have exactly one test tier; found {sorted(tiers)}")


@pytest.fixture(autouse=True)
def disable_live_provider_by_default(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """Ordinary tiers start without provider credentials or review enablement."""
    if request.node.get_closest_marker("provider") is not None:
        return
    for key in ("DEEPSEEK_API_KEY", "DEEPSEEK_REVIEW_ENABLED", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
