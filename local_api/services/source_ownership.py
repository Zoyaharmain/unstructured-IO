"""Immutable source ledger and atomic, source-only structural repair.

Record identity is anchored to source, never employer spelling or chronology.
Geometry and upstream element types are evidence, not semantic authority.
"""
from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from types import MappingProxyType
from collections.abc import Mapping

from local_api.services.llm_section_review import assert_coverage, source_ledger


@dataclass(frozen=True)
class SourceSpan:
    source_id: str
    element: int
    start: int
    end: int
    text: str
    page: int | None
    order: int
    lane: str
    coordinates_json: str
    upstream_type: str
    bbox: tuple[float, float, float, float] | None = None
    reading_order_basis: str = 'extraction'
    source_metadata_json: str = '{}'
    list_marker: str | None = None
    indentation: int = 0
    section_candidate: str | None = None
    section_alternatives: tuple[str, ...] = ()
    parent_candidate: str | None = None
    ambiguity_reason: str | None = None
    confidence: float = 1.0


@dataclass(frozen=True)
class Owner:
    section: str | None
    record: str | None
    fields: tuple[str, ...] = ()
    status: str = 'provisional'


@dataclass(frozen=True)
class Ownership:
    digest: str
    spans: tuple[SourceSpan, ...]
    owners: Mapping[str, Owner]
    parents: Mapping[str, str]
    record_parents: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    groups: frozenset[str] = frozenset()

    def payload(self):
        from dataclasses import asdict
        sections = {}
        for span in self.spans:
            owner = self.owners[span.source_id]
            section = sections.setdefault(owner.section or 'needs_review', {'source_ids': [], 'records': {}})
            section['source_ids'].append(span.source_id)
            if owner.record:
                section['records'].setdefault(owner.record, []).append(span.source_id)
        spans = []
        for source in self.spans:
            span = asdict(source)
            span['coordinates'] = json.loads(span.pop('coordinates_json'))
            span['source_metadata'] = json.loads(span.pop('source_metadata_json'))
            span['section_alternatives'] = list(source.section_alternatives)
            span['owner'] = asdict(self.owners[source.source_id])
            span['owner']['fields'] = list(self.owners[source.source_id].fields)
            if span['bbox'] is not None:
                span['bbox'] = list(span['bbox'])
            spans.append(span)
        return {'source_digest': self.digest,
                'spans': spans,
                'employer_parents': dict(self.parents), 'record_parents': dict(self.record_parents),
                'group_records': sorted(self.groups), 'sections': sections}


def validate_record_tree(entries):
    """Parent links are section-local, acyclic, and do not share primary text."""
    parents = {e.entry_id: getattr(e, 'parent_entry_id', None) for e in entries}
    if len(parents) != len(entries):
        raise ValueError('Duplicate record ID')
    for rid in parents:
        visited = set()
        cursor = rid
        while cursor is not None:
            if cursor not in parents:
                raise ValueError('Invalid parent record reference')
            if cursor in visited:
                raise ValueError('Cyclic parent record reference')
            visited.add(cursor)
            cursor = parents[cursor]


def snapshot(elements, result):
    """Freeze exact Unicode offsets and all original metadata into a digest.

    IDs are stable for an identical extraction and interval. Reading order keeps
    the extractor's order; lane/geometry are retained rather than re-sorting
    unrelated columns by y and silently claiming an inferred reading order.
    """
    ledger = source_ledger(result)
    assert_coverage(elements, ledger)
    raw = json.dumps([e.model_dump() for e in elements], sort_keys=True, ensure_ascii=False)
    digest = sha256(raw.encode()).hexdigest()
    membership, fields, parents, statuses = {}, {}, {}, {}
    record_parents, groups = {}, set()
    for section in result.sections:
        validate_record_tree(section.entries)
        record_ids = {e.entry_id: f'{section.category}@e{section.blocks[e.block_indices[0]].source_element_index}:{section.blocks[e.block_indices[0]].start}:{section.blocks[e.block_indices[0]].end}'
                      for e in section.entries if e.block_indices and all(0 <= i < len(section.blocks) for i in e.block_indices)}
        for entry in section.entries:
            if not entry.block_indices:
                continue
            if any(not 0 <= i < len(section.blocks) for i in entry.block_indices):
                raise ValueError('Invalid record block index')
            if any(i not in entry.block_indices for indices in entry.fields.values() for i in indices):
                raise ValueError('Field evidence crosses primary record ownership')
            from local_api.services.employer_context import valid_record_context
            if not valid_record_context(section, entry):
                raise ValueError('Invalid record context')
            anchor = section.blocks[entry.block_indices[0]]
            rid = f'{section.category}@e{anchor.source_element_index}:{anchor.start}:{anchor.end}'
            if entry.parent_entry_id is not None:
                if entry.parent_entry_id not in record_ids:
                    raise ValueError('Invalid parent record reference')
                record_parents[rid] = record_ids[entry.parent_entry_id]
            if entry.record_kind == 'group':
                groups.add(rid)
            for i in entry.block_indices:
                if not 0 <= i < len(section.blocks):
                    raise ValueError('Invalid record block index')
                b = section.blocks[i]
                key = (b.source_element_index, b.start, b.end)
                if key in membership:
                    raise ValueError('Multiple primary record owners')
                membership[key] = rid
                statuses[key] = entry.relationship_status
                fields[key] = tuple(k for k, indices in entry.fields.items() if i in indices)
            employers = entry.fields.get('employer', []) or entry.context_fields.get('company', [])
            if len(set(employers)) == 1:
                b = section.blocks[employers[0]]
                parents[rid] = f'employer@e{b.source_element_index}:{b.start}:{b.end}'
            elif len(set(employers)) > 1:
                for i in entry.block_indices:
                    b = section.blocks[i]
                    statuses[b.source_element_index, b.start, b.end] = 'needs_review'
    spans, owners = [], {}
    from local_api.services.source_accounting import artifact_reason
    for order, (block, category) in enumerate(ledger):
        key = (block.source_element_index, block.start, block.end)
        sid = f'e{key[0]}:{key[1]}:{key[2]}'
        element = elements[key[0]]
        geometry = {'element': element.metadata.get('coordinates'),
                    'lines': [h for h in element.metadata.get('pdf_source_lines', [])
                              if min(block.end, h.get('end', 0)) > max(block.start, h.get('start', 0))]}
        boxes = [h['bbox'] for h in geometry['lines'] if len(h.get('bbox', [])) == 4]
        bbox = None
        if boxes:
            bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
        else:
            coords = geometry['element'] or {}
            points, width, height = coords.get('points', []), coords.get('layout_width'), coords.get('layout_height')
            if points and width and height:
                bbox = (min(p[0] for p in points)/width, min(p[1] for p in points)/height,
                        max(p[0] for p in points)/width, max(p[1] for p in points)/height)
        import re
        marker = re.match(r'^\s*([•▪●*]|[-–—](?=\s)|\d+(?:\.\d+)*[.)]?)\s+', block.text)
        record = membership.get(key)
        from local_api.services.logical_blocks import RECORD_SECTIONS
        from local_api.services.resume_structure import heading_boundary
        from local_api.services.resume_sections import ALIASES
        is_heading = block.assignment in {'section_heading', 'structural_heading'} or heading_boundary(block.text, ALIASES) == (category, None)
        status = 'needs_review' if block.assignment == 'ownership_needs_review' or statuses.get(key) == 'needs_review' or category is None or category in RECORD_SECTIONS and record is None and not is_heading else 'provisional'
        if artifact_reason(element, block):
            status = 'non_content_artifact'
        owners[sid] = Owner(category, record, fields.get(key, ()), status)
        cand_parent = record_parents.get(record) or parents.get(record)
        ambiguity_r = None
        conf = 1.0
        if status == 'needs_review':
            conf = 0.5
            ambiguity_r = 'needs_review'
            for sec in result.sections:
                for entry in sec.entries:
                    if entry.entry_id == record or (entry.block_indices and f"{sec.category}@{sec.blocks[entry.block_indices[0]].source_element_index}:{sec.blocks[entry.block_indices[0]].start}:{sec.blocks[entry.block_indices[0]].end}" == record):
                        if entry.review_reasons:
                            ambiguity_r = "; ".join(entry.review_reasons)
        elif status == 'non_content_artifact':
            conf = 0.0
            ambiguity_r = 'artifact'
        spans.append(SourceSpan(sid, *key, block.text, element.page_number, order, block.lane,
                                json.dumps(geometry, sort_keys=True), element.type, bbox,
                                source_metadata_json=json.dumps(element.metadata, sort_keys=True),
                                list_marker=marker.group(1) if marker else None,
                                indentation=len(block.text) - len(block.text.lstrip()),
                                section_candidate=block.candidate_section, section_alternatives=tuple(block.alternatives),
                                parent_candidate=cand_parent,
                                ambiguity_reason=ambiguity_r,
                                confidence=conf))
    orphan_groups = groups - set(record_parents.values())
    for sid, owner in list(owners.items()):
        if owner.record in orphan_groups:
            owners[sid] = replace(owner, status='needs_review')
    return Ownership(digest, tuple(spans), MappingProxyType(owners), MappingProxyType(parents),
                     MappingProxyType(record_parents), frozenset(groups))


def role_boundary_operations(state):
    """Split repeated role anchors only with intervening duty evidence.

    This does not infer employment from date chronology, capitalization, or an
    upstream Title. A role without supporting evidence stays provisional.
    """
    import re
    from local_api.services.record_relationships import field_kinds
    from local_api.services.record_subfields import employment_header_fields, ROLE, responsibility_fragment, ACTION
    operations = []
    order = {s.source_id: s.order for s in state.spans}
    spans_by_record = {}
    for s in state.spans:
        o = state.owners[s.source_id]
        if o.record and o.section == 'experience':
            spans_by_record.setdefault(o.record, []).append(s)

    def is_role_anchor(s):
        text = s.text.strip()
        if len(text.split()) > 10: return False
        if responsibility_fragment(text) or ACTION.search(text): return False
        if re.search(r'\b(?:for|across|supporting|delivering|ensuring|managing|building|leading)\b', text, re.I): return False
        explicit = employment_header_fields(text)
        if explicit.get('role'): return True
        return bool(ROLE.search(text) and text[:1].isupper() and not re.search(r'[.;]$', text))

    for rid, spans in spans_by_record.items():
        role_spans = [s for s in spans if is_role_anchor(s)]
        if len(role_spans) < 2:
            continue
        first_role, second_role = role_spans[0], role_spans[1]
        is_opening_date = bool('dates' in state.owners[spans[0].source_id].fields or 'dates' in field_kinds(spans[0].text, 'experience'))
        second_has_dates = bool(re.search(r'(?:19|20)\d{2}', second_role.text))
        if is_opening_date and not second_has_dates:
            continue
        intervening = [s for s in spans if order[first_role.source_id] < order[s.source_id] < order[second_role.source_id]]
        has_resp = any('responsibilities' in state.owners[s.source_id].fields or 'responsibilities' in field_kinds(s.text, 'experience') for s in intervening)
        if not has_resp:
            continue
        if first_role.lane != second_role.lane and 'wide' not in {first_role.lane, second_role.lane}:
            operations.append({'op': 'review', 'source_ids': [s.source_id for s in spans]})
            continue
        employers = [s for s in spans if 'employer' in state.owners[s.source_id].fields or 'employer' in field_kinds(s.text, 'experience')]
        if any(order[s.source_id] > order[first_role.source_id] for s in employers):
            continue
        following = [s for s in spans if order[s.source_id] > order[second_role.source_id]]
        if following:
            operations.append({'op': 'split', 'record': rid, 'anchor': second_role.source_id})
    return operations


def apply_operations(state, operations, categories):
    """Validate an entire transaction before committing any ownership changes.

    split: existing record + existing anchor source id
    merge: existing records with the same section and employer parent
    assign: existing source ids + existing record (or null) + canonical section
    review: existing source ids, clearing uncertain record/field ownership
    No operation may generate text, offsets, field values, or source IDs.
    """
    if not isinstance(operations, list) or len(operations) > 1000:
        raise ValueError('Invalid operations')
    owners, parents = dict(state.owners), dict(state.parents)
    record_parents, groups = dict(state.record_parents), set(state.groups)
    order = {s.source_id: s.order for s in state.spans}
    def records():
        return {o.record for o in owners.values() if o.record is not None}
    def ids(value):
        if not isinstance(value, list) or not value or len(set(value)) != len(value) or any(s not in owners for s in value):
            raise ValueError('Unknown or duplicate source IDs')
        return value
    for op in operations:
        if not isinstance(op, dict):
            raise ValueError('Invalid operation')
        kind = op.get('op')
        required = {'create': {'op', 'section', 'source_ids'},
                    'create_group': {'op', 'section', 'source_ids'},
                    'link_parent': {'op', 'record', 'parent'},
                    'link_employer': {'op', 'record', 'source_id'},
                    'split': {'op', 'record', 'anchor'}, 'merge': {'op', 'records'},
                    'assign': {'op', 'source_ids', 'section', 'record', 'fields'},
                    'review': {'op', 'source_ids'}}
        if kind not in required or set(op) != required[kind]:
            raise ValueError('Invalid operation schema')
        if kind == 'link_parent':
            rid, parent = op['record'], op['parent']
            if rid not in records() or parent not in records() or rid == parent:
                raise ValueError('Invalid parent record reference')
            if len({o.section for o in owners.values() if o.record in {rid, parent}}) != 1:
                raise ValueError('Parent crosses section')
            lanes = {s.lane for s in state.spans if owners[s.source_id].record in {rid, parent}} - {'wide'}
            if len(lanes) > 1:
                raise ValueError('Parent crosses reading lanes')
            record_parents[rid] = parent
        elif kind == 'link_employer':
            rid, sid = op['record'], op['source_id']
            if rid not in records() or sid not in owners or owners[sid].section != 'experience' or 'employer' not in owners[sid].fields:
                raise ValueError('Employer context must reference existing employer evidence')
            members = [o for o in owners.values() if o.record == rid]
            if any(o.section != 'experience' or 'employer' in o.fields for o in members):
                raise ValueError('Employer context cannot replace a primary employer')
            parents[rid] = f'employer@{sid}'
        elif kind in {'create', 'create_group'}:
            ss = ids(op['source_ids'])
            category = op['section']
            if category not in categories or category not in {'experience','education','projects','certifications','awards','volunteering','publications'}:
                raise ValueError('Only repeated sections can contain a new record')
            anchor = min(ss, key=order.get)
            rid = f'{category}@{anchor}'
            if rid in records():
                raise ValueError('Record already exists')
            if any(owners[sid].section not in {None, category} for sid in ss):
                raise ValueError('Creation crosses section')
            if kind == 'create_group':
                groups.add(rid)
            for sid in ss:
                owners[sid] = Owner(category, rid, (), 'needs_review')
        elif kind == 'split':
            rid, anchor = op['record'], op['anchor']
            if rid not in records() or anchor not in owners or owners[anchor].record != rid:
                raise ValueError('Split must reference an owned source anchor')
            members = [s for s, o in owners.items() if o.record == rid]
            moved = [s for s in members if order[s] >= order[anchor]]
            if len(moved) == len(members):
                raise ValueError('Split must leave two nonempty records')
            new = f'{owners[anchor].section}@{anchor}'
            if new in records():
                raise ValueError('Record already exists')
            if rid in parents:
                parents[new] = parents[rid]
            if rid in record_parents:
                record_parents[new] = record_parents[rid]
            for sid in moved:
                owners[sid] = replace(owners[sid], record=new)
        elif kind == 'merge':
            rs = op['records']
            if not isinstance(rs, list) or len(rs) < 2 or len(set(rs)) != len(rs) or any(r not in records() for r in rs):
                raise ValueError('Invalid merge records')
            sections = {o.section for o in owners.values() if o.record in rs}
            if len(sections) != 1 or len({parents.get(r) for r in rs}) != 1 or ('experience' in sections and any(r not in parents for r in rs)):
                raise ValueError('Merge crosses section or unestablished employer')
            lanes = {s.lane for s in state.spans if owners[s.source_id].record in rs} - {'wide'}
            if len(lanes) > 1:
                raise ValueError('Merge crosses reading lanes')
            for sid, owner in list(owners.items()):
                if owner.record in rs:
                    owners[sid] = replace(owner, record=rs[0])
            if any(r in groups for r in rs) or len({record_parents.get(r) for r in rs}) != 1:
                raise ValueError('Merge crosses hierarchy')
            for child, parent in list(record_parents.items()):
                if parent in rs:
                    record_parents[child] = rs[0]
            for rid in rs[1:]:
                parents.pop(rid, None)
                record_parents.pop(rid, None)
        else:
            ss = ids(op['source_ids'])
            if kind == 'review':
                for sid in ss:
                    owners[sid] = replace(owners[sid], record=None, fields=(), status='needs_review')
                continue
            category, rid, fs = op['section'], op['record'], op['fields']
            entity_fields = {
                'experience': {'employer','title','dates','responsibilities','achievements','technologies','location','client'},
                'education': {'institution','qualification','dates','grade','field_of_study'},
                'projects': {'title','dates','responsibilities','technologies'},
                'certifications': {'title','dates','issuer'},
                'awards': {'title','dates','responsibilities'},
            }
            if category not in categories or not isinstance(fs, list) or any(f not in entity_fields.get(category, set()) for f in fs):
                raise ValueError('Invalid section or entity kind')
            if rid is not None and (rid not in records() or any(o.section != category for o in owners.values() if o.record == rid)):
                raise ValueError('Record section mismatch')
            if fs and rid is None:
                raise ValueError('Entity requires a primary record')
            for sid in ss:
                from local_api.services.resume_structure import heading_boundary
                from local_api.services.resume_sections import ALIASES
                heading = heading_boundary(next(s.text for s in state.spans if s.source_id == sid), ALIASES) == (category, None)
                owners[sid] = Owner(category, rid, tuple(fs), 'provisional' if rid or category != 'experience' or heading else 'needs_review')
    used = {o.record for o in owners.values()}
    employer_ids = {f'employer@{sid}' for sid, owner in owners.items() if 'employer' in owner.fields}
    parents = {r:p for r,p in parents.items() if r in used and p in employer_ids}
    for rid in used - {None}:
        employers = [sid for sid, owner in owners.items() if owner.record == rid and 'employer' in owner.fields]
        if len(employers) == 1:
            parents[rid] = f'employer@{employers[0]}'
        elif len(employers) > 1:
            parents.pop(rid, None)
    if any(child not in used or parent not in used for child, parent in record_parents.items()):
        raise ValueError('Operation would orphan a parent relationship')
    for child in record_parents:
        seen = set()
        cursor = child
        while cursor in record_parents:
            if cursor in seen:
                raise ValueError('Cyclic parent record reference')
            seen.add(cursor)
            cursor = record_parents[cursor]
    orphan_groups = groups - set(record_parents.values())
    for sid, owner in list(owners.items()):
        if owner.record in orphan_groups:
            owners[sid] = replace(owner, status='needs_review')
    for child, parent in record_parents.items():
        if len({o.section for o in owners.values() if o.record in {child, parent}}) != 1:
            raise ValueError('Parent crosses section')
    return replace(state, owners=MappingProxyType(owners), parents=MappingProxyType(parents),
                   record_parents=MappingProxyType(record_parents), groups=frozenset(groups & used))


def materialize(elements, result, state, *, strict_parent_links=False):
    """Project validated ownership onto the existing section/entry API."""
    from local_api.schemas.sections import SectionEntry
    from local_api.services.resume_sections import build_sections
    current = snapshot(elements, result)
    if current.digest != state.digest or current.spans != state.spans:
        raise ValueError('Stale source ledger')
    blocks = {f'e{b.source_element_index}:{b.start}:{b.end}': b for b, _ in source_ledger(result)}
    grouped, unresolved, artifacts = {}, [], []
    artifact_ids = {f'e{b.source_element_index}:{b.start}:{b.end}' for b in result.source_artifacts}
    for span in state.spans:
        owner = state.owners[span.source_id]
        block = blocks[span.source_id]
        if owner.section != current.owners[span.source_id].section:
            block = block.model_copy(update={'assignment': 'semantic', 'context_source_element_index': None,
                                             'reason': 'Validated source-ID section reassignment'})
        if owner.status != 'needs_review' and block.assignment == 'ownership_needs_review':
            block = block.model_copy(update={'assignment': 'semantic', 'reason': 'Validated primary source ownership'})
        if owner.status == 'needs_review':
            block = block.model_copy(update={'assignment': 'ownership_needs_review',
                                             'reason': 'Primary source ownership requires review'})
        if span.source_id in artifact_ids:
            if owner != current.owners[span.source_id]:
                raise ValueError('Artifact cannot be reassigned')
            artifacts.append(block)
        elif owner.section is None:
            unresolved.append(block)
        else:
            grouped.setdefault(owner.section, []).append(block)
    out = result.model_copy(deep=True)
    out.sections = build_sections(grouped, elements, refine=False)
    out.needs_review, out.source_artifacts = unresolved, artifacts
    for section in out.sections:
        section.blocks = [b.model_copy(update={'assignment':'ownership_needs_review'})
                          if state.owners[f'e{b.source_element_index}:{b.start}:{b.end}'].status == 'needs_review' else b
                          for b in section.blocks]
        original = next((s for s in result.sections if s.category == section.category), None)
        unchanged = original is not None and [f'e{b.source_element_index}:{b.start}:{b.end}' for b in original.blocks] == [f'e{b.source_element_index}:{b.start}:{b.end}' for b in section.blocks] and all(
            state.owners[f'e{b.source_element_index}:{b.start}:{b.end}'] == current.owners[f'e{b.source_element_index}:{b.start}:{b.end}']
            and state.parents.get(state.owners[f'e{b.source_element_index}:{b.start}:{b.end}'].record) == current.parents.get(current.owners[f'e{b.source_element_index}:{b.start}:{b.end}'].record)
            for b in section.blocks)
        unchanged = unchanged and dict(state.record_parents) == dict(current.record_parents) and state.groups == current.groups
        if unchanged:
            section.entries = [e.model_copy(deep=True) for e in original.entries]
            continue
        entries = {}
        for i, block in enumerate(section.blocks):
            sid = f'e{block.source_element_index}:{block.start}:{block.end}'
            owner = state.owners[sid]
            if owner.record is None:
                continue
            entry = entries.setdefault(owner.record, SectionEntry(entry_id=owner.record, block_indices=[], lane=block.lane,
                boundary_reason='validated source ownership',
                parent_entry_id=state.record_parents.get(owner.record),
                record_kind='group' if owner.record in state.groups else 'record'))
            entry.block_indices.append(i)
            for field in owner.fields:
                entry.fields.setdefault(field, []).append(i)
            if owner.status == 'needs_review':
                entry.relationship_status = 'needs_review'
                entry.review_reasons = ['source_ownership_unresolved']
        section.entries = list(entries.values())
        for entry in section.entries:
            parent_id = state.parents.get(entry.entry_id, '')
            parent_sid = parent_id.removeprefix('employer@')
            parent_index = next((i for i,b in enumerate(section.blocks)
                                 if f'e{b.source_element_index}:{b.start}:{b.end}' == parent_sid), None)
            if parent_index is not None and parent_index not in entry.block_indices:
                entry.context_fields['company'] = [parent_index]
                from local_api.services.employer_context import valid_record_context
                if not valid_record_context(section, entry):
                    if strict_parent_links:
                        raise ValueError('Employer context scope mismatch')
                    entry.context_fields.pop('company')
                    entry.relationship_status = 'needs_review'
                    entry.review_reasons.append('employer_context_unresolved')
            from local_api.services.employer_context import valid_record_context
            if section.category == 'experience' and not entry.fields.get('employer') and not (entry.context_fields and valid_record_context(section, entry)):
                entry.relationship_status = 'needs_review'
                entry.review_reasons = sorted(set(entry.review_reasons + ['employer_requires_parent_context_review']))
    assert_coverage(elements, source_ledger(out))
    from local_api.services.employer_context import recover_employer_context
    out = recover_employer_context(out)
    out.metadata['source_ownership'] = state.payload()
    out.status = 'needs_review' if any(o.status == 'needs_review' for o in state.owners.values()) or any(e.relationship_status == 'needs_review' for s in out.sections for e in s.entries) else 'provisional'
    return out


def validated_ownership_state(elements, result):
    """Verify persisted ownership before consuming it without heuristic recovery."""
    state = snapshot(elements, result)
    expected = result.metadata.get('source_ownership', {})
    if expected.get('source_digest') != state.digest:
        raise ValueError('Stale validated ownership source')
    rows = expected.get('spans', [])
    stored = {s['source_id']:s for s in rows}
    if len(rows) != len(stored):
        raise ValueError('Duplicate validated source ID')
    if expected.get('record_parents', {}) != dict(state.record_parents) or set(expected.get('group_records', [])) != state.groups or expected.get('employer_parents', {}) != dict(state.parents):
        raise ValueError('Validated ownership relationships changed')
    if len(stored) != len(state.spans):
        raise ValueError('Validated ownership ledger changed')
    for span in state.spans:
        row = stored.get(span.source_id, {})
        owner = state.owners[span.source_id]
        reference = row.get('owner', {})
        if row.get('text') != span.text or reference.get('section') != owner.section or reference.get('record') != owner.record or set(reference.get('fields', ())) != set(owner.fields) or reference.get('status') != owner.status:
            raise ValueError('Validated ownership ledger changed')
    return state


def ambiguity_package(state, result):
    """Batch unresolved relationships with whole candidate records and neighbors.

    Confidence is categorical: no synthetic probability is assigned. Source text,
    layout/style and current owners remain in each span's evidence payload.
    """
    payload = state.payload()
    questions = []
    focus = set()
    for span in state.spans:
        owner = state.owners[span.source_id]
        if owner.status == 'needs_review':
            focus.add(span.source_id)
            questions.append({'source_ids': [span.source_id], 'reason': 'unresolved_source_ownership',
                              'question': 'Which existing record owns this source, or must it remain unresolved?'})
    for section in result.sections:
        for entry in section.entries:
            if entry.relationship_status != 'needs_review' and not entry.review_reasons:
                continue
            ids = [f'e{section.blocks[i].source_element_index}:{section.blocks[i].start}:{section.blocks[i].end}' for i in entry.block_indices]
            focus.update(ids)
            reasons = entry.review_reasons
            if 'potential_merged_records' in reasons:
                rec_id = state.owners[ids[0]].record if ids and ids[0] in state.owners else entry.entry_id
                second_anchor = ids[1] if len(ids) > 1 else ids[0]
                q = f'Record {rec_id} contains multiple independent items. Propose a split: {{"op": "split", "record": "{rec_id}", "anchor": "{second_anchor}"}}.'
            elif 'potential_multiline_continuation' in reasons:
                rec_id = state.owners[ids[0]].record if ids and ids[0] in state.owners else entry.entry_id
                q = f'Record {rec_id} appears to be a wrapped continuation line. Propose a merge with adjacent fragmented record.'
            elif 'heading_as_employer' in reasons:
                q = f'Employer {ids[0]} is a section heading. Propose: {{"op": "assign", "source_ids": ["{ids[0]}"], "section": "{section.category}", "record": null, "fields": []}}.'
            else:
                q = 'Are these boundaries and parent links supported? Correct ownership using existing sources only.'
            questions.append({'source_ids': ids, 'reason': ','.join(reasons) or 'unresolved_record_relationship',
                              'question': q})
    candidates = {state.owners[sid].record for sid in focus} - {None}
    # Adjacent records are candidates, not automatically inferred owners.
    for i, span in enumerate(state.spans):
        if span.source_id in focus:
            candidates.update(state.owners[state.spans[j].source_id].record for j in (i-1, i+1) if 0 <= j < len(state.spans))
    candidates.discard(None)
    pending = list(candidates)
    while pending:
        parent = state.record_parents.get(pending.pop())
        if parent is not None and parent not in candidates:
            candidates.add(parent)
            pending.append(parent)
    selected = focus | {s.source_id for s in state.spans if state.owners[s.source_id].record in candidates}
    for i, span in enumerate(state.spans):
        if span.source_id in focus:
            selected.update(state.spans[j].source_id for j in (i-1, i+1) if 0 <= j < len(state.spans))
    # Include explicit parent evidence without widening primary ownership.
    for rid in list(candidates):
        parent = state.parents.get(rid, '').removeprefix('employer@')
        if parent in state.owners:
            selected.add(parent)
    payload['record_parents'] = {child: parent for child, parent in state.record_parents.items() if child in candidates}
    payload['group_records'] = sorted(state.groups & candidates)
    payload['employer_parents'] = {rid: parent for rid, parent in state.parents.items() if rid in candidates}
    payload['ambiguities'] = questions
    payload['candidate_records'] = sorted(candidates)
    payload['spans'] = [row for row in payload['spans'] if row['source_id'] in selected]
    payload['sections'] = {key: {'source_ids': [sid for sid in value['source_ids'] if sid in selected],
                                'records': {rid: ids for rid, ids in value['records'].items() if rid in candidates}}
                           for key, value in payload['sections'].items() if any(sid in selected for sid in value['source_ids'])}
    payload['evidence_status'] = 'unresolved' if questions else 'explicit_review'
    return payload


def translate_decisions_to_operations(decisions, state):
    """Translate structured recovery decisions into validated state operations.

    Supported decisions:
    - ATTACH_TO_EXISTING_RECORD: assign source span(s) to existing record
    - ASSIGN_HEADING: assign source span(s) as section heading with record: null
    - SPLIT_RECORD: split merged record at anchor
    - CREATE_NEW_RECORD: create record anchored at earliest source ID
    - CREATE_PARENT_GROUP: create group record and optionally link child records
    - ATTACH_CHILD_TO_PARENT: link child record to parent group
    - MERGE_CONTINUATION: merge adjacent records
    - KEEP_SEPARATE: retain separate records
    - UNRESOLVED: mark source span(s) for review
    """
    ops = []
    for d in decisions:
        if not isinstance(d, dict):
            raise ValueError('Each decision must be a dict')
        decision_type = d.get('decision')
        if not decision_type:
            raise ValueError('Decision missing "decision" field')

        if decision_type == 'ATTACH_TO_EXISTING_RECORD':
            source_ids = d.get('source_ids', [])
            record = d.get('record')
            fields = d.get('fields', []) if record else []
            section = d.get('section')
            if not section and record and '@' in record:
                section = record.split('@', 1)[0]
            if not section and source_ids and source_ids[0] in state.owners:
                section = state.owners[source_ids[0]].section
            ops.append({'op': 'assign', 'source_ids': source_ids, 'section': section, 'record': record, 'fields': fields})

        elif decision_type in {'ASSIGN_HEADING', 'ASSIGN_SECTION_HEADING'}:
            source_ids = d.get('source_ids', [])
            section = d.get('section')
            if not section and source_ids and source_ids[0] in state.owners:
                section = state.owners[source_ids[0]].section
            ops.append({'op': 'assign', 'source_ids': source_ids, 'section': section, 'record': None, 'fields': []})

        elif decision_type == 'SPLIT_RECORD':
            record = d.get('record')
            anchor = d.get('anchor')
            if not record or not anchor:
                raise ValueError('SPLIT_RECORD requires record and anchor')
            ops.append({'op': 'split', 'record': record, 'anchor': anchor})

        elif decision_type == 'CREATE_NEW_RECORD':
            section = d.get('section')
            source_ids = d.get('source_ids', [])
            if not section or not source_ids:
                raise ValueError('CREATE_NEW_RECORD requires section and source_ids')
            ops.append({'op': 'create', 'section': section, 'source_ids': source_ids})

        elif decision_type == 'CREATE_PARENT_GROUP':
            section = d.get('section')
            source_ids = d.get('source_ids', [])
            if not section or not source_ids:
                raise ValueError('CREATE_PARENT_GROUP requires section and source_ids')
            ops.append({'op': 'create_group', 'section': section, 'source_ids': source_ids})
            parent_id = f"{section}@{source_ids[0]}"
            for child in d.get('child_records', []):
                ops.append({'op': 'link_parent', 'record': child, 'parent': parent_id})

        elif decision_type == 'ATTACH_CHILD_TO_PARENT':
            record = d.get('record')
            parent = d.get('parent')
            if not record or not parent:
                raise ValueError('ATTACH_CHILD_TO_PARENT requires record and parent')
            ops.append({'op': 'link_parent', 'record': record, 'parent': parent})

        elif decision_type == 'MERGE_CONTINUATION':
            records = d.get('records', [])
            if len(records) < 2:
                raise ValueError('MERGE_CONTINUATION requires at least 2 records')
            ops.append({'op': 'merge', 'records': records})

        elif decision_type == 'KEEP_SEPARATE':
            pass  # Valid boundary confirmation

        elif decision_type == 'UNRESOLVED':
            source_ids = d.get('source_ids', [])
            if not source_ids:
                raise ValueError('UNRESOLVED requires source_ids')
            ops.append({'op': 'review', 'source_ids': source_ids})

        else:
            raise ValueError(f'Unsupported decision: {decision_type}')

    return ops


def finalize_ownership(elements, result, *, settings=None, transport=None, review=False):
    """Always audit locally; optionally perform budgeted configured-provider review using context-aware chunks."""
    from local_api.services.llm_section_review import ReviewSettings, ReviewError, call_deepseek
    if result.metadata.get('structure_review', {}).get('status') == 'provisional' and not review:
        validated_ownership_state(elements, result)
        return result.model_copy(deep=True)
    from local_api.services.employer_context import recover_employer_context
    result = recover_employer_context(result)
    from local_api.services.project_hierarchy import recover_project_groups
    result = recover_project_groups(result)
    state = snapshot(elements, result)
    out = result.model_copy(deep=True)
    from local_api.services.resume_sections import ANCHORS, ALIASES
    from local_api.services.resume_structure import heading_boundary
    import re
    operations = role_boundary_operations(state)
    if operations:
        state = apply_operations(state, operations, set(ANCHORS))
        out = materialize(elements, out, state)
        state = snapshot(elements, out)
    for section in out.sections:
        if section.category == 'experience':
            for entry in section.entries:
                titles = entry.fields.get('title', [])
                employers = entry.fields.get('employer', [])
                if titles and employers and min(employers) > min(titles):
                    entry.relationship_status = 'needs_review'
                    entry.review_reasons = sorted(set(entry.review_reasons + ['employer_after_first_role']))
                if employers:
                    emp_text = section.blocks[employers[0]].text.strip()
                    if heading_boundary(emp_text, ALIASES)[0] == 'experience' or re.match(r'^(?:work\s+history|experience\s+history|professional\s+experience)\b', emp_text, re.I):
                        entry.relationship_status = 'needs_review'
                        entry.review_reasons = sorted(set(entry.review_reasons + ['heading_as_employer']))
                if not titles and employers:
                    entry.relationship_status = 'needs_review'
                    entry.review_reasons = sorted(set(entry.review_reasons + ['missing_title']))
        elif section.category == 'awards':
            for entry in section.entries:
                text = ' '.join(section.blocks[i].text for i in entry.block_indices)
                award_matches = list(re.finditer(r'\b(?:Awarded\s+as|Won\s+|Winner\s+of|Received\s+|Achieved\s+)\b', text, re.I))
                if len(award_matches) > 1:
                    entry.relationship_status = 'needs_review'
                    entry.review_reasons = sorted(set(entry.review_reasons + ['potential_merged_records']))
                if entry.block_indices:
                    last_text = section.blocks[entry.block_indices[-1]].text.strip()
                    if re.search(r'\b(?:in|at|for|to|with|and|or|of)\s*$', last_text, re.I):
                        entry.relationship_status = 'needs_review'
                        entry.review_reasons = sorted(set(entry.review_reasons + ['potential_multiline_continuation']))
    state = snapshot(elements, out)
    status = {'status': 'not_requested', 'provider_calls': 0}
    if review:
        settings = settings or ReviewSettings.from_env()
        status['status'] = 'disabled'
        if settings.enabled and (settings.api_key or transport):
            payload = ambiguity_package(state, out)
            feedback = {'ambiguities': payload.get('ambiguities', [])}
            previous_calls = result.metadata.get('llm_review', {}).get('provider_calls', 0)
            if review == 'ambiguous' and not payload['ambiguities']:
                status['status'] = 'not_needed'
            elif previous_calls >= settings.max_total_requests or settings.max_units < 1:
                status['status'] = 'budget_exceeded'
            else:
                try:
                    settings.validate()
                    from local_api.services.review_chunking import run_structural_chunks, new_budget, ChunkError
                    budget = new_budget(settings)
                    budget.total = previous_calls
                    exec_transport = transport or call_deepseek
                    out = run_structural_chunks(
                        elements, state, out, settings, exec_transport,
                        budget=budget, feedback=feedback
                    )
                    status = out.metadata.get('structure_review', status)
                    state = snapshot(elements, out)
                except (ValueError, TypeError, KeyError, RuntimeError, ReviewError, ChunkError) as exc:
                    from local_api.services.review_chunking import ChunkError
                    from local_api.services.llm_section_review import FAILURE_MESSAGES
                    status['provider_calls'] = budget.total
                    if str(exc) == 'request_budget_exhausted':
                        status['status'] = 'budget_exceeded'
                    else:
                        status['status'] = 'rejected'
                        status['error_code'] = exc.args[0] if isinstance(exc, (ReviewError, ChunkError)) and exc.args and exc.args[0] in FAILURE_MESSAGES else 'invalid_structural_operations'
                        if isinstance(exc, (ValueError, ChunkError)):
                            status['validation_reason'] = str(exc)
    out.metadata['source_ownership'] = state.payload()
    out.metadata['structure_review'] = status
    if status['status'] in {'rejected', 'budget_exceeded'} or any(o.status == 'needs_review' for o in state.owners.values()):
        out.status = 'needs_review'
    return out
