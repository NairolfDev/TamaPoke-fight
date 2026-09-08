#!/usr/bin/env python3
"""Baja de PokeAPI los tipos (1 y 2) de las 151 y escribe tools/type_data.py.

  python3 tools/gen_type_data.py

dex_data.py solo guarda UN tipo por especie y ademas solo como color de la
UI (le falta 'volador' entero). Para el combate hacen falta los dos tipos
reales, asi que se bajan aparte.

Las respuestas se cachean en tools/.pokeapi/ para no repetir descargas.
"""
import concurrent.futures
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from type_chart import TYPES

CACHE = os.path.join(os.path.dirname(__file__), '.pokeapi')


def fetch(url, key):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, key + '.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    for intento in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return data
        except Exception:
            if intento == 3:
                raise SystemExit(f'no se pudo bajar {url}')


# PokeAPI sirve los tipos MODERNOS. Las especies que cambiaron de tipo
# despues de gen 1 (las de tipo hada, sobre todo) traen su tipo antiguo en
# past_types; se coge la entrada de generacion mas baja, que es la que cubre
# gen 1.
GEN_ORDER = ['generation-i', 'generation-ii', 'generation-iii', 'generation-iv',
             'generation-v', 'generation-vi', 'generation-vii', 'generation-viii',
             'generation-ix']


def one(num):
    d = fetch(f'https://pokeapi.co/api/v2/pokemon/{num}/', f'mon{num}')
    bloque = d['types']
    pasados = d.get('past_types') or []
    if pasados:
        pasados.sort(key=lambda p: GEN_ORDER.index(p['generation']['name']))
        bloque = pasados[0]['types']
    tipos = [t['type']['name'] for t in sorted(bloque, key=lambda t: t['slot'])]
    for t in tipos:
        if t not in TYPES:
            raise SystemExit(f'tipo desconocido en gen 1: {t} (dex {num})')
    return num, tipos


def main():
    out = {}
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for num, tipos in sorted(ex.map(one, range(1, 152))):
            out[num] = tipos

    dobles = sum(1 for t in out.values() if len(t) == 2)
    path = os.path.join(os.path.dirname(__file__), 'type_data.py')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""GENERADO por tools/gen_type_data.py desde PokeAPI - no editar a mano.\n\n')
        f.write('Tipos reales de gen 1 por numero de dex. El segundo es None si la\n')
        f.write('especie tiene un solo tipo.\n"""\n\n')
        f.write('SPECIES_TYPES = {\n')
        for num in range(1, 152):
            t = out[num]
            t2 = f"'{t[1]}'" if len(t) == 2 else 'None'
            f.write(f"    {num}: ('{t[0]}', {t2}),\n")
        f.write('}\n')
    print(f'guardado {os.path.normpath(path)} - {dobles} especies con doble tipo')


if __name__ == '__main__':
    main()
