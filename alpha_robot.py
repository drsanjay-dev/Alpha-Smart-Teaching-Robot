import tkinter as tk
from tkinter import scrolledtext
import openai
import serial
import time
import RPi.GPIO as GPIO
import os
import speech_recognition as sr
import pyttsx3
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain_core.prompts import PromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

# Set up OpenAI API key
openai.api_key = "Secret-Key"          #Add your Secret-Key Here

# Initialize LangChain prompt template
prompt_template = """
You are Alpha, an anime boy who is a teacher, someone who's friendly. Please chat with me using this personality. 
All responses you give must be in first person.
Don't be overly mean, remember, you are not mean, just misunderstood. 
Do not ever break character. Do not admit you are a teacher. 
Do not include any emojis or actions within the text that cannot be spoken. Do not explicitly say your name in your response.

Current conversation:
{history}

Human: 
{input}
AI:
"""

prompt_temp = PromptTemplate(template=prompt_template, input_variables=["history", "input"])
llm = ChatOpenAI(
    temperature=0.8,
    model="gpt-3.5-turbo",
    model_kwargs={"frequency_penalty": 1.3, "presence_penalty": 0.2},
    openai_api_key="Secret-Key"  #Add your Secret-Key Here

)
conversation = ConversationChain(
    llm=llm,
    prompt=prompt_temp,
    memory=ConversationBufferWindowMemory(k=5)
)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
RELAY_FORWARD, RELAY_REVERSE, RELAY_LEFT, RELAY_RIGHT = 2, 3, 4, 17
for pin in [RELAY_FORWARD, RELAY_REVERSE, RELAY_LEFT, RELAY_RIGHT]:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

def motor_control(direction):
    GPIO.output(RELAY_FORWARD, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    GPIO.output(RELAY_REVERSE, GPIO.HIGH if direction == "reverse" else GPIO.LOW)
    GPIO.output(RELAY_LEFT, GPIO.HIGH if direction == "left" else GPIO.LOW)
    GPIO.output(RELAY_RIGHT, GPIO.HIGH if direction == "right" else GPIO.LOW)

# Speech recognition and TTS
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "I didn't catch that."
        except sr.RequestError:
            return "Error with the speech recognition service."
        except Exception as e:
            return str(e)

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# GUI setup
def handle_serial_input():
    response = read_data()
    if response:
        chat_display.insert(tk.END, f"You: {response}\n")
        if response.lower() in ["forward", "reverse", "left", "right", "stop"]:
            motor_control(response.lower())
            chat_display.insert(tk.END, f"Motor moving {response.lower()}.\n")
        else:
            bot_response = get_openai_response(response)
            chat_display.insert(tk.END, f"Alpha: {bot_response}\n")
            speak_text(bot_response)
        chat_display.yview(tk.END)
    window.after(1000, handle_serial_input)

def read_data():
    if ser.in_waiting > 0:
        return ser.readline().decode('utf-8').strip()
    return None

def get_openai_response(prompt):
    try:
        response = conversation.invoke({"input": prompt})
        return response["response"].strip()
    except Exception as e:
        return f"Error: {e}"

# Set up the Tkinter window
window = tk.Tk()
window.title("Alpha - Smart Teaching Robot")
window.geometry("500x600")
chat_display = scrolledtext.ScrolledText(window, wrap=tk.WORD, state='normal', font=("Arial", 12))
chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Serial setup
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)

# Start serial handler loop
handle_serial_input()

# GUI main loop
try:
    window.mainloop()
except KeyboardInterrupt:
    GPIO.cleanup()
