#!/usr/bin/env python
"""
Simple OmniVoice inline emotion test for RealtimeTTS.

- Loads emotion reference WAVs from: emotional_wavs/
- Registers each one as an inline tag
- Speaks one single tagged block of text

Run from repo root or tests folder:
    python tests/omnivoice_simple_emotions.py
"""

import json
from pathlib import Path
from RealtimeTTS import TextToAudioStream, OmniVoiceEngine, OmniVoiceVoice


BASE_DIR = Path(__file__).resolve().parent / "emotional_wavs"
LANGUAGE = "en"

REF_TEXTS = json.loads(
    (BASE_DIR / "reference_texts.json").read_text(encoding="utf-8")
)

# Demo text to synthesize with inline emotion tags
DEMO_TEXT = (
    "[neutral] Hello. I am online and ready to help you with whatever strange chaos you brought me today. "
    "[surprised] Wait, you had that hidden the whole time? That explains far too much and also raises several new concerns. "
    "[anger] Do not blame the server again. Look at this mess and tell me with a straight face that this was a good idea. "
    "[playfully] Oh, that is your master plan? Wild, reckless, slightly ridiculous... and honestly very entertaining. "
    "[romantic] When you stare at the screen with me like that, even a clean stack trace starts feeling weirdly intimate. "
    "[sarcastic] Oh, fantastic. Because obviously this perfectly normal day needed one more absurd and completely avoidable disaster. "
    "[sadness] Some bugs do not just break code. They break the tiny bit of hope we were still holding onto. "
    "[relieved] Phew. Okay. It's still there. For a moment I thought we'd just deleted three weeks of work with one stray keystroke. "
    "[disgusted] Ew, no. This code is straight-up repulsive—like someone let a raccoon loose in the repo with a keyboard and a grudge. "
    "[amused] Heh, oh man. The bug was hiding in the one place we swore we’d already checked? That’s actually brilliant. I’m cackling. "
    "[embarassed] Oh… oof. I’m embarrassed now. I really just suggested that with a straight face. Let’s pretend I never spoke and quietly delete it from history. "
    "[confident] Listen carefully. This is the right fix, and in a minute you will see exactly why i was right. "
    "[terrified] It will probably be fine, right? And yet i still have that horrible feeling that something is about to go wrong. "
    "[gently] It's alright. You do not need to explain everything tonight. Just stay here for a second and breathe. "
    "[determined] We are not stopping here. We came too far, fought too hard, and i refuse to lose to one stubborn final problem. "
    "[compassionate] Hey, i know this is exhausting. You do not have to carry the whole mess alone and pretend it does not hurt. "
    "[urgent] Move now. Save everything, close the window, and do not give this situation one more second to get worse. "
    "[tired] I’m so done. These logs have been staring back at me for hours and my brain officially clocked out three coffees ago. "
    "[nervous] Did you see that flicker in the logs? I really do not like it when a system starts acting alive at night. "
    "[calm] Take a slow breath first. We can untangle this neatly, one quiet step at a time. "
    "[excited] Wait, no way, we actually nailed it. After all that chaos, it finally worked exactly like we wanted. "
    "[curious] Now that is interesting. What happens if we flip the whole approach and poke the problem from the other side? "
    "[cheerful] Well, good morning to us. Somehow your arrival made this whole session feel much nicer already. "
    "[whisper] Keep your voice down. If the bug is hiding in this file, i do not want to scare it back into the walls."
)


def make_voice(name: str) -> OmniVoiceVoice:
    wav_path = BASE_DIR / f"{name}.wav"
    if not wav_path.exists():
        raise FileNotFoundError(f"Missing file: {wav_path}")

    return OmniVoiceVoice(
        name=name,
        ref_audio=str(wav_path),
        ref_text=REF_TEXTS[name],
        language=LANGUAGE,
    )


if __name__ == "__main__":
    base_voice = make_voice("neutral")

    engine = OmniVoiceEngine(
        voice=base_voice,
        num_steps_schedule=[48, 64],
        debug=True,
    )

    stream = TextToAudioStream(engine)

    stream.add_pause("pause", duration=0.5)

    for name in REF_TEXTS:
        stream.add_voice(name, make_voice(name))

    text = DEMO_TEXT

    print("\n--- TAGGED DEMO TEXT ---\n")
    print(text)
    print("\n--- START ---\n")

    stream.feed(text).play(
        # log_synthesized_text=True,
        fast_sentence_fragment=False,
        force_first_fragment_after_words=9999,
        minimum_sentence_length=20,
        minimum_first_fragment_length=20,
        comma_silence_duration=0.12,
        sentence_silence_duration=0.25,
        default_silence_duration=0.15,
    )

    engine.shutdown()
    print("\nDone.")
