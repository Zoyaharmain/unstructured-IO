"""Live provider protocol check containing generated fiction only, no resume input."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():p.error('Output must be new')
    from local_api.schemas.extraction import ExtractedElement
    from local_api.schemas.sections import SectionBlock, SectionResponse
    from local_api.services.source_ownership import finalize_ownership
    from local_api.services.source_validation import validate_result
    from local_api.core.provider_env import load_provider_env
    from local_api.services.llm_section_review import ReviewSettings, call_deepseek
    # Deliberately generated generic test strings, never read from a document.
    texts = ['WORK EXPERIENCE','Fictional Example Employer Ltd','Software Engineer | 2019 - 2021',
             'Built an imaginary service across','regions.', 'Senior Engineer | 2021 - Present',
             'Led delivery of a fictional application.','SKILLS','Python, SQL']
    elements = [ExtractedElement(type='Footer' if i in {3,6} else 'Title',text=t,
        page_number=1 if i<4 else 2,metadata={'synthetic':True}) for i,t in enumerate(texts)]
    blocks = [SectionBlock(source_element_index=i,start=0,end=len(t),text=t,page_number=e.page_number,
              assignment='needs_review',lane='main',reason='Generated fictional integration fixture')
              for i,(t,e) in enumerate(zip(texts,elements))]
    local = SectionResponse(status='needs_review',sections=[],needs_review=blocks,metadata={},warnings=[])
    load_provider_env(ROOT/'.env')
    responses = []
    def transport(settings,messages):
        content=call_deepseek(settings,messages)
        responses.append(content)
        return content
    result=finalize_ownership(elements,local,settings=ReviewSettings.from_env(),transport=transport,review=True)
    errors=validate_result(elements,result)
    args.output.mkdir(parents=True,mode=0o700)
    for i,content in enumerate(responses):(args.output/f'provider-response-{i+1}.json').write_text(content)
    (args.output/'sections.json').write_text(result.model_dump_json(indent=2))
    summary={**result.metadata['structure_review'],'source_validation_errors':len(errors),
             'data_scope':'Generated fictional fixture only; no person or source resume',
             'unseen_resume_accuracy':'not_established'}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
