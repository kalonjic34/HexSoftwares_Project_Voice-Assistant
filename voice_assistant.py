import threading
import queue
import time
import os
import sys
import webbrowser
import datetime as _dt
from dataclasses import dataclass
from typing import Callable, Dict, Optional
import random

import tkinter as tk
from tkinter import ttk, messagebox

import pyttsx3
import speech_recognition as sr

@dataclass
class IntentResult:
    intent: str
    text: str

class Speaker:
    def __init__(self, rate: int = 180, volume: float = 1.0, voice_name: Optional[str] = None):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)
        if voice_name:
            for v in self.engine.getProperty("voices"):
                if voice_name.lower() in v.name.lower():
                    self.engine.setProperty("voice", v.id)
                    break
        self._speak_lock = threading.Lock()

    def say_blocking(self, text: str):
        with self._speak_lock:
            self.engine.say(text)
            self.engine.runAndWait()

class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True

    def listen_once(self, timeout=5, phrase_time_limit=6) -> Optional[str]:
        with sr.Microphone() as mic:
            print("Adjusting to ambient noise...")
            self.recognizer.adjust_for_ambient_noise(mic, duration=1)
            print("Listening...")
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
        self.intents: Dict[str, Callable[[IntentResult], str]] = {}
        self.register_intents()

    def register(self, name: str):
        def _wrap(fn: Callable[[IntentResult], str]):
            self.intents[name] = fn
            return fn
        return _wrap

    def register_intents(self):
        @self.register("greet")
        def _(res: IntentResult) -> str:
            hour = _dt.datetime.now().hour
            part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
            return f"Good {part}! How can I help?"

        @self.register("time")
        def _(res:IntentResult) -> str:
            now = _dt.datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}. The current time is {now.strftime('%I:%M %p')}."

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
                return f"Opening YouTube for you." if "youtube" in site else f"Opening {site}."
            return "Which website should I open?"

        @self.register("calc")
        def _(res:IntentResult) -> str:
            text = res.text.lower()
            text = text.replace("calculate", "")
            text = text.replace("what is", "")
            text = text.replace("what's", "")
            text = text.replace(" x ", " * ")
            allowed = set("0123456789+-*/().% ")
            if not set(text) <= allowed or not any(ch.isdigit() for ch in text):
                return "I can only handle simple arithmetic."
            try:
                result = eval(text, {"__builtins__": {}}, {})
                return f"The result is {result}."
            except Exception:
                return "Sorry, that math expression failed."


        @self.register("weather")
        def _(res: IntentResult) -> str:
            return "The weather today is sunny with a light breeze."

        @self.register("fact")
        def _(res: IntentResult) -> str:
            facts = [
                "Did you know honey never spoils? Ancient tombs had edible honey!",
                "Octopuses have three hearts!",
                "Bananas are berries but strawberries aren't!",
                "A group of flamingos is called a 'flamboyance'.",
                "Sharks existed before trees!"
            ]
            return random.choice(facts)

        @self.register("quit")
        def _(res: IntentResult) -> str:
            return "Goodbye!"

        @self.register("fallback")
        def _(res: IntentResult) -> str:
            return "I didn't get that. Try asking about the date, weather, a fact, or open YouTube."

    def detect_intent(self, text: str) -> IntentResult:
        t = text.lower().strip()
        if any(w in t for w in ["hello", "hey", "hi"]):
            return IntentResult("greet", text)
        if any(k in t for k in ["time", "date", "day"]):
            return IntentResult("time", text)
        if any(k in t for k in ["open", "youtube", "google", "github"]):
            return IntentResult("open_site", text)
        if any(k in t for k in ["calculate", "+", "-", "*", "/", "what is", "what's"]):
            return IntentResult("calc", text)
        if any(k in t for k in ["weather", "forecast"]):
            return IntentResult("weather", text)
        if any(k in t for k in ["fact", "interesting"]):
            return IntentResult("fact", text)
        if any(k in t for k in ["quit", "exit", "goodbye"]):
            return IntentResult("quit", text)
        return IntentResult("fallback", text)

class VoiceAssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Voice Assistant")
        self.geometry("720x520")
        self.minsize(520, 420)

        try:
            self.style = ttk.Style(self)
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        self.assistant = Assistant()
        self.ui_queue: "queue.Queue[tuple[str,str]]" = queue.Queue()
        self._build_widgets()
        self.after(100, self._process_queue)
        self.listening = False
        self.speaking = False

    def _build_widgets(self):
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(12, 6))
        self.title_lbl = ttk.Label(top, text="Assistant", font=("Segoe UI", 16, "bold"))
        self.title_lbl.pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Idle")
        self.status_lbl = ttk.Label(top, textvariable=self.status_var, foreground="#555")
        self.status_lbl.pack(side=tk.RIGHT)
        mid = ttk.Frame(self)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=6)
        self.text = tk.Text(mid, wrap="word", state="disabled", height=16)
        self.text.configure(font=("Consolas", 11))
        self.scroll = ttk.Scrollbar(mid, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)
        bottom = ttk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)
        self.push_btn = ttk.Button(bottom, text="Push to Talk", command=self.on_push_to_talk)
        self.push_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(bottom, text="Stop Speaking", command=self.on_stop_speaking)
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.entry = ttk.Entry(bottom)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 8))
        self.entry.bind("<Return>", self.on_text_submit)
        self.send_btn = ttk.Button(bottom, text="Send", command=self.on_send_click)
        self.send_btn.pack(side=tk.LEFT)

    def set_status(self, text: str):
        self.status_var.set(text)
        color = {
            "Idle": "#555",
            "Listening": "#0a7",
            "Thinking": "#a70",
            "Speaking": "#a7a",
        }.get(text, "#555")
        self.status_lbl.configure(foreground=color)

    def append_transcript(self, who: str, msg: str):
        self.text.configure(state="normal")
        tag = "user" if who == "You" else "bot"
        if tag not in self.text.tag_names():
            self.text.tag_configure("user", foreground="#2b6cb0")
            self.text.tag_configure("bot", foreground="#2f855a")
            self.text.tag_configure("sys", foreground="#888888", font=("Consolas", 10, "italic"))
        self.text.insert("end", f"{who}: ", ("sys",))
        self.text.insert("end", f"{msg}\n", (tag,))
        self.text.see("end")
        self.text.configure(state="disabled")

    def on_push_to_talk(self):
        if self.listening:
            return
        self.listening = True
        self.set_status("Listening")
        self.append_transcript("System", "Listening...")
        self.push_btn.configure(state="disabled")
        threading.Thread(target=self._listen_and_respond, daemon=True).start()

    def on_text_submit(self, event=None):
        self.on_send_click()

    def on_send_click(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.set_status("Thinking")
        threading.Thread(target=self._handle_text_query, args=(text,), daemon=True).start()

    def on_stop_speaking(self):
        messagebox.showinfo("Speaking", "If I'm listening, please wait a moment. I'll finish shortly.")

    def _listen_and_respond(self):
        try:
            listener = self.assistant.listener
            try:
                text = listener.listen_once()
            except Exception:
                text = None

            self.ui_queue.put(("listen_done", text or ""))
            if not text:
                self.ui_queue.put(("append", ("System", "Sorry, I didn't catch that.")))
                self.ui_queue.put(("status", "Idle"))
                self.ui_queue.put(("unlock_btn", ""))
                return

            self.ui_queue.put(("append", ("You", text)))
            self.ui_queue.put(("status", "Thinking"))

            res = self.assistant.detect_intent(text)
            handler = self.assistant.intents.get(res.intent, self.assistant.intents["fallback"])
            reply = handler(res)

            if res.intent == "quit":
                self.ui_queue.put(("append", ("Assistant", reply)))
                self._speak_async(reply)
                time.sleep(0.1)
                self.ui_queue.put(("exit", ""))
                return

            self.ui_queue.put(("append", ("Assistant", reply)))
            self._speak_async(reply)
        finally:
            self.ui_queue.put(("status", "Idle"))
            self.ui_queue.put(("unlock_btn", ""))

    def _handle_text_query(self, text: str):
        res = self.assistant.detect_intent(text)
        handler = self.assistant.intents.get(res.intent, self.assistant.intents["fallback"])
        reply = handler(res)
        if res.intent == "quit":
            self.ui_queue.put(("append", ("Assistant", reply)))
            self._speak_async(reply)
            time.sleep(0.1)
            self.ui_queue.put(("exit", ""))
            return
        self.ui_queue.put(("append", ("You", text)))
        self.ui_queue.put(("append", ("Assistant", reply)))
        self._speak_async(reply)
        self.ui_queue.put(("status", "Idle"))

    def _speak_async(self, text: str):
        def run():
            self.ui_queue.put(("status", "Speaking"))
            try:
                self.assistant.speaker.say_blocking(text)
            finally:
                self.ui_queue.put(("status", "Idle"))
        threading.Thread(target=run, daemon=True).start()

    def _process_queue(self):
        try:
            while True:
                action, payload = self.ui_queue.get_nowait()
                if action == "append":
                    who, msg = payload
                    self.append_transcript(who, msg)
                elif action == "status":
                    self.set_status(payload)
                elif action == "listen_done":
                    pass
                elif action == "unlock_btn":
                    self.push_btn.configure(state="normal")
                    self.listening = False
                elif action == "exit":
                    self.after(150, self.destroy)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

def main():
    app = VoiceAssistantApp()
    app.mainloop()

if __name__ == "__main__":
    main()