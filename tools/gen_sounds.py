#!/usr/bin/env python3
"""Synthesises the original (CC0) placeholder sound effects for the Pain Origin mod.

Usage: gen_sounds.py <sounds_out_dir> <work_dir>
Writes mono 44.1 kHz Ogg Vorbis files through ffmpeg (libvorbis).
"""
import os
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

OUT = sys.argv[1]
WORK = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)
SR = 44100
rng = np.random.default_rng(777)


def tvec(sec):
    return np.arange(int(SR * sec)) / SR


def noise(sec):
    return rng.standard_normal(int(SR * sec)).astype(np.float64)


def bp(x, lo, hi, order=3):
    lo = max(lo, 20.0)
    hi = min(hi, SR / 2 - 100)
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, fc, order=3):
    sos = signal.butter(order, min(fc, SR / 2 - 100), btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, fc, order=3):
    sos = signal.butter(order, fc, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def sweep_noise(sec, f0, f1, width=0.5, bands=14, order=2):
    """Noise whose band-pass centre glides f0 -> f1 (log-spaced bands cross-faded in time)."""
    t = tvec(sec)
    x = noise(sec)
    out = np.zeros_like(t)
    centres = np.geomspace(f0, f1, bands)
    for i, fc in enumerate(centres):
        pos = i / (bands - 1)
        env = np.exp(-(((t / sec) - pos) / (1.2 / bands)) ** 2)
        out += bp(x, fc / (1 + width), fc * (1 + width), order) * env
    return out


def reverb(x, sec=0.7, mix=0.25, seed=5):
    g = np.random.default_rng(seed)
    n = int(SR * sec)
    ir = g.standard_normal(n) * np.exp(-np.arange(n) / (SR * sec / 5.0))
    ir[0] = 0
    wet = signal.fftconvolve(x, ir)[: len(x)]
    wet *= np.max(np.abs(x)) / (np.max(np.abs(wet)) + 1e-9)
    return x * (1 - mix) + wet * mix


def fade(x, fin=0.003, fout=0.03):
    n = len(x)
    a = int(SR * fin)
    b = int(SR * fout)
    x = x.copy()
    x[:a] *= np.linspace(0, 1, a)
    x[-b:] *= np.linspace(1, 0, b)
    return x


def finish(name, x, peak):
    x = np.nan_to_num(x)
    x = fade(x)
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    wav = os.path.join(WORK, name + ".wav")
    wavfile.write(wav, SR, (x * 32767).astype(np.int16))
    ogg = os.path.join(OUT, name + ".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-ar", str(SR),
                    "-c:a", "libvorbis", "-q:a", "4", ogg], check=True)
    print("wrote", ogg, f"{len(x) / SR:.2f}s peak={peak}")


def osc_phase(freq):
    return 2 * np.pi * np.cumsum(freq) / SR


# 1. charge-up ----------------------------------------------------------------
def charge():
    sec = 1.0
    t = tvec(sec)
    f = 170 + 760 * (t / sec) ** 2
    ph = osc_phase(f)
    tone = np.sin(ph) + 0.6 * np.sin(ph * 1.005 + 0.4) + 0.25 * np.sin(2 * ph)
    trem = 1 - 0.30 * (0.5 + 0.5 * np.sin(2 * np.pi * 17 * t))
    env = (t / sec) ** 1.4
    shimmer = bp(noise(sec), 2800, 7000) * (t / sec) ** 2.2 * 0.35
    x = (tone * 0.5 * trem + shimmer) * env
    x[int(SR * 0.93):] *= np.linspace(1, 0, len(x) - int(SR * 0.93))
    return reverb(x, 0.45, 0.2), 0.6


# 2. Shinra Tensei: release boom ----------------------------------------------
def shinra():
    sec = 1.8
    t = tvec(sec)
    f = 42 + 130 * np.exp(-t / 0.055)
    thump = np.sin(osc_phase(f)) * np.exp(-t / 0.50)
    body = lp(noise(sec), 1800) * np.exp(-t / 0.13) * 0.9
    crack = hp(noise(sec), 3200) * np.exp(-t / 0.018) * 0.55
    rumble = lp(noise(sec), 140, 2) * np.exp(-t / 0.85) * 0.55
    air = bp(noise(sec), 400, 5000) * np.exp(-t / 0.30) * 0.35
    x = thump * 1.1 + body + crack + rumble + air
    return reverb(x, 0.9, 0.30), 0.85


# 3. shock-wave whoosh ---------------------------------------------------------
def shockwave():
    sec = 1.4
    t = tvec(sec)
    w = sweep_noise(sec, 260, 4800, 0.6)
    env = (1 - np.exp(-t / 0.05)) * np.exp(-t / 0.42)
    rumble = lp(noise(sec), 220, 2) * np.exp(-t / 0.5) * 0.5
    x = w * env * 1.2 + rumble
    return reverb(x, 0.6, 0.22), 0.70


# 4. Bansho Ten'in: pull / suction ---------------------------------------------
def bansho():
    sec = 1.3
    t = tvec(sec)
    w = sweep_noise(sec, 3600, 240, 0.55)
    env = np.clip(t / 0.55, 0, 1) ** 1.3 * np.where(t < 0.92, 1.0, np.exp(-(t - 0.92) / 0.05))
    pulse = 0.5 + 0.5 * np.sin(2 * np.pi * (6 + 14 * (t / sec)) * t)
    sub = np.sin(osc_phase(55 + 90 * (t / sec) ** 2)) * np.clip(t / 0.6, 0, 1) * np.where(t < 0.92, 1.0, 0.0)
    snap_t = np.clip(t - 0.92, 0, None)
    snap = (np.sin(osc_phase(np.full_like(t, 70.0) + 0 * t)) * np.exp(-snap_t / 0.12)) * (t >= 0.92)
    snap += lp(noise(sec), 900) * np.exp(-snap_t / 0.06) * (t >= 0.92) * 0.8
    x = w * env * (0.6 + 0.4 * pulse) * 1.1 + sub * 0.5 + snap * 0.9
    return reverb(x, 0.5, 0.2), 0.75


# 5. Chibaku Tensei core hum (designed to be re-triggered with overlap) ---------
def chibaku_core():
    sec = 2.4
    t = tvec(sec)
    x = np.zeros_like(t)
    for f, a in [(38, 1.0), (57, 0.7), (76.5, 0.55), (95.5, 0.35)]:
        x += a * np.sin(osc_phase(np.full_like(t, f)) + rng.uniform(0, 6.28))
        x += a * 0.6 * np.sin(osc_phase(np.full_like(t, f * 1.006)) + rng.uniform(0, 6.28))
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.85 * t + 0.6)
    x *= 0.8 + 0.2 * np.sin(2 * np.pi * 3.1 * t)
    swirl = lp(noise(sec), 700) * (0.4 + 0.6 * np.sin(2 * np.pi * 0.6 * t + 1.2) ** 2) * 0.5
    ring = (np.sin(osc_phase(np.full_like(t, 523.0))) + np.sin(osc_phase(np.full_like(t, 785.0)))) * 0.06 * (0.5 + 0.5 * np.sin(2 * np.pi * 1.7 * t))
    x = x * 0.45 + swirl + ring
    env = np.minimum(1, np.minimum(t / 0.35, (sec - t) / 0.45))
    return reverb(x * env, 0.7, 0.2), 0.60


# 6. rocks being dragged toward the core ---------------------------------------
def chibaku_debris():
    sec = 1.6
    t = tvec(sec)
    base = lp(noise(sec), 520) * (0.45 + 0.55 * np.sin(2 * np.pi * 1.3 * t + 0.5) ** 2)
    click_env = np.zeros_like(t)
    n_clicks = 55
    pos = np.sort(rng.beta(1.6, 1.2, n_clicks) * (sec - 0.15))
    for p in pos:
        i = int(p * SR)
        ln = int(SR * rng.uniform(0.012, 0.04))
        click_env[i:i + ln] += rng.uniform(0.3, 1.0) * np.exp(-np.arange(min(ln, len(t) - i)) / (SR * 0.008))[: len(click_env[i:i + ln])]
    crackle = bp(noise(sec), 700, 3600) * click_env
    x = base * 0.9 + crackle * 1.4
    env = np.minimum(1, np.minimum(t / 0.12, (sec - t) / 0.35))
    return reverb(x * env, 0.5, 0.18), 0.62


# 7. Chibaku Tensei collapse ----------------------------------------------------
def chibaku_collapse():
    sec = 3.2
    t = tvec(sec)
    f = 32 + 120 * np.exp(-t / 0.12)
    thump = np.sin(osc_phase(f)) * np.exp(-t / 0.9)
    body = lp(noise(sec), 2200) * np.exp(-t / 0.22) * 1.0
    crack = hp(noise(sec), 2800) * np.exp(-t / 0.03) * 0.6
    rumble = lp(noise(sec), 120, 2) * np.exp(-t / 1.4) * 0.7
    debris = np.zeros_like(t)
    for p in np.sort(rng.uniform(0.05, 2.4, 70)):
        i = int(p * SR)
        ln = int(SR * rng.uniform(0.02, 0.07))
        seg = rng.standard_normal(min(ln, len(t) - i)) * np.exp(-np.arange(min(ln, len(t) - i)) / (SR * 0.015))
        debris[i:i + len(seg)] += seg * rng.uniform(0.15, 0.5) * np.exp(-p / 1.4)
    debris = bp(debris, 500, 4200)
    x = thump * 1.2 + body + crack + rumble + debris * 1.2
    return reverb(x, 1.2, 0.34), 0.90


# 8. Universal Defense repulsion -------------------------------------------------
def defense():
    sec = 0.55
    t = tvec(sec)
    f = 140 + 520 * np.exp(-t / 0.07)
    tone = np.sin(osc_phase(f)) * np.exp(-t / 0.16)
    shimmer = bp(noise(sec), 2200, 6200) * np.exp(-t / 0.10) * 0.45
    click = hp(noise(sec), 2500) * np.exp(-t / 0.004) * 0.4
    x = tone + shimmer + click
    return reverb(x, 0.3, 0.15), 0.60


if __name__ == "__main__":
    for name, fn in [("charge", charge), ("shinra_tensei", shinra), ("shockwave", shockwave),
                     ("bansho_tenin", bansho), ("chibaku_core", chibaku_core),
                     ("chibaku_debris", chibaku_debris), ("chibaku_collapse", chibaku_collapse),
                     ("defense", defense)]:
        sig, peak = fn()
        finish(name, sig, peak)
