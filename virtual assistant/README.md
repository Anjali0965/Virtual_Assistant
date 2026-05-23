# Virtual Assistant

Minimal virtual assistant script `assistant.py`.

Setup (from workspace root):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python assistant.py
```

Notes:

- If a microphone or PyAudio is not available, the script falls back to text input.
- If TTS (`pyttsx3`) is not available, speech output falls back to console prints.
- Wikipedia/network errors are handled gracefully.
