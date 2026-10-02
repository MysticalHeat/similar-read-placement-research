"""UNRUN v0.3: one selected synthetic stage; D001 references are NOT permission.
Pending amendment/batch approval required externally. No retry or automatic stages.
Soft current-VmRSS observations, NOT whole-domain time/RAM/disk certification.
"""
import time
FIRST_WALL = time.monotonic()
INITIAL_CPU = time.process_time()  # absolute CPU, including initial CPU, charged once
import os
import sys
import resource
import signal
import stat
import json
import hashlib
import math
from pathlib import Path
from types import ModuleType
from contextlib import contextmanager

PROJECT = Path('/home/nomli/workspace/bdss_lab/research1')
S = '.research/experiments/scripts/'
CALLER = S + 'synthetic_deadline_caller_v0.3.py'
HELPER = S + 'synthetic_practical_caller_v0.1.py'
ADAPTER = S + 'synthetic_stage_adapter_v0.1.py'
AMENDMENT = '.research/protocol/synthetic-deadline-demo-v0.3.md'
BASE = '.research/experiments/control/synthetic-deadline-v0.3/'
ROOTS = dict(zip(('bootstrap', 'E004', 'E005'), (BASE+'bootstrap-002', BASE+'E004-001', BASE+'E005-001')))
REFS = {'bootstrap': 'D001', 'E004': 'D001.E004', 'E005': 'D001.E005'}
SCOPED = ('.research/experiments/configs/synthetic-temperature-demo-v0.1.json',
          '.research/protocol/synthetic-temperature-demo-v0.1.md',
          '.research/protocol/synthetic-preparation-approval-2026-10-01.md',
          '.research/protocol/synthetic-runtime-contract-v0.1.md',
          '.research/protocol/synthetic-controlled-launch-plan-v0.2.md',
          S+'synthetic_temperature_demo.py', S+'synthetic_models.py', ADAPTER)
EXTRA = (S+'synthetic_expectations.py', S+'test_synthetic_temperature_demo.py')
CAPS = {'inventory': 15, 'E004_preparation': 35, 'E005_fits': 40, 'prediction_metrics': 15, 'finalization': 15}
WORK = {'inventory': 12, 'E004_preparation': 32, 'E005_fits': 40, 'prediction_metrics': 13, 'finalization': 12}
DISPATCH = {'bootstrap': 15, 'E004': 35, 'E005': 70}
DISK, PER_FILE, NORMAL, FAILURE = 5242880, 2097152, 65536, 8192
REPORT = '.research/experiments/processed/synthetic-deadline-v0.3'
B001_REVIEW = '.research/reviews/bootstrap-B001-outcome-review-2026-10-02.md'
REPORT_BYTES, REPORT_ENTRIES, TOL = 32768, 8, 1e-6  # accounting tolerance, NOT statistical uncertainty
UNKNOWN = {'B001_costs': None, 'startup_wall_before_marker': None, 'after_last_clock_stdout_exit_tail': None,
           'tool_tail': None, 'whole_domain_RAM': None, 'quota_certificate': None, 'exit_code_observed': None}
def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)
def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)+'\n').encode('ascii')
def digest(data):
    return hashlib.sha256(data).hexdigest()
class Budget:
    def __init__(self):
        self.first, self.memory, self.latest, self.max_current = None, None, None, None
        self.phases, self.old = {p: [0., 0.] for p in CAPS}, [0., 0.]
        self.last, self.phase, self.fit, self.fits = [0., 0.], 'inventory', None, 0
        self.entry, self.reporting, self.link, self.prior_known = [0., 0.], False, None, False
        self.phase_prior_at_entry, self.return_link, self.max_gap, self.dispatch_cap = [0., 0.], None, 0., 15
        signal.signal(signal.SIGALRM, self.alarm)
        self.sample(True)  # BEFORE any guard, ownership, argv/path/census check
    def alarm(self, signum, frame):
        self.sample(memory=False)
        raise RuntimeError('soft wall alarm; scheduling/I/O/exit latency unbounded')
    def sample(self, force=False, memory=True):
        now, cpu = time.monotonic(), time.process_time()
        current = [now-FIRST_WALL, cpu]
        for i in range(2):
            require(current[i] >= self.last[i], 'worker clock regressed')
            self.phases[self.phase][i] += current[i]-self.last[i]
        self.last = current
        self.latest = {'worker_wall': current[0], 'worker_cpu': cpu, 'wall_source': 'time.monotonic-first_marker',
                       'cpu_source': 'absolute time.process_time; initial charged once'}
        if memory and (force or self.memory is None or now-self.memory['monotonic'] >= .25):
            self.max_gap = max(self.max_gap, 0. if self.memory is None else now-self.memory['monotonic'])
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
            self.memory = {'monotonic': now, 'current_VmRSS_bytes': None, 'kernel_peak_bytes': peak,
                           'source': '/proc/self/status VmRSS kB interpreted KiB; Linux SELF ru_maxrss KiB'}
            earliest = self.first is None
            if earliest:
                self.first = dict(self.memory)
            with open('/proc/self/status', 'rb') as f:
                data = f.read(16385)
            require(len(data) <= 16384 and len(data.splitlines()) <= 128, 'own status byte/line cap')
            rows = [r.split() for r in data.splitlines() if r.startswith(b'VmRSS:')]
            require(len(rows) == 1 and len(rows[0]) == 3 and rows[0][1].isdigit()
                    and len(rows[0][1]) <= 20 and rows[0][2] == b'kB', 'VmRSS parse/units STOP')
            self.memory['current_VmRSS_bytes'] = int(rows[0][1])*1024
            if earliest:
                self.first = dict(self.memory)
            self.max_current = self.memory['current_VmRSS_bytes'] if self.max_current is None else max(self.max_current, self.memory['current_VmRSS_bytes'])
        return tuple(self.old[i]+current[i] for i in range(2))
    def check(self, work=False, force=False):
        total = self.sample(force, memory=not self.reporting)
        require(all(v < 120 for v in total) and all(v < CAPS[self.phase] for v in self.phases[self.phase])
                and all(v < self.dispatch_cap for v in self.last), 'full global/phase/dispatch target')
        require(self.fit is None or all(total[i]-self.fit[i] < 10 for i in range(2)), 'full per-fit target')
        if not self.reporting:
            require(self.memory['current_VmRSS_bytes'] is not None and self.max_current is not None and self.max_current < 1073741824, 'sampled current VmRSS target')
            if work:
                require(all(v < WORK[self.phase] for v in self.phases[self.phase]) and all(v < self.dispatch_cap-3 for v in self.last), 'work target / reserved finish time')
                require(self.fit is None or all(total[i]-self.fit[i] < 9 for i in range(2)), 'fit work9 / reserve1')
        return total
    def arm(self):
        total = self.check()
        remaining = min(120-total[0], CAPS[self.phase]-self.phases[self.phase][0], self.dispatch_cap-self.last[0])
        if self.fit is not None:
            remaining = min(remaining, 10-(total[0]-self.fit[0]))
        require(remaining > 0, 'no alarm reserve')
        signal.setitimer(signal.ITIMER_REAL, remaining)
    def origin(self, phase, fit):
        total = self.check()  # charge prior phase BEFORE snapshot/transition
        require(phase in CAPS, 'unregistered phase')
        if phase != self.phase:
            self.phase_prior_at_entry, self.entry = list(self.phases[phase]), list(total)
            self.phase, self.fit = phase, None
        origin = tuple(self.entry[i]-self.phase_prior_at_entry[i] for i in range(2))
        if fit is not None:
            require(phase == 'E005_fits' and type(fit) is int and fit == self.fits+1 and fit <= 4, 'fresh sequential fit1..4 only')
            self.fit, self.fits = self.check(True), fit
        self.arm()
        return origin if fit is None else self.fit
    def adopt(self, ledger, previous_hash, return_hash):
        self.sample(True)  # NEW startup retained; inventory entry is logical stage entry
        validate(ledger)
        phases, old = ledger['phase_totals'], ledger['observed_totals']
        self.entry, self.phase_prior_at_entry = list(old), list(phases['inventory'])
        for p in CAPS:
            self.phases[p] = [self.phases[p][i]+phases[p][i] for i in range(2)]
        self.old, self.link, self.prior_known = list(old), previous_hash, True
        self.return_link = return_hash
        self.check()
        self.arm()
    def ledger(self, status):
        total = self.sample(not self.reporting, memory=not self.reporting)
        return {'status': status, 'observed_totals': list(total), 'phase_totals': {p: list(v) for p, v in self.phases.items()},
                'targets': CAPS, 'previous_receipt_sha256': self.link, 'previous_return_sha256': self.return_link, 'prior_known': self.prior_known,
                'phase': self.phase, 'entry': list(self.entry), 'phase_prior_at_entry': list(self.phase_prior_at_entry),
                'origin': [self.entry[i]-self.phase_prior_at_entry[i] for i in range(2)],
                'benchmark_fits': self.fits, 'first_memory': self.first, 'current_memory': self.memory,
                'max_SAMPLED_current_bytes': self.max_current, 'worker': self.latest, 'initial_cpu': INITIAL_CPU,
                'dispatch_cap': self.dispatch_cap, 'max_memory_sample_gap': self.max_gap,
                'clock_start': [FIRST_WALL, INITIAL_CPU], 'clock_end': [FIRST_WALL+self.last[0], self.last[1]],
                'allowance': 'NEW D001120 requested; historical B001 UNKNOWN separately, not historical total120', 'unknown': UNKNOWN}

def validate(v, earlier=None):
    require(v['status'] == 'SUCCESS_OBSERVED' and v['targets'] == CAPS and v['unknown'] == UNKNOWN, 'ledger status/design')
    phases, total = v['phase_totals'], v['observed_totals']
    def pair(x, cap):
        return isinstance(x, (list, tuple)) and len(x) == 2 and all(type(n) in (int, float) and math.isfinite(n) and 0 <= n < cap for n in x)
    require(set(phases) == set(CAPS) and pair(total, 120) and all(pair(phases[p], CAPS[p]) for p in CAPS), 'ledger coordinates')
    require(all(abs(total[i]-sum(phases[p][i] for p in CAPS)) <= TOL for i in range(2)), 'phase/global sum')
    require(type(v['phase']) is str and v['phase'] in CAPS and all(pair(v[k], 120) for k in ('entry', 'phase_prior_at_entry', 'origin')), 'fixed origin fields')
    require(all(v['origin'][i] == v['entry'][i]-v['phase_prior_at_entry'][i] and v['entry'][i] <= total[i]
                and v['phase_prior_at_entry'][i] <= phases[v['phase']][i] for i in range(2)), 'fixed origin consistency')
    worker = [v['worker']['worker_wall'], v['worker']['worker_cpu']]
    start, end = v['clock_start'], v['clock_end']
    require(type(v['dispatch_cap']) is int and v['dispatch_cap'] in DISPATCH.values() and pair(worker, v['dispatch_cap'])
            and pair(start, math.inf) and pair(end, math.inf) and all(end[i] >= start[i] for i in range(2)), 'worker/clock domains')
    require(abs(end[0]-start[0]-worker[0]) <= TOL and abs(end[1]-worker[1]) <= TOL
            and all(total[i]+TOL >= worker[i] for i in range(2)), 'clock identity / absolute CPU once')
    require(type(v['benchmark_fits']) is int and 0 <= v['benchmark_fits'] <= 4, 'fit ledger domain')
    if earlier is not None:
        require(all(v[k] == earlier[k] for k in ('targets', 'unknown', 'phase', 'entry', 'phase_prior_at_entry', 'origin', 'benchmark_fits', 'previous_receipt_sha256', 'previous_return_sha256', 'clock_start', 'dispatch_cap')), 'immutable handoff metadata')
        require(all(total[i] >= earlier['observed_totals'][i] and all(phases[p][i] >= earlier['phase_totals'][p][i] for p in CAPS) for i in range(2)), 'known observations regressed')
        old_worker = [earlier['worker']['worker_wall'], earlier['worker']['worker_cpu']]
        require(all(worker[i] >= old_worker[i] and end[i] >= earlier['clock_end'][i]
                    and abs((total[i]-earlier['observed_totals'][i])-(worker[i]-old_worker[i])) <= TOL for i in range(2)), 'global delta != worker delta')
        require(all(abs((phases[p][i]-earlier['phase_totals'][p][i])-(worker[i]-old_worker[i] if p == v['phase'] else 0)) <= TOL
                    for p in CAPS for i in range(2)), 'only active phase may increase')

def capture(rel, helper=None, budget=None, work=True):
    if budget is not None:
        budget.check(work)
    path = PROJECT/rel
    require(PROJECT in path.parents and '..' not in path.parts, 'outside project')
    if helper is not None:
        data = helper.read_data(path, helper.checked(path))
        if budget is not None:
            budget.check(work)
        return data
    require(not PROJECT.is_symlink() and PROJECT.is_dir(), 'unsafe project')
    for p in [*reversed([p for p in path.parents if PROJECT in p.parents]), path]:
        require(not stat.S_ISLNK(p.lstat().st_mode), 'input symlink')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        before = os.fstat(f.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= PER_FILE, 'input type/size')
        data = f.read(PER_FILE+1)
        after = os.fstat(f.fileno())
    require(len(data) <= PER_FILE and (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'input changed')
    if budget is not None:
        budget.check(work)
    return data
def load(rel, source, expected, name):
    require(digest(source) == expected and name not in sys.modules, 'captured source hash/cache')
    module = ModuleType(name)
    module.__file__, module.__package__ = str(PROJECT/rel), ''
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec', dont_inherit=True), module.__dict__)
    require(sys.modules[name] is module and module.__file__ == str(PROJECT/rel), 'source binding changed')
    return module  # __name__ is never __main__; old mains stay STOP/unexecuted
def census(h, b):
    scanned = [0]
    @contextmanager
    def scan(path):
        with os.scandir(path) as entries:
            def bounded():
                for entry in entries:
                    b.check()
                    scanned[0] += 1
                    require(scanned[0] <= 256, 'combined helper+extra enumeration bound')
                    yield entry
            yield bounded()
    class CensusOS:
        def __getattr__(self, name):
            return getattr(os, name)
        def scandir(self, path):
            return scan(path)
    original_os, h.os = h.os, CensusOS()  # bound CONTROL module only, never global os/source mutation
    try:
        records, stats, _ = h.census(b)
    finally:
        h.os = original_os
    seen = {(s.st_dev, s.st_ino) for s in stats.values()}
    def add(path, recursive=False):
        b.check()
        s = h.checked(path, missing=True)
        if s is None:
            return
        rel = str(path.relative_to(PROJECT))
        if rel in records:
            return
        directory, identity = stat.S_ISDIR(s.st_mode), (s.st_dev, s.st_ino)
        require(len(records) < 256 and (directory or stat.S_ISREG(s.st_mode) and s.st_size <= PER_FILE), 'extra census type/entry/file bound')
        duplicate = identity in seen
        seen.add(identity)
        records[rel] = {'kind': 'dir' if directory else 'file', 'nlink': s.st_nlink, 'logical': 0 if directory or duplicate else s.st_size,
                        'allocated': 0 if duplicate else s.st_blocks*512, 'hardlink_counted_elsewhere': duplicate}
        stats[rel] = s
        if recursive and directory:
            with scan(path) as children:
                for child in sorted(children, key=lambda e: e.name):
                    add(path/child.name, True)
    add(PROJECT/B001_REVIEW)
    require(B001_REVIEW in records, 'required B001 outcome review missing')
    add(PROJECT/REPORT, True)  # metadata ONLY, including future derived partials; E005 no truth reads
    totals = {k: sum(r[k] for r in records.values()) for k in ('logical', 'allocated')}
    totals['metadata_estimate'] = 512*len(records)
    return records, stats, totals

class Control:
    def __init__(self, h, budget, stage):
        self.h, self.b, self.stage, self.root = h, budget, stage, PROJECT/ROOTS[stage]
        self.owned, self.outputs, self.attempted, self.normal = False, {}, set(), 0
    def space(self, payload=0):
        records, stats, totals = census(self.h, self.b)
        report = [p for p in records if p == REPORT or p.startswith(REPORT+'/')]
        materialized = sum(stats[p].st_size for p in report if records[p]['kind'] == 'file')
        require(materialized <= REPORT_BYTES and len(report) <= REPORT_ENTRIES, 'report payload/entry reservation')
        future = 3*2048 + REPORT_BYTES-materialized  # actual report bytes already in census, no permanent double charge
        for stage, rel in ROOTS.items():
            normal = sum(r['logical'] for p, r in records.items() if p.startswith(rel+'/') and not p.endswith('/failure.json'))
            require(normal <= NORMAL, 'outer return record exceeds shared64KiB')
            future += max(0, NORMAL-normal) + (0 if rel+'/failure.json' in records else FAILURE)
        for stage in ('E004', 'E005'):
            for name, reserve in (('manifest.json', 32768), ('failure-001.json', 8192)):
                if '.research/experiments/raw/'+stage+'/'+name not in records:
                    future += reserve
        entries = 68 + REPORT_ENTRIES-len(report)  # single existing future-entry estimate + remaining report slots
        logical = totals['logical']+future+payload+totals['metadata_estimate']+entries*512
        allocated = totals['allocated']+future+payload+totals['metadata_estimate']+entries*(4096+512)
        require(len(records)+entries <= 256 and logical <= DISK and allocated <= DISK, '5MiB census + remaining reservations')
        return {'totals': totals, 'entry_count': len(records), 'remaining_reserved': future,
                'report_reserve_remaining': REPORT_BYTES-materialized, 'report_future_entries': REPORT_ENTRIES-len(report),
                'logical_estimate': logical, 'allocated_estimate': allocated, 'residual': int(min(DISK-logical, DISK-allocated))}
    def create(self):
        self.b.check()
        self.space()
        for rel in ('.research/experiments/control', BASE.rstrip('/'), ROOTS[self.stage]):
            path = PROJECT/rel
            existing = self.h.checked(path, missing=True)
            if existing is not None:
                require(path != self.root and stat.S_ISDIR(existing.st_mode), 'occupied control stage; no retry')
                continue
            self.h.checked(path.parent)
            path.mkdir(mode=0o700)
            if path == self.root:
                self.owned = True
            self.h.sync_dir(path.parent)
            self.h.sync_dir(path)
    def put(self, name, value):
        data = encoded(value)
        require(self.owned and name in ('freeze.json', 'ledger.json', 'outcome.json', 'failure.json') and name not in self.attempted, 'control ownership/name')
        require(len(data) <= (FAILURE if name == 'failure.json' else NORMAL-8192-self.normal), 'control bound; outer return8KiB inside64KiB')
        self.b.check()
        self.space(len(data))
        self.attempted.add(name)
        if name != 'failure.json':
            self.normal += len(data)
        with (self.root/name).open('xb') as f:
            require(f.write(data) == len(data), 'short control write')
            f.flush()
            os.fsync(f.fileno())
        self.h.sync_dir(self.root)
        self.outputs[name] = {'sha256': digest(data), 'bytes': len(data)}
        self.b.check()
        self.space()
def previous(h, stage, freeze_hash, budget):
    prior = 'bootstrap' if stage == 'E004' else 'E004'
    outcome_bytes = capture(ROOTS[prior]+'/outcome.json', h, budget)
    outcome = json.loads(outcome_bytes)
    require(h.checked(PROJECT/ROOTS[prior]/'failure.json', missing=True) is None and outcome['status'] == 'SUCCESS_OBSERVED'
            and outcome['stage'] == prior and outcome['freeze_sha256'] == freeze_hash, 'failed/mismatched prior outcome')
    ledger_bytes = capture(ROOTS[prior]+'/ledger.json', h, budget)
    require(digest(ledger_bytes) == outcome['ledger_sha256'], 'prior ledger link')
    ledger = json.loads(ledger_bytes)
    validate(ledger)
    latest = outcome['worker_observation']
    validate(latest, ledger)  # later observed outcome costs are NOT unknown/zero
    require(outcome['previous_receipt_sha256'] == ledger['previous_receipt_sha256'], 'outcome previous link')
    returned_bytes = capture(ROOTS[prior]+'/return-record.json', h, budget)
    require(len(returned_bytes) <= 8192, 'outer return bound')
    returned = json.loads(returned_bytes)
    summary = returned['stdout']  # exact parsed ONE stdout, written by orchestrator AFTER tool return
    require(returned['version'] == '0.3' and returned['stage'] == prior and returned['outcome_sha256'] == digest(outcome_bytes)
            and returned['tool_return_observed'] is True and returned['tool_timeout_or_error'] is False
            and (returned['actual_tool_OS_exit'] is None or type(returned['actual_tool_OS_exit']) is int and returned['actual_tool_OS_exit'] == 0), 'tool return/exit gate')
    require(type(summary['local_return_intended']) is int and summary['local_return_intended'] == 0 and summary['stage'] == prior
            and summary['outcome_sha256'] == digest(outcome_bytes) and summary['outcome_path'] == ROOTS[prior]+'/outcome.json'
            and summary['primary'] is None and summary['secondary'] is None, 'stdout success/link gate')
    handoff = summary['handoff_ledger']
    require(set(handoff) == {'status', 'observed_totals', 'phase_totals', 'phase', 'worker', 'clock_start', 'clock_end'}, 'compact handoff fields')
    require(handoff['status'] == 'SUCCESS_OBSERVED' and handoff['phase'] == latest['phase'], 'latest phase/status')
    require(isinstance(handoff['worker'], list) and len(handoff['worker']) == 2
            and all(type(v) in (int, float) and math.isfinite(v) and 0 <= v < DISPATCH[prior] for v in handoff['worker'])
            and all(handoff['worker'][i] >= outcome['worker_observation']['worker'][('worker_wall', 'worker_cpu')[i]] for i in range(2)), 'latest worker counters')
    latest = dict(latest, observed_totals=handoff['observed_totals'], phase_totals=handoff['phase_totals'],
                  worker=dict(latest['worker'], worker_wall=handoff['worker'][0], worker_cpu=handoff['worker'][1]),
                  clock_start=handoff['clock_start'], clock_end=handoff['clock_end'])
    validate(latest, outcome['worker_observation'])  # worker/totals/clocks updated TOGETHER before comparison
    if stage == 'E004':
        require(ledger['previous_receipt_sha256'] is None and ledger['previous_return_sha256'] is None and ledger['benchmark_fits'] == 0, 'bootstrap genesis')
    else:
        boot = capture(ROOTS['bootstrap']+'/outcome.json', h, budget)
        require(ledger['previous_receipt_sha256'] == digest(boot) and ledger['previous_return_sha256'] == digest(capture(ROOTS['bootstrap']+'/return-record.json', h, budget))
                and ledger['benchmark_fits'] == 0, 'E004 successor consistency')
        manifest_bytes = capture('.research/experiments/raw/E004/manifest.json', h, budget)
        manifest = json.loads(manifest_bytes)
        checks = manifest['checks']
        require(digest(manifest_bytes) == outcome['manifest_sha256']
                and manifest['status'] == 'LOCAL_WORKER_COMPLETE' and len(checks['checklist']) == 11
                and checks['toy_fits'] == 8 and checks['benchmark_fits'] == 0 and checks['invariants'] == 'LOCAL_CHECKS_PASSED', 'E004 11/8/0 gate')
    return latest, digest(outcome_bytes), digest(returned_bytes), outcome.get('manifest_sha256')

def bootstrap(c, ref, helper_hash):
    c.b.prior_known = True
    require(c.h.checked(PROJECT/BASE.rstrip('/'), missing=True) is None, 'occupied D001 namespace')
    hashes, config = {}, None
    for rel in SCOPED+EXTRA+(CALLER, HELPER, AMENDMENT):
        c.b.check(True)
        source = capture(rel, c.h, c.b)  # DATA; NO P/M/O/T/adapter execution in bootstrap
        hashes[rel] = digest(source)
        if rel == SCOPED[0]:
            config = source.decode('utf-8')
    require(hashes[HELPER] == helper_hash, 'helper changed during bootstrap')
    c.create()
    c.b.check(True)
    c.put('freeze.json', {'version': '0.3', 'hashes': hashes, 'runtime': sys.version, 'config_bytes_utf8': config,
          'stage_SCOPED': {'E004': list(SCOPED+EXTRA), 'E005': list(SCOPED)}, 'amendment': AMENDMENT,
          'approval_reference': ref, 'approval_is_permission': False, 'dependency_lock': [],
          'environment_spec': 'Linux /usr/bin/python3 -B -S; trusted system stdlib; single worker/thread; no children',
          'OS': list(os.uname()), 'CPU_hardware': None, 'RAM_hardware': None, 'compiler': 'embedded in sys.version',
          'repo_revision': None, 'dirty_state': None, 'unknown': UNKNOWN, 'disk': c.space()})
    return c.outputs['freeze.json']['sha256'], None
def run_stage(c, ref, freeze, frozen_hash):
    ledger, previous_hash, return_hash, manifest_hash = previous(c.h, c.stage, frozen_hash, c.b)
    c.b.adopt(ledger, previous_hash, return_hash)
    c.create()
    source = capture(ADAPTER, c.h, c.b)
    adapter = load(ADAPTER, source, freeze['hashes'][ADAPTER], 'synthetic_deadline_bound_adapter_v03')
    limits = {'per_file': PER_FILE, 'total': c.space()['residual']+40960, 'manifest_reserve': 32768, 'failure_reserve': 8192}
    require(40960 < limits['total'] <= DISK, 'no residual worker output allowance')
    original_writer, original_session = adapter.Writer, adapter.Session
    class GuardedWriter(original_writer):
        def create(self):
            c.b.check(True)
            c.space(4096)
            c.h.checked(self.root.parent)
            require(c.h.checked(self.root, missing=True) is None, 'occupied raw ID')
            return super().create()
        def put(self, name, data, slot=None):
            work = slot is None and not name.startswith('resource-')
            c.space(len(data)+4096)
            c.b.check(work)
            result = super().put(name, data, slot)
            c.space()
            c.b.check(work)  # SAME predicate; endpoint writes may consume their existing finish reserve
            return result
    class SafeSession(original_session):
        def __init__(self, context, stage):
            context['active_session'] = self
            super().__init__(context, stage)
        def read(self, path, expected=None):
            c.b.check(True)
            data = capture(str(path.relative_to(PROJECT)), c.h)
            require(expected is None or digest(data) == expected, 'safe adapter input checksum')
            c.b.check(True)
            return data
    adapter.Writer, adapter.Session = GuardedWriter, SafeSession
    def checkpoint(stage, point):
        c.space()
        totals = c.b.check(force=True)  # ONE final observation AFTER census, fit deadline still active
        receipt = {'operation_ref': ref, 'point': point, 'observed_totals': list(totals), 'phase': c.b.phase,
                   'phase_totals': {p: list(v) for p, v in c.b.phases.items()}, 'worker': dict(c.b.latest), 'memory': dict(c.b.memory),
                   'amendment': AMENDMENT, 'mode': 'NOT_ENFORCED_PRACTICAL', 'unknown': dict(UNKNOWN)}
        if point.startswith('fit_'):
            c.b.fit = None
            c.b.arm()  # later samples count future time; saved receipt arrays/maps are detached
        return receipt
    def persist(writer, stage, point, receipt):
        return writer.put('resource-%02d.json' % (len(writer.attempted)+1), encoded(receipt))
    command = ['/usr/bin/python3', '-B', '-S', str(PROJECT/CALLER), '--stage', c.stage, '--approval-ref', ref]
    context = {'project': str(PROJECT), 'checkpoint': checkpoint, 'persist_resource_receipt': persist,
               'sample': lambda: c.b.check(True), 'origin': c.b.origin, 'writer_limits': limits,
               'frozen_hashes': {p: freeze['hashes'][p] for p in (SCOPED+EXTRA if c.stage == 'E004' else SCOPED)},
               'adapter_loading': {'path': str(PROJECT/ADAPTER), 'sha256': freeze['hashes'][ADAPTER], 'mode': 'captured-source-no-cache'},
               'dispatch': {'operation_ref': ref, 'owner': 'same-worker-control', 'approval_reference': ref,
                            'prestart_record': ROOTS[c.stage]+'/outcome.json#NOT_ENFORCED_PRACTICAL',
                            'quota_record': 'NOT_ENFORCED_PRACTICAL; dynamic census estimates',
                            'postexit_record_locator': ROOTS[c.stage]+'/return-record.json#P43_P54_NULLABLE_EXIT_PENDING_D001'},
               'resource_receipt': {'mode': 'NOT_ENFORCED_PRACTICAL', 'amendment': AMENDMENT, 'prior_receipt_sha256': previous_hash, 'unknown': UNKNOWN},
               'provenance': {'runtime': sys.version, 'OS': list(os.uname()), 'CPU': None, 'RAM': None,
                              'compiler': 'embedded in sys.version', 'repo_revision': None, 'dirty_state': None,
                              'secret_free_environment': {'environment_dump': 'NOT_READ', 'dependency_lock': [], 'caller_sha256': freeze['hashes'][CALLER]}, 'commands': [command]},
               'e004_manifest_sha256': manifest_hash}
    c.context = context
    result = adapter.prepare_e004(context) if c.stage == 'E004' else adapter.compare_e005(context)
    c.b.check()
    actual = capture('.research/experiments/raw/'+c.stage+'/manifest.json', c.h, c.b, work=False)  # terminal verify, NOT scientific work
    require(digest(actual) == result['manifest_sha256'], 'finished manifest hash')
    c.b.check()
    return frozen_hash, digest(actual)  # captured AFTER adapter returns, never edit raw
def emit(b, c, code, primary, secondary):
    try:
        b.sample(True, memory=not b.reporting)
        if code == 0:
            b.check()
    except BaseException as error:
        code, secondary = 2, {'type': type(error).__name__, 'reason': 'terminal sample/guard failed'}
    try:
        signal.setitimer(signal.ITIMER_REAL, 0)  # only terminal formatting/write/exit remains
        b.sample(memory=False)  # LAST clocks: includes cancellation and all earlier known costs
        if code == 0:
            require(all(v < 120 for v in (b.old[i]+b.last[i] for i in range(2)))
                    and all(v < CAPS[b.phase] for v in b.phases[b.phase]) and all(v < b.dispatch_cap for v in b.last), 'last clock target')
    except BaseException as error:
        code, secondary = 2, {'type': type(error).__name__, 'reason': 'last clock/cancel failed'}
    def mem(v):
        return None if v is None else [v.get('monotonic'), v.get('current_VmRSS_bytes'), v.get('kernel_peak_bytes')]
    def short(v):
        return None if v is None else {'type': v['type'][:24], 'preview': (v.get('reason') or 'UNKNOWN')[:48], 'details_omitted': True}
    telemetry = {'memory': {'first': mem(b.first), 'last': mem(b.memory), 'max_current': b.max_current, 'max_gap': b.max_gap},
                 'worker': list(b.last), 'observed_totals': [b.old[i]+b.last[i] for i in range(2)] if b.prior_known else None}
    pointer = ROOTS[c.stage]+'/failure.json' if c and 'failure.json' in c.outputs else None
    try:
        handoff = {'status': 'SUCCESS_OBSERVED' if code == 0 else 'FAILED', 'observed_totals': telemetry['observed_totals'],
                   'phase_totals': {p: list(v) for p, v in b.phases.items()}, 'phase': b.phase, 'worker': list(b.last),
                   'clock_start': [FIRST_WALL, INITIAL_CPU], 'clock_end': [FIRST_WALL+b.last[0], b.last[1]]}
        summary = dict(telemetry, local_return_intended=code, stage=c.stage if c else None, primary=short(primary), secondary=short(secondary),
                       outcome_path=ROOTS[c.stage]+'/outcome.json' if c and 'outcome.json' in c.outputs else None,
                       outcome_sha256=c.outputs['outcome.json']['sha256'] if c and 'outcome.json' in c.outputs else None,
                       handoff_ledger=handoff, failure_pointer=pointer, unknown='B001/startup-before-marker/post-LAST-clock/stdout/exit/tool; OS exit UNKNOWN')
        output = encoded(summary)
        require(len(output) <= 2048, 'success handoff/stdout cap')
    except BaseException:
        code = 2  # fallback CANNOT authorise a successor; numeric telemetry retained
        kind = lambda v: None if v is None else v['type'].encode('ascii', 'replace').decode()[:16]
        output = encoded(dict(telemetry, local_return_intended=2, primary_type=kind(primary), secondary_type=kind(secondary),
                              failure_pointer=pointer, handoff_ledger=None, details_omitted=True))
    try:
        return code if len(output) <= 2048 and os.write(1, output) == len(output) else 2
    except BaseException:
        return 2  # exactly ONE write attempt; no stderr/second write/retry

def main():
    b, c, primary, secondary, code = Budget.__new__(Budget), None, None, None, 2
    try:
        Budget.__init__(b)
        require(len(sys.argv) == 5 and sys.argv[1] == '--stage' and sys.argv[3] == '--approval-ref', 'exact CLI flags')
        stage, ref = sys.argv[2], sys.argv[4]
        require(stage in REFS and ref == REFS[stage], 'D001 stage reference required; placeholders rejected; NOT permission')
        require(sys.executable == '/usr/bin/python3' and sys.flags.no_site and sys.flags.dont_write_bytecode
                and Path(__file__) == PROJECT/CALLER and os.uname().sysname == 'Linux', 'exact Linux runtime/path -B -S')
        b.dispatch_cap = DISPATCH[stage]
        b.check(True)
        b.arm()
        helper_source = capture(HELPER, budget=b)
        helper_hash = digest(helper_source)
        freeze, frozen_hash = None, None
        if stage != 'bootstrap':  # BEFORE helper exec: no O/T/traces/truth reads
            frozen_bytes = capture(ROOTS['bootstrap']+'/freeze.json', budget=b)
            freeze, frozen_hash = json.loads(frozen_bytes), digest(frozen_bytes)
            require(freeze['version'] == '0.3' and freeze['runtime'] == sys.version and freeze['amendment'] == AMENDMENT
                    and freeze['stage_SCOPED'] == {'E004': list(SCOPED+EXTRA), 'E005': list(SCOPED)}, 'frozen runtime/scope')
            require(helper_hash == freeze['hashes'][HELPER], 'control helper drift BEFORE exec')
            for rel in (CALLER, AMENDMENT):
                require(digest(capture(rel, budget=b)) == freeze['hashes'][rel], 'caller/amendment drift BEFORE helper exec')
        h = load(HELPER, helper_source, helper_hash, 'synthetic_deadline_control_helpers_v03')
        c = Control(h, b, stage)
        freeze_hash, manifest_hash = bootstrap(c, ref, helper_hash) if stage == 'bootstrap' else run_stage(c, ref, freeze, frozen_hash)
        b.check()
        c.put('ledger.json', b.ledger('SUCCESS_OBSERVED'))
        c.put('outcome.json', {'status': 'SUCCESS_OBSERVED', 'stage': stage, 'approval_reference': ref,
              'freeze_sha256': freeze_hash, 'manifest_sha256': manifest_hash, 'ledger_sha256': c.outputs['ledger.json']['sha256'],
              'previous_receipt_sha256': b.link, 'worker_observation': b.ledger('SUCCESS_OBSERVED'),
              'local_return_intended': 0, 'exit_code_observed': None, 'mode': 'NOT_ENFORCED_PRACTICAL',
              'commands': [['/usr/bin/python3', '-B', '-S', str(PROJECT/CALLER), '--stage', stage, '--approval-ref', ref]], 'unknown': UNKNOWN})
        code = 0
    except BaseException as error:
        primary = {'type': type(error).__name__, 'reason': None}
        try:
            primary['reason'] = str(error)
            b.reporting = True  # memory/schema concern: numeric reporting ONLY, full time caps remain
            b.arm()  # SAME absolute global/phase/dispatch/fit deadline; no new allowance
            if c is not None and c.owned:
                secondary_error = getattr(error, 'failure_reporting_error', None)
                c.put('failure.json', {'status': 'FAILED', 'primary': primary,
                      'adapter_secondary': str(secondary_error) if secondary_error is not None else None,
                      'ledger': b.ledger('FAILED'), 'outputs': c.outputs, 'unknown': UNKNOWN})
        except BaseException as reporting:
            secondary = {'type': type(reporting).__name__, 'reason': 'bounded reporting failed; full pointer UNKNOWN'}
    return emit(b, c, code, primary, secondary)

if __name__ == '__main__':
    raise SystemExit(main())
