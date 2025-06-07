# ===== app/utils/helpers.py =====
def calculate_audio_duration(text: str) -> int:
    """Estimate audio duration in milliseconds based on text length"""
    # Approximate: 150 words per minute, average 5 characters per word
    words = len(text) / 5
    duration_minutes = words / 150
    return int(duration_minutes * 60 * 1000)