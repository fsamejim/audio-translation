import assemblyai as aai
from dotenv import load_dotenv
from pathlib import Path
import os
import glob

# === CONFIGURATION ===
CHUNKS_FOLDER = "processed_audio/chunks"
OUTPUT_FILE = "transcript_en_08_full.txt"
API_KEY_ENV_VAR = "assemblyai_KEY"

# === SETUP ===
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

aai.settings.api_key = os.getenv(API_KEY_ENV_VAR)
if not aai.settings.api_key:
    raise EnvironmentError("Missing AssemblyAI API key in .env")

# === CONFIG ===
config = aai.TranscriptionConfig(
    speech_model=aai.SpeechModel.best,
    speaker_labels=True
)

transcriber = aai.Transcriber(config=config)

# === TRANSCRIBE EACH CHUNK ===
chunk_files = sorted(glob.glob(f"{CHUNKS_FOLDER}/chunk_*.wav"))

if not chunk_files:
    raise FileNotFoundError("No chunk files found in folder")

with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    for chunk_path in chunk_files:
        print(f"🎙 Transcribing: {chunk_path}")
        transcript = transcriber.transcribe(chunk_path)

        if transcript.status == "error":
            print(f"❌ Transcription failed for {chunk_path}: {transcript.error}")
            continue

        # Save each speaker-marked line
        for utterance in transcript.utterances:
            outfile.write(f"Speaker {utterance.speaker}: {utterance.text}\n")

        outfile.write("\n--- End of chunk ---\n\n")

print(f"✅ Merged transcript saved to: {OUTPUT_FILE}")