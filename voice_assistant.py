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
class IntentResults:
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
            