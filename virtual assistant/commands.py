import re
from browser import open_url, open_google_search, open_youtube_search, open_gmail, open_github, open_linkedin, open_chatgpt
import automation


ACTION_MARKERS = (
    "open ",
    "start ",
    "launch ",
    "close ",
    "search ",
    "google ",
    "youtube ",
    "play ",
    "go to ",
    "type ",
    "press ",
    "shutdown",
    "restart",
    "sleep",
    "lock",
    "mute",
    "volume up",
    "volume down",
    "screenshot",
)


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _looks_like_multi_command(text: str) -> bool:
    return sum(1 for marker in ACTION_MARKERS if marker in text) >= 2


def _split_on_connector(text: str, connector: str):
    parts = [part.strip() for part in text.split(connector) if part.strip()]
    return parts if len(parts) > 1 else [text]


def _split_command_chain(text: str):
    normalized = normalize(text)
    if " and then " in normalized:
        return _split_on_connector(normalized, " and then ")
    if " after that " in normalized:
        return _split_on_connector(normalized, " after that ")
    if " next " in normalized:
        parts = _split_on_connector(normalized, " next ")
        if len(parts) > 1:
            return parts
    if " then " in normalized:
        parts = _split_on_connector(normalized, " then ")
        if len(parts) > 1:
            return parts
    if " and " in normalized and _looks_like_multi_command(normalized):
        return _split_on_connector(normalized, " and ")
    return [normalized]


def _handle_single_command(text: str, debug: bool = False) -> str:
    if not text:
        return ""

    t = normalize(text)

    # App control
    if any(x in t for x in ("open vscode", "open code", "start vscode", "start code", "launch vscode", "launch code")):
        automation.open_app('vscode')
        return "open_app:vscode"
    if "open chrome" in t or "start chrome" in t or "launch chrome" in t:
        automation.open_app('chrome')
        return "open_app:chrome"
    if "open notepad" in t or "start notepad" in t or "launch notepad" in t:
        automation.open_app('notepad')
        return "open_app:notepad"
    if "open calculator" in t or "open calc" in t or "launch calculator" in t or "launch calc" in t:
        automation.open_app('calculator')
        return "open_app:calculator"
    if "open whatsapp" in t or "start whatsapp" in t or "launch whatsapp" in t:
        automation.open_app('whatsapp')
        return "open_app:whatsapp"
    if "open spotify" in t or "start spotify" in t or "launch spotify" in t:
        automation.open_app('spotify')
        return "open_app:spotify"
    if "open explorer" in t or "open file" in t or "open folder" in t:
        m = re.search(r"open (?:folder|explorer|open) (.+)", text, re.I)
        if m:
            automation.open_folder(m.group(1))
            return f"open_folder:{m.group(1)}"
        automation.open_app('explorer')
        return "open_app:explorer"
    if "go to gmail" in t or "open gmail" in t or "launch gmail" in t:
        open_gmail()
        return "open:gmail"
    if "go to github" in t or "open github" in t or "launch github" in t:
        open_github()
        return "open:github"
    if "go to linkedin" in t or "open linkedin" in t or "launch linkedin" in t:
        open_linkedin()
        return "open:linkedin"
    if "go to chatgpt" in t or "open chatgpt" in t or "launch chatgpt" in t:
        open_chatgpt()
        return "open:chatgpt"
    if "go to youtube" in t or "open youtube" in t or "launch youtube" in t:
        open_url("https://www.youtube.com")
        return "open:youtube"
    if "go to google" in t or "open google" in t or "launch google" in t:
        open_url("https://www.google.com")
        return "open:google"

    # Close app
    m = re.match(r"close (.+)", t)
    if m:
        name = m.group(1).strip()
        exe_map = {'notepad': 'notepad.exe', 'chrome': 'chrome.exe', 'vscode': 'Code.exe'}
        exe = exe_map.get(name, f"{name}.exe")
        automation.close_app(exe)
        return f"close_app:{exe}"

    # Browser actions
    if t.startswith('search ') or t.startswith('google ') or 'search for' in t:
        q = re.sub(r"^(search for |search |google )", "", t)
        open_google_search(q)
        return f"search:google:{q}"
    if 'youtube' in t and ('search' in t or 'play' in t):
        q = re.sub(r".*(youtube|play)\s*", "", t)
        open_youtube_search(q)
        return f"search:youtube:{q}"

    # System control
    if 'shutdown' in t:
        automation.shutdown()
        return "system:shutdown"
    if 'restart' in t:
        automation.restart()
        return "system:restart"
    if 'sleep' in t:
        return "system:sleep_request"
    if 'lock' in t:
        automation.lock()
        return "system:lock"

    if 'mute' in t:
        automation.mute_toggle()
        return "volume:mute_toggle"
    if 'volume up' in t:
        automation.volume_up()
        return "volume:up"
    if 'volume down' in t:
        automation.volume_down()
        return "volume:down"

    # Keyboard / mouse
    if t.startswith('type '):
        to_type = text[text.lower().find('type ') + 5:]
        automation.type_text(to_type)
        return f"type:{to_type}"
    if t.startswith('press '):
        key = text[text.lower().find('press ') + 6:].strip()
        automation.press_key(key)
        return f"press:{key}"
    if 'screenshot' in t or 'take screenshot' in t:
        automation.screenshot()
        return "screenshot"

    if debug:
        print("No query matched")
    return ""


def handle_command(text: str, debug: bool = False) -> str:
    """Handle a normalized command text. Returns a short description of the action executed or empty string if none."""
    segments = _split_command_chain(text)
    if debug and len(segments) > 1:
        print(f"[debug] Split into command chain: {segments}")

    actions = []
    for segment in segments:
        action = _handle_single_command(segment, debug=debug)
        if action:
            actions.append(action)
            if debug:
                print(f"[debug] Executed action: {action}")

    if not actions and debug:
        print("No query matched")

    return ";".join(actions)
