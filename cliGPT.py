import argparse
import configparser
import imghdr
import openai
import os
import requests
import time
from PIL import Image


MODEL = "gpt-3.5-turbo"
OUTPUT_DIR = "./DALLE_OUTPUT"
DEFAULT_IMAGE_URL = "https://static.wikia.nocookie.net/gmod/images/9/99/The_Missing_textures.png"
IMAGE_SIZES = {
    "small": "256x256",
    "medium": "512x512",
    "large": "1024x1024"
}
EXIT_STR = "EXIT"

LOGO = """
       _ _  ____ ____ _____ 
   ___| (_)/ ___|  _ \_   _|
  / __| | | |  _| |_) || |  
 | (__| | | |_| |  __/ | |  
  \___|_|_|\____|_|    |_|  
                            
"""
LOGO_DALLE = """
  ____    _    _     _          _____ 
 |  _ \  / \  | |   | |        | ____|
 | | | |/ _ \ | |   | |   _____|  _|  
 | |_| / ___ \| |___| |__|_____| |___ 
 |____/_/   \_\_____|_____|    |_____|
                                      
"""
LOGO_CHATGPT = """
   ____ _           _    ____ ____ _____ 
  / ___| |__   __ _| |_ / ___|  _ \_   _|
 | |   | '_ \ / _` | __| |  _| |_) || |  
 | |___| | | | (_| | |_| |_| |  __/ | |  
  \____|_| |_|\__,_|\__|\____|_|    |_|  
                                         
"""

INIT_PROMPT = "Respond to all questions efficiently and as accurately as possible"

tokens_input = 0
tokens_output = 0

def dl_img(url):
    # DL image from url
    filepath = ""
    try:
        rsp = requests.get(url)
        if rsp.status_code == 200:
            # Get file extension
            ext = imghdr.what(file=None, h=rsp.content)
            # Write to file, name created from current time
            filename = int(time.time())
            filepath = os.path.join(OUTPUT_DIR, f"{filename}.{ext}")
            with open(filepath, "wb") as f:
                f.write(rsp.content)
    except Exception as e:
        print(f"ERROR \nDL IMG: {url}\nFILE: {filepath}\n")

    return filepath

def print_tokens():
    print(f"Tokens In: {tokens_input}, Tokens Out: {tokens_output}\n")

def gen_img(prompt, size=IMAGE_SIZES["medium"], num=1):
    # API has limit of 10 image per request (Update to work with > 1)
    if num != 1:
        num = 1

    # Create image from prompt and return url
    try:
        response = openai.Image.create(
            prompt=prompt, n=num, size=size
        )
        img_url = response.data[0].url
    except Exception as e:
  	# Gen failed, return default (error) image
        img_url = DEFAULT_IMAGE_URL

    return img_url

def run_dalle(size):
    # Create image dl folder
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(LOGO_DALLE)
    print("Describe anything.")
    while True:
        prompt = input("> ")
        if prompt == EXIT_STR:
            break
        rsp = gen_img(prompt, IMAGE_SIZES[size])
        print(f"\n{rsp}\n")

        # Open image with PIL (Pillow)
        filepath = dl_img(rsp)
        if os.path.exists(filepath):
            im = Image.open(filepath)
            im.show()

def gen_chat_rsp(message, message_history, role="user", model=MODEL):
    global tokens_input, tokens_output

    # Generate response to message + history
    message_history.append({"role": role, "content": f"{message}"})
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=message_history
        )
        reply = completion.choices[0].message.content

        # Keep track of usage ($$$)
        tokens_input = completion.usage.prompt_tokens
        tokens_output = completion.usage.completion_tokens
    except Exception as e:
        # Response failed, give default (error) response
        reply = "An Error occurred. Please try again."

    # Update message history
    message_history.append({"role": "assistant", "content": f"{reply}"})

    return reply

def run_chat_gpt(model):
    message_history = [
        {"role": "user", "content": INIT_PROMPT},
        {"role": "assistant", "content": "OK"}
    ]

    print(LOGO_CHATGPT)
    print("Ask anything.")
    while True:
        prompt = input("> ")
        if prompt == EXIT_STR:
            break
        rsp = gen_chat_rsp(prompt, message_history, model=model)
        print(f"\n :: {rsp}")
        print_tokens()

def main():
    # Load dev key, init openai
    config = configparser.ConfigParser()
    config.read('config.ini')
    openai.api_key = config["DEFAULT"]["API_KEY"]

    # Set up and read command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--model", default=MODEL)
    parser.add_argument("-s", "--size", default="medium")
    args = parser.parse_args()
    print(f"M: {args.model}, S: {args.size}")

    print(LOGO)
    while True:
        print("1) ChatGPT")
        print("2) DALL-E\n")
        print("What would you like to do?")
        print(f"Type \"{EXIT_STR}\" to quit or go back within an app.")
        selection = input("> ")

        if selection == "1":
            run_chat_gpt(args.model)
            print(LOGO)
        elif selection == "2":
            run_dalle(args.size)
            print(LOGO)
        elif selection == EXIT_STR:
            break
        else:
            print(f"\nUnrecognized option \"{selection}\".")
            print("Please select from the following.\n")

if __name__ == "__main__":
    main()
