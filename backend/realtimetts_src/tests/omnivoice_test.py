import logging
from RealtimeTTS import TextToAudioStream, OmniVoiceEngine, OmniVoiceVoice

logging.basicConfig(level=logging.WARN)

# 1. Provide reference audio and text for the voice you want to clone
REFERENCE_AUDIO = "don_sample.wav"
REFERENCE_TEXT = "This summer. One man. One decision. One voiceover."

if __name__ == "__main__":
    # 2. Define the voice mapping
    my_voice = OmniVoiceVoice(
        name="ClonedVoice",
        ref_audio=REFERENCE_AUDIO,
        ref_text=REFERENCE_TEXT,
        language="en" # or 'de'
    )

    # 3. Initialize the Engine
    # Note: num_steps_first_sentence enables faster first-chunk generation
    engine = OmniVoiceEngine(
        voice=my_voice,
        # num_steps_schedule=[14, 22, 32],  # balanced
        # num_steps_schedule=[8, 16, 24],  # faster but more quality drop (unstable)
        num_steps_schedule=[32, 32, 48],  # better quality, safer generation, but slower (stable)
        debug=True
    )

    # 4. Attach Engine to Stream and Play
    stream = TextToAudioStream(engine)
    
    print("Generating audio...")
    stream.feed("Hello, how are you doing? [laughter] This is a little test. We are checking out how well real-time streaming works. Using OmniVoice and RealtimeTTS.").play()
    
    engine.shutdown()