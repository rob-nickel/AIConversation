from openai import OpenAI
import tiktoken
import os
from rich import print

def num_tokens_from_messages(messages, model='gpt-3.5-turbo'):
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
    
    def __init__(self):
        self.chat_history = [] # Stores the entire conversation
        try:
            self.client = OpenAI(api_key='')#api_key=os.environ['OPENAI_API_KEY']) #TODO: fill in key
        except TypeError:
            exit("Set your OPENAI_API_KEY")

    # Asks a question with no chat history
    def chat(self, prompt="", use_history=False):
        if not prompt:
            print("Didn't receive input!")
            return

        # Create chat question
        chat_question = [{"role": "user", "content": prompt}]
        if use_history:
            chat_question = self.chat_history + chat_question

        # Check total token limit. Remove old messages as needed
        print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(chat_question)}")
        while num_tokens_from_messages(chat_question) > 2500:
            if use_history:
                self.chat_history.pop(1) # We skip the 1st message since it's the system message
                chat_question = self.chat_history + [{"role": "user", "content": prompt}]
            else:
                print("The length of this chat question is too large for the GPT model")
                return
            print(f"Popped a message! New token length is: {num_tokens_from_messages(chat_question)}")

        # Check that the prompt is under the token context limit
        chat_question = [{"role": "user", "content": prompt}]
        if num_tokens_from_messages(chat_question) > 8000:
            print("The length of this chat question is too large for the GPT model")
            return

        print("[orange1]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
          model="gpt-4",
          messages=chat_question
        )

       # Add this answer to our chat history
        if use_history:
            self.chat_history.append({"role": "user", "content": prompt})
            self.chat_history.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

        # Process the answer
        openai_answer = completion.choices[0].message.content
        print(f"[green]\n{openai_answer}\n")
        return openai_answer

    # Asks a question that includes the full conversation history
    def chat_with_history(self, prompt=""):
        if not prompt:
            print(f"[red]Didn't receive input!")
            return

        # Add our prompt into the chat history
        self.chat_history.append({"role": "user", "content": prompt})

        # Check total token limit. Remove old messages as needed
        print(f"[coral]Chat History has a current token length of {num_tokens_from_messages(self.chat_history)}")
        while num_tokens_from_messages(self.chat_history) > 8000:
            self.chat_history.pop(1) # We skip the 1st message since it's the system message
            print(f"Popped a message! New token length is: {num_tokens_from_messages(self.chat_history)}")

        print("[orange1]\nAsking ChatGPT a question...")
        completion = self.client.chat.completions.create(
          model="gpt-4",
          messages=self.chat_history
        )

        # Add this answer to our chat history
        self.chat_history.append({"role": completion.choices[0].message.role, "content": completion.choices[0].message.content})

        # Process the answer
        openai_answer = completion.choices[0].message.content
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
        openai_manager.chat_with_history(new_prompt)
        