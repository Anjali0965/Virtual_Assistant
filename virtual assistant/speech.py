import speech_recognition as sr
import pyttsx3
import traceback
import re
try:
    import sounddevice as sd
    import numpy as np
except Exception:
    sd = None
    np = None

from config import (
    SOUNDDEVICE_DEVICE,
    RECORD_DURATION,
    SAMPLE_RATE,
    ENABLE_WAKE,
    WAKE_WORDS,
    WAKE_LISTEN_DURATION,
    MIN_RMS,
    WAKE_MIN_RMS,
    MAX_RMS,
)


def init_tts():
    try:
        engine = pyttsx3.init('sapi5')
    except Exception:
        engine = None
    return engine


ENGINE = init_tts()


def speak(text: str):
    if ENGINE:
        ENGINE.say(text)
        ENGINE.runAndWait()
    else:
        print(f"[speak] {text}")


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[\.,!?;:\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_filler_words(text: str) -> str:
    words = _normalize_text(text).split()
    fillers = {
        "please",
        "hey",
        "okay",
        "ok",
        "assistant",
        "jarvis",
        "kindly",
        "could",
        "you",
        "please",
    }
    while words and words[0] in fillers:
        words.pop(0)
    return " ".join(words).strip()


def _strip_wake_words(text: str):
    normalized = _normalize_text(text)
    for wake_word in WAKE_WORDS:
        if normalized.startswith(wake_word + " "):
            remainder = normalized[len(wake_word):].strip()
            return True, _strip_filler_words(remainder)
        if normalized == wake_word:
            return True, ""
    for wake_word in WAKE_WORDS:
        if wake_word in normalized:
            parts = normalized.split(wake_word, 1)
            remainder = (parts[0] + " " + parts[1]).strip()
            remainder = " ".join(remainder.split())
            return True, _strip_filler_words(remainder)
    return False, normalized


def listen_with_microphone(timeout=None):
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            r.pause_threshold = 1
            audio = r.listen(source, timeout=timeout)
            print("Recognizing...")
            return r.recognize_google(audio, language='en-in')
    except Exception as e:
        print(f"[debug] Microphone listen failed: {e}")
        return None


def listen_with_sounddevice(duration=RECORD_DURATION, fs=SAMPLE_RATE):
    if sd is None or np is None:
        print("[debug] sounddevice or numpy not available")
        return None
    try:
        sd.default.device = SOUNDDEVICE_DEVICE
        print(f"[debug] Recording {duration}s via sounddevice (device {SOUNDDEVICE_DEVICE}) - started")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        print(f"[debug] Recording {duration}s via sounddevice - completed")
        mono = np.asarray(recording, dtype=np.float32).reshape(-1)
        mono = np.clip(mono, -1.0, 1.0)
        # energy check
        rms = float(np.sqrt(np.mean(mono * mono))) if mono.size else 0.0
        print(f"[debug] Recorded RMS={rms:.6f}")
        if rms < MIN_RMS:
            print("[debug] Recording considered silent (RMS too low)")
            return None
        if rms > MAX_RMS:
            print("[debug] Recording considered noisy/clipped (RMS too high)")
            return None
        pcm16 = (mono * 32767).astype(np.int16)
        audio_data = sr.AudioData(pcm16.tobytes(), fs, 2)
        r = sr.Recognizer()
        print("[debug] Sending recorded audio to recognizer")
        try:
            text = r.recognize_google(audio_data, language='en-in')
            print(f"[debug] Speech recognized (sd): {text}")
            return text
        except sr.UnknownValueError:
            print("[debug] Recognition failed: UnknownValueError")
            return None
        except sr.RequestError as e:
            print(f"[debug] Recognition failed: RequestError: {e}")
            return None
    except Exception as e:
        print(f"[debug] Sounddevice listen failed: {repr(e)}")
        traceback.print_exc()
        return None


def _short_listen(prefer_mic=True, duration=WAKE_LISTEN_DURATION):
    # Short listen used for wake-word detection
    if prefer_mic:
        text = listen_with_microphone(timeout=duration)
        if text:
            return text
    text = listen_with_sounddevice(duration=duration)
    if text:
        return text
    return None


def wait_for_wakeword(debug=False):
    print("[debug] Waiting for wake-word...")
    while True:
        try:
            # Do a very short energy-only capture first to avoid repeated recognizer calls on silence
            if sd is not None and np is not None:
                try:
                    short_dur = 0.5
                    sd.default.device = SOUNDDEVICE_DEVICE
                    short_rec = sd.rec(int(short_dur * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
                    sd.wait()
                    mono = np.asarray(short_rec, dtype=np.float32).reshape(-1)
                    mono = np.clip(mono, -1.0, 1.0)
                    rms = float(np.sqrt(np.mean(mono * mono))) if mono.size else 0.0
                    if debug:
                        print(f"[wake-debug] short RMS={rms:.6f}")
                    if rms < WAKE_MIN_RMS:
                        continue
                    # energy detected — run a normal recognizer pass to detect wake-word
                    text = listen_with_sounddevice(duration=WAKE_LISTEN_DURATION)
                    if not text:
                        continue
                    t = _normalize_text(text)
                    if debug:
                        print(f"[wake-debug] Heard phrase: {t}")
                    for w in WAKE_WORDS:
                        if w in t:
                            print(f"[debug] Wake-word '{w}' detected")
                            return t
                    continue
                except Exception as e:
                    if debug:
                        print(f"[wake-debug] short energy check failed: {e}")
                    # fall back to previous behavior below

            # Fallback: use recognizer short listen
            text = _short_listen()
            if not text:
                continue
            t = _normalize_text(text)
            if debug:
                print(f"[wake-debug] Heard short phrase: {t}")
            for w in WAKE_WORDS:
                if w in t:
                    print(f"[debug] Wake-word '{w}' detected")
                    return t
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[debug] wakeword listen error: {e}")



def listen(prefer_mic=False, debug=False):
    # If wake-word mode enabled, wait for the keyword first
    wake_phrase = None
    if ENABLE_WAKE:
        try:
            wake_phrase = wait_for_wakeword(debug=debug)
        except KeyboardInterrupt:
            return ""

        if wake_phrase:
            matched, remainder = _strip_wake_words(wake_phrase)
            if matched and debug:
                print("[debug] Detected wake word")
                print(f"[debug] Extracted command: {remainder if remainder else '[none]'}")
            if matched and remainder:
                return remainder

    # After wake-word (or if disabled), capture the user's command
    # Prefer microphone (requires PyAudio) but gracefully fall back to sounddevice
    if prefer_mic:
        try:
            text = listen_with_microphone()
            if text:
                if debug:
                    print(f"[debug] Recognized (mic): {text}")
                # Strip wake words if present even when ENABLE_WAKE is False
                matched, remainder = _strip_wake_words(text)
                if matched:
                    if debug:
                        print(f"[debug] Stripped wake word, remainder: {remainder}")
                    return remainder
                return text
        except sr.UnknownValueError:
            # microphone recognizer couldn't understand
            speak("I didn't understand, please try again")
            return ""
        except Exception as e:
            if debug:
                print(f"[debug] Microphone path failed: {e}")

    # sounddevice fallback
    text = listen_with_sounddevice()
    if text:
        # Strip wake words if present even when ENABLE_WAKE is False
        matched, remainder = _strip_wake_words(text)
        if matched:
            if debug:
                print("[debug] Detected wake word")
                print(f"[debug] Extracted command: {remainder if remainder else '[none]'}")
            if remainder:
                return remainder
            return ""
        if debug:
            print(f"[debug] Recognized (sd): {text}")
        return text
        if debug:
            print(f"[debug] Recognized (sd): {text}")
        return text

    # If speech not recognized, prompt and continue listening
    try:
        speak("I didn't understand, please try again")
    except Exception:
        pass
    return ""
