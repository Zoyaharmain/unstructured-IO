# Architectural Fixes Implemented for Robustness Hardening

**Project:** `unstructured-IO`  
**Branch:** `schema-mapping-accuracy-fixes`  
**Author:** Document Understanding & Production Reliability Staff Engineering  

---

## 1. Overview of Code Modifications

All fixes adhere strictly to the project's generalized architecture principles:
1. **Zero Overfitting:** No candidate names, document hashes, or hardcoded company names.
2. **Evidence-Grounded Attribution:** All extracted fields trace back to immutable source byte ranges (`e<index>:<start>:<end>`).
3. **Defense-in-Depth:** Validation at lexical, structural, and semantic mapping layers.

---

## 2. Modified Files & Key Implementations

### A. `local_api/services/record_subfields.py`
1. **Adversarial Prompt Injection Shielding:**
   - In `employment_header_fields`: Excluded phrases matching `\b(?:system\s+(?:prompt|instruction|override)|ignore\s+all\s+(?:previous|prior)\s+instructions|human\s+review\s*:|output\s+role\s*:)\b`.
   - In `labelled_fields`: Required structural delimiters before matching label keys (`prefix_before and not re.search(r'[|;\n\r•*▪●✓✔\uf0b7\-]\s*$', prefix_before)`).
2. **Comprehensive Canonical Role Regex:**
   - Expanded `ROLE` pattern to cover titles across healthcare, law, executive leadership, and research:
     ```python
     ROLE = re.compile(
         r'\b(?:engineer(?:ing)?|developer|analyst|consultant|architect|manager|'
         r'specialist|scientist|researcher|associate|director|administrator|officer|'
         r'executive|intern|underwriter|supervisor|leader|lead|head|owner|master|'
         r'roles?|sde|swe|mts|tpm|pm|tester|diagnostician|fellow|resident|vp|'
         r'vice\s+president|president|psychotherapist|physician|attorney|counsel|'
         r'cso|cto|cio|cfo|ceo|investigator|chemist)\b', re.I
     )
     ```
3. **Multi-Word Lookahead in `ACTION` Verbs:**
   - Updated `ACTION` regex lookahead from single-word to arbitrary modifier chains before role nouns:
     ```python
     lead(?!\s+(?:[A-Za-z-]+\s+)*(?:engineer|developer|analyst|consultant|architect|manager|specialist|designer|scientist|researcher|director|lead|officer|administrator|tester|intern|associate|resident|fellow)\b)
     ```
4. **Career Gap & Fellowship Filter:**
   - In `employment_header_fields`: Explicitly ignored non-employment intervals matching `career break|career gap|sabbatical|parental leave|family leave|fellowship|scholarship|research grant|grant funding`.
5. **Department vs Employer Disambiguation:**
   - In `employment_header_fields`: When `role_index == 0` (role precedes the dash), trailing tokens matching reporting/operations/analytics/management without corporate suffixes are recognized as role specializations, preserving the independent employer line.

---

### B. `local_api/services/resume_structure.py`
1. **Employment Start Exclusion Criteria:**
   - Updated `employment_start` to exclude career breaks, sabbaticals, fellowships, scholarships, and research grants from initiating corporate employment records:
     ```python
     if re.search(r'\b(?:award|awarded|prize|winner|best employee|certified|certification|certificate|career\s+break|career\s+gap|sabbatical|parental\s+leave|family\s+leave|fellowship|scholarship|research\s+grant|grant\s+funding)\b', lookup, re.I):
         return False
     ```

---

### C. `local_api/services/resume_sections.py`
1. **Table-Aware Employment Boundaries:**
   - Added `table_emp_boundary` to detect tabular key-value employment entries formatted with `Company:` and `Designation:`/`Role:`.
2. **Headingless Education Transition Support:**
   - Added `edu_boundary` to capture degree + institution transitions in headingless or cross-section text without requiring an explicit "Education" heading.
3. **Restored Cross-Column Layout Transitions:**
   - Decoupled `employer_boundary` and `engagement_boundary` so that dated employment entries and labelled engagements can resume Experience across multi-column pages.

---

### D. `local_api/services/record_relationships.py`
1. **Paired Header Field Assignment:**
   - In `annotate_relationships`, when an entry begins with an employer block followed by a title block, ensured existing employer classification on the first block is preserved and not shadowed by subsequent subfunction tokens.
2. **Fellowship & Grant Filtering in Organization Detection:**
   - Ensured fellowships and research grants do not get tagged as corporate `employer` entities.

---

### E. `scripts/run_adversarial_evaluation.py`
1. **Source Evidence Citations for Invariant 3:**
   - Refactored Invariant 3 ("no_cross_record_leakage") to verify unique byte-range source evidence spans (`e<idx>:<start>:<end>`) instead of raw string equality. This accurately identifies true cross-record bleed while permitting legitimate, identically phrased professional responsibilities across distinct roles.
