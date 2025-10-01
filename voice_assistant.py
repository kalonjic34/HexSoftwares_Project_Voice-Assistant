import threading
import queue
import time
import os
import sys
import webbrowser
import datetime as _dt
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import tkinter as tk
from tkinter import ttk, messagebox

import pyttsx3
import speech_recognition as sr

@dataclass
class IntentResult:
    intent: str
    text: str

class Speaker:
    def __init__(self,rate: int = 180,volume: float = 1.0, voice_name:Optional[str]=None):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate",rate)
        self.engine.setProperty("volume",volume)
        if voice_name:
            for v in self.engine.getProperty("voices"):
                if voice_name.lower() in v.name.lower():
                    self.engine.setProperty("voice",v.id)
                    break
        self._speak_lock = threading.Lock()
    def say_blocking(self,text:str):
        with self._speak_lock:
            self.engine.say(text)
            self.engine.runAndWait()

class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True
        
    def listen_once(self, timeout = 5, phrase_time_limit=6)-> Optional[str]:
        with sr.Microphone() as mic:
            audio = self.recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            return self.recognizer.recognize_sphinx(audio)
        except Exception:
            try:
                return self.recognizer.recognize_google(audio)
            except Exception:
                return None
class Assistant:
    def __init__(self):
        self.speaker = Speaker()
        self.listener = Listener()
        self.intents = Dict[str, Callable[[IntentResult], str]] = {}
        self.regsister_intents()
        
    def register(self,name:str):
        def _wrap(fn: Callable[[IntentResult], str]):
            self.intents[name] = fn
            return fn
        return _wrap
    
    def register_intents(self):
        @self.register("greet")
        def _(res: IntentResult) -> str:
            hour = _dt.datetime.now().hour
            part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
            return f"Good {part}! How can you help?"
        
        @self.register("time")
        def _(res:IntentResult) -> str:
            now = _dt.datetime.now().strftime("%A %I:%M %p")
            return f"it is {now}"
        
        @self.register("open_site")
        def _(res:IntentResult) -> str:
            text = res.text.lower()
            site = None
            if "youtube" in text:
                site = "https://youtube.com"
            elif "github" in text:
                site = "https://github.com"
            elif "google" in text:
                site = "https://google.com"
            if site:
                webbrowser.open(site)
                return f"Opening {site}."
            return "Which website should I open?" 
            
        @self.register("calc")
        def _(res:IntentResult) -> str:
            text = res.text.lower()
            text = text.replace("calculate","")
            text = text.replace("what is","")
            text = text.replace("what's","")
            text = text.replace(" x "," * ")
            allowed = set("0123456789+-*/().% ")
            if not set(text) <= allowed or not any(ch.isdigit() for ch in text):
                return "I can only handle simple arithmetic."
            try:
                result = eval(text, {"__builtins__":{}}, {})
                return f"The result is {result}."
            except Exception:
          
                return "Sorry, That math expression failed."
        @self.register("quit")
        def _(res: IntentResult) -> str:
            return "Goodbye!"

        @self.register("fallback")
        def _(res: IntentResult) -> str:
            return "I didn't get that. Try: time, open YouTube, or calculate 12 times 7."

    def detect_intent(self, text: str) -> IntentResult:
        t = text.lower().strip()
        if any(w in t for w in ["hello", "hey", "hi"]):
            return IntentResult("greet", text)
        if "time" in t or "clock" in t:
            return IntentResult("time", text)
        if "open" in t or "go to" in t:
            return IntentResult("open_site", text)
        if any(k in t for k in ["calculate", "+", "-", "*", " x ", "/", "what is", "what's"]):
            t = t.replace(" x ", " * ")
            return IntentResult("calc", t)
        if any(k in t for k in ["quit", "exit", "goodbye"]):
            return IntentResult("quit", text)
        return IntentResult("fallback", text)
            