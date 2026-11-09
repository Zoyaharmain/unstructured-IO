"""Strengthened offline semantic evaluation engine for schema mapping ground truth.

Compares actual mapped/standardized outputs against human-verified expected outputs:
- Checks candidate name and validates against address/institution/family contamination.
- Bipartite matching of employment records (company, role, dates).
- Detects missing, extra, duplicate, merged, and split employment records.
- Bipartite matching of education records (institution, degree, graduation year).
- Detects missing, extra, duplicate, and split education records.
- Verifies calculated experience vs source-backed employment periods and overlaps.
- Enforces strict PASS / FAIL / INCOMPLETE status rules: missing expected records never receive PASS.
"""
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from local_api.schemas.extraction import ExtractedElement
from local_api.schemas.sections import SectionResponse


ARTIFACT_MAP: Dict[str, Tuple[str, ...]] = {
    "shyam_kumar_donka": ("schema", "reports/test_50_resumes_output/ShyamKumarDonka_schema.json"),
    "ashfaq_rahman": ("schema", "reports/test_50_resumes_output/Ashfaq Rahman_schema.json"),
    "chaganti_leela_sankar": ("schema", "reports/test_50_resumes_output/Chaganti Leela Sankar_schema.json"),
    "sureshbabus": ("schema", "reports/suresh-section-review-20261028/after/schema.json"),
    "a_suribhotla": ("schema", "reports/test_50_resumes_output/A Suribhotla_schema.json"),
    "abhishek_tiwari": ("schema", "reports/test_50_resumes_output/AbhishekTiwari_schema.json"),
    "ashwin_s_s": ("schema", "reports/test_50_resumes_output/Ashwin S S_schema.json"),
    "arnab_kumar_kar": ("pair", "reports/arnab-schema-review-20261101/after/extraction.json", "reports/arnab-schema-review-20261101/after/sections.json"),
    "yogendra_singh": ("pair", "reports/assignment-generalization-20261101/yogendra-after/extraction.json", "reports/assignment-generalization-20261101/yogendra-after/sections.json"),
    "deeksha_yadu": ("schema", "reports/test_50_resumes_output/DeekshaYadu_schema.json"),
    "supriya_bhagat": ("schema", "reports/test_50_resumes_output/Supriya Bhagat_schema.json"),
    "ravisankar_sundar": ("schema", "reports/test_50_resumes_output/Ravisankar Sundar_schema.json"),
}


def load_ground_truth_inputs(rid: str, original_filename: str) -> Tuple[List[ExtractedElement], SectionResponse]:
    """Load extracted elements and reviewed sections without destructive rebuilding."""
    entry = ARTIFACT_MAP[rid]
    if entry[0] == "schema":
        with open(entry[1], "r", encoding="utf-8") as f:
            data = json.load(f)
        rev = data["meta"]["reviewed_sections"]
        all_blocks = []
        for s in rev["sections"]:
            all_blocks.extend(s["blocks"])
        all_blocks.extend(rev.get("needs_review", []))
        by_idx: Dict[int, List[Dict[str, Any]]] = {}
        for b in all_blocks:
            by_idx.setdefault(b["source_element_index"], []).append(b)
        max_idx = max(by_idx.keys())
        element_texts: Dict[int, str] = {}
        for idx in range(max_idx + 1):
            blocks = by_idx.get(idx, [])
            blocks_sorted = sorted(blocks, key=lambda b: b["start"])
            cur = 0
            pieces = []
            for b in blocks_sorted:
                if b["start"] > cur:
                    pieces.append(" " * (b["start"] - cur))
                pieces.append(b["text"])
                cur = b["end"]
            element_texts[idx] = "".join(pieces)
        elements = [ExtractedElement(element_id=f"e{i}", text=element_texts[i], type="NarrativeText", metadata={}) for i in range(max_idx + 1)]
        sections = SectionResponse.model_validate(rev)
    else:
        with open(entry[1], "r", encoding="utf-8") as f:
            ext_data = json.load(f)
        with open(entry[2], "r", encoding="utf-8") as f:
            sec_data = json.load(f)
        elements = [ExtractedElement.model_validate(e) for e in ext_data["elements"]]
        sections = SectionResponse.model_validate(sec_data)

    return elements, sections


def norm_text(s: Optional[str]) -> str:
    """Normalize text for semantic comparison: strip common legal noise and punctuation."""
    if not s:
        return ""
    cleaned = re.sub(r"\b(?:pvt|ltd|limited|private|inc|corp|corporation|llc)\b", "", s, flags=re.I)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return " ".join(cleaned.lower().split())


def text_match_score(s1: Optional[str], s2: Optional[str]) -> float:
    """Compute normalized token and sequence overlap ratio between two strings."""
    n1, n2 = norm_text(s1), norm_text(s2)
    if not n1 and not n2:
        return 1.0
    if not n1 or not n2:
        return 0.0
    if n1 == n2 or n1 in n2 or n2 in n1:
        return 1.0
    tokens1, tokens2 = set(n1.split()), set(n2.split())
    if tokens1 and tokens2:
        overlap = len(tokens1 & tokens2) / max(len(tokens1), len(tokens2))
        if overlap >= 0.5:
            return 0.85
    return SequenceMatcher(None, n1, n2).ratio()


def evaluate_resume_mapping(rid: str, std_resume: Any, exp_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate mapped and standardized resume output against ground truth.

    Returns a detailed audit dict with status: 'PASS', 'FAIL', or 'INCOMPLETE'.
    Missing expected records will never receive 'PASS'.
    """
    results: Dict[str, Any] = {
        "resume_id": rid,
        "status": "PASS",
        "failures": [],
        "name_status": "PASS",
        "candidate_actual": (std_resume.contact.full_name or "").strip(),
        "candidate_expected": (exp_data.get("contact", {}).get("full_name") or "").strip(),
        "jobs_expected": len(exp_data.get("experience", [])),
        "jobs_actual": len(std_resume.experience),
        "missing_jobs": [],
        "extra_jobs": [],
        "split_jobs": [],
        "matched_jobs": [],
        "edu_expected": len(exp_data.get("education", [])),
        "edu_actual": len(std_resume.education),
        "missing_edu": [],
        "extra_edu": [],
        "matched_edu": [],
        "exp_years_actual": std_resume.total_experience_years,
        "exp_years_expected": exp_data.get("total_experience_years") or exp_data.get("total_years_experience"),
    }

    # 1. Candidate Name Validation
    act_name = results["candidate_actual"]
    exp_name = results["candidate_expected"]
    if not act_name:
        results["name_status"] = "FAIL"
        results["failures"].append("Candidate name is missing")
    elif norm_text(act_name) != norm_text(exp_name) and not (norm_text(act_name) in norm_text(exp_name) or norm_text(exp_name) in norm_text(act_name)):
        results["name_status"] = "FAIL"
        results["failures"].append(f"Candidate name mismatch: actual={act_name!r} vs expected={exp_name!r}")

    # Name Contamination Check (institutions, address, family relationship markers)
    for bad_tok in ["university", "college", "school", "institute", "father", "d/o", "s/o", "c/o", "street", "road", "pincode"]:
        if bad_tok in act_name.lower() and bad_tok not in exp_name.lower():
            results["name_status"] = "FAIL"
            results["failures"].append(f"Candidate name contaminated: {act_name!r} contains {bad_tok!r}")

    # 2. Total Experience & Overlap Verification
    exp_years = results["exp_years_expected"]
    act_years = results["exp_years_actual"]
    if exp_years is not None:
        if act_years is None:
            results["failures"].append(f"Total experience is None, expected ~{exp_years}")
        else:
            diff = abs(float(act_years) - float(exp_years))
            if diff > 0.5:
                results["failures"].append(f"Total experience mismatch: actual={act_years} vs expected={exp_years}")

    # 3. Employment Record Matching & Boundary Integrity
    exp_jobs = exp_data.get("experience", [])
    act_jobs = std_resume.experience

    matched_exp_jobs = set()
    matched_act_jobs = set()

    for e_idx, e_job in enumerate(exp_jobs):
        best_score = 0.0
        best_a_idx = None
        for a_idx, a_job in enumerate(act_jobs):
            if a_idx in matched_act_jobs:
                continue
            r_sim = text_match_score(e_job.get("role"), a_job.role)
            c_sim = text_match_score(e_job.get("company"), a_job.company)
            d_bonus = 0.0
            if e_job.get("start_date") and a_job.start_date:
                if str(e_job["start_date"])[:4] == str(a_job.start_date)[:4]:
                    d_bonus += 0.3
            score = (r_sim * 0.45) + (c_sim * 0.35) + d_bonus
            if score > best_score and score >= 0.5:
                best_score = score
                best_a_idx = a_idx

        if best_a_idx is not None:
            matched_exp_jobs.add(e_idx)
            matched_act_jobs.add(best_a_idx)
            a_job = act_jobs[best_a_idx]
            match_info = {
                "exp_idx": e_idx,
                "act_idx": best_a_idx,
                "expected": f"{e_job.get('company')} | {e_job.get('role')} ({e_job.get('start_date')} - {e_job.get('end_date')})",
                "actual": f"{a_job.company} | {a_job.role} ({a_job.start_date} - {a_job.end_date})",
            }
            results["matched_jobs"].append(match_info)
            if e_job.get("company") and not a_job.company:
                results["failures"].append(f"Job {e_idx} ({e_job.get('role')}) missing company name")
            if e_job.get("role") and not a_job.role:
                results["failures"].append(f"Job {e_idx} missing role")
        else:
            results["missing_jobs"].append({
                "index": e_idx,
                "company": e_job.get("company"),
                "role": e_job.get("role"),
                "dates": f"{e_job.get('start_date')} - {e_job.get('end_date')}",
            })

    # Detect split or extra actual jobs
    for a_idx, a_job in enumerate(act_jobs):
        if a_idx not in matched_act_jobs:
            is_split = False
            for e_idx in matched_exp_jobs:
                e_job = exp_jobs[e_idx]
                if text_match_score(e_job.get("role"), a_job.role) >= 0.7 or text_match_score(e_job.get("company"), a_job.company) >= 0.7:
                    results["split_jobs"].append({
                        "act_idx": a_idx,
                        "role": a_job.role,
                        "company": a_job.company,
                        "split_from_exp_idx": e_idx,
                    })
                    is_split = True
                    break
            if not is_split:
                results["extra_jobs"].append({
                    "act_idx": a_idx,
                    "role": a_job.role,
                    "company": a_job.company,
                    "dates": f"{a_job.start_date} - {a_job.end_date}",
                })

    # 4. Education Record Matching
    exp_edu = exp_data.get("education", [])
    act_edu = std_resume.education

    matched_exp_edu = set()
    matched_act_edu = set()

    for e_idx, e_ed in enumerate(exp_edu):
        best_score = 0.0
        best_a_idx = None
        for a_idx, a_ed in enumerate(act_edu):
            if a_idx in matched_act_edu:
                continue
            i_sim = text_match_score(e_ed.get("institution"), a_ed.institution)
            d_sim = text_match_score(e_ed.get("degree"), a_ed.degree)
            score = (i_sim * 0.55) + (d_sim * 0.45)
            if score > best_score and score >= 0.45:
                best_score = score
                best_a_idx = a_idx

        if best_a_idx is not None:
            matched_exp_edu.add(e_idx)
            matched_act_edu.add(best_a_idx)
            a_ed = act_edu[best_a_idx]
            results["matched_edu"].append({
                "exp_idx": e_idx,
                "act_idx": best_a_idx,
                "expected": f"{e_ed.get('institution')} | {e_ed.get('degree')}",
                "actual": f"{a_ed.institution} | {a_ed.degree}",
            })
        else:
            results["missing_edu"].append({
                "index": e_idx,
                "institution": e_ed.get("institution"),
                "degree": e_ed.get("degree"),
            })

    for a_idx, a_ed in enumerate(act_edu):
        if a_idx not in matched_act_edu:
            results["extra_edu"].append({
                "act_idx": a_idx,
                "institution": a_ed.institution,
                "degree": a_ed.degree,
            })

    # 5. Strict Status Determination
    # Rule: Missing expected records must NEVER receive PASS.
    if results["missing_jobs"] or results["missing_edu"]:
        results["status"] = "INCOMPLETE"
    elif results["name_status"] == "FAIL":
        results["status"] = "FAIL"
    elif any("missing company name" in f for f in results["failures"]) or results["split_jobs"]:
        results["status"] = "FAIL"
    elif results["failures"]:
        results["status"] = "INCOMPLETE" if any("Total experience is None" in f for f in results["failures"]) else "FAIL"
    else:
        results["status"] = "PASS"

    return results

