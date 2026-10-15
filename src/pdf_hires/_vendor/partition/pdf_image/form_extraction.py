from __future__ import annotations

from typing import IO

from pdf_hires._vendor.documents.elements import Element, FormKeysValues


def run_form_extraction(
    filename: str,
    file: IO[bytes],
    model_name: str,
    elements: list[Element],
    skip_table_regions: bool,
) -> list[FormKeysValues]:
    raise NotImplementedError("Form extraction not yet available.")
