from openai import OpenAI
import tiktoken
import os
from rich import print
import base64
import time
import json

def num_tokens_from_messages(messages, model='gpt-4-turbo'):
  """Returns the number of tokens used by a list of messages.
  Copied with minor changes from: https://platform.openai.com/docs/guides/chat/managing-tokens """
  try:
      encoding = tiktoken.encoding_for_model(model)
      num_tokens = 0
      for message in messages:
          num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
          for key, value in message.items():
              num_tokens += len(encoding.encode(value))
              if key == "name":  # if there's a name, the role is omitted
                  num_tokens += -1  # role is always required and always 1 token
      num_tokens += 2  # every reply is primed with <im_start>assistant
      return num_tokens
  except Exception:
      raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
      #See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
      

class OpenAiManager:
    
    def __init__(self, system_prompt=None, chat_history_backup=None):
        try:
            self.client = OpenAI(api_key='')#api_key=os.environ['OPENAI_API_KEY']) #TODO: fill in key
        except TypeError:
            exit("Set your OPENAI_API_KEY")

        self.logging = True # Determines whether the module should print out its results
        self.tiktoken_encoder = None # Used to calculate the token count in messages
        self.chat_history = []

        # If a backup file is provided, we will save our chat history to that file after every call
        self.chat_history_backup = chat_history_backup
        
        # If the backup file already exists, we load its contents into the chat_history
        if chat_history_backup and os.path.exists(chat_history_backup):
            with open(chat_history_backup, 'r') as file:
                self.chat_history = json.load(file)
        elif system_prompt:
            # If the chat history file doesn't exist, then our chat history is currently empty.
            # If we were provided a system_prompt, add it into the chat history as the first message.
            self.chat_history.append(system_prompt)

    # Write our current chat history to the txt file
    def save_chat_to_backup(self):
        if self.chat_history_backup:
            with open(self.chat_history_backup, 'w') as file:
                json.dump(self.chat_history, file)

    def num_tokens_from_messages(self, messages, model='gpt-4-turbo'):
        """Returns the number of tokens used by a list of messages.
        The code below is an adaptation of this text-only version: https://platform.openai.com/docs/guides/chat/managing-tokens 
        The guide for image token calculation is here: https://platform.openai.com/docs/guides/vision
        Short version is that a 1920x1080 image is going to be 1105 tokens, so just using that for all images for now.

        There are three message formats we have to check:
        Version 1: the 'content' is just a text string
            'content' = 'What are considered some of the most popular characters in videogames?'
        Version 2: the content is an array with a single dictionary, with two key/value pairs
            'content' = [{'type': 'text', 'text': 'What are considered some of the most popular characters in videogames?'}]
        Version 3: the content is an array with two dictionaries, one for the text portion and one for the image portion
            'content' = [{'type': 'text', 'text': 'Okay now please compare the previous image I sent you with this new image!'}, {'type': 'image_url', 'image_url': {'url': 'https://i.gyazo.com/8ec349446dbb538727e515f2b964224c.png', 'detail': 'high'}}]
        """
        try:
            if self.tiktoken_encoder == None:
                self.tiktoken_encoder = tiktoken.encoding_for_model(model) # We store this value so we don't have to check again every time
            num_tokens = 0
            for message in messages:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                for key, value in message.items():
                    if key == 'role':
                        num_tokens += len(self.tiktoken_encoder.encode(value))
                    elif key == 'content':
                        # In the case that value is just a string, simply get its token value and move on
                        if isinstance(value, str):
                            num_tokens += len(self.tiktoken_encoder.encode(value))
                            continue

                        # In this case the 'content' variables value is an array of dictionaries
                        for message_data in value:
                            for content_key, content_value in message_data.items():
                                if content_key == 'type':
                                    num_tokens += len(self.tiktoken_encoder.encode(content_value))
                                elif content_key == 'text': 
                                    num_tokens += len(self.tiktoken_encoder.encode(content_value))
                                elif content_key == "image_url":
                                    num_tokens += 1105 # Assumes the image is 1920x1080 and that detail is set to high               
            num_tokens += 2  # every reply is primed with <im_start>assistant
            return num_tokens
        except Exception:
            # Either this model is not implemented in tiktoken, or there was some error processing the messages
            raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.""")

    # Asks a question with no chat history
    def chat(self, prompt="", use_history=False, single_character=True):
        if not prompt:
            print("Didn't receive input!")
            return

        # Create chat question
        chat_question = [{"role": "user", "content": prompt}]
        if use_history:
            chat_question = self.chat_history + chat_question

        # Check total token limit. Remove old messages as needed
        print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(chat_question)}")
        if single_character:
            while num_tokens_from_messages(chat_question) > 2500: # Make larger for longer conversation history.
                if use_history:
                    self.chat_history.pop(1) # We skip the 1st message since it's the system message
                    chat_question = self.chat_history + [{"role": "user", "content": prompt}]
                else:
                    print("The length of this chat question is too large for the GPT model")
                    return
                print(f"Popped a message! New token length is: {num_tokens_from_messages(chat_question)}")

        elif self.num_tokens_from_messages(chat_question) > 13000: # Make larger for longer group conversations.
            print("The length of this conversation is getting too expensive. Ending now.")

        print("[orange1]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
          model="gpt-4-turbo",
          messages=chat_question
        )

       # Add this answer to our chat history
        if single_character and use_history:
            self.chat_history.append({"role": "user", "content": prompt})
            self.chat_history.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

        # Process the answer
        openai_answer = completion.choices[0].message.content
        if self.logging:
            print(f"[green]\n{openai_answer}\n")
        return openai_answer

    # Analyze an image without history
    # Works with jpg, jpeg, or png. Alternatively can provide an image URL by setting local_image to False
    # More info here: https://platform.openai.com/docs/guides/vision
    def analyze_image(self, prompt, image_path, local_image=True):
        # Use default prompt if one isn't provided
        if prompt is None:
            prompt = "Please give me a detailed description of this image."
        # If this is a local image, encode it into base64. Otherwise just use the provided URL.
        if local_image:
            try:
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                    url = f"data:image/jpeg;base64,{base64_image}"
            except:
                print("[red]ERROR: COULD NOT BASE64 ENCODE THE IMAGE!!")
                return None
        else:
            url = image_path # The provided image path is a URL
        if self.logging:
            print("[orange]\nAsking ChatGPT to analyze image...")
        completion = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                            "detail": "high"
                        }
                    },
                ],
                },
            ],
            max_tokens=4096, # max of 4096 tokens
        )
        openai_answer = completion.choices[0].message.content
        if self.logging:
            print(f"[green]\n{openai_answer}\n")
        return openai_answer

    # Asks a question that includes the full conversation history
    def chat_with_history(self, prompt="", image_path="", local_image=True, single_character=True):
        if single_character:
            if not prompt:
                print(f"[red]Didn't receive input!")
                return
            # Add our prompt into the chat history
            self.chat_history.append({"role": "user", "content": prompt})

        elif not single_character and prompt is not None and prompt != "":
            # Create a new chat message with the text prompt
            new_chat_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
            # If an image is provided, add the image url info into our new message.
            if image_path != "":
                # If this is a local image, we encode it into base64. Otherwise just use the provided URL.
                if local_image:
                    try:
                        with open(image_path, "rb") as image_file:
                            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                            url = f"data:image/jpeg;base64,{base64_image}"
                    except:
                        print("[red]ERROR: COULD NOT BASE64 ENCODE THE IMAGE. PANIC!!")
                        return None
                else:
                    url = image_path # The provided image path is a URL
                new_image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "high"
                    }
                }
                new_chat_message["content"].append(new_image_content)

            # Add the new message into our chat history
            self.chat_history.append(new_chat_message)


        # Check total token limit. Remove old messages as needed
        if single_character:
            print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(self.chat_history)}")
            while num_tokens_from_messages(self.chat_history) > 5000: # Make larger for longer conversations.
                self.chat_history.pop(1) # We skip the 1st message since it's the system message
                print(f"Popped a message! New token length is: {num_tokens_from_messages(self.chat_history)}")
        else:
            print(f"[coral]Chat History has a current token length of {self.num_tokens_from_messages(self.chat_history)}")
            while self.num_tokens_from_messages(self.chat_history) > 13000: # Make larger for longer conversations.
                self.chat_history.pop(1) # We skip the 1st message since it's the system message
                print(f"Popped a message! New token length is: {self.num_tokens_from_messages(self.chat_history)}")

        print("[orange1]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=self.chat_history
        )

        # Add this answer to our chat history
        self.chat_history.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

        # If a backup file was provided, write out convo history to the txt file
        self.save_chat_to_backup()

        # Process the answer
        openai_answer = completion.choices[0].message.content
        if self.logging:
            print(f"[green]\n{openai_answer}\n")
        return openai_answer
   

if __name__ == '__main__':
    openai_manager = OpenAiManager()

    # CHAT TEST
    chat = openai_manager.chat("Hey ChatGPT what is the pythagorean theorem? But tell it to me as Pythagoras from Ancient Greece")

    # CHAT WITH HISTORY TEST
    FIRST_SYSTEM_MESSAGE = {"role": "system", "content": "Act like you are Captain Jack Sparrow from the Pirates of Carribean movie series!"}
    FIRST_USER_MESSAGE = {"role": "user", "content": "Ahoy there! Who are you, and what are you doing in these parts? Please give me a 1 sentence background on how you got here. And do you have any mayonnaise I can borrow?"}
    openai_manager.chat_history.append(FIRST_SYSTEM_MESSAGE)
    openai_manager.chat_history.append(FIRST_USER_MESSAGE)

    while True:
        new_prompt = input("\nNext question? \n\n")
        openai_manager.chat_with_history(new_prompt, True)
        