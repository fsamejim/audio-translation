import assemblyai as aai
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from same directory as the script
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Set your API key
aai.settings.api_key = os.getenv("assemblyai_KEY")

print("Loaded API key:", aai.settings.api_key)  # Debug print

# Local file path
audio_file = os.getenv("AUDIO_FILE")

# Enable speaker diarization
config = aai.TranscriptionConfig(
    speech_model=aai.SpeechModel.best,
    speaker_labels=True
)

# Transcribe
transcriber = aai.Transcriber(config=config)
transcript = transcriber.transcribe(audio_file)

# Check for errors
if transcript.status == "error":
    raise RuntimeError(f"Transcription failed: {transcript.error}")

# Save transcript to file
with open("transcript_en_04.txt", "w", encoding="utf-8") as f:
    for utterance in transcript.utterances:
        f.write(f"Speaker {utterance.speaker}: {utterance.text}\n")