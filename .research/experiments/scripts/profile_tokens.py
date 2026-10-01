#!/usr/bin/env python3
"""Literal profiling only, no semantics/training. Optional paths: max two.
Integer validity: runtime int(token,10). Whitelisted first tokens, else OTHER.
Counts: complete accepted lines; hashes: separately stated byte prefix."""
import time
START = time.monotonic()
import datetime, hashlib, json, os, signal, stat, sys
from pathlib import Path
CAP, RAM, WALL = 65536, 512 * 1024 * 1024, 115.0
DEADLINE = START + WALL
SAFE = {s for t in ('R', 'W', 'READ', 'WRITE', 'F', 'FLUSH', 'D', 'DISCARD', 'T', 'TRIM') for s in (t.encode(), t.lower().encode())}
report = {'kind': 'exploratory_literal_profile', 'status': 'not_started',
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'limits': {'wall_seconds_total': WALL, 'address_space_bytes': RAM, 'line_bytes': CAP},
          'rules': {'delimiter': 'binary ASCII whitespace', 'comment_prefix': '# after whitespace',
                    'op_tokens': sorted(s.decode('ascii') for s in SAFE), 'other': 'OTHER',
                    'integers': 'int(token,10), fields after first, noncomment rows only'}, 'files': []}
def timeout(signum, frame):
    raise TimeoutError()
def check():
    if time.monotonic() >= DEADLINE:
        raise TimeoutError()
def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
def metadata(s):
    return {'size_bytes': s.st_size, 'mtime_ns': s.st_mtime_ns}

def profile(path, r):
    prefix = (hashlib.sha256(), 0)
    before = None
    r.update(status='partial', eof=False, counts={'rows': 0, 'nonempty': 0, 'blank': 0,
             'comment': 0, 'field_counts': {}, 'first_tokens': {}, 'integer_valid': 0,
             'integer_invalid': 0, 'counted_prefix_bytes': 0})
    try:
        check(); r['path'] = str(path); before = path.stat(); r['before'] = metadata(before)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError()
        with path.open('rb', buffering=CAP) as f:
            if identity(os.fstat(f.fileno())) != identity(before):
                raise RuntimeError()
            while True:
                check(); line = f.readline(CAP + 1)
                if not line:
                    r['eof'] = True; break
                h = prefix[0].copy(); h.update(line); prefix = (h, prefix[1] + len(line))
                check()
                if len(line) > CAP:
                    raise OverflowError()
                c = r['counts'].copy()
                c['field_counts'] = c['field_counts'].copy(); c['first_tokens'] = c['first_tokens'].copy()
                fields = line.split(); c['rows'] += 1; c['counted_prefix_bytes'] += len(line)
                c['nonempty' if fields else 'blank'] += 1
                k = str(len(fields)); c['field_counts'][k] = c['field_counts'].get(k, 0) + 1
                if fields and line.lstrip().startswith(b'#'):
                    c['comment'] += 1
                elif fields:
                    op = fields[0].decode('ascii') if fields[0] in SAFE else 'OTHER'
                    c['first_tokens'][op] = c['first_tokens'].get(op, 0) + 1
                    for token in fields[1:]:
                        check()
                        try:
                            int(token, 10); c['integer_valid'] += 1
                        except ValueError:
                            c['integer_invalid'] += 1
                check(); r['counts'] = c
            if identity(os.fstat(f.fileno())) != identity(before):
                raise RuntimeError()
    except Exception as exc:
        r['error_type'] = type(exc).__name__
    finally:
        try:
            after = path.stat(); r['after'] = metadata(after)
            r['stable'] = before is not None and identity(before) == identity(after)
        except Exception as exc:
            r['stable'] = False; r['stat_error_type'] = type(exc).__name__
        full = r['eof'] and r['stable'] and 'error_type' not in r and prefix[1] == before.st_size
        r['status'] = 'stable_eof_full' if full else 'partial_or_failed'
        r['hashed_prefix_bytes'] = prefix[1]
        r['sha256_full_bytes_at_eof' if full else 'sha256_partial_prefix'] = prefix[0].hexdigest()

try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (RAM, RAM))
    signal.signal(signal.SIGALRM, timeout); signal.setitimer(signal.ITIMER_REAL, max(0.001, DEADLINE - time.monotonic()))
    report['runtime'] = {'python': sys.version, 'platform': sys.platform + ' ' + os.uname().release + ' ' + os.uname().machine, 'cpu_count': os.cpu_count()}
    source = Path(__file__).resolve(); report['script_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    paths = [Path(p) for p in sys.argv[1:]] or [source.parents[3] / 'dataset' / n for n in ('hm_0.csv', 'prxy_0.csv')]
    if len(paths) > 2: raise ValueError()
    report['files'] = [{'input_index': i, 'status': 'not_started'} for i in range(len(paths))]
    for path, r in zip(paths, report['files']):
        profile(path, r)
        if r['status'] != 'stable_eof_full': break
    report['status'] = 'complete' if all(r['status'] == 'stable_eof_full' for r in report['files']) else 'stopped'
except Exception as exc:
    report.update(status='stopped', error_type=type(exc).__name__)
finally:
    try: signal.setitimer(signal.ITIMER_REAL, 0)
    except Exception: pass
    report['elapsed_seconds'] = time.monotonic() - START
    report['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps(report, sort_keys=True)); sys.exit(0 if report['status'] == 'complete' else 1)
