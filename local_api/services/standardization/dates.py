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
    # Apostrophes delimit explicitly shortened years; retain an inference warning.
    short = re.fullmatch(r'(' + MONTH_REGEX + r")[.\s‘’'-]+(\d{2})", text, re.I)
    if short:
        year = 2000 + int(short[2])
        if year > (reference_date or datetime.now(timezone.utc)).year:
            year -= 100
        warnings.append(StandardizationWarning(field=field_context, warning_type='two_digit_year_interpretation',
            severity='warning', original_value=raw_date, normalized_value=f'{year}-{MONTH_MAP[short[1].lower()[:3]]:02d}',
            basis='Most recent matching year not after the current UTC year; century requires review.',
            message='Two-digit year expanded using an explicit century policy.'))
        return f'{year}-{MONTH_MAP[short[1].lower()[:3]]:02d}', 'month_year', False, warnings

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
    m_my = re.match(r"^(" + MONTH_REGEX + r")[,.\s\-\/]*(19\d{2}|20\d{2})$", text, re.I)
    if m_my:
        month_str, year_str = m_my.group(1), m_my.group(2)
        month_num = MONTH_MAP.get(month_str.lower()[:3])
        if month_num:
            iso_str = f"{year_str}-{month_num:02d}"
            return iso_str, "month_year", False, warnings

    # Match Year + Month: "2022 Aug", "2022-Aug", "2022/Aug"
    m_ym = re.match(r"^(19\d{2}|20\d{2})[.\s\-\/]+(" + MONTH_REGEX + r")$", text, re.I)
    if m_ym:
        year_str, month_str = m_ym.group(1), m_ym.group(2)
        month_num = MONTH_MAP.get(month_str.lower()[:3])
        if month_num:
            iso_str = f"{year_str}-{month_num:02d}"
            return iso_str, "month_year", False, warnings

    # Match Numeric MM/YYYY or MM-YYYY or YYYY-MM
    m_num_my = re.match(r"^(0?[1-9]|1[0-2])[\-\/](19\d{2}|20\d{2})$", text)
    if m_num_my:
        month_num = int(m_num_my.group(1))
        year_str = m_num_my.group(2)
        return f"{year_str}-{month_num:02d}", "month_year", False, warnings

    m_iso_ym = re.match(r"^(19\d{2}|20\d{2})[\-\/](0?[1-9]|1[0-2])$", text)
    if m_iso_ym:
        year_str = m_iso_ym.group(1)
        month_num = int(m_iso_ym.group(2))
        return f"{year_str}-{month_num:02d}", "month_year", False, warnings

    # Match Year only: "2022"
    m_yr = re.match(r"^(19\d{2}|20\d{2})$", text)
    if m_yr:
        return m_yr.group(1), "year", False, warnings

    # Match ISO Date YYYY-MM-DD
    m_iso_d = re.match(r"^(19\d{2}|20\d{2})[\-\/](0?[1-9]|1[0-2])[\-\/](0?[1-9]|[12]\d|3[01])$", text)
    if m_iso_d:
        y, m, d = int(m_iso_d.group(1)), int(m_iso_d.group(2)), int(m_iso_d.group(3))
        try: date(y,m,d)
        except ValueError: return _invalid_date(raw_date,field_context)
        return f"{y:04d}-{m:02d}-{d:02d}", "day", False, warnings

    # Match Day Month Year: "15 Aug 2022", "15-Aug-2022"
    m_dmy = re.match(r"^(0?[1-9]|[12]\d|3[01])[.\s\-\/]+(" + MONTH_REGEX + r")[,.\s\-\/]*(19\d{2}|20\d{2})$", text, re.I)
    if m_dmy:
        day_str, month_str, year_str = m_dmy.group(1), m_dmy.group(2), m_dmy.group(3)
        month_num = MONTH_MAP.get(month_str.lower()[:3])
        if month_num:
            try: date(int(year_str),month_num,int(day_str))
            except ValueError: return _invalid_date(raw_date,field_context)
            return f"{year_str}-{month_num:02d}-{int(day_str):02d}", "day", False, warnings

    # Numeric ambiguity check: e.g. "05/06/2022"
    m_ambig = re.match(r"^(\d{1,2})[\-\/](\d{1,2})[\-\/](19\d{2}|20\d{2})$", text)
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
            severity="info",
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
    current_month_index = reference_date.year * 12 + reference_date.month

    intervals: list[tuple[int, int]] = []
    for idx, rec in enumerate(experience_records):
        start_iso = rec.get("start_date_iso")
        end_iso = rec.get("end_date_iso")
        start_prec = rec.get("start_date_precision")
        end_prec = rec.get("end_date_precision")
        is_curr = rec.get("is_current", False)

        if start_prec == 'year' or (end_prec == 'year' and not is_curr):
            continue
        start_m = date_to_month_index(start_iso, start_prec, is_end=False)
        if start_m is None:
            continue

        if is_curr:
            end_m = current_month_index
        else:
            end_m = date_to_month_index(end_iso, end_prec, is_end=True)
            if end_m is None:
                continue  # Missing end is not evidence of a one-month job.

        future_day = (start_prec == 'day' and start_iso > reference_date.date().isoformat()) or (
            not is_curr and end_prec == 'day' and end_iso and end_iso > reference_date.date().isoformat())
        if future_day or start_m > current_month_index or end_m > current_month_index or start_m > end_m:
            warnings.append(
                StandardizationWarning(
                    field=f"experience[{idx}].dates",
                    warning_type="invalid_date_order",
                    severity="warning",
                    original_value={"start_date": rec.get("raw_start_date"), "end_date": rec.get("raw_end_date")},
                    normalized_value={"start_date_iso": start_iso, "end_date_iso": end_iso},
                    message=f"Start date ({start_iso}) is after end date ({end_iso})."
                )
            )
            continue

        intervals.append((start_m, end_m))

    if not intervals:
        return None, False, warnings

    # Sort intervals by start month
    intervals.sort(key=lambda x: (x[0], x[1]))

    overlap_detected = False
    merged: list[tuple[int, int]] = []
    for interval in intervals:
        if not merged:
            merged.append(interval)
            continue

        prev_start, prev_end = merged[-1]
        curr_start, curr_end = interval

        if curr_start <= prev_end:
            overlap_detected = True
            # Overlapping or adjacent, extend
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(interval)

    total_months = sum((end - start + 1) for start, end in merged)
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
    if not start_iso or (not end_iso and not current) or start_precision == 'year' or (end_precision == 'year' and not current):
        return None, None, 'insufficient_dates'
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
        import calendar
        first=date.fromisoformat(start_iso)
        last=reference_date.date() if current else date.fromisoformat(end_iso)
        months=(last.year-first.year)*12+last.month-first.month
        if last.day<first.day:months-=1
        year=first.year+(first.month-1+months)//12
        month=(first.month-1+months)%12+1
        anchor=date(year,month,min(first.day,calendar.monthrange(year,month)[1]))
        days=(last-anchor).days
        years,remainder=divmod(months,12)
        parts=[]
        for amount,unit in [(years,'year'),(remainder,'month'),(days,'day')]:
            if amount:parts.append(f"{amount} {unit}{'s' if amount!=1 else ''}")
        return ' '.join(parts) or '0 days',months,'calculated'
    months=end-start+1
    years,remainder=divmod(months,12)
    parts=[]
    if years:parts.append(f"{years} year{'s' if years!=1 else ''}")
    if remainder:parts.append(f"{remainder} month{'s' if remainder!=1 else ''}")
    return ' '.join(parts),months,'calculated'
