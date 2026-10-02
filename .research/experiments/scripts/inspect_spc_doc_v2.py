#!/usr/bin/env python3
"""Single S018 PDF-only attempt. Read entirety before execution; no retry mode.

v1 is preserved. v2 fixes preparation-only hard-limit inheritance; scientific
design and total approved budgets are unchanged. Stdlib and installed pdftotext
only; no PDF instructions/actions, trace links, credentials, installs or git.
"""
import time
START = time.monotonic()
import os
import resource
import signal
import sys

MIB = 1024 * 1024
EARLY_ERROR = None
INITIAL_LIMITS = {}
try:
    for key in ('RLIMIT_AS', 'RLIMIT_CPU', 'RLIMIT_FSIZE', 'RLIMIT_CORE'):
        INITIAL_LIMITS[key] = resource.getrlimit(getattr(resource, key))
    # A child inherits hard ceilings. Parent never raises its own soft ceiling.
    for key, soft, hard in [('RLIMIT_AS', 64 * MIB, 192 * MIB),
                            ('RLIMIT_CPU', 8, 20), ('RLIMIT_FSIZE', MIB, MIB),
                            ('RLIMIT_CORE', 0, 0)]:
        old_soft, old_hard = INITIAL_LIMITS[key]
        if old_hard != resource.RLIM_INFINITY and old_hard < hard:
            raise RuntimeError('inherited hard ceiling incompatible')
        if old_soft != resource.RLIM_INFINITY and old_soft < soft:
            raise RuntimeError('inherited soft ceiling incompatible')
        resource.setrlimit(getattr(resource, key), (soft, hard))
        if resource.getrlimit(getattr(resource, key)) != (soft, hard):
            raise RuntimeError('parent limit verification failed')
    signal.signal(signal.SIGXCPU, signal.SIG_DFL)
except Exception as error:
    EARLY_ERROR = type(error).__name__

import ctypes
import datetime
import errno
import hashlib
import json
from pathlib import Path
import selectors
import ssl
import subprocess
import urllib.request

ROOT = Path('/home/nomli/workspace/bdss_lab/research1')
OUT = ROOT / '.research/experiments/documentation/S018-2026-10-01-docaudit-v2-b83df0'
OLD = ROOT / '.research/experiments/documentation/S018-2026-10-01-docaudit-a91c7e'
SCRIPT = Path(__file__).resolve()
V1 = ROOT / '.research/experiments/scripts/inspect_spc_doc_v1.py'
PROTOCOL = ROOT / '.research/protocol/temperature-poc-checkpoint-2026-10-01.md'
EXTRACTOR = Path('/usr/bin/pdftotext')
URL = 'https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf'
CHILD_ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
             'HOME': '/nonexistent', 'XDG_CACHE_HOME': '/nonexistent',
             'TMPDIR': '/nonexistent', 'OMP_NUM_THREADS': '1'}
CHILD_COMMAND = [str(EXTRACTOR), '-layout', '-enc', 'UTF-8', '-eol', 'unix', '-', '-']
CONFIG = {
    'version': 'S018-document-audit-v2', 'kind': 'DOCUMENT_ONLY_NOT_EXPERIMENT',
    'url': URL, 'max_source_attempts': 1, 'retry': False, 'redirect': False,
    'proxy': False, 'ca_file': '/etc/ssl/certs/ca-certificates.crt',
    'socket_timeout_s': 10, 'operation_watchdog_s': 45, 'total_watchdog_s': 50,
    'shell_timeout_s': 55, 'prior_inventory_wall_ceiling_s': 5,
    'prior_inventory_cpu_ceiling_s': 2, 'remaining_cpu_budget_s': 28,
    'parent_as_soft_hard': [64 * MIB, 192 * MIB],
    'parent_cpu_soft_hard': [8, 20], 'child_as_soft_hard': [192 * MIB, 192 * MIB],
    'child_cpu_soft_hard': [20, 20], 'parent_child_fsize_soft_hard': [MIB, MIB],
    'child_nproc_soft_hard': [0, 0], 'core_soft_hard': [0, 0],
    'pdf_body_cap_bytes': MIB, 'text_cap_bytes': MIB, 'stderr_cap_bytes': 16384,
    'log_cap_bytes': 8192, 'manifest_cap_bytes': 32768,
    'all_old_new_document_and_script_cap_bytes': 5 * MIB,
    'child_command': CHILD_COMMAND, 'child_environment': CHILD_ENV,
    'seed': None, 'warmup': None, 'repetitions': None, 'independent_unit': None,
    'workload_split_model': None,
}
EVENTS = []
CHILD = None
PARENT_PID = os.getpid()
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.prctl.restype = ctypes.c_int


class StopAudit(Exception):
    pass


def require(condition, reason):
    if not condition:
        raise StopAudit(reason)


def event(message):
    require(len(EVENTS) < 24, 'log event cap')
    EVENTS.append({'elapsed_s': round(time.monotonic() - START, 6), 'message': message[:180]})


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + '\n').encode()


def write_once(path, data, cap):
    require(len(data) <= cap, 'metadata byte cap')
    with path.open('xb') as stream:
        stream.write(data)


def fingerprint(path, cap):
    result, total = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while True:
            block = stream.read(16384)
            if not block:
                break
            total += len(block)
            require(total <= cap, 'fingerprint input byte cap')
            result.update(block)
    return {'bytes': total, 'sha256': result.hexdigest()}


def rusage(who):
    value = resource.getrusage(who)
    return {'user_cpu_s': value.ru_utime, 'system_cpu_s': value.ru_stime,
            'maxrss_kib_linux': value.ru_maxrss, 'minor_faults': value.ru_minflt,
            'major_faults': value.ru_majflt, 'voluntary_context_switches': value.ru_nvcsw,
            'involuntary_context_switches': value.ru_nivcsw}


def limits():
    return {key: list(resource.getrlimit(getattr(resource, key)))
            for key in ('RLIMIT_AS', 'RLIMIT_CPU', 'RLIMIT_FSIZE', 'RLIMIT_CORE', 'RLIMIT_NPROC')}


class Filter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
               ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint32)]


class Program(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filter', ctypes.POINTER(Filter))]


def install_seccomp(child):
    # x86_64 LE only. BPF load arch@4, nr@0, open flags args[1]@24 /
    # openat flags args[2]@32. Wrong arch or x32 is killed. This is a
    # denylist, NOT a full sandbox: existing FD writes and filesystem reads
    # remain available. Child has only stdio/handshake/exec-error pipe FDs.
    code = [Filter(0x20, 0, 0, 4), Filter(0x15, 1, 0, 0xC000003E),
            Filter(0x06, 0, 0, 0x80000000), Filter(0x20, 0, 0, 0),
            Filter(0x35, 0, 1, 0x40000000), Filter(0x06, 0, 0, 0x80000000)]
    if child:
        denied = list(range(41, 56)) + [56, 57, 58, 101, 272, 288, 299, 307,
                  308, 321, 322, 425, 426, 427, 435, 437,
                  76, 77, 82, 83, 84, 85, 86, 87, 88, 133,
                  258, 259, 260, 263, 264, 265, 266, 316]
        for number in sorted(set(denied)):
            code += [Filter(0x15, 0, 1, number), Filter(0x06, 0, 0, 0x00050000 | errno.EPERM)]
        for number, offset in [(2, 24), (257, 32)]:
            # JEQ false skips four instructions to the next syscall rule.
            # JSET false skips deny-return, then reloads nr for next rule.
            code += [Filter(0x15, 0, 4, number), Filter(0x20, 0, 0, offset),
                     Filter(0x45, 0, 1, 3 | 64 | 512 | 1024 | 0x400000),
                     Filter(0x06, 0, 0, 0x00050000 | errno.EPERM), Filter(0x20, 0, 0, 0)]
    code += [Filter(0x06, 0, 0, 0x7FFF0000)]
    array = (Filter * len(code))(*code)
    program = Program(len(code), array)
    require(LIBC.prctl(38, 1, 0, 0, 0) == 0, 'no_new_privs unavailable')
    require(LIBC.prctl(22, 2, ctypes.byref(program), 0, 0) == 0, 'seccomp unavailable')
    require(LIBC.prctl(21, 0, 0, 0, 0) == 2, 'seccomp verification failed')
    require(LIBC.prctl(39, 0, 0, 0, 0) == 1, 'no_new_privs verification failed')


def child_setup(record_fd):
    # Bound even a default-SIGXCPU/outer-timeout parent death; survive no orphan.
    require(LIBC.prctl(1, signal.SIGKILL, 0, 0, 0) == 0, 'parent death signal unavailable')
    require(os.getppid() == PARENT_PID, 'parent died during child setup')
    inherited = limits()
    for key, value in [('RLIMIT_AS', 192 * MIB), ('RLIMIT_CPU', 20),
                       ('RLIMIT_FSIZE', MIB), ('RLIMIT_CORE', 0), ('RLIMIT_NPROC', 0)]:
        resource.setrlimit(getattr(resource, key), (value, value))
        require(resource.getrlimit(getattr(resource, key)) == (value, value), 'child limit verification failed')
    signal.signal(signal.SIGXCPU, signal.SIG_DFL)
    install_seccomp(True)
    data = encode({'inherited': inherited, 'actual_before_exec': limits(),
                   'seccomp_mode': 2, 'no_new_privs': 1, 'parent_death_signal': 'SIGKILL'})
    require(len(data) < 4096 and os.write(record_fd, data) == len(data), 'child handshake write failed')
    os.close(record_fd)


def wall_alarm(signum, frame):
    raise TimeoutError('internal wall watchdog')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise StopAudit('redirect forbidden')


def pump_pdf(text_file, stderr_file):
    counts = {'stdin': 0, 'stdout': 0, 'stderr': 0}
    pending = b''
    with (OUT / 'source.pdf').open('rb') as source, selectors.DefaultSelector() as selector:
        for pipe, key, mode in [(CHILD.stdin, 'stdin', selectors.EVENT_WRITE),
                                (CHILD.stdout, 'stdout', selectors.EVENT_READ),
                                (CHILD.stderr, 'stderr', selectors.EVENT_READ)]:
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, mode, key)
        while selector.get_map():
            for selected, mask in selector.select(timeout=0.25):
                key = selected.data
                if key == 'stdin':
                    if not pending:
                        pending = source.read(16384)
                    if not pending:
                        selector.unregister(selected.fileobj)
                        selected.fileobj.close()
                        continue
                    written = os.write(selected.fd, pending)
                    counts[key] += written
                    pending = pending[written:]
                else:
                    block = os.read(selected.fd, 16384)
                    if not block:
                        selector.unregister(selected.fileobj)
                        selected.fileobj.close()
                        continue
                    cap, stream = ((CONFIG['text_cap_bytes'], text_file) if key == 'stdout'
                                   else (CONFIG['stderr_cap_bytes'], stderr_file))
                    remaining = cap - counts[key]
                    stream.write(block[:remaining])
                    counts[key] += min(remaining, len(block))
                    require(len(block) <= remaining, 'extractor output byte cap')
    return counts


def main():
    global CHILD
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = {'source_id': 'S018', 'related_claim': 'C022', 'experiment_id': None,
                'document_audit_id': OUT.name, 'status': 'failed', 'exit_code': 1,
                'started_at': started, 'source_url': URL, 'network_attempts': 0,
                'download_complete': False, 'extraction_complete': False,
                'config': CONFIG, 'initial_parent_rlimits': INITIAL_LIMITS,
                'parent_as_soft_never_raised_after_configuration': True,
                'commands': [[sys.executable, '-I', '-S', '-B', str(SCRIPT)]],
                'code_commit': None, 'source_title_byline_date': None,
                'extractor_version': None, 'dependency_lock': None,
                'preparation_deviation': 'v1 unexecuted inheritance defect corrected in new v2; zero previous source attempts. Orchestrator permits correction under existing PDF-only approval. No scientific/numerical budget change or runtime retry.',
                'inspection_record': str(OUT / 'INSPECTION-RESULT.md'),
                'notes': [
                    'RLIMIT_AS is virtual address space, not RSS/cgroup enforcement.',
                    'Parent64MiB + child192MiB address-space soft caps sum256MiB; parent hard192MiB is inherited ceiling, never used to raise parent soft.',
                    'CPU limits use OS scheduling granularity; actual aggregate CPU incl prior shell children reported where available.',
                    'Seccomp denylist/minimal env/no descendants, not complete OS/filesystem-read sandbox; installed Poppler/libs trusted.',
                    'No credentials/proxies forwarded. Wire/TLS/header/DNS bytes are unmeasured; cap is HTTP application body.',
                    'Versioned stdlib config and exact binary hashes; no installed dependency source audit/full shared-library lock.',
                    'Outer hard timeout/SIGXCPU/OOM can prevent final metadata; preserve partial files.',
                    'No seed/warmup/model/split/experimental unit; documentary extraction only.',
                ]}
    phase = 'preflight'
    prior_bytes = 0
    try:
        signal.signal(signal.SIGALRM, wall_alarm)
        signal.setitimer(signal.ITIMER_REAL, max(0.1, 45 - (time.monotonic() - START)))
        require(EARLY_ERROR is None, 'inherited limits incompatible; no network')
        require(os.uname().sysname == 'Linux' and os.uname().machine == 'x86_64' and os.getuid() != 0,
                'unsupported enforcement platform or root uid')
        require(OUT.is_dir() and not OUT.is_symlink(), 'owned directory unavailable')
        require(sorted(p.name for p in OUT.iterdir()) == ['INSPECTION-RESULT.md', 'NOTES.md'],
                'directory already used or inspection absent')
        require(EXTRACTOR.is_file() and os.access(EXTRACTOR, os.X_OK), 'extractor unavailable')
        require(EXTRACTOR.stat().st_mode & 0o6000 == 0, 'privileged extractor binary forbidden')
        with EXTRACTOR.open('rb') as stream:
            header = stream.read(64)
        require(header[:6] == b'\x7fELF\x02\x01' and header[18:20] == b'\x3e\x00', 'extractor native ELF required')
        manifest['script'] = {'path': str(SCRIPT), **fingerprint(SCRIPT, 65536)}
        manifest['protocol'] = {'path': str(PROTOCOL), **fingerprint(PROTOCOL, 65536)}
        manifest['extractor'] = {'path': str(EXTRACTOR), **fingerprint(EXTRACTOR, 8 * MIB)}
        manifest['python_binary'] = {'path': sys.executable, **fingerprint(Path(sys.executable), 16 * MIB)}
        manifest['v1_preserved'] = {'script': fingerprint(V1, 65536), 'docs': {
            p.name: fingerprint(p, 65536) for p in OLD.iterdir() if p.is_file()}}
        prior_bytes = manifest['v1_preserved']['script']['bytes'] + sum(
            item['bytes'] for item in manifest['v1_preserved']['docs'].values())
        manifest['prior_preparation_bytes'] = prior_bytes
        manifest['environment'] = {'python': sys.version, 'openssl': ssl.OPENSSL_VERSION,
                                   'uname': list(os.uname()), 'logical_cpu_count': os.cpu_count(),
                                   'hardware_model': None, 'load_average_before': os.getloadavg(),
                                   'no_installs': True, 'no_git_commands': True}
        manifest['parent_actual_rlimits_before_network'] = limits()
        require(limits()['RLIMIT_AS'] == [64 * MIB, 192 * MIB]
                and limits()['RLIMIT_CPU'] == [8, 20]
                and limits()['RLIMIT_FSIZE'] == [MIB, MIB], 'parent limits changed')
        install_seccomp(False)
        write_once(OUT / 'config.json', encode(CONFIG), 8192)
        manifest['config_sha256'] = fingerprint(OUT / 'config.json', 8192)['sha256']
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=CONFIG['ca_file'])
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                             urllib.request.HTTPSHandler(context=context))
        # Start the sole real extractor BEFORE networking, waiting for stdin.
        # Popen's exec-error pipe and our handshake prove limits/filter setup
        # succeeded before any PDF request; there is no helper subprocess.
        with (OUT / 'extracted.txt').open('xb') as text_file, \
                (OUT / 'extractor.stderr.log').open('xb') as stderr_file:
            record_read, record_write = os.pipe()
            try:
                CHILD = subprocess.Popen(CHILD_COMMAND, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         env=CHILD_ENV, cwd=str(OUT), close_fds=True,
                                         pass_fds=(record_write,),
                                         preexec_fn=lambda: child_setup(record_write))
            finally:
                os.close(record_write)
            with os.fdopen(record_read, 'rb') as record:
                child_record = record.read(8193)
            require(len(child_record) <= 8192, 'child handshake cap')
            manifest['child_enforcement_before_network'] = json.loads(child_record)
            child_limits = manifest['child_enforcement_before_network']['actual_before_exec']
            require(child_limits['RLIMIT_AS'] == [192 * MIB, 192 * MIB]
                    and child_limits['RLIMIT_CPU'] == [20, 20]
                    and child_limits['RLIMIT_FSIZE'] == [MIB, MIB]
                    and child_limits['RLIMIT_NPROC'] == [0, 0], 'child handshake limits mismatch')
            require(CHILD.poll() is None, 'extractor exited before input')
            manifest['commands'].append(CHILD_COMMAND)
            manifest['extractor_pid'] = CHILD.pid
            event('Parent/child inherited and actual limits + seccomp verified before networking; extractor awaits stdin.')
            phase = 'single PDF request'
            request = urllib.request.Request(URL, headers={'Accept': 'application/pdf',
                       'Accept-Encoding': 'identity', 'User-Agent': 'S018-document-audit-v2'})
            with (OUT / 'source.pdf').open('xb') as source:
                manifest['network_attempts'] = 1
                transfer_start = time.monotonic()
                with opener.open(request, timeout=10) as response:
                    require(response.status == 200 and response.geturl() == URL, 'unexpected HTTP status/URL')
                    require(response.headers.get('Content-Encoding', 'identity').strip().lower() == 'identity',
                            'HTTP compression forbidden')
                    require(response.headers.get_content_type() == 'application/pdf', 'non-PDF content type')
                    require(not response.headers.get('Transfer-Encoding'), 'transfer encoding unsupported')
                    lengths = response.headers.get_all('Content-Length', [])
                    require(len(lengths) == 1 and lengths[0].isdigit() and len(lengths[0]) <= 10,
                            'unambiguous bounded Content-Length required')
                    length = int(lengths[0])
                    require(5 <= length <= MIB, 'Content-Length outside budget')
                    manifest['http'] = {'status': response.status, 'content_type': 'application/pdf',
                                        'content_encoding': 'identity', 'content_length': length}
                    received = 0
                    prefix = b''
                    while received < length:
                        block = response.read(min(16384, length - received))
                        require(bool(block), 'truncated body')
                        source.write(block)
                        if len(prefix) < 5:
                            prefix = (prefix + block)[:5]
                        received += len(block)
                    require(prefix == b'%PDF-', 'PDF magic absent')
                    manifest['download_body_bytes'] = received
                    manifest['download_complete'] = True
                    manifest['source_retrieved_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    manifest['download_wall_s'] = time.monotonic() - transfer_start
            event('Single PDF body complete; no redirect/retry/trace links or licensing acceptance.')
            phase = 'local text extraction'
            extraction_start = time.monotonic()
            manifest['extractor_pipe_bytes'] = pump_pdf(text_file, stderr_file)
            manifest['extractor_exit_code'] = CHILD.wait(timeout=1)
            manifest['extraction_wall_s'] = time.monotonic() - extraction_start
        require(manifest['extractor_exit_code'] == 0, 'extractor nonzero exit')
        phase = 'text validation'
        with (OUT / 'extracted.txt').open('rb') as stream:
            text = stream.read(MIB + 1).decode('utf-8', errors='strict')
        pages = text.split('\f')
        require(len(pages) > 1 and not pages[-1].strip() and bool(text.strip()), 'page delimiters/text absent')
        manifest['text_validation'] = {'utf8': True, 'form_feed_delimiters': len(pages) - 1,
                                       'nonempty_pages': sum(bool(p.strip()) for p in pages),
                                       'manual_sections_read_pending': True}
        require(limits()['RLIMIT_AS'] == [64 * MIB, 192 * MIB], 'parent AS changed')
        manifest['extraction_complete'] = True
        manifest['status'], manifest['exit_code'] = 'complete', 0
        event('Extraction complete with valid UTF-8/page delimiters; source claims require manual text inspection.')
    except Exception as error:
        manifest['failure_phase'] = phase
        manifest['error_type'] = type(error).__name__
        manifest['local_reason'] = str(error)[:180] if isinstance(error, StopAudit) else None
        event('Failure in ' + phase + ': ' + type(error).__name__ + '; STOP without retry.')
    finally:
        signal.signal(signal.SIGALRM, wall_alarm)
        signal.setitimer(signal.ITIMER_REAL, max(0.1, 50 - (time.monotonic() - START)))
        if CHILD is not None:
            if CHILD.poll() is None:
                CHILD.kill()
                CHILD.wait(timeout=2)
            manifest['extractor_exit_code'] = CHILD.returncode
            for pipe in (CHILD.stdin, CHILD.stdout, CHILD.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()
        manifest['parent_usage'] = rusage(resource.RUSAGE_SELF)
        manifest['children_usage_including_inherited_waited_children_if_any'] = rusage(resource.RUSAGE_CHILDREN)
        manifest['current_process_tree_cpu_s_before_final_writes'] = sum(
            manifest[key][field] for key in ('parent_usage', 'children_usage_including_inherited_waited_children_if_any')
            for field in ('user_cpu_s', 'system_cpu_s'))
        if manifest['current_process_tree_cpu_s_before_final_writes'] > 28:
            manifest['status'], manifest['exit_code'] = 'budget_failure', 1
        write_once(OUT / 'audit.log', encode(EVENTS), 8192)
        manifest['outputs'] = {p.name: fingerprint(p, MIB) for p in OUT.iterdir() if p.is_file()}
        manifest['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        manifest['wall_s_before_manifest'] = time.monotonic() - START
        new_bytes = sum(item['bytes'] for item in manifest['outputs'].values())
        manifest['old_docs_v1_script_plus_new_docs_v2_script_bytes_before_manifest'] = (
            prior_bytes + new_bytes + manifest.get('script', {}).get('bytes', 0))
        encoded = encode(manifest)
        total = manifest['old_docs_v1_script_plus_new_docs_v2_script_bytes_before_manifest'] + len(encoded) + 128
        require(total < 5 * MIB, 'aggregate old/new documentation byte cap')
        write_once(OUT / 'manifest.json', encoded, 32768)
        manifest_hash = fingerprint(OUT / 'manifest.json', 32768)
        sidecar = (manifest_hash['sha256'] + '  manifest.json\n').encode()
        write_once(OUT / 'manifest.sha256', sidecar, 128)
        final_cpu = sum(rusage(who)[field] for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
                        for field in ('user_cpu_s', 'system_cpu_s'))
        print(json.dumps({'status': manifest['status'], 'exit_code': manifest['exit_code'],
              'path': str(OUT), 'manifest': manifest_hash, 'wall_s': time.monotonic() - START,
              'current_tree_cpu_s': final_cpu,
              'old_and_new_docs_and_scripts_bytes': total - 128 + len(sidecar)}, sort_keys=True), flush=True)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return manifest['exit_code']


if __name__ == '__main__':
    sys.exit(main())
