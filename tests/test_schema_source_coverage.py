"""UI coverage distinguishes mapped substrings from truly unassigned text."""
import shutil
import subprocess
from pathlib import Path
import pytest


def test_source_coverage_uses_union_of_record_citations_and_keeps_missing_content():
    if not shutil.which('node'):
        pytest.skip('Node required for frontend coverage regression')
    source=Path('local_api/static/schema.js').read_text()
    function=source[source.index('function schemaSourceCoverage('):source.index('function renderSubschemas(')]
    checks=r'''
const section={category:'skills',records:[{attributes:[{name:'all_skills',items:[
 {evidence:[{source_id:'own',quote:'Program Management'}]},
 {evidence:[{source_id:'own',quote:'Vendor Management'}]}
]}]}]};
const mapped=schemaSourceCoverage(section,{source_id:'own',quote:'Leadership: Program Management · Vendor Management'});
if(mapped.remaining.length || !mapped.mappedFields.includes('skills.all_skills')) throw Error('Mapped list mislabelled unassigned');
const partial=schemaSourceCoverage(section,{source_id:'own',quote:'Program Management · Unmapped Capability'});
if(!partial.remaining.some(v=>v.includes('Unmapped Capability'))) throw Error('Missing capability hidden');
const foreign=schemaSourceCoverage(section,{source_id:'foreign',quote:'Program Management'});
if(!foreign.remaining.includes('Program Management')) throw Error('Foreign citation counted');
const heading=schemaSourceCoverage(section,{source_id:'e0:0:17',quote:'CORE COMPETENCIES'},[
 {source_element_index:0,start:0,end:17,assignment:'structural_heading'}]);
if(heading.remaining.length || heading.context[0]!=='CORE COMPETENCIES') throw Error('Heading is not context');
const repeated=schemaSourceCoverage(section,{source_id:'own',quote:'Program Management · Program Management'});
if(!repeated.remaining.length) throw Error('Ambiguous repeated quote silently covered');
'''
    subprocess.run(['node'],input=function+'\n'+checks,text=True,check=True,capture_output=True)
