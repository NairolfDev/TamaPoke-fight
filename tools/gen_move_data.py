#!/usr/bin/env python3
"""Baja de PokeAPI los ataques de gen 1 y escribe move_data.py + move_names.py.

  python3 tools/gen_move_data.py

Se queda con los ataques por subida de nivel de rojo/azul. De los 165 de gen 1
solo entran los utiles para un combate de cuatro huecos: potencia >= 40, mas
una lista corta de ataques de estado. Si a una especie le quedan menos de
cuatro, se le devuelven los suyos mas potentes aunque no lleguen al corte.

Cache en tools/.pokeapi/ (compartida con gen_type_data.py).
"""
import concurrent.futures
import json
import os
import sys
import unicodedata
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from type_chart import TYPES

CACHE = os.path.join(os.path.dirname(__file__), '.pokeapi')
VERSION_GROUP = 'red-blue'
POWER_MIN = 40

# idiomas de PokeAPI por indice de Lang (i18n.h). PT no existe alli -> ingles.
LANG_API = ('es', 'en', 'fr', 'de', 'it', None)

# efecto -> ataques. IDs segun docs/BATTLE_SPEC.md seccion 5.2.
EFFECTS = {
    1: ('body-slam', 'thunder-shock', 'thunderbolt', 'thunder', 'lick',
        'thunder-punch', 'thunder-wave'),
    2: ('ember', 'flamethrower', 'fire-blast', 'fire-punch', 'fire-spin'),
    3: ('poison-sting', 'sludge', 'smog', 'twineedle'),
    4: ('slash', 'razor-leaf', 'crabhammer', 'karate-chop'),
    5: ('double-slap', 'comet-punch', 'fury-attack', 'pin-missile', 'barrage',
        'fury-swipes', 'spike-cannon', 'double-kick', 'bonemerang'),
    6: ('absorb', 'mega-drain', 'leech-life'),
    7: ('screech',),
    8: ('swords-dance',),
}
MOVE_EFFECT = {mv: eid for eid, movs in EFFECTS.items() for mv in movs}

# unicos ataques sin dano que entran (los demas gastarian hueco para nada)
STATUS_KEEP = ('swords-dance', 'screech')

# Safcon, Kokuna, Abra y Ditto no aprenden NINGUN ataque con dano en gen 1
# (Endura, Teleport, Wandler). El juego original ya tiene la respuesta:
# Verzweifler, que se usa cuando no queda nada. Entra siempre, aunque no
# este en ningun movepool, y el motor lo usa como ultimo recurso.
ALWAYS = ('struggle',)

# En gen 1 estos hacen dano fijo, asi que PokeAPI los da con potencia 0 y se
# caerian del corte. Sin ellos, dragon se queda SIN NINGUN ataque y fantasma
# con uno solo. Se aproximan con una potencia normal del nivel que les toca:
# el motor no tiene dano fijo y tampoco lo necesita.
POWER_OVERRIDE = {
    'dragon-rage': 40,   # gen 1: 40 puntos clavados
    'night-shade': 50,   # gen 1: dano = nivel del atacante
    'seismic-toss': 50,  # idem
    'psywave': 40,       # gen 1: dano aleatorio segun nivel
}

GEN_ORDER = ['generation-i', 'generation-ii', 'generation-iii', 'generation-iv',
             'generation-v', 'generation-vi', 'generation-vii', 'generation-viii',
             'generation-ix']


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


def ascii_up(s):
    s = s.replace('♀', 'F').replace('♂', 'M')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.upper()


def machines(num):
    """Ataques de MT/MO de rojo/azul. Solo se usan como red de seguridad."""
    d = fetch(f'https://pokeapi.co/api/v2/pokemon/{num}/', f'mon{num}')
    out = set()
    for m in d['moves']:
        for v in m['version_group_details']:
            if (v['version_group']['name'] == VERSION_GROUP
                    and v['move_learn_method']['name'] == 'machine'):
                out.add(m['move']['name'])
    return out


def learnset(num):
    """[(nivel, slug_ataque)] de rojo/azul, ordenado y sin repetidos."""
    d = fetch(f'https://pokeapi.co/api/v2/pokemon/{num}/', f'mon{num}')
    vistos, res = {}, []
    for m in d['moves']:
        slug = m['move']['name']
        for v in m['version_group_details']:
            if (v['version_group']['name'] == VERSION_GROUP
                    and v['move_learn_method']['name'] == 'level-up'):
                lv = v['level_learned_at']
                if slug not in vistos or lv < vistos[slug]:
                    vistos[slug] = lv
    for slug, lv in vistos.items():
        res.append((max(1, lv), slug))
    res.sort()
    return num, res


def movedata(slug):
    """Valores de gen 1: PokeAPI sirve los actuales y los viejos en past_values."""
    d = fetch(f'https://pokeapi.co/api/v2/move/{slug}/', 'mv_' + slug)
    tipo, power = d['type']['name'], d['power']
    acc, pp = d['accuracy'], d['pp']
    pasados = [p for p in (d.get('past_values') or [])
               if p['version_group']['name'] in ('red-blue', 'gold-silver',
                                                 'ruby-sapphire', 'diamond-pearl',
                                                 'black-white', 'x-y')]
    if pasados:
        pasados.sort(key=lambda p: GEN_ORDER.index(
            {'red-blue': 'generation-i', 'gold-silver': 'generation-ii',
             'ruby-sapphire': 'generation-iii', 'diamond-pearl': 'generation-iv',
             'black-white': 'generation-v', 'x-y': 'generation-vi'}[
                p['version_group']['name']]))
        v = pasados[0]
        if v.get('power') is not None:
            power = v['power']
        if v.get('accuracy') is not None:
            acc = v['accuracy']
        if v.get('pp') is not None:
            pp = v['pp']
        if v.get('type'):
            tipo = v['type']['name']
    if slug in POWER_OVERRIDE:
        power = POWER_OVERRIDE[slug]
    nombres = {n['language']['name']: n['name'] for n in d['names']}
    loc = []
    for code in LANG_API:
        raw = nombres.get(code) if code else None
        loc.append(ascii_up(raw or nombres.get('en', slug)))
    return {'slug': slug, 'type': tipo, 'power': power or 0,
            'accuracy': acc or 100, 'pp': pp or 20,
            'effect': MOVE_EFFECT.get(slug, 0), 'names': loc}


def main():
    print('bajando movepools...')
    learns = {}
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for num, ls in ex.map(learnset, range(1, 152)):
            learns[num] = ls

    mts = set()
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for m in ex.map(machines, range(1, 152)):
            mts |= m
    slugs = sorted({s for ls in learns.values() for _, s in ls} | set(ALWAYS) | mts)
    print(f'{len(slugs)} ataques distintos en los movepools de rojo/azul')

    print('bajando datos de ataque...')
    info = {}
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for d in ex.map(movedata, slugs):
            if d['type'] not in TYPES:
                raise SystemExit(f"tipo raro en {d['slug']}: {d['type']}")
            info[d['slug']] = d

    # Red de seguridad STAB: quien no aprende por nivel ningun ataque de su
    # propio tipo (Voltobal, Sandan, Enton...) se queda peleando solo con
    # ataques normales. En una partida real eso se arregla con una MT, asi que
    # se le regala la mejor MT de su tipo al nivel 1.
    from type_data import SPECIES_TYPES
    regalos = 0
    for num in range(1, 152):
        t1, t2 = SPECIES_TYPES[num]
        propios = [s2 for _, s2 in learns[num]
                   if info[s2]['power'] > 0 and info[s2]['type'] in (t1, t2)]
        if propios:
            continue
        cand = [m for m in machines(num)
                if m in info and info[m]['power'] > 0 and info[m]['type'] in (t1, t2)]
        if not cand:
            continue  # gen 1 no tiene MT de bicho: no hay nada que hacer
        mejor = max(cand, key=lambda m: info[m]['power'])
        learns[num].insert(0, (1, mejor))
        regalos += 1
    print(f'{regalos} especies reciben una MT de su tipo por falta de STAB')

    # corte principal
    keep = {s for s, d in info.items()
            if (d['power'] >= POWER_MIN or s in STATUS_KEEP or s in ALWAYS)}

    # garantia: nadie se queda con menos de 4 ataques disponibles
    rescatados = 0
    for num, ls in learns.items():
        propios = [s for _, s in ls if s in keep]
        if len(propios) >= 4:
            continue
        extra = sorted((s for _, s in ls if s not in keep),
                       key=lambda s: -info[s]['power'])
        for s in extra:
            if info[s]['power'] <= 0:
                continue
            keep.add(s)
            rescatados += 1
            propios.append(s)
            if len(propios) >= 4:
                break
    print(f'{len(keep)} ataques tras el corte ({rescatados} rescatados por cobertura)')

    resto = sorted(keep - set(ALWAYS),
                   key=lambda s: (info[s]['type'], -info[s]['power'], s))
    orden = list(ALWAYS) + resto  # Verzweifler siempre el id 1
    ids = {s: i + 1 for i, s in enumerate(orden)}  # 0 = hueco vacio

    cobertura = {}
    for s in orden:
        cobertura.setdefault(info[s]['type'], 0)
        cobertura[info[s]['type']] += 1
    faltan = [t for t in TYPES if cobertura.get(t, 0) == 0]
    print('cobertura por tipo: ' + ', '.join(
        f'{t}={cobertura.get(t, 0)}' for t in TYPES))
    if faltan:
        print('AVISO: tipos sin ningun ataque: ' + ', '.join(faltan))

    from dex_data import DEX
    prevo = {d[4]: d[0] for d in DEX if d[4]}
    prevo[135] = 133; prevo[136] = 133  # ramas de Eevee

    base = os.path.dirname(__file__)
    with open(os.path.join(base, 'move_data.py'), 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""GENERADO por tools/gen_move_data.py desde PokeAPI - no editar a mano.\n\n')
        f.write('MOVES: id -> (slug, tipo, potencia, precision, ap, efecto)\n')
        f.write('LEARNSETS: dex -> [(nivel, id_ataque)] de rojo/azul, ordenado.\n"""\n\n')
        f.write('MOVES = {\n')
        for s in orden:
            d = info[s]
            f.write(f"    {ids[s]}: ('{s}', '{d['type']}', {d['power']}, "
                    f"{d['accuracy']}, {d['pp']}, {d['effect']}),\n")
        f.write('}\n\nLEARNSETS = {\n')
        for num in range(1, 152):
            pares = [(lv, ids[s]) for lv, s in learns[num] if s in ids]
            pares.sort()
            f.write(f'    {num}: {pares},\n')
        f.write('}\n\nPREVO = {\n')
        for num in range(1, 152):
            f.write(f'    {num}: {prevo.get(num, 0)},\n')
        f.write('}\n')

    with open(os.path.join(base, 'move_names.py'), 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""GENERADO por tools/gen_move_data.py desde PokeAPI - no editar a mano.\n\n')
        f.write('Nombre oficial por idioma, en el orden de Lang (ES, EN, FR, DE, IT, PT).\n')
        f.write('PT no existe en PokeAPI, asi que repite el ingles. Mayusculas y sin\n')
        f.write('acentos porque la fuente GFX es ASCII.\n"""\n\n')
        f.write('MOVE_NAMES = {\n')
        for s in orden:
            f.write(f"    {ids[s]}: {tuple(info[s]['names'])!r},\n")
        f.write('}\n')

    print(f'guardado move_data.py y move_names.py ({len(orden)} ataques)')


if __name__ == '__main__':
    main()
