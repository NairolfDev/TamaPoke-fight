#!/usr/bin/env python3
"""Schuetzt das Pokemon vor dem Flashen.

Prueft, dass kein Teil, den flash.bat schreibt, die NVS-Partition beruehrt.
Dort liegt der ganze Spielstand. Das 16-MB-Vollabbild merged.bin enthaelt an
dieser Stelle nur 0xFF - wer es ab 0x0 schreibt, loescht das Pokemon. Genau
so ist das beim Flash von Phase 5 passiert.

    python3 tools/check_flash.py [build/battle]   # Exitcode 0 = sicher
    python3 tools/check_flash.py --self-test
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def nvs_range(partitions_csv):
    for line in partitions_csv.splitlines():
        cols = [c.strip() for c in line.split('#')[0].split(',')]
        if len(cols) >= 5 and cols[1] == 'data' and cols[2] == 'nvs':
            off = int(cols[3], 0)
            return off, off + int(cols[4], 0)
    raise ValueError('keine nvs-Partition in partitions.csv')


def segments(flash_args, sizes):
    """(Adresse, Datei, Laenge) aus flash_args; sizes: Datei -> Bytes."""
    out = []
    for line in flash_args.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].startswith('0x'):
            out.append((int(parts[0], 16), parts[1], sizes[parts[1]]))
    if not out:
        raise ValueError('flash_args enthaelt keine Adressen')
    return out


def problems(nvs, segs):
    lo, hi = nvs
    return ['%s an %s..%s ueberschreibt NVS %s..%s'
            % (f, hex(a), hex(a + n), hex(lo), hex(hi))
            for a, f, n in segs if a < hi and a + n > lo]


def check(build_dir):
    csv = open(os.path.join(build_dir, 'partitions.csv'), encoding='utf-8').read()
    args = open(os.path.join(build_dir, 'flash_args'), encoding='utf-8').read()
    names = [l.split()[1] for l in args.splitlines()
             if len(l.split()) == 2 and l.split()[0].startswith('0x')]
    sizes = {n: os.path.getsize(os.path.join(build_dir, n)) for n in names}
    bad = problems(nvs_range(csv), segments(args, sizes))
    for b in bad:
        print('GEFAHR: ' + b)
    if not bad:
        print('sicher: kein Teil beruehrt den Spielstand (NVS)')
    return not bad


def self_test():
    csv = 'nvs,      data, nvs,     0x9000,  0x5000,\n' \
          'app0,     app,  ota_0,   0x10000, 0x300000,\n'
    assert nvs_range(csv) == (0x9000, 0xE000)
    safe = '--flash-mode dio\n0x0 boot.bin\n0x8000 part.bin\n' \
           '0xe000 app0.bin\n0x10000 app.bin\n'
    sizes = {'boot.bin': 19968, 'part.bin': 3072, 'app0.bin': 8192,
             'app.bin': 628848, 'merged.bin': 0x1000000}
    assert problems(nvs_range(csv), segments(safe, sizes)) == []
    # Genau der Fehler von Phase 5: Vollabbild ab 0x0
    assert problems(nvs_range(csv), segments('0x0 merged.bin\n', sizes))
    # Grenzfaelle: endet genau an NVS-Beginn ok, ein Byte hinein nicht
    assert problems((0x9000, 0xE000), [(0x8000, 'p', 0x1000)]) == []
    assert problems((0x9000, 0xE000), [(0x8000, 'p', 0x1001)])
    assert problems((0x9000, 0xE000), [(0xE000, 'p', 0x2000)]) == []
    print('Selbsttest OK')


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
        sys.exit(0)
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'battle')
    sys.exit(0 if check(d) else 1)
