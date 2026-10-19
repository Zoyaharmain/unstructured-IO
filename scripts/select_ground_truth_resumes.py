"""Select exactly 15 representative resumes across page counts, layouts, and complexity.

Reproducible sampling with seed 42.
"""
import argparse
import json
from pathlib import Path
import random
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path('/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT')


def get_details(r, results_dir):
    art_path = results_dir / r['artifact']
    art = json.loads(art_path.read_text())
    sections = art['sections']['sections']
    lanes = set()
    category_counts = {}
    for s in sections:
        category_counts[s['category']] = len(s.get('entries', []))
        for b in s['blocks']:
            if b.get('lane'):
                lanes.add(b.get('lane'))
    is_two_col = 'left' in lanes and 'right' in lanes
    return {
        'file': r['file'],
        'pages': len(r.get('pages', [])),
        'coverage': r.get('assigned_text_percent', 0.0),
        'categories': r.get('categories', []),
        'two_col': is_two_col,
        'flags': r.get('flags', []),
        'elements': r.get('elements', 0),
        'words': r.get('words', 0),
        'artifact': r['artifact'],
        'category_counts': category_counts,
        'sha256': r.get('sha256'),
    }


def select_15(source_dir=DEFAULT_SOURCE, results_dir=ROOT / '.upstream/batch-validation', seed=42):
    random.seed(seed)
    with open(results_dir / 'results.jsonl') as f:
        records = [json.loads(l) for l in f if l.strip()]

    pdf_records = [r for r in records if r.get('extension', '').lower() == '.pdf' and r.get('artifact')]
    valid = []
    for r in pdf_records:
        art_path = results_dir / r['artifact']
        if not art_path.exists():
            continue
        valid.append(get_details(r, results_dir))

    # Stratified selection
    selected = []
    used_files = set()

    def pick_one(candidates, rationale):
        avail = [c for c in candidates if c['file'] not in used_files]
        if not avail:
            raise RuntimeError(f"No candidate available for: {rationale}")
        # Deterministic shuffle with seeded random
        choice = random.choice(avail)
        used_files.add(choice['file'])
        choice['selection_rationale'] = rationale
        selected.append(choice)
        return choice

    # 1. 1-Page Resumes (2)
    p1 = [c for c in valid if c['pages'] == 1]
    pick_one([c for c in p1 if not c['two_col'] and c['coverage'] >= 98.0],
             "1-page resume, standard single-column layout, high baseline coverage")
    pick_one([c for c in p1 if c['two_col']],
             "1-page resume, dense two-column / multi-lane layout")

    # 2. 2-Page Resumes (5)
    p2 = [c for c in valid if c['pages'] == 2]
    pick_one([c for c in p2 if not c['two_col'] and c['coverage'] >= 99.0],
             "2-page resume, standard linear single-column format, high coverage")
    pick_one([c for c in p2 if c['two_col'] and c['coverage'] >= 95.0],
             "2-page resume, distinct two-column split layout with sidebar")
    pick_one([c for c in p2 if c['coverage'] < 80.0],
             "2-page resume, low baseline coverage (<80%) with unassigned text and preamble challenges")
    pick_one([c for c in p2 if 'few_sections' in c['flags'] or len(c['categories']) <= 3],
             "2-page resume, sparse or unconventional section headings")
    pick_one([c for c in p2 if c['category_counts'].get('experience', 0) >= 3 and c['words'] > 500],
             "2-page resume, rich multi-entry work experience history")

    # 3. 3-Page Resumes (4)
    p3 = [c for c in valid if c['pages'] == 3]
    pick_one([c for c in p3 if 'skills' in c['categories'] and 'projects' in c['categories'] and c['coverage'] >= 98.0],
             "3-page resume, technical profile with rich skills matrix and multiple project entries")
    pick_one([c for c in p3 if c['two_col']],
             "3-page resume, multi-lane layout across multiple pages")
    pick_one([c for c in p3 if 'certifications' in c['categories'] and 'education' in c['categories']],
             "3-page resume, structured academic qualifications, certifications, and multi-page experience")
    pick_one([c for c in p3 if 'unassigned_text' in c['flags'] and c['coverage'] < 95.0],
             "3-page resume, challenging layout with unassigned text requiring LLM boundary recovery")

    # 4. 4-Page Resumes (2)
    p4 = [c for c in valid if c['pages'] == 4]
    pick_one([c for c in p4 if c['words'] > 1000],
             "4-page resume, senior extensive career history with numerous employment records")
    pick_one([c for c in p4 if c['two_col'] or len(c['categories']) >= 5],
             "4-page resume, multi-section comprehensive CV with education, projects, skills, and experience")

    # 5. 5+ Page Resumes (2)
    p5 = [c for c in valid if c['pages'] == 5]
    p6plus = [c for c in valid if c['pages'] >= 6]
    pick_one(p5, "5-page resume, long-form extensive project and engagement portfolio")
    pick_one(p6plus, "6+ page resume, complex multi-page document testing cross-page boundary continuity")

    assert len(selected) == 15, f"Expected exactly 15 resumes, got {len(selected)}"
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE, help="Source resumes folder")
    parser.add_argument('--copy-to', type=Path, default=ROOT / 'ground_truth/pilot_resumes', help="Destination folder for 15 pilot PDFs")
    parser.add_argument('--output-json', type=Path, default=ROOT / 'ground_truth/selected_15_resumes.json')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    selected = select_15(source_dir=args.source, seed=args.seed)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(selected, indent=2, ensure_ascii=False) + '\n')

    print(f"Successfully selected {len(selected)} resumes with seed {args.seed}:")
    for i, s in enumerate(selected, 1):
        print(f" {i:2d}. {s['file']} | {s['pages']} pages | cov={s['coverage']:.1f}% | 2-col={s['two_col']} | rationale: {s['selection_rationale']}")

    if args.copy_to and args.source.exists():
        args.copy_to.mkdir(parents=True, exist_ok=True)
        copied = 0
        for s in selected:
            src = args.source / s['file']
            if src.exists():
                dst = args.copy_to / s['file']
                shutil.copy2(src, dst)
                copied += 1
        print(f"Copied {copied}/{len(selected)} pilot PDFs to {args.copy_to}")


if __name__ == '__main__':
    main()

