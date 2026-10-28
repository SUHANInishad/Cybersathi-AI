"""Offline rule-based scam-message detector for CYBERSAATHI-AI."""
import re
from url_checker import check_url

PATTERNS = [
    ("credential_request", re.compile(
        r"\b(otp|one[- ]time password|password|pin|cvv|verification code|bank details)\b",
        re.I
    ), 35, "The message mentions sensitive credentials or banking information."),
    ("payment_request", re.compile(
        r"\b(registration fee|processing fee|pay(?:ment)?|transfer money|send money|upfront fee|deposit)\b",
        re.I
    ), 30, "The message asks for money or a fee."),
    ("urgency_threat", re.compile(
        r"\b(urgent|immediately|within \d+ hours?|account blocked|account suspended|legal action|will be closed|last warning)\b",
        re.I
    ), 20, "The message uses urgency, threats, or account-closure pressure."),
    ("too_good_to_be_true", re.compile(
        r"\b(won|winner|prize|lottery|free gift|guaranteed job|selected for|scholarship|internship)\b",
        re.I
    ), 15, "The message mentions a prize, scholarship, internship, or unusually attractive offer."),
    ("link_prompt", re.compile(
        r"\b(click here|open this link|verify your account|claim now|apply now)\b",
        re.I
    ), 10, "The message urges you to click a link or claim/verify something."),
]

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>'\"]+")


def _extract_urls(message: str) -> list:
    """Extract URLs and remove common trailing punctuation."""
    matches = URL_RE.findall(message or "")
    return [u.rstrip(".,!?;:)]}") for u in matches if u.rstrip(".,!?;:)]}")]


def analyze_message(message: str) -> dict:
    """Return score, level, warning signs, recommendation, and URL results."""
    text = (message or "").strip()
    if not text:
        return {
            "message": text,
            "risk_score": 0,
            "risk_level": "Unknown",
            "warning_signs": ["No message provided."],
            "warnings": ["No message provided."],
            "recommendation": "Paste a message to analyze.",
            "url_results": [],
        }

    score = 0
    warnings = []
    matched_patterns = set()
    for name, pattern, points, explanation in PATTERNS:
        if pattern.search(text):
            score += points
            matched_patterns.add(name)
            warnings.append(explanation)

    url_results = []
    for url in _extract_urls(text):
        result = check_url(url)
        url_results.append(result)
        if result["risk_score"] >= 60:
            score += 25
            warnings.append("A URL in the message has a high rule-based risk score.")
        elif result["risk_score"] >= 30:
            score += 15
            warnings.append("A URL in the message has medium rule-based risk signals.")
        elif result["risk_score"] >= 15:
            score += 5
            warnings.append("A URL in the message has some warning signals.")

    # High-risk combinations should not be under-scored as isolated keyword matches.
    if "credential_request" in matched_patterns and "urgency_threat" in matched_patterns:
        score += 15
        warnings.append("The message combines a request for sensitive credentials with urgency or a threat.")

    # Common scam pattern: an attractive offer paired with an upfront payment.
    has_attractive_offer = bool(re.search(
        r"\b(scholarship|internship|prize|winner|selected for|lottery|guaranteed job)\b",
        text, re.I
    ))
    asks_upfront_payment = bool(re.search(
        r"\b(registration fee|processing fee|upfront fee|deposit|pay(?:ment)?|transfer money|send money)\b",
        text, re.I
    ))
    if has_attractive_offer and asks_upfront_payment:
        score += 20
        warnings.append("The message pairs an attractive offer with a payment request.")

    score = min(100, score)
    if score >= 60:
        level = "High"
        recommendation = "Do not share OTPs, passwords, PINs, or money. Verify the sender using an official contact method."
    elif score >= 30:
        level = "Medium"
        recommendation = "Be cautious. Verify the offer and sender independently before clicking links or paying."
    else:
        level = "Low"
        recommendation = "No strong scam pattern was detected, but still verify unexpected messages."

    if not warnings:
        warnings.append("No obvious scam pattern was detected by these rules.")

    return {
        "message": text,
        "risk_score": score,
        "risk_level": level,
        "warning_signs": warnings,
        "warnings": warnings,  # alias for simple UI integration
        "recommendation": recommendation,
        "url_results": url_results,
    }


# Backward-compatible alias.
detect_scam = analyze_message
