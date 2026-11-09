import os
import json
import hashlib
from pathlib import Path

def main():
    repo = Path('/home/zoyaharmain/unstructured-IO')
    resumes_flat = Path('/mnt/c/Users/LENOVO/Eragina Digital Solutions Private Limited/Eragina Digital - RESUMES/Old/resume/RESUMES_FLAT')

    # LLM test directories and ground truth directories
    search_dirs = [
        'reports/live-deepseek-test-5-resumes-20261105',
        'reports/live-five-new-resumes-20261105',
        'reports/live-next-10-schema-mapping-20261106',
        'reports/deepseek-schema-full350-20261022',
        'reports/deepseek-schema-pilot10-20261022',
        'reports/deepseek-schema-pilot30-20261022',
        'reports/deepseek-schema-pilot5-20261022',
        'reports/deepseek-schema-pilot5-v2-20261022',
        'reports/pilot100-additional-llm-20261021-025143',
        'reports/pilot100-fixed-llm-20261021-041000',
        'reports/pilot250-llm-20261021-004616',
        'reports/resume-batch-10-llm-20261027',
        'reports/single-jayesh-feedback-live-20261022',
        'ground_truth',
        'resume ground truth',
        'tests/fixtures'
    ]

    print("Indexing LLM and GT directory tokens...")
    seen_tokens = set()
    seen_hashes = set()
    total_files = 0

    for sd in search_dirs:
        p = repo / sd
        if not p.exists():
            continue
        for f in p.glob('**/*'):
            if f.is_file():
                total_files += 1
                seen_tokens.add(f.name.lower())
                seen_tokens.add(f.stem.lower())
                stem_clean = f.stem.lower().split('(')[0].split('[')[0].strip()
                seen_tokens.add(stem_clean)
                
                # Check for hashes or text
                if f.suffix in ('.json', '.csv', '.md', '.txt', '.log'):
                    try:
                        content = f.read_text(errors='ignore').lower()
                        for line in content.splitlines():
                            for word in line.split():
                                w = word.strip('"\'`:,;()[]{}<>')
                                if len(w) >= 5:
                                    seen_tokens.add(w)
                                    if len(w) == 64 and all(c in '0123456789abcdef' for c in w):
                                        seen_hashes.add(w)
                    except Exception:
                        pass

    print(f"Indexed {total_files} files; {len(seen_tokens)} tokens and {len(seen_hashes)} hashes.")

    # Now scan RESUMES_FLAT
    print("Scanning RESUMES_FLAT...")
    verified = []
    
    with os.scandir(resumes_flat) as it:
        for entry in it:
            if not entry.is_file() or not entry.name.lower().endswith('.pdf'):
                continue
            
            fname_lower = entry.name.lower()
            stem = Path(entry.name).stem.lower()
            stem_clean = stem.split('(')[0].split('[')[0].strip()
            
            if len(stem_clean) < 6:
                continue
                
            # Check if clean stem is in seen_tokens (exact set lookup O(1))
            if fname_lower in seen_tokens or stem in seen_tokens or stem_clean in seen_tokens:
                continue

            # Read file bytes to check sha256
            data = Path(entry.path).read_bytes()
            sha256 = hashlib.sha256(data).hexdigest().lower()
            if sha256 in seen_hashes:
                continue

            verified.append({
                'filename': entry.name,
                'path': entry.path,
                'sha256': sha256,
                'stem': stem_clean,
                'size': len(data)
            })
            print(f"Verified candidate #{len(verified)}: {entry.name} ({sha256[:12]}..., {len(data)} bytes)")
            if len(verified) >= 10:
                break

    output_path = repo / 'reports/live_candidates_verified.json'
    with open(output_path, 'w') as f:
        json.dump(verified, f, indent=2)
    print(f"Saved {len(verified)} verified candidates to {output_path}")

if __name__ == '__main__':
    main()
