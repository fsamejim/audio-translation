from pydub import AudioSegment, effects, silence
import os
import math

# === CONFIGURATION ===
INPUT_AUDIO_PATH = "Geoffrey_Hinton_org.mp3"
OUTPUT_AUDIO_PATH = "Geoffrey_Hinton_enhanced.wav"
CHUNK_DIR = "processed_audio/chunks"
TARGET_SAMPLE_RATE = 16000
SILENCE_THRESH_DB = -40
PADDING_MS = 500
NORMALIZATION_TARGET_DBFS = -20
CHUNK_DURATION_MS = 15 * 60 * 1000  # 15 minutes

def preprocess_audio(input_path: str, output_path: str, sample_rate: int = 16000):
    print(f"🔊 Loading audio from: {input_path}")
    audio = AudioSegment.from_file(input_path)

    # Convert to mono and target sample rate
    audio = audio.set_channels(1).set_frame_rate(sample_rate)

    # Normalize audio
    normalized_audio = effects.normalize(audio)
    if normalized_audio.dBFS < NORMALIZATION_TARGET_DBFS:
        gain_needed = NORMALIZATION_TARGET_DBFS - normalized_audio.dBFS
        print(f"📈 Boosting volume by {gain_needed:.2f} dB")
        normalized_audio = normalized_audio.apply_gain(gain_needed)

    print(f"📉 Volume after normalization: {normalized_audio.dBFS:.2f} dBFS")

    # Remove silence
    nonsilent_ranges = silence.detect_nonsilent(
        normalized_audio,
        min_silence_len=500,
        silence_thresh=normalized_audio.dBFS + SILENCE_THRESH_DB
    )

    if not nonsilent_ranges:
        raise ValueError("❌ No non-silent segments found.")

    cleaned_audio = AudioSegment.silent(duration=0)
    for start_ms, end_ms in nonsilent_ranges:
        start_ms = max(0, start_ms - PADDING_MS)
        end_ms = min(len(normalized_audio), end_ms + PADDING_MS)
        cleaned_audio += normalized_audio[start_ms:end_ms]

    cleaned_duration_sec = len(cleaned_audio) / 1000
    print(f"⏱ Cleaned duration: {cleaned_duration_sec:.2f} seconds")

    # Export full cleaned file, if the target file not exist, cleate it
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    cleaned_audio.export(output_path, format="wav")
    print(f"✅ Exported cleaned audio to: {output_path}")

    # Split into chunks
    split_audio(cleaned_audio, CHUNK_DIR, CHUNK_DURATION_MS)

def split_audio(audio: AudioSegment, output_dir: str, chunk_duration_ms: int):
    total_length_ms = len(audio)
    total_chunks = math.ceil(total_length_ms / chunk_duration_ms)

    print(f"📦 Splitting into {total_chunks} chunk(s) of {chunk_duration_ms / 1000:.0f} seconds each")
    os.makedirs(output_dir, exist_ok=True)

    for i in range(total_chunks):
        start = i * chunk_duration_ms
        end = min((i + 1) * chunk_duration_ms, total_length_ms)
        chunk = audio[start:end]

        chunk_filename = os.path.join(output_dir, f"chunk_{i+1:02}.wav")
        chunk.export(chunk_filename, format="wav")
        print(f"✅ Saved: {chunk_filename} ({len(chunk) / 1000:.2f} sec)")

    print("🎉 All chunks saved.")

if __name__ == "__main__":
    preprocess_audio(INPUT_AUDIO_PATH, OUTPUT_AUDIO_PATH)
