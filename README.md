# audio-translation
Audio translation from one language to another

###
# main objective
# translate English Audio file into the Japanese Audio File
# the audio is made with 2 person conversation
###

#
# sub objective
# determin what tool to extract the English text from English audio file
# requires Separate Speakers (Diarization)
#
 https://www.assemblyai.com
 Up to 460 hours free


#
# sub objective
# determin what tool to convert the English text to Japanese text
# requires script tagging as Separate Speakers (Diarization)
#
 create API_KEY
 https://platform.openai.com/settings/organization/api-keys

#
# sub objective
# determin what tool to generate the Japanese audio file from the Japanese text
# requires script tagging as Separate Speakers (Diarization)
#
Set up Google Cloud
	1.	Go to Google Cloud Console
	2.	Create a project (or use an existing one)
	3.	Enable the Text-to-Speech API for your project
		✅ 1. Enable the Cloud Text-to-Speech API
		Go here:
		👉 https://console.cloud.google.com/marketplace/product/google/texttospeech.googleapis.com

		✅ 2. Create credentials (Service Account)
		Go to:
		👉 https://console.cloud.google.com/apis/credentials
	•	Click “Create Credentials” → “Service Account”
	•	Assign basic role: Project > Editor
	4.	Create a service account key:
	•	Go to: IAM & Admin > Service Accounts
	•	Create service account → Give it a name and basic role (e.g., Editor)
	•	Create and download a JSON key file
#
# to setup environment
#
git clone git@github.com:your-username/audio-translation.git
cd audio-translation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

=== new Mac
brew install pyenv
✗ which pyenv
/opt/homebrew/bin/pyenv
Code VS setup
echo 'eval "$(pyenv init --path)"' >> ~/.zprofile
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
exec "$SHELL"

% git commit -m "[sammy]Add message"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# Process Workflow
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# Step1: Extract text script from audio
#
extract-audio/assemblescript.py
Use assembllyai api to extract native text from the audio.
assembllyai supports diarization

extract-audio/massage_text.py
Make human readable format with speaker tags at the beginning
#
# Step2: Translate the native text script into Japanese
#
translate-text/translate_chunks.py
Use OpenAI api to translate the native language into Japanese.
This script creates chunks text in the chunks folder.(error handling/retry)

translate-text/merge_chunks.py
Consodidate all chunks texts into one script
#
# Step3: Generate the mp3 audio file with Japanese
# Use Google api for the audio creation 
generate-audio/multi_speaker_tts.py 
Accomodate with safe limits, retry, error handling
When the process hand, re-use the existing result audio produced in the output folder
This, jsut re-run again.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

#
# Note:
#
git add README.md generate-audio/multi_speaker_tts.py translate-text/merge_chunks.py translate-text/translate_chunks.py
git commit -m "[sammy] Update README and scripts for audio translation and merging"

Using VS Code as a code editor on Mac (Mac terminal environment is different from VS terminal)
Shell Command: Install 'code' command in PATH (This will install the code CLI tool and allow you to run: code .)

At root repository folder, run : 
source .venv/bin/activate

pip install openai
pip install pydub
brew install ffmpeg 

pip freeze > requirements.txt





