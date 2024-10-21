import time
import keyboard
import sys
from rich import print
from azure_speech_to_text import SpeechToTextManager
from openai_chat import OpenAiManager
from eleven_labs import ElevenLabsManager
from audio_player import AudioManager

def initialize_managers():
    return (ElevenLabsManager(), SpeechToTextManager(), OpenAiManager(), AudioManager())

def read_file_contents(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"[red]Error: The file '{filename}' was not found.")
        return None
    except Exception as e:
        print(f"[red]An error occurred: {e}")
        return None

def main():
    if len(sys.argv) != 2:
        print("[red]Usage: python script.py <voice>")
        return

    voice_arg = sys.argv[1]

    # Simulating a switch statement using a dictionary
    voice_settings = {
        "abe": {
            "ELEVENLABS_VOICE": "Abraham Lincoln",
            "SCENARIO_FILE": "scenario_strings/abraham_lincoln.txt"
        },
        "clown": {
            "ELEVENLABS_VOICE": "Cowboy",
            "SCENARIO_FILE": "scenario_strings/bill_the_clown.txt"
        },
        "default": {
            "ELEVENLABS_VOICE": "Patrick",
            "SCENARIO_FILE": "scenario_strings/bill_the_clown.txt"
        }
    }

    # Get the settings based on the command-line argument
    settings = voice_settings.get(voice_arg, voice_settings["default"])
    ELEVENLABS_VOICE = settings["ELEVENLABS_VOICE"]
    SCENARIO_FILE = settings["SCENARIO_FILE"]

    voice_summary = read_file_contents(SCENARIO_FILE)
    if voice_summary is None:
        print("[red]No voice summary")
        return
    
    #print(voice_summary)

    elevenlabs_manager, speechtotext_manager, openai_manager, audio_manager = initialize_managers()
    BACKUP_FILE = "ChatHistoryBackup.txt"

    FIRST_SYSTEM_MESSAGE = {
        "role": "system", 
        "content": voice_summary
    }
    openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)

    print("[orange1]Starting the loop, press '4' to begin")
    while True:
        if keyboard.read_key() != "4":
            time.sleep(0.1)
            continue

        print("[orange1]User pressed 4 key! Now listening to your microphone. Press 'p' to finish your message:")
        mic_result = speechtotext_manager.speechtotext_from_mic_continuous()

        if mic_result == '':
            print("[red]Did not receive any input from the microphone!")
            continue

        openai_result = openai_manager.chat_with_history(mic_result, "", "", True)
        print(f"[green]\n{openai_result}\n")

        with open(BACKUP_FILE, "w") as file:
            file.write(str(openai_manager.chat_history))

        elevenlabs_output = elevenlabs_manager.text_to_audio(openai_result, ELEVENLABS_VOICE, False)
        audio_manager.play_audio(elevenlabs_output, True, True, True) #sleep_during_playback=True, delete_file=False, play_using_music=True

        print("[orange1]\nPress '4' for next message\n")

if __name__ == "__main__":
    main()