"""Procedural music and sound effects - every sound in the game is synthesized here at startup.
Original compositions by Ironite / generated in code, so there are no copyright concerns.
"""
import numpy as np

SR = 44100


def _t(dur):
    return np.arange(int(SR * dur), dtype=np.float32) / SR


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def env_ad(n, attack=0.005, decay=0.5):
    t = np.arange(n, dtype=np.float32) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / max(decay, 1e-4))


def pluck(freq, dur, bright=0.6, decay=0.9):
    """Warm plucked-string tone (guitar / harp-like)."""
    t = _t(dur)
    out = np.zeros_like(t)
    for k, amp in enumerate([1.0, 0.55 * bright + 0.1, 0.35 * bright, 0.22 * bright, 0.12 * bright, 0.06 * bright], 1):
        f = freq * k * (1 + 0.0004 * k * k)
        out += amp * np.sin(2 * np.pi * f * t) * np.exp(-t * (1.0 / decay) * (1 + 0.6 * (k - 1)))
    out *= np.clip(t / 0.004, 0, 1)
    return out


def flute(freq, dur, vib=0.006):
    """Soft recorder / flute voice for melodies."""
    t = _t(dur)
    ph = 2 * np.pi * freq * (t + vib / (2 * np.pi * 5.2) * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.25, 0, 1))
    out = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
    rng = np.random.default_rng(int(freq))
    breath = rng.standard_normal(len(t)).astype(np.float32) * 0.015
    att = np.clip(t / 0.05, 0, 1)
    rel = np.clip((dur - t) / 0.08, 0, 1)
    return (out + breath) * att * rel


def bell(freq, dur, decay=0.8):
    t = _t(dur)
    out = np.zeros_like(t)
    for ratio, amp, dk in [(1, 1, 1), (2.0, 0.45, 0.7), (3.01, 0.25, 0.5), (4.2, 0.12, 0.35), (5.43, 0.08, 0.25)]:
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / (decay * dk))
    return out * np.clip(t / 0.002, 0, 1)


def soft_bass(freq, dur):
    t = _t(dur)
    out = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return out * np.exp(-t / 0.9) * np.clip(t / 0.01, 0, 1)


def add(buf, sig, start, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def reverb(x, wet=0.25, loop=False):
    """Small warm room reverb via a sparse decaying impulse response (FFT convolution)."""
    rng = np.random.default_rng(3)
    length = int(SR * 1.6)
    ir = np.zeros(length, np.float32)
    times = np.sort(rng.uniform(0.012, 1.55, 220))
    for tt in times:
        ir[int(tt * SR)] += rng.uniform(-1, 1) * np.exp(-tt / 0.45)
    ir = np.convolve(ir, np.ones(40, np.float32) / 40, mode="same")  # soften
    n = len(x) + length
    nfft = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:n].astype(np.float32)
    y /= max(1e-6, np.max(np.abs(ir)) * 6)
    if loop:  # wrap the tail back to the start for a seamless loop
        dry = x
        wet_sig = y[:len(x)].copy()
        tail = y[len(x):]
        wet_sig[:len(tail)] += tail[:len(x)]
    else:
        dry = np.concatenate([x, np.zeros(length, np.float32)])
        wet_sig = y[:len(dry)]
    return dry * (1 - wet) + wet_sig * wet


def to_stereo_int16(mono, gain=0.9, channels=2, pan_wide=None):
    peak = max(1e-6, float(np.max(np.abs(mono))))
    m = mono / peak * gain
    if pan_wide is not None:
        left, right = pan_wide
        stereo = np.stack([left / peak * gain, right / peak * gain], axis=1)
    else:
        stereo = np.stack([m, m], axis=1)
    data = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
    if channels == 1:
        data = data[:, :1].copy()
    return np.ascontiguousarray(data)


# ---------------------------------------------------------------------- music
CHORDS = {  # midi notes (root position-ish voicings around G3)
    "G": [43, 55, 59, 62, 67], "C": [48, 55, 60, 64, 67], "D": [50, 57, 62, 66, 69],
    "Em": [40, 55, 59, 64, 67], "Am": [45, 57, 60, 64, 69],
}
SECTION_A = [("G", [(71, 1), (74, 1), (71, 1)]), ("C", [(72, 1.5), (71, .5), (69, 1)]),
             ("G", [(67, 1), (71, 1), (74, 1)]), ("D", [(69, 2), (66, 1)]),
             ("Em", [(67, 1), (71, 1), (76, 1)]), ("C", [(76, 1.5), (74, .5), (72, 1)]),
             ("D", [(71, 1), (69, 1), (66, 1)]), ("G", [(67, 3)])]
SECTION_B = [("C", [(76, 1), (79, 1), (76, 1)]), ("G", [(74, 1.5), (71, .5), (67, 1)]),
             ("Am", [(72, 1), (76, 1), (69, 1)]), ("D", [(74, 2), (69, 1)]),
             ("C", [(76, 1), (74, 1), (72, 1)]), ("G", [(71, 1), (74, 1), (79, 1)]),
             ("Am", [(69, 1), (72, 1), (71, 1)]), ("D", [(69, 1), (66, 1), (62, 1)])]
SECTION_A2 = SECTION_A[:7] + [("G", [(71, 1), (74, 1), (79, 1)])]


def make_music(bpm=100):
    beat = 60.0 / bpm
    bars = SECTION_A + SECTION_B + SECTION_A2 + SECTION_B[:7] + [("G", [(67, 3)])]
    total = len(bars) * 3 * beat
    left = np.zeros(int(SR * total) + 1, np.float32)
    right = np.zeros_like(left)
    for b, (ch, mel) in enumerate(bars):
        t0 = b * 3 * beat
        notes = CHORDS[ch]
        # bass on beat 1
        add(left, soft_bass(midi_hz(notes[0]), 2.2), t0, 0.55)
        add(right, soft_bass(midi_hz(notes[0]), 2.2), t0, 0.55)
        # guitar: gentle waltz arpeggio (one-and-two-and-three-and)
        pattern = [1, 2, 3, 4, 3, 2]
        for i, idx in enumerate(pattern):
            f = midi_hz(notes[idx])
            g = 0.22 if i % 2 == 0 else 0.15
            sig = pluck(f, 1.8, bright=0.5, decay=0.7)
            add(left, sig, t0 + i * beat / 2, g * 1.1)
            add(right, sig, t0 + i * beat / 2 + 0.012, g * 0.85)
        # melody on flute, doubled softly by a bell in the B sections
        tm = t0
        b_section = 8 <= b < 16 or 24 <= b < 32
        for m, beats in mel:
            d = beats * beat
            sig = flute(midi_hz(m), d * 0.96)
            add(left, sig, tm, 0.30)
            add(right, sig, tm, 0.36)
            if b_section:
                bl = bell(midi_hz(m + 12), 1.2, 0.5)
                add(left, bl, tm, 0.05)
                add(right, bl, tm, 0.07)
            tm += d
    n = int(SR * total)
    left, right = left[:n], right[:n]
    left = reverb(left, 0.28, loop=True)
    right = reverb(right, 0.28, loop=True)
    # tiny fade at loop seam to avoid clicks
    k = 256
    for ch in (left, right):
        ch[:k] *= np.linspace(0.6, 1, k)
        ch[-k:] *= np.linspace(1, 0.6, k)
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    return left / peak, right / peak


# ---------------------------------------------------------------------- effects
def sfx_click():
    t = _t(0.06)
    s = np.sin(2 * np.pi * 1300 * t) * np.exp(-t / 0.012) + 0.5 * np.sin(2 * np.pi * 650 * t) * np.exp(-t / 0.02)
    return s


def sfx_found():
    out = np.zeros(int(SR * 1.2), np.float32)
    for i, m in enumerate([76, 79, 84]):
        add(out, bell(midi_hz(m), 1.0, 0.45), i * 0.07, 0.8)
    rng = np.random.default_rng(5)
    for i in range(6):  # sparkle
        add(out, bell(midi_hz(rng.integers(88, 100)), 0.3, 0.12), 0.18 + i * 0.045, 0.18)
    return reverb(out, 0.2)


def sfx_wrong():
    t = _t(0.26)
    f = 300 - 90 * (t / t[-1])
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * np.exp(-t / 0.09) * np.clip(t / 0.01, 0, 1)
    return s * 0.7


def sfx_hint():
    out = np.zeros(int(SR * 1.1), np.float32)
    for i, m in enumerate([84, 88, 91, 96, 100]):
        add(out, bell(midi_hz(m), 0.6, 0.22), i * 0.06, 0.5)
    return reverb(out, 0.3)


def sfx_puzzle():
    out = np.zeros(int(SR * 2.2), np.float32)
    for i, m in enumerate([72, 76, 79, 84]):
        add(out, bell(midi_hz(m), 1.4, 0.6), i * 0.1, 0.7)
        add(out, pluck(midi_hz(m - 12), 1.4, 0.4, 0.6), i * 0.1, 0.4)
    for m in (72, 76, 79, 84):
        add(out, flute(midi_hz(m), 1.0), 0.45, 0.18)
    return reverb(out, 0.25)


def sfx_win():
    out = np.zeros(int(SR * 3.2), np.float32)
    seq = [(67, 0.0), (72, 0.18), (76, 0.36), (79, 0.54), (84, 0.8)]
    for m, st in seq:
        add(out, flute(midi_hz(m), 0.5 if m != 84 else 1.4), st, 0.5)
        add(out, bell(midi_hz(m + 12), 1.2, 0.5), st, 0.25)
    for m in (60, 64, 67, 72):
        add(out, pluck(midi_hz(m), 2.4, 0.5, 1.0), 0.8, 0.3)
    return reverb(out, 0.3)


def sfx_flip():
    t = _t(0.09)
    rng = np.random.default_rng(9)
    n = rng.standard_normal(len(t)).astype(np.float32)
    n = np.convolve(n, np.ones(12) / 12, mode="same")
    return n * np.exp(-t / 0.025) * 2.0 + 0.3 * np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.02)


def sfx_slide():
    t = _t(0.12)
    s = np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.03) + 0.4 * np.sin(2 * np.pi * 840 * t) * np.exp(-t / 0.02)
    return s * 0.8


SFX = {
    "click": (sfx_click, 0.55), "found": (sfx_found, 0.8), "wrong": (sfx_wrong, 0.5), "hint": (sfx_hint, 0.7),
    "puzzle": (sfx_puzzle, 0.8), "win": (sfx_win, 0.85), "flip": (sfx_flip, 0.5), "slide": (sfx_slide, 0.5),
}
