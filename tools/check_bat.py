#!/usr/bin/env python3
"""Rechnet die Akku-Schaetzung aus rtcbat.h nach.

Es gibt keinen Host-Compiler auf dem Entwicklungsrechner, deshalb ein Zwilling
wie bei battle_sim.py. Damit er nicht still auseinanderlaeuft, prueft der Test
auch, dass die Konstanten im Header noch dieselben sind.

    python3 tools/check_bat.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADER = open(os.path.join(ROOT, 'rtcbat.h'), encoding='utf-8').read()


def rate_blend(old10, drop_pct, dt_ms):
    if dt_ms == 0 or drop_pct == 0:
        return old10
    r = drop_pct * 36000000 // dt_ms          # 0.1 %/h
    r = max(1, min(60000, r))
    return (old10 * 3 + r) // 4 if old10 else r


def hours_from_rate(pct, rate10):
    if pct < 0 or rate10 == 0:
        return -1
    return min(99, pct * 10 // rate10)


def main():
    # 2 % in einer Stunde = 2,0 %/h = 20
    assert rate_blend(0, 2, 3600000) == 20
    # bei 80 % Akku reicht das 40 Stunden
    assert hours_from_rate(80, 20) == 40
    # 5 % in 30 Min = 10 %/h = 100; 100 % -> 10 h
    assert rate_blend(0, 5, 1800000) == 100
    assert hours_from_rate(100, 100) == 10
    # gleitender Mittelwert: drei Teile alt, ein Teil neu
    assert rate_blend(20, 5, 1800000) == (20 * 3 + 100) // 4
    # kein Messwert -> unbekannt, nie durch null teilen
    assert hours_from_rate(50, 0) == -1
    assert hours_from_rate(-1, 20) == -1
    assert rate_blend(20, 0, 3600000) == 20
    assert rate_blend(20, 3, 0) == 20
    # Obergrenze: ein Stundenwert ueber 99 wird nicht angezeigt
    assert hours_from_rate(100, 1) == 99
    # sehr schneller Abfall: begrenzt, laeuft nicht ueber uint16
    assert rate_blend(0, 100, 1000) == 60000
    # dropPct * 36e6 muss in uint32 passen (C rechnet mit uint32_t)
    assert 100 * 36000000 < 2 ** 32

    # dieselben Konstanten wie im Header?
    for needle in ('36000000UL', '* 3 +', '/ 4', '60000', '* 10 / rate10', '99'):
        assert needle in HEADER, 'rtcbat.h: %r fehlt - Zwilling veraltet?' % needle
    assert re.search(r'dtMs == 0 \|\| dropPct == 0', HEADER)
    print('check_bat: OK')


if __name__ == '__main__':
    main()
