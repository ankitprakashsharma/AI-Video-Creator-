import os
from openai import OpenAI


def generate_script(prompt_text: str, timestamps_dict: dict) -> str:
    """
    Build a short script using OpenAI based on prompt and timestamps.
    timestamps_dict = { pid: [(start,end), ...], ... }
    """
    # fail fast if key missing
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Please configure your environment.")

    # Build readable timestamp hint
    hints = []
    for pid, pairs in timestamps_dict.items():
        for s, e in pairs:
            hints.append(f"Person {pid}: {s:.1f}s–{e:.1f}s")
    hint_text = "; ".join(hints) if hints else "No faces detected."

    system = (
        "You are a helpful script writer for short social videos (20-45s). "
        "Given a prompt and timestamps of people in clips, produce a concise "
        "scene-by-scene narration script (2-4 short sentences per scene). "
        "Include short captions in [] where appropriate."
    )
    user_msg = f"Prompt: {prompt_text}\nTimestamps: {hint_text}\nOutput: Provide a short script and scene labels."

    client = OpenAI()

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=400,
        )
        script = (resp.choices[0].message.content or "").strip()
        if not script:
            raise RuntimeError("Empty script generated from OpenAI response.")
        return script
    except Exception as exc:
        raise RuntimeError(f"OpenAI error: {exc}")
