#!/usr/bin/env python3
"""Prueft, dass StrId (i18n.h) und STRINGS (i18n.cpp) parallel laufen.

Ein Eintrag zu viel oder zu wenig verschiebt jeden spaeteren Text still in
allen Sprachen - der Compiler merkt das nicht, solange die Anzahl stimmt.

    python3 tools/check_i18n.py                 # Anzahl pro Sprache pruefen
    python3 tools/check_i18n.py --dump a.json   # Zuordnung Name -> Text sichern
    python3 tools/check_i18n.py --diff a.json   # gegen Sicherung vergleichen

--dump vor einer Aenderung, --diff danach: jeder Name, der in beiden Staenden
existiert, muss in jeder Sprache denselben Text haben.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['ES', 'EN', 'FR', 'DE', 'IT', 'PT']


def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)


def enum_names():
    h = strip_comments(open(os.path.join(ROOT, 'i18n.h'), encoding='utf-8').read())
    body = re.search(r'enum StrId : uint8_t \{(.*?)\};', h, re.S).group(1)
    names = [n.strip() for n in body.split(',') if n.strip()]
    assert names[-1] == 'STR_COUNT', 'STR_COUNT muss der letzte Eintrag sein'
    return names[:-1]


def string_rows():
    c = open(os.path.join(ROOT, 'i18n.cpp'), encoding='utf-8').read()
    body = re.search(r'STRINGS\[LANG_COUNT\]\[STR_COUNT\] = \{(.*?)\n\};', c, re.S).group(1)
    rows = re.findall(r'\n  \{\n(.*?)\n  \},', body, re.S)
    # Stringliterale; benachbarte Literale verkettet C, hier nicht vorhanden
    return [re.findall(r'"((?:[^"\\]|\\.)*)"', strip_comments(r)) for r in rows]


def mapping():
    names = enum_names()
    rows = string_rows()
    ok = True
    if len(rows) != len(LANGS):
        print('FEHLER: %d Sprachzeilen statt %d' % (len(rows), len(LANGS)))
        ok = False
    for lang, row in zip(LANGS, rows):
        if len(row) != len(names):
            print('FEHLER %s: %d Texte, StrId hat %d' % (lang, len(row), len(names)))
            ok = False
    m = {lang: dict(zip(names, row)) for lang, row in zip(LANGS, rows)}
    return names, m, ok


def main():
    names, m, ok = mapping()
    print('StrId: %d Eintraege, 6 Sprachen' % len(names))
    if '--dump' in sys.argv:
        json.dump(m, open(sys.argv[sys.argv.index('--dump') + 1], 'w'), indent=1)
        print('gesichert')
    if '--diff' in sys.argv:
        old = json.load(open(sys.argv[sys.argv.index('--diff') + 1]))
        for lang in LANGS:
            gone = sorted(set(old[lang]) - set(m[lang]))
            new = sorted(set(m[lang]) - set(old[lang]))
            moved = [n for n in m[lang] if n in old[lang] and m[lang][n] != old[lang][n]]
            for n in moved:
                print('VERSATZ %s %s: %r -> %r' % (lang, n, old[lang][n], m[lang][n]))
                ok = False
            if lang == 'ES':
                print('entfernt: %s' % (', '.join(gone) or '-'))
                print('neu:      %s' % (', '.join(new) or '-'))
        print('jeder gemeinsame Name hat in allen Sprachen denselben Text'
              if ok else '')
    print('OK' if ok else '!!! FEHLER')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
