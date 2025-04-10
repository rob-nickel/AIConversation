# This code runs a thread that manages the frontend code, a thread that listens for keyboard presses from the human, and then threads for the 3 speakers
# Once running, the human can activate a single speaker and then let the speakers continue an ongoing conversation.
# Each thread has the following core logic:

# Main Thread
    # Runs the web app

# Speaker X
    # Waits to be activated
    # Once it is activated (by user or by another speaker):
        # Acquire conversation lock
            # Get response from OpenAI
            # Add this new response to all other speakers' chat histories
        # Creates TTS with ElevenLabs
        # Acquire speaking lock (so only 1 speaks at a time)
            # Pick another thread randomly, activate them
                # Because this happens within the speaking lock, we are guaranteed that the other speakers are inactive when this called.
                # But, we start this now so that the next speaker can have their answer and audio ready to go the instant this speaker is done talking.
            # Play the TTS audio
            # Release speaking lock (Other threads can now talk)
    
# Human Input Thread
    # Listens for keypresses:

    # If 7 is pressed:
        # Toggles "pause" flag - stops other speakers from activating additional speakers

        # Record mic audio (until you press p)

        # Get convo lock (but not speaking lock)
            # In theory, wait until everyone is done speaking, and because the speakers are "paused" then no new ones will add to the convo
            # But to be safe, grab the convo lock to ensure that all speakers HAVE to wait until my response is added into the convo history
        
        # Transcribe mic audio into text with Azure
        # Add user's response into all speakers' chat history
        
        # Release the convo lock
        # (then optionally press a key to trigger a specific bot)
    
    # If 1 pressed:
        # Turns off "pause" flag
        # Activates Speaker 1
    
    # If 2 pressed: 
        # Turns off "pause" flag
        # Activates Speaker 2
    
    # If 3 pressed: 
        # Turns off "pause" flag
        # Activates Speaker 3

    # If 4 pressed:
        # Toggles "pause" flag - stops all other speakers from activating additional speakers

    # If 5 pressed:
        # Stops generating new speakers, finishes playing all generated audio, ends program

import threading
import time
import keyboard
import random
import logging
import mutagen
import os
from rich import print

from audio_player import AudioManager
from eleven_labs import ElevenLabsManager
from openai_chat import OpenAiManager
from azure_speech_to_text import SpeechToTextManager
from conversation_prompts.automation import SPEAKER_1
from conversation_prompts.automation import SPEAKER_2
from conversation_prompts.automation import SPEAKER_3

elevenlabs_manager = ElevenLabsManager()
audio_manager = AudioManager()
speech_manager = SpeechToTextManager()

speaking_lock = threading.Lock()
conversation_lock = threading.Lock()

speakers_paused = False
continue_program = True

# Class that represents a single ChatGPT Speaker and its information
class Speaker():
    
    def __init__(self, speaker_name, speaker_id, all_speakers, system_prompt, elevenlabs_voice):
        # Flag of whether this speaker should begin speaking
        self.activated = False 
        # Used to identify each speaker in the conversation history
        self.name = speaker_name 
        # an int used to ID this speaker to the frontend code
        self.speaker_id = speaker_id 
        # A list of the other speakers, so that you can pick one to randomly "activate" when you finish talking
        self.all_speakers = all_speakers
        # The name of the Elevenlabs voice that you want this speaker to speak with
        self.voice = elevenlabs_voice
        # The name of the txt backup file where this speaker's conversation history will be stored
        backup_file_name = f"backup_history_{speaker_name}.txt"
        # Initialize the OpenAi manager with a system prompt and a file that you would like to save your conversation too
        # If the backup file isn't empty, then it will restore that backed up conversation for this speaker
        self.openai_manager = OpenAiManager(system_prompt, backup_file_name) 
        # Optional - tells the OpenAi manager not to print as much
        self.openai_manager.logging = False

    def run(self):
        while continue_program:
            # Wait until we've been activated
            if not self.activated:
                time.sleep(0.1)
                if not continue_program:
                    break
                continue

            self.activated = False
            if self.speaker_id == 1:
                print(f"[italic purple] {self.name} has STARTED speaking.")
            elif self.speaker_id == 2:
                print(f"[italic yellow] {self.name} has STARTED speaking.")
            elif self.speaker_id == 3:
                print(f"[italic blue] {self.name} has STARTED speaking.")
            else:
                print(f"[italic white] {self.name} has STARTED speaking.")

            # This lock isn't necessary in theory, but for safety we will require this lock whenever updating any speaker's convo history
            with conversation_lock:
                # Generate a response to the conversation
                openai_answer = self.openai_manager.chat_with_history("Okay what is your response? Try to be as specific and detail-oriented as possible. Again, 3 sentences maximum.")
                openai_answer = openai_answer.replace("*", "")
                if self.speaker_id == 1:
                    print(f"[purple] {openai_answer}")
                elif self.speaker_id == 2:
                    print(f"[yellow] {openai_answer}")
                elif self.speaker_id == 3:
                    print(f"[blue] {openai_answer}")
                else:
                    print(f"[white] {openai_answer}")

                # Add your new response into everyone else's chat history, then have them save their chat history
                # This speaker's responses are marked as "assistant" role to itself, so everyone elses messages are "user" role.
                for speaker in self.all_speakers:
                    if speaker is not self:
                        speaker.openai_manager.chat_history.append({"role": "user", "content": f"[{self.name}] {openai_answer}"})
                        speaker.openai_manager.save_chat_to_backup()

                # Create audio response
                tts_file = elevenlabs_manager.text_to_audio(openai_answer, self.voice, False)
                audio_file_for_duration = mutagen.File(tts_file)
                audio_duration = audio_file_for_duration.info.length

            # Wait here until the current speaker is finished
            with speaking_lock:

                # If we're "paused", then simply finish speaking without activating another speaker
                # Otherwise, pick another speaker randomly, then activate it
                if not speakers_paused:
                    other_speakers = [speaker for speaker in self.all_speakers if speaker is not self]
                    random_speaker = random.choice(other_speakers)
                    random_speaker.activated = True
            
                # Play the TTS audio (without pausing)
                audio_manager.play_audio(tts_file, False, True, True)
            
                time.sleep(audio_duration + .25) # Wait one quarter second before the next person talks, otherwise their audio gets cut off
                if os.path.exists(tts_file):
                    os.remove(tts_file)
            if self.speaker_id == 1:
                print(f"[italic purple] {self.name} has FINISHED speaking.")
            elif self.speaker_id == 2:
                print(f"[italic yellow] {self.name} has FINISHED speaking.")
            elif self.speaker_id == 3:
                print(f"[italic blue] {self.name} has FINISHED speaking.")
            else:
                print(f"[italic white] {self.name} has FINISHED speaking.")  
        print(f"[italic white] {self.name} has ended thread.")  

# Class that handles human input, this thread is how you can manually activate or pause the other speakers
class Human():
    
    def __init__(self, name, all_speakers):
        self.name = name # This will be added to the beginning of the response
        self.all_speakers = all_speakers

    def run(self):
        global speakers_paused
        global continue_program
        while continue_program:

            # Speak into mic and add the dialogue to the chat history
            if keyboard.is_pressed('7'):

                # Toggles "pause" flag - stops other speakers from activating additional speakers
                speakers_paused = True
                print(f"[italic red] Speakers have been paused")

                with conversation_lock:
                    # Record mic audio from user (until presses '=')
                    print(f"[italic green] User has STARTED speaking. Press 'p' to finish your message:")
                    mic_result = speech_manager.speechtotext_from_mic_continuous()

                    if mic_result == '':
                        print("[italic red]Did not receive any input from the microphone!")
                        continue
                    print(f"[teal]Got the following audio from User:\n{mic_result}")

                    # Add User's response into all speakers chat history
                    for speaker in self.all_speakers:
                        speaker.openai_manager.chat_history.append({"role": "user", "content": f"[{self.name}] {mic_result}"})
                        speaker.openai_manager.save_chat_to_backup() # Tell the other speakers to save their chat history to their backup file
                
                print(f"[italic magenta] User has FINISHED speaking.")

                # Activate another speaker randomly
                speakers_paused = False
                random_speaker = random.randint(0, len(self.all_speakers)-1)
                print(f"[cyan]Activating Speaker {random_speaker+1}")
                self.all_speakers[random_speaker].activated = True

            
            # "Pause" the other speakers.
            # Whoever is currently speaking will finish, but no future speakers will be activated
            if keyboard.is_pressed('4'):
                print("[italic red] Speakers have been paused")
                speakers_paused = True
                time.sleep(1) # Wait for a bit to ensure you don't press this twice in a row
            
            # Activate Speaker 1
            if keyboard.is_pressed('1'):
                print("[cyan]Activating Speaker 1")
                speakers_paused = False
                self.all_speakers[0].activated = True
                time.sleep(1) # Wait for a bit to ensure you don't press this twice in a row
            
            # Activate Speaker 2
            if keyboard.is_pressed('2'):
                print("[cyan]Activating Speaker 2")
                speakers_paused = False
                self.all_speakers[1].activated = True
                time.sleep(1) # Wait for a bit to ensure you don't press this twice in a row
            
            # Activate Speaker 3
            if keyboard.is_pressed('3'):
                print("[cyan]Activating Speaker 3")
                speakers_paused = False
                self.all_speakers[2].activated = True
                time.sleep(1) # Wait for a bit to ensure you don't press this twice in a row

            if keyboard.is_pressed('5'):
                print("[bold red]Ending program")
                speakers_paused = True
                continue_program = False
                with conversation_lock:
                    print("Conversation lock obtained.")
                    time.sleep(45)
                    with speaking_lock:
                        print("Speaking lock obtained. Ending soon.")
            
            time.sleep(0.05)
        print(f"[italic white] User has ended thread.")  


def start_bot(bot):
    bot.run()

if __name__ == '__main__':

    all_speakers = []

    # Speaker 1
    speaker1 = Speaker("EDGAR", 1, all_speakers, SPEAKER_1, "Cowboy")
    speaker1_thread = threading.Thread(target=start_bot, args=(speaker1,))
    speaker1_thread.start()

    # Speaker 2
    speaker2 = Speaker("ARNOLD", 2, all_speakers, SPEAKER_2, "Benny")
    speaker2_thread = threading.Thread(target=start_bot, args=(speaker2,))
    speaker2_thread.start()

    # Speaker 3
    speaker3 = Speaker("WALLACE", 3, all_speakers, SPEAKER_3, "George")
    speaker3_thread = threading.Thread(target=start_bot, args=(speaker3,))
    speaker3_thread.start()

    all_speakers.append(speaker1)
    all_speakers.append(speaker2)
    all_speakers.append(speaker3)

    # Human thread
    human = Human("ROB", all_speakers)
    human_thread = threading.Thread(target=start_bot, args=(human,))
    human_thread.start()

    print("[italic green]!!SPEAKERS ARE READY TO GO!!\nPress 1, 2, or 3 to activate an speaker.\tPress 7 to speak to the speakers.\tPress 4 to pause.\tPress 5 to quit.")

    speaker1_thread.join()
    speaker2_thread.join()
    speaker3_thread.join()
    human_thread.join()

    print(f"[green] All threads ended.")  