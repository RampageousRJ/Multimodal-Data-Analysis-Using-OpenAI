import openai
import argparse
import dotenv
import os
from openai_text import translate_text, classify_text

dotenv.load_dotenv()

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="text"
        )
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe or translate audio files.")
    group = parser.add_mutually_exclusive_group(required=False)
    parser.add_argument("-path", type=str, help="Path to the audio file to process.", required=True)
    group.add_argument("-translate", type=str, help="Translate the audio instead of transcribing.")
    group.add_argument("-sentiment", action="store_true", help="Classify sentiment of the transcribed text.")
    args = parser.parse_args()

    if args.translate:
        print("Translating audio...")
        response = transcribe_audio(args.path)
        translated_text = translate_text(response, args.translate)
        print("Translation:", translated_text)
    elif args.sentiment:
        print("Analyzing sentiment...")
        response = transcribe_audio(args.path)
        sentiment = classify_text(response)
        print("Sentiment:", sentiment)
    else:
        print("Transcribing audio...")
        response = transcribe_audio(args.path)
        print("Transcription:", response)