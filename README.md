# AIConversation
Audible interviews and conversations with AI-voiced figures and characters. Have them with 1 character or between 3 characters.

## SETUP:
1) This was written in Python 3.9.6. Install page here: https://www.python.org/downloads/release/python-396/

2) Run `pip install -r requirements.txt` to install all modules.

3) This uses the Microsoft Azure TTS, ElevenLabs, and OpenAi services. You'll need to set up an account with these services and generate an API key from them. Then add these keys at the top of azure_speech_to_text.py, eleven_labs.py, and openai_chat.py respectively. Each is marked with a "TODO".

4) This app uses the GPT-4-Turbo model from OpenAi. As of this writing, you need to pay $1 to OpenAi in order to get access to the GPT-4 model API. So after setting up your account with OpenAi, you will need to pay for at least $1 in credits so that your account is given the permission to use the GPT-4 model when running the app. See here: https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4

5) ElevenLabs is the service used for these AI voices. Ensure you create and save an AI voice on the ElevenLabs website.

## Using the Interview App

1) Link your ElevenLabs voice. Open up chatgpt_interview.py and replace the `ELEVENLABS_VOICE` variable with the name of your voice.

2) Write your own characters and create a .txt file within the `scenario_strings` folder. Include this in the `SCENARIO_FILE` variable within chatgpt_interview.py.

3) Run `chatgpt_interview.py` followed by the character from the `voice_settings` variable within that file (`abe`, `clown`, etc.).

4) Once it's running, press 4 to start the conversation, and Azure Speech-to-Text will listen to your microphone and transcribe it into text.

5) Once you're done talking, press P. Then the code will send all of the recorded text to the AI. Note that you should wait a second or two after you're done talking before pressing P so that Azure has enough time to process all of the audio.

6) Wait a few seconds for OpenAi to generate a response and for ElevenLabs to turn that response into audio. Once it's done playing the response, you can press 4 to start the loop again and continue the conversation.

## Using the Conversation App

1) Link each character's name and ElevenLabs voice. Near the bottom of chatgpt_conversation.py is where each character is established. Adjust the name (`Edgar`, `Arnold`, etc.) and match it with one of your ElevenLabs voices (`Cowboy`, `Benny`, etc.).

2) Write your own topic and characters in the converstaion_prompts.py file. The `SYSTEM_INTRO` is the topic the AIs will discuss, and it's refrenced slightly in the `SYSTEM_OUTRO`. Each AI also has their own personalities and quirks established in each of the `SPEAKER_#` variables that you can adjust.

3) Run `chatgpt_conversation`.

4) Once it's running, press 7 to talk to all the AI characters. Once you're done talking, press P. Then the code will send all of the recorded text to the AIs. Note that you should wait a second or two after you're done talking before pressing P so that Azure has enough time to process all of the audio.

5) Listen as the conversation goes, moving from one AI to another. Press 1, 2, or 3 to have a specific AI character speak. The program will prompt that character next after each of the previously generated responses finish.

6) Press 4 to pause all conversations. All of the AI responses that are created will finish speaking, then they will pause. Press 1, 2, 3, or 7 to resume the conversation with one of those speakers.

7) When you restart the program, the conversation will pick up where it left off using the `backup_history.txt` files. If you're wanting a totally new conversation, then delete the `backup_history.txt` files.