from google.cloud import texttospeech  # Google Cloud Text-to-Speech API
from pydub import AudioSegment         # For audio merging and editing
import glob                            # For file matching
import os                              # For file and folder operations
import sys                             # For exiting the program
import textwrap                        # For safely splitting long text
import time                            # For pause between API calls
import re                              # For regex filtering during merge

# Max character length per TTS request (stay under 5000 char limit)
MAX_TTS_LENGTH = 4000

# Exit early if not run as main script
if __name__ != "__main__":
    sys.exit(0)

# Load dialogue from a text file (expects "Speaker: text" per line)
def load_dialogue_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    dialogue = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue  # Skip blank or malformed lines
            speaker, text = line.split(":", 1)
            dialogue.append((speaker.strip(), text.strip()))
    return dialogue

# Generate MP3 audio chunks using Google TTS for each speaker line
def generate_audio_chunks(dialogue):
    SERVICE_ACCOUNT_PATH = "google_json/json_local.json" #Set access json for Google api
    client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_PATH)

    # Set specific voice model for each speaker
    SPEAKER_VOICES = {
        "Speaker A": "ja-JP-Wavenet-C",
        "Speaker B": "ja-JP-Wavenet-D",
        "Speaker C": "ja-JP-Wavenet-A",
    }

    os.makedirs("output", exist_ok=True)  # Create output directory if not exists

    for i, (speaker, text) in enumerate(dialogue):
        print(f"[INFO] Processing {speaker}, entry {i + 1}/{len(dialogue)}")

        # Split long text into chunks to fit API limit
        chunks = textwrap.wrap(text, width=MAX_TTS_LENGTH, break_long_words=False)
        for j, chunk in enumerate(chunks):
            filename = f"output/{i:02d}_{speaker.replace(' ', '_')}_{j + 1}.mp3"

            # Skip if audio file already exists
            if os.path.exists(filename):
                print(f"    ⏩ Skipping existing: {filename}")
                continue

            print(f"    [CHUNK] {speaker} chunk {j + 1}/{len(chunks)} (Length: {len(chunk)})")

            # Prepare input text for TTS
            synthesis_input = texttospeech.SynthesisInput(text=chunk)

            # Select voice based on speaker tag
            voice_name = SPEAKER_VOICES.get(speaker, "ja-JP-Wavenet-C")
            print(f"    [VOICE] Using voice: {voice_name}")

            voice = texttospeech.VoiceSelectionParams(
                language_code="ja-JP",
                name=voice_name
            )

            # Set audio format and speaking rate
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.2  # Adjust speaking speed if desired
            )

            try:
                # Generate speech from text
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )

                # Write audio to file
                with open(filename, "wb") as out:
                    out.write(response.audio_content)
                print(f"    ✅ Saved: {filename}")

            except Exception as e:
                print(f"    ❌ Error at entry {i}, chunk {j}: {e}")
                continue  # Skip problematic chunk

            time.sleep(0.5)  # Delay to avoid hitting API rate limits

# Merge all generated MP3 files into one final output file
def merge_audio_chunks(output_dir="output", result_path="full_conversation.mp3", pause_ms=1000):
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms)  # Add silence between segments

    # Filter only files that match the expected numbered chunk pattern
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
        combined += audio + pause  # Append audio with pause

    combined.export(result_path, format="mp3")
    print(f"✅ Merged audio saved as '{result_path}'")

# Main execution: read dialogue, generate audio, and merge it
# Set input file here
if __name__ == "__main__":
    dialogue = load_dialogue_from_file("../translate-text/transcript_ja_02.txt")
    generate_audio_chunks(dialogue)
    merge_audio_chunks()
    print("🎉 Done!")
    