#pragma once
#include <stdint.h>
#include "i18n.h"  // gLang

// GENERADO por tools/gen_types.py desde tools/type_chart.py - no editar

#define TYPE_COUNT 15

enum : uint8_t {
  T_NORMAL, T_FIGHTING, T_FLYING, T_POISON,
  T_GROUND, T_ROCK, T_BUG, T_GHOST,
  T_FIRE, T_WATER, T_GRASS, T_ELECTRIC,
  T_PSYCHIC, T_ICE, T_DRAGON,
  T_NONE = 255,  // segundo tipo ausente
};

// En rojo/azul, fantasma contra psiquico era 0x por un fallo del juego
// original (deberia ser 2x). 0 = corregido, 1 = bug historico.
#define GEN1_GHOST_BUG 0

// Eficacia codificada: 0 = x0, 1 = x0.5, 2 = x1, 4 = x2.
// Se aplica como (dmg * TYPE_CHART[atacante][defensor]) / 2, sin floats.
static const uint8_t TYPE_CHART[TYPE_COUNT][TYPE_COUNT] = {
  { 2, 2, 2, 2, 2, 1, 2, 0, 2, 2, 2, 2, 2, 2, 2 },  // normal
  { 4, 2, 1, 1, 2, 4, 1, 0, 2, 2, 2, 2, 1, 4, 2 },  // fighting
  { 2, 4, 2, 2, 2, 1, 4, 2, 2, 2, 4, 1, 2, 2, 2 },  // flying
  { 2, 2, 2, 1, 1, 1, 4, 1, 2, 2, 4, 2, 2, 2, 2 },  // poison
  { 2, 2, 0, 4, 2, 4, 1, 2, 4, 2, 1, 4, 2, 2, 2 },  // ground
  { 2, 1, 4, 2, 1, 2, 4, 2, 4, 2, 2, 2, 2, 4, 2 },  // rock
  { 2, 1, 1, 4, 2, 2, 2, 1, 1, 2, 4, 2, 4, 2, 2 },  // bug
  { 0, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 4, 2, 2 },  // ghost
  { 2, 2, 2, 2, 2, 1, 4, 2, 1, 1, 4, 2, 2, 4, 1 },  // fire
  { 2, 2, 2, 2, 4, 4, 2, 2, 4, 1, 1, 2, 2, 2, 1 },  // water
  { 2, 2, 1, 1, 4, 4, 1, 2, 1, 4, 1, 2, 2, 2, 1 },  // grass
  { 2, 2, 4, 2, 0, 2, 2, 2, 2, 4, 1, 1, 2, 2, 1 },  // electric
  { 2, 4, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2 },  // psychic
  { 2, 2, 4, 2, 4, 2, 2, 2, 2, 1, 4, 2, 2, 1, 4 },  // ice
  { 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4 },  // dragon
};

#if GEN1_GHOST_BUG
// bug original: ghost -> psychic sin efecto
#define TYPE_MULT_RAW(a, d) \
  (((a) == T_GHOST && (d) == T_PSYCHIC) ? 0 : TYPE_CHART[a][d])
#else
#define TYPE_MULT_RAW(a, d) TYPE_CHART[a][d]
#endif

// color de acento por tipo (RGB565), para nombre y botones de ataque
static const uint16_t TYPE_ACCENT[TYPE_COUNT] = {
  0x8C4D, 0xA2A5, 0x7C58, 0x8A73,
  0xB447, 0x9407, 0x7CC4, 0x6AD3,
  0xEA87, 0x4C98, 0x3C49, 0xBCA1,
  0xD28F, 0x4DB8, 0x5A98,
};

// nombre del tipo por idioma
static const char *const TYPE_NAME_ES[TYPE_COUNT] = {
  "NORMAL", "LUCHA", "VOLADOR",
  "VENENO", "TIERRA", "ROCA",
  "BICHO", "FANTASMA", "FUEGO",
  "AGUA", "PLANTA", "ELECTRICO",
  "PSIQUICO", "HIELO", "DRAGON",
};
static const char *const TYPE_NAME_EN[TYPE_COUNT] = {
  "NORMAL", "FIGHTING", "FLYING",
  "POISON", "GROUND", "ROCK",
  "BUG", "GHOST", "FIRE",
  "WATER", "GRASS", "ELECTRIC",
  "PSYCHIC", "ICE", "DRAGON",
};
static const char *const TYPE_NAME_FR[TYPE_COUNT] = {
  "NORMAL", "COMBAT", "VOL",
  "POISON", "SOL", "ROCHE",
  "INSECTE", "SPECTRE", "FEU",
  "EAU", "PLANTE", "ELECTRIK",
  "PSY", "GLACE", "DRAGON",
};
static const char *const TYPE_NAME_DE[TYPE_COUNT] = {
  "NORMAL", "KAMPF", "FLUG",
  "GIFT", "BODEN", "GESTEIN",
  "KAEFER", "GEIST", "FEUER",
  "WASSER", "PFLANZE", "ELEKTRO",
  "PSYCHO", "EIS", "DRACHE",
};
static const char *const TYPE_NAME_IT[TYPE_COUNT] = {
  "NORMALE", "LOTTA", "VOLANTE",
  "VELENO", "TERRA", "ROCCIA",
  "COLEOTTERO", "SPETTRO", "FUOCO",
  "ACQUA", "ERBA", "ELETTRO",
  "PSICO", "GHIACCIO", "DRAGO",
};
static const char *const TYPE_NAME_PT[TYPE_COUNT] = {
  "NORMAL", "LUTADOR", "VOADOR",
  "VENENOSO", "TERRESTRE", "PEDRA",
  "INSETO", "FANTASMA", "FOGO",
  "AGUA", "PLANTA", "ELETRICO",
  "PSIQUICO", "GELO", "DRAGAO",
};

static const char *const *const TYPE_NAMES[LANG_COUNT] = {
  TYPE_NAME_ES, TYPE_NAME_EN, TYPE_NAME_FR, TYPE_NAME_DE, TYPE_NAME_IT, TYPE_NAME_PT,
};

static inline const char *typeName(uint8_t t) {
  if (t >= TYPE_COUNT) return "";
  return TYPE_NAMES[gLang][t];
}

// Multiplicador combinado contra un defensor de uno o dos tipos.
// Devuelve el numerador de una fraccion sobre 4: 0, 1, 2, 4, 8 o 16
// (x0, x0.25, x0.5, x1, x2, x4). Aplicar como (dmg * m) / 4.
static inline uint8_t typeMult(uint8_t atk, uint8_t d1, uint8_t d2) {
  if (atk >= TYPE_COUNT || d1 >= TYPE_COUNT) return 4;
  uint16_t m = TYPE_MULT_RAW(atk, d1) * 2;  // x2 -> base 4
  if (d2 < TYPE_COUNT) m = (m * TYPE_MULT_RAW(atk, d2)) / 2;
  return (uint8_t)m;
}
