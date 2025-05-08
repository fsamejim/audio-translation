from google.cloud import texttospeech
from pydub import AudioSegment
import glob
import os
import sys
import textwrap
import time
import re

MAX_TTS_LENGTH = 4000  # keep it safely below the 5000 limit

if __name__ != "__main__":
    sys.exit(0)

def load_dialogue_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    dialogue = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            speaker, text = line.split(":", 1)
            dialogue.append((speaker.strip(), text.strip()))
    return dialogue

def generate_audio_chunks(dialogue):
    SERVICE_ACCOUNT_PATH = "google_json/json_local.json"
    client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_PATH)

    SPEAKER_VOICES = {
        "Speaker A": "ja-JP-Wavenet-C",
        "Speaker B": "ja-JP-Wavenet-D",
        "Speaker C": "ja-JP-Wavenet-A",
    }

    os.makedirs("output", exist_ok=True)

    for i, (speaker, text) in enumerate(dialogue):
        print(f"[INFO] Processing {speaker}, entry {i + 1}/{len(dialogue)}")

        chunks = textwrap.wrap(text, width=MAX_TTS_LENGTH, break_long_words=False)
        for j, chunk in enumerate(chunks):
            filename = f"output/{i:02d}_{speaker.replace(' ', '_')}_{j + 1}.mp3"
            if os.path.exists(filename):
                print(f"    ⏩ Skipping existing: {filename}")
                continue

            print(f"    [CHUNK] {speaker} chunk {j + 1}/{len(chunks)} (Length: {len(chunk)})")

            synthesis_input = texttospeech.SynthesisInput(text=chunk)

            voice_name = SPEAKER_VOICES.get(speaker, "ja-JP-Wavenet-C")
            print(f"    [VOICE] Using voice: {voice_name}")

            voice = texttospeech.VoiceSelectionParams(
                language_code="ja-JP",
                name=voice_name
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.2
            )

            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                with open(filename, "wb") as out:
                    out.write(response.audio_content)
                print(f"    ✅ Saved: {filename}")

            except Exception as e:
                print(f"    ❌ Error at entry {i}, chunk {j}: {e}")
                continue  # skip this chunk

            time.sleep(0.5)

def merge_audio_chunks(output_dir="output", result_path="full_conversation.mp3", pause_ms=1000):
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms)

    files = sorted([
      f for f in glob.glob(os.path.join(output_dir, "*.mp3"))
      if re.search(r"_\d+\.mp3$", f)
    ])
    print(f"[DEBUG] Found {len(files)} files to merge.")

    if not files:
        print("❌ No MP3 files found to merge.")
        return

    print("🔊 Merging audio chunks...")
    for f in files:
        print(f"  Adding {f}")
        audio = AudioSegment.from_mp3(f)
        combined += audio + pause

    combined.export(result_path, format="mp3")
    print(f"✅ Merged audio saved as '{result_path}'")

if __name__ == "__main__":
    dialogue = load_dialogue_from_file("../translate-text/transcript_ja_01_done.txt")
    generate_audio_chunks(dialogue)
    merge_audio_chunks()
    print("🎉 Done!")

