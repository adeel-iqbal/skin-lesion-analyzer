import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANGUAGE_NAMES = {
    "en": "English",
    "ur": "Urdu",
    "ar": "Arabic",
}

BASE_SYSTEM = (
    "You are a helpful medical assistant. Write in plain, everyday language. "
    "Short sentences. No bullet points unless asked. "
    "Never use em dashes (the — character). Use commas or periods instead. "
    "Never use words like: seamless, leverage, delve, robust, comprehensive, navigate, boasts. "
    "Sound like a real person talking to a friend, not like a robot or a brochure."
)


def _chat(messages: list, language: str = "en", max_tokens: int = 400) -> str:
    lang_name = LANGUAGE_NAMES.get(language, "English")
    system = BASE_SYSTEM
    if language != "en":
        system += f" Respond entirely in {lang_name}."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}] + messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def explain(predicted_class: str, full_name: str, confidence: float, risk: str, language: str = "en") -> str:
    return _chat([{
        "role": "user",
        "content": (
            f"A skin lesion was classified as {full_name} ({predicted_class}) "
            f"with {confidence}% confidence. Risk level: {risk}. "
            "In 3 to 4 sentences, explain what this condition is in plain language. "
            "What does it look like, where does it appear, and what causes it? "
            "Do not give medical advice. Do not use technical jargon."
        )
    }], language=language)


def triage(predicted_class: str, full_name: str, confidence: float, risk: str, language: str = "en") -> dict:
    lang_name = LANGUAGE_NAMES.get(language, "English")
    reason_instruction = (
        f"Write the REASON in {lang_name}." if language != "en"
        else "Write the REASON in plain English."
    )
    response = _chat([{
        "role": "user",
        "content": (
            f"A skin lesion was classified as {full_name} ({predicted_class}) "
            f"with {confidence}% confidence. Risk: {risk}. "
            "Reply in this exact format:\n"
            "LEVEL: <Low / Medium / Urgent>\n"
            f"REASON: <one sentence explaining why> {reason_instruction}\n"
            "Keep LEVEL in English exactly as shown."
        )
    }], language="en", max_tokens=150)

    level = "Medium"
    reason = response
    for line in response.splitlines():
        if line.startswith("LEVEL:"):
            level = line.replace("LEVEL:", "").strip()
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return {"level": level, "reason": reason}


def next_steps(predicted_class: str, full_name: str, triage_level: str, language: str = "en") -> list[str]:
    response = _chat([{
        "role": "user",
        "content": (
            f"A skin lesion was identified as {full_name} with urgency level: {triage_level}. "
            "Give exactly 4 practical next steps the person should take. "
            "Number them 1 to 4. One short sentence each. "
            "No medical jargon. Sound like a friend giving advice."
        )
    }], language=language, max_tokens=300)

    steps = []
    for line in response.splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            steps.append(line.lstrip("1234567890.). ").strip())
    return steps[:4] if steps else [response]


def run_agents(prediction: dict, language: str = "en") -> dict:
    cls = prediction["predicted_class"]
    full = prediction["full_name"]
    conf = prediction["confidence"]
    risk = prediction["risk"]

    explanation = explain(cls, full, conf, risk, language)
    triage_result = triage(cls, full, conf, risk, language)
    steps = next_steps(cls, full, triage_result["level"], language)

    return {
        "explanation": explanation,
        "triage": triage_result,
        "next_steps": steps,
    }
