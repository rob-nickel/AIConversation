# AIConversation
Audible conversations with AI-voiced figures and characters.

## SETUP:
1) This was written in Python 3.9.6. Install page here: https://www.python.org/downloads/release/python-396/

2) Run `pip install -r requirements.txt` to install all modules.

3) This uses the Microsoft Azure TTS, ElevenLabs, and OpenAi services. You'll need to set up an account with these services and generate an API key from them. Then add these keys at the top of azure_speech_to_text.py, eleven_labs.py, and openai_chat.py respectively. Each is marked with a "TODO"

4) This app uses the GPT-4 model from OpenAi. As of this writing, you need to pay $1 to OpenAi in order to get access to the GPT-4 model API. So after setting up your account with OpenAi, you will need to pay for at least $1 in credits so that your account is given the permission to use the GPT-4 model when running the app. See here: https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4

5) ElevenLabs is the service used for these AI voices. Once you've made an AI voice on the ElevenLabs website, open up chatgpt_character.py and replace the `ELEVENLABS_VOICE` variable with the name of your voice.

6) Write your own characters and create a .txt file within the `scenario_strings` folder. Include this in the `SCENARIO_FILE` variable within chatgpt_character.py.

## Using the App

1) Run `chatgpt_character.py` followed by the character from the `voice_settings` variable within that file (`abe`, `clown`, etc.).

2) Once it's running, press 4 to start the conversation, and Azure Speech-to-Text will listen to your microphone and transcribe it into text.

3) Once you're done talking, press P. Then the code will send all of the recorded text to the AI. Note that you should wait a second or two after you're done talking before pressing P so that Azure has enough time to process all of the audio.

4) Wait a few seconds for OpenAi to generate a response and for ElevenLabs to turn that response into audio. Once it's done playing the response, you can press F4 to start the loop again and continue the conversation.
