'use strict';
// Processing status and semantic correctness are separate. Keep the original
// review failure in field_review even when usable local output is available.
function schemaOutcome(data, reviewRequested) {
  const meta = data.meta || {}, review = meta.field_review || {};
  const coverage = meta.source_coverage_ledger?.status_counts || {};
  const pending = Boolean(meta.missing_required_fields?.length || coverage.present_but_unmapped || coverage.present_but_ambiguous || meta.needs_review?.length || data.validation_status?.requires_human_review || data.validation_status?.is_valid === false || meta.completeness_check?.meaningful_unmapped_fragments || meta.completeness_check?.conflicting_field_overlaps?.length);
  let status = meta.mapping_result?.status || (reviewRequested && review.status !== 'complete'
    ? data.success ? 'fallback_used' : 'failed' : pending ? 'needs_review' : 'success');
  if (status === 'success' && pending) status = 'needs_review';
  const summaries = {
    fallback_used: 'DeepSeek field mapping did not complete. Source-bound local results are available, but require review.',
    needs_review: 'Schema assignment completed with items requiring review.',
    success: 'Schema assignment completed. Compare field values with the original resume.',
    failed: 'Schema assignment failed; no validated mapping result is available.'
  };
  const history = [...(review.diagnostics || [])];
  if (review.diagnostic && !history.some(d => d.id && d.id === review.diagnostic.id)) history.push(review.diagnostic);
  const reviewReasons = [];
  const completeness = meta.completeness_check || {};
  if (completeness.meaningful_unmapped_fragments) reviewReasons.push(`${completeness.meaningful_unmapped_fragments} source fragment(s) lack a field association`);
  if (completeness.conflicting_field_overlaps?.length) reviewReasons.push(`${completeness.conflicting_field_overlaps.length} overlapping field association(s) require review`);
  const standardizationIssues = (data.warnings || []).filter(w => ['warning', 'review_required'].includes(w.severity)).length;
  if (standardizationIssues) reviewReasons.push(`${standardizationIssues} standardization issue(s) require review`);
  if (meta.missing_required_fields?.length) reviewReasons.push(`${meta.missing_required_fields.length} required field(s) missing`);
  if (coverage.present_but_unmapped) reviewReasons.push(`${coverage.present_but_unmapped} field(s) unmapped`);
  if (coverage.present_but_ambiguous) reviewReasons.push(`${coverage.present_but_ambiguous} field(s) ambiguous`);
  if (meta.needs_review?.length) reviewReasons.push(`${meta.needs_review.length} source item(s) require review`);
  const omitted = (review.evidence_repairs || []).filter(r => ['unsupported_list_item_pruned', 'unsupported_optional_scalar_pruned', 'scalar_multiple_values_truncated'].includes(r.code)).length;
  if (omitted) reviewReasons.push(`${omitted} unsupported or conflicting provider item(s) omitted`);
  return {status, reviewReasons, recoveredDiagnostics: history.filter(d => d.recovered === true), message: review.status === 'partial' ? 'DeepSeek reviewed some sections. Failed sections retain local results and require review.' : summaries[status] || summaries.failed,
    className: status === 'failed' ? 'status error' : ['fallback_used', 'needs_review'].includes(status) ? 'status warning' : 'status',
    diagnostic: [...history].reverse().find(d => d.recovered !== true) || null};
}
if (typeof module !== 'undefined') module.exports = {schemaOutcome};
