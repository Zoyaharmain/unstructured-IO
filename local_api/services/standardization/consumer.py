"""Discoverable version-2 consumer schema derived from normalization contracts."""
from pydantic import ConfigDict, Field, create_model
from local_api.services.standardization.contracts import (
    StandardizedResumeSchema, StandardizedContactInfo, StandardizedWorkExperience,
    StandardizedEducation, StandardizedCertification, StandardizedProject,
)
from local_api.vendor.handoff_schema.models import CategorizedSkills


def projection(name, source, exclude=(), rename=None, extra=None):
    rename = rename or {}
    fields = {}
    for key, field in source.model_fields.items():
        if key.startswith('raw_') or key in exclude: continue
        annotation = field.annotation
        # Missing scalar text is null consistently, including legacy required strings.
        if annotation is str: annotation = str | None
        default = field.default_factory() if field.default_factory else None if field.is_required() else field.default
        target = rename.get(key, key)
        if target in {'date', 'start_date', 'end_date', 'issue_date', 'expiry_date'}:
            default = Field(default=default, pattern=r'^\d{4}(?:-\d{2}(?:-\d{2})?)?$')
        fields[target] = (annotation, default)
    fields.update(extra or {})
    return create_model(name, __config__=ConfigDict(extra='forbid', allow_inf_nan=False), **fields)


ConsumerContact = projection('ConsumerContact', StandardizedContactInfo, exclude={'phone_e164'})
ConsumerSkills = projection('ConsumerSkills', CategorizedSkills)
ConsumerExperience = projection('ConsumerExperience', StandardizedWorkExperience,
    exclude={'duration_is_approximate', 'duration_as_of', 'duration_status', 'start_date_iso',
             'end_date_iso', 'start_date_precision', 'end_date_precision'},
    extra={'stated_duration': (str | None, None)})
ConsumerEducation = projection('ConsumerEducation', StandardizedEducation,
    exclude={'start_year_iso', 'graduation_year_iso'}, rename={'start_year': 'start_date', 'graduation_year': 'end_date'})
ConsumerCertification = projection('ConsumerCertification', StandardizedCertification,
    exclude={'issue_year_iso'}, rename={'issue_year': 'issue_date'})
ConsumerProject = projection('ConsumerProject', StandardizedProject)
ConsumerResume = projection('ConsumerResume', StandardizedResumeSchema,
    exclude={'calculated_experience_years', 'calculated_experience_complete', 'calculated_experience_is_approximate', 'experience_overlap_detected'},
    extra={'contact': (ConsumerContact, ...), 'skills': (ConsumerSkills, ...),
           'experience': (list[ConsumerExperience], []), 'education': (list[ConsumerEducation], []),
           'certifications': (list[ConsumerCertification], []), 'projects': (list[ConsumerProject], [])})
