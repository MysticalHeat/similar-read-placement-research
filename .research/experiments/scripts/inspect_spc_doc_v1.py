#!/usr/bin/env python3
"""One authorized S018 document audit; never a trace or experimental run.

Stdlib only. Read this entire file before execution. No retry or resume mode.
All owned outputs use exclusive creation; a manifest is written once at the end.
Linux x86_64 only: fail closed on missing limits/seccomp/extractor. Installed
pdftotext is a trusted system tool, not downloaded source code. Its child gets
no credentials, no network/descendants/write-open syscalls, and bounded pipes.
RLIMIT_AS is virtual address space, NOT measured RSS or a cgroup memory limit.
"""
import ctypes
import datetime
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import selectors
import signal
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path('/home/nomli/workspace/bdss_lab/research1')
OUT = ROOT / '.research/experiments/documentation/S018-2026-10-01-docaudit-a91c7e'
URL = 'https://skulddata.cs.umass.edu/traces/storage/SPC-Traces.pdf'
EXTRACTOR = Path('/usr/bin/pdftotext')
PROTOCOL = ROOT / '.research/protocol/temperature-poc-checkpoint-2026-10-01.md'
SCRIPT = Path(__file__).resolve()
MIB = 1024 * 1024
CONFIG = {
    'version': 'S018-document-audit-v1', 'source_id': 'S018', 'related_claim': 'C022',
    'kind': 'DOCUMENT_ONLY_NOT_EXPERIMENT', 'url': URL, 'max_attempts': 1,
    'redirects': False, 'proxies': False, 'socket_timeout_s': 10,
    'operation_wall_s': 45, 'internal_total_wall_s': 50, 'shell_timeout_s': 55,
    'inventory_timeout_s': 5, 'parent_cpu_s': 7, 'child_cpu_s': 20,
    'inventory_shell_cpu_s': 1, 'inventory_ls_cpu_s': 1,
    'execution_ls_cpu_s': 1, 'aggregate_controlled_cpu_ceiling_s': 30,
    'parent_as_bytes': 64 * MIB, 'child_as_bytes': 192 * MIB,
    'pdf_bytes': MIB, 'text_bytes': 2 * MIB, 'stderr_bytes': 16384,
    'log_bytes': 8192, 'manifest_bytes': 32768, 'config_bytes': 8192,
    'max_new_document_bytes': 5 * MIB, 'child_fsize_bytes': 2 * MIB,
    'child_nproc': 0, 'child_environment': {
        'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
        'HOME': '/nonexistent', 'XDG_CACHE_HOME': '/nonexistent',
        'TMPDIR': '/nonexistent', 'OMP_NUM_THREADS': '1',
    },
    'extractor_options': ['-layout', '-enc', 'UTF-8', '-eol', 'unix'],
    'warmup': None, 'seed': None, 'independent_unit': None,
    'repetitions': None, 'workload_split_model': None,
}
START = time.monotonic()
START_UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()
CHILD = None
EVENTS = []


def event(message):
    # Only first-party operational messages, never server headers/body/errors.
    EVENTS.append({'elapsed_s': round(time.monotonic() - START, 6),
                   'message': message[:180]})
    if len(EVENTS) > 24:
        raise RuntimeError('log event cap')


def write_once(path, data, cap):
    if len(data) > cap:
        raise RuntimeError('artifact byte cap')
    with path.open('xb') as stream:
        stream.write(data)


def serialized(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + '\n').encode()


def digest(path, cap):
    h = hashlib.sha256()
    n = 0
    with path.open('rb') as stream:
        while True:
            block = stream.read(16384)
            if not block:
                break
            n += len(block)
            if n > cap:
                raise RuntimeError('hash input cap')
            h.update(block)
    return {'bytes': n, 'sha256': h.hexdigest()}


def limit(which, value):
    soft, hard = resource.getrlimit(which)
    if hard != resource.RLIM_INFINITY and hard < value:
        raise RuntimeError('existing hard limit incompatible')
    resource.setrlimit(which, (value, value))
    if resource.getrlimit(which) != (value, value):
        raise RuntimeError('limit verification failed')


class BPF(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
               ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint32)]


class Program(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filter', ctypes.POINTER(BPF))]


LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.prctl.restype = ctypes.c_int


def seccomp(child):
    # seccomp_data: nr@0, arch@4, args[1]@24, args[2]@32 (x86_64 LE).
    # Kill wrong architecture/x32; deny listed calls with EPERM.
    instructions = [BPF(0x20, 0, 0, 4),
                    BPF(0x15, 1, 0, 0xC000003E), BPF(0x06, 0, 0, 0x80000000),
                    BPF(0x20, 0, 0, 0),
                    BPF(0x35, 0, 1, 0x40000000), BPF(0x06, 0, 0, 0x80000000)]
    if child:
        denied = list(range(41, 56)) + [56, 57, 58, 101, 272, 288, 299,
                   307, 308, 321, 322, 425, 426, 427, 435, 437,
                   76, 77, 82, 83, 84, 85, 86, 87, 88, 133,
                   258, 259, 260, 263, 264, 265, 266, 316]
        for number in sorted(set(denied)):
            instructions += [BPF(0x15, 0, 1, number),
                             BPF(0x06, 0, 0, 0x00050000 | errno.EPERM)]
        for number, offset in [(2, 24), (257, 32)]:  # open, openat flags
            instructions += [BPF(0x15, 0, 4, number), BPF(0x20, 0, 0, offset),
                             BPF(0x45, 0, 1, 3 | 64 | 512 | 1024 | 0x400000),
                             BPF(0x06, 0, 0, 0x00050000 | errno.EPERM),
                             BPF(0x20, 0, 0, 0)]
    instructions += [BPF(0x06, 0, 0, 0x7FFF0000)]
    array = (BPF * len(instructions))(*instructions)
    program = Program(len(instructions), array)
    if LIBC.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise RuntimeError('no_new_privs unavailable')
    if LIBC.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise RuntimeError('seccomp filter unavailable')


def child_setup():
    limit(resource.RLIMIT_AS, CONFIG['child_as_bytes'])
    limit(resource.RLIMIT_CPU, CONFIG['child_cpu_s'])
    limit(resource.RLIMIT_FSIZE, CONFIG['child_fsize_bytes'])
    limit(resource.RLIMIT_NPROC, 0)
    limit(resource.RLIMIT_CORE, 0)
    seccomp(True)


def alarm_handler(signum, frame):
    raise TimeoutError('internal wall watchdog')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError('redirect forbidden')


def package_records():
    # Inspect existing installed-package metadata, not repository code/scripts.
    result, paragraph, total = [], [], 0
    with open('/var/lib/dpkg/status', 'r', encoding='utf-8') as stream:
        while True:
            line = stream.readline(8193)
            total += len(line.encode('utf-8'))
            if total > 8 * MIB or len(line) > 8192:
                raise RuntimeError('installed metadata read cap')
            if line.strip():
                paragraph.append(line)
                if len(paragraph) > 256:
                    raise RuntimeError('installed paragraph cap')
            else:
                fields = {}
                for item in paragraph:
                    if ': ' in item and not item.startswith(' '):
                        key, value = item.rstrip().split(': ', 1)
                        if key in ('Package', 'Version', 'Architecture'):
                            fields[key] = value
                name = fields.get('Package', '')
                if name == 'poppler-utils' or name.startswith(('libpoppler', 'libssl')) or name == 'libc6':
                    result.append(fields)
                paragraph = []
                if not line:
                    break
    return result


def cpu_model():
    with open('/proc/cpuinfo', 'rb') as stream:
        text = stream.read(16384).decode('ascii', errors='replace')
    for line in text.splitlines():
        if line.startswith('model name'):
            return line.split(':', 1)[1].strip()[:160]
    return None


def usage(who):
    value = resource.getrusage(who)
    return {'user_cpu_s': value.ru_utime, 'system_cpu_s': value.ru_stime,
            'maxrss_kib_linux': value.ru_maxrss,
            'minor_faults': value.ru_minflt, 'major_faults': value.ru_majflt,
            'voluntary_context_switches': value.ru_nvcsw,
            'involuntary_context_switches': value.ru_nivcsw}


def main():
    global CHILD
    manifest = {'source_id': 'S018', 'related_claim': 'C022', 'experiment_id': None,
                'document_audit_id': OUT.name, 'started_at': START_UTC,
                'source_url': URL, 'status': 'failed', 'exit_code': 1,
                'network_attempts': 0, 'download_complete': False,
                'extraction_complete': False, 'error_type': None,
                'code_commit': None, 'git_inspection': 'not authorized/performed',
                'config': CONFIG, 'commands': [], 'deviations': [],
                'inspection_record': str(OUT / 'INSPECTION.md'),
                'isolation_caveats': [
                    'RLIMIT_AS caps virtual address space, not RSS/cgroup memory.',
                    'Controlled processes only; tool host and kernel resources not cgroup-accounted.',
                    'System extractor/dependencies trusted; no source-level audit of Poppler.',
                    'Seccomp denylist is not a full OS sandbox/filesystem-read isolation.',
                    'DNS/TLS involve system resolver and permitted HTTPS server; no proxy/redirect/retry.',
                    'No PDF actions explicitly invoked; pdftotext text conversion only.',
                    'Shared-library hashes/complete dependency lock not captured; selected installed versions only.',
                    'Outer hard kill/CPU hard kill could prevent final manifest; partial files remain.',
                ]}
    outputs = ['INSPECTION.md', 'config.json', 'source.pdf', 'extracted.txt',
               'extractor.stderr.log', 'audit.log']
    extract_command = [str(EXTRACTOR), *CONFIG['extractor_options'], str(OUT / 'source.pdf'), '-']
    try:
        limit(resource.RLIMIT_AS, CONFIG['parent_as_bytes'])
        limit(resource.RLIMIT_CPU, CONFIG['parent_cpu_s'])
        limit(resource.RLIMIT_FSIZE, CONFIG['pdf_bytes'])
        limit(resource.RLIMIT_CORE, 0)
        if platform.system() != 'Linux' or platform.machine() != 'x86_64' or os.getuid() == 0:
            raise RuntimeError('unsupported enforcement platform/uid')
        if not OUT.is_dir() or OUT.is_symlink() or not SCRIPT.is_file():
            raise RuntimeError('owned directory/script unavailable')
        if sorted(p.name for p in OUT.iterdir()) != ['INSPECTION.md']:
            raise RuntimeError('directory is not a new inspected audit directory')
        if not EXTRACTOR.is_file() or not os.access(EXTRACTOR, os.X_OK):
            raise RuntimeError('existing extractor unavailable')
        with EXTRACTOR.open('rb') as stream:
            header = stream.read(64)
        if header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\x3e\x00':
            raise RuntimeError('extractor not native x86_64 ELF')
        seccomp(False)  # Verify filter support before the one network request.
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.setitimer(signal.ITIMER_REAL, CONFIG['operation_wall_s'] - (time.monotonic() - START))
        manifest['script'] = {'path': str(SCRIPT), **digest(SCRIPT, 65536)}
        manifest['protocol'] = {'path': str(PROTOCOL), **digest(PROTOCOL, 65536)}
        manifest['extractor'] = {'path': str(EXTRACTOR), **digest(EXTRACTOR, 8 * MIB)}
        manifest['runtime'] = {'executable': sys.executable, 'python': sys.version,
                               'openssl': ssl.OPENSSL_VERSION,
                               'uname': platform.uname()._asdict(), 'cpu_model': cpu_model(),
                               'logical_cpu_count': os.cpu_count(),
                               'installed_packages': package_records(),
                               'load_average_before': os.getloadavg(),
                               'third_party_installs': False}
        manifest['parent_rlimits'] = {name: resource.getrlimit(getattr(resource, name))
                                      for name in ('RLIMIT_AS', 'RLIMIT_CPU', 'RLIMIT_FSIZE', 'RLIMIT_CORE')}
        manifest['commands'].append([sys.executable, '-I', '-S', str(SCRIPT)])
        write_once(OUT / 'config.json', serialized(CONFIG), CONFIG['config_bytes'])
        manifest['config_sha256'] = digest(OUT / 'config.json', CONFIG['config_bytes'])['sha256']
        event('Preflight complete; installed extractor ELF/sha256 and local package metadata inspected.')
        context = ssl.create_default_context()
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                             urllib.request.HTTPSHandler(context=context))
        request = urllib.request.Request(URL, headers={'Accept': 'application/pdf',
                                                      'Accept-Encoding': 'identity',
                                                      'User-Agent': 'S018-document-audit-v1'})
        # Empty exclusive file persists even on HTTP/TLS/header failure.
        with (OUT / 'source.pdf').open('xb') as destination:
            manifest['network_attempts'] = 1
            download_start = time.monotonic()
            event('Single HTTPS request started; SSL verification enabled, no proxies/retry/redirect.')
            with opener.open(request, timeout=CONFIG['socket_timeout_s']) as response:
                if response.status != 200 or response.geturl() != URL:
                    raise RuntimeError('unexpected response status/URL')
                if response.headers.get('Content-Encoding', 'identity').strip().lower() != 'identity':
                    raise RuntimeError('compressed HTTP response forbidden')
                content_type = response.headers.get_content_type()
                if content_type != 'application/pdf':
                    raise RuntimeError('non-PDF content type')
                if response.headers.get('Transfer-Encoding'):
                    raise RuntimeError('transfer encoding unsupported for strict byte cap')
                lengths = response.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or not lengths[0].isdigit():
                    raise RuntimeError('unambiguous bounded Content-Length required')
                length = int(lengths[0])
                if length < 5 or length > CONFIG['pdf_bytes']:
                    raise RuntimeError('Content-Length outside PDF budget')
                manifest['http'] = {'status': response.status, 'content_type': content_type,
                                    'content_length': length, 'content_encoding': 'identity'}
                received = 0
                while received < length:
                    block = response.read(min(16384, length - received))
                    if not block:
                        raise RuntimeError('truncated body')
                    if received == 0 and not block.startswith(b'%PDF-'):
                        raise RuntimeError('non-PDF magic')
                    destination.write(block)
                    received += len(block)
                # Do not read an extra probe byte: strict application body budget.
                manifest['download_complete'] = True
                manifest['download_body_bytes'] = received
                manifest['download_wall_s'] = time.monotonic() - download_start
        event('PDF body complete within Content-Length/body cap; no trace links followed.')
        manifest['commands'].append(extract_command)
        extract_start = time.monotonic()
        with (OUT / 'extracted.txt').open('xb') as text_file, \
                (OUT / 'extractor.stderr.log').open('xb') as error_file:
            CHILD = subprocess.Popen(extract_command, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     env=CONFIG['child_environment'], cwd=str(OUT),
                                     close_fds=True, preexec_fn=child_setup)
            manifest['extractor_pid'] = CHILD.pid
            sizes = {'stdout': 0, 'stderr': 0}
            with selectors.DefaultSelector() as selector:
                for pipe, key, stream, cap in [(CHILD.stdout, 'stdout', text_file, CONFIG['text_bytes']),
                                               (CHILD.stderr, 'stderr', error_file, CONFIG['stderr_bytes'])]:
                    os.set_blocking(pipe.fileno(), False)
                    selector.register(pipe, selectors.EVENT_READ, (key, stream, cap))
                while selector.get_map():
                    for selected, mask in selector.select(timeout=0.25):
                        key, stream, cap = selected.data
                        block = os.read(selected.fd, 16384)
                        if not block:
                            selector.unregister(selected.fileobj)
                            selected.fileobj.close()
                            continue
                        remaining = cap - sizes[key]
                        stream.write(block[:remaining])
                        sizes[key] += min(len(block), remaining)
                        if len(block) > remaining:
                            raise RuntimeError('extractor pipe byte cap reached')
            manifest['extractor_exit_code'] = CHILD.wait(timeout=1)
            manifest['extractor_pipe_bytes'] = sizes
        manifest['extract_wall_s'] = time.monotonic() - extract_start
        if manifest['extractor_exit_code'] != 0:
            raise RuntimeError('extractor nonzero exit')
        with (OUT / 'extracted.txt').open('rb') as stream:
            extracted = stream.read(CONFIG['text_bytes'] + 1)
        text = extracted.decode('utf-8', errors='strict')
        pages = text.split('\f')
        count = len(pages) - 1
        if count < 1 or pages[-1].strip() or not text.strip():
            raise RuntimeError('text/page delimiters unavailable')
        manifest['text_validation'] = {'utf8': True, 'form_feed_delimiters': count,
                                       'nonempty_pages': sum(bool(p.strip()) for p in pages),
                                       'manual_sections_inspection_pending': True}
        manifest['extraction_complete'] = True
        manifest['status'], manifest['exit_code'] = 'complete', 0
        event('Extractor completed; UTF-8 and form-feed page delimiters validated; manual reading pending.')
    except Exception as error:
        manifest['error_type'] = type(error).__name__
        # No raw exception string: remote messages could contain hostile/large data.
        manifest['failure_stage'] = EVENTS[-1]['message'] if EVENTS else 'preflight'
        event('Failure: ' + type(error).__name__ + '; STOP, no retry.')
    finally:
        # Operation timer leaves >=5s for bounded cleanup/manifest under 50s.
        signal.signal(signal.SIGALRM, alarm_handler)
        remaining = max(0.1, CONFIG['internal_total_wall_s'] - (time.monotonic() - START))
        signal.setitimer(signal.ITIMER_REAL, remaining)
        if CHILD is not None:
            if CHILD.poll() is None:
                CHILD.kill()
                CHILD.wait(timeout=2)
            manifest['extractor_exit_code'] = CHILD.returncode
            for pipe in (CHILD.stdout, CHILD.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()
        manifest['parent_usage'] = usage(resource.RUSAGE_SELF)
        manifest['child_usage'] = usage(resource.RUSAGE_CHILDREN)
        manifest['controlled_python_and_child_cpu_s'] = sum(
            manifest[key][field] for key in ('parent_usage', 'child_usage')
            for field in ('user_cpu_s', 'system_cpu_s'))
        write_once(OUT / 'audit.log', serialized(EVENTS), CONFIG['log_bytes'])
        manifest['outputs'] = {name: digest(OUT / name, 3 * MIB)
                               for name in outputs if (OUT / name).is_file()}
        manifest['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        manifest['wall_s_before_manifest'] = time.monotonic() - START
        encoded = serialized(manifest)
        manifest['document_bytes_excluding_manifest'] = sum(x['bytes'] for x in manifest['outputs'].values())
        encoded = serialized(manifest)
        if manifest['document_bytes_excluding_manifest'] + len(encoded) > CONFIG['max_new_document_bytes']:
            raise RuntimeError('total documentation byte cap')
        write_once(OUT / 'manifest.json', encoded, CONFIG['manifest_bytes'])
        # Manifest cannot self-hash; bounded stdout supplies its independent hash.
        result = {'status': manifest['status'], 'exit_code': manifest['exit_code'],
                  'path': str(OUT), 'manifest': digest(OUT / 'manifest.json', CONFIG['manifest_bytes']),
                  'total_document_bytes': manifest['document_bytes_excluding_manifest'] + len(encoded),
                  'wall_s': time.monotonic() - START,
                  'controlled_cpu_s': manifest['controlled_python_and_child_cpu_s']}
        print(json.dumps(result, sort_keys=True), flush=True)
        signal.setitimer(signal.ITIMER_REAL, 0)
    return manifest['exit_code']


if __name__ == '__main__':
    sys.exit(main())
