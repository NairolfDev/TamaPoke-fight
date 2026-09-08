#pragma once
#include <stdint.h>
#include "i18n.h"  // gLang
#include "types.h"

// GENERADO por tools/gen_moves.py desde tools/move_data.py - no editar

#define MOVE_COUNT 103
#define MOVE_SLOTS 4  // huecos de ataque por bicho
#define MOVE_STRUGGLE 1  // ultimo recurso: sin AP o sin movepool

// efecto: 0 ninguno | 1 paralisis 10% | 2 quemadura 10% | 3 veneno 30%
// 4 mas criticos | 5 golpes multiples | 6 drena 50% | 7 baja DEF rival
// 8 sube ATK propio. Ver docs/BATTLE_SPEC.md 5.2.
struct Move {
  uint8_t type;
  uint8_t power;      // 0 = ataque de estado
  uint8_t accuracy;   // 0-100
  uint8_t maxPp;
  uint8_t effect;
};

static const Move MOVE_TBL[MOVE_COUNT + 1] = {
  { T_NORMAL, 0, 0, 0, 0 },  // 0: hueco vacio
  { T_NORMAL, 50, 100, 1, 0 },  // 1 struggle
  { T_BUG, 80, 100, 10, 6 },  // 2 leech-life
  { T_BUG, 25, 100, 20, 3 },  // 3 twineedle
  { T_BUG, 14, 85, 20, 5 },  // 4 pin-missile
  { T_DRAGON, 40, 100, 10, 0 },  // 5 dragon-rage
  { T_ELECTRIC, 110, 70, 10, 1 },  // 6 thunder
  { T_ELECTRIC, 95, 100, 15, 1 },  // 7 thunderbolt
  { T_ELECTRIC, 75, 100, 15, 1 },  // 8 thunder-punch
  { T_ELECTRIC, 40, 100, 30, 1 },  // 9 thunder-shock
  { T_FIGHTING, 85, 90, 10, 0 },  // 10 high-jump-kick
  { T_FIGHTING, 80, 80, 25, 0 },  // 11 submission
  { T_FIGHTING, 70, 95, 10, 0 },  // 12 jump-kick
  { T_FIGHTING, 60, 85, 15, 0 },  // 13 rolling-kick
  { T_FIGHTING, 50, 90, 20, 0 },  // 14 low-kick
  { T_FIGHTING, 50, 100, 20, 0 },  // 15 seismic-toss
  { T_FIRE, 110, 85, 5, 2 },  // 16 fire-blast
  { T_FIRE, 95, 100, 15, 2 },  // 17 flamethrower
  { T_FIRE, 75, 100, 15, 2 },  // 18 fire-punch
  { T_FIRE, 40, 100, 25, 2 },  // 19 ember
  { T_FIRE, 15, 70, 15, 2 },  // 20 fire-spin
  { T_FLYING, 140, 90, 5, 0 },  // 21 sky-attack
  { T_FLYING, 80, 100, 20, 0 },  // 22 drill-peck
  { T_FLYING, 70, 95, 15, 0 },  // 23 fly
  { T_FLYING, 35, 100, 35, 0 },  // 24 peck
  { T_FLYING, 35, 100, 35, 0 },  // 25 wing-attack
  { T_GHOST, 50, 100, 15, 0 },  // 26 night-shade
  { T_GHOST, 20, 100, 30, 1 },  // 27 lick
  { T_GRASS, 120, 100, 10, 0 },  // 28 solar-beam
  { T_GRASS, 70, 100, 10, 0 },  // 29 petal-dance
  { T_GRASS, 55, 95, 25, 4 },  // 30 razor-leaf
  { T_GRASS, 45, 100, 10, 0 },  // 31 vine-whip
  { T_GRASS, 40, 100, 10, 6 },  // 32 mega-drain
  { T_GRASS, 20, 100, 20, 6 },  // 33 absorb
  { T_GROUND, 100, 100, 10, 0 },  // 34 dig
  { T_GROUND, 100, 100, 10, 0 },  // 35 earthquake
  { T_GROUND, 65, 85, 20, 0 },  // 36 bone-club
  { T_GROUND, 50, 90, 10, 5 },  // 37 bonemerang
  { T_ICE, 110, 90, 5, 0 },  // 38 blizzard
  { T_ICE, 95, 100, 10, 0 },  // 39 ice-beam
  { T_ICE, 75, 100, 15, 0 },  // 40 ice-punch
  { T_ICE, 65, 100, 20, 0 },  // 41 aurora-beam
  { T_NORMAL, 170, 100, 5, 0 },  // 42 explosion
  { T_NORMAL, 150, 90, 5, 0 },  // 43 hyper-beam
  { T_NORMAL, 130, 100, 5, 0 },  // 44 self-destruct
  { T_NORMAL, 120, 75, 5, 0 },  // 45 mega-kick
  { T_NORMAL, 100, 100, 15, 0 },  // 46 double-edge
  { T_NORMAL, 100, 75, 10, 0 },  // 47 egg-bomb
  { T_NORMAL, 100, 100, 15, 0 },  // 48 skull-bash
  { T_NORMAL, 90, 85, 20, 0 },  // 49 take-down
  { T_NORMAL, 90, 100, 20, 0 },  // 50 thrash
  { T_NORMAL, 85, 100, 15, 1 },  // 51 body-slam
  { T_NORMAL, 80, 90, 15, 0 },  // 52 hyper-fang
  { T_NORMAL, 80, 85, 20, 0 },  // 53 mega-punch
  { T_NORMAL, 80, 75, 10, 0 },  // 54 razor-wind
  { T_NORMAL, 80, 75, 20, 0 },  // 55 slam
  { T_NORMAL, 80, 100, 15, 0 },  // 56 strength
  { T_NORMAL, 80, 100, 10, 0 },  // 57 tri-attack
  { T_NORMAL, 70, 100, 10, 0 },  // 58 dizzy-punch
  { T_NORMAL, 70, 100, 15, 0 },  // 59 headbutt
  { T_NORMAL, 70, 100, 20, 4 },  // 60 slash
  { T_NORMAL, 65, 100, 25, 0 },  // 61 horn-attack
  { T_NORMAL, 65, 100, 20, 0 },  // 62 stomp
  { T_NORMAL, 60, 100, 25, 0 },  // 63 bite
  { T_NORMAL, 60, 100, 20, 0 },  // 64 swift
  { T_NORMAL, 55, 100, 30, 0 },  // 65 vice-grip
  { T_NORMAL, 50, 95, 30, 0 },  // 66 cut
  { T_NORMAL, 50, 100, 25, 4 },  // 67 karate-chop
  { T_NORMAL, 40, 100, 35, 0 },  // 68 gust
  { T_NORMAL, 40, 100, 20, 0 },  // 69 pay-day
  { T_NORMAL, 40, 100, 35, 0 },  // 70 pound
  { T_NORMAL, 40, 100, 30, 0 },  // 71 quick-attack
  { T_NORMAL, 40, 100, 35, 0 },  // 72 scratch
  { T_NORMAL, 35, 95, 35, 0 },  // 73 tackle
  { T_NORMAL, 20, 100, 20, 0 },  // 74 rage
  { T_NORMAL, 20, 100, 15, 5 },  // 75 spike-cannon
  { T_NORMAL, 18, 80, 15, 5 },  // 76 fury-swipes
  { T_NORMAL, 15, 85, 20, 5 },  // 77 barrage
  { T_NORMAL, 15, 75, 20, 0 },  // 78 bind
  { T_NORMAL, 15, 85, 10, 5 },  // 79 double-slap
  { T_NORMAL, 15, 85, 20, 5 },  // 80 fury-attack
  { T_NORMAL, 15, 85, 20, 0 },  // 81 wrap
  { T_NORMAL, 10, 100, 35, 0 },  // 82 constrict
  { T_NORMAL, 0, 85, 40, 7 },  // 83 screech
  { T_NORMAL, 0, 100, 30, 8 },  // 84 swords-dance
  { T_POISON, 65, 100, 20, 3 },  // 85 sludge
  { T_POISON, 40, 100, 30, 0 },  // 86 acid
  { T_POISON, 20, 70, 20, 3 },  // 87 smog
  { T_POISON, 15, 100, 35, 3 },  // 88 poison-sting
  { T_PSYCHIC, 100, 100, 15, 0 },  // 89 dream-eater
  { T_PSYCHIC, 90, 100, 10, 0 },  // 90 psychic
  { T_PSYCHIC, 65, 100, 20, 0 },  // 91 psybeam
  { T_PSYCHIC, 50, 100, 25, 0 },  // 92 confusion
  { T_PSYCHIC, 40, 80, 15, 0 },  // 93 psywave
  { T_ROCK, 75, 90, 10, 0 },  // 94 rock-slide
  { T_ROCK, 50, 65, 15, 0 },  // 95 rock-throw
  { T_WATER, 120, 80, 5, 0 },  // 96 hydro-pump
  { T_WATER, 100, 85, 10, 4 },  // 97 crabhammer
  { T_WATER, 95, 100, 15, 0 },  // 98 surf
  { T_WATER, 80, 100, 15, 0 },  // 99 waterfall
  { T_WATER, 65, 100, 20, 0 },  // 100 bubble-beam
  { T_WATER, 40, 100, 25, 0 },  // 101 water-gun
  { T_WATER, 35, 75, 10, 0 },  // 102 clamp
  { T_WATER, 20, 100, 30, 0 },  // 103 bubble
};

static const char *const MOVE_NAME_ES[MOVE_COUNT + 1] = {
  "",
  "FORCEJEO",
  "CHUPAVIDAS",
  "DOBLE ATAQUE",
  "PIN MISIL",
  "FURIA DRAGON",
  "TRUENO",
  "RAYO",
  "PUNO TRUENO",
  "IMPACTRUENO",
  "PATADA SALTO ALTA",
  "SUMISION",
  "PATADA SALTO",
  "PATADA GIRO",
  "PATADA BAJA",
  "SISMICO",
  "LLAMARADA",
  "LANZALLAMAS",
  "PUNO FUEGO",
  "ASCUAS",
  "GIRO FUEGO",
  "ATAQUE AEREO",
  "PICO TALADRO",
  "VUELO",
  "PICOTAZO",
  "ATAQUE ALA",
  "TINIEBLAS",
  "LENGUETAZO",
  "RAYO SOLAR",
  "DANZA PETALO",
  "HOJA AFILADA",
  "LATIGO CEPA",
  "MEGAAGOTAR",
  "ABSORBER",
  "EXCAVAR",
  "TERREMOTO",
  "HUESO PALO",
  "HUESOMERANG",
  "VENTISCA",
  "RAYO HIELO",
  "PUNO HIELO",
  "RAYO AURORA",
  "EXPLOSION",
  "HIPERRAYO",
  "AUTODESTRUCCION",
  "MEGAPATADA",
  "DOBLE FILO",
  "BOMBA HUEVO",
  "CABEZAZO",
  "DERRIBO",
  "SANA",
  "GOLPE CUERPO",
  "HIPERCOLMILLO",
  "MEGAPUNO",
  "VIENTO CORTANTE",
  "ATIZAR",
  "FUERZA",
  "TRIATAQUE",
  "PUNO MAREO",
  "GOLPE CABEZA",
  "CUCHILLADA",
  "CORNADA",
  "PISOTON",
  "MORDISCO",
  "METEOROS",
  "AGARRE",
  "CORTE",
  "GOLPE KARATE",
  "TORNADO",
  "DIA DE PAGO",
  "DESTRUCTOR",
  "ATAQUE RAPIDO",
  "ARANAZO",
  "PLACAJE",
  "FURIA",
  "CLAVO CANON",
  "GOLPES FURIA",
  "BOMBARDEO",
  "ATADURA",
  "DOBLE BOFETON",
  "ATAQUE FURIA",
  "CONSTRICCION",
  "RESTRICCION",
  "CHIRRIDO",
  "DANZA ESPADA",
  "RESIDUOS",
  "ACIDO",
  "POLUCION",
  "PICOTAZO VENENO",
  "COMESUENOS",
  "PSIQUICO",
  "PSICORRAYO",
  "CONFUSION",
  "PSICOONDA",
  "AVALANCHA",
  "LANZARROCAS",
  "HIDROBOMBA",
  "MARTILLAZO",
  "SURF",
  "CASCADA",
  "RAYO BURBUJA",
  "PISTOLA AGUA",
  "TENAZA",
  "BURBUJA",
};
static const char *const MOVE_NAME_EN[MOVE_COUNT + 1] = {
  "",
  "STRUGGLE",
  "LEECH LIFE",
  "TWINEEDLE",
  "PIN MISSILE",
  "DRAGON RAGE",
  "THUNDER",
  "THUNDERBOLT",
  "THUNDER PUNCH",
  "THUNDER SHOCK",
  "HIGH JUMP KICK",
  "SUBMISSION",
  "JUMP KICK",
  "ROLLING KICK",
  "LOW KICK",
  "SEISMIC TOSS",
  "FIRE BLAST",
  "FLAMETHROWER",
  "FIRE PUNCH",
  "EMBER",
  "FIRE SPIN",
  "SKY ATTACK",
  "DRILL PECK",
  "FLY",
  "PECK",
  "WING ATTACK",
  "NIGHT SHADE",
  "LICK",
  "SOLAR BEAM",
  "PETAL DANCE",
  "RAZOR LEAF",
  "VINE WHIP",
  "MEGA DRAIN",
  "ABSORB",
  "DIG",
  "EARTHQUAKE",
  "BONE CLUB",
  "BONEMERANG",
  "BLIZZARD",
  "ICE BEAM",
  "ICE PUNCH",
  "AURORA BEAM",
  "EXPLOSION",
  "HYPER BEAM",
  "SELF-DESTRUCT",
  "MEGA KICK",
  "DOUBLE-EDGE",
  "EGG BOMB",
  "SKULL BASH",
  "TAKE DOWN",
  "THRASH",
  "BODY SLAM",
  "HYPER FANG",
  "MEGA PUNCH",
  "RAZOR WIND",
  "SLAM",
  "STRENGTH",
  "TRI ATTACK",
  "DIZZY PUNCH",
  "HEADBUTT",
  "SLASH",
  "HORN ATTACK",
  "STOMP",
  "BITE",
  "SWIFT",
  "VISE GRIP",
  "CUT",
  "KARATE CHOP",
  "GUST",
  "PAY DAY",
  "POUND",
  "QUICK ATTACK",
  "SCRATCH",
  "TACKLE",
  "RAGE",
  "SPIKE CANNON",
  "FURY SWIPES",
  "BARRAGE",
  "BIND",
  "DOUBLE SLAP",
  "FURY ATTACK",
  "WRAP",
  "CONSTRICT",
  "SCREECH",
  "SWORDS DANCE",
  "SLUDGE",
  "ACID",
  "SMOG",
  "POISON STING",
  "DREAM EATER",
  "PSYCHIC",
  "PSYBEAM",
  "CONFUSION",
  "PSYWAVE",
  "ROCK SLIDE",
  "ROCK THROW",
  "HYDRO PUMP",
  "CRABHAMMER",
  "SURF",
  "WATERFALL",
  "BUBBLE BEAM",
  "WATER GUN",
  "CLAMP",
  "BUBBLE",
};
static const char *const MOVE_NAME_FR[MOVE_COUNT + 1] = {
  "",
  "LUTTE",
  "VAMPIRISME",
  "DOUBLE DARD",
  "DARD-NUEE",
  "DRACO-RAGE",
  "FATAL-FOUDRE",
  "TONNERRE",
  "POING ECLAIR",
  "ECLAIR",
  "PIED VOLTIGE",
  "SACRIFICE",
  "PIED SAUTE",
  "MAWASHI GERI",
  "BALAYAGE",
  "FRAPPE ATLAS",
  "DEFLAGRATION",
  "LANCE-FLAMMES",
  "POING FEU",
  "FLAMMECHE",
  "DANSE FLAMMES",
  "PIQUE",
  "BEC VRILLE",
  "VOL",
  "PICPIC",
  "CRU-AILES",
  "OMBRE NOCTURNE",
  "LECHOUILLE",
  "LANCE-SOLEIL",
  "DANSE FLEURS",
  "TRANCH’HERBE",
  "FOUET LIANES",
  "MEGA-SANGSUE",
  "VOLE-VIE",
  "TUNNEL",
  "SEISME",
  "MASSD’OS",
  "OSMERANG",
  "BLIZZARD",
  "LASER GLACE",
  "POING GLACE",
  "ONDE BOREALE",
  "EXPLOSION",
  "ULTRALASER",
  "DESTRUCTION",
  "ULTIMAWASHI",
  "DAMOCLES",
  "BOMBE ŒUF",
  "COUD’KRANE",
  "BELIER",
  "MANIA",
  "PLAQUAGE",
  "CROC DE MORT",
  "ULTIMAPOING",
  "COUPE-VENT",
  "SOUPLESSE",
  "FORCE",
  "TRIPLATTAQUE",
  "UPPERCUT",
  "COUP D’BOULE",
  "TRANCHE",
  "KOUD’KORNE",
  "ECRASEMENT",
  "MORSURE",
  "METEORES",
  "FORCE POIGNE",
  "COUPE",
  "POING KARATE",
  "TORNADE",
  "JACKPOT",
  "ECRAS’FACE",
  "VIVE-ATTAQUE",
  "GRIFFE",
  "CHARGE",
  "FRENESIE",
  "PICANON",
  "COMBO-GRIFFE",
  "PILONNAGE",
  "ETREINTE",
  "TORGNOLES",
  "FURIE",
  "LIGOTAGE",
  "CONSTRICTION",
  "GRINCEMENT",
  "DANSE LAMES",
  "DETRITUS",
  "ACIDE",
  "PUREDPOIS",
  "DARD-VENIN",
  "DEVOREVE",
  "PSYKO",
  "RAFALE PSY",
  "CHOC MENTAL",
  "VAGUE PSY",
  "EBOULEMENT",
  "JET-PIERRES",
  "HYDROCANON",
  "PINCE-MASSE",
  "SURF",
  "CASCADE",
  "BULLES D’O",
  "PISTOLET A O",
  "CLAQUOIR",
  "ECUME",
};
static const char *const MOVE_NAME_DE[MOVE_COUNT + 1] = {
  "",
  "VERZWEIFLER",
  "BLUTSAUGER",
  "DUONADEL",
  "NADELRAKETE",
  "DRACHENWUT",
  "DONNER",
  "DONNERBLITZ",
  "DONNERSCHLAG",
  "DONNERSCHOCK",
  "TURMKICK",
  "UBERROLLER",
  "SPRUNGKICK",
  "FEGEKICK",
  "FUSSKICK",
  "GEOWURF",
  "FEUERSTURM",
  "FLAMMENWURF",
  "FEUERSCHLAG",
  "GLUT",
  "FEUERWIRBEL",
  "HIMMELSFEGER",
  "BOHRSCHNABEL",
  "FLIEGEN",
  "PIKSER",
  "FLUGELSCHLAG",
  "NACHTNEBEL",
  "SCHLECKER",
  "SOLARSTRAHL",
  "BLATTERTANZ",
  "RASIERBLATT",
  "RANKENHIEB",
  "MEGASAUGER",
  "ABSORBER",
  "SCHAUFLER",
  "ERDBEBEN",
  "KNOCHENKEULE",
  "KNOCHMERANG",
  "BLIZZARD",
  "EISSTRAHL",
  "EISHIEB",
  "AURORASTRAHL",
  "EXPLOSION",
  "HYPERSTRAHL",
  "FINALE",
  "MEGAKICK",
  "RISIKOTACKLE",
  "EIERBOMBE",
  "SCHADELWUMME",
  "BODYCHECK",
  "FUCHTLER",
  "BODYSLAM",
  "HYPERZAHN",
  "MEGAHIEB",
  "KLINGENSTURM",
  "SLAM",
  "STARKE",
  "TRIPLETTE",
  "IRRSCHLAG",
  "KOPFNUSS",
  "SCHLITZER",
  "HORNATTACKE",
  "STAMPFER",
  "BISS",
  "STERNSCHAUER",
  "KLAMMER",
  "ZERSCHNEIDER",
  "KARATESCHLAG",
  "WINDSTOSS",
  "ZAHLTAG",
  "KLAPS",
  "RUCKZUCKHIEB",
  "KRATZER",
  "TACKLE",
  "RASEREI",
  "DORNKANONE",
  "KRATZFURIE",
  "STAKKATO",
  "KLAMMERGRIFF",
  "DUPLEXHIEB",
  "FURIENSCHLAG",
  "WICKEL",
  "UMKLAMMERUNG",
  "KREIDESCHREI",
  "SCHWERTTANZ",
  "SCHLAMMBAD",
  "SAURE",
  "SMOG",
  "GIFTSTACHEL",
  "TRAUMFRESSER",
  "PSYCHOKINESE",
  "PSYSTRAHL",
  "KONFUSION",
  "PSYWELLE",
  "STEINHAGEL",
  "STEINWURF",
  "HYDROPUMPE",
  "KRABBHAMMER",
  "SURFER",
  "KASKADE",
  "BLUBBSTRAHL",
  "AQUAKNARRE",
  "SCHNAPPER",
  "BLUBBER",
};
static const char *const MOVE_NAME_IT[MOVE_COUNT + 1] = {
  "",
  "SCONTRO",
  "SANGUISUGA",
  "DOPPIO AGO",
  "MISSILSPILLO",
  "IRA DI DRAGO",
  "TUONO",
  "FULMINE",
  "TUONOPUGNO",
  "TUONOSHOCK",
  "CALCINVOLO",
  "SOTTOMISSIONE",
  "CALCIOSALTO",
  "CALCIORULLO",
  "COLPO BASSO",
  "MOVIM. SISMICO",
  "FUOCOBOMBA",
  "LANCIAFIAMME",
  "FUOCOPUGNO",
  "BRACIERE",
  "TURBOFUOCO",
  "AEROATTACCO",
  "PERFORBECCO",
  "VOLO",
  "BECCATA",
  "ATTACCO D’ALA",
  "OMBRA NOTTURNA",
  "LECCATA",
  "SOLARRAGGIO",
  "PETALODANZA",
  "FOGLIELAMA",
  "FRUSTATA",
  "MEGASSORBIMENTO",
  "ASSORBIMENTO",
  "FOSSA",
  "TERREMOTO",
  "OSSOCLAVA",
  "OSSOMERANG",
  "BORA",
  "GELORAGGIO",
  "GELOPUGNO",
  "RAGGIAURORA",
  "ESPLOSIONE",
  "IPER RAGGIO",
  "AUTODISTRUZIONE",
  "MEGACALCIO",
  "SDOPPIATORE",
  "UOVOBOMBA",
  "CAPOCCIATA",
  "RIDUTTORE",
  "COLPO",
  "CORPOSCONTRO",
  "IPERZANNA",
  "MEGAPUGNO",
  "VENTAGLIENTE",
  "SCHIANTO",
  "FORZA",
  "TRIPLETTA",
  "STORDIPUGNO",
  "BOTTINTESTA",
  "LACERAZIONE",
  "INCORNATA",
  "PESTONE",
  "MORSO",
  "COMETE",
  "PRESA",
  "TAGLIO",
  "COLPOKARATE",
  "RAFFICA",
  "GIORNOPAGA",
  "BOTTA",
  "ATTACCO RAPIDO",
  "GRAFFIO",
  "AZIONE",
  "IRA",
  "SPARALANCE",
  "SFURIATE",
  "ATTACCO PIOGGIA",
  "LEGATUTTO",
  "DOPPIASBERLA",
  "FURIA",
  "AVVOLGIBOTTA",
  "LIMITAZIONE",
  "STRIDIO",
  "DANZASPADA",
  "FANGO",
  "ACIDO",
  "SMOG",
  "VELENOSPINA",
  "MANGIASOGNI",
  "PSICHICO",
  "PSICORAGGIO",
  "CONFUSIONE",
  "PSICONDA",
  "FRANA",
  "SASSATA",
  "IDROPOMPA",
  "MARTELLATA",
  "SURF",
  "CASCATA",
  "BOLLARAGGIO",
  "PISTOLACQUA",
  "TENAGLIA",
  "BOLLA",
};

// PT no tiene nombres propios en PokeAPI: usa los ingleses.
static const char *const *const MOVE_NAMES_BY_LANG[LANG_COUNT] = {
  MOVE_NAME_ES, MOVE_NAME_EN, MOVE_NAME_FR,
  MOVE_NAME_DE, MOVE_NAME_IT, MOVE_NAME_EN,
};

struct LearnEntry { uint8_t level, move; };

// 586 pares (nivel, ataque) de las 151, seguidos
static const LearnEntry LEARN_ALL[586] = {
  {1,73}, {13,31}, {27,30}, {48,28}, {1,73}, {13,31},
  {30,30}, {54,28}, {1,31}, {1,73}, {30,30}, {65,28},
  {1,72}, {9,19}, {22,74}, {30,60}, {38,17}, {46,20},
  {1,19}, {1,72}, {24,74}, {33,60}, {42,17}, {56,20},
  {1,19}, {1,72}, {24,74}, {36,60}, {46,17}, {55,20},
  {1,73}, {8,103}, {15,101}, {22,63}, {35,48}, {42,96},
  {1,73}, {1,103}, {15,101}, {24,63}, {39,48}, {47,96},
  {1,73}, {1,101}, {1,103}, {24,63}, {42,48}, {52,96},
  {1,73}, {1,92}, {32,91}, {1,88}, {1,80}, {20,3},
  {25,74}, {30,4}, {1,68}, {12,71}, {28,25}, {1,68},
  {12,71}, {31,25}, {1,68}, {1,71}, {31,25}, {1,73},
  {7,71}, {14,52}, {1,71}, {1,73}, {14,52}, {1,24},
  {15,80}, {29,22}, {1,24}, {15,80}, {34,22}, {1,81},
  {10,88}, {17,63}, {31,83}, {38,86}, {1,81}, {1,88},
  {17,63}, {36,83}, {47,86}, {1,9}, {16,71}, {26,64},
  {43,6}, {1,9}, {1,34}, {1,72}, {17,60}, {24,88},
  {31,64}, {38,76}, {1,34}, {1,72}, {17,60}, {27,88},
  {36,64}, {47,76}, {1,73}, {8,72}, {14,88}, {29,63},
  {36,76}, {1,72}, {1,73}, {14,88}, {32,63}, {41,76},
  {1,51}, {1,72}, {1,73}, {14,88}, {1,73}, {8,61},
  {14,88}, {29,80}, {1,61}, {1,73}, {14,88}, {32,80},
  {1,50}, {1,61}, {1,73}, {1,88}, {1,70}, {18,79},
  {1,79}, {1,19}, {16,71}, {35,17}, {42,20}, {1,19},
  {1,71}, {9,70}, {24,79}, {34,51}, {39,46}, {1,79},
  {1,2}, {15,63}, {28,25}, {1,2}, {1,63}, {1,83},
  {32,25}, {1,33}, {24,86}, {33,29}, {46,28}, {1,33},
  {28,86}, {38,29}, {52,28}, {1,29}, {1,86}, {1,72},
  {20,2}, {34,60}, {1,2}, {1,72}, {39,60}, {1,73},
  {27,2}, {35,91}, {43,90}, {1,2}, {1,73}, {38,91},
  {50,90}, {1,72}, {19,34}, {31,60}, {40,35}, {1,34},
  {1,72}, {35,60}, {47,35}, {1,72}, {12,63}, {17,69},
  {24,83}, {33,76}, {44,60}, {1,63}, {1,72}, {1,83},
  {17,69}, {37,76}, {51,60}, {1,72}, {36,92}, {43,76},
  {52,96}, {1,72}, {39,92}, {48,76}, {59,96}, {1,72},
  {15,67}, {21,76}, {33,15}, {39,50}, {1,67}, {1,72},
  {1,76}, {37,15}, {46,50}, {1,63}, {18,19}, {30,49},
  {50,17}, {1,19}, {1,49}, {1,103}, {19,101}, {25,79},
  {31,51}, {45,96}, {1,101}, {1,103}, {26,79}, {33,51},
  {49,96}, {1,51}, {1,79}, {1,101}, {1,90}, {1,92},
  {27,91}, {38,90}, {1,92}, {27,91}, {38,90}, {1,67},
  {20,14}, {39,15}, {46,11}, {1,14}, {1,67}, {44,15},
  {52,11}, {1,14}, {1,67}, {44,15}, {52,11}, {1,31},
  {13,81}, {26,86}, {33,30}, {42,55}, {1,31}, {1,81},
  {29,86}, {38,30}, {49,55}, {1,30}, {1,86}, {13,81},
  {1,86}, {13,81}, {18,88}, {22,101}, {27,82}, {40,83},
  {48,96}, {1,81}, {1,86}, {18,88}, {22,101}, {27,82},
  {43,83}, {50,96}, {1,73}, {16,95}, {21,44}, {31,35},
  {36,42}, {1,73}, {16,95}, {21,44}, {36,35}, {43,42},
  {1,73}, {16,95}, {21,44}, {36,35}, {43,42}, {1,19},
  {32,62}, {39,20}, {43,49}, {1,19}, {1,62}, {39,20},
  {47,49}, {1,92}, {22,59}, {33,101}, {48,90}, {1,59},
  {1,92}, {33,101}, {55,90}, {1,73}, {25,9}, {41,64},
  {47,83}, {1,9}, {1,73}, {46,64}, {54,83}, {1,24},
  {15,80}, {23,84}, {39,60}, {1,24}, {24,80}, {30,22},
  {36,74}, {40,57}, {1,24}, {1,80}, {30,22}, {39,74},
  {45,57}, {1,59}, {1,98}, {35,41}, {45,49}, {50,39},
  {1,41}, {1,59}, {50,49}, {56,39}, {1,70}, {37,85},
  {48,83}, {1,70}, {37,85}, {53,83}, {1,73}, {23,102},
  {30,41}, {50,39}, {1,41}, {1,102}, {50,75}, {1,26},
  {1,27}, {35,89}, {1,26}, {1,27}, {38,89}, {1,26},
  {1,27}, {38,89}, {1,73}, {1,83}, {15,78}, {19,95},
  {25,74}, {33,55}, {1,70}, {17,92}, {24,59}, {32,90},
  {1,70}, {1,92}, {24,59}, {37,90}, {1,103}, {20,65},
  {30,62}, {35,97}, {1,65}, {1,103}, {34,62}, {42,97},
  {1,6}, {1,73}, {1,83}, {22,44}, {36,64}, {43,42},
  {1,6}, {1,73}, {1,83}, {22,44}, {40,64}, {50,42},
  {1,77}, {42,28}, {1,28}, {1,77}, {28,62}, {1,36},
  {38,50}, {43,37}, {46,74}, {1,36}, {41,50}, {48,37},
  {55,74}, {33,13}, {38,12}, {48,10}, {53,45}, {1,11},
  {33,18}, {38,40}, {43,8}, {48,53}, {1,81}, {7,62},
  {31,55}, {39,83}, {1,73}, {1,87}, {32,85}, {40,44},
  {48,42}, {1,73}, {1,85}, {1,87}, {43,44}, {53,42},
  {1,34}, {1,61}, {30,62}, {40,80}, {55,49}, {1,34},
  {1,61}, {1,62}, {1,80}, {64,49}, {1,70}, {1,79},
  {54,46}, {1,78}, {1,82}, {29,33}, {45,55}, {1,74},
  {26,63}, {36,53}, {46,58}, {1,103}, {30,101}, {45,96},
  {1,103}, {30,101}, {52,96}, {1,24}, {24,61}, {30,80},
  {37,99}, {1,24}, {24,61}, {30,80}, {39,99}, {1,73},
  {17,101}, {32,64}, {47,96}, {1,73}, {1,101}, {1,92},
  {31,79}, {1,71}, {29,60}, {35,84}, {1,70}, {18,27},
  {23,79}, {31,40}, {39,51}, {47,50}, {58,38}, {1,71},
  {34,9}, {37,83}, {42,8}, {54,6}, {1,19}, {43,18},
  {52,87}, {55,17}, {1,65}, {25,15}, {49,60}, {54,84},
  {1,73}, {21,62}, {44,74}, {51,49}, {15,73}, {1,5},
  {1,63}, {1,96}, {52,43}, {1,101}, {25,51}, {38,39},
  {46,96}, {1,73}, {27,71}, {37,63}, {45,49}, {1,71},
  {1,73}, {1,101}, {40,63}, {54,96}, {1,9}, {1,71},
  {1,73}, {48,4}, {54,6}, {1,19}, {1,71}, {1,73},
  {40,63}, {44,20}, {48,74}, {54,17}, {1,73}, {23,91},
  {42,57}, {1,101}, {34,61}, {46,75}, {53,96}, {1,61},
  {1,101}, {44,75}, {49,96}, {1,72}, {34,33}, {39,60},
  {49,96}, {1,33}, {1,72}, {39,60}, {53,96}, {1,25},
  {38,63}, {45,49}, {54,43}, {1,59}, {35,51}, {48,46},
  {56,43}, {1,24}, {1,39}, {51,38}, {1,9}, {1,22},
  {51,6}, {1,20}, {1,24}, {60,21}, {1,81}, {30,55},
  {40,5}, {50,43}, {1,81}, {35,55}, {45,5}, {55,43},
  {1,81}, {35,55}, {45,5}, {60,43}, {1,64}, {1,90},
  {1,92}, {1,70}, {20,53}, {40,90},
};

// LEARN_OFF[dex] .. LEARN_OFF[dex+1] delimita el movepool de esa especie
static const uint16_t LEARN_OFF[DEX_COUNT + 2] = {
  0, 0, 4, 8, 12, 18, 24, 30, 36, 42, 48, 49,
  49, 51, 52, 52, 56, 59, 62, 65, 68, 71, 74, 77,
  82, 87, 91, 92, 98, 104, 109, 114, 118, 122, 126, 130,
  132, 133, 137, 139, 143, 144, 147, 151, 155, 159, 161, 164,
  167, 171, 175, 179, 183, 189, 195, 199, 203, 208, 213, 217,
  219, 224, 229, 232, 233, 236, 239, 243, 247, 251, 256, 261,
  264, 271, 278, 283, 288, 293, 297, 301, 305, 309, 313, 317,
  321, 326, 331, 336, 340, 343, 346, 350, 353, 356, 359, 362,
  368, 372, 376, 380, 384, 390, 396, 398, 401, 405, 409, 413,
  418, 422, 427, 432, 437, 442, 445, 449, 453, 456, 459, 463,
  467, 471, 473, 475, 478, 485, 490, 494, 498, 502, 503, 507,
  511, 511, 515, 520, 525, 532, 535, 539, 543, 547, 551, 555,
  559, 562, 565, 568, 572, 576, 580, 583, 586,
};

// especie de la que evoluciona cada una (0 = forma base)
static const uint8_t MOVE_PREVO[DEX_COUNT + 1] = {
  0,
  0, 1, 2, 0, 4, 5, 0, 7, 8, 0, 10, 11,
  0, 13, 14, 0, 16, 17, 0, 19, 0, 21, 0, 23,
  0, 25, 0, 27, 0, 29, 30, 0, 32, 33, 0, 35,
  0, 37, 0, 39, 0, 41, 0, 43, 44, 0, 46, 0,
  48, 0, 50, 0, 52, 0, 54, 0, 56, 0, 58, 0,
  60, 61, 0, 63, 64, 0, 66, 67, 0, 69, 70, 0,
  72, 0, 74, 75, 0, 77, 0, 79, 0, 81, 0, 0,
  84, 0, 86, 0, 88, 0, 90, 0, 92, 93, 0, 0,
  96, 0, 98, 0, 100, 0, 102, 0, 104, 0, 0, 0,
  0, 109, 0, 111, 0, 0, 0, 0, 116, 0, 118, 0,
  120, 0, 0, 0, 0, 0, 0, 0, 0, 129, 0, 0,
  0, 133, 133, 133, 0, 0, 138, 0, 140, 0, 0, 0,
  0, 0, 0, 147, 148, 0, 0,
};

static inline const char *moveName(uint8_t id) {
  if (id > MOVE_COUNT) return "";
  return MOVE_NAMES_BY_LANG[gLang][id];
}

// Los cuatro ataques mas recientes que la especie sabe a ese nivel.
// Rellena out[] con 0 en los huecos libres y devuelve cuantos hay.
static inline uint8_t movesForLevel(int16_t dex, uint8_t level,
                                    uint8_t out[MOVE_SLOTS]) {
  for (uint8_t i = 0; i < MOVE_SLOTS; i++) out[i] = 0;
  if (dex < 1 || dex > DEX_COUNT) return 0;
  uint8_t n = 0;
  // sube por la cadena evolutiva: al evolucionar se conservan los
  // ataques, asi que un Dragoran tambien cuenta con los de Dratini
  for (int16_t sp = dex; sp >= 1 && n < MOVE_SLOTS; sp = MOVE_PREVO[sp]) {
    // de atras adelante: el movepool esta ordenado por nivel
    for (uint16_t i = LEARN_OFF[sp + 1]; i > LEARN_OFF[sp] && n < MOVE_SLOTS; ) {
      i--;
      if (LEARN_ALL[i].level > level) continue;
      bool dup = false;
      for (uint8_t k = 0; k < n; k++)
        if (out[k] == LEARN_ALL[i].move) { dup = true; break; }
      if (!dup) out[n++] = LEARN_ALL[i].move;
    }
    if (MOVE_PREVO[sp] == 0) break;
  }
  if (n == 0) { out[0] = MOVE_STRUGGLE; return 1; }

  // Garantiza al menos un ataque del tipo propio (STAB). Sin esto, un
  // Pikachu de nivel alto pelea solo con ataques normales.
  uint8_t t1 = DEX_TBL[dex].type1, t2 = DEX_TBL[dex].type2;
  bool tiene = false;
  for (uint8_t k = 0; k < n; k++)
    if (MOVE_TBL[out[k]].type == t1 || MOVE_TBL[out[k]].type == t2) tiene = true;
  if (!tiene) {
    uint8_t mejor = 0;
    for (int16_t sp = dex; sp >= 1; sp = MOVE_PREVO[sp]) {
      for (uint16_t i = LEARN_OFF[sp]; i < LEARN_OFF[sp + 1]; i++) {
        uint8_t m = LEARN_ALL[i].move;
        if (LEARN_ALL[i].level > level) continue;
        if (MOVE_TBL[m].type != t1 && MOVE_TBL[m].type != t2) continue;
        if (MOVE_TBL[m].power > MOVE_TBL[mejor].power) mejor = m;
      }
      if (MOVE_PREVO[sp] == 0) break;
    }
    if (mejor) {
      uint8_t flojo = 0;  // sacrifica el mas debil de los elegidos
      for (uint8_t k = 1; k < n; k++)
        if (MOVE_TBL[out[k]].power < MOVE_TBL[out[flojo]].power) flojo = k;
      out[n < MOVE_SLOTS ? n++ : flojo] = mejor;
    }
  }
  return n;
}

// Ataque que toca aprender justo a ese nivel (0 = ninguno).
static inline uint8_t newMoveAt(int16_t dex, uint8_t level) {
  if (dex < 1 || dex > DEX_COUNT) return 0;
  for (uint16_t i = LEARN_OFF[dex]; i < LEARN_OFF[dex + 1]; i++)
    if (LEARN_ALL[i].level == level) return LEARN_ALL[i].move;
  return 0;
}
