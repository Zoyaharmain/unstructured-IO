"""Freeze a hash-verified PDF selection excluding every saved batch selection.

Selection only: no extraction, model loading, provider calls or approval claims.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.check_pilot_fallback import DEFAULT_FOLDER
from scripts.select_ground_truth_resumes import get_details


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_selections(reports):
    hashes=set();names=set();sources=[]
    for path in sorted(Path(reports).rglob('manifest.json')):
        data=json.loads(path.read_text())
        if 'selected' not in data:continue
        selected=data['selected']
        if not isinstance(selected,list):raise ValueError('Invalid selected list: '+str(path))
        for item in selected:
            if not isinstance(item,dict) or not re.fullmatch('[0-9a-fA-F]{64}',item.get('sha256','')) or not item.get('file'):
                raise ValueError('Invalid exclusion record: '+str(path))
            hashes.add(item['sha256'].lower());names.add(item['file'])
        if selected:sources.append({'manifest':str(path.resolve()),'sha256':sha(path),'selected_documents':len(selected)})
    if not hashes:raise ValueError('No previous selections found; refusing an unprotected selection')
    return hashes,names,sources


def choose(pool,count,seed,excluded_hashes,excluded_names):
    if count<1:raise ValueError('Count must be positive')
    buckets={}
    for item in sorted(pool,key=lambda x:x['file']):
        if item['sha256'].lower() in excluded_hashes or item['file'] in excluded_names:continue
        key=(min(item['pages'],5),item['two_col'],item['coverage']<95)
        buckets.setdefault(key,[]).append(item)
    rng=random.Random(seed)
    for items in buckets.values():rng.shuffle(items)
    selected=[];used_hashes=set();used_names=set()
    while len(selected)<count:
        progress=False
        for key in sorted(buckets):
            while buckets[key]:
                item=buckets[key].pop();digest=item['sha256'].lower()
                if digest in used_hashes or item['file'] in used_names:continue
                selected.append(item);used_hashes.add(digest);used_names.add(item['file']);progress=True;break
            if len(selected)==count:break
        if not progress:raise ValueError(f'Insufficient unseen distinct PDFs: requested {count}, available {len(selected)}')
    return selected


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',type=Path,default=DEFAULT_FOLDER)
    p.add_argument('--reports',type=Path,default=ROOT/'reports')
    p.add_argument('--pool',type=Path,default=ROOT/'.upstream/batch-validation')
    p.add_argument('--count',type=int,default=300);p.add_argument('--seed',type=int,default=42)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Output already exists; choose a new manifest path')
    hashes,names,sources=prior_selections(a.reports)
    pool=[]
    for row in json.loads((a.pool/'current-results.json').read_text()):
        if row.get('extension','').lower()!='.pdf' or row.get('status')!='processed':continue
        if row.get('sha256','').lower() in hashes or row['file'] in names:continue
        source=a.folder/row['file'];artifact=a.pool/row.get('artifact','')
        if not source.is_file() or not artifact.is_file() or sha(source)!=row.get('sha256'):continue
        pool.append({**get_details(row,a.pool),'original_source_path':str(source.resolve()),'bytes':source.stat().st_size})
    selected=choose(pool,a.count,a.seed,hashes,names)
    for item in selected:item['selection_rationale']=f'Seed{a.seed} stratified selection excluding union of saved batch hashes and filenames'
    # Refuse if history changes while source files are being checked.
    for source in sources:
        if sha(Path(source['manifest']))!=source['sha256']:raise ValueError('Prior manifest changed during selection')
    current_hashes,current_names,_=prior_selections(a.reports)
    if any(s['sha256'].lower() in current_hashes or s['file'] in current_names for s in selected):raise ValueError('Selection overlaps current batch history')
    result={'count':len(selected),'seed':a.seed,'selection':f'{a.count} unseen distinct PDFs; excludes union of all saved batch selections by hash and filename',
        'prior_distinct_hashes':len(hashes),'prior_distinct_filenames':len(names),'exclusion_manifests':sources,
        'disjoint_confirmed':True,'new_api_calls':0,'human_verified':False,'ready_for_production':False,'selected':selected}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'selected','exclusion_manifests'}},indent=2))
if __name__=='__main__':main()
