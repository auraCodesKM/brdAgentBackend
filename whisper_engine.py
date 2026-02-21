from faster_whisper import WhisperModel
import os

class TranscriptionEngine:
    def __init__(self):
        # We use large-v3 for maximum accuracy in hackathon demos
        model_size = "large-v3"
        print(f"Loading Whisper Engine: {model_size}...")
        
        # CPU or Cuda depending on the system, the prompt says RTX 4090 so "cuda"
        self.model = WhisperModel(model_size, device="cuda", compute_type="float16")

    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe an audio or video file into raw text."""
        segments, info = self.model.transcribe(audio_file_path, beam_size=5)
        
        # Combine all segments into a single transcription text
        transcription = " ".join([segment.text for segment in segments])
        return transcription

whisper_engine = TranscriptionEngine()
