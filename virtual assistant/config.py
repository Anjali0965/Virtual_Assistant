import os

# Chrome executable path (update if Chrome is installed elsewhere)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Common application paths (update as needed)
APP_PATHS = {
    'vscode': r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    'chrome': CHROME_PATH,
    'notepad': r"C:\Windows\system32\notepad.exe",
    'calculator': r"C:\Windows\System32\calc.exe",
    'explorer': r"explorer.exe",
    # WhatsApp desktop path placeholder (if user has it)
    'whatsapp': r"C:\Users\%USERNAME%\AppData\Local\WhatsApp\WhatsApp.exe",
    'spotify': r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
}

# Sounddevice default devices (input, output)
SOUNDDEVICE_DEVICE = (1, 3)

# Recording settings
# Main command recording duration (seconds) — increase for reliability
RECORD_DURATION = 6
SAMPLE_RATE = 16000

# Wake-word / short listen duration (seconds). Increase if wake detection was too short.
WAKE_LISTEN_DURATION = 5

# Audio energy thresholds (RMS) to detect silent or clipped/noisy recordings
# If RMS below MIN_RMS, treat command recordings as silence and ignore.
# Wake-word listening uses a lower threshold so quiet speech is still considered.
MIN_RMS = 0.001
WAKE_MIN_RMS = 0.0005
MAX_RMS = 0.95

# Wake-word / always-listening config
# Disable by default to avoid blocking startup in environments without a microphone
ENABLE_WAKE = False
WAKE_WORDS = ["jarvis", "assistant"]



# Allow user overrides via assistant_config.json in workspace root.
import json
import pathlib

_cfg_file = pathlib.Path(__file__).parent / 'assistant_config.json'
if _cfg_file.exists():
    try:
        with open(_cfg_file, 'r', encoding='utf-8') as fh:
            user_cfg = json.load(fh)
        # merge app paths
        if isinstance(user_cfg.get('APP_PATHS'), dict):
            APP_PATHS.update(user_cfg['APP_PATHS'])
        # override chrome path
        if user_cfg.get('CHROME_PATH'):
            CHROME_PATH = user_cfg['CHROME_PATH']
            APP_PATHS['chrome'] = CHROME_PATH
    except Exception:
        pass
