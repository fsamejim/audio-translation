import os
import re
import time
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# === CONFIGURATION ===
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR.parent / "joe-charlie-aa-js/test-output/EN-audio-text-output/joe-charlie-first-5-minutes.txt"

def main():
    # === SETUP ===
    # Load .env from parent of current file
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   # CHUNK_DIR = "chunks"
    CHUNK_DIR = SCRIPT_DIR.parent / "joe-charlie-aa-js/test-output/JP-text-translation/chunks"
    TRANSLATION_CHUNK_WIDTH = int(os.getenv("TRANSLATION_CHUNK_WIDTH", "3000"))
    TRANSLATION_MAX_RETRIES = int(os.getenv("TRANSLATION_MAX_RETRIES", "4"))
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
    ENABLE_TAG_NORMALIZATION = True
    
    print(f"🔍 Model: {OPENAI_MODEL_NAME}, Chunk width: {TRANSLATION_CHUNK_WIDTH}, Retries: {TRANSLATION_MAX_RETRIES}")
    
    if not OPENAI_API_KEY or not OPENAI_MODEL_NAME or not INPUT_FILE:
        raise RuntimeError("❌ Missing required environment variables (OPENAI_API_KEY, OPENAI_MODEL_NAME, English_Text)")

    client = OpenAI(api_key=OPENAI_API_KEY)
    os.makedirs(CHUNK_DIR, exist_ok=True)

    def is_speaker_line(line):
        return bool(re.match(r"^Speaker [A-Z]:", line.strip()))

    def split_long_block(block_lines, max_chars):
        if not block_lines:
            return []
        header_match = re.match(r"^(Speaker [A-Z]:)", block_lines[0].strip())
        speaker_label = header_match.group(1) if header_match else "Speaker X:"
        content = "\n".join(block_lines)
        sentences = re.split(r'(?<=[.?!])\s+', content)
        chunks = []
        current_chunk = speaker_label + " "
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = speaker_label + " " + sentence
            else:
                current_chunk += sentence
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    # === STEP 1: Speaker-aware chunking ===
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if not is_speaker_line(lines[0]):
        print("⚠️ First line is missing a speaker label. Assuming 'Speaker B:'")
        lines[0] = f"Speaker B: {lines[0]}"

    chunks = []
    current_block = []

    for line in lines:
        if is_speaker_line(line):
            if current_block:
                block_text = "\n".join(current_block)
                if len(block_text) > TRANSLATION_CHUNK_WIDTH:
                    sub_blocks = split_long_block(current_block, TRANSLATION_CHUNK_WIDTH)
                    chunks.extend(sub_blocks)
                else:
                    chunks.append(block_text)
                current_block.clear()
        current_block.append(line)

    if current_block:
        block_text = "\n".join(current_block)
        if len(block_text) > TRANSLATION_CHUNK_WIDTH:
            sub_blocks = split_long_block(current_block, TRANSLATION_CHUNK_WIDTH)
            chunks.extend(sub_blocks)
        else:
            chunks.append(block_text)

    print(f"🔹 Total speaker-safe chunks: {len(chunks)}")

    # === STEP 2: Translate and save each chunk ===
    for idx, chunk in enumerate(chunks, start=1):
        out_file = os.path.join(CHUNK_DIR, f"chunk_{idx:03}.txt")
        if os.path.exists(out_file):
            print(f"✅ Chunk {idx:03} already exists. Skipping.")
            continue

        print(f"🔁 Translating chunk {idx}/{len(chunks)}...")

        if not re.match(r"^Speaker [A-Z]:", chunk.strip()):
            raise ValueError(f"❌ Chunk {idx} is missing a speaker tag at the top.")

        messages = [
            {
                "role": "system",
                "content": (
                    "This is well known Joe and Charlies's AA workshop conversation."
                    "You are a professional translator. Translate the following English dialogue into natural, sincere spoken Japanese, as if it were a respectful and heartfelt conversation between two older men. "
                    "The tone should feel like a mature discussion between two lifelong friends or seasoned individuals — warm, humble, and spoken, yet carrying dignity and emotional depth. "
                    "Avoid stiff or formal language. Use natural phrasing that fits a spoken tone, suitable for an audiobook, podcast, or sincere AA talk. "
                    "Use 僕 instead of 俺. Translate 'sobriety' as ソーバー (not 清酒). "
                    "Do not change or translate the speaker labels — keep 'Speaker A:' and 'Speaker B:' exactly as they are. "
                    "Do not use labels like '話者', 'スピーカー', or 'Speaker 1/2'. "
                    "Translate ALL English into natural spoken Japanese. Do not leave any part in English. Even if the sentence sounds like a quote, a slogan, or an AA motto, translate it. Do not preserve any English phrases. Keep the speaker labels exactly as they are (e.g., 'Speaker A:', 'Speaker B:')."
                    "Do not add or infer speaker tags if they are missing. Keep all line breaks and structure as-is."
                )
            },
            {
                "role": "user",
                "content": chunk
            }
        ]

        for attempt in range(1, TRANSLATION_MAX_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL_NAME,
                    messages=messages
                )
                content = response.choices[0].message.content.strip()
                if not content:
                    raise ValueError("Empty response.")

                if ENABLE_TAG_NORMALIZATION:
                    for i, speaker in enumerate(["A", "B", "C", "D", "E"], start=1):
                        pattern = fr"(話者\s*{speaker}|スピーカー\s*{speaker}|Speaker\s*{i}|Speaker{speaker})"
                        content = re.sub(pattern, f"Speaker {speaker}:", content)

                    lines = content.splitlines()
                    output_lines = []
                    last_speaker = None
                    speaker_pattern = "|".join([f"Speaker {s}" for s in ["A", "B", "C", "D", "E"]])
                    for line in lines:
                        match = re.match(fr"^({speaker_pattern}):", line.strip())
                        if match:
                            speaker = match.group(1)
                            if last_speaker and speaker != last_speaker:
                                output_lines.append("")
                                output_lines.append("")
                            last_speaker = speaker
                        output_lines.append(line)
                    content = "\n".join(output_lines)

                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"✅ Saved: {out_file}")
                break

            except Exception as e:
                print(f"❌ Attempt {attempt}/{TRANSLATION_MAX_RETRIES} failed: {e}")
                if attempt == TRANSLATION_MAX_RETRIES:
                    print(f"💥 Giving up on chunk {idx}")
                else:
                    time.sleep(5)

if __name__ == "__main__":
    main()