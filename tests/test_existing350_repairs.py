import pytest
from local_api.services.record_relationships import dated_organization_header,field_kinds
from local_api.services.resume_structure import reviewed_employment_groups
from tests.test_structural_grouping import _elem,_block

@pytest.mark.parametrize('text',[
 'State Street (Apr 2019 - Dec 2025)',
 'NTT Data, Noida (November 2022- Currently working)',
 'Tech Mahindra, Noida (May 2022- October 2022)',
])
def test_parenthesized_organization_history_is_source_supported(text):
 assert dated_organization_header(text)
 assert 'employer' in field_kinds(text,'experience')

@pytest.mark.parametrize('text',[
 'Project Apollo (2019-2022)','Training (2019-2022)',
 'University College (2019-2022)','Software Engineer (2019-2022)',
 'Performed reconciliation (2019-2022)','Client Example (2019-2022)',
 'Skills (2019)','State Street (2019)',
])
def test_projects_duties_education_and_bare_dates_do_not_become_employers(text):
 assert not dated_organization_header(text)


def test_three_organizations_without_company_suffix_keep_distinct_duties():
 texts=['Work Experience:', 'NTT Data, Noida (November 2022- Currently working)',
 'Employment Summary:', 'Job Role: Network Engineering Specialist',
 'Configured the first employer network.',
 'Tech Mahindra, Noida (May 2022- October 2022)',
 'Employment Summary:', 'Job Role: Senior Associate Technical Support',
 'Supported the second employer clients.', 'Wipro Technology, Pune (2019-2022)',
 'Employment Summary:', 'Job Role: Student Computer Applications',
 'Prepared the third employer reports.']
 els=[_elem(t,y=.1+i*.04,bold=True) for i,t in enumerate(texts)]
 blocks=[_block(i,t) for i,t in enumerate(texts)]
 groups=reviewed_employment_groups(blocks,els)
 assert len(groups)==3
 assert 1 in groups[0]['block_indices'] and 4 in groups[0]['block_indices']
 assert 5 in groups[1]['block_indices'] and 8 in groups[1]['block_indices']
 assert 9 in groups[2]['block_indices'] and 12 in groups[2]['block_indices']

def test_repeated_table_cells_map_to_their_own_physical_rows():
 from local_api.services.pdf_section_layout import line_occurrences
 top={'key':'B.S.E.B','bbox':[.3,.38,.4,.39]}
 bottom={'key':'B.S.E.B','bbox':[.3,.40,.4,.41]}
 peers=[bottom,top]
 first=line_occurrences(r'B\.S\.E\.B','B.S.E.BB.S.E.B',peers,top)
 second=line_occurrences(r'B\.S\.E\.B','B.S.E.BB.S.E.B',peers,bottom)
 assert first[0].start()==0 and second[0].start()==7
 assert not line_occurrences(r'B\.S\.E\.B','B.S.E.B',peers,top)
