# Voice Assistant (Project 1)

A lightweight desktop Voice Assistant built with Python and Tkinter. It listens on demand, understands simple intents, and speaks back using offline TTS. Ideal as a starter project for GUI + threading + speech integration.

## Features

- Push-to-talk listening with speech_recognition (Google Speech API)
- Offline text-to-speech with pyttsx3
- Intent handling:
  - Greetings
  - Current time
  - Open sites: YouTube, GitHub, Google
  - Quick arithmetic (safe, simple expressions)
- Tkinter GUI with states: Listening, Thinking, Speaking
- Live transcript with colored roles (You, Assistant, System)
- Threaded design + UI queue for non-blocking updates

## Tech Stack

- Python 3.10+
- Tkinter, ttk
- speech_recognition
- pyttsx3
- threading, queue, dataclasses

## Getting Started

1) Clone the repo
- git clone https://github.com/kalonjic34/HexSoftwares_Project_Voice-Assistant
- cd HexSoftwares_Project_Voice-Assistant

2) Create and activate a virtual environment (recommended)
- python -m venv .venv
- On Windows: .venv\Scripts\activate
- On macOS/Linux: source .venv/bin/activate

3) Install dependencies
- pip install -r requirements.txt
If you don’t have a requirements file yet, install directly:
- pip install pyttsx3 SpeechRecognition

Optional (Windows/macOS/Linux audio backends):
- pip install pyaudio
If PyAudio is hard to install, try:
- pip install pipwin
- pipwin install pyaudio

4) Run
- python voice_assistant.py

## Usage

- Push to Talk: click to capture one utterance.
- Text box + Send: type a command instead of speaking.
- Stop Speaking: shows a notice if speaking/listening is in progress.

Examples you can say or type:
- “hello” or “hey”
- “what time is it”
- “open YouTube” / “open GitHub” / “open Google”
- “calculate 12 x 7” or “what is (20+5)/5”

## How It Works

- Listener (speech_recognition)
  - Adjusts to ambient noise
  - Uses Google STT for a single utterance
- Assistant
  - detect_intent maps text to intents: greet, time, open_site, calc, quit, fallback
  - Each intent returns a response string (and may perform an action like opening a browser)
- Speaker (pyttsx3)
  - say_blocking handles synthesized speech with a thread-safe lock
- GUI (Tkinter)
  - Background worker threads handle listening and reply generation
  - A Queue transfers UI updates back to the main thread to keep the app responsive

## Configuration Notes

- Microphone selection
  - The code tries to find “Microphone (Realtek High Definition Audio)”. If not found, it falls back to the default microphone.
- Voice settings
  - Speaker(rate=180, volume=1.0, voice_name=None). You can pass a partial voice name (e.g., “Zira”, “David”) to select a voice available on your system.

## Security & Safety

- Calculation intent restricts input to digits and basic operators: 0–9, +, -, *, /, %, parentheses, and spaces.
- eval is run with disabled builtins and validated input to reduce risk. It’s still intended for simple math only.

## Known Limitations

- Requires internet for Google STT (speech_recognition). TTS (pyttsx3) is offline.
- Mic device name may need adjusting on non‑Realtek systems.
- Arithmetic is simple and intentionally limited.

## Roadmap

- Add more intents (weather, reminders, notes)
- Hotword/always‑listening mode with VAD toggle
- Configurable site shortcuts
- Theme toggle and improved styling
- Packaging (PyInstaller) for one‑click install

## Troubleshooting

- No microphone found
  - Remove or change the device name filter in Listener.listen_once.
- PyAudio install issues (Windows)
  - Use pipwin as noted above or install a prebuilt wheel.
- No voice output
  - Verify system TTS voices and audio device; try different voice_name.

## Contributing

Issues and PRs are welcome. Please open an issue describing the bug/feature first.

## License

MIT License (add a LICENSE file if not present)

## Acknowledgments

- speech_recognition by Uberi
- pyttsx3 TTS
- Tkinter/ttk for the GUI
