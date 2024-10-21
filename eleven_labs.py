from elevenlabs import play, stream, save, generate, set_api_key, voices
import time
import os

try:
  set_api_key('') #os.getenv('ELEVENLABS_API_KEY')) #TODO Fill in Eleven Labs Key
except TypeError:
  exit("Set your ELEVENLABS_API_KEY")

class ElevenLabsManager:

    def __init__(self):
        all_voices = voices()
        #print(f"\nAll ElevenLabs voices: \n{self.voices}\n")

    def generate_audio(self, input_text, voice, model="eleven_monolingual_v1"):
        return generate(
          text=input_text,
          voice=voice,
          model=model
        )

    # Convert text to speech, then save it to file. Returns the file path.
    # Current model options (that I would use) are eleven_monolingual_v1 or eleven_turbo_v2
    # eleven_turbo_v2 takes about 60% of the time that eleven_monolingual_v1 takes
    # However eleven_monolingual_v1 seems to produce more variety and emphasis, whereas turbo feels more monotone. Turbo still sounds good, just a little less interesting
    def text_to_audio(self, input_text, voice="Dave", save_as_wave=True, subdirectory="", model_id="eleven_monolingual_v1"):
        audio = self.generate_audio(input_text, voice)
        if save_as_wave:
          file_name = f"___Msg{str(hash(input_text))}.wav"
        else:
          file_name = f"___Msg{str(hash(input_text))}.mp3"
        tts_file = os.path.join(os.path.abspath(os.curdir), subdirectory, file_name)
        save(audio, tts_file)
        return tts_file

    # Convert text to speech, then play it out loud
    def text_to_audio_played(self, input_text, voice="Dave"):
        audio = self.generate_audio(input_text, voice)
        play(audio)

    # Convert text to speech, then stream it out loud
    def text_to_audio_streamed(self, input_text, voice="Dave"):
        audio_stream = self.generate_audio(input_text, voice, stream=True)
        stream(audio_stream)


if __name__ == '__main__':
    elevenlabs_manager = ElevenLabsManager()

    elevenlabs_manager.text_to_audio_streamed("Streamed test audio")
    time.sleep(2)
    elevenlabs_manager.text_to_audio_played("Played test audio")
    time.sleep(2)
    file_path = elevenlabs_manager.text_to_audio("Saved test audio")
    print("Finished with all tests")

    time.sleep(30)