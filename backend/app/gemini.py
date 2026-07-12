import os
import json
import time

from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Configure Gemini
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def evaluate_pronunciation(audio_path, mime_type=None):

    prompt = """
You are an expert English pronunciation evaluator and transcriber.

First, transcribe the attached audio recording verbatim. Identify the language spoken in the recording.

If the language is NOT English, return a JSON object with only the "language" field set to the detected language code (e.g. "es", "fr", "de"), and an "error" field indicating that only English speech is supported. For example:
{
  "language": "es",
  "error": "The audio is in Spanish, but only English speech is supported."
}

If the language IS English, perform the transcription and a detailed pronunciation analysis. Return a JSON object with the following fields:
{
  "language": "en",
  "transcript": "The exact verbatim text transcribed from the audio.",
  "corrected_transcript": "The text with obvious transcription errors corrected (like names or punctuation). Do not rewrite, paraphrase, or improve the speaker's grammar unless they are clearly transcription misrecognitions.",
  "overall_score": 85, // An integer from 0 to 100 representing the overall speaking quality
  "pronunciation_score": 88, // An integer from 0 to 100
  "fluency_score": 82, // An integer from 0 to 100
  "clarity_score": 85, // An integer from 0 to 100
  "pace": "Good", // "Too Slow", "Good", or "Too Fast"
  "mispronounced_words": [
    {
      "word": "artificial", // The word that was mispronounced (must match its spelling in the transcript)
      "severity": "Medium", // "Low", "Medium", or "High"
      "issue": "Weak stress on the third syllable.",
      "tip": "Stress the 'fi' syllable (ar-ti-FI-cial)."
    }
  ],
  "strengths": [
    "Clear vowel sounds",
    "Good speaking pace"
  ],
  "suggestions": [
    "Practice word stress on longer words like 'artificial'."
  ],
  "overall_feedback": "Overall very good pronunciation with minor improvements needed on word stresses."
}

Rules:
1. Under "mispronounced_words", identify actual mispronounced words or unclear segments from the audio. Do NOT invent pronunciation mistakes. If pronunciation is clear, return an empty list.
2. The transcript must represent the spoken audio as closely as possible.
3. Return ONLY valid JSON matching the schema above. Do not include markdown formatting or backticks.
"""
    try:
        # Upload audio to Gemini
        upload_config = {}
        if mime_type:
            upload_config["mime_type"] = mime_type
            
        uploaded_file = client.files.upload(file=audio_path, config=upload_config)

        print("=" * 50)
        print("Audio uploaded successfully to Gemini")
        print("File Name:", uploaded_file.name)
        print("Initial State:", uploaded_file.state.name)
        print("=" * 50)

        # Wait for Gemini to process the file
        for attempt in range(30):
            uploaded_file = client.files.get(name=uploaded_file.name)
            print(f"Attempt {attempt + 1}: Current State = {uploaded_file.state.name}")

            if uploaded_file.state.name == "ACTIVE":
               print("File is ACTIVE!")
               break

            if uploaded_file.state.name == "FAILED":
               raise Exception("Gemini failed to process the uploaded file.")

            time.sleep(2)
        else:
            raise Exception("Timed out waiting for Gemini to process the file.")

        # Generate pronunciation evaluation using response_mime_type config with fallback chain
        models_to_try = ["gemini-3.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"]
        response = None
        last_error = None
        for model in models_to_try:
            try:
                print(f"Attempting content generation using model: {model}")
                response = client.models.generate_content(
                   model=model,
                   contents=[
                      uploaded_file,
                      prompt
                   ],
                   config={
                       "response_mime_type": "application/json"
                   }
                )
                print(f"Content generation succeeded with model: {model}")
                break
            except Exception as e:
                last_error = e
                print(f"Model {model} failed: {e}")
                continue
        else:
            raise last_error if last_error else Exception("All models failed to generate content.")

        text = response.text.strip()

        # Delete uploaded file from Gemini
        try:
            client.files.delete(name=uploaded_file.name)
            print("Audio file deleted from Gemini storage.")
        except Exception as delete_error:
            print(f"Failed to delete file from Gemini storage: {delete_error}")

        # Load as JSON
        data = json.loads(text)
        return data

    except Exception as e:
        print(f"Error in evaluate_pronunciation: {e}")
        return {
            "error": str(e)
        }