"""Deterministic date parsing, precision preservation, and non-overlapping experience calculation."""
from __future__ import annotations

import re
from datetime import datetime, timezone, date
from typing import Literal
from local_api.services.standardization.contracts import StandardizationWarning

MONTH_MAP: dict[str, int] = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

CURRENT_PATTERNS = re.compile(
    r"^(?:present|current(?:ly)?(?: working)?|till date|till now|now|ongoing|onwards|to date|till present)$",
    re.I
)

# Month Names or Abbreviations
MONTH_REGEX = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"


def parse_date_string(
    raw_date: str | None,
    field_context: str = "date",
    *, reference_date: datetime | None = None,
) -> tuple[str | None, Literal["year", "month_year", "day"] | None, bool, list[StandardizationWarning]]:
    """Parse a date string into ISO-8601 format, preserving precision.

    Returns:
        (iso_date, precision, is_current, warnings)
    """
    warnings: list[StandardizationWarning] = []
    if not raw_date:
        return None, None, False, warnings

    text = raw_date.strip()
    # A shortened year does not establish a century. Preserve it in audit only.
    short = re.fullmatch(r'(' + MONTH_REGEX + r")[.\s‘’'-]+(\d{2})", text, re.I)
    if short:
        warnings.append(StandardizationWarning(field=field_context, warning_type='two_digit_year_interpretation',
            severity='warning', original_value=raw_date, normalized_value=None,
            basis='Two-digit year does not establish its century; no normalized date inferred.',
            message='Two-digit year requires source verification before normalization.'))
        return None, None, False, warnings

    if not text:
        return None, None, False, warnings

    # Repair whitespace only inside a four-digit year, not the source value.
    def compact_year(match):
        value=re.sub(r'\s+','',match.group())
        return value if len(value)==4 else match.group()
    compact=re.sub(r'(?<!\d)(?:19|20)\d?\s+\d{1,2}(?!\d)',compact_year,text)
    if compact != text:
        warnings.append(StandardizationWarning(field=field_context,warning_type='date_spacing_normalization',
            severity='warning',original_value=raw_date,normalized_value=compact,applied=True,
            basis='Whitespace removed only inside a four-digit 19xx/20xx year in a date field.',
            message='Possible extraction spacing in year normalized; original source retained.'))
        text=compact
    # Check for current employment indicators
    if CURRENT_PATTERNS.match(text):
        return None, None, True, warnings

    # Match Month + Year: "Aug 2022", "August 2022", "Aug-2022", "Aug/2022", "Aug. 2022"
    m_my = re.match(r"^(" + MONTH_REGEX + r")[,.\s\-\/]*([1-9]\d{3})$", text, re.I)
    if m_my:
        month_str, year_str = m_my.group(1), m_my.group(2)
        month_num = MONTH_MAP.get(month_str.lower()[:3])
        if month_num:
            iso_str = f"{year_str}-{month_num:02d}"
            return iso_str, "month_year", False, warnings

    # Match Year + Month: "2022 Aug", "2022-Aug", "2022/Aug"
    m_ym = re.match(r"^([1-9]\d{3})[.\s\-\/]+(" + MONTH_REGEX + r")$", text, re.I)
    if m_ym:
        year_str, month_str = m_ym.group(1), m_ym.group(2)
        month_num = MONTH_MAP.get(month_str.lower()[:3])
        if month_num:
            iso_str = f"{year_str}-{month_num:02d}"
            return iso_str, "month_year", False, warnings

    # Match Numeric MM/YYYY or MM-YYYY or YYYY-MM
    m_num_my = re.match(r"^(0?[1-9]|1[0-2])[\-\/]([1-9]\d{3})$", text)
    if m_num_my:
        month_num = int(m_num_my.group(1))
        year_str = m_num_my.group(2)
        return f"{year_str}-{month_num:02d}", "month_year", False, warnings

    m_iso_ym = re.match(r"^([1-9]\d{3})[\-\/](0?[1-9]|1[0-2])$", text)
    if m_iso_ym:
        year_str = m_iso_ym.group(1)
        month_num = int(m_iso_ym.group(2))
        return f"{year_str}-{month_num:02d}", "month_year", False, warnings

    # Match Year only: "2022"
    m_yr = re.match(r"^([1-9]\d{3})$", text)
    if m_yr:
        return m_yr.group(1), "year", False, warnings

    # Match ISO Date YYYY-MM-DD
    m_iso_d = re.match(r"^([1-9]\d{3})[\-\/](0?[1-9]|1[0-2])[\-\/](0?[1-9]|[12]\d|3[01])$", text)
    if m_iso_d:
        y, m, d = int(m_iso_d.group(1)), int(m_iso_d.group(2)), int(m_iso_d.group(3))
        try: date(y,m,d)
        except ValueError: return _invalid_date(raw_date,field_context)
        return f"{y:04d}-{m:02d}-{d:02d}", "day", False, warnings

    # Match Day Month Year: "15 Aug 2022", "15-Aug-2022"
    m_dmy = re.match(r"^(0?[1-9]|[12]\d|3[01])[.\s\-\/]+(" + MONTH_REGEX + r")[,.\s\-\/]*([1-9]\d{3})$", text, re.I)
    if m_dmy:
        day_str, month_str, year_str = m_dmy.group(1), m_dmy.group(2), m_dmy.group(3)
        month_num = MONTH_MAP.get(month_str.lower()[:3])
        if month_num:
            try: date(int(year_str),month_num,int(day_str))
            except ValueError: return _invalid_date(raw_date,field_context)
            return f"{year_str}-{month_num:02d}-{int(day_str):02d}", "day", False, warnings

    # Numeric ambiguity check: e.g. "05/06/2022"
    m_ambig = re.match(r"^(\d{1,2})[\-\/](\d{1,2})[\-\/]([1-9]\d{3})$", text)
    if m_ambig:
        v1, v2, year = int(m_ambig.group(1)), int(m_ambig.group(2)), m_ambig.group(3)
        if v1 <= 12 and v2 <= 12 and v1 != v2:
            warnings.append(
                StandardizationWarning(
                    field=field_context,
                    warning_type="ambiguous_numeric_date",
                    severity="warning",
                    original_value=raw_date,
                    normalized_value=raw_date,
                    message=f"Ambiguous date '{raw_date}': cannot distinguish MM/DD/YYYY from DD/MM/YYYY without source evidence."
                )
            )
            return None, None, False, warnings
        elif v1 == v2 and 1 <= v1 <= 12:
            return f"{year}-{v1:02d}-{v2:02d}", "day", False, warnings
        elif v1 > 12 and v2 <= 12:
            # DD/MM/YYYY
            try: date(int(year),v2,v1)
            except ValueError: return _invalid_date(raw_date,field_context)
            return f"{year}-{v2:02d}-{v1:02d}", "day", False, warnings
        elif v2 > 12 and v1 <= 12:
            # MM/DD/YYYY
            try: date(int(year),v1,v2)
            except ValueError: return _invalid_date(raw_date,field_context)
            return f"{year}-{v1:02d}-{v2:02d}", "day", False, warnings

    # Unparseable / unrecognized format
    warnings.append(
        StandardizationWarning(
            field=field_context,
            warning_type="unrecognized_date_format",
            severity="review_required",
            original_value=raw_date,
            normalized_value=raw_date,
            message=f"Date '{raw_date}' could not be safely parsed to canonical ISO format; preserved raw."
        )
    )
    return None, None, False, warnings


def date_to_month_index(iso_date: str | None, precision: str | None, is_end: bool = False) -> int | None:
    """Convert an ISO date string to absolute month index (year * 12 + month)."""
    if not iso_date:
        return None
    parts = iso_date.split("-")
    try:
        year = int(parts[0])
    except ValueError:
        return None

    if len(parts) >= 2:
        month = int(parts[1])
    else:
        month = 12 if is_end else 1
    return year * 12 + month


def calculate_non_overlapping_experience(
    experience_records: list[dict],
    reference_date: datetime | None = None,
) -> tuple[float | None, bool, list[StandardizationWarning]]:
    """Calculate total professional experience in years, merging overlapping intervals.

    Returns:
        (total_years, overlap_detected, warnings)
    """
    warnings: list[StandardizationWarning] = []
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)
    intervals = []
    for idx, rec in enumerate(experience_records):
        start_iso, end_iso = rec.get('start_date_iso'), rec.get('end_date_iso')
        start_prec, end_prec = rec.get('start_date_precision'), rec.get('end_date_precision')
        current = rec.get('is_current', False)
        _, _, status = calculated_duration(start_iso, end_iso, start_prec, end_prec, current, reference_date)
        if status not in {'calculated','estimated_year_precision'}:
            if status == 'invalid_dates':
                warnings.append(StandardizationWarning(field=f'experience[{idx}].dates',
                    warning_type='invalid_date_order', severity='review_required',
                    original_value={'start_date': start_iso, 'end_date': end_iso},
                    message='Dates are reversed or in the future; excluded from experience calculation.'))
            continue
        # Month precision establishes boundaries only at month granularity.
        # Use matching first-of-month boundaries for approximate interval union.
        if status == 'estimated_year_precision':
            # Year labels define a coarse computational interval, not actual
            # January employment dates. Source dates remain year-only.
            intervals.append((date(int(start_iso[:4]),1,1),date(reference_date.year if current else int(end_iso[:4]),1,1)))
            continue
        precise = start_prec == 'day' and (current or end_prec == 'day')
        start = date.fromisoformat(start_iso if precise else start_iso[:7] + '-01')
        if current:
            end = reference_date.date() if precise else reference_date.date().replace(day=1)
        else:
            end = date.fromisoformat(end_iso if precise else end_iso[:7] + '-01')
        if start > end:
            continue
        intervals.append((start, end))

    if not intervals:
        return None, False, warnings

    # Sort by elapsed interval boundaries
    intervals.sort(key=lambda x: (x[0], x[1]))

    overlap_detected = False
    merged: list[tuple[date, date]] = []
    for interval in intervals:
        if not merged:
            merged.append(interval)
            continue

        prev_start, prev_end = merged[-1]
        curr_start, curr_end = interval

        if curr_start <= prev_end:
            # Touching elapsed intervals merge without implying an overlap.
            overlap_detected = overlap_detected or curr_start < prev_end
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(interval)

    total_months = 0.0
    for start, end in merged:
        _, months, days = calendar_elapsed(start, end)
        total_months += months + days / (365.2425 / 12)
    total_years = round(total_months / 12.0, 1)

    if overlap_detected:
        warnings.append(
            StandardizationWarning(
                field="total_experience_years",
                warning_type="experience_overlap_resolved",
                severity="info",
                original_value=None,
                normalized_value=total_years,
                message=f"Overlapping employment periods were merged to prevent double-counting: total non-overlapping duration is {total_years} years."
            )
        )

    return total_years, overlap_detected, warnings



def _invalid_date(raw, field):
    return None, None, False, [StandardizationWarning(field=field,warning_type='invalid_calendar_date',
        severity='warning',original_value=raw,message='Date is not valid in the calendar; no duration calculated.')]


def calculated_duration(start_iso, end_iso, start_precision, end_precision, current, reference_date):
    if not start_iso or (not end_iso and not current):
        return None, None, 'insufficient_dates'
    if start_precision == 'year' or (end_precision == 'year' and not current):
        start_year=int(start_iso[:4]);end_year=reference_date.year if current else int(end_iso[:4])
        if start_year>end_year or end_year>reference_date.year or start_year>reference_date.year:
            return None,None,'invalid_dates'
        for value,precision in ((start_iso,start_precision),(None if current else end_iso,end_precision)):
            if value and precision != 'year' and value>reference_date.date().isoformat()[:len(value)]:
                return None,None,'invalid_dates'
        years=end_year-start_year
        text=f"Approximately {years} year{'s' if years!=1 else ''}" if years else 'Less than 1 year (year precision)'
        return text,years*12,'estimated_year_precision'
    start=date_to_month_index(start_iso,start_precision)
    end=reference_date.year*12+reference_date.month if current else date_to_month_index(end_iso,end_precision)
    today=reference_date.year*12+reference_date.month
    if start is None or end is None or start>end or end>today:
        return None,None,'invalid_dates'
    if start_precision == 'day' and end_precision == 'day' and not current and start_iso>end_iso:
        return None,None,'invalid_dates'
    if not current and end_precision == 'day' and end_iso>reference_date.date().isoformat():
        return None,None,'invalid_dates'
    if start_precision == 'day' and start_iso>reference_date.date().isoformat():
        return None,None,'invalid_dates'
    if start_precision == 'day' and (current or end_precision == 'day'):
        text, months, _ = calendar_elapsed(date.fromisoformat(start_iso),
            reference_date.date() if current else date.fromisoformat(end_iso))
        return text, months, 'calculated'
    months=end-start
    years,remainder=divmod(months,12)
    parts=[]
    if years:parts.append(f"{years} year{'s' if years!=1 else ''}")
    if remainder:parts.append(f"{remainder} month{'s' if remainder!=1 else ''}")
    return ' '.join(parts) or '0 months',months,'calculated'


def calendar_elapsed(first, last):
    """Completed calendar months plus remaining days; no inclusive endpoint bonus."""
    import calendar
    months = (last.year - first.year) * 12 + last.month - first.month
    if last.day < first.day: months -= 1
    year = first.year + (first.month - 1 + months) // 12
    month = (first.month - 1 + months) % 12 + 1
    anchor = date(year, month, min(first.day, calendar.monthrange(year, month)[1]))
    days = (last - anchor).days
    years, remainder = divmod(months, 12)
    parts = [f"{amount} {unit}{'s' if amount != 1 else ''}"
             for amount, unit in ((years, 'year'), (remainder, 'month'), (days, 'day')) if amount]
    return ' '.join(parts) or '0 days', months, days
