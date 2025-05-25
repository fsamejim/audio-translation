import re
import os

# Input and output file paths
input_path = "transcript_ja_08.txt"  
output_path = "transcript_ja_08_done.txt"

def clean_japanese_dialogue(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        return

    # Read raw input
    with open(input_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Normalize line endings
    raw_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove all chunk header lines like "=== TRANSLATION CHUNK chunk_006.txt ==="
    raw_text = re.sub(r"^=== TRANSLATION CHUNK chunk_\\d{3}\\.txt ===\\s*", "", raw_text, flags=re.MULTILINE)

    # Remove non-printable or problematic characters (safe for TTS)
    raw_text = re.sub(r'[^\x20-\x7E\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF。、「」！？\sA-Za-z0-9:：]', '', raw_text)

    # Split into speaker blocks, allowing both full-width and half-width colons
    speaker_blocks = re.split(r'(?=Speaker [A-Z][:：])', raw_text)
    cleaned_blocks = []

    for block in speaker_blocks:
        block = block.strip()
        if not block:
            continue

        # Merge lines inside each speaker's block
        lines = block.splitlines()
        merged = lines[0]  # Keep the speaker tag + first line
        for line in lines[1:]:
            merged += line.strip()  # Remove internal newlines
        cleaned_blocks.append(merged)

    if not cleaned_blocks:
        print("⚠️ No speaker blocks found. Check your input file formatting.")
        return

    # Join with two line breaks between speakers
    final_output = "\n\n".join(cleaned_blocks)

    # Save to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_output)

    print(f"✅ Cleaned {len(cleaned_blocks)} speaker blocks.")
    print(f"📄 Saved to: {output_path}")

# Run the function
clean_japanese_dialogue(input_path, output_path)
