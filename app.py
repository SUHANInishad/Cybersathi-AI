import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import base64
import re
import html
import io
import time

from detector import analyze_message as calculate_risk

try:
    from ai_analyzer import analyze_message
except ImportError:
    analyze_message = None

try:
    from screenshot import read_screenshot
except ImportError:
    read_screenshot = None


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CyberSathi AI | Scam Detection Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
BACKGROUND_PATH = BASE_DIR / "background.jpeg"


# ============================================================
# 2. BACKGROUND IMAGE
#    (overlay lightened + made cool-blue so the image is visible)
# ============================================================

if BACKGROUND_PATH.exists():
    with open(BACKGROUND_PATH, "rb") as image_file:
        encoded_image = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    background_css = f"""
        linear-gradient(
            180deg,
            rgba(240, 247, 255, 0.50) 0%,
            rgba(236, 245, 255, 0.40) 45%,
            rgba(236, 245, 255, 0.45) 100%
        ),
        url("data:image/jpeg;base64,{encoded_image}")
    """
else:
    background_css = """
        linear-gradient(
            135deg,
            #e5f3ff 0%,
            #f7fbff 55%,
            #eaf5ff 100%
        )
    """


# ============================================================
# 3. CSS - THEME + HEADINGS + REFINED 3D LOOK (UI only)
# ============================================================

# Selector prefix for the three result metric blocks (used inside the CSS)
METRIC_ROW = (
    '[data-testid="stMain"] '
    '[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) '
    '> [data-testid="stColumn"]'
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Poppins:wght@400;500;600;700&display=swap');

/* ============ DESIGN TOKENS ============ */

:root {
    --blue-900: #0b2e4d;
    --blue-800: #0f3a5f;
    --blue-700: #155b91;
    --blue-600: #1768a5;
    --blue-500: #1f8dd0;
    --sky-400: #35b0e6;
    --ink: #18344d;
    --ink-soft: #35536c;

    /* soft top light on glossy surfaces */
    --gloss: linear-gradient(180deg, rgba(255, 255, 255, 0.20) 0%, rgba(255, 255, 255, 0) 52%);

    /* raised "plate": light top edge + thin solid underside + soft ground shadow */
    --plate:
        inset 0 1px 0 rgba(255, 255, 255, 0.95),
        inset 0 -1px 0 rgba(23, 104, 165, 0.10),
        0 1px 0 #c9dff0,
        0 3px 0 #b1cfe7,
        0 4px 0 rgba(12, 58, 100, 0.22),
        0 16px 26px -8px rgba(10, 50, 90, 0.34);

    --plate-hover:
        inset 0 1px 0 rgba(255, 255, 255, 0.95),
        inset 0 -1px 0 rgba(23, 104, 165, 0.10),
        0 1px 0 #c9dff0,
        0 3px 0 #b1cfe7,
        0 4px 0 rgba(12, 58, 100, 0.22),
        0 24px 34px -10px rgba(10, 50, 90, 0.42);

    /* recessed "well" used for BOTH input boxes (same colour) */
    --well:
        inset 0 3px 7px rgba(14, 58, 98, 0.20),
        inset 0 0 0 1px rgba(255, 255, 255, 0.35),
        0 1px 0 rgba(255, 255, 255, 0.95);
}

/* ============ PAGE ============ */

[data-testid="stApp"] {
    color-scheme: light;
}

[data-testid="stAppViewContainer"] {
    background: __BG__;
    background-size: cover;
    background-position: center center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

[data-testid="stHeader"] {
    background: rgba(239, 247, 255, 0.55);
    backdrop-filter: blur(6px);
}

[data-testid="stMain"] {
    background: transparent;
}

.block-container,
[data-testid="stMainBlockContainer"] {
    padding-top: 3.4rem !important;
    padding-bottom: 2rem !important;
}

[data-testid="stMain"] [data-testid="stVerticalBlock"] {
    gap: 0.8rem;
}

/* ============ SCREEN 1 : fills the laptop screen, equal spacing ============ */

.st-key-screen1 {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    gap: 1.3rem !important;
}

/* ============ SCREEN 2 : the report always starts on a fresh screen ============ */

.st-key-report_screen {
    min-height: 100vh;
    margin-top: 2.2rem;
    padding-top: 1.2rem;
    gap: 1.6rem !important;
}

#output-scroll-anchor {
    height: 0;
    scroll-margin-top: 4rem;
}

/* ============ THIN ENGRAVED DIVIDER LINES ============ */

[data-testid="stMain"] hr {
    border: 0 !important;
    height: 1px !important;
    margin: 0 !important;
    background: linear-gradient(
        90deg,
        rgba(23, 104, 165, 0) 0%,
        rgba(23, 104, 165, 0.55) 14%,
        rgba(23, 104, 165, 0.55) 86%,
        rgba(23, 104, 165, 0) 100%
    ) !important;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9);
}

/* ============ COLOURFUL ICONS ============ */

.icon-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: none;
    line-height: 1;
    font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif;
    filter: drop-shadow(0 3px 2px rgba(10, 37, 64, 0.35));
}

/* tile used in the three info cards */
.icon-badge:not(.sm):not(.sec):not(.lg) {
    font-size: 2.2rem;
    border-radius: 16px;
    background: transparent !important;
    border: none;
    box-shadow: none;
}

/* inline icons: exactly the size of the heading text next to them */
.icon-badge.sm  { font-size: 1.35rem; }
.icon-badge.sec { font-size: clamp(1.5rem, 2.4vw, 2.1rem); }
.icon-badge.lg  { font-size: clamp(1.8rem, 3.6vw, 2.9rem); }

/* ============ MAIN HEADINGS (Playfair Display, extruded 3D) ============ */

.fancy-title {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: clamp(14px, 1.6vw, 26px);
    margin: 0;
    line-height: 1.1;
}

.fancy-title .hero-shield {
    height: clamp(3.6rem, min(7vw, 11.5vh), 5.8rem);
    width: auto;
    flex: none;
    filter: drop-shadow(0 7px 6px rgba(10, 37, 64, 0.38));
}

.fancy-title .fancy-text {
    font-family: 'Playfair Display', 'Georgia', 'Times New Roman', serif;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: clamp(2.6rem, min(5.4vw, 9.6vh), 4.9rem);
    background: linear-gradient(
        90deg,
        #0b2e4d 0%,
        #1768a5 38%,
        #2b9ad8 62%,
        #155b91 82%,
        #0d3556 100%
    );
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
    filter:
        drop-shadow(1px 1px 0 #0a2540)
        drop-shadow(2px 2px 0 #0a2540)
        drop-shadow(3px 5px 6px rgba(10, 37, 64, 0.35));
}

.fancy-title .hero-text {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.fancy-title .hero-text .fancy-text {
    display: inline-block;
}

.hero-sub {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-size: clamp(1rem, 1.25vw, 1.2rem);
    font-weight: 500;
    line-height: 1.5;
    color: #1f425e;
    margin-top: clamp(12px, 1.9vh, 22px);
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.9), 0 1px 0 rgba(255, 255, 255, 0.9);
}

/* Section heading: same style, smaller, lighter blue */
.fancy-title.section-size {
    gap: 14px;
}

.fancy-title.section-size .fancy-text {
    font-weight: 700;
    letter-spacing: 0.8px;
    font-size: clamp(1.5rem, 2.4vw, 2.1rem);
    background: linear-gradient(
        90deg,
        #0f6f9e 0%,
        #1f94cf 45%,
        #2fa8e0 70%,
        #1768a5 100%
    );
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    filter:
        drop-shadow(1px 1px 0 #0d3f63)
        drop-shadow(2px 3px 4px rgba(10, 37, 64, 0.25));
}

/* Report heading */
.fancy-title.report-size {
    margin: 0 0 0.6rem 0;
}

.fancy-title.report-size .fancy-text {
    font-size: clamp(1.8rem, 3.6vw, 2.9rem);
    letter-spacing: 0.5px;
}

/* ============ THREE INFO CARDS ============ */

[data-testid="stHorizontalBlock"]:has(.mini-card) {
    gap: 1.4rem !important;
}

.mini-card {
    display: flex;
    align-items: center;
    gap: 16px;
   
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(200, 220, 240, 0.6);

    border-left: 5px solid var(--blue-600);
    border-radius: 16px;
    padding: clamp(14px, 2.3vh, 22px) 22px;
    line-height: 1.3;
    box-shadow: var(--plate);
    overflow-wrap: anywhere;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}



.mini-card:hover {
    transform: perspective(900px) rotateX(2.5deg) translateY(-3px);
    box-shadow: var(--plate-hover);
}

.mini-card .mini-text {
    min-width: 0;
}

.mini-card .mini-label {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--ink-soft);
    margin-bottom: 3px;
}

.mini-card .mini-value {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-size: clamp(1.2rem, 1.85vw, 1.6rem);
    font-weight: 600;
    color: #174e79;
    text-shadow: 0 1px 0 #ffffff, 0 2px 3px rgba(23, 78, 121, 0.18);
}

/* ============ INPUT PANEL (light frosted slab) ============ */

.st-key-input_panel {
    gap: 1.1rem !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

.st-key-input_panel [data-testid="stHorizontalBlock"] {
    gap: 1.6rem !important;
}

.st-key-input_panel [data-testid="stColumn"] [data-testid="stVerticalBlock"] {
    gap: 1.1rem !important;
}

/* ===== FIX: "ANALYZE SUSPICIOUS CONTENT" heading aur uske neeche wali
   headings (Paste Message / Upload Screenshot) ke beech distance =====
   Zyada ya kam chahiye to neeche ki 2 values (34px aur 1.2rem) badal do. */
.st-key-input_panel .fancy-title.section-size {
    margin-bottom: 2px !important;
    padding-bottom: 6px !important;
}

.st-key-input_panel [data-testid="stHorizontalBlock"] {
    margin-top: 0.2rem !important;
}

/* ANALYZE SUSPICIOUS CONTENT के मुख्य ब्लॉक के नीचे दूरी बढ़ाने के लिए */
.stMainBlockContainer > div:has(.input-heading) {
    margin-bottom: 25px !important;
}
.input-heading {
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-weight: 600;
    font-size: 1.35rem;
    color: #153d60;
    margin-bottom: 11px !important;
    line-height: 1.3;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.9), 0 2px 4px rgba(21, 61, 96, 0.2);
}



.input-desc {
    font-size: 1rem;
    color: var(--ink);
    margin-bottom: 20px !important;
    line-height: 1.4;
    text-shadow: 0 0 6px rgba(255, 255, 255, 0.85);
}

[data-testid="stAppViewContainer"] .stMarkdown,
[data-testid="stAppViewContainer"] .stText,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] .stCaption {
    color: var(--ink);
}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    color: #153d60;
}

/* ============ SIDEBAR ============ */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #102b46 0%, #173d60 55%, #10263d 100%);
    border-right: 1px solid #315a7c;
}

[data-testid="stSidebar"] * {
    color: #f0f7ff;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff;
}

[data-testid="stSidebar"] hr {
    background: rgba(220, 239, 255, 0.25) !important;
    box-shadow: none;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #c5d9eb;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #f4f9ff;
    border: 1px solid #9cc8eb;
    border-radius: 8px;
}

[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #18344d;
}

[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(203, 229, 250, 0.35);
    border-radius: 10px;
}

[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 0;
}

[data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div {
    min-width: 0;
}

/* ============ INPUT BOXES : BOTH IDENTICAL, LIGHT, RECESSED 3D ============ */

/* clear any dark theme background on the wrappers */
[data-testid="stTextArea"] div {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

[data-testid="stTextArea"] textarea {
    background: linear-gradient(180deg, #e8f2fc 0%, #f6faff 100%) !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    caret-color: var(--blue-600);
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-size: 1rem;
    line-height: 1.55;
    padding: 14px 16px !important;
    border: 1px solid #9fc4e2 !important;
    border-radius: 14px !important;
    box-shadow: var(--well) !important;
    resize: none;
    height: 140px !important;
    min-height: 140px !important;
    box-sizing: border-box;
    margin-bottom: 20px !important;
}

[data-testid="stTextArea"] textarea:focus {
    border-color: #2788c9 !important;
    box-shadow: var(--well), 0 0 0 3px rgba(39, 136, 201, 0.25) !important;
    outline: none !important;
}

[data-testid="stTextArea"] textarea::placeholder {
    color: #6b86a0 !important;
    -webkit-text-fill-color: #6b86a0 !important;
    opacity: 1;
}

[data-testid="InputInstructions"],
[data-testid="stTextArea"] small {
    color: #5d7a93 !important;
}

[data-testid="stFileUploader"] {
    background: linear-gradient(180deg, #e8f2fc 0%, #f6faff 100%) !important;
    border: 1px solid #9fc4e2;
    border-radius: 14px;
    padding: 10px 14px;
    box-shadow: var(--well);
    margin-top: 0;
    /* same visible size as the message box */
    height: 140px;
    box-sizing: border-box;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.60) !important;
    border: 1.5px dashed #6fa8d6 !important;
    border-radius: 10px !important;
    padding: 10px !important;
    min-height: 70px;
}

[data-testid="stFileUploaderDropzone"] * {
    color: #244967 !important;
}

/* uploaded-file chip: light instead of black */
[data-testid="stFileUploaderFile"] {
    background: #d9eafa !important;
    border: 1px solid #9fc4e2 !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 0 #b1cfe7 !important;
}

[data-testid="stFileUploaderFile"] * {
    background-color: transparent !important;
    color: #164b76 !important;
}

[data-testid="stFileUploaderFile"] svg {
    fill: #164b76 !important;
}

[data-testid="stFileUploader"] button {
    background: #e2f1ff !important;
    color: #164b76 !important;
    border: 1px solid #9ac7eb !important;
    border-radius: 8px !important;
}

[data-testid="stFileUploader"] button:hover {
    background: #d1e9ff !important;
    color: #103c61 !important;
    border-color: #5d9ed0 !important;
}

[data-testid="stFileUploader"] button svg {
    fill: #164b76 !important;
}

/* uploaded-file chip (newer Streamlit versions) */
[data-testid^="stFileChip"],
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
    background: #d9eafa !important;
    border: 1px solid #9fc4e2 !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 0 #b1cfe7 !important;
}

[data-testid^="stFileChip"] *,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p {
    background-color: transparent !important;
    color: #164b76 !important;
}

.preview-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.80);
    border: 1px solid #9fc4e2;
    box-shadow: 0 3px 0 #b1cfe7, 0 10px 16px -8px rgba(10, 50, 90, 0.35);
    font-size: 0.9rem;
    color: var(--ink-soft);
}

.preview-box img {
    height: 64px;
    width: auto;
    border-radius: 8px;
    box-shadow: 0 3px 8px rgba(10, 50, 90, 0.3);
}

/* caption under the result cards: always clearly readable */
[data-testid="stMain"] [data-testid="stCaptionContainer"] {
    display: inline-block;
    width: fit-content;
    max-width: 100%;
    padding: 8px 16px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.82);
    border-left: 4px solid var(--blue-600);
    box-shadow: 0 3px 0 #b1cfe7, 0 10px 16px -8px rgba(10, 50, 90, 0.35);
}

[data-testid="stMain"] [data-testid="stCaptionContainer"] p {
    color: #12344d !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
}

/* small, tidy preview thumbnail */
[data-testid="stImage"] img {
    border-radius: 10px;
    max-height: 100px;
    object-fit: contain;
}

[data-testid="stImage"] [data-testid="stImageCaption"] {
    color: var(--ink-soft);
    font-size: 0.85rem;
}

/* ============ ANALYZE BUTTON (pressable 3D key, slim + centred) ============ */

.st-key-action_zone {
    gap: 0.8rem !important;
    align-items: center;
}

.st-key-action_zone .stButton {
    display: flex;
    justify-content: center;
    width: 100%;
    margin-top: 25px !important;
    margin-bottom: 20px !important;
}

[data-testid="stMain"] .stButton > button {
    position: relative;
    overflow: hidden;
    width: 100% !important;
    background:
        var(--gloss),
        linear-gradient(180deg, #6a5cf5 0%, #4a3fd6 52%, #30279e 100%);
    color: #ffffff;
    border: 1px solid #231a7c;
    border-radius: 8px !important;
    font-weight: 700;
    min-height: 3.1rem;
    text-shadow: 0 1px 2px rgba(15, 8, 60, 0.5);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.55),
        inset 0 -2px 0 rgba(20, 12, 80, 0.30),
        0 5px 0 #1d1570,
        0 6px 0 #130d4d,
        0 16px 22px -6px rgba(48, 39, 158, 0.55);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

[data-testid="stMain"] .stButton > button::after {
    content: "";
    position: absolute;
    top: 0;
    left: -60%;
    width: 38%;
    height: 100%;
    background: linear-gradient(
        100deg,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.34) 50%,
        rgba(255, 255, 255, 0) 100%
    );
    transform: skewX(-18deg);
    transition: left 0.7s ease;
    pointer-events: none;
}

[data-testid="stMain"] .stButton > button:hover::after {
    left: 130%;
}

[data-testid="stMain"] .stButton > button p {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    color: #ffffff !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.6px;
}

[data-testid="stMain"] .stButton > button:hover {
    background:
        var(--gloss),
        linear-gradient(180deg, #7b6dff 0%, #5a4ee6 52%, #3a30b3 100%);
    color: #ffffff;
    border-color: #231a7c;
    transform: translateY(-2px);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.6),
        inset 0 -2px 0 rgba(20, 12, 80, 0.30),
        0 7px 0 #1d1570,
        0 8px 0 #130d4d,
        0 22px 28px -8px rgba(48, 39, 158, 0.6);
}

[data-testid="stMain"] .stButton > button:active {
    transform: translateY(4px);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.4),
        0 1px 0 #1d1570,
        0 5px 8px rgba(48, 39, 158, 0.4);
}

/* ============ REPORT: THREE SCORE BLOCKS ============ */

[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
    gap: 1.4rem !important;
}

[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid #c2ddef;
    border-radius: 16px;
    padding: 18px 24px;
    min-height: 108px;
    box-shadow: var(--plate);
    min-width: 0;
}

__METRIC_ROW__ [data-testid="stMetric"] {
    border: 1px solid #0f4f84 !important;
    border-left: 7px solid #7cc0ee !important;
    border-bottom: 4px solid #07233d !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.30),
        0 3px 0 #061e35,
        0 16px 24px -8px rgba(10, 37, 64, 0.45) !important;
    transition: transform 0.25s ease;
}

__METRIC_ROW__ [data-testid="stMetric"]:hover {
    transform: perspective(900px) rotateX(2deg) translateY(-3px);
}

__METRIC_ROW__:nth-child(1) [data-testid="stMetric"] {
    background: var(--gloss), linear-gradient(135deg, #0b2e4d, #155b91) !important;
}

__METRIC_ROW__:nth-child(2) [data-testid="stMetric"] {
    background: var(--gloss), linear-gradient(135deg, #155b91, #2b8fd1) !important;
}

__METRIC_ROW__:nth-child(3) [data-testid="stMetric"] {
    background: var(--gloss), linear-gradient(135deg, #0f6f9e, #35b0e6) !important;
}

__METRIC_ROW__ [data-testid="stMetricLabel"] p {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: #dcefff !important;
}

__METRIC_ROW__ [data-testid="stMetricValue"],
__METRIC_ROW__ [data-testid="stMetricValue"] > div {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    text-shadow: 0 2px 3px rgba(5, 25, 45, 0.45);
    overflow-wrap: anywhere;
    white-space: normal !important;
}

/* ============ ALERT BOXES (blue by default, colour-coded by level) ============ */

div[data-testid="stMainBlockContainer"] [data-testid="stAlert"],
div[data-testid="stMainBlockContainer"] [data-baseweb="notification"] {
    background-color: #e6f2fc !important;
    background-image: none !important;
    border: 1px solid #a1d0f5 !important;
    border-left: 6px solid #1768a5 !important;
    border-radius: 14px !important;
    padding: 4px 8px;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.9),
        0 3px 0 #b9d8ef,
        0 12px 20px -8px rgba(24, 52, 77, 0.30) !important;
}

div[data-testid="stMainBlockContainer"] [data-testid="stAlert"] *,
div[data-testid="stMainBlockContainer"] [data-baseweb="notification"] * {
    color: #12344d !important;
    fill: #12344d !important;
    font-weight: 600 !important;
    font-size: 0.97rem !important;
}

/* HIGH RISK / error */
div[data-testid="stMainBlockContainer"] [data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {
    background-color: #fdeef0 !important;
    border-color: #efb3bc !important;
    border-left-color: #b32d44 !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.9),
        0 3px 0 #efc3ca,
        0 12px 20px -8px rgba(110, 20, 40, 0.30) !important;
}

div[data-testid="stMainBlockContainer"] [data-testid="stAlert"]:has([data-testid="stAlertContentError"]) * {
    color: #5c1223 !important;
    fill: #5c1223 !important;
}

/* MEDIUM RISK / warning */
div[data-testid="stMainBlockContainer"] [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {
    background-color: #fff6e6 !important;
    border-color: #f1d08f !important;
    border-left-color: #c27712 !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.9),
        0 3px 0 #f0d9a8,
        0 12px 20px -8px rgba(110, 66, 6, 0.28) !important;
}

div[data-testid="stMainBlockContainer"] [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) * {
    color: #5a3605 !important;
    fill: #5a3605 !important;
}

/* LOW RISK / success */
div[data-testid="stMainBlockContainer"] [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
    background-color: #e8f7f2 !important;
    border-color: #9fdcc7 !important;
    border-left-color: #168f73 !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.9),
        0 3px 0 #b3e3d3,
        0 12px 20px -8px rgba(10, 84, 70, 0.26) !important;
}

div[data-testid="stMainBlockContainer"] [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) * {
    color: #0a4538 !important;
    fill: #0a4538 !important;
}

div[data-testid="stSidebar"] [data-testid="stAlert"],
div[data-testid="stSidebar"] [data-baseweb="notification"] {
    background-color: rgba(255, 255, 255, 0.12) !important;
    background-image: none !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 10px !important;
}

div[data-testid="stSidebar"] [data-testid="stAlert"] *,
div[data-testid="stSidebar"] [data-baseweb="notification"] * {
    color: #ffffff !important;
    fill: #ffffff !important;
    font-weight: 500 !important;
}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li {
    font-size: 1rem !important;
    line-height: 1.6 !important;
    overflow-wrap: anywhere !important;
}

div[data-testid="stMarkdownContainer"] {
    overflow-wrap: anywhere;
    min-width: 0;
}

/* ============ REPORT CARDS (3D plates) ============ */

.report-card {
    background: rgba(255, 255, 255, 0.84);
    border: 1px solid rgba(103, 153, 195, 0.48);
    border-radius: 16px;
    padding: 18px 22px;
    margin: 0;
    box-sizing: border-box;
    box-shadow: var(--plate);
    color: #102f49;
    overflow-wrap: anywhere;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.report-card:hover {
    transform: perspective(1000px) rotateX(1.2deg) translateY(-3px);
    box-shadow: var(--plate-hover);
}

/* 2x2 grid: all four main report blocks have equal size */
.report-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: 1fr;
    gap: 24px;
    margin: 6px 0 8px 0;
}

.report-grid .report-card {
    height: 100%;
}

.report-single {
    margin: 0 0 8px 0;
}

.report-card h3 {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    color: #103b5d !important;
    font-size: 1.14rem !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    margin: 0 0 12px 0 !important;
    padding: 0 0 10px 0 !important;
    border-bottom: 1px solid rgba(45, 100, 145, 0.28);
}

.report-card p,
.report-card li {
    color: #102f49 !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
}

.report-card p {
    margin: 0 0 8px 0 !important;
}

.report-card p:last-child {
    margin-bottom: 0 !important;
}

.report-card ul,
.report-card ol {
    padding-left: 22px;
    margin: 0;
}

.report-card li {
    margin-bottom: 6px;
}

.report-card li:last-child {
    margin-bottom: 0;
}

.report-card a {
    color: #155b91 !important;
    font-weight: 700;
    text-decoration: underline;
}

.report-card .footer-note {
    color: var(--ink) !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    margin: 0 0 9px 0 !important;
}

.report-card .footer-note:last-child {
    margin-bottom: 0 !important;
}

.report-card .report-url code {
    background: #e2f1ff;
    color: #103b5d;
    border: 1px solid #a8c9e5;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.92rem;
}

.report-card .secondary {
    color: var(--ink-soft) !important;
    font-size: 0.92rem !important;
    margin-bottom: 8px;
}

.report-card .detail-label {
    color: #244967;
    font-weight: 700;
    font-size: 0.94rem;
    margin-bottom: 4px;
}

.report-card .detail-value {
    color: #102f49;
    font-size: 1rem;
    line-height: 1.6;
}

.report-note {
    color: #244967;
    font-size: 0.91rem;
    line-height: 1.55;
    margin: 6px 0 10px 0;
}

.report-url {
    color: #103b5d;
    overflow-wrap: anywhere;
    word-break: break-word;
}

@media (max-width: 900px) {
    .report-grid {
        grid-template-columns: 1fr;
        grid-auto-rows: auto;
    }
}

@media (max-width: 768px) {
    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .st-key-screen1 {
        min-height: auto;
    }

    __METRIC_ROW__ [data-testid="stMetricValue"],
    __METRIC_ROW__ [data-testid="stMetricValue"] > div {
        font-size: 1.35rem !important;
    }

    .report-card {
        padding: 14px 16px;
    }

    .report-card h3 {
        font-size: 1.05rem !important;
    }
}
"""

st.markdown(
    "<style>"
    + CSS.replace("__BG__", background_css).replace("__METRIC_ROW__", METRIC_ROW)
    + "</style>",
    unsafe_allow_html=True
)


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def as_text(value, default=""):
    if value is None:
        return default

    if isinstance(value, (list, tuple)):
        return "\n".join(str(item) for item in value if item)

    return str(value).strip() or default


def as_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, str):
        return [value] if value.strip() else []

    return [str(value)]


def safe_html(value):
    """Escape untrusted message/AI output before placing it in HTML."""
    return html.escape(as_text(value), quote=True)


def unique_text_items(*groups):
    items = []
    seen = set()

    for group in groups:
        for value in as_list(group):
            text_value = as_text(value).strip()
            key = text_value.casefold()

            if text_value and key not in seen:
                seen.add(key)
                items.append(text_value)

    return items


def extract_screenshot_text(upload):
    if read_screenshot is None:
        raise RuntimeError(
            "screenshot.py could not be imported. "
            "Check that it contains read_screenshot()."
        )

    upload.seek(0)
    result = read_screenshot(upload)

    if isinstance(result, dict):
        extracted = result.get(
            "text",
            result.get("extracted_text", "")
        )
    else:
        extracted = result

    return as_text(extracted)


def extract_urls(message, report):
    urls = []

    if isinstance(report, dict):
        urls = as_list(report.get("urls_analyzed", []))

    if not urls:
        urls = re.findall(
            r"""https?://[^\s<>"']+|www\.[^\s<>"']+""",
            message,
            flags=re.IGNORECASE
        )

    unique_urls = []
    seen = set()

    for url in urls:
        cleaned = str(url).rstrip(".,;:!?) ]}")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_urls.append(cleaned)

    return unique_urls


def card_html(title, content, extra_class=""):
    """Build one report card as a single-line HTML string."""
    content = re.sub(r">\s+<", "><", str(content).strip())
    heading = f"<h3>{safe_html(title)}</h3>" if title else ""
    return (
        f'<section class="report-card {extra_class}">'
        f'{heading}{content}</section>'
    )


def render_report_card(title, content, extra_class=""):
    """Render a single full-width report card."""
    st.markdown(
        f'<div class="report-single">'
        f'{card_html(title, content, extra_class)}</div>',
        unsafe_allow_html=True
    )


def render_card_grid(cards):
    """Render report cards in a 2-column grid with equal-sized blocks."""
    inner = "".join(card_html(title, content) for title, content in cards)
    st.markdown(
        f'<div class="report-grid">{inner}</div>',
        unsafe_allow_html=True
    )


def make_list_html(items, ordered=False):
    if not items:
        return (
            "<p>No specific items were returned by this analysis.</p>"
        )

    tag = "ol" if ordered else "ul"
    list_items = "".join(
        f"<li>{safe_html(item)}</li>"
        for item in items
    )

    return f"<{tag}>{list_items}</{tag}>"


# ---------- UI-only helpers (icons / layout) ----------

def one_line(markup):
    """Collapse HTML into one line so Markdown never breaks the block."""
    markup = re.sub(r"\s+", " ", markup.strip())
    return re.sub(r">\s+<", "><", markup)


def keyed_container(key):
    """Container with a CSS hook; falls back to a plain one on old Streamlit."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()



ICON_EMOJI = {
    "shield-check": "🔒",   
    "image": "📑",         
    "cpu": "🗣️",            
    "scan-search": "🔍",
    "message": "📝",
    "upload": "📸",
    "chart": "📊",
}

def icon_badge(name, size=""):
    return (
        f'<span class="icon-badge {size}" aria-hidden="true">'
        f'{ICON_EMOJI[name]}</span>'
    )


def make_preview_html(upload):
    """Small base64 thumbnail so the preview never shows a broken image."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(upload.getvalue()))
        img.thumbnail((320, 200))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=80)
        data = base64.b64encode(buf.getvalue()).decode("utf-8")
        return (
            '<div class="preview-box">'
            f'<img src="data:image/jpeg;base64,{data}" alt="Preview"/>'
            '<span>Preview of Uploaded Screenshot</span></div>'
        )
    except Exception:
        return None

HERO_SHIELD = (
    '<svg class="hero-shield" viewBox="0 0 100 100" width="70" height="70" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<!-- Base 3D Shadow -->'
    '<ellipse cx="50" cy="88" rx="35" ry="7" fill="#000" fill-opacity="0.25"/>'
    '<!-- Outer 3D Shield Layer -->'
    '<path d="M50 8L15 24V48C15 69.5 30 84 50 90C70 84 85 69.5 85 48V24L50 8Z" fill="url(#shield_grad_back)"/>'
    '<!-- Inner 3D Front Plate -->'
    '<path d="M50 14L22 27V48C22 65 34 77 50 82C66 77 78 65 78 48V27L50 14Z" fill="url(#shield_grad_front)"/>'
    '<!-- Glossy Highlights -->'
    '<path d="M50 14L22 27V48C22 65 34 77 50 82V14Z" fill="#FFFFFF" fill-opacity="0.15"/>'
    '<!-- 3D Center Tech Core (No Checkmark) -->'
    '<circle cx="50" cy="46" r="14" fill="url(#core_grad)" stroke="#FFFFFF" stroke-width="2"/>'
    '<circle cx="50" cy="46" r="6" fill="#FFFFFF"/>'
    '<!-- Gradients -->'
    '<defs>'
    '<linearGradient id="shield_grad_back" x1="50" y1="8" x2="50" y2="90" gradientUnits="userSpaceOnUse">'
    '<stop stop-color="#0A2540"/><stop offset="1" stop-color="#1768A5"/>'
    '</linearGradient>'
    '<linearGradient id="shield_grad_front" x1="22" y1="14" x2="78" y2="82" gradientUnits="userSpaceOnUse">'
    '<stop stop-color="#35B0E6"/><stop offset="1" stop-color="#0F4F84"/>'
    '</linearGradient>'
    '<linearGradient id="core_grad" x1="36" y1="32" x2="64" y2="60" gradientUnits="userSpaceOnUse">'
    '<stop stop-color="#00F0FF"/><stop offset="1" stop-color="#0047FF"/>'
    '</linearGradient>'
    '</defs>'
    '</svg>'
)


def mini_card(icon, label, value):
    return one_line(
        f"""
        <div class="mini-card">
            {icon_badge(icon)}
            <div class="mini-text">
                <div class="mini-label">{label}</div>
                <div class="mini-value">{value}</div>
            </div>
        </div>
        """
    )


# ============================================================
# 4B. INTRO SPLASH (plays once per session, then auto-hides)
#     UI only - no backend code touched
# ============================================================

SPLASH_CSS = """
.cs-splash {
    position: fixed;
    inset: 0;
    z-index: 999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(14px, 3vh, 30px);
    background:
        radial-gradient(ellipse at 50% 38%, rgba(53, 176, 230, 0.35) 0%, rgba(53, 176, 230, 0) 55%),
        radial-gradient(ellipse at 50% 100%, rgba(31, 141, 208, 0.25) 0%, rgba(31, 141, 208, 0) 60%),
        linear-gradient(180deg, #061a2e 0%, #0b2e4d 55%, #081f36 100%);
    animation: csSplashOut 0.9s ease 4.8s forwards;
    overflow: hidden;
}

/* element container of the splash must not push the page layout */
[data-testid="stElementContainer"]:has(.cs-splash) {
    position: absolute;
    height: 0;
    margin: 0;
}

.cs-splash::before {
    content: "";
    position: absolute;
    inset: -20%;
    background:
        conic-gradient(from 0deg at 50% 50%,
            rgba(53, 176, 230, 0) 0deg,
            rgba(53, 176, 230, 0.10) 40deg,
            rgba(53, 176, 230, 0) 90deg,
            rgba(53, 176, 230, 0) 180deg,
            rgba(31, 141, 208, 0.10) 220deg,
            rgba(31, 141, 208, 0) 270deg);
    animation: csSpin 14s linear infinite;
}

.cs-splash .cs-shield {
    position: relative;
    z-index: 1;
    opacity: 0;
    animation: csShieldIn 0.9s cubic-bezier(.2, .9, .3, 1.3) 0.1s forwards;
    filter: drop-shadow(0 12px 14px rgba(0, 0, 0, 0.5))
            drop-shadow(0 0 26px rgba(53, 176, 230, 0.55));
}

.cs-splash .cs-shield svg {
    width: clamp(84px, 13vh, 130px);
    height: clamp(84px, 13vh, 130px);
}

.cs-splash .cs-word {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    perspective: 900px;
    padding: 0 4vw;
}

.cs-splash .cs-letter {
    display: inline-block;
    font-family: 'Playfair Display', 'Georgia', 'Times New Roman', serif;
    font-weight: 900;
    text-transform: uppercase;
    font-size: clamp(2.2rem, 8.2vw, 7.6rem);
    line-height: 1.05;
    letter-spacing: 0.03em;
    color: #eaf7ff;
    opacity: 0;
    transform-origin: 50% 100%;
    transform-style: preserve-3d;
    /* stacked shadows = solid 3D extrusion, then ground shadow + glow */
    text-shadow:
        0 1px 0 #bfe3fa,
        0 2px 0 #8ccaf0,
        0 3px 0 #5fb0e3,
        0 4px 0 #3a93cf,
        0 5px 0 #2579b6,
        0 6px 0 #1a629a,
        0 7px 0 #134d7c,
        0 8px 0 #0e3c62,
        0 9px 0 #0a2f4e,
        0 10px 0 #072540,
        0 18px 18px rgba(0, 0, 0, 0.55),
        0 0 36px rgba(53, 176, 230, 0.55);
    animation: csLetterIn 0.85s cubic-bezier(.2, .9, .3, 1.25) forwards;
}

.cs-splash .cs-space {
    display: inline-block;
    width: 0.38em;
    font-size: clamp(2.2rem, 8.2vw, 7.6rem);
}

.cs-splash .cs-tag {
    position: relative;
    z-index: 1;
    font-family: 'Poppins', 'Segoe UI', sans-serif;
    font-weight: 500;
    font-size: clamp(0.85rem, 1.5vw, 1.25rem);
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: #b8dcf5;
    text-shadow: 0 2px 10px rgba(53, 176, 230, 0.6);
    opacity: 0;
    animation: csFadeUp 0.9s ease 3.0s forwards;
}

.cs-splash .cs-bar {
    position: relative;
    z-index: 1;
    width: clamp(160px, 22vw, 320px);
    height: 4px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.14);
    overflow: hidden;
    opacity: 0;
    animation: csFadeUp 0.6s ease 3.2s forwards;
}

.cs-splash .cs-bar::after {
    content: "";
    position: absolute;
    inset: 0;
    width: 0;
    border-radius: 4px;
    background: linear-gradient(90deg, #35b0e6, #8fe0ff);
    box-shadow: 0 0 12px rgba(53, 176, 230, 0.9);
    animation: csBar 1.5s ease-in-out 3.2s forwards;
}

@keyframes csLetterIn {
    0%   { opacity: 0; transform: translateY(70px) rotateX(-95deg) scale(0.6); }
    55%  { opacity: 1; transform: translateY(-12px) rotateX(18deg) scale(1.06); }
    80%  { transform: translateY(3px) rotateX(-5deg) scale(0.99); }
    100% { opacity: 1; transform: translateY(0) rotateX(0deg) scale(1); }
}

@keyframes csShieldIn {
    0%   { opacity: 0; transform: scale(0.3) rotateY(-180deg); }
    100% { opacity: 1; transform: scale(1) rotateY(0deg); }
}

@keyframes csFadeUp {
    0%   { opacity: 0; transform: translateY(14px); }
    100% { opacity: 1; transform: translateY(0); }
}

@keyframes csBar {
    0%   { width: 0; }
    100% { width: 100%; }
}

@keyframes csSpin {
    to { transform: rotate(360deg); }
}

@keyframes csSplashOut {
    0%   { opacity: 1; visibility: visible; }
    100% { opacity: 0; visibility: hidden; pointer-events: none; }
}
"""

if "intro_played" not in st.session_state:
    st.session_state["intro_played"] = True

    _letters_html = ""
    _delay = 0.55

    for _ch in "CyberSathi AI":
        if _ch == " ":
            _letters_html += '<span class="cs-space"></span>'
        else:
            _letters_html += (
                f'<span class="cs-letter" '
                f'style="animation-delay:{_delay:.2f}s">{_ch}</span>'
            )
            _delay += 0.16

    st.markdown(
        "<style>" + SPLASH_CSS + "</style>"
        + one_line(
            f"""
            <div class="cs-splash">
                <div class="cs-shield">{HERO_SHIELD}</div>
                <div class="cs-word">{_letters_html}</div>
                <div class="cs-tag">Student Cyber Safety Shield</div>
                <div class="cs-bar"></div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )


# ============================================================
# 5. SIDEBAR
# ============================================================

with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2092/2092663.png",
        width=80
    )

    st.title("CyberSathi AI")
    st.write("**Protecting Students Online**")

    st.write(
        "Detect suspicious job offers, scholarship scams, "
        "phishing links, and fake payment requests."
    )

    st.divider()

    scam_type = st.selectbox(
        "🎯 Select Category to Verify:",
        [
            "🎓 Fake Internship / Job Offer",
            "💰 Scholarship Scam / Grant Fraud",
            "🏆 Fake Hackathon Request",
            "💳 Registration Fee Demand",
            "🔗 Phishing Link / Fake Portal",
            "📱 WhatsApp Impersonation"
        ]
    )

    st.info(
        "💡 **Tip:** Paste message text or upload a screenshot "
        "to analyze potential threats."
    )

    st.divider()
    st.caption("Version 1.0 | Hackathon Prototype")


# ============================================================
# 6. FIRST SCREEN  (header + info cards + input + analyze button)
#    One container that fills the laptop screen; children are
#    spaced equally, the Analyze button sits at the bottom.
# ============================================================

screen1 = keyed_container("screen1")

with screen1:

    # ---------- HEADER ----------
    st.markdown(
        one_line(
            f"""
            <div class="fancy-title">
                {HERO_SHIELD}
                <div class="hero-text">
                    <span class="fancy-text">CyberSathi AI</span>
                    <div class="hero-sub">
                        AI-Powered Shield Against Student Cyber Scams,
                        Fake Internships &amp; Online Fraud
                    </div>
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True
    )

    st.divider()

    # ---------- THREE INFO CARDS ----------
    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown(
            mini_card("shield-check", "Shield Status", "Active Cyber Guard"),
            unsafe_allow_html=True
        )

    with m2:
        st.markdown(
            mini_card("image", "Supported Formats", "Text + Screenshot"),
            unsafe_allow_html=True
        )

    with m3:
        st.markdown(
            mini_card("cpu", "Detection Engine", "Hinglish / English NLP"),
            unsafe_allow_html=True
        )

    st.divider()

    # ---------- INPUT SECTION ----------
    input_panel = keyed_container("input_panel")

    with input_panel:
        st.markdown(
            one_line(
                f"""
                <div class="fancy-title section-size">
                    {icon_badge("scan-search", "sec")}
                    <span class="fancy-text">Analyze Suspicious Content</span>
                </div>
                """
            ),
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2, vertical_alignment="top")

        with col1:
            st.markdown(
                one_line(
                    f"""
                    <div class="input-heading">
                        {icon_badge("message", "sm")}
                        <span>Paste Message / Email Text</span>
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="input-desc">'
                'Enter suspicious SMS, Email, or WhatsApp text:'
                '</div>',
                unsafe_allow_html=True
            )

            user_text = st.text_area(
                "Enter suspicious SMS, Email, or WhatsApp text:",
                height=170,
                label_visibility="collapsed",
                placeholder=(
                    "Example: Congratulations! You have been selected "
                    "for a remote internship. Pay a registration fee "
                    "immediately to confirm your slot."
                )
            )

        with col2:
            st.markdown(
                one_line(
                    f"""
                    <div class="input-heading">
                        {icon_badge("upload", "sm")}
                        <span>Upload Screenshot / Document</span>
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="input-desc">'
                'Upload a screenshot of an offer letter, chat, or email.'
                '</div>',
                unsafe_allow_html=True
            )

            uploaded_file = st.file_uploader(
                "Upload screenshot",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )

            if uploaded_file is not None:
                # getvalue() always returns the full bytes, so the
                # preview never breaks after the file has been read.
                preview_html = make_preview_html(uploaded_file)

                if preview_html:
                    st.markdown(preview_html, unsafe_allow_html=True)
                else:
                    st.image(
                        uploaded_file.getvalue(),
                        caption="Preview of Uploaded Screenshot",
                        width=200
                    )

    # ---------- ANALYZE BUTTON ----------
    action_zone = keyed_container("action_zone")

    with action_zone:
        analyze_button = st.button(
            "🔍 Analyze Threat Level",
            type="primary",
            use_container_width=True
        )

        # Message such as "please enter text" appears right under the button.
        notice_slot = st.empty()


# ============================================================
# 7. THREAT ANALYSIS REPORT  (starts on its own new screen)
# ============================================================

if analyze_button:
    if not user_text.strip() and uploaded_file is None:
        notice_slot.warning(
            "Please enter a message or upload a screenshot first."
        )

    else:
        with keyed_container("report_screen"):

            st.markdown(
                "<div id='output-scroll-anchor'></div>",
                unsafe_allow_html=True
            )

            st.markdown(
                one_line(
                    f"""
                    <div class="fancy-title report-size">
                        {icon_badge("chart", "lg")}
                        <span class="fancy-text">CyberSathi Threat Intelligence Report</span>
                    </div>
                    """
                ),
                unsafe_allow_html=True
            )

            try:
                # Prefer manually pasted text when both inputs are provided.
                message = user_text.strip()
                used_ocr = False

                if not message and uploaded_file is not None:
                    used_ocr = True

                    with st.spinner("Reading screenshot text with OCR..."):
                        message = extract_screenshot_text(uploaded_file)

                    if not message.strip():
                        st.warning(
                            "Readable text could not be extracted. "
                            "Try a clearer screenshot or paste the message manually."
                        )

                if message.strip():
                    # Core detector call.
                    with st.spinner(
                        "Analyzing message patterns, URLs, and available AI insights..."
                    ):
                        report = calculate_risk(message)

                        # Adapt the unchanged detector.py output to this app's report fields.
                        # The detector's scoring rules and implementation remain untouched.
                        report["score"] = report.get("risk_score", 0)
                        report["level"] = report.get("risk_level", "Low")
                        report["evidence"] = report.get("warning_signs", [])
                        report["reasons"] = report.get("warnings", [])
                        report["recommendations"] = (
                            [report["recommendation"]]
                            if report.get("recommendation") else []
                        )
                        report["verdict"] = report.get("risk_level", "Unknown")
                        report["context_signs"] = []

                        # Optional AI analysis call.
                        ai_report = {}

                        if analyze_message is not None:
                            try:
                                ai_result = analyze_message(message)

                                if isinstance(ai_result, dict):
                                    ai_report = ai_result
                                else:
                                    st.info(
                                        "AI analysis returned an unexpected format. "
                                        "The core detector results are still shown."
                                    )
                            except Exception:
                                st.warning(
                                    "AI analysis is currently unavailable. "
                                    "Showing the core detector results instead."
                                )

                    if not isinstance(report, dict):
                        raise ValueError(
                            "calculate_risk() must return a dictionary."
                        )

                    # ------------------------------------------------
                    # NORMALIZE RESULTS
                    # ------------------------------------------------

                    try:
                        score_val = round(float(report.get("score", 0)))
                        score_val = max(0, min(100, score_val))
                    except (TypeError, ValueError):
                        score_val = 0

                    level_val = as_text(
                        report.get("level", "Low"), "Low"
                    ).upper()

                    if level_val not in ("HIGH", "MEDIUM", "LOW"):
                        level_val = "LOW"

                    fallback_category = (
                        scam_type.split(" ", 1)[1]
                        if " " in scam_type else scam_type
                    )

                    detected_category = as_text(
                        report.get("category")
                        or ai_report.get("category")
                        or fallback_category,
                        fallback_category
                    )

                    warnings = unique_text_items(
                        report.get("evidence", []),
                        report.get("reasons", []),
                        ai_report.get("warning_signs", [])
                    )

                    recommendations = unique_text_items(
                        ai_report.get("recommendations", []),
                        report.get("recommendations", [])
                    )

                    # Build a useful explanation even when the optional AI
                    # analyzer does not return one. This does not change detector.py.
                    fallback_explanation = (
                        "The analysis found these warning indicators: "
                        + "; ".join(warnings[:4])
                        + ". Treat them as reasons to verify the sender and offer independently, "
                        "not as definitive proof of fraud."
                        if warnings
                        else
                        "The available checks did not find obvious scam indicators. "
                        "This does not guarantee the message is genuine; verify unexpected "
                        "offers and requests through official contact details."
                    )

                    explanation = as_text(
                        ai_report.get("explanation"),
                        fallback_explanation
                    )
                    if explanation.lower().strip() in {
                        "no additional detector explanation was returned.",
                        "not identified",
                        "none"
                    }:
                        explanation = fallback_explanation

                    context_signs = unique_text_items(
                        report.get("context_signs", [])
                    )

                    # ------------------------------------------------
                    # KEY RESULT METRICS
                    # ------------------------------------------------

                    res_col1, res_col2, res_col3 = st.columns(3)

                    with res_col1:
                        st.metric(
                            label="Risk Level",
                            value=f"{level_val} RISK"
                        )

                        # Colour-coded Risk Level card (UI only)
                        # Theme-matched: deep crimson = high, amber = medium, teal-green = low
                        risk_tint, risk_accent, risk_edge, risk_base = {
                            "HIGH": (
                                "linear-gradient(135deg, #6f1024, #b32d44)",
                                "#ff9fb0", "#8c1c34", "#3f0714"
                            ),
                            "MEDIUM": (
                                "linear-gradient(135deg, #6e3a05, #b9690f)",
                                "#ffd08a", "#85490a", "#3d2002"
                            ),
                            "LOW": (
                                "linear-gradient(135deg, #0a5446, #168f73)",
                                "#8ee6cc", "#0c6b58", "#042d25"
                            ),
                        }[level_val]

                        st.markdown(
                            f"""
                            <style>
                            {METRIC_ROW}:first-child [data-testid="stMetric"] {{
                                background: var(--gloss), {risk_tint} !important;
                                border-color: {risk_edge} !important;
                                border-left-color: {risk_accent} !important;
                                border-bottom-color: {risk_base} !important;
                            }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                    with res_col2:
                        st.metric(
                            label="Risk Score (Heuristic)",
                            value=f"{score_val}/100"
                        )

                    with res_col3:
                        st.metric(
                            label="Threat Category",
                            value=detected_category
                        )

                    st.caption(
                        "The risk score is based on detected indicators; "
                        "it is not a calibrated probability of fraud."
                    )

                    # ------------------------------------------------
                    # RISK STATUS
                    # ------------------------------------------------

                    if level_val == "HIGH":
                        st.error(
                            "**High Risk Detected:** Multiple suspicious "
                            "indicators were found. Do not pay, click links, "
                            "or share sensitive information until independently verified."
                        )

                    elif level_val == "MEDIUM":
                        st.warning(
                            "**Medium Risk Detected:** Some suspicious "
                            "indicators were found. Verify the sender and "
                            "organization through official channels."
                        )

                    else:
                        st.success(
                            "**Low Risk Detected:** Few common warning "
                            "indicators were found. This does not guarantee "
                            "that the message or website is genuine."
                        )

                    # ------------------------------------------------
                    # ASSESSMENT DETAILS
                    # ------------------------------------------------

                    verdict = as_text(
                        report.get("verdict"),
                        "Assessment unavailable"
                    )

                    detector_explanation = as_text(
                        report.get("explanation"),
                        (
                            "The detector flagged these indicators: "
                            + "; ".join(warnings[:4])
                            + ". Verify the sender and claims independently."
                            if warnings
                            else
                            "No obvious warning indicators were returned by the local rules. "
                            "This is not proof that the message is safe."
                        )
                    )
                    if detector_explanation.lower().strip() == (
                        "no additional detector explanation was returned."
                    ):
                        detector_explanation = (
                            "The detector flagged these indicators: "
                            + "; ".join(warnings[:4])
                            + ". Verify the sender and claims independently."
                            if warnings
                            else
                            "No obvious warning indicators were returned by the local rules. "
                            "This is not proof that the message is safe."
                        )

                    assessment_html = (
                        f'<p><strong>Detector verdict:</strong> '
                        f'{safe_html(verdict)}</p>'
                        f'<p>{safe_html(detector_explanation)}</p>'
                    )

                    explanation_html = (
                        '<div class="detail-label">Analysis Explanation</div>'
                        f'<div class="detail-value">{safe_html(explanation)}</div>'
                    )

                    # ------------------------------------------------
                    # WARNING SIGNS AND RECOMMENDATIONS
                    # ------------------------------------------------

                    warning_content = make_list_html(warnings)

                    if not warnings:
                        warning_content = (
                            "<p>No specific warning signs were returned by "
                            "the available checks. This does not prove the "
                            "message is safe.</p>"
                        )

                    if recommendations:
                        recommendation_content = make_list_html(
                            recommendations,
                            ordered=True
                        )
                    else:
                        recommendation_content = """
                        <ol>
                            <li>Verify the sender using independently obtained official contact details.</li>
                            <li>Do not pay unexpected fees or share OTPs, passwords, UPI PINs, or banking details.</li>
                            <li>Open official websites yourself instead of trusting links in unsolicited messages.</li>
                            <li>Keep suspicious messages and transaction details if you need to report a suspected scam.</li>
                        </ol>
                        """

                    # All four main blocks in one 2x2 grid (equal size, clear gaps)
                    render_card_grid([
                        ("🛡️ Detector Assessment", assessment_html),
                        ("🤖 AI Message Analysis", explanation_html),
                        ("🔍 Warning Signs Detected", warning_content),
                        ("💡 Recommended Action Steps", recommendation_content),
                    ])

                    if context_signs:
                        render_report_card(
                            "🧾 Context Checks",
                            make_list_html(context_signs)
                        )

                    # ------------------------------------------------
                    # URL CHECK RESULTS (title now inside the card)
                    # ------------------------------------------------

                    urls = extract_urls(message, report)

                    if urls:
                        url_items = "".join(
                            f'<li class="report-url"><code>{safe_html(url)}</code></li>'
                            for url in urls
                        )

                        render_report_card(
                            "🔗 URLs Found in the Message",
                            f"<ul>{url_items}</ul>"
                        )

                    else:
                        render_report_card(
                            "🔗 URLs Found in the Message",
                            "<p>No URLs were detected in the analyzed text.</p>"
                        )

                    # ------------------------------------------------
                    # NOTES + REPORTING LINK (one clearly visible card)
                    # ------------------------------------------------

                    footer_notes = []

                    if urls:
                        footer_notes.append(
                            "Finding a URL does not automatically mean it is malicious. "
                            "A low score does not prove that a website is safe."
                        )

                    if used_ocr:
                        footer_notes.append(
                            "This report was generated from text extracted from "
                            "your screenshot. OCR can make mistakes, so verify "
                            "the extracted text when possible."
                        )

                    footer_notes.append(
                        "CyberSathi AI is a hackathon prototype. Its heuristic "
                        "and AI outputs may be incomplete or incorrect. "
                        "Verify important claims independently."
                    )

                    footer_html = "".join(
                        f'<p class="footer-note">{safe_html(note)}</p>'
                        for note in footer_notes
                    ) + (
                        '<p class="footer-note"><strong>If you suspect cybercrime, '
                        'visit the official </strong>'
                        '<a href="https://cybercrime.gov.in/" target="_blank" '
                        'rel="noopener noreferrer">'
                        'National Cyber Crime Reporting Portal</a>.</p>'
                    )

                    render_report_card("", footer_html)

                else:
                    st.warning(
                        "No readable text was available for analysis. "
                        "Please paste the message and try again."
                    )

            except Exception as error:
                st.error(
                    "The report could not be completed. Check that detector.py, "
                    "ai_analyzer.py, screenshot.py, and their dependencies are "
                    "configured correctly."
                )
                st.exception(error)

            # --------------------------------------------------------
            # AUTO-SCROLL TO REPORT
            # --------------------------------------------------------

            scroll_js = """
                <script>
                // run id: __NONCE__
                (function () {
                    var tries = 0;
                    function scrollToReport() {
                        tries += 1;
                        try {
                            var d = window.parent.document;
                            var anchor = d.getElementById("output-scroll-anchor")
                                || d.querySelector('[class*="st-key-report_screen"]');
                            if (anchor) {
                                anchor.scrollIntoView({behavior: "smooth", block: "start"});
                            }
                        } catch (error) {}
                        if (tries < 4) { setTimeout(scrollToReport, 600); }
                    }
                    setTimeout(scrollToReport, 250);
                })();
                </script>
            """.replace("__NONCE__", str(time.time()))

            components.html(scroll_js, height=0, scrolling=False)
