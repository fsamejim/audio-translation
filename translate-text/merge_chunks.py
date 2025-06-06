import os
import re

CHUNK_DIR = "chunks"
OUTPUT_FILE = "transcript_ja_04.txt"

chunk_files = sorted(f for f in os.listdir(CHUNK_DIR) if f.startswith("chunk_") and f.endswith(".txt"))

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for chunk_file in chunk_files:
        chunk_path = os.path.join(CHUNK_DIR, chunk_file)
        with open(chunk_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        # Optional: mark chunk boundary
        out.write(f"\n\n=== TRANSLATION CHUNK {chunk_file} ===\n")

        last_speaker = None
        for line in lines:
            match = re.match(r"^(Speaker [AB]):", line.strip())
            if match:
                speaker = match.group(1)
                if last_speaker and speaker != last_speaker:
                    out.write("\n\n")  # 🔸 Insert two line breaks between speaker switches
                last_speaker = speaker

            out.write(line + "\n")

print(f"✅ Merged {len(chunk_files)} chunks into {OUTPUT_FILE} with double line breaks between speakers.")
