# Project URL mapping fix

The separate GitHub label and URL spans in Aditya's two final projects were already record-local, but the mapper only parsed inline labels. Standalone URL rows now populate the shared legacy and hierarchical URL field. Multiple distinct URL rows abstain with a review reason. Prose and email rows are not accepted.

- Essay Writer: github.com/av525/essay-writer-langgraph
- AI Customer Support: github.com/av525/ai-customer-support

285 network-blocked regression tests passed (19.96 seconds). Five saved resumes were replayed locally in offline-replay/ with zero provider calls. Legacy data changes against the previous verified replay are listed in data-changes.json; only the two URL fields changed. Original reports were not overwritten. No semantic accuracy claim is made.

Changed production file: local_api/services/record_subfields.py. Five regression cases added in tests/test_saved_hierarchical_defects.py, including exact record-local URL evidence and ambiguity/prose/email safeguards.
