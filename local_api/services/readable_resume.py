"""Adapt pinned repository grouping to immutable Unstructured source spans."""
import re

from local_api.vendor.resume_semantic_blocks import prepare_blocks, group_sections, ACTION, PERIOD, ROLE, ORG_SUFFIX

SECTION_NAMES = {'personal_information': 'Header', 'summary': 'Summary',
                 'experience': 'Experience', 'projects': 'Projects',
                 'education': 'Education', 'skills': 'Skills',
                 'certifications': 'Certifications', 'awards': 'Awards',
                 'publications': 'Publications'}
HEADINGS = {'section_heading', 'structural_heading'}


def readable_groups(section, elements):
    """Return a tree whose leaves partition the original section block indices.

    Derived repository strings label groups only. Displayed body text always
    comes from original spans, including duplicates and rows the parser ignores.
    Separate layout lanes are never passed to a shared employer/role context.
    """
    nodes = []
    for lane in dict.fromkeys(block.lane for block in section.blocks):
        indices = [i for i, b in enumerate(section.blocks) if b.lane == lane]
        metas, layout = [], []
        for line, index in enumerate(indices):
            block = section.blocks[index]
            metas.append({'line_index': line, 'line': block.text,
                          'section': SECTION_NAMES.get(section.category, section.label),
                          'section_id': f'{section.category}:{lane}',
                          'is_header': block.assignment in HEADINGS})
            layout.append({'text': block.text, 'page': block.page_number, 'block_index': index})
        pre = {'line_meta': metas, 'sentence_meta': [], 'sentences': []}
        rows = prepare_blocks(pre, layout)
        if section.category == 'experience':
            for row in rows:
                period = PERIOD.search(row['text'])
                prefix = row['text'][:period.start()].strip(' |–—-()') if period else ''
                first_word = prefix.split()[0] if prefix else ''
                if (row['block_type'] == 'RESPONSIBILITY' and period and ROLE.search(prefix)
                        and len(prefix.split()) <= 12 and not ORG_SUFFIX.search(prefix)
                        and ' at ' not in prefix.casefold()
                        and (not ACTION.search(prefix) or ROLE.fullmatch(first_word))):
                    row.update(block_type='ROLE', entities={'designation': prefix, 'period': period[0],
                                                           'start_date': period[1], 'end_date': period[2]})
            # A slash explicitly continues an employer name onto the next line.
            # Repair classifier input only; immutable source spans stay separate.
            for left, right in zip(rows, rows[1:]):
                if (left['text'].rstrip().endswith('/') and len(left['text'].split()) <= 12
                        and not ACTION.search(left['text'])
                        and right['block_type'] in {'COMPANY', 'COMPANY_ROLE'}
                        and PERIOD.search(right['text'])):
                    fields = dict(right['entities'])
                    fields['company'] = left['text'].strip() + ' ' + fields.get('company', right['text'])
                    for field in ('designation', 'period', 'start_date', 'end_date'):
                        fields.pop(field, None)
                    left.update(block_type='COMPANY', entities=fields)
                    # The employer already owns this period. Keep the second
                    # source line at employer level instead of creating a
                    # placeholder role before the actual role header.
                    right.update(block_type='PAGE_ARTIFACT', entities={}, wrapped_employer_owner_id=left['id'])
        grouped = group_sections(rows)
        by_id = {row['id']: row for row in rows}
        for row in rows:
            if row.get('wrapped_employer_owner_id'):
                row['destination'] = by_id[row['wrapped_employer_owner_id']].get('destination')
        if section.category != 'experience':
            # Projects and education use the same repository ownership paths;
            # ordinary prose/list sections are one readable block per lane.
            by_path = {}
            for row in rows:
                index = indices[row['line_index']]
                if section.blocks[index].assignment in HEADINGS:
                    continue
                path = row.get('destination') or ''
                match = re.match(r'^\$\.(?:projects|education)\[\d+\]', path)
                key = match[0] if match else 'section'
                by_path.setdefault(key, []).append(index)
            for owned in by_path.values():
                nodes.append({'kind': 'content', 'title': '', 'block_indices': owned, 'children': []})
            continue
        employers = {}
        for group in grouped['groups'].values():
            if group['key'] == 'work_history':
                for record in group['value']:
                    employers[len(employers)] = record
        paths = {}
        for row in rows:
            index = indices[row['line_index']]
            if section.blocks[index].assignment in HEADINGS:
                continue
            path = row.get('destination') or ''
            match = re.match(r'^\$\.work_history\[(\d+)\](?:\.roles\[(\d+)\])?', path)
            company_id = int(match[1]) if match else None
            role_id = int(match[2]) if match and match[2] is not None else None
            # Every source span receives one visible owner, even if repository
            # cleaning marked it an artifact or deduplicated its field value.
            key = (company_id, role_id)
            paths.setdefault(key, []).append(index)
        parent_nodes = {}
        for (company_id, role_id), owned in paths.items():
            record = employers.get(company_id, {})
            if company_id not in parent_nodes:
                parent_nodes[company_id] = {'kind': 'employer', 'title': record.get('company') or 'Work history',
                                            'block_indices': [], 'children': []}
                nodes.append(parent_nodes[company_id])
            parent = parent_nodes[company_id]
            if role_id is None:
                parent['block_indices'].extend(owned)
            else:
                roles = record.get('roles', [])
                role = roles[role_id] if role_id < len(roles) else {}
                parent['children'].append({'kind': 'role', 'title': role.get('designation') or 'Role and responsibilities',
                                           'block_indices': owned, 'children': []})
    headings = [i for i, block in enumerate(section.blocks) if block.assignment in HEADINGS]
    for index in headings[1:]:
        nodes.append({'kind': 'subheading', 'title': '', 'block_indices': [index], 'children': []})
    def leaves(node):
        return node['block_indices'] + [index for child in node['children'] for index in leaves(child)]
    actual = [index for node in nodes for index in leaves(node)]
    expected = [index for index, block in enumerate(section.blocks) if index not in headings[:1]]
    missing = [index for index in expected if index not in set(actual)]
    if missing:
        nodes.append({'kind': 'content', 'title': '', 'block_indices': missing, 'children': []})
        actual.extend(missing)
    if sorted(actual) != expected or len(actual) != len(set(actual)):
        raise RuntimeError('Readable groups must preserve every non-heading source span exactly once')
    nodes.sort(key=lambda node: min(leaves(node), default=-1))
    return nodes
