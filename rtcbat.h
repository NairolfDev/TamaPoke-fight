#pragma once
#include <Arduino.h>

// RTC PCF85063: hora persistente mientras la placa tenga alimentacion
bool rtcBegin();
uint32_t rtcEpoch();             // segundos unix; 0 si el RTC no es valido
void rtcSetEpoch(uint32_t e);

// PMU AXP2101: estado de la bateria
bool batBegin();
void pmuEnablePanel();           // enciende BLDO1 (OLED VDD 3.3V); llamar antes de gfx->begin()
int batPercent();                // 0-100, -1 si no hay bateria conectada
bool batCharging();
bool usbPresent();

// Restlaufzeit. Die Kapazitaet des Akkus ist unbekannt und der AXP2101 hat
// keinen Strommesser - die Entladerate wird deshalb aus dem Prozentverlauf
// gelernt (0.1 %/h, gleitend gemittelt) und in einem eigenen NVS-Bereich
// "tpbat" abgelegt, den ein Zuruecksetzen des Spielstands nicht loescht.
// Jede Schleife aufrufen; quiet = Schirm dunkel oder Schlaf, nur dann wird
// geschrieben (ein NVS-Schreiben friert beide Kerne ~1 s ein).
void batEstimateTick(bool quiet);
int batHoursLeft();              // Stunden, -1 = noch nicht gelernt

// Reine Rechnung, ohne Hardware - tools/check_bat.py rechnet sie nach.
inline uint16_t batRateBlend(uint16_t old10, uint8_t dropPct, uint32_t dtMs) {
  if (dtMs == 0 || dropPct == 0) return old10;
  uint32_t r = (uint32_t)dropPct * 36000000UL / dtMs;  // 0.1 %/h
  if (r < 1) r = 1;
  if (r > 60000) r = 60000;
  return old10 ? (uint16_t)(((uint32_t)old10 * 3 + r) / 4) : (uint16_t)r;
}
// Energiesparmodus: unter 25 % ohne Ladegeraet an, erst ab 30 % wieder aus.
// Dazwischen bleibt der Zustand - ein Prozent Rauschen darf ihn nicht flackern
// lassen. Laden beendet ihn sofort.
inline bool batSaverNext(bool cur, int pct, bool charging) {
  if (pct < 0 || charging) return false;
  if (pct < 25) return true;
  if (pct >= 30) return false;
  return cur;
}
inline int batHoursFromRate(int pct, uint16_t rate10) {
  if (pct < 0 || rate10 == 0) return -1;
  uint32_t hh = (uint32_t)pct * 10 / rate10;
  return hh > 99 ? 99 : (int)hh;
}

// boton PWR del AXP2101: pulsacion larga 4s = apagado fisico (RTC sigue vivo);
// la pulsacion corta la captura el firmware (pantalla on/off)
void pwrSetup();
bool pwrShortPressed();  // sondear en el loop
