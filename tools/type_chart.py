# -*- coding: utf-8 -*-
"""Tabla de tipos de gen 1. FUENTE A MANO - no se genera desde PokeAPI.

PokeAPI sirve la tabla moderna (con siniestro, acero y hada), que no existia
en gen 1 y ademas cambio varias relaciones. Aqui va la de rojo/azul.

Orden de los tipos = orden del enum en types.h. No reordenar sin regenerar.
"""

# identificadores en ingles (el codigo del firmware usa ingles; los
# comentarios van en aleman, ver CLAUDE.md)
TYPES = [
    'normal', 'fighting', 'flying', 'poison', 'ground', 'rock',
    'bug', 'ghost', 'fire', 'water', 'grass', 'electric',
    'psychic', 'ice', 'dragon',
]

# color de acento por tipo (RGB hex -> el generador lo pasa a RGB565).
# Heredados de TYPE_ACCENTS en dex_data.py; 'flying' es nuevo (faltaba).
ACCENTS = {
    'normal':   '#8a8a6a',
    'fighting': '#a5552d',
    'flying':   '#7a8ac4',
    'poison':   '#8a4f9e',
    'ground':   '#b08a3d',
    'rock':     '#93803d',
    'bug':      '#7a9a24',
    'ghost':    '#6a5a9e',
    'fire':     '#e8503a',
    'water':    '#4f93c4',
    'grass':    '#3c8a4c',
    'electric': '#b8960b',
    'psychic':  '#d4527e',
    'ice':      '#4fb4c4',
    'dragon':   '#5a52c4',
}

# nombres por idioma, en el orden del enum Lang de i18n.h:
# ES, EN, FR, DE, IT, PT. Mayusculas y sin acentos (la fuente GFX es ASCII).
NAMES = {
    'normal':   ('NORMAL', 'NORMAL', 'NORMAL', 'NORMAL', 'NORMALE', 'NORMAL'),
    'fighting': ('LUCHA', 'FIGHTING', 'COMBAT', 'KAMPF', 'LOTTA', 'LUTADOR'),
    'flying':   ('VOLADOR', 'FLYING', 'VOL', 'FLUG', 'VOLANTE', 'VOADOR'),
    'poison':   ('VENENO', 'POISON', 'POISON', 'GIFT', 'VELENO', 'VENENOSO'),
    'ground':   ('TIERRA', 'GROUND', 'SOL', 'BODEN', 'TERRA', 'TERRESTRE'),
    'rock':     ('ROCA', 'ROCK', 'ROCHE', 'GESTEIN', 'ROCCIA', 'PEDRA'),
    'bug':      ('BICHO', 'BUG', 'INSECTE', 'KAEFER', 'COLEOTTERO', 'INSETO'),
    'ghost':    ('FANTASMA', 'GHOST', 'SPECTRE', 'GEIST', 'SPETTRO', 'FANTASMA'),
    'fire':     ('FUEGO', 'FIRE', 'FEU', 'FEUER', 'FUOCO', 'FOGO'),
    'water':    ('AGUA', 'WATER', 'EAU', 'WASSER', 'ACQUA', 'AGUA'),
    'grass':    ('PLANTA', 'GRASS', 'PLANTE', 'PFLANZE', 'ERBA', 'PLANTA'),
    'electric': ('ELECTRICO', 'ELECTRIC', 'ELECTRIK', 'ELEKTRO', 'ELETTRO', 'ELETRICO'),
    'psychic':  ('PSIQUICO', 'PSYCHIC', 'PSY', 'PSYCHO', 'PSICO', 'PSIQUICO'),
    'ice':      ('HIELO', 'ICE', 'GLACE', 'EIS', 'GHIACCIO', 'GELO'),
    'dragon':   ('DRAGON', 'DRAGON', 'DRAGON', 'DRACHE', 'DRAGO', 'DRAGAO'),
}

# Solo las desviaciones de 1x. Todo lo no listado es neutro.
# 2.0 = muy eficaz, 0.5 = poco eficaz, 0.0 = sin efecto.
CHART = {
    'normal':   {'rock': 0.5, 'ghost': 0.0},
    'fighting': {'normal': 2.0, 'rock': 2.0, 'ice': 2.0,
                 'flying': 0.5, 'poison': 0.5, 'bug': 0.5, 'psychic': 0.5,
                 'ghost': 0.0},
    'flying':   {'fighting': 2.0, 'bug': 2.0, 'grass': 2.0,
                 'rock': 0.5, 'electric': 0.5},
    'poison':   {'bug': 2.0, 'grass': 2.0,
                 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5},
    'ground':   {'poison': 2.0, 'rock': 2.0, 'fire': 2.0, 'electric': 2.0,
                 'bug': 0.5, 'grass': 0.5, 'flying': 0.0},
    'rock':     {'flying': 2.0, 'bug': 2.0, 'fire': 2.0, 'ice': 2.0,
                 'fighting': 0.5, 'ground': 0.5},
    'bug':      {'poison': 2.0, 'grass': 2.0, 'psychic': 2.0,
                 'fighting': 0.5, 'flying': 0.5, 'ghost': 0.5, 'fire': 0.5},
    'ghost':    {'ghost': 2.0, 'psychic': 2.0, 'normal': 0.0},
    'fire':     {'bug': 2.0, 'grass': 2.0, 'ice': 2.0,
                 'rock': 0.5, 'fire': 0.5, 'water': 0.5, 'dragon': 0.5},
    'water':    {'ground': 2.0, 'rock': 2.0, 'fire': 2.0,
                 'water': 0.5, 'grass': 0.5, 'dragon': 0.5},
    'grass':    {'ground': 2.0, 'rock': 2.0, 'water': 2.0,
                 'flying': 0.5, 'poison': 0.5, 'bug': 0.5, 'fire': 0.5,
                 'grass': 0.5, 'dragon': 0.5},
    'electric': {'flying': 2.0, 'water': 2.0,
                 'grass': 0.5, 'electric': 0.5, 'dragon': 0.5, 'ground': 0.0},
    'psychic':  {'fighting': 2.0, 'poison': 2.0, 'psychic': 0.5},
    'ice':      {'flying': 2.0, 'ground': 2.0, 'grass': 2.0, 'dragon': 2.0,
                 'water': 0.5, 'ice': 0.5},
    'dragon':   {'dragon': 2.0},
}

# En rojo/azul, fantasma contra psiquico era 0x por un fallo de programacion
# (deberia ser 2x). Arriba esta la version corregida; types.h expone
# GEN1_GHOST_BUG para volver al comportamiento original.
GHOST_BUG_OVERRIDE = ('ghost', 'psychic', 0.0)

# mapa del tipo espanol de dex_data.py al identificador ingles
ES_TO_EN = {
    'normal': 'normal', 'lucha': 'fighting', 'veneno': 'poison',
    'tierra': 'ground', 'roca': 'rock', 'bicho': 'bug',
    'fantasma': 'ghost', 'fuego': 'fire', 'agua': 'water',
    'planta': 'grass', 'electrico': 'electric', 'psiquico': 'psychic',
    'hielo': 'ice', 'dragon': 'dragon',
}
