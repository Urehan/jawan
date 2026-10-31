import io
import time
import wave
import numpy as np
import streamlit as st
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS
from faster_whisper import WhisperModel

st.set_page_config(
    page_title="Urdu ⇄ Malay Translator",
    page_icon="🌍",
    layout="centered",
)

# ---------- Glassmorphism + 3D styling ----------
st.markdown(
    """
    <style>
    /* Background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 45%, #0e7490 100%);
        background-attachment: fixed;
    }

    /* Floating glow orbs (3D depth ka effect) */
    .bg-orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(70px);
        opacity: 0.55;
        z-index: 0;
        pointer-events: none;
        animation: float 14s ease-in-out infinite;
    }
    .orb1 { width: 420px; height: 420px; background: #7c3aed; top: -120px; left: -100px; }
    .orb2 { width: 380px; height: 380px; background: #06b6d4; bottom: -120px; right: -80px; animation-delay: -5s; }
    .orb3 { width: 260px; height: 260px; background: #ec4899; top: 40%; left: 60%; animation-delay: -9s; }

    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(40px, -50px) scale(1.12); }
    }

    /* Glass cards with 3D tilt on hover */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(18px) saturate(160%);
        -webkit-backdrop-filter: blur(18px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25);
        transform-style: preserve-3d;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
        position: relative;
        z-index: 1;
        margin-bottom: 1rem;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: perspective(900px) rotateX(3deg) rotateY(-3deg) translateY(-4px);
        box-shadow: 0 22px 50px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }

    /* Text colors dark background ke liye */
    .stApp, .stApp label, .stApp p, .stApp span {
        color: #f1f5f9;
    }

    /* Header */
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #c4b5fd, #67e8f9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #cbd5e1 !important;
        margin-bottom: 1.5rem;
    }

    .section-label {
        font-weight: 600;
        margin-bottom: 0.4rem;
        color: #e2e8f0 !important;
    }

    /* Inputs: glass look */
    textarea, [data-baseweb="select"] > div {
        background: rgba(15, 23, 42, 0.45) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
    }
    textarea:focus {
        border-color: #67e8f9 !important;
        box-shadow: 0 0 0 2px rgba(103, 232, 249, 0.3) !important;
    }

    /* Buttons: gradient + lift */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #06b6d4) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.45);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 10px 28px rgba(6, 182, 212, 0.45);
    }

    /* Translation output: glass box */
    .output-box {
        padding: 1rem 1.25rem;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        font-size: 1.25rem;
        line-height: 1.9;
        min-height: 80px;
        color: #ffffff !important;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
    }
    .output-rtl {
        direction: rtl;
        text-align: right;
        font-family: "Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", serif;
    }
    </style>

    <div class="bg-orb orb1"></div>
    <div class="bg-orb orb2"></div>
    <div class="bg-orb orb3"></div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🌍 Urdu ⇄ Malay Translator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Likhein ya bol kar translate karein, aur awaz bhi sunein</div>',
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def is_rate_limit(error):
    return "too many requests" in str(error).lower()


def retry_on_rate_limit(func, *args, **kwargs):
    # Rate limit par 2s, 4s wait karke dobara try karein
    last_error = None
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if is_rate_limit(e) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
            elif is_rate_limit(e):
                break
            else:
                raise
    raise last_error


@st.cache_data
def get_languages():
    # {'urdu': 'ur', 'malay': 'ms', ...}
    return GoogleTranslator().get_supported_languages(as_dict=True)


@st.cache_resource
def load_whisper():
    # "medium" Urdu ke liye behtar hai. CPU par slow ho to "small" par wapas jayein.
    return WhisperModel("medium", device="cpu", compute_type="int8")


def wav_to_16k_mono(audio_bytes):
    # Streamlit ka audio WAV hota hai. Ise numpy array mein badal dete hain.
    with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
        channels = wf.getnchannels()
        rate = wf.getframerate()
        width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if width == 1:
        data = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128) / 128.0
    elif width == 2:
        data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif width == 4:
        data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError("Ye audio format support nahi hai.")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    if rate != 16000:
        new_len = int(len(data) * 16000 / rate)
        data = np.interp(
            np.linspace(0, len(data) - 1, new_len),
            np.arange(len(data)),
            data,
        )

    # Awaz ko normalize karein, taake dheemi awaz bhi saaf sunai de
    peak = np.max(np.abs(data)) if data.size else 0
    if peak > 0:
        data = data / peak * 0.95

    return data.astype(np.float32)


# Whisper ko language ka context dene wale prompts
INITIAL_PROMPTS = {
    "ur": "یہ اردو زبان میں گفتگو ہے۔",
    "ms": "Ini ialah perbualan dalam Bahasa Melayu.",
}


@st.cache_data(show_spinner=False)
def transcribe(audio_bytes, lang_code):
    model = load_whisper()
    audio_array = wav_to_16k_mono(audio_bytes)
    segments, _ = model.transcribe(
        audio_array,
        language=lang_code,
        beam_size=5,
        initial_prompt=INITIAL_PROMPTS.get(lang_code),
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,
    )
    return " ".join(seg.text.strip() for seg in segments)


@st.cache_data(show_spinner=False)
def cached_translate(text, src_code, tgt_code, src_name, tgt_name):
    # Pehle Google, rate limit par MyMemory (jo language ka naam leta hai)
    try:
        return retry_on_rate_limit(
            lambda: GoogleTranslator(source=src_code, target=tgt_code).translate(text)
        )
    except Exception as e:
        if not is_rate_limit(e):
            raise
    return MyMemoryTranslator(source=src_name, target=tgt_name).translate(text)


@st.cache_data(show_spinner=False)
def make_speech(text_to_say, lang_code):
    def _generate():
        buf = io.BytesIO()
        gTTS(text=text_to_say, lang=lang_code).write_to_fp(buf)
        return buf.getvalue()

    return retry_on_rate_limit(_generate)


# ---------- Session state ----------
languages = get_languages()
names = sorted(languages.keys())

if "src" not in st.session_state:
    st.session_state.src = "urdu"
if "tgt" not in st.session_state:
    st.session_state.tgt = "malay"
if "text" not in st.session_state:
    st.session_state.text = ""


def swap_languages():
    st.session_state.src, st.session_state.tgt = st.session_state.tgt, st.session_state.src


# ---------- Language selector ----------
with st.container(border=True):
    col1, col2, col3 = st.columns([5, 1, 5], vertical_alignment="bottom")
    with col1:
        src = st.selectbox("Source language", names, key="src")
    with col2:
        st.button("⇄", on_click=swap_languages, help="Languages ulta karein", use_container_width=True)
    with col3:
        tgt = st.selectbox("Target language", names, key="tgt")

# ---------- Input card ----------
with st.container(border=True):
    st.markdown('<div class="section-label">🎤 Bol kar likhein</div>', unsafe_allow_html=True)
    audio = st.audio_input("Mic dabayein aur bolein", label_visibility="collapsed")

    if audio is not None and st.button("Audio ko text banayein"):
        with st.spinner("Sun raha hoon..."):
            try:
                st.session_state.text = transcribe(audio.getvalue(), languages[src])
            except Exception as e:
                st.error(f"Audio samajh nahi aaya: {e}")

    st.markdown('<div class="section-label">✍️ Ya likhein</div>', unsafe_allow_html=True)
    text = st.text_area(
        "Text",
        key="text",
        height=150,
        placeholder="Yahan text likhein...",
        label_visibility="collapsed",
    )

    want_audio = st.checkbox("Translation ki awaz bhi sunein")

    translate_clicked = st.button("Translate", type="primary", use_container_width=True)

# ---------- Translation ----------
if translate_clicked:
    if not text.strip():
        st.error("Pehle kuch text likhein.")
    elif src == tgt:
        st.warning("Source aur target language aik jaisi nahi honi chahiye.")
    else:
        try:
            with st.spinner("Translate ho raha hai..."):
                result = cached_translate(
                    text, languages[src], languages[tgt], src, tgt
                )

            with st.container(border=True):
                st.markdown('<div class="section-label">✅ Translation</div>', unsafe_allow_html=True)
                rtl_class = "output-rtl" if tgt == "urdu" else ""
                st.markdown(
                    f'<div class="output-box {rtl_class}">{result}</div>',
                    unsafe_allow_html=True,
                )

                if want_audio:
                    try:
                        with st.spinner("Awaz bana raha hoon..."):
                            audio_bytes = make_speech(result, languages[tgt])
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.warning(f"Awaz banane mein masla aaya: {e}")

        except Exception as e:
            if is_rate_limit(e):
                st.error("Dono translation services abhi busy hain. Thodi der baad dobara try karein.")
            else:
                st.error(f"Translation mein masla aaya: {e}")
