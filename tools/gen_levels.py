#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera levels.h con la curva de nivel de docs/BATTLE_SPEC.md 3.2.

    LVL_REQ[n] = 60 + (n - 1) * 5     // minutos de nivel n a n+1, n = 1..99

Se toma la *forma* de la curva medium-fast, no su pendiente: la curva real
(n^3) normalizada a una hora para 1 -> 2 daria 16 anos hasta el nivel 100.
Aqui el tiempo es la moneda y no escala con el combate.

Tabla completa en flash (200 bytes), sin coma flotante en el target.
"""
import os

LEVEL_CAP = 100          # 3.2: el nivel no pasa de 100
BASE = 60                # minutos de nivel 1 a 2
STEP = 5                 # cada nivel cuesta 5 minutos mas que el anterior


def req(n):
    """Minutos de nivel n a n+1."""
    return BASE + (n - 1) * STEP


def main():
    o = []
    o.append('#pragma once\n')
    o.append('#include <stdint.h>\n\n')
    o.append('// GENERADO por tools/gen_levels.py - no editar a mano\n')
    o.append('// Curva de nivel de docs/BATTLE_SPEC.md 3.2:\n')
    o.append('//   LVL_REQ[n] = %d + (n - 1) * %d   // minutos de nivel n a n+1\n'
             % (BASE, STEP))
    o.append('// Indice 0 sin usar; validos 1..%d. El nivel no pasa de %d.\n\n'
             % (LEVEL_CAP - 1, LEVEL_CAP))
    o.append('#define LEVEL_CAP %d\n\n' % LEVEL_CAP)

    o.append('static const uint16_t LVL_REQ[%d] = {\n' % LEVEL_CAP)
    o.append('  0,  // 0: sin usar\n')
    for row in range(1, LEVEL_CAP, 10):
        vals = [req(n) for n in range(row, min(row + 10, LEVEL_CAP))]
        o.append('  %s  // %d-%d\n'
                 % (' '.join('%d,' % v for v in vals),
                    row, min(row + 9, LEVEL_CAP - 1)))
    o.append('};\n')

    path = os.path.join(os.path.dirname(__file__), '..', 'levels.h')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(o))

    total = sum(req(n) for n in range(1, LEVEL_CAP))
    print('guardado %s' % os.path.abspath(path))
    print('  nivel 1->2: %d min,  99->100: %d min' % (req(1), req(LEVEL_CAP - 1)))
    print('  total 1->%d: %d min = %.1f dias' % (LEVEL_CAP, total, total / 1440.0))
    print('  flash: %d bytes' % (2 * LEVEL_CAP))


if __name__ == '__main__':
    main()
