"""Offline source spot-check metrics do not reuse a record for multiple jobs."""
from scripts.report_llm_resume_batch import employer_matches


def test_employer_core_matching_tolerates_punctuation_and_location_suffix():
    assert employer_matches(['Example Pvt. Ltd.'],[{'company':'EXAMPLE PVT LTD – Bengaluru'}])==1


def test_repeated_employers_require_separate_job_records():
    assert employer_matches(['Example','Example'],[{'company':'Example'}])==1
    assert employer_matches(['Example','Example'],[{'company':'Example'},{'company':'Example'}])==2


def test_company_mention_in_role_or_responsibility_is_not_recovery():
    assert employer_matches(['Example'],[{'company':'Other','role':'Analyst at Example'}])==0
    assert employer_matches(['Example'],[{'responsibilities':['Worked with Example']}])==0


def test_partial_company_candidates_use_maximum_matching():
    assert employer_matches(['Example','Example Labs'],[{'company':'Example Labs'},{'company':'Example'}])==2
