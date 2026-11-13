"""Conservative provenance audit and source-hash-disjoint dataset lifecycle.

Historical exposure never becomes unseen evaluation evidence. Absence from this
repository's audit is not proof of independence or of absence from model training.
"""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile

SUPPORTED = {'.pdf', '.docx', '.doc'}


def inventory(folder):
    by_hash = {}
    for path in sorted(Path(folder).rglob('*')):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED or path.name.startswith('~$'):
            continue
        digest = sha256(path.read_bytes()).hexdigest()
        item = by_hash.setdefault(digest, {'sha256':digest, 'paths':[], 'names':[], 'extensions':[]})
        item['paths'].append(str(path.resolve()))
        if '\n' in path.name or '\r' in path.name:
            raise ValueError('Unsupported newline in source filename')
        item['names'].append(path.name)
        if path.suffix.lower() not in item['extensions']:
            item['extensions'].append(path.suffix.lower())
    return list(by_hash.values())


def evidence_kind(path):
    parts = Path(path).parts
    if 'tests' in parts:
        return 'regression_testing'
    if 'ground_truth' in parts:
        return 'annotation_or_expected_output'
    if '.upstream' in parts:
        return 'previous_processing_or_inventory'
    if 'reports' in parts:
        return 'previous_evaluation_or_development'
    if 'manifests' in parts:
        return 'previous_selection'
    return 'development_reference'


def audit_usage(documents, roots):
    """Search exact byte hashes and literal filenames without opening document text.

    rg streams matched patterns, not full resume lines. Treat filename matches as
    conservative exposure evidence; retain hash-vs-name provenance explicitly.
    """
    lookup = defaultdict(set)
    for doc in documents:
        lookup[doc['sha256']].add(doc['sha256'])
        for name in doc['names']:
            lookup[name.casefold()].add(doc['sha256'])
    evidence = defaultdict(set)
    if not lookup:
        return []
    with tempfile.TemporaryDirectory(prefix='resume-provenance-') as temp:
        patterns = Path(temp)/'patterns.txt'
        patterns.write_text('\n'.join(sorted(lookup))+'\n')
        command = ['rg','--hidden','--no-ignore','--null','--no-heading','--no-line-number','-o','-i','-F',
                   '-f',str(patterns),'--glob','*.json','--glob','*.jsonl','--glob','*.py',
                   '--glob','*.md','--glob','*.csv','--glob','*.txt','--glob','!**/.git/**',
                   '--glob','!**/.venv/**','--glob','!**/node_modules/**',*[str(p) for p in roots if Path(p).exists()]]
        import shutil
        if not any(Path(p).exists() for p in roots):
            return [{**d, 'historical_evidence':[], 'training_use':'not_documented'} for d in documents]
        if shutil.which('rg'):
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                for line in process.stdout:
                    path, separator, match = line.rstrip('\n').partition('\0')
                    if not separator:
                        continue
                    token = match.casefold()
                    for digest in lookup.get(token, ()):
                        evidence[digest].add((path, 'source_sha256' if token == digest else 'literal_filename', evidence_kind(path)))
                error = process.stderr.read()
                code = process.wait()
                if code not in (0, 1):
                    raise RuntimeError('Provenance search failed; refusing to reserve held-out data')
        else:
            patterns_set = set(lookup.keys())
            globs = {'.json', '.jsonl', '.py', '.md', '.csv', '.txt'}
            for r in roots:
                rp = Path(r)
                if not rp.exists():
                    continue
                for path in rp.rglob('*'):
                    if not path.is_file() or path.suffix.lower() not in globs:
                        continue
                    if any(part in ('.git', '.venv', 'node_modules') for part in path.parts):
                        continue
                    try:
                        content = path.read_text(errors='ignore').casefold()
                        for token in patterns_set:
                            if token in content:
                                for digest in lookup.get(token, ()):
                                    evidence[digest].add((str(path), 'source_sha256' if token == digest else 'literal_filename', evidence_kind(str(path))))
                    except Exception:
                        continue
    # Source copies can be renamed original.pdf, so also compare their bytes.
    hashes = by_hash_set(documents)
    for root in roots:
        for path in Path(root).rglob('*'):
            if path.is_file() and path.suffix.lower() in SUPPORTED:
                digest = sha256(path.read_bytes()).hexdigest()
                if digest in hashes:
                    evidence[digest].add((str(path), 'source_sha256', evidence_kind(path)))
    return [{**doc, 'historical_evidence':[{'artifact':p,'match':m,'use':k} for p,m,k in sorted(evidence[doc['sha256']])],
             'training_use':'not_documented', 'training_caveat':'No claim about external pretraining or untracked use.'}
            for doc in documents]


def by_hash_set(documents):
    return {doc['sha256'] for doc in documents}


def make_splits(audited, *, seed='resume-ownership-v1', validation_fraction=.2, heldout_fraction=.2):
    if not 0 <= validation_fraction <= 1 or not 0 <= heldout_fraction <= 1 or validation_fraction+heldout_fraction > 1:
        raise ValueError('Invalid split fractions')
    if len(by_hash_set(audited)) != len(audited):
        raise ValueError('Deduplicate document hashes before splitting')
    splits = {'development':[], 'validation':[], 'held_out_test':[]}
    for doc in audited:
        score = int(sha256((seed+doc['sha256']).encode()).hexdigest(),16)/2**256
        if doc['historical_evidence']:
            split = 'development'
        elif score < heldout_fraction:
            split = 'held_out_test'
        elif score < heldout_fraction+validation_fraction:
            split = 'validation'
        else:
            split = 'development'
        splits[split].append({**doc, 'split':split,
                              'annotation_status':'not_independently_verified',
                              'independence_status':'previously_exposed' if doc['historical_evidence'] else 'requires_independence_attestation'})
    return splits


def validate_splits(splits):
    seen = set()
    for name in ('development','validation','held_out_test'):
        for doc in splits[name]:
            digest = doc['sha256']
            if digest in seen:
                raise ValueError('Source hash occurs in multiple dataset entries')
            if doc.get('split', name) != name:
                raise ValueError('Manifest entry has the wrong dataset split')
            seen.add(digest)
            if name != 'development' and doc.get('historical_evidence'):
                raise ValueError('Previously exposed resume cannot be reserved as unseen')
    return True


def validate_annotation(annotation, source_digest, *, held_out=False):
    """A parser prediction or LLM draft can never promote itself to gold."""
    if annotation.get('source_digest') != source_digest:
        raise ValueError('Annotation source digest mismatch')
    review = annotation.get('review', {})
    if annotation.get('annotation_origin') != 'independent_human':
        raise ValueError('Unlabeled templates and LLM-generated labels are not independent ground truth')
    if annotation.get('human_verified') is not True or review.get('method') != 'independent_human' or not review.get('reviewer_id'):
        raise ValueError('Independent human review is required')
    if review.get('saw_parser_predictions') is not False:
        raise ValueError('Annotation must be made without parser predictions')
    if held_out and (review.get('independence_attested') is not True or not review.get('adjudicator_id') or review['adjudicator_id'] == review['reviewer_id']):
        raise ValueError('Held-out labels require independent adjudication and independence attestation')
    return True
