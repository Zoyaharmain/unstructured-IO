"""Run every test module with bounded isolation and report all actual outcomes.

Ordinary pytest provider exclusions and credential fixtures remain active.
A timed-out module is reported incomplete; no skipped/unreached test is a pass.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from xml.etree import ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]


def run_module(module, output, timeout):
    name = module.stem
    log = output/(name+'.txt')
    xml = output/(name+'.xml')
    env = dict(os.environ, OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', HF_HUB_OFFLINE='1')
    started = time.monotonic()
    command = [sys.executable,'-m','pytest','-q',str(module),'--junitxml='+str(xml)]
    with log.open('w') as file:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=file, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            return {'module':str(module.relative_to(ROOT)), 'status':'timeout', 'seconds':round(time.monotonic()-started,2),
                    'tests':None,'passed':None,'failures':None,'errors':None,'skipped':None,'log':log.name}
    row = {'module':str(module.relative_to(ROOT)),'status':'complete' if code in (0,1,5) else 'runner_error',
           'exit_code':code,'seconds':round(time.monotonic()-started,2),'log':log.name}
    if xml.exists():
        cases = ET.parse(xml).getroot().findall('.//testcase')
        row.update(tests=len(cases), failures=sum(c.find('failure') is not None for c in cases),
                   errors=sum(c.find('error') is not None for c in cases), skipped=sum(c.find('skipped') is not None for c in cases))
        row['passed'] = row['tests']-row['failures']-row['errors']-row['skipped']
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--module-timeout',type=int,default=90)
    p.add_argument('--workers',type=int,default=3)
    args = p.parse_args()
    if args.output.exists() or not 1 <= args.workers <= 4 or args.module_timeout < 1:
        p.error('Use a new output, 1-4 workers and a positive timeout')
    args.output.mkdir(parents=True, mode=0o700)
    output = args.output.resolve()
    modules = sorted((ROOT/'tests').glob('test_*.py'))
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(run_module, m, output, args.module_timeout) for m in modules]
        for job in as_completed(jobs):
            results.append(job.result())
            print(json.dumps({'completed_modules':len(results),'total_modules':len(modules),
                              'last_status':results[-1]['status']}),flush=True)
            (output/'results.json').write_text(json.dumps(sorted(results,key=lambda r:r['module']),indent=2))
    summary = {'modules_attempted':len(results), 'complete_modules':sum(r['status']=='complete' for r in results),
               'timed_out_modules':sum(r['status']=='timeout' for r in results),
               'runner_error_modules':sum(r['status']=='runner_error' for r in results),
               'scope':'Every tests/test_*.py module; default live-provider exclusion retained; isolated module processes.'}
    for key in ('tests','passed','failures','errors','skipped'):
        summary[key] = sum(r.get(key) or 0 for r in results)
    summary['all_tests_completed'] = not summary['timed_out_modules'] and not summary['runner_error_modules']
    (output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
