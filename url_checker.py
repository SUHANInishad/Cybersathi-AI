"""Offline, rule-based URL risk checks for CYBERSAATHI-AI."""
from urllib.parse import urlparse
import ipaddress
import re

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly",
    "ow.ly", "buff.ly", "rb.gy", "shorturl.at",
}
SUSPICIOUS_WORDS = (
    "login", "verify", "secure", "account", "update", "confirm",
    "wallet", "banking", "password", "claim", "free", "prize",
)


def check_url(url: str) -> dict:
    """Return URL, risk score/level, warnings, and recommendation."""
    original = (url or "").strip()
    if not original:
        return {
            "url": original,
            "risk_score": 0,
            "risk_level": "Unknown",
            "warnings": ["No URL provided."],
            "recommendation": "Paste a URL to check it.",
        }

    candidate = original
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate):
        candidate = "http://" + candidate

    try:
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        parsed = urlparse("")
        host = ""

    score = 0
    warnings = []
    if not host:
        warnings.append("The URL could not be parsed correctly.")
        score += 25

    if parsed.scheme.lower() == "http":
        warnings.append("The connection uses HTTP, not encrypted HTTPS.")
        score += 10

    if "@" in parsed.netloc:
        warnings.append("The URL contains '@', which can obscure the real destination.")
        score += 25

    is_ip_address = False
    if host:
        try:
            ipaddress.ip_address(host)
            is_ip_address = True
            warnings.append("The destination is an IP address rather than a domain name.")
            score += 20
        except ValueError:
            pass

    if host in SHORTENER_DOMAINS:
        warnings.append("This is a URL-shortening service; the final destination is hidden.")
        score += 20

    if host.startswith("xn--") or ".xn--" in host:
        warnings.append("The domain uses punycode, which can sometimes disguise look-alike characters.")
        score += 15

    if host.count("-") >= 3:
        warnings.append("The domain contains many hyphens.")
        score += 10

    if len(host) > 45:
        warnings.append("The domain name is unusually long.")
        score += 10

    # Only count domain labels for hostnames, never for dotted IPv4 addresses.
    if host and not is_ip_address and len(host.split(".")) >= 4:
        warnings.append("The domain has many subdomain levels; check the actual registered domain.")
        score += 10

    combined = (host + parsed.path + parsed.query).lower()
    matched = [word for word in SUSPICIOUS_WORDS if word in combined]
    if matched:
        warnings.append(
            "The URL contains potentially deceptive terms: "
            + ", ".join(matched[:5]) + "."
        )
        score += min(20, 5 * len(matched))

    score = min(100, score)
    if score >= 60:
        level = "High"
        recommendation = "Do not open it or enter information unless you independently verify the domain."
    elif score >= 30:
        level = "Medium"
        recommendation = "Check the domain through an official source before opening or entering information."
    else:
        level = "Low"
        recommendation = "No major rule-based warning was found, but this does not prove the URL is safe."

    if not warnings:
        warnings.append("No obvious URL warning pattern was detected by these checks.")

    return {
        "url": original,
        "risk_score": score,
        "risk_level": level,
        "warnings": warnings,
        "recommendation": recommendation,
    }


# Backward-compatible alias in case the UI calls this name.
analyze_url = check_url
