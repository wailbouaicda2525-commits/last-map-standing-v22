"""
voice_sfx_v22.py — edge-tts WordBoundary narration + Saul Bass editorial procedural soundscape.
100% $0/month, zero copyrighted audio, mastered to -14 LUFS via FFmpeg.
"""
import asyncio
import json
import os
import subprocess
import time
import wave
import edge_tts
import imageio_ffmpeg
import numpy as np

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


async def _synth_once(text, voice, rate, pitch, mp3_path):
    comm = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        boundary="WordBoundary",
    )
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / 10_000_000.0
                d = chunk["duration"] / 10_000_000.0
                words.append({"word": chunk["text"], "start": s, "end": s + d})
    return words


def synthesize_voice(text, mp3_path, voice="en-US-AndrewNeural", fallbacks=None, rate="+4%", pitch="-2Hz"):
    voices = [voice] + list(fallbacks or ["en-US-ChristopherNeural", "en-US-GuyNeural"])
    last_err = None
    for v in voices:
        for attempt in range(3):
            try:
                words = asyncio.run(_synth_once(text, v, rate, pitch, mp3_path))
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 2000:
                    return words
            except Exception as e:
                last_err = e
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"edge-tts failed across all voices: {last_err}")


def get_audio_duration(path):
    p = subprocess.run([FFMPEG, "-i", path], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in p.stderr.splitlines():
        if "Duration:" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 10.0


def synthesize_saul_bass_soundscape(duration_s, elim_cues, act_cues, winner_t, wav_path, sr=44100):
    """Synthesize warm vintage editorial pulse + tactile paper-stamp thuds + chart ticks + brass winner chord."""
    n = int(duration_s * sr)
    t = np.linspace(0, duration_s, n, dtype=np.float32)

    # Warm upright-bass-like low editorial pulse (65.4Hz C2 + 98Hz G2 gentle fifth)
    pulse_env = 0.55 + 0.45 * np.sin(2 * np.pi * 0.22 * t)
    bed = (0.065 * np.sin(2 * np.pi * 65.41 * t) + 0.032 * np.sin(2 * np.pi * 130.81 * t)) * pulse_env

    # Soft mechanical metronome click every 0.5s (120 BPM crisp editorial pacing)
    step = int(sr * 0.5)
    clen = int(sr * 0.028)
    ct = np.linspace(0, 0.028, clen, dtype=np.float32)
    click = 0.035 * np.sin(2 * np.pi * 1280 * ct) * np.exp(-ct * 145)
    for pos in range(0, n - clen, step):
        bed[pos:pos + clen] += click

    def add_stamp_thud(t0, amp=0.30):
        i0 = int(t0 * sr)
        dur = 0.28
        L = min(int(dur * sr), n - i0)
        if i0 < 0 or L <= 0:
            return
        lt = np.linspace(0, dur, L, dtype=np.float32)
        freq = 125.0 * (42.0 / 125.0) ** (lt / dur)
        phase = 2 * np.pi * np.cumsum(freq) / sr
        bed[i0:i0 + L] += amp * np.sin(phase) * np.exp(-lt * 11.0)

    def add_paper_whoosh(t0, amp=0.14):
        i0 = int(t0 * sr)
        dur = 0.35
        L = min(int(dur * sr), n - i0)
        if i0 < 0 or L <= 0:
            return
        rng = np.random.default_rng(int(t0 * 100) + 7)
        lt = np.linspace(0, dur, L, dtype=np.float32)
        noise = rng.normal(0, 1, L).astype(np.float32)
        # Simple low-pass smoothing
        kernel = np.ones(15, dtype=np.float32) / 15.0
        soft = np.convolve(noise, kernel, mode="same")
        env = np.clip(np.sin(np.pi * (lt / dur)), 0.0, 1.0) ** 1.5
        bed[i0:i0 + L] += amp * soft * env

    def add_winner_chord(t0):
        for off, freq in [(0.0, 261.63), (0.06, 329.63), (0.12, 392.00), (0.20, 523.25)]:
            i0 = int((t0 + off) * sr)
            dur = 1.2
            L = min(int(dur * sr), n - i0)
            if i0 < 0 or L <= 0:
                continue
            lt = np.linspace(0, dur, L, dtype=np.float32)
            bed[i0:i0 + L] += 0.11 * np.sin(2 * np.pi * freq * lt) * np.exp(-lt * 2.4)

    for ct_elim in elim_cues:
        add_stamp_thud(ct_elim, amp=0.28)
    for ct_act in act_cues:
        add_paper_whoosh(ct_act, amp=0.16)
    if winner_t is not None:
        add_winner_chord(winner_t)

    fade = min(int(sr * 0.4), n // 4)
    if fade > 0:
        bed[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        bed[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)

    bed = np.nan_to_num(bed, nan=0.0, posinf=0.95, neginf=-0.95)
    bed = np.clip(bed, -0.95, 0.95)
    stereo = np.stack([bed, bed], axis=-1)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def mix_voice_and_sfx(voice_mp3, sfx_wav, out_m4a, total_dur):
    subprocess.run([
        FFMPEG, "-y",
        "-i", voice_mp3,
        "-i", sfx_wav,
        "-filter_complex",
        "[0:a]volume=1.18,apad=pad_dur=2.0[v];[1:a]volume=0.78[s];[v][s]amix=inputs=2:duration=shortest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]",
        "-map", "[out]", "-c:a", "aac", "-b:a", "192k", "-t", f"{total_dur:.3f}", out_m4a
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
