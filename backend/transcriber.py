import whisper

_model = None


def get_model(model_size: str = "small") -> whisper.Whisper:
    global _model
    if _model is None:
        _model = whisper.load_model(model_size)
    return _model


def transcribe(audio_path: str) -> str:
    model = get_model()
    result = model.transcribe(audio_path, language="en")
    return result["text"].strip()
