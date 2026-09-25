# Sounds for the strange events (Succubi Server v1.1.15), synthesized from code: noise, filters, formant voices,
# reverb. Mono 22.05 kHz Ogg Vorbis (mono so Bedrock places them in 3D). Writes the .ogg files and prints
# sound_definitions entries as JSON (sounds.json next to this script).
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

RP = sys.argv[1] if len(sys.argv) > 1 else "Succubi Server RP"
OUT = os.path.join(RP, "sounds/succubi/ev")
os.makedirs(OUT, exist_ok=True)
SR = 22050
rng = np.random.default_rng(1333)
DEFS = {}


def t(dur):
    return np.arange(int(dur * SR)) / SR


def white(dur):
    return rng.standard_normal(int(dur * SR))


def brown(dur):
    x = np.cumsum(white(dur))
    x = signal.lfilter([1, -1], [1, -0.995], x)
    return x / (np.abs(x).max() + 1e-9)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(0.99, hi / (SR / 2))], "band")
    return signal.lfilter(b, a, x)


def lp(x, f, order=2):
    b, a = signal.butter(order, min(0.99, f / (SR / 2)), "low")
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def env(n, a=0.005, d=0.1, curve=4.0):
    """attack then exponential decay over n samples"""
    tt = np.arange(n) / SR
    e = np.minimum(1, tt / max(a, 1e-4)) * np.exp(-np.maximum(0, tt - a) * curve / max(d, 1e-3))
    return e


def adsr(n, a, s_level, r):
    tt = np.arange(n) / SR
    dur = n / SR
    e = np.minimum(1, tt / max(a, 1e-4))
    e = np.where(tt > dur - r, e * np.clip((dur - tt) / r, 0, 1), e)
    return e * s_level


def place(buf, x, at):
    i = int(at * SR)
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[: j - i]
    return buf


def reverb(x, size=1.2, wet=0.35, damp=3000):
    ir_n = int(size * SR)
    ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR * (6.9 / size))
    ir = lp(ir, damp)
    ir[0] = 0
    y = signal.fftconvolve(x, ir)[: len(x) + ir_n]
    y = y / (np.abs(y).max() + 1e-9) * (np.abs(x).max() + 1e-9)
    out = np.zeros(len(y))
    out[: len(x)] += x * (1 - wet)
    out += y * wet
    return out


def glottal(f0, dur, jitter=0.01, breath=0.1):
    """pulse train following f0 (array or number), plus breath noise"""
    n = int(dur * SR)
    f = np.full(n, f0, float) if np.isscalar(f0) else np.interp(np.arange(n), np.linspace(0, n, len(f0)), f0)
    f = f * (1 + jitter * rng.standard_normal(n).cumsum() / math.sqrt(n) * 3)
    ph = np.cumsum(f / SR)
    saw = 2 * (ph % 1) - 1
    src = lp(saw, 2800) + breath * rng.standard_normal(n)
    return src


FORMANTS = {
    "a": [(800, 80), (1200, 90), (2500, 120)],
    "i": [(300, 60), (2300, 100), (3000, 120)],
    "u": [(320, 60), (800, 80), (2400, 120)],
    "m": [(280, 60), (1000, 150), (2300, 200)],
    "o": [(500, 70), (850, 80), (2500, 120)],
    "e": [(450, 70), (1900, 100), (2600, 120)],
}


def formant(src, vowel, shift=1.0):
    out = np.zeros_like(src)
    for i, (f, bw) in enumerate(FORMANTS[vowel]):
        f *= shift
        r = math.exp(-math.pi * bw / SR)
        w = 2 * math.pi * f / SR
        b = [1 - r]
        a = [1, -2 * r * math.cos(w), r * r]
        out += signal.lfilter(b, a, src) * (1.0, 0.6, 0.3)[i]
    return out


def norm(x, peak=0.9):
    return x / (np.abs(x).max() + 1e-9) * peak


def fade(x, fi=0.005, fo=0.05):
    n = len(x)
    a = min(n, int(fi * SR))
    b = min(n, int(fo * SR))
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def write(name, x, peak=0.9):
    x = fade(norm(np.asarray(x, float), peak))
    sf.write(os.path.join(OUT, name + ".ogg"), x.astype(np.float32), SR, format="OGG", subtype="VORBIS")


def define(event, files, volume=1.0, category="hostile", max_distance=None, pitch=None, stream=False):
    sounds = []
    for f in files:
        s = {"name": f"sounds/succubi/ev/{f}", "volume": volume}
        if pitch:
            s["pitch"] = pitch
        if stream:
            s["stream"] = True
        sounds.append(s)
    d = {"category": category, "sounds": sounds}
    if max_distance:
        d["max_distance"] = max_distance
        d["min_distance"] = 1.0
    DEFS[event] = d


# ---------------------------------------------------------------- footsteps
def step_wet(i):
    n = 0.32
    x = bp(white(n), 250, 1800) * env(int(n * SR), 0.004, 0.08)
    squelch = np.sin(2 * np.pi * np.cumsum(np.linspace(420 + i * 40, 150, int(0.12 * SR))) / SR) * env(int(0.12 * SR), 0.002, 0.05)
    x = place(x, squelch * 0.6, 0.01)
    drip = np.sin(2 * np.pi * np.cumsum(np.linspace(1400, 2200, int(0.04 * SR))) / SR) * env(int(0.04 * SR), 0.001, 0.02)
    x = place(x, drip * 0.25, 0.16 + i * 0.02)
    x = x + lp(white(n), 180) * env(int(n * SR), 0.003, 0.05) * 1.5
    return reverb(x, 0.4, 0.15)


def step_child(i):
    n = 0.2
    x = bp(white(n), 900 + i * 150, 4000) * env(int(n * SR), 0.002, 0.03)
    thump = np.sin(2 * np.pi * (160 + i * 20) * t(n)) * env(int(n * SR), 0.002, 0.03)
    return reverb(x * 0.7 + thump * 0.5, 0.3, 0.1)


def step_heavy(i):
    n = 0.7
    f = np.linspace(90 - i * 8, 38, int(n * SR))
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(int(n * SR), 0.004, 0.25)
    grit = bp(white(n), 120, 900) * env(int(n * SR), 0.002, 0.06)
    creak = bp(white(n), 500, 700) * env(int(n * SR), 0.1, 0.3) * 0.2
    return reverb(boom + grit * 0.6 + creak, 0.9, 0.3, 1500)


def roof_step(i):
    x = step_heavy(i)
    n = len(x)
    wood = np.zeros(n)
    fc = 300 + i * 40
    for k, (f, g) in enumerate(((fc, 1), (fc * 2.3, 0.5), (fc * 3.9, 0.3))):
        wood += g * np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, 0.003, 0.12 + 0.05 * k)
    sprinkle = bp(white(n / SR), 3000, 8000) * np.exp(-np.arange(n) / SR * 3) * (rng.random(n) > 0.97) * 3
    return lp(x, 900) * 1.2 + wood * 0.25 + sprinkle * 0.3


# ---------------------------------------------------------------- hands, drags, scratches
def hand_slap(i):
    n = 0.45
    x = bp(white(n), 400, 5000) * env(int(n * SR), 0.001, 0.03)
    wet = bp(white(n), 200, 1200) * env(int(n * SR), 0.01, 0.15) * 0.5
    thud = np.sin(2 * np.pi * 110 * t(n)) * env(int(n * SR), 0.002, 0.06)
    return reverb(x + wet + thud * 0.6, 0.6 + i * 0.2, 0.25)


def drag(i):
    n = 2.6
    base = lp(brown(n), 700) * 1.2 + bp(white(n), 900, 2500) * 0.12
    # uneven pulls: something heavy pulled in jerks
    pulls = np.zeros(int(n * SR))
    tt = 0.0
    while tt < n - 0.3:
        ln = rng.uniform(0.35, 0.7)
        seg = np.sin(np.linspace(0, np.pi, int(ln * SR))) ** 0.7
        pulls = place(pulls, seg, tt)
        tt += ln + rng.uniform(0.05, 0.25)
    x = base * pulls
    return reverb(x, 0.8, 0.25, 1800)


def scratch(i):
    n = 1.2 + i * 0.2
    x = np.zeros(int(n * SR))
    tt = 0.02
    while tt < n - 0.25:
        ln = rng.uniform(0.18, 0.4)
        seg = bp(white(ln), 1800, 6500) * (0.4 + 0.6 * (rng.random(int(ln * SR)) > 0.6))
        seg *= np.sin(np.linspace(0, np.pi, len(seg))) ** 0.5
        # fingernail squeak
        f = np.linspace(rng.uniform(2200, 3200), rng.uniform(1400, 2000), len(seg))
        seg += 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, len(seg)))
        x = place(x, seg, tt)
        tt += ln + rng.uniform(0.05, 0.2)
    wood = bp(white(n), 150, 600) * 0.3 * (np.abs(x) > 0.1)
    return reverb(x + wood, 0.5, 0.2)


def scrape():
    # a finger dragging through ash: dry, soft, grainy
    n = 2.4
    x = bp(white(n), 1200, 5000) * (0.3 + 0.7 * (rng.random(int(n * SR)) > 0.5))
    e = np.zeros(int(n * SR))
    tt = 0.05
    while tt < n - 0.3:
        ln = rng.uniform(0.2, 0.45)
        e = place(e, np.sin(np.linspace(0, np.pi, int(ln * SR))), tt)
        tt += ln + rng.uniform(0.02, 0.15)
    return reverb(x * e, 0.4, 0.15)


def ash_scatter():
    n = 1.3
    x = bp(white(n), 2000, 9000) * env(int(n * SR), 0.05, 0.5)
    whoosh = bp(white(n), 300, 1500) * np.sin(np.linspace(0, np.pi, int(n * SR))) * 0.5
    return reverb(x + whoosh, 0.7, 0.3)


def hair():
    n = 1.4
    x = bp(white(n), 3000, 9000) * np.sin(np.linspace(0, np.pi, int(n * SR))) ** 2
    x *= 0.5 + 0.5 * np.sin(2 * np.pi * 7 * t(n)) ** 2
    return reverb(x, 0.5, 0.2)


def rustle(i):
    n = 0.9
    x = bp(white(n), 1500, 7000) * (rng.random(int(n * SR)) > 0.4)
    e = np.zeros(int(n * SR))
    for _ in range(6):
        e = place(e, env(int(0.15 * SR), 0.005, 0.06), rng.uniform(0, n - 0.2))
    return reverb(x * e, 0.4, 0.15)


def exhale():
    n = 2.2
    x = bp(white(n), 300, 2800) * np.sin(np.linspace(0, np.pi, int(n * SR))) ** 1.5
    x = formant(x, "a", 0.8) * 0.6 + x * 0.4
    growl = glottal(62, n, 0.02, 0.0) * np.sin(np.linspace(0, np.pi, int(n * SR))) ** 3
    return reverb(x + formant(growl, "o", 0.8) * 0.12, 0.6, 0.2)


def breath_close(i):
    # slow in-out breathing right behind the ear
    n = 3.4
    x = np.zeros(int(n * SR))
    inh = bp(white(1.2), 700, 4000) * np.sin(np.linspace(0, np.pi, int(1.2 * SR))) ** 2 * 0.6
    exh = bp(white(1.6), 250, 2200) * np.sin(np.linspace(0, np.pi, int(1.6 * SR))) ** 1.2
    exh = formant(exh, "u" if i else "a", 0.9) * 0.5 + exh * 0.5
    x = place(x, inh, 0.05)
    x = place(x, exh, 1.4)
    wet = bp(white(0.05), 1500, 4000) * env(int(0.05 * SR), 0.001, 0.01) * 0.3
    x = place(x, wet, 1.35)
    return x


def gasp():
    n = 0.7
    x = bp(white(n), 800, 5000) * env(int(n * SR), 0.02, 0.2)
    return reverb(formant(x, "a", 1.2) + x * 0.3, 0.5, 0.2)


def sniff():
    n = 1.6
    x = np.zeros(int(n * SR))
    for k in range(4):
        s = bp(white(0.12), 1500, 6000) * np.sin(np.linspace(0, np.pi, int(0.12 * SR)))
        x = place(x, s, 0.1 + k * 0.2 + (0.35 if k == 3 else 0))
    snort = formant(glottal(55, 0.4, 0.03, 0.4), "o", 0.7) * env(int(0.4 * SR), 0.02, 0.15)
    x = place(x, snort * 0.5, 1.05)
    return reverb(x, 0.5, 0.2)


def chain(i):
    n = 1.8
    x = lp(brown(n), 1200) * 0.4 * np.sin(np.linspace(0, np.pi, int(n * SR))) ** 0.5
    for _ in range(int(rng.integers(9, 15))):
        at = rng.uniform(0, n - 0.3)
        f0 = rng.uniform(1800, 3200)
        ln = int(0.25 * SR)
        clink = np.zeros(ln)
        for m in (1, 2.76, 5.4, 8.93):
            clink += np.sin(2 * np.pi * f0 * m * np.arange(ln) / SR) / m
        x = place(x, clink * env(ln, 0.0005, 0.05) * rng.uniform(0.2, 0.6), at)
    return reverb(x, 0.9, 0.3, 4000)


# ---------------------------------------------------------------- voices (synthesized, crude on purpose)
def giggle(i):
    n = 1.5
    x = np.zeros(int(n * SR))
    base = 430 + i * 60
    for k in range(5):
        ln = 0.14
        f0 = base * (1.1 - k * 0.04) * np.array([1.08, 0.94])
        src = glottal(f0, ln, 0.02, 0.35)
        syl = formant(src, "i", 1.25) * env(int(ln * SR), 0.01, 0.08)
        hhh = bp(white(0.05), 2000, 7000) * env(int(0.05 * SR), 0.002, 0.03) * 0.4
        x = place(x, hhh, 0.1 + k * 0.19)
        x = place(x, syl, 0.13 + k * 0.19)
    return reverb(x, 1.1, 0.35)


LULLABY = [  # (semitones from the root, beats) - an invented, slow minor tune
    (7, 1), (5, 1), (3, 2), (5, 1), (3, 1), (0, 2),
    (3, 1), (5, 1), (7, 1), (8, 1), (7, 3), (0, 1),
    (7, 1), (5, 1), (3, 2), (2, 1), (0, 1), (-2, 2),
    (0, 1), (2, 1), (3, 1), (2, 1), (0, 4),
]


def lullaby_parts():
    # a child's hum ("mmm") with vibrato, cut into 8 phrases so it can move around the player
    beat = 0.52
    root = 392.0
    notes = []
    for semis, beats in LULLABY:
        notes.append((root * 2 ** (semis / 12), beats * beat))
    n = sum(int(d * SR) for _, d in notes)
    total = n / SR
    f0 = np.zeros(n)
    amp = np.zeros(n)
    pos = 0
    for f, d in notes:
        m = int(d * SR)
        seg = np.full(m, f)
        glide = min(m, int(0.06 * SR))
        if pos > 0:
            seg[:glide] = np.linspace(f0[pos - 1], f, glide)
        f0[pos:pos + m] = seg
        amp[pos:pos + m] = np.minimum(1, np.arange(m) / (0.05 * SR)) * (0.85 + 0.15 * np.exp(-np.arange(m) / SR * 2))
        pos += m
    vib = 1 + 0.012 * np.sin(2 * np.pi * 5.2 * np.arange(n) / SR)
    src = glottal(f0 * vib, total, 0.004, 0.08)
    voice = formant(src, "m", 1.2) * 0.8 + formant(src, "u", 1.25) * 0.4
    voice *= amp
    # warble like an old recording
    voice = voice * (1 + 0.1 * np.sin(2 * np.pi * 0.4 * np.arange(n) / SR))
    voice = reverb(voice, 1.6, 0.4)
    cut = len(voice) // 8
    parts = []
    for k in range(8):
        seg = voice[k * cut:(k + 1) * cut + int(0.15 * SR)].copy()
        parts.append(seg)
    return parts


def sob(i):
    n = 2.8
    x = np.zeros(int(n * SR))
    tt = 0.05
    base = 300 + i * 25
    while tt < n - 0.5:
        ln = rng.uniform(0.25, 0.45)
        f0 = np.linspace(base * rng.uniform(1.0, 1.15), base * 0.8, 8)
        src = glottal(f0, ln, 0.05, 0.6)
        syl = formant(src, rng.choice(["u", "o", "a"]), 1.15) * np.sin(np.linspace(0, np.pi, int(ln * SR))) ** 0.8
        # shaky tremolo of crying
        syl *= 1 + 0.5 * np.sin(2 * np.pi * 9 * np.arange(len(syl)) / SR)
        x = place(x, syl, tt)
        tt += ln + rng.uniform(0.08, 0.2)
        if rng.random() < 0.3:
            inhale = bp(white(0.3), 1200, 5000) * np.sin(np.linspace(0, np.pi, int(0.3 * SR))) * 0.5
            x = place(x, inhale, tt)
            tt += 0.35
    return reverb(x, 1.4, 0.35)


def laugh():
    n = 2.4
    x = np.zeros(int(n * SR))
    for k in range(7):
        ln = 0.17
        f0 = np.array([340, 300]) * (1.15 - k * 0.05)
        src = glottal(f0, ln, 0.02, 0.4)
        syl = formant(src, "a", 1.1) * env(int(ln * SR), 0.008, 0.1)
        h = bp(white(0.06), 1500, 6000) * env(int(0.06 * SR), 0.002, 0.03) * 0.5
        x = place(x, h, 0.05 + k * 0.23)
        x = place(x, syl, 0.08 + k * 0.23)
    # a low version underneath: two voices at once
    low = signal.resample(x, int(len(x) * 1.35))[: len(x)] * 0.5
    return reverb(x + low, 1.2, 0.35)


def scream_rev():
    n = 2.4
    f0 = np.concatenate([np.linspace(650, 980, 10), np.linspace(980, 820, 10)])
    src = glottal(f0, n, 0.08, 0.8)
    src *= 1 + 0.25 * np.sin(2 * np.pi * 6.5 * np.arange(len(src)) / SR)
    v = formant(src, "a", 1.25) + formant(src, "e", 1.2) * 0.5
    v *= adsr(len(v), 0.05, 1.0, 0.8)
    v = reverb(v, 2.2, 0.55, 3500)
    return v[::-1].copy()


def stinger(soft=False):
    n = 2.0 if not soft else 1.4
    x = np.zeros(int(n * SR))
    freqs = [220, 233.1, 311.1, 329.6, 440, 466.2, 622.3] if not soft else [196, 207.7, 293.7]
    tt = np.arange(int(n * SR)) / SR
    for f in freqs:
        ph = rng.uniform(0, 1)
        saw = 2 * ((f * (1 + 0.004 * rng.standard_normal()) * tt + ph) % 1) - 1
        x += saw
    x = lp(x, 3500 if not soft else 1800)
    x *= env(len(x), 0.004, 0.9 if not soft else 0.6, 3)
    if not soft:
        hit = lp(white(0.4), 400) * env(int(0.4 * SR), 0.001, 0.12) * 4
        x = place(x, hit, 0)
        x += bp(white(n), 2500, 8000) * env(len(x), 0.001, 0.3) * 0.8
    return reverb(x, 1.5, 0.3)


def drone_low():
    n = 5.0
    tt = t(n)
    x = np.sin(2 * np.pi * 41 * tt) + 0.6 * np.sin(2 * np.pi * 43.3 * tt) + 0.3 * np.sin(2 * np.pi * 61.7 * tt)
    x += lp(brown(n), 200) * 0.6
    x *= adsr(len(x), 1.2, 1, 1.6)
    return x


def vhs():
    n = 4.0
    tt = t(n)
    hiss = hp(white(n), 2000) * 0.35
    hum = 0.25 * np.sin(2 * np.pi * 60 * tt) + 0.12 * np.sin(2 * np.pi * 120 * tt)
    wob = 1 + 0.05 * np.sin(2 * np.pi * 0.7 * tt) + 0.02 * np.sin(2 * np.pi * 7 * tt)
    tone = 0.3 * np.sin(2 * np.pi * np.cumsum(880 * wob) / SR) * (np.sin(2 * np.pi * 0.35 * tt) > 0.2)
    drop = (rng.random(int(n * 20) + 2) > 0.8).repeat(SR // 20 + 1)[: len(tt)]
    crackle = (rng.random(len(tt)) > 0.998) * rng.standard_normal(len(tt)) * 3
    x = (hiss + hum + tone) * np.where(drop, 0.2, 1.0) + crackle
    # tape stretch at the end
    stretch = np.sin(2 * np.pi * np.cumsum(np.linspace(600, 90, int(0.8 * SR))) / SR) * np.linspace(1, 0, int(0.8 * SR))
    x = place(x, stretch * 0.6, n - 0.9)
    return x


def clock_tick(i):
    n = 0.12
    x = bp(white(n), 2000 + i * 600, 7000) * env(int(n * SR), 0.0005, 0.01)
    x += np.sin(2 * np.pi * (1300 + i * 200) * t(n)) * env(int(n * SR), 0.0005, 0.015) * 0.6
    return reverb(x, 0.5, 0.35)


def clock_chime():
    n = 4.0
    tt = t(n)
    f = 146.8
    x = np.zeros(len(tt))
    for m, g, d in ((1, 1, 3.5), (2.0, 0.5, 2.2), (2.4, 0.35, 1.6), (3.0, 0.3, 1.2), (4.2, 0.2, 0.8), (0.5, 0.4, 3.8)):
        x += g * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt / d)
    x *= np.minimum(1, tt / 0.003)
    x *= 1 + 0.1 * np.sin(2 * np.pi * 1.3 * tt)
    return reverb(x, 2.5, 0.35)


def drip(i):
    n = 0.5
    f = np.linspace(900 + i * 250, 1900 + i * 300, int(0.05 * SR))
    plink = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(f), 0.001, 0.03)
    x = np.zeros(int(n * SR))
    x = place(x, plink, 0.01)
    return reverb(x, 0.9, 0.45)


def power(up):
    n = 1.6
    f = np.linspace(120, 25, int(n * SR)) if not up else np.linspace(30, 110, int(n * SR))
    tt = t(n)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(f * 2) / SR)) * 0.3
    x *= np.linspace(1, 0.1, len(x)) if not up else np.linspace(0.2, 1, len(x)) * adsr(len(x), 0.01, 1, 0.3)
    click = bp(white(0.05), 1000, 6000) * env(int(0.05 * SR), 0.0005, 0.01) * 2
    x = place(x, click, 0 if not up else 0.02)
    if not up:
        x = place(x, click * 0.6, n - 0.2)
    return reverb(lp(x, 2500), 0.8, 0.3)


def count_tick():
    n = 0.8
    x = bp(white(0.3), 900, 5000) * env(int(0.3 * SR), 0.004, 0.06) * 0.4
    tone = np.sin(2 * np.pi * 220 * t(0.6)) * env(int(0.6 * SR), 0.002, 0.25) + 0.4 * np.sin(2 * np.pi * 330 * t(0.6)) * env(int(0.6 * SR), 0.002, 0.2)
    out = np.zeros(int(n * SR))
    out = place(out, x, 0)
    out = place(out, tone * 0.6, 0.0)
    return reverb(out, 1.2, 0.4)


def hiss():
    n = 1.4
    x = bp(white(n), 2500, 9000) * env(int(n * SR), 0.03, 0.6)
    g = formant(glottal(90, n, 0.05, 0.9), "e", 1.3) * env(int(n * SR), 0.05, 0.5) * 0.3
    return reverb(x + g, 0.8, 0.3)


def wisp_hum():
    n = 3.0
    tt = t(n)
    x = np.zeros(len(tt))
    for f in (523.3, 527.1, 784.9, 1046.5):
        x += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * (0.6 if f < 800 else 0.3)
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.8 * tt)
    shimmer = bp(white(n), 5000, 9000) * 0.1 * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * tt))
    x = (x + shimmer) * adsr(len(x), 0.4, 1, 0.6)
    return reverb(x, 1.5, 0.5)


def chime_good():
    n = 2.5
    tt = t(n)
    x = np.zeros(len(tt))
    for k, f in enumerate((784, 988, 1175, 1568)):
        seg = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 1.0) + 0.3 * np.sin(2 * np.pi * f * 2.01 * tt) * np.exp(-tt / 0.5)
        x = place(x, seg[: int((n - k * 0.12) * SR)] * 0.5, k * 0.12)
    return reverb(x, 1.6, 0.4)


def gong():
    n = 3.0
    tt = t(n)
    x = np.zeros(len(tt))
    for m, g in ((1, 1), (1.47, 0.6), (2.09, 0.5), (2.56, 0.3), (3.2, 0.2)):
        x += g * np.sin(2 * np.pi * 110 * m * tt) * np.exp(-tt / (2.5 / m))
    x *= np.minimum(1, tt / 0.01)
    return reverb(x, 2.0, 0.4)


def banish():
    n = 3.2
    x = chime_good()
    x = np.pad(x, (0, max(0, int(n * SR) - len(x))))[: int(n * SR)]
    whoosh = bp(white(n), 400, 3000) * np.sin(np.linspace(0, np.pi, int(n * SR))) ** 2
    whoosh *= np.linspace(1, 0, int(n * SR))
    choir = formant(glottal(np.array([220, 330]), n, 0.003, 0.05), "a", 1.0) * adsr(int(n * SR), 0.3, 1, 1.5)
    return x + whoosh * 0.5 + choir * 0.15


def haunt(i):
    # whispery mumbling that never becomes words
    n = 3.2
    x = np.zeros(int(n * SR))
    tt = 0.05
    while tt < n - 0.3:
        ln = rng.uniform(0.08, 0.2)
        src = bp(white(ln), 500, 6000)
        syl = formant(src, rng.choice(list(FORMANTS.keys())), rng.uniform(0.9, 1.3))
        syl *= np.sin(np.linspace(0, np.pi, len(syl)))
        x = place(x, syl, tt)
        tt += ln + rng.uniform(0.02, 0.12)
    x = x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t(n)))
    return reverb(x, 1.4 + i * 0.3, 0.45)


def paper():
    n = 0.8
    x = np.zeros(int(n * SR))
    for _ in range(9):
        c = bp(white(0.04), 2000, 8000) * env(int(0.04 * SR), 0.001, 0.015)
        x = place(x, c * rng.uniform(0.3, 1), rng.uniform(0, n - 0.1))
    x += bp(white(n), 1500, 5000) * np.sin(np.linspace(0, np.pi, int(n * SR))) * 0.15
    return x


def burn():
    n = 1.8
    x = bp(white(n), 600, 4000) * adsr(int(n * SR), 0.2, 1, 0.8) * 0.4
    for _ in range(40):
        c = bp(white(0.01), 2000, 9000) * env(int(0.01 * SR), 0.0005, 0.004)
        x = place(x, c * rng.uniform(0.3, 1.2), rng.uniform(0, n - 0.1))
    return x


def candle_light():
    n = 0.7
    x = bp(white(n), 300, 3000) * env(int(n * SR), 0.01, 0.12) * 0.8
    for _ in range(6):
        c = bp(white(0.01), 2500, 9000) * env(int(0.01 * SR), 0.0005, 0.004)
        x = place(x, c, rng.uniform(0.05, 0.5))
    return reverb(x, 0.6, 0.25)


def candle_out():
    n = 1.6
    x = bp(white(n), 200, 2500) * np.sin(np.linspace(0, np.pi, int(n * SR))) ** 0.6
    x *= np.linspace(1, 0.1, int(n * SR))
    breath = formant(bp(white(n), 300, 3000), "u", 0.9) * np.sin(np.linspace(0, np.pi, int(n * SR))) * 0.5
    return reverb(x + breath, 1.2, 0.3)


def heart_other():
    n = 0.9
    out = np.zeros(int(n * SR))
    for at, g in ((0.0, 1.0), (0.24, 0.7)):
        f = np.linspace(70, 38, int(0.18 * SR))
        beat = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(f), 0.004, 0.08)
        out = place(out, beat * g, at)
    wet = lp(white(n), 300) * np.abs(out) * 0.4
    return lp(out + wet, 500)


def build():
    for i in range(3):
        write(f"step_wet_{i + 1}", step_wet(i))
        write(f"step_child_{i + 1}", step_child(i), 0.7)
        write(f"step_heavy_{i + 1}", step_heavy(i))
        write(f"roof_step_{i + 1}", roof_step(i))
        write(f"scratch_{i + 1}", scratch(i))
        write(f"rustle_{i + 1}", rustle(i), 0.7)
        write(f"chain_{i + 1}", chain(i))
        write(f"sob_{i + 1}", sob(i))
        write(f"drip_{i + 1}", drip(i), 0.7)
        write(f"tick_{i + 1}", clock_tick(i), 0.7)
    for i in range(2):
        write(f"hand_slap_{i + 1}", hand_slap(i))
        write(f"drag_{i + 1}", drag(i))
        write(f"giggle_{i + 1}", giggle(i), 0.8)
        write(f"breath_close_{i + 1}", breath_close(i))
        write(f"haunt_{i + 1}", haunt(i), 0.8)
    for k, part in enumerate(lullaby_parts()):
        write(f"lullaby_{k + 1}", part, 0.75)
    write("scrape", scrape(), 0.7)
    write("ash_scatter", ash_scatter(), 0.7)
    write("hair", hair(), 0.6)
    write("exhale", exhale())
    write("gasp", gasp(), 0.7)
    write("sniff", sniff())
    write("laugh", laugh())
    write("scream_rev", scream_rev())
    write("stinger", stinger(), 0.95)
    write("stinger_soft", stinger(True), 0.8)
    write("drone_low", drone_low())
    write("vhs", vhs(), 0.7)
    write("clock_chime", clock_chime())
    write("power_down", power(False))
    write("power_up", power(True))
    write("count_tick", count_tick(), 0.7)
    write("hiss", hiss())
    write("wisp_hum", wisp_hum(), 0.6)
    write("chime_good", chime_good(), 0.8)
    write("gong", gong(), 0.8)
    write("banish", banish())
    write("paper", paper(), 0.7)
    write("burn", burn(), 0.7)
    write("candle_light", candle_light(), 0.7)
    write("candle_out", candle_out())
    write("heart_other", heart_other())

    r3 = lambda b: [f"{b}_{i}" for i in (1, 2, 3)]
    r2 = lambda b: [f"{b}_{i}" for i in (1, 2)]
    define("succubi.ev.step_wet", r3("step_wet"), 0.8, max_distance=24)
    define("succubi.ev.step_child", r3("step_child"), 0.7, max_distance=20)
    define("succubi.ev.step_heavy", r3("step_heavy"), 1.0, max_distance=32)
    define("succubi.ev.roof_step", r3("roof_step"), 1.0, max_distance=24)
    define("succubi.ev.scratch", r3("scratch"), 0.9, max_distance=24)
    define("succubi.ev.rustle", r3("rustle"), 0.7, max_distance=20)
    define("succubi.ev.chain", r3("chain"), 0.9, max_distance=28)
    define("succubi.ev.sob", r3("sob"), 0.8, max_distance=40)
    define("succubi.ev.drip", r3("drip"), 0.6, max_distance=16)
    define("succubi.ev.clock_tick", r3("tick"), 0.8, category="player")
    define("succubi.ev.hand_slap", r2("hand_slap"), 0.9, max_distance=24)
    define("succubi.ev.drag", r2("drag"), 0.9, max_distance=32)
    define("succubi.ev.giggle", r2("giggle"), 0.7, max_distance=24)
    define("succubi.ev.breath_close", r2("breath_close"), 0.9, max_distance=8)
    define("succubi.ev.haunt", r2("haunt"), 0.7, max_distance=16)
    for k in range(8):
        define(f"succubi.ev.lullaby{k + 1}", [f"lullaby_{k + 1}"], 0.7, max_distance=32)
    for name, vol, dist in (("scrape", 0.7, 16), ("ash_scatter", 0.7, 16), ("hair", 0.6, 12), ("exhale", 1.0, 16),
                            ("gasp", 0.7, 12), ("sniff", 1.0, 20), ("laugh", 1.0, 32), ("scream_rev", 1.0, 64),
                            ("hiss", 0.8, 20), ("wisp_hum", 0.6, 24), ("paper", 0.8, 12), ("burn", 0.7, 12),
                            ("candle_light", 0.6, 16), ("candle_out", 0.9, 16), ("heart_other", 0.9, 8),
                            ("drone_low", 0.8, 32), ("chime_good", 0.8, 24), ("gong", 0.7, 24), ("banish", 1.0, 32)):
        define(f"succubi.ev.{name}", [name], vol, max_distance=dist)
    # screen-side sounds (not placed in the world)
    for name, vol in (("stinger", 1.0), ("stinger_soft", 0.8), ("vhs", 0.7), ("clock_chime", 0.9),
                      ("power_down", 1.0), ("power_up", 0.9), ("count_tick", 0.8)):
        define(f"succubi.ev.{name}", [name], vol, category="player")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds.json"), "w") as f:
        json.dump(DEFS, f, indent=2)
    print("events:", len(DEFS), "files:", len(os.listdir(OUT)))


if __name__ == "__main__":
    build()
