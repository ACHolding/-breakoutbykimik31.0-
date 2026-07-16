#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FAMICOM BREAKOUT
================
A Breakout / Arkanoid-style brick breaker with authentic NES (Famicom)
flavor, built on Pygame at 60 FPS:

  * 256x240 picture (real NES resolution) upscaled with nearest neighbor
  * The classic 64-color NES master palette
  * 8x8 pixel font, chunky sprites, CRT scanline overlay
  * APU-style chiptune audio synthesized at runtime: two pulse channels,
    one triangle channel and one noise channel (15-bit LFSR), just like
    the 2A03 sound chip - music loop plus all sound effects
  * No external files, no assets - everything is generated in code

Controls
--------
  LEFT / RIGHT or A / D : move paddle      (mouse works too)
  SPACE / ENTER         : launch ball / start game
  P                     : pause
  F1                    : toggle CRT scanlines
  M                     : toggle music
  ESC                   : quit

Run:
  pip install pygame-ce        (or: pip install pygame)
  python famicom_breakout.py [scale 1-4]
"""
import math
import random
import sys
from array import array

import pygame

# ---------------------------------------------------------------------------
# NES master palette (blargg NTSC 2C02 approximation, 64 entries)
# ---------------------------------------------------------------------------
PAL = [
    ( 84, 84, 84), (  0, 30,116), (  8, 16,144), ( 48,  0,136),
    ( 68,  0,100), ( 92,  0, 48), ( 84,  4,  0), ( 60, 24,  0),
    ( 32, 42,  0), (  8, 58,  0), (  0, 64,  0), (  0, 60,  0),
    (  0, 50, 60), (  0,  0,  0), (  0,  0,  0), (  0,  0,  0),
    (152,150,152), (  8, 76,196), ( 48, 50,236), ( 92, 30,228),
    (136, 20,176), (160, 20,100), (152, 34, 32), (120, 60,  0),
    ( 84, 90,  0), ( 40,114,  0), (  8,124,  0), (  0,118, 40),
    (  0,102,120), (  0,  0,  0), (  0,  0,  0), (  0,  0,  0),
    (236,238,236), ( 76,154,236), (120,124,236), (176, 98,236),
    (228, 84,236), (236, 88,180), (236,106,100), (212,136, 32),
    (160,170,  0), (116,196,  0), ( 76,208, 32), ( 56,204,108),
    ( 56,180,204), ( 60, 60, 60), (  0,  0,  0), (  0,  0,  0),
    (236,238,236), (168,204,236), (188,188,236), (212,178,236),
    (236,174,236), (236,174,212), (236,180,176), (228,196,144),
    (204,210,120), (180,222,120), (168,226,144), (152,226,180),
    (160,214,228), (160,162,160), (  0,  0,  0), (  0,  0,  0),
]

BLACK  = PAL[13]
WHITE  = PAL[32]
GRAY   = PAL[0]
LGRAY  = PAL[16]
DGRAY  = PAL[45]
RED    = PAL[38]
DRED   = PAL[22]
SKY    = PAL[33]
YELLOW = PAL[56]
PINK   = PAL[37]

# ---------------------------------------------------------------------------
# 8x8 pixel font ('#' = pixel on).  Glyphs advance 8 px, NES tile style.
# ---------------------------------------------------------------------------
FONT = {
    ' ': ["........"] * 8,
    'A': ["..###...", ".##.##..", "##...##.", "##...##.", "#######.", "##...##.", "##...##.", "##...##."],
    'B': ["######..", "##...##.", "##...##.", "######..", "##...##.", "##...##.", "##...##.", "######.."],
    'C': [".#####..", "##...##.", "##......", "##......", "##......", "##......", "##...##.", ".#####.."],
    'D': ["######..", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", "######.."],
    'E': ["#######.", "##......", "##......", "#####...", "##......", "##......", "##......", "#######."],
    'F': ["#######.", "##......", "##......", "#####...", "##......", "##......", "##......", "##......"],
    'G': [".#####..", "##...##.", "##......", "##......", "##..###.", "##...##.", "##...##.", ".#####.."],
    'H': ["##...##.", "##...##.", "##...##.", "#######.", "##...##.", "##...##.", "##...##.", "##...##."],
    'I': [".######.", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", ".######."],
    'J': ["...####.", ".....##.", ".....##.", ".....##.", ".....##.", ".....##.", "##...##.", ".#####.."],
    'K': ["##...##.", "##..##..", "##.##...", "####....", "##.##...", "##..##..", "##...##.", "##...##."],
    'L': ["##......", "##......", "##......", "##......", "##......", "##......", "##......", "#######."],
    'M': ["##...##.", "###.###.", "#######.", "#######.", "##.#.##.", "##...##.", "##...##.", "##...##."],
    'N': ["##...##.", "###..##.", "####.##.", "##.####.", "##..###.", "##...##.", "##...##.", "##...##."],
    'O': [".#####..", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", ".#####.."],
    'P': ["######..", "##...##.", "##...##.", "######..", "##......", "##......", "##......", "##......"],
    'Q': [".#####..", "##...##.", "##...##.", "##...##.", "##.#.##.", "##..##..", "##..##..", ".####.##"],
    'R': ["######..", "##...##.", "##...##.", "######..", "##.##...", "##..##..", "##...##.", "##...##."],
    'S': [".#####..", "##...##.", "##......", ".#####..", ".....##.", ".....##.", "##...##.", ".#####.."],
    'T': ["#######.", "...##...", "...##...", "...##...", "...##...", "...##...", "...##...", "...##..."],
    'U': ["##...##.", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", ".#####.."],
    'V': ["##...##.", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.", ".##.##..", "..###..."],
    'W': ["##...##.", "##...##.", "##...##.", "##.#.##.", "#######.", "#######.", "###.###.", "##...##."],
    'X': ["##...##.", "##...##.", ".##.##..", "..###...", "..###...", ".##.##..", "##...##.", "##...##."],
    'Y': ["##...##.", "##...##.", ".##.##..", "..###...", "..###...", "...##...", "...##...", "...##..."],
    'Z': ["#######.", ".....##.", "....##..", "...##...", "..##....", ".##.....", "##......", "#######."],
    '0': [".#####..", "##...##.", "##..###.", "##.####.", "####.##.", "###..##.", "##...##.", ".#####.."],
    '1': ["...##...", "..###...", ".####...", "...##...", "...##...", "...##...", "...##...", ".######."],
    '2': [".#####..", "##...##.", ".....##.", "....##..", "...##...", "..##....", ".##.....", "#######."],
    '3': [".#####..", "##...##.", ".....##.", "...###..", ".....##.", ".....##.", "##...##.", ".#####.."],
    '4': ["....###.", "...####.", "..##.##.", ".##..##.", "##...##.", "#######.", ".....##.", ".....##."],
    '5': ["#######.", "##......", "######..", ".....##.", ".....##.", ".....##.", "##...##.", ".#####.."],
    '6': ["..####..", ".##.....", "##......", "######..", "##...##.", "##...##.", "##...##.", ".#####.."],
    '7': ["#######.", "##...##.", ".....##.", "....##..", "...##...", "..##....", "..##....", "..##...."],
    '8': [".#####..", "##...##.", "##...##.", ".#####..", "##...##.", "##...##.", "##...##.", ".#####.."],
    '9': [".#####..", "##...##.", "##...##.", "##...##.", ".######.", ".....##.", "....##..", ".####..."],
    '!': ["...##...", "...##...", "...##...", "...##...", "...##...", "........", "...##...", "...##..."],
    '.': ["........", "........", "........", "........", "........", "........", "..###...", "..###..."],
    ',': ["........", "........", "........", "........", "........", "...##...", "...##...", "..##...."],
    ':': ["........", "..###...", "..###...", "........", "........", "..###...", "..###...", "........"],
    '-': ["........", "........", "........", "######..", "........", "........", "........", "........"],
    "'": ["...##...", "...##...", "..##....", "........", "........", "........", "........", "........"],
    '?': [".#####..", "##...##.", ".....##.", "....##..", "...##...", "........", "...##...", "...##..."],
    '/': ["......##", ".....##.", "....##..", "...##...", "..##....", ".##.....", "##......", "........"],
    '(': ["....##..", "...##...", "..##....", "..##....", "..##....", "..##....", "...##...", "....##.."],
    ')': ["..##....", "...##...", "....##..", "....##..", "....##..", "....##..", "...##...", "..##...."],
    '+': ["........", "...##...", "...##...", ".######.", "...##...", "...##...", "........", "........"],
    '*': ["........", ".##..##.", "..####..", "########", "..####..", ".##..##.", "........", "........"],
}
for _ch, _g in FONT.items():
    assert len(_g) == 8 and all(len(_r) == 8 for _r in _g), "bad glyph %r" % _ch

_text_cache = {}

def text_surface(text, color):
    """Render a string to a small surface (cached)."""
    key = (text, color)
    surf = _text_cache.get(key)
    if surf is None:
        surf = pygame.Surface((max(1, len(text) * 8), 8), pygame.SRCALPHA)
        for i, ch in enumerate(text.upper()):
            glyph = FONT.get(ch, FONT[' '])
            for r, row in enumerate(glyph):
                for c, px in enumerate(row):
                    if px == '#':
                        surf.set_at((i * 8 + c, r), color)
        _text_cache[key] = surf
    return surf

def draw_text(surf, text, x, y, color, shadow=None):
    if shadow is not None:
        surf.blit(text_surface(text, shadow), (x + 1, y + 1))
    surf.blit(text_surface(text, color), (x, y))

def draw_text_center(surf, text, y, color, scale=1, shadow=None):
    s = text_surface(text, color)
    w, h = s.get_size()
    if scale != 1:
        s = pygame.transform.scale(s, (w * scale, h * scale))
        w, h = s.get_size()
    x = 128 - w // 2
    if shadow is not None:
        sh = text_surface(text, shadow)
        if scale != 1:
            sh = pygame.transform.scale(sh, (w, h))
        surf.blit(sh, (x + scale, y + scale))
    surf.blit(s, (x, y))

# ---------------------------------------------------------------------------
# 2A03-style audio synthesis: pulse x2, triangle, noise (LFSR) - 22050 Hz mono
# ---------------------------------------------------------------------------
SR = 22050
_synth_cache = {}

def _env(i, n, a=0.02, r=0.30):
    na = max(1, int(n * a))
    nr = max(1, int(n * r))
    if i < na:
        return i / na
    if i >= n - nr:
        return max(0.0, (n - i) / nr)
    return 1.0

def synth_pulse(n, freq, vol=0.5, duty=0.5, sweep=0.0):
    key = ('p', n, round(freq, 2), vol, duty, sweep)
    hit = _synth_cache.get(key)
    if hit is not None:
        return hit
    out = array('h', [0]) * n
    phase = 0.0
    for i in range(n):
        f = freq + sweep * (i / n)
        phase += f / SR
        p = phase - int(phase)
        amp = vol if p < duty else -vol
        out[i] = int(amp * _env(i, n) * 32767)
    _synth_cache[key] = out
    return out

def synth_tri(n, freq, vol=0.6, sweep=0.0):
    key = ('t', n, round(freq, 2), vol, sweep)
    hit = _synth_cache.get(key)
    if hit is not None:
        return hit
    out = array('h', [0]) * n
    phase = 0.0
    for i in range(n):
        f = freq + sweep * (i / n)
        phase += f / SR
        p = phase - int(phase)
        amp = vol * (1.0 - 4.0 * abs(p - 0.5))
        out[i] = int(amp * _env(i, n, r=0.15) * 32767)
    _synth_cache[key] = out
    return out

def synth_noise(n, vol=0.4, rate=8, short=False, decay=True):
    key = ('n', n, vol, rate, short, decay)
    hit = _synth_cache.get(key)
    if hit is not None:
        return hit
    out = array('h', [0]) * n
    lfsr = 1
    cnt = 0
    amp = vol
    tap = 6 if short else 1
    for i in range(n):
        if cnt <= 0:
            fb = ((lfsr ^ (lfsr >> tap)) & 1)
            lfsr = (lfsr >> 1) | (fb << 14)
            amp = -vol if (lfsr & 1) else vol
            cnt = rate
        cnt -= 1
        e = (1.0 - i / n) if decay else _env(i, n)
        out[i] = int(amp * e * 32767)
    _synth_cache[key] = out
    return out

def synth_kick(n, vol=0.8):
    key = ('k', n, vol)
    hit = _synth_cache.get(key)
    if hit is not None:
        return hit
    out = array('h', [0]) * n
    phase = 0.0
    for i in range(n):
        f = 150.0 - 110.0 * (i / n)          # pitch drop = punch
        phase += f / SR
        p = phase - int(phase)
        amp = vol * (1.0 - 4.0 * abs(p - 0.5))
        out[i] = int(amp * (1.0 - i / n) * 32767)
    _synth_cache[key] = out
    return out

def seq(*parts):
    out = array('h', [])
    for p in parts:
        out.extend(p)
    return out

def mix(*parts):
    n = max(len(p) for p in parts)
    acc = [0.0] * n
    for p in parts:
        for i, v in enumerate(p):
            acc[i] += v / 32767.0
    peak = max(1e-9, max(abs(v) for v in acc))
    g = min(1.0, 0.9 / peak)
    return array('h', [int(v * g * 32767) for v in acc])

# --- note helpers ----------------------------------------------------------
_SEMI = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
         'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}

def freq_of(note):
    if note[1:2] == '#':
        name, octv = note[:2], int(note[2:])
    else:
        name, octv = note[0], int(note[1:])
    m = 12 * (octv + 1) + _SEMI[name]
    return 440.0 * 2.0 ** ((m - 69) / 12.0)

def oct_up(note):
    return note[:-1] + str(int(note[-1]) + 1)

# --- the title/game music: an original 8-bar chiptune loop -----------------
LEAD_BARS = [
    [(0,1,'C5'), (1,1,'D5'), (2,1,'E5'), (3,1,'G5'), (4,1,'E5'), (5,1,'C5'), (6,1,'D5'), (7,1,'E5')],
    [(0,1,'A4'), (1,1,'C5'), (2,1,'D5'), (3,1,'E5'), (4,1,'D5'), (5,1,'C5'), (6,1,'D5')],
    [(0,1,'E5'), (1,1,'G5'), (2,1,'A5'), (3,1,'G5'), (4,1,'E5'), (5,1,'G5'), (6,1,'A5'), (7,1,'C6')],
    [(0,1,'B5'), (1,1,'A5'), (2,1,'G5'), (3,1,'E5'), (4,2,'D5')],
    [(0,1,'C5'), (1,1,'D5'), (2,1,'E5'), (3,1,'G5'), (4,1,'A5'), (5,1,'G5'), (6,1,'E5'), (7,1,'G5')],
    [(0,1,'A5'), (1,1,'G5'), (2,1,'E5'), (3,1,'D5'), (4,1,'C5'), (5,1,'D5'), (6,1,'E5')],
    [(0,1,'C5'), (1,1,'E5'), (2,1,'G5'), (3,1,'C6'), (4,1,'C6'), (5,1,'B5'), (6,1,'G5'), (7,1,'E5')],
    [(0,1,'D5'), (1,1,'C5'), (2,1,'D5'), (3,1,'E5'), (4,2,'C5')],
]
CHORDS = [('C2', ['C4', 'E4', 'G4']), ('A1', ['A3', 'C4', 'E4']),
          ('E2', ['E4', 'G4', 'B4']), ('G1', ['G3', 'B3', 'D4']),
          ('C2', ['C4', 'E4', 'G4']), ('F1', ['F3', 'A3', 'C4']),
          ('C2', ['C4', 'E4', 'G4']), ('G1', ['G3', 'B3', 'D4'])]
BASS_PAT = [0, None, 0, 1, 0, None, 1, 0]

def build_music():
    bpm = 152.0
    e8 = 60.0 / bpm / 2.0
    n_total = int(SR * e8 * 8 * 8)
    buf = [0.0] * n_total

    def put(start_s, samples):
        i0 = int(start_s * SR)
        for i, v in enumerate(samples):
            if i0 + i < n_total:
                buf[i0 + i] += v / 32767.0

    for bar, notes in enumerate(LEAD_BARS):                    # pulse 1: lead
        base = bar * 8 * e8
        for slot, ln, note in notes:
            n = int(SR * e8 * ln * 0.92)
            put(base + slot * e8, synth_pulse(n, freq_of(note), 0.30, 0.25))
    for bar, (root, tones) in enumerate(CHORDS):               # triangle: bass
        base = bar * 8 * e8
        for slot, p in enumerate(BASS_PAT):
            if p is None:
                continue
            note = root if p == 0 else oct_up(root)
            put(base + slot * e8, synth_tri(int(SR * e8 * 0.90), freq_of(note), 0.55))
    s16 = e8 / 2.0
    for bar, (root, tones) in enumerate(CHORDS):               # pulse 2: arpeggio
        base = bar * 8 * e8
        for s in range(16):
            note = tones[(0, 1, 2, 1)[s % 4]]
            put(base + s * s16, synth_pulse(int(SR * s16 * 0.85), freq_of(note), 0.13, 0.125))
    for bar in range(8):                                       # noise: drums
        base = bar * 8 * e8
        for slot in range(8):
            t = base + slot * e8
            if slot in (0, 4):
                put(t, synth_kick(int(SR * 0.10), 0.80))
            if slot in (2, 6):
                put(t, synth_noise(int(SR * 0.11), 0.30, rate=24))
            put(t, synth_noise(int(SR * 0.03), 0.09 if slot % 2 else 0.05, rate=5, short=True))
    peak = max(1e-9, max(abs(v) for v in buf))
    g = 0.85 / peak
    return array('h', [int(v * g * 32767) for v in buf])

def build_sfx():
    ms = lambda v: int(SR * v / 1000.0)
    sfx = {}
    sfx['paddle'] = synth_pulse(ms(55), 480, 0.45, 0.5)
    sfx['wall']   = synth_pulse(ms(55), 260, 0.35, 0.5)
    sfx['shrink'] = synth_pulse(ms(100), 600, 0.40, 0.5, sweep=-350)
    sfx['launch'] = synth_pulse(ms(110), 250, 0.40, 0.25, sweep=650)
    sfx['die']    = synth_pulse(ms(450), 500, 0.45, 0.5, sweep=-410)
    sfx['silver'] = mix(synth_pulse(ms(40), 1400, 0.35, 0.125),
                        synth_noise(ms(40), 0.28, rate=6, short=True))
    sfx['gold']   = mix(synth_pulse(ms(100), 130, 0.45, 0.5),
                        synth_noise(ms(60), 0.22, rate=18))
    sfx['break']  = mix(synth_noise(ms(90), 0.45, rate=30),
                        synth_pulse(ms(90), 800, 0.28, 0.25, sweep=-500))
    for row in range(8):                                       # pitch rises with row value
        sfx['brick%d' % row] = synth_pulse(ms(70), 520 + row * 55, 0.42, 0.25)
    j = lambda f, d, duty=0.5, v=0.42: synth_pulse(ms(d), f, v, duty)
    sfx['start'] = seq(j(freq_of('C5'), 90), j(freq_of('E5'), 90),
                       j(freq_of('G5'), 90), j(freq_of('C6'), 190))
    sfx['clear'] = seq(j(freq_of('C5'), 75, 0.25), j(freq_of('E5'), 75, 0.25),
                       j(freq_of('G5'), 75, 0.25), j(freq_of('C6'), 75, 0.25),
                       j(freq_of('E6'), 75, 0.25), j(freq_of('G6'), 220, 0.25))
    sfx['over']  = seq(j(freq_of('A4'), 170), j(freq_of('G4'), 170),
                       j(freq_of('E4'), 170), j(freq_of('C4'), 340))
    return sfx

# ---------------------------------------------------------------------------
# Levels - 15 columns x up to 8 rows, Arkanoid-style color codes
#   W white  O orange  L light blue  G green  R red  B blue  P purple  Y yellow
#   S silver (2 hits)  X gold (unbreakable)  . empty
# ---------------------------------------------------------------------------
LEVELS = [
    ("CLASSIC", [
        "RRRRRRRRRRRRRRR",
        "OOOOOOOOOOOOOOO",
        "YYYYYYYYYYYYYYY",
        "GGGGGGGGGGGGGGG",
        "LLLLLLLLLLLLLLL",
        "BBBBBBBBBBBBBBB",
        "PPPPPPPPPPPPPPP",
        "WWWWWWWWWWWWWWW",
    ]),
    ("CHECKERS", [
        "R.R.R.R.R.R.R.R",
        ".W.W.W.W.W.W.W.",
        "L.L.L.L.L.L.L.L",
        ".G.G.G.G.G.G.G.",
        "O.O.O.O.O.O.O.O",
        ".Y.Y.Y.Y.Y.Y.Y.",
    ]),
    ("FORTRESS", [
        "X.............X",
        "XSSSSSSSSSSSSSX",
        "X.............X",
        "XRRRRRRRRRRRRRX",
        "XYYYYYYYYYYYYYX",
        "X.............X",
        "XGGGGGGGGGGGGGX",
        "XWWWWWWWWWWWWWX",
    ]),
    ("PYRAMID", [
        ".......S.......",
        "......SWS......",
        ".....SWYWS.....",
        "....SWYYYWS....",
        "...SWYYYYYWS...",
        "..SWYYYYYYYWS..",
        ".SWYYYYYYYYYWS.",
        "SWYYYYYYYYYYYWS",
    ]),
    ("INVASION", [
        "..X.........X..",
        "...X.......X...",
        "..WWWWWWWWWWW..",
        ".WW.WWWWWWW.WW.",
        "WWWWWWWWWWWWWWW",
        "W.SSSSSSSSSSS.W",
        "W.W.........W.W",
        "...WW.....WW...",
    ]),
    ("COLUMNS", [
        "S.S.S.S.S.S.S.S",
        "W.W.W.W.W.W.W.W",
        "X...X...X...X..",
        "R.R.R.R.R.R.R.R",
        "X...X...X...X..",
        "O.O.O.O.O.O.O.O",
        "X...X...X...X..",
        "Y.Y.Y.Y.Y.Y.Y.Y",
    ]),
]

# style: (main color, highlight, shadow, points, hits)
BRICK_STYLE = {
    'W': (PAL[16], PAL[32], PAL[0],  50, 1),
    'O': (PAL[39], PAL[55], PAL[23], 60, 1),
    'L': (PAL[44], PAL[60], PAL[28], 70, 1),
    'G': (PAL[41], PAL[57], PAL[25], 80, 1),
    'R': (PAL[38], PAL[54], PAL[22], 90, 1),
    'B': (PAL[33], PAL[49], PAL[1], 100, 1),
    'P': (PAL[35], PAL[51], PAL[3], 110, 1),
    'Y': (PAL[56], PAL[32], PAL[24], 120, 1),
    'S': (PAL[61], PAL[32], PAL[45], 200, 2),
    'X': (PAL[39], PAL[56], PAL[23], 0, 999),
}

# ---------------------------------------------------------------------------
# Playfield geometry (in 256x240 "NES pixels")
# ---------------------------------------------------------------------------
W, H = 256, 240
WALL_L, WALL_R = 8, 248          # inner edges of side walls
WALL_T = 16                      # inner edge of top wall (HUD sits above)
BRICK_W, BRICK_H = 16, 8
BRICK_TOP = 40
PADDLE_Y = 222
PADDLE_W, PADDLE_W_SMALL = 32, 22
PADDLE_H = 6
PADDLE_SPEED = 4.6
BALL = 4                         # ball sprite size
FPS = 60


class Brick:
    __slots__ = ('x', 'y', 'ch', 'hits', 'alive', 'row')

    def __init__(self, x, y, ch, row):
        self.x, self.y, self.ch, self.row = x, y, ch, row
        self.hits = BRICK_STYLE[ch][4]
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, BRICK_W, BRICK_H)


class Game:
    def __init__(self, scale=3, audio=True):
        if audio:
            pygame.mixer.pre_init(SR, -16, 1, 512)
        pygame.init()
        self.audio_ok = False
        if audio:
            try:
                if pygame.mixer.get_init() is None:
                    pygame.mixer.init(SR, -16, 1, 512)
                pygame.mixer.set_num_channels(8)
                self.audio_ok = True
            except pygame.error:
                self.audio_ok = False

        self.scale = scale
        self.screen = pygame.display.set_mode((W * scale, H * scale))
        pygame.display.set_caption("FAMICOM BREAKOUT")
        pygame.mouse.set_visible(False)
        self.frame = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()

        # CRT scanline overlay
        self.scan = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(1, H, 2):
            pygame.draw.line(self.scan, (0, 0, 0, 72), (0, y), (W, y))
        self.scan_on = True

        # faint starfield backdrop
        rnd = random.Random(1986)
        self.stars = [(rnd.randrange(WALL_L + 2, WALL_R - 2),
                       rnd.randrange(WALL_T + 4, H - 4),
                       rnd.choice((PAL[45], PAL[13], PAL[0]))) for _ in range(26)]

        # audio
        self.sfx = {}
        self.music = None
        self.music_ch = None
        self.music_on = False
        if self.audio_ok:
            print("Generating NES chiptune audio...")
            self.sfx = {k: pygame.mixer.Sound(buffer=v.tobytes())
                        for k, v in build_sfx().items()}
            self.music = pygame.mixer.Sound(buffer=build_music().tobytes())
            self.music_ch = None

        self.hi = 0
        self.frame_count = 0
        self.last_mouse_x = -1
        self.state = 'title'
        self.score = self.lives = self.level = 0
        self.bricks = []
        self.running = True

    # ------------------------------------------------------------------ audio
    def play(self, name):
        if self.audio_ok and name in self.sfx:
            self.sfx[name].play()

    def toggle_music(self):
        if not self.audio_ok or self.music is None:
            return
        self.music_on = not self.music_on
        if self.music_on:
            self.music_ch = self.music.play(loops=-1)
            if self.music_ch:
                self.music_ch.set_volume(0.55)
        elif self.music_ch:
            self.music_ch.stop()

    # --------------------------------------------------------------- control
    def start_game(self):
        self.score, self.lives, self.level = 0, 3, 1
        self.load_level()
        self.new_serve(banner=True)
        self.play('start')

    def to_title(self):
        self.state = 'title'
        self.bricks = []

    def load_level(self):
        name, rows = LEVELS[(self.level - 1) % len(LEVELS)]
        self.level_name = name
        self.bricks = []
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch != '.':
                    self.bricks.append(Brick(WALL_L + c * BRICK_W,
                                             BRICK_TOP + r * BRICK_H, ch, r))
        self.base_speed = min(3.2, 2.3 + 0.12 * (self.level - 1))

    def new_serve(self, banner=False):
        self.paddle_w = PADDLE_W
        self.paddle_x = (W - self.paddle_w) / 2.0
        self.bx = W / 2.0
        self.by = PADDLE_Y - BALL
        self.bvx = self.bvy = 0.0
        self.bspeed = self.base_speed
        self.hits = 0
        self.state = 'serve'
        self.round_timer = 110 if banner else 0

    def try_launch(self):
        if self.state != 'serve':
            return
        ang = math.radians(random.uniform(32, 56)) * random.choice((-1, 1))
        self.bvx = self.bspeed * math.sin(ang)
        self.bvy = -self.bspeed * math.cos(ang)
        self.state = 'play'
        self.play('launch')

    def set_speed(self, s):
        cur = math.hypot(self.bvx, self.bvy) or 1.0
        self.bspeed = s
        self.bvx *= s / cur
        self.bvy *= s / cur

    # ---------------------------------------------------------------- events
    def events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key
            if k == pygame.K_ESCAPE:
                return False
            if k == pygame.K_F1:
                self.scan_on = not self.scan_on
            elif k == pygame.K_m:
                self.toggle_music()
            elif k == pygame.K_p:
                if self.state == 'play':
                    self.state = 'pause'
                    if self.music_ch:
                        self.music_ch.pause()
                elif self.state == 'pause':
                    self.state = 'play'
                    if self.music_ch and self.music_on:
                        self.music_ch.unpause()
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.state == 'title':
                    self.start_game()
                elif self.state == 'serve':
                    self.try_launch()
                elif self.state == 'clear':
                    self.clear_timer = 1
                elif self.state == 'over':
                    self.to_title()
        return True

    # ---------------------------------------------------------------- update
    def update(self):
        self.frame_count += 1
        if self.state in ('serve', 'play'):
            self.move_paddle()
        if self.state == 'serve':
            if self.round_timer > 0:
                self.round_timer -= 1
            self.bx = self.paddle_x + self.paddle_w / 2.0
            self.by = PADDLE_Y - BALL
        elif self.state == 'play':
            self.update_ball()
        elif self.state == 'clear':
            self.clear_timer -= 1
            if self.clear_timer <= 0:
                self.level += 1
                self.load_level()
                self.new_serve(banner=True)

    def move_paddle(self):
        keys = pygame.key.get_pressed()
        dx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PADDLE_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PADDLE_SPEED
        mx = pygame.mouse.get_pos()[0] / self.scale
        if abs(mx - self.last_mouse_x) > 1.0:
            self.paddle_x = mx - self.paddle_w / 2.0
            self.last_mouse_x = mx
        self.paddle_x += dx
        self.paddle_x = max(WALL_L, min(WALL_R - self.paddle_w, self.paddle_x))

    def update_ball(self):
        px, py = self.bx, self.by
        self.bx += self.bvx
        self.by += self.bvy

        # walls
        if self.bx < WALL_L:
            self.bx, self.bvx = WALL_L, abs(self.bvx)
            self.play('wall')
        elif self.bx > WALL_R - BALL:
            self.bx, self.bvx = WALL_R - BALL, -abs(self.bvx)
            self.play('wall')
        if self.by < WALL_T:
            self.by, self.bvy = WALL_T, abs(self.bvy)
            self.play('wall')
            if self.paddle_w != PADDLE_W_SMALL:     # classic Breakout: paddle shrinks
                self.paddle_w = PADDLE_W_SMALL      # once the ball reaches the top
                self.play('shrink')

        # lost ball
        if self.by > H + 8:
            self.lives -= 1
            self.play('die')
            if self.lives <= 0:
                self.hi = max(self.hi, self.score)
                self.state = 'over'
                self.play('over')
            else:
                self.new_serve()
            return

        # paddle
        if self.bvy > 0 and py + BALL <= PADDLE_Y + 2:
            pr = pygame.Rect(self.paddle_x, PADDLE_Y, self.paddle_w, PADDLE_H)
            if pr.colliderect(pygame.Rect(self.bx, self.by, BALL, BALL)):
                rel = (self.bx + BALL / 2 - pr.centerx) / (self.paddle_w / 2.0)
                rel = max(-1.0, min(1.0, rel))
                ang = rel * math.radians(62)
                self.bvx = self.bspeed * math.sin(ang)
                self.bvy = -self.bspeed * math.cos(ang)
                self.by = PADDLE_Y - BALL
                self.play('paddle')

        # bricks (one per frame, like the original hardware would)
        ball_rect = pygame.Rect(self.bx, self.by, BALL, BALL)
        for b in self.bricks:
            if not b.alive or not ball_rect.colliderect(b.rect):
                continue
            r = b.rect
            from_left = (px + BALL) - r.left
            from_right = r.right - px
            from_top = (py + BALL) - r.top
            from_bottom = r.bottom - py
            m = min(from_left, from_right, from_top, from_bottom)
            if m == from_left:
                self.bvx, self.bx = -abs(self.bvx), r.left - BALL
            elif m == from_right:
                self.bvx, self.bx = abs(self.bvx), r.right
            elif m == from_top:
                self.bvy, self.by = -abs(self.bvy), r.top - BALL
            else:
                self.bvy, self.by = abs(self.bvy), r.bottom
            self.hit_brick(b)
            break

        # keep the ball from going too horizontal
        if self.bvy and abs(self.bvy) < 0.30 * self.bspeed:
            self.bvy = math.copysign(0.30 * self.bspeed, self.bvy)
            self.bvx = math.copysign(math.sqrt(self.bspeed ** 2 - self.bvy ** 2), self.bvx)

    def hit_brick(self, b):
        if b.ch == 'X':
            self.play('gold')
            return
        b.hits -= 1
        if b.hits > 0:
            self.play('silver')
            return
        b.alive = False
        pts = BRICK_STYLE[b.ch][3]
        self.score += pts
        self.hits += 1
        self.play('break')
        self.play('brick%d' % min(7, b.row))
        # classic Breakout speed-ups at 4 / 12 / 24 brick hits
        if self.hits == 4:
            self.set_speed(max(self.bspeed, 2.9))
        elif self.hits == 12:
            self.set_speed(max(self.bspeed, 3.3))
        elif self.hits == 24:
            self.set_speed(min(4.2, max(self.bspeed, 3.7)))
        if not any(x.alive and x.ch != 'X' for x in self.bricks):
            self.score += 100 * self.level
            self.hi = max(self.hi, self.score)
            self.state = 'clear'
            self.clear_timer = 200
            self.play('clear')

    # ------------------------------------------------------------------ draw
    def draw(self):
        f = self.frame
        f.fill(BLACK)
        # starfield
        for i, (x, y, c) in enumerate(self.stars):
            if (self.frame_count // 24 + i) % 4:
                f.set_at((x, y), c)
        self.draw_hud(f)
        self.draw_walls(f)
        if self.state == 'title':
            self.draw_title(f)
        else:
            for b in self.bricks:
                if b.alive:
                    self.draw_brick(f, b)
            self.draw_paddle(f)
            if self.state in ('serve', 'play', 'pause'):
                self.draw_ball(f)
            if self.state == 'serve' and self.round_timer > 0:
                draw_text_center(f, "ROUND %d" % self.level, 96, WHITE, 2, DGRAY)
                draw_text_center(f, self.level_name, 122, YELLOW, 1, DGRAY)
            elif self.state == 'serve':
                if (self.frame_count // 30) % 2:
                    draw_text_center(f, "READY!", 120, WHITE, 1, DGRAY)
                draw_text_center(f, "PRESS SPACE", 150, SKY, 1)
            elif self.state == 'pause':
                draw_text_center(f, "PAUSE", 116, WHITE, 2, DGRAY)
            elif self.state == 'clear':
                draw_text_center(f, "ROUND CLEAR!", 96, YELLOW, 2, DGRAY)
                draw_text_center(f, "BONUS %d" % (100 * self.level), 126, WHITE, 1)
            elif self.state == 'over':
                draw_text_center(f, "GAME OVER", 84, RED, 2, DGRAY)
                draw_text_center(f, "SCORE %06d" % self.score, 118, WHITE, 1)
                if self.score >= self.hi and self.score > 0:
                    draw_text_center(f, "NEW HI-SCORE!", 134, YELLOW, 1)
                if (self.frame_count // 30) % 2:
                    draw_text_center(f, "PRESS ENTER", 164, SKY, 1)
        if self.scan_on:
            f.blit(self.scan, (0, 0))
        pygame.transform.scale(f, self.screen.get_size(), self.screen)

    def draw_hud(self, f):
        draw_text(f, "SC %06d" % self.score, 8, 0, WHITE)
        draw_text(f, "HI %06d" % max(self.hi, self.score), 88, 0, RED)
        if self.state != 'title':
            draw_text(f, "LV %02d" % self.level, 176, 0, SKY)
            for i in range(min(self.lives, 5)):
                x = 218 + i * 7
                pygame.draw.rect(f, WHITE, (x, 2, 4, 4))

    def draw_walls(self, f):
        for x in (0, W - 8):                       # side walls with rivets
            pygame.draw.rect(f, LGRAY, (x, 8, 8, H - 8))
            pygame.draw.rect(f, WHITE, (x if x == 0 else x, 8, 8, 1))
            edge = 7 if x == 0 else 0
            pygame.draw.line(f, DGRAY, (x + edge, 8), (x + edge, H - 1))
            for y in range(16, H, 16):
                f.set_at((x + 3, y), DGRAY)
                f.set_at((x + 4, y), DGRAY)
        pygame.draw.rect(f, LGRAY, (0, 8, W, 8))   # top wall
        pygame.draw.line(f, DGRAY, (0, 15), (W - 1, 15))
        pygame.draw.line(f, WHITE, (0, 8), (W - 1, 8))

    def draw_brick(self, f, b):
        main, hi, lo, _, _ = BRICK_STYLE[b.ch]
        r = b.rect
        if b.ch == 'S' and b.hits == 1:            # damaged silver
            main, hi, lo = lo, main, PAL[13]
        pygame.draw.rect(f, main, r)
        pygame.draw.line(f, hi, r.topleft, (r.right - 1, r.top))
        pygame.draw.line(f, hi, r.topleft, (r.left, r.bottom - 1))
        pygame.draw.line(f, lo, (r.left, r.bottom - 1), (r.right - 1, r.bottom - 1))
        pygame.draw.line(f, lo, (r.right - 1, r.top), (r.right - 1, r.bottom - 1))
        pygame.draw.rect(f, BLACK, r, 1)
        if b.ch == 'X':                            # gold sparkle
            f.set_at((r.x + 4, r.y + 3), PAL[56])
            f.set_at((r.x + 11, r.y + 5), PAL[56])
        if b.ch == 'S' and b.hits == 1:            # crack
            f.set_at((r.x + 7, r.y + 2), BLACK)
            f.set_at((r.x + 8, r.y + 3), BLACK)
            f.set_at((r.x + 7, r.y + 4), BLACK)

    def draw_paddle(self, f):
        x, y, w = int(self.paddle_x), PADDLE_Y, self.paddle_w
        pygame.draw.rect(f, BLACK, (x, y, w, PADDLE_H))
        pygame.draw.rect(f, LGRAY, (x + 1, y + 1, w - 2, PADDLE_H - 2))
        pygame.draw.line(f, WHITE, (x + 1, y + 1), (x + w - 2, y + 1))
        pygame.draw.line(f, DGRAY, (x + 1, y + PADDLE_H - 2), (x + w - 2, y + PADDLE_H - 2))
        pygame.draw.rect(f, RED, (x + 1, y + 1, 3, PADDLE_H - 2))
        pygame.draw.rect(f, RED, (x + w - 4, y + 1, 3, PADDLE_H - 2))

    def draw_ball(self, f):
        x, y = int(self.bx), int(self.by)
        for dx, dy in ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)):
            f.set_at((x + dx, y + dy), WHITE)
        f.set_at((x + 1, y + 1), PAL[48])

    def draw_title(self, f):
        # decorative brick strip
        demo = "ROWGLBPY"
        for i, ch in enumerate(demo):
            bb = Brick(48 + i * 16, 128, ch, 0)
            self.draw_brick(f, bb)
        draw_text_center(f, "FAMICOM", 34, RED, 2, DGRAY)
        draw_text_center(f, "BREAKOUT", 62, WHITE, 3, DGRAY)
        draw_text_center(f, "HI-SCORE %06d" % self.hi, 152, YELLOW, 1)
        if (self.frame_count // 30) % 2:
            draw_text_center(f, "PRESS ENTER", 176, SKY, 1)
        draw_text_center(f, "(C) 2026 KIMISOFT", 208, GRAY, 1)

    # ------------------------------------------------------------------ loop
    def run(self):
        while self.running:
            self.running = self.events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)                   # hard 60 FPS, NES vblank style
        pygame.quit()


def main():
    scale = 3
    if len(sys.argv) > 1:
        try:
            scale = max(1, min(4, int(sys.argv[1])))
        except ValueError:
            pass
    Game(scale=scale).run()


if __name__ == '__main__':
    main()
