"""Source-bound heading scope, shared by review application and validation.

Source order is retained. Geometry establishes applicability, never a new reading
order. Uncertain scope is a review requirement, not permission to invent owners.
"""
from dataclasses import replace
from types import MappingProxyType
import json


FIELD_KINDS = {
    'experience': {'employer', 'title', 'dates', 'responsibilities', 'achievements', 'technologies', 'location', 'client'},
    'education': {'institution', 'qualification', 'dates', 'grade', 'field_of_study'},
    'projects': {'title', 'dates', 'responsibilities', 'technologies'},
    'certifications': {'title', 'dates', 'issuer'},
    'awards': {'title', 'dates', 'responsibilities'},
}


def horizontal_overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0])


def boundary_scope(state, heading_id):
    """Return (source, supported) up to the next applicable heading.

    A full-width physical paragraph immediately below a heading establishes a
    full-width region even when individual short lines have different lanes.
    Independent headings in the same vertical band prevent that expansion.
    Without geometry only a single explicit main lane is sufficient to move.
    Page transitions and uncertain lanes are flagged, never auto-transferred.
    """
    spans = sorted(state.spans, key=lambda s: s.order)
    head = next(s for s in spans if s.source_id == heading_id)
    following = [s for s in spans if s.order > head.order]
    boxes = {}
    for s in spans:
        if s.bbox:
            key = (s.page, s.element)
            old = boxes.get(key, s.bbox)
            boxes[key] = (min(old[0], s.bbox[0]), min(old[1], s.bbox[1]),
                          max(old[2], s.bbox[2]), max(old[3], s.bbox[3]))
    first = next((s for s in following if s.text.strip() and state.owners[s.source_id].status != 'non_content_artifact'), None)
    first_box = boxes.get((first.page, first.element)) if first else None
    competing = bool(head.bbox and any(
        s.page == head.page and s.bbox and s.source_id != heading_id
        and state.owners[s.source_id].heading
        and not horizontal_overlap(head.bbox, s.bbox)
        and max(head.bbox[1], s.bbox[1]) < min(head.bbox[3], s.bbox[3]) for s in spans))
    full_region = bool(head.bbox and (
        head.bbox[2] - head.bbox[0] >= .65 or
        (first and first.page == head.page and first_box and
         first_box[2] - first_box[0] >= .65 and first_box[1] >= head.bbox[3] and not competing)))
    result = []
    for span in following:
        owner = state.owners[span.source_id]
        same_page = span.page == head.page
        box = boxes.get((span.page, span.element))
        overlap = bool(head.bbox and box and horizontal_overlap(head.bbox, box))
        same_lane = span.lane == head.lane
        main = head.lane == span.lane == 'main'
        applicable = full_region or overlap or same_lane or span.lane == 'wide'
        styled = any(h.get('heading_style') for h in json.loads(span.coordinates_json).get('lines', []))
        if owner.heading or (styled and len(span.text.split()) <= 12):
            if applicable or not same_page:
                break
            continue
        # A visibly separate column with no spanning source is unrelated.
        if not applicable:
            continue
        if owner.status == 'non_content_artifact':
            continue
        supported = same_page and (
            bool(head.bbox and box and box[1] >= head.bbox[3] and (full_region or overlap))
            or (not head.bbox and not box and main))
        result.append((span, supported))
    return result


def reconcile_boundaries(state, heading_ids):
    """Reconcile complete existing records; never guess new record boundaries."""
    owners = dict(state.owners)
    for hid in sorted(heading_ids, key=lambda sid: next(s.order for s in state.spans if s.source_id == sid)):
        current = replace(state, owners=MappingProxyType(owners))
        target = owners[hid].section
        scope = boundary_scope(current, hid)
        eligible = {s.source_id for s, supported in scope if supported}
        records = {}
        for sid, owner in owners.items():
            if owner.record:
                records.setdefault(owner.record, set()).add(sid)
        linked = set(state.record_parents) | set(state.record_parents.values()) | set(state.parents)
        for span, supported in scope:
            sid = span.source_id
            old = owners[sid]
            if old.section == target:
                continue
            members = records.get(old.record, set())
            # Whole records and compatible identity tags are required. A job
            # with employer evidence cannot silently become a project.
            safe_record = bool(old.record and members <= eligible and old.record not in linked
                               and all(set(owners[s].fields) <= FIELD_KINDS.get(target, set()) for s in members))
            if supported and safe_record:
                anchor = min((s for s in state.spans if s.source_id in members), key=lambda s: s.order)
                rid = f'{target}@{anchor.source_id}'
                owners[sid] = replace(old, section=target, record=rid, boundary_source=hid)
            else:
                peers = {owners[s.source_id].record for s in state.spans
                         if s.element == span.element and s.source_id != sid
                         and owners[s.source_id].section == target and owners[s.source_id].record}
                if supported and set(old.fields) <= FIELD_KINDS.get(target, set()):
                    # A contaminated record must not make its unrelated members
                    # inseparable. Physical siblings can establish a new owner.
                    rid = next(iter(peers)) if len(peers) == 1 else None
                    owners[sid] = replace(old, section=target, record=rid,
                        fields=old.fields if rid else (), status='provisional' if rid else 'needs_review', boundary_source=hid)
                else:
                    owners[sid] = replace(old, record=None, fields=(), status='needs_review', boundary_source=hid)
    return replace(state, owners=MappingProxyType(owners))


def boundary_errors(state):
    """Semantic checks supplement (and never replace) source integrity checks."""
    errors = []
    by_id = {s.source_id: s for s in state.spans}
    for sid, owner in state.owners.items():
        hid = owner.boundary_source
        if not hid:
            continue
        if hid == sid and owner.heading:
            for span, _ in boundary_scope(state, sid):
                child = state.owners[span.source_id]
                if child.section != owner.section and child.status != 'needs_review':
                    errors.append('unresolved_section_boundary_conflict')
            continue
        head = state.owners.get(hid)
        if not head or not head.heading or by_id[hid].order >= by_id[sid].order:
            errors.append('invalid_section_boundary_reference')
        elif owner.section != head.section and owner.status != 'needs_review':
            errors.append('unresolved_section_boundary_conflict')
    return sorted(set(errors))
