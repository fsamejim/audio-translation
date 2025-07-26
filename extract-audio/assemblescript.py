#!/usr/bin/env python

import time
import assemblyai as aai
from dotenv import load_dotenv
from pathlib import Path
import os
import glob

# === CONFIGURATION ===
SCRIPT_DIR = Path(__file__).resolve().parent
PREPROCESS_AUDIO_CHUNKS_FOLDER = SCRIPT_DIR.parent / "joe-charlie-aa-js/test-output/preprocess-audio/chunks"
EN_AUDIO_OUTPUT_TEXT_FILE = SCRIPT_DIR.parent / "joe-charlie-aa-js/test-output/EN-audio-text-output/joe-charlie-first-5-minutes.txt"

def main():
    # === SETUP ===
    # Load .env from parent of current file
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not aai.settings.api_key:
        raise EnvironmentError("Missing AssemblyAI API key in .env")

    # === CONFIG ===
    model_name = os.getenv("ASSEMBLYAI_MODEL", "best").lower()

    model_map = {
        "best": aai.SpeechModel.best,
        "nano": aai.SpeechModel.nano,
        "slam-1": aai.SpeechModel.slam_1,
        "universal": aai.SpeechModel.universal,
    }

    if model_name not in model_map:
        raise ValueError(f"Invalid ASSEMBLYAI_MODEL: '{model_name}'. Must be one of: {list(model_map.keys())}")

    speech_model = model_map[model_name]
    
    rate_limit_delay = float(os.getenv("TRANSCRIPTION_RATE_LIMIT_DELAY", "1"))

    '''
    Where the actual speaker determination happens:
    AssemblyAi uses Speaker A, B, C... lable
    AssemblyAI can detect speaker changes.
    It uses speaker diarization (clustering of voice characteristics) to detect when the speaker changes.
    Each change in vocal pattern (pitch, tone, cadence, etc.) is analyzed and clustered as a distinct speaker.
    In a 2-person conversation, the AssemblyAI is typically very accurate to distinguish the difference.
    It does not carry memory across files. Each audio is processed in isolation.
    Does not track speaker identity across files.
    '''
    use_diarization = os.getenv("USE_SPEAKER_DIARIZATION", "true").lower() == "true"
    config = aai.TranscriptionConfig(
        speech_model=speech_model,
        speaker_labels=use_diarization
    )

    transcriber = aai.Transcriber(config=config)

    # === TRANSCRIBE EACH CHUNK ===
    chunk_files = sorted(glob.glob(str(PREPROCESS_AUDIO_CHUNKS_FOLDER / "chunk_*.wav")))

    if not chunk_files:
        raise FileNotFoundError("No chunk files found in folder")

    os.makedirs(os.path.dirname(EN_AUDIO_OUTPUT_TEXT_FILE), exist_ok=True)
    with open(EN_AUDIO_OUTPUT_TEXT_FILE, "w", encoding="utf-8") as outfile:
        for chunk_path in chunk_files:
            print(f"🎙 Transcribing: {chunk_path}")
            transcript = transcriber.transcribe(chunk_path)

            if transcript.status == "error":
                print(f"❌ Transcription failed for {chunk_path}: {transcript.error}")
                continue

            # Save each speaker-marked line
            for utterance in transcript.utterances:
                outfile.write(f"Speaker {utterance.speaker}: {utterance.text}\n")

            time.sleep(rate_limit_delay)

    print(f"✅ Merged transcript saved to: {EN_AUDIO_OUTPUT_TEXT_FILE}")

if __name__ == "__main__":
    main()