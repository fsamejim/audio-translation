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

Note:

Using VS Code as a code editor on Mac (Mac terminal environment is different from VS terminal)
Shell Command: Install 'code' command in PATH (This will install the code CLI tool and allow you to run: code .)

At root repository folder, run : 
source .venv/bin/activate

pip install openai
pip install pydub
brew install ffmpeg 

pip freeze > requirements.txt





