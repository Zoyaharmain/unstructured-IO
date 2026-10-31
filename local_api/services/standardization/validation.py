"""One interpretation of validation flags and explicit transformation accounting."""
from local_api.services.standardization.contracts import StandardizationWarning, ValidationStatus


def finalize_status(warnings):
    unresolved = any(w.severity in {'warning', 'review_required'} for w in warnings)
    invalid = any(w.warning_type in {'invalid_input_type', 'invalid_calendar_date', 'invalid_dates',
                                    'invalid_date_order', 'missing_required_field'} for w in warnings)
    return ValidationStatus(is_valid=not invalid, usable=not unresolved,
                            requires_human_review=unresolved, issues_count=len(warnings))


def normalization_changes(original, standardized, existing):
    changes = []
    applied_paths = {w.field for w in existing if w.applied}
    def visit(before, after, path):
        if isinstance(before, dict) and isinstance(after, dict):
            for key in before.keys() & after.keys():
                if key.startswith('raw_'): continue
                visit(before[key], after[key], f'{path}.{key}' if path else key)
        elif isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
            for i, (old, new) in enumerate(zip(before, after)):
                visit(old, new, f'{path}[{i}]')
        elif before != after and (path not in applied_paths or isinstance(before, list)):
            date_field = path.rsplit('.', 1)[-1] in {'start_date', 'end_date', 'start_year', 'graduation_year', 'issue_year', 'issue_date', 'expiry_date', 'date'}
            changes.append(StandardizationWarning(field=path,
                warning_type='date_standardized' if date_field and after is not None else 'collection_standardized' if isinstance(before, list) else 'value_standardized',
                original_value=before, normalized_value=after, applied=True,
                basis='Deterministic formatting, date parsing, filtering or alias rule; original retained in evidence.',
                message='System corrected the date representation to ISO format; the original date is retained and no calendar date was inferred.' if date_field and after is not None else 'System changed the standardized representation; original source value retained.'))
    visit(original, standardized, '')
    return changes
