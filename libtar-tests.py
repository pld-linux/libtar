#!/usr/bin/python3
"""Regression inputs for the PLD libtar patches; no network or system install."""
import ctypes
import os
from pathlib import Path
import resource
import subprocess
import sys
import tarfile
import tempfile

exe, libdir, probe = map(lambda x: str(Path(x).resolve()), sys.argv[1:])
env = dict(os.environ, LD_LIBRARY_PATH=libdir, MALLOC_MMAP_THRESHOLD_='0')
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
failures = []


def run(args, ok=True):
    p = subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if (p.returncode == 0) != ok or p.returncode < 0:
        raise AssertionError((args, p.returncode, p.stderr.decode(errors='replace')))
    return p


def header(name, kind=tarfile.REGTYPE, size=0, link=''):
    h = tarfile.TarInfo(name)
    h.type, h.size, h.linkname, h.mode = kind, size, link, 0o644
    return h.tobuf(format=tarfile.USTAR_FORMAT)


def check(label, func):
    try:
        func()
        print('PASS:', label, flush=True)
    except Exception as e:
        failures.append(label)
        print('FAIL:', label, repr(e), flush=True)


def read_one(path, expected):
    args = [probe, str(path), str(expected)]
    if os.environ.get('LIBTAR_VALGRIND'):
        args = ['valgrind', '--quiet', '--leak-check=full',
                '--errors-for-leak-kinds=definite,indirect',
                '--error-exitcode=99'] + args
    run(args)


with tempfile.TemporaryDirectory(prefix='libtar-tests-') as tmp:
    os.chdir(tmp)
    p = Path(tmp)

    def roundtrip(compressed):
        tag = 'gzip' if compressed else 'plain'
        src = p / ('in-' + tag)
        src.mkdir()
        (src / 'file').write_bytes(b'libtar roundtrip\n' * 100)
        (src / 'symlink').symlink_to('file')
        os.link(src / 'file', src / 'hardlink')
        archive = p / (tag + '.tar')
        flags = ['-z'] if compressed else []
        run([exe, *flags, '-C', str(src), '-c', str(archive), '.'])
        run([exe, *flags, '-t', str(archive)])
        dest = p / ('out-' + tag)
        dest.mkdir()
        run([exe, *flags, '-C', str(dest), '-x', str(archive)])
        assert (dest / 'file').read_bytes() == (src / 'file').read_bytes()
        assert (dest / 'symlink').is_symlink()
        assert (dest / 'file').stat().st_ino == (dest / 'hardlink').stat().st_ino

    check('plain archive create/list/extract with links', lambda: roundtrip(False))
    check('gzip LP64 create/list/extract with mmap allocations', lambda: roundtrip(True))

    for kind in (tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK):
        label = kind.decode()
        for size in (0, 0xffffffff):
            path = p / ('bad-' + label + '-' + str(size) + '.tar')
            path.write_bytes(header('././@LongLink', kind, size) + header('normal') + bytes(1024))
            check('reject GNU %s size %d' % (label, size), lambda path=path: read_one(path, -1))
        for truncated in (False, True):
            path = p / ('long-' + label + str(truncated) + '.tar')
            data = b'x' * 160 + b'\0'
            path.write_bytes(header('././@LongLink', kind, len(data)) +
                             (b'' if truncated else data.ljust(512, b'\0') + header('normal')))
            check('close GNU %s truncated=%s' % (label, truncated),
                  lambda path=path, truncated=truncated: read_one(path, -1 if truncated else 0))

    def traversal(name, kind, link, number):
        archive = p / ('traversal-%d.tar' % number)
        archive.write_bytes(header(name, kind, 1 if kind == tarfile.REGTYPE else 0, link) +
                            (b'X' + bytes(511) if kind == tarfile.REGTYPE else b'') + bytes(1024))
        case = p / ('case-%d' % number)
        case.mkdir()
        dest = case / 'out'
        dest.mkdir()
        outside = case / 'escape'
        outside.write_bytes(b'untouched')
        # Relative hardlink targets are interpreted against the working directory.
        old_cwd = Path.cwd()
        try:
            os.chdir(dest)
            run([exe, '-x', str(archive)], ok=False)
        finally:
            os.chdir(old_cwd)
        assert not list(dest.iterdir())
        assert outside.read_bytes() == b'untouched'

    attacks = [('../escape', tarfile.REGTYPE, ''),
               ('a/../../escape', tarfile.REGTYPE, ''),
               (str(p / 'escape'), tarfile.REGTYPE, ''),
               ('link', tarfile.SYMTYPE, '..'),
               ('link', tarfile.SYMTYPE, '../escape'),
               ('link', tarfile.LNKTYPE, '../escape')]
    for i, args in enumerate(attacks):
        check('CVE-2013-4420 case %d' % i, lambda args=args, i=i: traversal(*args, i))

    def malformed_listing():
        path = p / 'broken.tar'
        path.write_bytes(b'x' * 512)
        run([exe, '-t', str(path)], ok=False)
    check('CLI propagates malformed archive error', malformed_listing)

    def octal():
        lib = ctypes.CDLL(str(Path(libdir) / 'libtar.so.0.0.0'))
        f = lib.int_to_oct_nonull
        f.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
        f.restype = None
        for n in (0, 83, 4095):
            out = ctypes.create_string_buffer(8)
            f(n, out, 8)
            assert out.raw == (format(n, 'o').rjust(7) + ' ').encode()
    check('octal header formatting', octal)

if failures:
    sys.exit('Failed: ' + ', '.join(failures))
