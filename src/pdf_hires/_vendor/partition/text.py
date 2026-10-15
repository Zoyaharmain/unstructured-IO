from __future__ import annotations

import copy
import re
from typing import IO, Any, Callable, Literal

from pdf_hires._vendor.cleaners.core import (
    auto_paragraph_grouper,
    clean_bullets,
)
from pdf_hires._vendor.documents.coordinates import CoordinateSystem
from pdf_hires._vendor.documents.elements import (
    Address,
    Element,
    ElementMetadata,
    EmailAddress,
    Footer,
    Header,
    ListItem,
    NarrativeText,
    Text,
    Title,
)
from pdf_hires._vendor.file_utils.encoding import read_txt_file
from pdf_hires._vendor.file_utils.model import FileType
from pdf_hires._vendor.nlp.patterns import PARAGRAPH_PATTERN, UNICODE_BULLETS_RE
from pdf_hires._vendor.partition.common.common import exactly_one
from pdf_hires._vendor.partition.common.metadata import apply_metadata, get_last_modified_date
from pdf_hires._vendor.partition.text_type import (
    is_bulleted_text,
    is_email_address,
    is_possible_narrative_text,
    is_possible_numbered_list,
    is_possible_title,
    is_us_city_state_zip,
)
from pdf_hires._vendor.telemetry import partition_runtime_telemetry




def element_from_text(
    text: str,
    coordinates: tuple[tuple[float, float], ...] | None = None,
    coordinate_system: CoordinateSystem | None = None,
) -> Element:
    if _is_in_header_position(coordinates, coordinate_system):
        return Header(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    elif _is_in_footer_position(coordinates, coordinate_system):
        return Footer(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    elif is_bulleted_text(text):
        clean_text = clean_bullets(text)
        return ListItem(
            text=clean_text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    elif is_email_address(text):
        return EmailAddress(text=text)
    elif is_us_city_state_zip(text):
        return Address(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    elif is_possible_numbered_list(text):
        return ListItem(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    elif is_possible_narrative_text(text):
        return NarrativeText(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    elif is_possible_title(text):
        return Title(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )
    else:
        return Text(
            text=text,
            coordinates=coordinates,
            coordinate_system=coordinate_system,
        )


# ================================================================================================
# HELPER FUNCTIONS
# ================================================================================================


def _get_height_percentage(
    coordinates: tuple[tuple[float, float], ...],
    coordinate_system: CoordinateSystem,
) -> float:
    avg_y = sum(coordinate[1] for coordinate in coordinates) / len(coordinates)
    return avg_y / coordinate_system.height


def _is_empty_bullet(text: str) -> bool:
    """Checks if input text is an empty bullet."""
    return bool(UNICODE_BULLETS_RE.match(text) and len(text) == 1)


def _is_in_footer_position(
    coordinates: tuple[tuple[float, float], ...] | None,
    coordinate_system: CoordinateSystem | None,
    threshold: float = 0.93,
) -> bool:
    """Checks to see if the position of the text indicates that the text belongs
    to a footer."""
    if coordinates is None or coordinate_system is None:
        return False

    height_percentage = _get_height_percentage(coordinates, coordinate_system)
    return height_percentage > threshold


def _is_in_header_position(
    coordinates: tuple[tuple[float, float], ...] | None,
    coordinate_system: CoordinateSystem | None,
    threshold: float = 0.07,
) -> bool:
    """Checks to see if the position of the text indicates that the text belongs to a header."""
    if coordinates is None or coordinate_system is None:
        return False

    height_percentage = _get_height_percentage(coordinates, coordinate_system)
    return height_percentage < threshold


