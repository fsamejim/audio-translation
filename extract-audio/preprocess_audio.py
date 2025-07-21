#!/usr/bin/env python3
"""
Audio Preprocessing Script
- Normalize audio to improve transcription accuracy
- Remove silence and clean the audio
- Perform smart silence-aware chunking (4-6 min)
"""

from pydub import AudioSegment, effects, silence
import os
import math

# === CONFIGURATION ===
# Path to your input MP3 file
INPUT_AUDIO_PATH = "/Users/sammy.samejima/privatespace/audio-translation/joe-charlie-aa-js/test-data/joe-charlie-first-15-minutes.mp3"
# Output path for the cleaned WAV version of the audio
OUTPUT_AUDIO_PATH = "/Users/sammy.samejima/privatespace/audio-translation/joe-charlie-aa-js/test-output/joe-charlie-first-15-minutes.wav"
# Directory where audio chunks will be saved
CHUNK_DIR = "preprocess_audio/chunks"

# Audio preprocessing settings
TARGET_SAMPLE_RATE = 16000                # For speech recognition systems
PADDING_MS = 500                          # Add buffer before and after non-silent audio
NORMALIZATION_TARGET_DBFS = -20           # Ideal volume level for clean voice audio
MIN_CHUNK_MS = 4 * 60 * 1000              # Minimum chunk size: 4 minutes
MAX_CHUNK_MS = 6 * 60 * 1000              # Maximum chunk size: 6 minutes

def preprocess_audio(input_path: str, output_path: str, sample_rate: int = 16000):
    print(f"🔊 Loading audio from: {input_path}")
    
    # Load and downmix audio to mono with target sample rate
    audio = AudioSegment.from_file(input_path).set_channels(1).set_frame_rate(sample_rate)

    # Normalize loudness to improve transcription accuracy
    normalized_audio = effects.normalize(audio)
    if normalized_audio.dBFS < NORMALIZATION_TARGET_DBFS:
        gain_needed = NORMALIZATION_TARGET_DBFS - normalized_audio.dBFS
        print(f"📈 Boosting volume by {gain_needed:.2f} dB")
        normalized_audio = normalized_audio.apply_gain(gain_needed)

    print(f"📉 Volume after normalization: {normalized_audio.dBFS:.2f} dBFS")

    # Silence threshold: adapt based on actual audio loudness (fallback at -40 dBFS)
    silence_thresh_db = min(-40, normalized_audio.dBFS - 10)
    print(f"🔍 Silence threshold set to: {silence_thresh_db:.2f} dBFS")

    # Detect non-silent regions
    nonsilent_ranges = silence.detect_nonsilent(
        normalized_audio,
        min_silence_len=500,
        silence_thresh=silence_thresh_db
    )

    # If no silence detected, just use the full audio
    if not nonsilent_ranges:
        print("⚠️ No silent segments detected — processing full audio without trimming.")
        cleaned_audio = normalized_audio
    else:
        # Merge all non-silent regions with padding
        cleaned_audio = AudioSegment.silent(duration=0)
        for start_ms, end_ms in nonsilent_ranges:
            start_ms = max(0, start_ms - PADDING_MS)
            end_ms = min(len(normalized_audio), end_ms + PADDING_MS)
            cleaned_audio += normalized_audio[start_ms:end_ms]

    # Report final cleaned length
    cleaned_duration_sec = len(cleaned_audio) / 1000
    print(f"⏱ Cleaned duration: {cleaned_duration_sec:.2f} seconds")

    # Save cleaned WAV file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cleaned_audio.export(output_path, format="wav")
    print(f"✅ Exported cleaned audio to: {output_path}")

    # If short audio, save as single chunk
    if len(cleaned_audio) <= MAX_CHUNK_MS:
        print("🧩 Audio is short — saving as single chunk.")
        os.makedirs(CHUNK_DIR, exist_ok=True)
        cleaned_audio.export(os.path.join(CHUNK_DIR, "chunk_01.wav"), format="wav")
    else:
        # Perform smart silence-aware chunking
        smart_chunk_audio(cleaned_audio, CHUNK_DIR, MIN_CHUNK_MS, MAX_CHUNK_MS)

def smart_chunk_audio(audio: AudioSegment, output_dir: str, min_chunk_ms: int, max_chunk_ms: int):
    """
    Split audio intelligently on silence, aiming for chunks between min and max duration
    """
    os.makedirs(output_dir, exist_ok=True)

    # Detect silence ranges to find split points
    silence_thresh_db = min(-40, audio.dBFS - 10)
    silent_ranges = silence.detect_silence(
        audio,
        min_silence_len=300,
        silence_thresh=silence_thresh_db
    )

    current_pos = 0
    chunk_index = 1

    while current_pos < len(audio):
        target_end = min(current_pos + max_chunk_ms, len(audio))

        # Find nearest silence point after min_chunk_ms
        candidate_silences = [
            s for s in silent_ranges if current_pos + min_chunk_ms <= s[0] <= target_end
        ]

        best_split = candidate_silences[0][0] if candidate_silences else target_end

        # Extract chunk and export
        chunk = audio[current_pos:best_split]
        chunk_filename = os.path.join(output_dir, f"chunk_{chunk_index:02}.wav")
        chunk.export(chunk_filename, format="wav")
        print(f"✅ Saved: {chunk_filename} ({len(chunk)/1000:.2f} sec)")

        current_pos = best_split
        chunk_index += 1

    print("🎉 All smart chunks saved.")

if __name__ == "__main__":
    preprocess_audio(INPUT_AUDIO_PATH, OUTPUT_AUDIO_PATH)