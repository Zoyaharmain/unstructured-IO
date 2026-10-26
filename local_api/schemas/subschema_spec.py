"""Deterministic child-field registry derived from the existing resume contract."""
import re
from local_api.vendor.handoff_schema.models import (
    ContactInfo, WorkExperience, Education, Project, Certification, CategorizedSkills,
)


def fields(model):
    schema = model.model_json_schema()['properties']
    return {name: {'type': 'string', 'multiple': prop.get('type') == 'array'}
            for name, prop in schema.items()}


SUBSCHEMAS = {
    'personal_information': fields(ContactInfo) | {'professional_title': {'type': 'string', 'multiple': False}},
    'summary': {'statements': {'type': 'string', 'multiple': True},
                'total_experience_years': {'type': 'number', 'multiple': False}},
    'experience': fields(WorkExperience), 'education': fields(Education),
    'projects': fields(Project), 'certifications': fields(Certification),
    'skills': fields(CategorizedSkills),
}
# Existing detected categories with no legacy ResumeSchema slot. These are
# explicit, conservative attribute slots, not model-generated schema names.
for parent, names in {
    'awards': ('name', 'issuer', 'date'),
    'publications': ('title', 'publisher', 'date', 'url'),
    'volunteering': ('organization', 'role', 'dates', 'activities'),
    'languages': ('language', 'proficiency'), 'interests': ('interest',),
    'references': ('name', 'relationship', 'organization', 'email', 'phone', 'availability'),
}.items():
    SUBSCHEMAS[parent] = {name: {'type': 'string', 'multiple': name in {'activities', 'interest', 'language', 'proficiency'}} for name in names}
SUBSCHEMAS['needs_review'] = {}

LEGACY_PARENTS = {'personal_information': 'contact', 'summary': 'summary',
                  **{key: key for key in ('experience', 'education', 'projects', 'certifications', 'skills', 'languages')}}
REPEATED = frozenset({'experience', 'education', 'projects', 'certifications'})


def valid_field_shape(parent, child, value):
    # A narrow sanity check, not a semantic name recognizer. Unknown identity
    # remains unresolved rather than being inferred from email or file names.
    if parent == 'personal_information' and child == 'full_name':
        return isinstance(value, str) and '@' not in value and not re.search(r'\d|\(cid:', value)
    return True


def hierarchy_definition():
    return {'version': 1, 'parents': SUBSCHEMAS, 'legacy_parents': LEGACY_PARENTS,
            'missing_policy': 'unresolved does not establish absence from the PDF',
            'field_names': 'Existing ResumeSchema names retained; no renamed legacy fields',
            'evidence_policy': 'Each item requires an exact quote in a record-local source block',
            'query_path': 'parent.child with optional record_id; results preserve record boundaries'}
