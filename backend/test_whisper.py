from app.ai import transcribe_audio

audio_path = "uploads/your_audio_file.mp3"

transcript = transcribe_audio(audio_path)

print("\nTranscript:\n")
print(transcript)