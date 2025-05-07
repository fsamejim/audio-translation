from google.cloud import texttospeech
from pydub import AudioSegment
import glob
import os
import sys

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

# Load from file
dialogue = load_dialogue_from_file("../translate-text/chunks/chunk_001.txt")

# Set this to your actual path
SERVICE_ACCOUNT_PATH = "google_json/json_local.json"  # ← Change this!

# Initialize the client
client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_PATH)

# Speaker voice settings (change if you want different combinations)
SPEAKER_VOICES = {
    "Speaker A": "ja-JP-Wavenet-C",
    "Speaker B": "ja-JP-Wavenet-D"
}

# Create output folder
os.makedirs("output", exist_ok=True)

# Loop through and generate audio
for i, (speaker, text) in enumerate(dialogue):
    print(f"Processing {speaker}: {text}")
    
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=SPEAKER_VOICES.get(speaker, "ja-JP-Wavenet-C")
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.1  # 1.0 = normal, <1 = slower, >1 = faster
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    filename = f"output/{i:02d}_{speaker.replace(' ', '_')}.mp3"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

print("✅ All segments generated in the 'output/' folder.")


# 🔄 Combine all MP3s in output folder in sorted order
def merge_audio_chunks(output_dir="output", result_path="full_conversation.mp3", pause_ms=1000):
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms)

    files = sorted(glob.glob(os.path.join(output_dir, "*.mp3")))
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

# Call the merge function
merge_audio_chunks()

# 🏁 Run everything
if __name__ == "__main__":
    dialogue = load_dialogue_from_file("dialogue.txt")
    generate_audio_chunks(dialogue)
    merge_audio_chunks()
    print("🎉 Done!")


