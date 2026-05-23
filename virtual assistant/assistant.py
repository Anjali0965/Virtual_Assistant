"""Main entrypoint for the assistant. Uses modular components for speech,
commands, automation and browser control."""

from speech import speak, listen
import commands
import automation
import browser
import wikipedia
import os


def wish_me():
    hour = int(__import__('datetime').datetime.now().hour)
    if hour >= 0 and hour < 12:
        speak("Good Morning!")
    elif hour >= 12 and hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am Jarvis Sir. Please tell me how may I help you")


import argparse


def main_loop(debug: bool = False):
    pending_sleep_confirmation = False
    _sleep_confirm_attempts = 0
    _sleep_confirm_max = 3
    wish_me()
    while True:
        query = listen(debug=debug)
        if not query:
            continue
        q = query.lower().strip()

        if pending_sleep_confirmation:
            # Accept explicit confirmations
            if q in ("yes", "yeah", "yep", "confirm", "okay", "ok", "do it"):
                if debug:
                    print("[debug] Sleep confirmation accepted")
                print("[debug] Executing sleep now")
                automation.sleep()
                pending_sleep_confirmation = False
                _sleep_confirm_attempts = 0
                continue
            if q in ("no", "cancel", "stop", "not now"):
                if debug:
                    print("[debug] Sleep confirmation cancelled")
                speak("Cancelled")
                pending_sleep_confirmation = False
                _sleep_confirm_attempts = 0
                continue
            # Also accept action-like phrases as confirmation (user may repeat the original command)
            if any(term in q for term in ("shutdown", "shut down", "sleep", "put to sleep", "hibernate")):
                if debug:
                    print("[debug] Interpreting spoken command as sleep confirmation")
                automation.sleep()
                pending_sleep_confirmation = False
                _sleep_confirm_attempts = 0
                continue
            # Track attempts and cancel after a few non-confirming replies
            _sleep_confirm_attempts += 1
            if _sleep_confirm_attempts >= _sleep_confirm_max:
                if debug:
                    print(f"[debug] Sleep confirmation timed out after {_sleep_confirm_attempts} attempts")
                speak("No confirmation received. Cancelled.")
                pending_sleep_confirmation = False
                _sleep_confirm_attempts = 0
                continue
            # ignore unrelated speech until confirmed or cancelled
            if debug:
                print(f"[debug] Waiting for sleep confirmation, heard: {q}")
            speak("Please say yes to sleep or no to cancel")
            continue

        # Wikipedia
        if 'wikipedia' in q:
            speak('Searching Wikipedia...')
            topic = q.replace('wikipedia', '').strip()
            try:
                results = wikipedia.summary(topic, sentences=2)
                speak('According to Wikipedia')
                print(results)
                speak(results)
            except Exception as e:
                print(f"Wikipedia lookup failed: {e}")
                speak("Sorry, I couldn't retrieve information from Wikipedia.")
            continue

        # Delegate to commands router
        try:
            action = commands.handle_command(q, debug=debug)
            if action == "system:sleep_request":
                if debug:
                    print(f"[debug] Recognized: {query}")
                    print("[debug] Matched action: system:sleep_request")
                speak("Do you want me to put the laptop to sleep?")
                pending_sleep_confirmation = True
                continue
            if debug:
                print(f"[debug] Recognized: {query}")
                print(f"[debug] Matched action: {action}")
        except Exception as e:
            print(f"[debug] command handling failed: {e}")


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--debug', action='store_true', help='Enable CLI debug/testing mode')
    return p.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    main_loop(debug=bool(args.debug))