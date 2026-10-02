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

PROJECT = Path('/home/nomli/workspace/bdss_lab/research1')
S = '.research/experiments/scripts/'
CALLER = S + 'synthetic_deadline_caller_v0.3.py'
HELPER = S + 'synthetic_practical_caller_v0.1.py'
ADAPTER = S + 'synthetic_stage_adapter_v0.1.py'
AMENDMENT = '.research/protocol/synthetic-deadline-runtime-amendment-v0.3.md'
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
DISK, PER_FILE, NORMAL, FAILURE = 5242880, 2097152, 65536, 8192
UNKNOWN = {'B001_costs': None, 'startup_wall_before_marker': None, 'own_preexit_control_tail': None,
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
        self.first, self.memory, self.latest, self.max_current = None, None, None, 0
        self.phases, self.old = {p: [0., 0.] for p in CAPS}, [0., 0.]
        self.last, self.phase, self.fit, self.fits = [0., 0.], 'inventory', None, 0
        self.entry, self.reporting, self.link, self.prior_known = [0., 0.], False, None, False
        self.sample(True)  # BEFORE any guard, ownership, argv/path/census check
        signal.signal(signal.SIGALRM, self.alarm)

    def alarm(self, signum, frame):
        self.sample(True)
        raise RuntimeError('soft wall alarm; scheduling/I/O/exit latency unbounded')

    def sample(self, force=False):
        now, cpu = time.monotonic(), time.process_time()
        current = [now-FIRST_WALL, cpu]
        for i in range(2):
            require(current[i] >= self.last[i], 'worker clock regressed')
            self.phases[self.phase][i] += current[i]-self.last[i]
        self.last = current
        self.latest = {'worker_wall': current[0], 'worker_cpu': cpu, 'wall_source': 'time.monotonic-first_marker',
                       'cpu_source': 'absolute time.process_time; initial charged once'}
        if force or self.memory is None or now-self.memory['monotonic'] >= .25:
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
            self.memory = {'monotonic': now, 'current_VmRSS_bytes': None, 'kernel_peak_bytes': peak,
                           'source': '/proc/self/status VmRSS kB interpreted KiB; Linux SELF ru_maxrss KiB'}
            if self.first is None:
                self.first = dict(self.memory)
            with open('/proc/self/status', 'rb') as f:
                data = f.read(16385)
            require(len(data) <= 16384 and len(data.splitlines()) <= 128, 'own status byte/line cap')
            rows = [r.split() for r in data.splitlines() if r.startswith(b'VmRSS:')]
            require(len(rows) == 1 and len(rows[0]) == 3 and rows[0][1].isdigit() and rows[0][2] == b'kB', 'VmRSS parse/units STOP')
            self.memory['current_VmRSS_bytes'] = int(rows[0][1])*1024
            if self.first['current_VmRSS_bytes'] is None:
                self.first = dict(self.memory)
            self.max_current = max(self.max_current, self.memory['current_VmRSS_bytes'])
        return tuple(self.old[i]+current[i] for i in range(2))

    def check(self):
        total = self.sample()
        if not self.reporting:
            require(self.memory['current_VmRSS_bytes'] is not None and self.max_current < 1073741824, 'sampled current VmRSS target')
            require(all(v < 120 for v in total), 'NEW cumulative D001 allowance exhausted')
            require(all(v < CAPS[self.phase] for v in self.phases[self.phase]), 'cumulative phase target')
            require(self.fit is None or all(total[i]-self.fit[i] < 10 for i in range(2)), 'per-fit target')
        return total

    def arm(self):
        total = self.check()
        remaining = min(120-total[0], CAPS[self.phase]-self.phases[self.phase][0])
        if self.fit is not None:
            remaining = min(remaining, 10-(total[0]-self.fit[0]))
        require(remaining > 0, 'no alarm reserve')
        signal.setitimer(signal.ITIMER_REAL, remaining)

    def origin(self, phase, fit):
        self.check()  # prior phase charged to actual transition, including stage startup
        require(phase in CAPS, 'unregistered phase')
        if phase != self.phase:
            self.phase, self.entry, self.fit = phase, list(self.sample()), None
        origin = tuple(self.entry[i]-self.phases[phase][i] for i in range(2))
        if fit is not None:
            require(phase == 'E005_fits' and type(fit) is int and fit == self.fits+1 and fit <= 4, 'fresh sequential fit1..4 only')
            self.fit, self.fits = self.check(), fit
        self.arm()
        return origin if fit is None else self.fit

    def adopt(self, ledger, previous_hash):
        self.sample(True)  # keep all NEW startup/inventory; never reset local clocks
        require(ledger['status'] == 'SUCCESS_OBSERVED' and ledger['targets'] == CAPS and ledger['unknown'] == UNKNOWN, 'prior ledger status/design')
        phases, old = ledger['phase_totals'], ledger['observed_totals']
        require(set(phases) == set(CAPS) and len(old) == 2, 'ledger fields')
        for p in CAPS:
            require(len(phases[p]) == 2 and all(type(v) in (int, float) and math.isfinite(v) and 0 <= v < CAPS[p] for v in phases[p]), 'prior phase values')
        require(all(type(old[i]) in (int, float) and math.isfinite(old[i]) and 0 <= old[i] < 120
                    and abs(old[i]-sum(phases[p][i] for p in CAPS)) < 1e-8 for i in range(2)), 'phase/global consistency')
        for p in CAPS:
            self.phases[p] = [self.phases[p][i]+phases[p][i] for i in range(2)]
        self.old, self.link, self.prior_known = list(old), previous_hash, True
        self.entry = list(old)  # inventory origin subtracts prior inventory, NOT old stage elapsed=0
        self.check()
        self.arm()

    def ledger(self, status):
        total = self.sample(True)
        return {'status': status, 'observed_totals': list(total), 'phase_totals': {p: list(v) for p, v in self.phases.items()},
                'targets': CAPS, 'previous_receipt_sha256': self.link, 'prior_known': self.prior_known,
                'phase': self.phase, 'entry': self.entry, 'origin': [self.entry[i]-self.phases[self.phase][i] for i in range(2)],
                'benchmark_fits': self.fits, 'first_memory': self.first, 'current_memory': self.memory,
                'max_SAMPLED_current_bytes': self.max_current, 'worker': self.latest, 'initial_cpu': INITIAL_CPU,
                'allowance': 'NEW D001120 requested; historical B001 UNKNOWN separately, not historical total120', 'unknown': UNKNOWN}


def capture(rel, helper=None):
    path = PROJECT/rel
    require(PROJECT in path.parents and '..' not in path.parts, 'outside project')
    if helper is not None:
        return helper.read_data(path, helper.checked(path))
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
    return data


def load(rel, source, expected, name):
    require(digest(source) == expected and name not in sys.modules, 'captured source hash/cache')
    module = ModuleType(name)
    module.__file__, module.__package__ = str(PROJECT/rel), ''
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec', dont_inherit=True), module.__dict__)
    require(sys.modules[name] is module and module.__file__ == str(PROJECT/rel), 'source binding changed')
    return module  # __name__ is never __main__; old mains stay STOP/unexecuted


class Control:
    def __init__(self, h, budget, stage):
        self.h, self.b, self.stage, self.root = h, budget, stage, PROJECT/ROOTS[stage]
        self.owned, self.outputs, self.attempted, self.normal = False, {}, set(), 0

    def space(self, payload=0):
        records, _, totals = self.h.census(self.b)  # metadata ONLY: no oracle/truth content
        future = 3*2048
        for stage, rel in ROOTS.items():
            normal = sum(r['logical'] for p, r in records.items() if p.startswith(rel+'/') and not p.endswith('/failure.json'))
            future += max(0, NORMAL-normal) + (0 if rel+'/failure.json' in records else FAILURE)
        for stage in ('E004', 'E005'):
            for name, reserve in (('manifest.json', 32768), ('failure-001.json', 8192)):
                if '.research/experiments/raw/'+stage+'/'+name not in records:
                    future += reserve
        entries = 60  # conservative future raw/control/capture entry estimate, NOT certified
        logical = totals['logical']+future+payload+totals['metadata_estimate']+entries*512
        allocated = totals['allocated']+future+payload+totals['metadata_estimate']+entries*(4096+512)
        require(len(records)+entries <= 256 and logical <= DISK and allocated <= DISK, '5MiB census + remaining reservations')
        return {'totals': totals, 'entry_count': len(records), 'remaining_reserved': future,
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
        require(len(data) <= (FAILURE if name == 'failure.json' else NORMAL-self.normal), 'control payload bound')
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


def previous(h, stage, freeze_hash):
    prior = 'bootstrap' if stage == 'E004' else 'E004'
    outcome_bytes = capture(ROOTS[prior]+'/outcome.json', h)
    outcome = json.loads(outcome_bytes)
    require(h.checked(PROJECT/ROOTS[prior]/'failure.json', missing=True) is None and outcome['status'] == 'SUCCESS_OBSERVED'
            and outcome['stage'] == prior and outcome['freeze_sha256'] == freeze_hash, 'failed/mismatched prior outcome')
    ledger_bytes = capture(ROOTS[prior]+'/ledger.json', h)
    require(digest(ledger_bytes) == outcome['ledger_sha256'], 'prior ledger link')
    ledger = json.loads(ledger_bytes)
    if stage == 'E004':
        require(ledger['previous_receipt_sha256'] is None and ledger['benchmark_fits'] == 0, 'bootstrap successor consistency')
    else:
        boot = capture(ROOTS['bootstrap']+'/outcome.json', h)
        require(ledger['previous_receipt_sha256'] == digest(boot) and ledger['benchmark_fits'] == 0, 'E004 successor consistency')
        manifest = json.loads(capture('.research/experiments/raw/E004/manifest.json', h))
        checks = manifest['checks']
        require(digest(encoded(manifest)) != '', 'manifest digest available')
        require(digest(capture('.research/experiments/raw/E004/manifest.json', h)) == outcome['manifest_sha256']
                and manifest['status'] == 'LOCAL_WORKER_COMPLETE' and len(checks['checklist']) == 11
                and checks['toy_fits'] == 8 and checks['benchmark_fits'] == 0 and checks['invariants'] == 'LOCAL_CHECKS_PASSED', 'E004 11/8/0 gate')
    return ledger, digest(outcome_bytes), outcome.get('manifest_sha256')


def bootstrap(c, ref, helper_hash):
    c.b.prior_known = True
    require(c.h.checked(PROJECT/BASE.rstrip('/'), missing=True) is None, 'occupied D001 namespace')
    hashes, config = {}, None
    for rel in SCOPED+EXTRA+(CALLER, HELPER, AMENDMENT):
        c.b.check()
        source = capture(rel, c.h)  # DATA; NO P/M/O/T/adapter execution in bootstrap
        hashes[rel] = digest(source)
        if rel == SCOPED[0]:
            config = source.decode('utf-8')
    require(hashes[HELPER] == helper_hash, 'helper changed during bootstrap')
    c.create()
    c.b.check()
    require(all(v < 12 for v in c.b.phases['inventory']), 'bootstrap work reserve3 exhausted')
    c.put('freeze.json', {'version': '0.3', 'hashes': hashes, 'runtime': sys.version, 'config_bytes_utf8': config,
          'stage_SCOPED': {'E004': list(SCOPED+EXTRA), 'E005': list(SCOPED)}, 'amendment': AMENDMENT,
          'approval_reference': ref, 'approval_is_permission': False, 'dependency_lock': [],
          'environment_spec': 'Linux /usr/bin/python3 -B -S; trusted system stdlib; single worker/thread; no children',
          'OS': list(os.uname()), 'CPU_hardware': None, 'RAM_hardware': None, 'compiler': 'embedded in sys.version',
          'repo_revision': None, 'dirty_state': None, 'unknown': UNKNOWN, 'disk': c.space()})
    return c.outputs['freeze.json']['sha256'], None


def run_stage(c, ref, helper_hash):
    frozen_bytes = capture(ROOTS['bootstrap']+'/freeze.json', c.h)
    freeze, frozen_hash = json.loads(frozen_bytes), digest(frozen_bytes)
    require(freeze['version'] == '0.3' and freeze['runtime'] == sys.version and freeze['amendment'] == AMENDMENT, 'frozen runtime/version mismatch')
    require(freeze['stage_SCOPED'] == {'E004': list(SCOPED+EXTRA), 'E005': list(SCOPED)}, 'scoped map drift')
    for rel in (CALLER, AMENDMENT):  # E005 never rehashes whole freeze or oracle/tests
        require(digest(capture(rel, c.h)) == freeze['hashes'][rel], 'caller/amendment drift')
    require(helper_hash == freeze['hashes'][HELPER], 'control helper drift')
    ledger, previous_hash, manifest_hash = previous(c.h, c.stage, frozen_hash)
    c.b.adopt(ledger, previous_hash)
    c.create()
    source = capture(ADAPTER, c.h)
    adapter = load(ADAPTER, source, freeze['hashes'][ADAPTER], 'synthetic_deadline_bound_adapter_v03')
    limits = {'per_file': PER_FILE, 'total': c.space()['residual']+40960, 'manifest_reserve': 32768, 'failure_reserve': 8192}
    require(40960 < limits['total'] <= DISK, 'no residual worker output allowance')
    # Runtime Writer/Session injection only, before dispatch; no source/raw mutation.
    original_writer, original_session = adapter.Writer, adapter.Session
    class GuardedWriter(original_writer):
        def create(self):
            c.b.check()
            c.space(4096)
            c.h.checked(self.root.parent)
            require(c.h.checked(self.root, missing=True) is None, 'occupied raw ID')
            return super().create()
        def put(self, name, data, slot=None):
            c.b.check()
            c.space(len(data)+4096)
            result = super().put(name, data, slot)
            c.b.check()
            c.space()
            return result
    class SafeSession(original_session):
        def __init__(self, context, stage):
            context['active_session'] = self
            super().__init__(context, stage)
        def read(self, path, expected=None):
            c.b.check()
            data = capture(str(path.relative_to(PROJECT)), c.h)
            require(expected is None or digest(data) == expected, 'safe adapter input checksum')
            return data
    adapter.Writer, adapter.Session = GuardedWriter, SafeSession
    def checkpoint(stage, point):
        c.b.sample(True)
        totals = c.b.check()
        c.space()
        if point.startswith('fit_'):
            c.b.fit = None
            c.b.arm()
        return {'operation_ref': ref, 'point': point, 'observed_totals': totals, 'phase': c.b.phase,
                'phase_totals': c.b.phases, 'memory': c.b.memory, 'amendment': AMENDMENT, 'mode': 'NOT_ENFORCED_PRACTICAL', 'unknown': UNKNOWN}
    def persist(writer, stage, point, receipt):
        return writer.put('resource-%02d.json' % (len(writer.attempted)+1), encoded(receipt))
    command = ['/usr/bin/python3', '-B', '-S', str(PROJECT/CALLER), '--stage', c.stage, '--approval-ref', ref]
    context = {'project': str(PROJECT), 'checkpoint': checkpoint, 'persist_resource_receipt': persist,
               'sample': c.b.check, 'origin': c.b.origin, 'writer_limits': limits,
               'frozen_hashes': {p: freeze['hashes'][p] for p in (SCOPED+EXTRA if c.stage == 'E004' else SCOPED)},
               'adapter_loading': {'path': str(PROJECT/ADAPTER), 'sha256': freeze['hashes'][ADAPTER], 'mode': 'captured-source-no-cache'},
               'dispatch': {'operation_ref': ref, 'owner': 'same-worker-control', 'approval_reference': ref,
                            'prestart_record': ROOTS[c.stage]+'/outcome.json#NOT_ENFORCED_PRACTICAL',
                            'quota_record': 'NOT_ENFORCED_PRACTICAL; dynamic census estimates',
                            'postexit_record_locator': ROOTS[c.stage]+'/outcome.json#PRE_EXIT_ONLY_TOOL_EXIT_UNKNOWN'},
               'resource_receipt': {'mode': 'NOT_ENFORCED_PRACTICAL', 'amendment': AMENDMENT, 'prior_receipt_sha256': previous_hash, 'unknown': UNKNOWN},
               'provenance': {'runtime': sys.version, 'OS': list(os.uname()), 'CPU': None, 'RAM': None,
                              'compiler': 'embedded in sys.version', 'repo_revision': None, 'dirty_state': None,
                              'secret_free_environment': {'environment_dump': 'NOT_READ', 'dependency_lock': [], 'caller_sha256': freeze['hashes'][CALLER]}, 'commands': [command]},
               'e004_manifest_sha256': manifest_hash}
    c.context = context
    result = adapter.prepare_e004(context) if c.stage == 'E004' else adapter.compare_e005(context)
    c.b.check()
    actual = capture('.research/experiments/raw/'+c.stage+'/manifest.json', c.h)
    require(digest(actual) == result['manifest_sha256'], 'finished manifest hash')
    return frozen_hash, digest(actual)  # captured AFTER adapter returns, never edit raw


def main():
    b, c, primary, secondary, code = Budget.__new__(Budget), None, None, None, 2
    try:
        Budget.__init__(b)
        require(len(sys.argv) == 5 and sys.argv[1] == '--stage' and sys.argv[3] == '--approval-ref', 'exact CLI flags')
        stage, ref = sys.argv[2], sys.argv[4]
        require(stage in REFS and ref == REFS[stage], 'D001 stage reference required; placeholders rejected; NOT permission')
        require(sys.executable == '/usr/bin/python3' and sys.flags.no_site and sys.flags.dont_write_bytecode
                and Path(__file__) == PROJECT/CALLER and os.uname().sysname == 'Linux', 'exact Linux runtime/path -B -S')
        b.check()
        b.arm()
        helper_source = capture(HELPER)
        helper_hash = digest(helper_source)
        h = load(HELPER, helper_source, helper_hash, 'synthetic_deadline_control_helpers_v03')
        c = Control(h, b, stage)
        freeze_hash, manifest_hash = bootstrap(c, ref, helper_hash) if stage == 'bootstrap' else run_stage(c, ref, helper_hash)
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
            b.reporting = True  # bounded reporting only; NEVER continue experiments or renew budget
            signal.setitimer(signal.ITIMER_REAL, 0)
            if c is not None and c.owned:
                secondary_error = getattr(error, 'failure_reporting_error', None)
                c.put('failure.json', {'status': 'FAILED', 'primary': primary,
                      'adapter_secondary': str(secondary_error) if secondary_error is not None else None,
                      'ledger': b.ledger('FAILED'), 'outputs': c.outputs, 'unknown': UNKNOWN})
        except BaseException as reporting:
            secondary = {'type': type(reporting).__name__, 'reason': 'bounded reporting failed; full pointer UNKNOWN'}
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
            b.sample(True)
        except BaseException:
            code = 2
    summary = {'local_return_intended': code, 'first_memory': b.first, 'current_memory': b.memory,
               'max_SAMPLED_current_bytes': b.max_current, 'worker': b.latest,
               'observed_totals': [b.old[i]+b.last[i] for i in range(2)] if b.prior_known else None,
               'previous_costs': 'B001 UNKNOWN; NEW D001 ledger only', 'primary': None if primary is None else
               {'type': primary['type'][:24], 'reason_preview': (primary['reason'] or 'UNKNOWN')[:64], 'full_reason': 'failure.json best effort'},
               'secondary': secondary, 'control': ROOTS[c.stage] if c and c.owned else None,
               'failure_pointer': str(c.root/'failure.json') if c and 'failure.json' in c.outputs else None,
               'tail': 'UNKNOWN pre-exit; missing/failed control ledger BLOCKS pipeline; intended code is not tool OS exit'}
    try:
        output = encoded(summary)
        require(len(output) <= 2048, 'stdout cap')
        return code if os.write(1, output) == len(output) else 2
    except BaseException:
        return 2  # no second stdout/stderr write, retry, traceback or continuation


if __name__ == '__main__':
    raise SystemExit(main())
