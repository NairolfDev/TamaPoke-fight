#!/usr/bin/env python3
"""Schuetzt das Pokemon vor dem Flashen.

Prueft, dass kein Teil, den flash.bat schreibt, die NVS-Partition beruehrt.
Dort liegt der ganze Spielstand. Das 16-MB-Vollabbild merged.bin enthaelt an
dieser Stelle nur 0xFF - wer es ab 0x0 schreibt, loescht das Pokemon. Genau
so ist das beim Flash von Phase 5 passiert.

    python3 tools/check_flash.py [build/battle]   # Exitcode 0 = sicher
    python3 tools/check_flash.py --self-test
    python3 tools/check_flash.py --web          # Browser-Installer in web/
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


def pairs(flash_args):
    """(Adresse, Datei) aus flash_args - Wort fuer Wort, so wie esptool die
    Datei liest. Schalter (--x wert) werden uebersprungen; ein Wort, das
    weder Schalter noch Adresse ist, bricht ab, statt still uebersehen zu
    werden."""
    words = flash_args.split()
    out = []
    i = 0
    while i < len(words):
        w = words[i]
        if w.startswith('--'):
            i += 2
        elif w.lower().startswith('0x') and i + 1 < len(words):
            out.append((int(w, 16), words[i + 1]))
            i += 2
        else:
            raise ValueError('unbekanntes Wort in flash_args: %r' % w)
    if not out:
        raise ValueError('flash_args enthaelt keine Adressen')
    return out


def segments(flash_args, sizes):
    """(Adresse, Datei, Laenge); sizes: Datei -> Bytes."""
    return [(a, f, sizes[f]) for a, f in pairs(flash_args)]


def problems(nvs, segs):
    lo, hi = nvs
    return ['%s an %s..%s ueberschreibt NVS %s..%s'
            % (f, hex(a), hex(a + n), hex(lo), hex(hi))
            for a, f, n in segs if a < hi and a + n > lo]


def web_segments(manifest, firmware_dir):
    """(Adresse, Datei, Laenge) aus dem Manifest des Web-Installers."""
    import json
    out = []
    for build in json.loads(manifest)['builds']:
        for part in build['parts']:
            path = os.path.join(firmware_dir, os.path.basename(part['path']))
            out.append((int(part['offset']), part['path'], os.path.getsize(path)))
    return out


def check_web(manifest_path, partitions_csv):
    """Der Browser-Installer schreibt seine Teile ohne Erase genauso hart wie
    esptool - auch er darf NVS nicht beruehren."""
    manifest = open(manifest_path, encoding='utf-8').read()
    fw = os.path.join(os.path.dirname(manifest_path), 'firmware')
    csv = open(partitions_csv, encoding='utf-8').read()
    bad = problems(nvs_range(csv), web_segments(manifest, fw))
    for b in bad:
        print('GEFAHR (Web-Installer): ' + b)
    if not bad:
        print('sicher: der Web-Installer beruehrt den Spielstand (NVS) nicht')
    return not bad


def check(build_dir):
    csv = open(os.path.join(build_dir, 'partitions.csv'), encoding='utf-8').read()
    args = open(os.path.join(build_dir, 'flash_args'), encoding='utf-8').read()
    sizes = {f: os.path.getsize(os.path.join(build_dir, f)) for _, f in pairs(args)}
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
    # esptool liest @flash_args Wort fuer Wort - mehrere Teile in einer Zeile
    # muessen genauso gesehen werden wie einer pro Zeile.
    one_line = '--flash-mode dio 0x0 boot.bin 0x8000 merged.bin\n'
    assert [s[1] for s in segments(one_line, sizes)] == ['boot.bin', 'merged.bin']
    assert problems(nvs_range(csv), segments(one_line, sizes)), 'Gefahr uebersehen'
    # ein Wort, das weder Schalter noch Adresse ist: lieber abbrechen
    try:
        segments('0x0 boot.bin seltsam\n', sizes)
        raise AssertionError('unbekanntes Wort nicht erkannt')
    except ValueError:
        pass
    print('Selbsttest OK')


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
        sys.exit(0)
    if '--web' in sys.argv:
        # gleiches Partitionsschema wie der Build (tools/build_web.sh: gleiche FQBN)
        csv = os.path.join(ROOT, 'build', 'battle', 'partitions.csv')
        sys.exit(0 if check_web(os.path.join(ROOT, 'web', 'manifest.json'), csv) else 1)
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'battle')
    sys.exit(0 if check(d) else 1)
