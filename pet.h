#pragma once
#include <Arduino.h>
#include <Preferences.h>

#include "levels.h"  // LVL_REQ, LEVEL_CAP (BATTLE_SPEC 3.2)

// Schemaversion des NVS-Blocks. Beim Hochzaehlen gehoert eine Migration in
// Pet::migrate() dazu - Nutzer sollen fuer ein Update kein WIPE brauchen.
#define NVS_VER 2

// 1 tick = 1 minuto de juego. Baja este valor para probar mas rapido
// (p. ej. 5000UL = las estadisticas caen 12x mas rapido).
#define PET_TICK_MS 60000UL
// Minutos de juego por nivel. Con 60, CHARMANDER evoluciona a las ~16 h
// de juego con cuidado perfecto. Baja a 1 para ver evoluciones al momento.
#define MINUTES_PER_LEVEL 60
#define EAT_ANIM_MS 2500UL
#define HEART_MS 1500UL
#define EVOLVE_ANIM_MS 5200UL              // animacion de evolucion (mas larga = mas epica)
#define CEREMONY_MS 10000UL                // duracion de la despedida en pantalla
// 3.3: Endstufe seit mindestens einem Tag. Frueher waren es drei Tage
// Gesamtalter - mit der Kurve aus 3.2 faellt die Endstufe aber selbst erst
// nach 3,5 Tagen, der Abschiedsbutton erschiene also im selben Moment wie
// die letzte Entwicklung, ohne Endgame-Fenster.
#define FINAL_FORM_MIN (24UL * 60)
#define RUNAWAY_TICKS 60                   // se escapa tras 1 h con TODO a cero

// ceremonias de fin de ciclo
enum : uint8_t { CER_NONE = 0, CER_FAREWELL, CER_RUNAWAY, CER_RELEASE };

enum PetMood : uint8_t { MOOD_HAPPY, MOOD_SAD, MOOD_EATING, MOOD_SLEEPING };

// medallas del individuo (bitmask)
enum : uint16_t {
  MED_LV10 = 1 << 0, MED_LV25 = 1 << 1, MED_LV50 = 1 << 2,
  MED_BERRY = 1 << 3, MED_STREAK7 = 1 << 4, MED_BOND = 1 << 5,
  MED_FINAL = 1 << 6, MED_FIT = 1 << 7,
};
#define MED_COUNT 8

class Pet {
public:
  // Estadisticas 0..100
  uint8_t fullness = 80;  // comida
  uint8_t joy = 80;       // felicidad
  uint8_t energy = 80;    // energia
  uint8_t hygiene = 100;  // limpieza
  uint8_t poops = 0;      // cacas en pantalla (max 3)
  uint8_t weight = 0;     // 0-100: las chuches engordan, el minijuego quema
  // genes (90-110%, se tiran al eclosionar) y entrenamiento (0-100)
  uint8_t geneAtk = 100, geneDef = 100, geneSpe = 100;
  uint8_t trAtk = 0, trDef = 0, trSpe = 0;
  bool berryKnown = false;  // ya descubrio su baya favorita
  bool shiny = false;       // variante de color rara (se sortea en el huevo)
  uint32_t ageMinutes = 0;
  int16_t speciesId = -1;      // numero de Pokedex (1-151), -1 = huevo
  int16_t prevSpeciesId = -1;  // para la animacion de evolucion
  uint8_t careMistakes = 0;   // descuidos: cada uno retrasa la evolucion 1 nivel
  bool sleeping = false;
  uint32_t lastSeenEpoch = 0;   // ultima hora RTC vista (para progresion offline)
  uint8_t ceremony = CER_NONE;  // despedida/escapada/liberacion en curso
  uint8_t lastEnd = CER_NONE;   // como acabo la anterior (afecta al huevo)
  uint8_t dexReg[19] = { 0 };       // pokedex de criados (bitmap 151 bits)
  uint8_t dexShinyReg[19] = { 0 };  // criados en version shiny
  // racha de cuidado diario (del jugador: persiste entre crianzas)
  uint16_t streak = 0, bestStreak = 0;
  uint32_t lastCareDay = 0;
  // vinculo (del bicho: sube lento con cuidado, se resetea al nacer otro)
  uint8_t bond = 0;
  char nick[12] = "";    // apodo (vacio = nombre de especie)
  // medallas: del individuo + contador acumulado entre todas las crianzas
  uint16_t medals = 0, totalMedals = 0;
  uint16_t newMedal = 0;   // recien conseguida(s), para celebrar
  uint16_t lastMilestone = 0;  // hito de racha ya celebrado
  uint16_t gameHi = 0;     // record del minijuego (del jugador)
  uint16_t strHi = 0;      // record de golpes al saco (sin usar desde Fase 5)

  // --- Phase 5: Levelaufstieg durch Kampf (BATTLE_SPEC 5.4) ---
  // ageMinutes laeuft unveraendert weiter und treibt weiter Statusverfall,
  // Kack-Rhythmus, Gewicht und Lebenszyklus. Das Level haengt daneben an
  // levelsWon, sonst friert ein Anhalten von ageMinutes das ganze Spiel ein.
  uint32_t xpMinutes = 0;    // Fortschritt, friert bei lvlReq() ein
  uint8_t levelsWon = 0;     // level() = 1 + levelsWon
  uint32_t finalFormAt = 0;  // ageMinutes beim Erreichen der Endstufe
  uint8_t moves[4] = { 0 };  // Attacken-IDs, 0 = leerer Slot (= MOVE_SLOTS)
  uint8_t pp[4] = { 0 };
  uint16_t battlesWon = 0, battlesLost = 0;
  uint8_t lossStreak = 0;    // Mitleidsstaffelung, siehe 6.7
  uint8_t nvsVer = NVS_VER;  // Schemaversion, siehe migrate() in pet.cpp

  // 4.2: xpMinutes zaehlt pro Spielminute um 1 hoch und STOPPT bei
  // lvlReq(). Kein Banking - es ist immer genau eine Stufe offen.
  void tickXp() {
    if (isEgg() || level() >= LEVEL_CAP) return;
    uint16_t need = lvlReq();
    if (xpMinutes < need) xpMinutes++;
  }

  void levelUp();               // 4.2: nach gewonnenem Levelkampf
  void addBattleXp(uint8_t foeLevel);  // 4.3: XP aus freiem Kampf
  void migrate();               // 5.4: NVS-Schema hochziehen
  void setLevel(uint8_t lv);    // Testhilfe fuer den LVL-Konsolenbefehl
  // Testhilfen fuer BOND und ENE auf der Konsole. save() ist privat, deshalb
  // hier statt im Sketch. Bindung und Erschoepfung sind sonst nicht gezielt
  // vorfuehrbar - Bindung braucht Tage, Energie Minuten.
  void setBond(uint8_t v);
  void setEnergy(uint8_t v);

  // --- Attackenslots (5.3) ---
  // moves[]/pp[] sind die Wahrheit: der Kampf liest sie, er leitet die
  // Attacken nicht mehr bei jedem Start aus dem Learnset ab. Sonst waere die
  // Wahl des Spielers im Lerndialog wirkungslos.
  void syncMoves();             // Slots aus dem Learnset fuellen
  void refillPp();              // 6.7: AP sind beim Aufwachen wieder voll
  void learnMove(uint8_t mv, int8_t slot);  // Slot ersetzen (oder belegen)
  int8_t freeMoveSlot() const {
    for (int8_t i = 0; i < 4; i++)
      if (!moves[i]) return i;
    return -1;
  }
  bool knowsMove(uint8_t mv) const {
    for (uint8_t i = 0; i < 4; i++)
      if (moves[i] == mv) return true;
    return false;
  }
  // Attacke, die nach einem Aufstieg ansteht und noch keinen Slot hat.
  // 0 = keine. Die UI raeumt sie ueber den Lerndialog ab.
  uint8_t pendingMove = 0;

  void begin();                 // carga estado de NVS (o crea el primer huevo)
  void update(uint32_t nowMs);  // llamar en cada loop()

  // Acciones (botones tactiles)
  void feed();              // baya roja (compatibilidad)
  void feedBerry(uint8_t color);  // 0 roja, 1 azul, 2 verde
  void feedCandy();
  bool lovesBerry(uint8_t color) const {
    return !isEgg() && (speciesId % 3) == color;  // gusto oculto por especie
  }
  void playResult(uint8_t score);  // recompensa del minijuego (entrena VEL)
  // Kampf, BATTLE_SPEC 6.7. battleCost() ist in jedem Fall faellig,
  // battleWin()/battleLoss() je nach Ausgang.
  void battleCost();
  void battleWin();
  void battleLoss();

  // stats de combate: base real de gen 1 x genes + nivel + entrenamiento
  uint16_t atkStat() const;
  uint16_t defStat() const;
  uint16_t speStat() const;
  void play();
  void toggleLight();  // dormir / despertar
  void clean();
  void caress();  // tocar al bicho
  void eggTap();  // tocar el huevo: 3 toques y eclosiona
  void newEgg();   // empezar de cero con un inicial aleatorio
  void release();  // soltar (pulsacion larga + confirmar)
  void syncClock(uint32_t nowEpoch);  // aplica el tiempo transcurrido apagado
  void setClock(uint32_t nowEpoch);   // fija la hora sin aplicar progresion
  void startFarewell();  // tambien usable desde la consola serie (BYE)
  void startRunaway();   // tambien usable desde la consola serie (RUN)

  bool isEgg() const { return speciesId < 0; }
  uint8_t eggCracks() const { return eggTaps; }
  bool eating() const { return millis() < eatUntil; }
  bool showHeart() const { return millis() < heartUntil; }
  bool evolving() const { return millis() < evolveUntil; }
  float evolveT() const {     // progreso de la animacion de evolucion 0..1
    uint32_t n = millis();
    uint32_t left = evolveUntil > n ? evolveUntil - n : 0;
    return 1.0f - (float)left / (float)EVOLVE_ANIM_MS;
  }
  bool canEvolveNow() const;  // condiciones de evolucion cumplidas (lista)
  void evolve();              // dispara la transformacion (la llama un toque del usuario)
  bool canFarewellNow() const;  // forma final + 7 dias: lista para despedirse (boton)
  bool canRunawayNow() const;   // abandono total 1h: lista para escaparse (boton triste)
  // el usuario decide en un dialogo; "mantener/quedaros" pospone y re-ofrece luego
  bool wantEvolveButton() const { return canEvolveNow() && level() > evoDeclinedLv; }
  bool wantFarewellButton() const { return canFarewellNow() && ageMinutes >= farDeclinedAge; }
  void declineEvolve() { evoDeclinedLv = level(); }              // re-ofrece al subir de nivel
  void declineFarewell() { farDeclinedAge = ageMinutes + 1440; } // re-ofrece dentro de 1 dia
  // primera partida: el jugador elige inicial (Bulbasaur/Charmander/Squirtle)
  bool awaitingStarter() const { return starterPick; }
  void chooseStarter(int16_t dex) { eggTarget = dex; starterPick = false; save(); }
  void factoryReset() { prefs.clear(); }  // borra la NVS (test: comando serie WIPE)
  void dbgRunawayReady() { fullness = joy = energy = hygiene = 0; neglectTicks = RUNAWAY_TICKS; }  // test
  // 4.2: das Level steigt nur durch gewonnene Kaempfe, nicht mit der Zeit.
  uint8_t level() const { return 1 + levelsWon; }

  // Minuten von diesem Level auf das naechste. Bei LEVEL_CAP friert der
  // Fortschritt ein, dann gibt es keine Levelkaempfe mehr.
  uint16_t lvlReq() const {
    return level() >= LEVEL_CAP ? 0xFFFF : LVL_REQ[level()];
  }

  // Eine offene Stufe: der naechste gewonnene Kampf ist der Levelkampf.
  // Kein Banking - xpMinutes stoppt bei lvlReq(), es ist immer genau eine.
  bool levelPending() const { return xpMinutes >= lvlReq(); }

  // 4.3: XP eines freien Kampfes. Nur wenn KEIN Level offen ist - sonst ist
  // der naechste Sieg selbst der Aufstieg.
  uint16_t xpGainFor(uint8_t foeLevel) const {
    if (levelPending() || level() >= LEVEL_CAP) return 0;
    int pct = 12 + 4 * ((int)foeLevel - (int)level());
    if (pct < 5) pct = 5;
    if (pct > 25) pct = 25;
    return (uint16_t)((uint32_t)lvlReq() * pct / 100);
  }
  bool isRegistered(int16_t dex) const {
    return dex >= 1 && dex <= 151 && (dexReg[(dex - 1) >> 3] & (1 << ((dex - 1) & 7)));
  }
  bool isShinyRegistered(int16_t dex) const {
    return dex >= 1 && dex <= 151 && (dexShinyReg[(dex - 1) >> 3] & (1 << ((dex - 1) & 7)));
  }
  uint16_t registeredCount() const;
  bool lineHasUnregistered(int16_t base) const;
  uint8_t eggRarity() const;       // rareza del huevo actual (sin revelar especie)
  int16_t pickEggSpecies();        // publica para poder simular tiradas (EGGS)
  uint8_t lowestStat() const { return min(min(fullness, joy), min(energy, hygiene)); }
  PetMood mood() const;
  // progreso de la ceremonia de despedida/escapada, 0..1 (para animarla)
  float ceremonyT() const {
    if (ceremony == CER_NONE) return 0.0f;
    uint32_t n = millis();
    uint32_t left = ceremonyUntil > n ? ceremonyUntil - n : 0;
    return 1.0f - (float)left / (float)CEREMONY_MS;
  }

  // racha / vinculo / medallas / nombre
  void rename(const char *name);
  bool hasMedal(uint16_t m) const { return medals & m; }
  bool showMedal() const { return millis() < medalUntil; }
  bool showMilestone() const { return millis() < milestoneUntil; }
  int careBonus() const;  // mejora del huevo por racha + vinculo

  // guardado periodico diferido: tick() marca pendiente y el loop lo vuelca
  // cuando la pantalla esta atenuada/apagada (la escritura a flash congela
  // ~1s ambos cores: asi no se ve ni corta el tactil)
  bool savePending() const { return pendingSave; }
  void flushSave();

private:
  Preferences prefs;
  uint32_t lastTick = 0;
  uint32_t eatUntil = 0;
  uint32_t heartUntil = 0;
  uint32_t evolveUntil = 0;
  int16_t eggTarget = 1;       // dex oculto que saldra del huevo
  bool eggShiny = false;       // sorpresa sorteada al crear el huevo
  uint8_t eggTaps = 0;
  uint8_t mistakeCooldown = 0;
  uint8_t ticksSinceSave = 0;
  bool pendingSave = false;     // guardado periodico pendiente de volcar
  uint8_t evoDeclinedLv = 0;    // "mantener forma": no ofrecer evolucion hasta subir de nivel
  uint32_t farDeclinedAge = 0;  // "quedaros juntos": no ofrecer despedida hasta esta edad
  bool starterPick = false;     // primera partida: esperando que el jugador elija inicial
  uint8_t neglectTicks = 0;
  uint16_t goodTicks = 0;  // racha bien cuidado: forja la DEF
  uint32_t ceremonyUntil = 0;
  uint8_t bondToday = 0;       // tope diario de subida de vinculo
  uint32_t medalUntil = 0;     // celebracion de medalla en pantalla
  uint32_t milestoneUntil = 0; // celebracion de hito de racha

  uint32_t today() const { return lastSeenEpoch ? lastSeenEpoch / 86400 : 0; }
  void registerCare();   // primer cuidado del dia: racha + vinculo
  void addBond(uint8_t amt);
  void checkMedals();
  void tick();
  void hatch();
  void registerSpecies(int16_t dex);
  void save();
  void load();
  static uint8_t clamp100(int v) { return v < 0 ? 0 : (v > 100 ? 100 : v); }
};
