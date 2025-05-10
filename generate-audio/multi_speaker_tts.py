from google.cloud import texttospeech  # Google Cloud Text-to-Speech API
from pydub import AudioSegment         # For audio merging and silence insertion
import glob                            # For listing audio files
import os                              # For file and directory operations
import sys                             # For exiting early
import textwrap                        # For splitting long text safely
import time                            # For delaying between retries or API calls
import re                              # For filtering files with patterns

# === CONFIGURATION ===
MAX_TTS_LENGTH = 4000                          # Character limit per TTS call (Google's max is ~5000 bytes)
MAX_RETRIES = 3                                # Max retries for failed TTS calls
SERVICE_ACCOUNT_PATH = "google_json/sammy.json"  # Your Google Cloud credential JSON
INPUT_FILE = "../translate-text/transcript_ja_02_done.txt" # Input dialogue text file
OUTPUT_DIR = "output"                          # Where each MP3 chunk is saved
MERGED_FILE = "full_conversation.mp3"          # Final merged MP3 output
PAUSE_MS = 1000                                # Silence (ms) between merged chunks

# Exit early if not run as a script
if __name__ != "__main__":
    sys.exit(0)

# === FUNCTION: Load speaker-tagged dialogue from file ===
def load_dialogue_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    dialogue = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue  # Skip lines without "Speaker: text"
            speaker, text = line.split(":", 1)
            dialogue.append((speaker.strip(), text.strip()))
    return dialogue

# Helper function to clean text before sending to TTS API
def sanitize_input(text):
    import re
    text = text.replace('\u3000', ' ')                         # Convert full-width spaces to regular spaces
    text = text.replace('\r\n', '\n').replace('\r', '\n')      # Normalize all line endings to Unix style
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)                # Remove control characters (ASCII 0–31 + 127)
    text = text.encode("utf-8", errors="ignore").decode("utf-8")  # Remove invalid UTF-8 characters
    return text.strip()                                        # Remove leading/trailing whitespace

# Main function to generate audio MP3s from dialogue lines
def generate_audio_chunks(dialogue):
    from google.api_core.exceptions import GoogleAPICallError, RetryError

    # Initialize Google Text-to-Speech client with your service account
    client = texttospeech.TextToSpeechClient.from_service_account_file(SERVICE_ACCOUNT_PATH)

    # Map each speaker label to a Japanese voice model
    SPEAKER_VOICES = {
        "Speaker A": "ja-JP-Wavenet-C",
        "Speaker B": "ja-JP-Wavenet-D",
        "Speaker C": "ja-JP-Wavenet-A",
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)  # Create output directory if it doesn't exist
    failed_chunks = []  # List to collect failed audio chunks for retry/reporting

    # Loop through each line of speaker dialogue
    for i, (speaker, text) in enumerate(dialogue):
        print(f"[INFO] Processing {speaker}, entry {i + 1}/{len(dialogue)}")

        # Sanitize the text and split into smaller chunks if too long
        sanitized = sanitize_input(text)
        def split_text_by_bytes(text, byte_limit=4800):
            chunks = []
            current_chunk = ""
            for sentence in re.split(r'(?<=[。！？\n])', text):
                sentence = sentence.strip()
                if not sentence:
                    continue

                test_chunk = current_chunk + sentence
                if len(test_chunk.encode("utf-8")) > byte_limit:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk = test_chunk

            if current_chunk:
                chunks.append(current_chunk.strip())

            return chunks

        chunks = split_text_by_bytes(text)

        # Process each chunk individually (most often there is only one)
        for j, chunk in enumerate(chunks):
            filename = f"{OUTPUT_DIR}/{i:02d}_{speaker.replace(' ', '_')}_{j + 1}.mp3"

            # Skip if file already exists (resume safe)
            if os.path.exists(filename):
                print(f"    ⏩ Skipping existing: {filename}")
                continue

            print(f"    [CHUNK] {speaker} chunk {j + 1}/{len(chunks)} (Length: {len(chunk)})")
            voice_name = SPEAKER_VOICES.get(speaker, "ja-JP-Wavenet-C")
            print(f"    [VOICE] Using voice: {voice_name}")

            # Prepare input parameters for the TTS API
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ja-JP",
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.2  # You can adjust speed here
            )

            # Try up to MAX_RETRIES times if there's an error
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    print(f"    [API] Sending request (attempt {attempt})...")
                    response = client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config,
                        timeout=15  # Give up after 15 seconds if unresponsive
                    )

                    # Save the response audio content to file
                    with open(filename, "wb") as out:
                        out.write(response.audio_content)
                    print(f"    ✅ Saved: {filename}")
                    break  # Exit retry loop if successful

                except (GoogleAPICallError, RetryError, Exception) as e:
                    print(f"    ❌ Error on try {attempt}/{MAX_RETRIES} — {e.__class__.__name__}: {e}")
                    if attempt == MAX_RETRIES:
                        # Give up after max attempts
                        failed_chunks.append(f"{i:02d}_{speaker}_{j + 1}")
                    else:
                        # Wait before retrying
                        time.sleep(3)

            time.sleep(0.5)  # Delay between calls to avoid hitting API rate limits

    # Log any failed chunks to a file so you can retry them later
    if failed_chunks:
        with open("failed_audio_chunks.log", "w", encoding="utf-8") as f:
            for item in failed_chunks:
                f.write(f"{item}\n")
        print("⚠️ Some chunks failed. See 'failed_audio_chunks.log'.")

# === FUNCTION: Merge all MP3 chunks into a final single audio file ===
def merge_audio_chunks(output_dir=OUTPUT_DIR, result_path=MERGED_FILE, pause_ms=PAUSE_MS):
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=pause_ms)  # Insert silence between parts

    # Only include files that match our naming pattern
    files = sorted([
        f for f in glob.glob(os.path.join(output_dir, "*.mp3"))
        if re.search(r"_\d+(_\d+)?\.mp3$", f)
    ])
    print(f"[DEBUG] Found {len(files)} files to merge.")

    if not files:
        print("❌ No MP3 files found to merge.")
        return

    print("🔊 Merging audio chunks...")
    for f in files:
        print(f"  Adding {f}")
        audio = AudioSegment.from_mp3(f)
        combined += audio + pause  # Append with silence

    combined.export(result_path, format="mp3")
    print(f"✅ Merged audio saved as '{result_path}'")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    dialogue = load_dialogue_from_file(INPUT_FILE)  # Load speaker-tagged text
    generate_audio_chunks(dialogue)                 # Convert each line to MP3
    merge_audio_chunks()                            # Merge all MP3s into one
    print("🎉 Done!")
