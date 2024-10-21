import time
import azure.cognitiveservices.speech as speechsdk
import keyboard
import os
from rich import print

class SpeechToTextManager:
    azure_speechconfig = None
    azure_audioconfig = None
    azure_speechrecognizer = None

    def __init__(self):
        # Creates an instance of a speech config with specified subscription key and service region.
        # Replace with your own subscription key and service region (e.g., "westus").
        try:
            self.azure_speechconfig = speechsdk.SpeechConfig(subscription='23fa7961ea1443ba9a703e2b5c697a8d', region='eastus')#subscription=os.getenv('AZURE_TTS_KEY'), region=os.getenv('AZURE_TTS_REGION')) #TODO fill in Azure Key and Region
        except TypeError:
            exit("Set your AZURE_TTS_KEY or AZURE_TTS_REGION")
        
        self.azure_speechconfig.speech_recognition_language="en-US"

    def speechtotext_from_mic_continuous(self, stop_key='p'):
        self.azure_speechrecognizer = speechsdk.SpeechRecognizer(speech_config=self.azure_speechconfig)

        done = False
        
        # Optional callback to print out whenever a chunk of speech is being recognized. This gets called basically every word.
        #def recognizing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        #    print('RECOGNIZING: {}'.format(evt))
        #self.azure_speechrecognizer.recognizing.connect(recognizing_cb)

        # Optional callback to print out whenever a chunk of speech is finished being recognized. Make sure to let this finish before ending the speech recognition.
        def recognized_cb(evt: speechsdk.SpeechRecognitionEventArgs):
            print(" ")
            #print('RECOGNIZED: {}'.format(evt))
        self.azure_speechrecognizer.recognized.connect(recognized_cb)

        # We register this to fire if we get a session_stopped or cancelled event.
        def stop_cb(evt: speechsdk.SessionEventArgs):
            #print('CLOSING speech recognition on {}'.format(evt))
            nonlocal done
            done = True

        # Connect callbacks to the events fired by the speech recognizer
        self.azure_speechrecognizer.session_stopped.connect(stop_cb)
        self.azure_speechrecognizer.canceled.connect(stop_cb)

        # This is where we compile the results we receive from the ongoing "Recognized" events
        all_results = []
        def handle_final_result(evt):
            all_results.append(evt.result.text)
        self.azure_speechrecognizer.recognized.connect(handle_final_result)

        # Perform recognition. `start_continuous_recognition_async asynchronously initiates continuous recognition operation,
        # Other tasks can be performed on this thread while recognition starts...
        # wait on result_future.get() to know when initialization is done.
        # Call stop_continuous_recognition_async() to stop recognition.
        result_future = self.azure_speechrecognizer.start_continuous_recognition_async()
        result_future.get()  # wait for voidfuture, so we know engine initialization is done.
        # print('Continuous Speech Recognition is now running, say something.')

        while not done:
            # METHOD 1 - Press the stop key. This is 'p' by default but user can provide different key
            if keyboard.read_key() == stop_key:
                print("\nEnding Azure speech recognition\n")
                self.azure_speechrecognizer.stop_continuous_recognition_async()
                break

            # Other methods: https://stackoverflow.com/a/57644349

            # No real sample parallel work to do on this thread, so just wait for user to give the signal to stop.
            # Can't exit function or speech_recognizer will go out of scope and be destroyed while running.

        final_result = " ".join(all_results).strip()
        print(f"\nHeres the result!\n")
        print(f"[blue]\n{final_result}\n\n")
        return final_result


# Tests
if __name__ == '__main__':
    
    speechtotext_manager = SpeechToTextManager()

    while True:
        result = speechtotext_manager.speechtotext_from_mic_continuous()
        print(f"\n\nRESULT:\n{result}")
        time.sleep(60)
