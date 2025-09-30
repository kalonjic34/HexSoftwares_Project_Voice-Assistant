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