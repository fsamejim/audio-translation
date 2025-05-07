import os
from dotenv import load_dotenv
# from pathlib import Path
from openai import OpenAI

# env_path = Path(__file__).parent / ".env"
#print(f"🧪 Checking for .env at: {env_path}")

# Try to load explicitly
##load_dotenv(dotenv_path=env_path)

# Check result
#api_key = os.getenv("OPENAI_API_KEY")

import re
import textwrap
import time


load_dotenv()  # This loads .env file into environment

# === CONFIG ===
API_KEY = os.getenv("OPENAI_API_KEY")
INPUT_FILE = os.getenv("English_Text")
CHUNK_DIR = "chunks"
CHUNK_WIDTH = 3000
MAX_RETRIES = 3

if not API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set. Did you load .env correctly?")

# === INIT ===
client = OpenAI(api_key=API_KEY)
os.makedirs(CHUNK_DIR, exist_ok=True)

# === STEP 1: Read and split input ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    english_transcript = f.read()

chunks = textwrap.wrap(english_transcript, width=CHUNK_WIDTH)
print(f"Total chunks: {len(chunks)}")

# === STEP 2: Translate each chunk and save ===
for idx, chunk in enumerate(chunks, start=1):
    out_file = os.path.join(CHUNK_DIR, f"chunk_{idx:03}.txt")
    if os.path.exists(out_file):
        print(f"✅ Chunk {idx:03} already exists. Skipping.")
        continue

    print(f"🔁 Translating chunk {idx}/{len(chunks)}...")

    messages = [
     	{
        	"role": "system",
        	"content": (
                "You are a professional translator. Translate the following English dialogue into natural, sincere spoken Japanese, as if it were a respectful and heartfelt conversation between two older men. "
                "The tone should feel like a mature discussion between two lifelong friends or seasoned individuals — warm, humble, and spoken, yet carrying dignity and emotional depth. "
                "Avoid stiff or formal language. Use natural phrasing that fits a spoken tone, suitable for an audiobook, podcast, or sincere AA talk. "
                "Do not change or translate the speaker labels — keep 'Speaker A:' and 'Speaker B:' exactly as they are. "
                "Do not use labels like '話者', 'スピーカー', or 'Speaker 1/2'. "
                "Preserve line breaks and paragraph structure. "
                "If the English contains informal expressions or contractions like 'don’t' or 'gonna', reflect that informality naturally in Japanese."
            )
    	},
        {
            "role": "user",
            "content": chunk
        }
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=os.getenv("MODEL_NAME") ### like "gpt-4",
                messages=messages
            )
            content = response.choices[0].message.content.strip()
            if not content:
                raise ValueError("Empty response.")

            # Normalize speaker tags (failsafe)
            content = re.sub(r"(話者\s*A|スピーカー\s*A|Speaker\s*1|SpeakerＡ)", "Speaker A:", content)
            content = re.sub(r"(話者\s*B|スピーカー\s*B|Speaker\s*2|SpeakerＢ)", "Speaker B:", content)

            # Insert 2 line breaks between speaker changes
            lines = content.splitlines()
            output_lines = []
            last_speaker = None
            for line in lines:
                match = re.match(r"^(Speaker [AB]):", line.strip())
                if match:
                    speaker = match.group(1)
                    if last_speaker and speaker != last_speaker:
                        output_lines.append("")  # first line break
                        output_lines.append("")  # second line break
                    last_speaker = speaker
                output_lines.append(line)

            content = "\n".join(output_lines)

            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Saved: {out_file}")
            break

        except Exception as e:
            print(f"❌ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                print(f"💥 Giving up on chunk {idx}")
            else:
                time.sleep(5)