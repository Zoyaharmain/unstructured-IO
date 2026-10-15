"""Public PDF-only interface. Detection and classification remain upstream code."""
from pathlib import Path
from typing import Any


def partition_pdf(filename: str | Path | None = None, *, file=None, **settings: Any):
    """Return upstream Element objects using hi_res exclusively.

    Accepts the original PDF keyword settings, except chunking and alternate strategies.
    A missing inference dependency raises rather than falling back to fast or ocr_only.
    """
    if settings.pop('strategy', 'hi_res') != 'hi_res':
        raise ValueError('Only strategy="hi_res" is supported')
    if settings.get('chunking_strategy') is not None:
        raise ValueError('Chunking is outside the scope of this PDF port')
    import unstructured_inference  # noqa: F401 -- fail before upstream strategy fallback
    from ._vendor.partition.pdf import partition_pdf as upstream_partition_pdf

    return upstream_partition_pdf(
        filename=str(filename) if filename is not None else None,
        file=file, strategy='hi_res', **settings,
    )


def extract_pdf(filename: str | Path | None = None, *, file=None, **settings: Any) -> list[dict]:
    """Return original serialized elements plus a one-based document reading_order.

    Coordinates remain in metadata.coordinates, with original pixel space and dimensions.
    No text, geometry, classification or metadata corrections are applied.
    """
    return [dict(element.to_dict(), reading_order=index)
            for index, element in enumerate(partition_pdf(filename, file=file, **settings), 1)]
