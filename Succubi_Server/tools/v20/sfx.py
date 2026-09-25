"""Pressure sounds, synthesised with numpy and written as OGG Vorbis (python soundfile):

    succubi.heartbeat   lub-dub thump (health low; scripts/succubi/pressure.js plays it faster and louder near death)
    succubi.stomach     stomach growl with gurgles (food low)
    succubi.pant        short panting breaths (thirst low)
    succubi.whisper     breathy unintelligible whispers with an echo (sanity low)
    succubi.tinnitus    a thin ringing in the ears that swells and fades (sanity very low)

Needs `pip install soundfile` (it bundles libsndfile with Vorbis)."""
import math, os
import numpy as np
from registry import step
from common import rjson, wjson, CORE_RP

SR = 22050
DIR = 'sounds/succubi'


# ------------------------------------------------------------------------------------------ helpers
def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def env_ad(n, attack, decay_tau):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(0, t - attack) / decay_tau)


def fft_filter(x, gain_fn):
    """zero-phase filter with a gain curve over frequency (Hz)"""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * gain_fn(f), len(x))


def lowpass(x, fc, order=2):
    return fft_filter(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order)))


def band(f, center, width):
    return np.exp(-0.5 * ((f - center) / width) ** 2)


def shaped_noise(sec, gain_at, rng, frame=512, hop=128):
    """white noise whose spectrum follows gain_at(t, freqs) over time (STFT overlap-add)"""
    n = int(sec * SR)
    noise = rng.standard_normal(n + frame)
    win = np.hanning(frame)
    out = np.zeros(n + frame)
    norm = np.zeros(n + frame)
    freqs = np.fft.rfftfreq(frame, 1 / SR)
    for start in range(0, n, hop):
        seg = noise[start:start + frame] * win
        spec = np.fft.rfft(seg) * gain_at(start / SR, freqs)
        out[start:start + frame] += np.fft.irfft(spec, frame) * win
        norm[start:start + frame] += win ** 2
    return (out / np.maximum(norm, 1e-3))[:n]


def normalize(x, peak=0.89):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def fade(x, fin=0.01, fout=0.05):
    n = len(x)
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[n - b:] *= np.linspace(1, 0, b)
    return x


# ------------------------------------------------------------------------------------------ sounds
def heartbeat(seed):
    rng = np.random.RandomState(seed)
    x = np.zeros(int(0.62 * SR))

    def thump(at, f0, f1, amp):
        n = int(0.24 * SR)
        t = np.arange(n) / SR
        freq = f1 + (f0 - f1) * np.exp(-t / 0.035)
        body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * env_ad(n, 0.004, 0.055)
        thud = lowpass(rng.standard_normal(n), 140, 3) * env_ad(n, 0.002, 0.025) * 0.9
        s = int(at * SR)
        x[s:s + n] += amp * (body + thud)[:len(x) - s]

    thump(0.0, 95 + rng.uniform(-6, 6), 46, 1.0)                 # lub
    thump(0.25 + rng.uniform(-0.02, 0.02), 110, 54, 0.72)         # dub
    x = np.tanh(x * 1.6)                                          # a little weight
    return fade(normalize(lowpass(x, 400)), 0.002, 0.08)


def stomach(seed, sec):
    rng = np.random.RandomState(seed)
    t = t_axis(sec)
    n = len(t)
    # the grumble: a buzzy pulse wandering between 55 and 150 Hz
    walk = np.cumsum(rng.standard_normal(n)) / math.sqrt(SR) * 4
    walk = lowpass(walk - walk.mean(), 3)
    f0 = np.clip(95 + 40 * walk / (np.std(walk) + 1e-6) * 0.6, 55, 150)
    phase = np.cumsum(f0) / SR
    buzz = (phase % 1.0) * 2 - 1
    buzz = fft_filter(buzz, lambda f: band(f, 260, 170) + 0.5 * band(f, 520, 200))
    # swells: 2-4 rumbles
    swell = np.zeros(n)
    for _ in range(rng.randint(2, 5)):
        c, w = rng.uniform(0.15, 0.85) * sec, rng.uniform(0.18, 0.45)
        swell += rng.uniform(0.6, 1.0) * np.exp(-0.5 * ((t - c) / w) ** 2)
    x = buzz * swell
    # gurgles: little rising chirps
    for _ in range(int(sec * rng.uniform(7, 12))):
        s = rng.randint(0, n - int(0.08 * SR))
        m = int(rng.uniform(0.025, 0.07) * SR)
        tt = np.arange(m) / SR
        fr = rng.uniform(180, 260) + np.linspace(0, rng.uniform(200, 450), m)
        x[s:s + m] += rng.uniform(0.15, 0.4) * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.hanning(m) * swell[s]
    x = np.tanh(x * 2.2)
    return fade(normalize(lowpass(x, 900)), 0.04, 0.25)


VOWELS = [(750, 1200), (500, 1800), (320, 2300), (520, 900), (360, 800), (650, 1650)]


def breath_gain(kind):
    f1, f2 = (700, 1250) if kind == 'out' else (900, 1900)

    def g(t, f):
        return 0.9 * band(f, f1, 260) + 0.7 * band(f, f2, 380) + 0.35 * band(f, 2700, 600) + 0.05
    return g


def pant(seed):
    rng = np.random.RandomState(seed)
    parts = []
    for _ in range(4):
        for kind, dur, amp in (('out', rng.uniform(0.28, 0.36), 1.0), ('in', rng.uniform(0.2, 0.27), 0.45)):
            b = shaped_noise(dur, breath_gain(kind), rng)
            m = len(b)
            e = np.minimum(1, np.arange(m) / (0.05 * SR)) * np.minimum(1, (m - np.arange(m)) / (0.11 * SR))
            if kind == 'out':
                e *= np.linspace(1.0, 0.55, m)
            parts.append(b * e * amp)
            parts.append(np.zeros(int(rng.uniform(0.03, 0.08) * SR)))
    x = np.concatenate(parts)
    return fade(normalize(lowpass(x, 5200)), 0.01, 0.1)


def whisper(seed, sec):
    rng = np.random.RandomState(seed)
    # syllable plan: (start, length, vowel, sibilant?) with pauses between "words"
    plan, at = [], 0.08
    while at < sec - 0.25:
        for _ in range(rng.randint(2, 5)):
            ln = rng.uniform(0.08, 0.19)
            plan.append((at, ln, VOWELS[rng.randint(len(VOWELS))], rng.random_sample() < 0.3))
            at += ln + rng.uniform(0.0, 0.04)
        at += rng.uniform(0.12, 0.3)

    def gain(t, f):
        g = 0.02
        for s, ln, (f1, f2), sib in plan:
            if s - 0.02 <= t <= s + ln + 0.02:
                k = math.sin(math.pi * min(1, max(0, (t - s) / ln)))
                g = g + k * (0.8 * band(f, f1, 180) + 0.7 * band(f, f2, 260) + 0.3 * band(f, 2600, 500))
                if sib and t < s + 0.05:
                    g = g + 0.9 * band(f, 6500, 1500)
        return g

    x = shaped_noise(sec, gain, rng)
    echo = np.zeros_like(x)
    d = int(0.13 * SR)
    echo[d:] = x[:-d] * 0.4
    echo[2 * d:] += x[:-2 * d] * 0.18
    return fade(normalize(x + echo), 0.02, 0.3)


def tinnitus():
    t = t_axis(3.2)
    x = 0.6 * np.sin(2 * np.pi * 5200 * t) + 0.4 * np.sin(2 * np.pi * 5237 * t)
    e = np.minimum(1, t / 1.1) * np.minimum(1, (t[-1] - t) / 1.4)
    return fade(x * e * 0.3, 0.05, 0.2)


SOUNDS = {
    'succubi.heartbeat': [('heartbeat_1', lambda: heartbeat(1)), ('heartbeat_2', lambda: heartbeat(2))],
    'succubi.stomach': [('stomach_1', lambda: stomach(3, 1.8)), ('stomach_2', lambda: stomach(4, 2.3)), ('stomach_3', lambda: stomach(5, 1.4))],
    'succubi.pant': [('pant_1', lambda: pant(6)), ('pant_2', lambda: pant(7))],
    'succubi.whisper': [('whisper_1', lambda: whisper(8, 2.4)), ('whisper_2', lambda: whisper(9, 2.9)), ('whisper_3', lambda: whisper(10, 2.0))],
    'succubi.tinnitus': [('tinnitus_1', tinnitus)],
}


@step
def build_sfx(out, ctx, log):
    import soundfile as sf
    rp = os.path.join(out, CORE_RP)
    os.makedirs(os.path.join(rp, DIR), exist_ok=True)
    defs_path = os.path.join(rp, 'sounds/sound_definitions.json')
    defs = rjson(defs_path)
    n = 0
    for event, files in SOUNDS.items():
        entries = []
        for name, fn in files:
            sf.write(os.path.join(rp, DIR, name + '.ogg'), fn().astype('float32'), SR, format='OGG', subtype='VORBIS')
            entries.append({"name": f"{DIR}/{name}", "volume": 1.0})
            n += 1
        defs['sound_definitions'][event] = {"category": "player", "sounds": entries}
    wjson(defs_path, defs)
    log(f'sfx: {n} pressure sounds ({", ".join(SOUNDS)})')
