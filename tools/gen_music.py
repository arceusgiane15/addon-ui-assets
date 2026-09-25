"""Tension music (RP sounds/music/succubi_*.ogg), made from scratch so it is the pack's own.

 succubi_danger.ogg   48 s loop - low health: a beating low drone, a dark filtered chord that opens and closes,
                      an endless rising Shepard tone and metal scrapes. No drums: the heartbeat sound keeps the pulse.
 succubi_madness.ogg  48 s loop - low sanity: a warbling tritone drone, an out-of-tune music box with echo,
                      reversed swells and radio static crackle (goes with the TV static on screen).
 succubi_silence.ogg  2 s of silence - played with a fade to let the tension music die away smoothly.

Every part repeats exactly every 48 s (filters run over two loops and the second is kept), so the tracks loop
without a click. Run: python3 tools/gen_music.py  (needs numpy, scipy, soundfile)
"""
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon", "Succubi Server RP", "sounds", "music")
SR = 44100
LOOP = 48.0
N = int(SR * LOOP)
rng = np.random.default_rng(119)
t = np.arange(2 * N) / SR  # two loops: filters settle in the first, the second is kept


def keep(x):
    return x[..., N:2 * N]


def lowpass(x, hz, order=2):
    return sosfilt(butter(order, hz, btype="low", fs=SR, output="sos"), x)


def bandpass(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def saw(phase):
    return 2.0 * (phase % 1.0) - 1.0


def phase_of(freq):
    """freq may be a constant or an array (Hz per sample). The pitch is nudged (far below hearing) so the kept
    loop holds a whole number of cycles - otherwise the wave would jump at the loop point and click."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), t.shape)
    ph = np.cumsum(f) / SR
    advance = ph[2 * N - 1] - ph[N - 1]
    return ph - ((advance - np.round(advance)) / N) * np.arange(2 * N)


def noise():
    """white noise that repeats every loop"""
    return np.tile(rng.standard_normal(N), 2)


def swell(period, low=0.0, high=1.0, offset=0.0):
    return low + (high - low) * (0.5 - 0.5 * np.cos(2 * np.pi * (t / period + offset)))


def env_events(times, attack, release, reverse=False):
    """sum of attack/release envelopes at the given loop times, repeated in both loops"""
    e = np.zeros_like(t)
    for start in times:
        for base in (0.0, LOOP, 2 * LOOP):
            s = start + base - LOOP
            i0 = int(s * SR)
            a, r = int(attack * SR), int(release * SR)
            shape = np.concatenate([np.linspace(0, 1, a) ** (3 if reverse else 1), np.exp(-np.linspace(0, 6, r))])
            if reverse:
                shape = np.concatenate([np.linspace(0, 1, a) ** 3, np.linspace(1, 0, int(0.08 * SR))])
            j0, j1 = max(0, i0), min(len(t), i0 + len(shape))
            if j1 > j0:
                e[j0:j1] += shape[j0 - i0:j1 - i0]
    return e


def cents(c):
    return 2 ** (c / 1200)


def master(left, right, peak=0.8):
    st = np.stack([keep(left), keep(right)])
    st -= st.mean(axis=1, keepdims=True)
    st *= peak / np.max(np.abs(st))
    return np.ascontiguousarray(st.T, dtype=np.float32)


def danger():
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    # beating drone: A1 against Bb1, breathing every 16 s
    drone = np.sin(2 * np.pi * phase_of(55.0)) + 0.8 * np.sin(2 * np.pi * phase_of(58.27))
    drone += 0.35 * lowpass(saw(phase_of(55.0 * cents(-6))), 180)
    drone *= swell(16, 0.55, 1.0)
    L += 0.55 * drone
    R += 0.55 * drone
    # dark diminished chord (A2 C3 Eb3), saw through a filter that opens and closes every 24 s
    for hz, pan in ((110.0, 0.3), (130.81, -0.2), (155.56, 0.1)):
        for side, det in ((-1, -5), (1, 5)):
            tone = saw(phase_of(hz * cents(det))) + 0.5 * saw(phase_of(hz * 2 * cents(-det)))
            cutoff_mod = swell(24, 0.0, 1.0, 0.25)
            # two filter settings blended by the swell (a moving cutoff without a per-sample filter)
            dark = lowpass(tone, 320) * (1 - cutoff_mod) + lowpass(tone, 950) * cutoff_mod
            gain = 0.09 * (1 + side * pan)
            if side < 0:
                L += gain * dark
            else:
                R += gain * dark
    # Shepard tone rising forever: octaves of a note sliding up, loudest in the middle; one cycle = 24 s
    cycle = 24.0
    shep = np.zeros_like(t)
    for k in range(6):
        pos = ((t / cycle) + k / 6.0) % 1.0  # 0..1 across 6 octaves
        freq = 80.0 * 2 ** (pos * 6)
        amp = np.exp(-((pos - 0.5) ** 2) / 0.045)
        shep += amp * np.sin(2 * np.pi * phase_of(freq))
    shep = lowpass(shep, 2500)
    L += 0.10 * shep
    R += 0.10 * shep
    # metal scrapes: band-passed noise with a slow rise, random pitch, left or right
    for when in sorted(rng.uniform(0, LOOP, 6)):
        lo = rng.uniform(900, 2600)
        band = bandpass(noise(), lo, lo * 1.25, order=3)
        scrape = band * env_events([when], rng.uniform(1.2, 2.6), 0.0, reverse=True)
        pan = rng.uniform(-0.8, 0.8)
        L += 0.22 * scrape * (1 - pan)
        R += 0.22 * scrape * (1 + pan)
    return master(L, R)


def madness():
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    # tritone drone that warbles out of tune (C2 + F#2)
    wobble = cents(15 * np.sin(2 * np.pi * t / 8.0))
    for hz, gain in ((65.41, 0.5), (92.5, 0.4), (130.81, 0.15)):
        tone = np.sin(2 * np.pi * phase_of(hz * wobble)) + 0.3 * lowpass(saw(phase_of(hz * wobble * cents(8))), 400)
        L += gain * tone * swell(48, 0.6, 1.0)
        R += gain * tone * swell(48, 0.6, 1.0, 0.5)
    # out-of-tune music box: whole-tone notes, each bent a little, with an echo
    scale = [523.25, 587.33, 659.26, 739.99, 830.61, 932.33, 1046.5]
    box = np.zeros_like(t)
    when = 0.4
    while when < LOOP - 0.5:
        hz = rng.choice(scale) * cents(rng.uniform(-35, 35))
        e = env_events([when], 0.004, 2.2)
        box += e * (np.sin(2 * np.pi * phase_of(hz)) + 0.35 * np.sin(2 * np.pi * phase_of(hz * 2.76)))
        when += rng.choice([0.9, 1.3, 1.7, 2.4, 3.1])
    echo = np.zeros_like(box)
    d = int(0.43 * SR)
    for n, g in enumerate((1.0, 0.45, 0.2, 0.09)):
        echo[n * d:] += g * box[:len(box) - n * d] if n else box
    L += 0.16 * echo
    R += 0.16 * np.roll(echo, int(0.021 * SR))
    # reversed swells (wind sucked backwards)
    for when in sorted(rng.uniform(0, LOOP, 5)):
        lo = rng.uniform(200, 700)
        band = bandpass(noise(), lo, lo * 1.6, order=2)
        sw = band * env_events([when], rng.uniform(2.0, 3.5), 0.0, reverse=True)
        L += 0.35 * sw
        R += 0.35 * np.roll(sw, int(0.05 * SR))
    # radio static crackle
    one = np.zeros(N)
    idx = rng.integers(0, N, size=int(9 * LOOP))
    one[idx] = rng.uniform(-1, 1, size=len(idx))
    crackle = np.tile(one, 2)
    crackle = bandpass(crackle, 1500, 6000) * swell(24, 0.2, 1.0, 0.1)
    hiss = bandpass(noise(), 3000, 9000) * swell(24, 0.02, 0.12, 0.6)
    L += 0.9 * crackle + 0.25 * hiss
    R += 0.9 * np.roll(crackle, 777) + 0.25 * np.roll(hiss, 1234)
    return master(L, R)


def write_ogg(name, data, quality=0.2):
    """written in blocks (libsndfile's Vorbis encoder does not like one huge write), mono to keep the
    .mcaddon under 30 MB - Minecraft plays music in mono anyway when it is not positional"""
    data = np.ascontiguousarray(data.mean(axis=1, keepdims=True), dtype=np.float32)
    with sf.SoundFile(os.path.join(OUT, name + ".ogg"), "w", SR, 1, format="OGG", subtype="VORBIS",
                      compression_level=1 - quality) as f:
        for i in range(0, len(data), 16384):
            f.write(data[i:i + 16384])


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, make in (("succubi_danger", danger), ("succubi_madness", madness)):
        write_ogg(name, make())
    write_ogg("succubi_silence", np.zeros((SR * 2, 2), dtype=np.float32))
    for f in sorted(os.listdir(OUT)):
        print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, "KB")


if __name__ == "__main__":
    main()
