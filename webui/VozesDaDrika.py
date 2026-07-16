from __future__ import annotations

import hashlib
import os
import sys
import re
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.services import fish_audio
from app.services.fish_voice_catalog import FISH_VOICE_GROUPS


APP_NAME = "Vozes da Drika"
OUTPUT_DIR = Path("storage") / "vozes_da_drika"
PREVIEW_DIR = OUTPUT_DIR / "previews"


def get_secret_value(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass

    return os.environ.get(name, default)


def require_password() -> bool:
    expected_password = (
        get_secret_value("VOICE_STUDIO_PASSWORD", "")
        or get_secret_value("VOICE_LAB_PASSWORD", "")
    )

    if not expected_password:
        st.warning("Senha do app não configurada. Configure VOICE_STUDIO_PASSWORD nos Secrets do Streamlit.")
        return True

    if st.session_state.get("drika_authenticated") is True:
        return True

    st.markdown(
        """
        <div class="drika-hero">
            <div class="drika-title">🎙️ Vozes da Drika</div>
            <div class="drika-subtitle">Acesso privado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("drika_login_form"):
        password = st.text_input(
            "Senha de acesso",
            type="password",
            placeholder="Digite a senha",
        )

        submitted = st.form_submit_button("Entrar", type="primary")

    if submitted:
        if password == expected_password:
            st.session_state["drika_authenticated"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    return False


def clean_fish_emotion_tags(text: str) -> str:
    clean_text = (text or "").strip()
    return re.sub(r"^(\s*\[[^\]]{1,40}\]\s*)+", "", clean_text).strip()


def apply_fish_style(text: str, selected_prefix: str) -> str:
    clean_text = clean_fish_emotion_tags(text)

    if not selected_prefix:
        return clean_text

    return f"{selected_prefix.strip()} {clean_text}".strip()


def build_output_file(prefix: str, extension: str = "mp3") -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.{extension}"
    return str(OUTPUT_DIR / filename)


def render_audio_result(session_key: str, download_label: str) -> None:
    audio_file = st.session_state.get(session_key)

    if not audio_file:
        return

    if not os.path.isfile(audio_file):
        st.warning("O arquivo de áudio não foi encontrado.")
        return

    with open(audio_file, "rb") as fp:
        audio_bytes = fp.read()

    st.audio(audio_bytes, format="audio/mp3")

    st.download_button(
        download_label,
        data=audio_bytes,
        file_name=os.path.basename(audio_file),
        mime="audio/mpeg",
        use_container_width=True,
    )


def get_preview_file(reference_id: str, text: str) -> str:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    preview_hash_source = f"{reference_id}|{text}"
    preview_hash = hashlib.sha1(preview_hash_source.encode("utf-8")).hexdigest()[:16]
    return str(PREVIEW_DIR / f"preview_{preview_hash}.mp3")


def sorted_labels(values: list[str]) -> list[str]:
    return sorted(values, key=lambda value: value.lower())


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎙️",
    layout="centered",
)

st.markdown(
    """
    <style>
    :root {
        --drika-bg: #fff8fc;
        --drika-surface: #ffffff;
        --drika-surface-soft: #fff1f7;
        --drika-border: #f6b6d4;
        --drika-pink: #ec4899;
        --drika-pink-dark: #db2777;
        --drika-pink-deep: #9d174d;
        --drika-text: #241321;
        --drika-muted: #765466;
        --drika-input: #ffffff;
        --drika-placeholder: #a97990;
    }

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 12% 0%, rgba(236, 72, 153, 0.12), transparent 28rem),
            linear-gradient(180deg, #fff8fc 0%, #ffffff 42%, #ffffff 100%) !important;
        color: var(--drika-text) !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 860px;
        padding-top: 2.2rem;
        padding-bottom: 4rem;
    }

    .drika-hero {
        padding: 1.65rem 1.55rem;
        border-radius: 26px;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(255, 241, 247, 0.96));
        border: 1px solid var(--drika-border);
        box-shadow: 0 18px 42px rgba(157, 23, 77, 0.10);
        margin-bottom: 1.25rem;
    }

    .drika-title {
        font-size: 2.15rem;
        font-weight: 850;
        line-height: 1.05;
        margin-bottom: 0.55rem;
        color: var(--drika-pink-deep);
        letter-spacing: -0.035em;
    }

    .drika-subtitle {
        color: var(--drika-muted);
        font-size: 1.02rem;
        line-height: 1.55;
    }

    h1, h2, h3 {
        color: var(--drika-text) !important;
        letter-spacing: -0.02em;
        font-weight: 800 !important;
    }

    label,
    p,
    span,
    div,
    small {
        color: var(--drika-text);
    }

    [data-testid="stCaptionContainer"],
    [data-testid="stMarkdownContainer"] small {
        color: var(--drika-muted) !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    input,
    textarea {
        background: var(--drika-input) !important;
        color: var(--drika-text) !important;
        -webkit-text-fill-color: var(--drika-text) !important;
        border: 1px solid var(--drika-border) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        caret-color: var(--drika-pink-dark) !important;
    }

    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder,
    input::placeholder,
    textarea::placeholder {
        color: var(--drika-placeholder) !important;
        -webkit-text-fill-color: var(--drika-placeholder) !important;
        opacity: 1 !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    input:focus,
    textarea:focus {
        border-color: var(--drika-pink) !important;
        box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.16) !important;
        outline: none !important;
    }

    div[data-baseweb="select"] > div {
        background: var(--drika-input) !important;
        color: var(--drika-text) !important;
        border: 1px solid var(--drika-border) !important;
        border-radius: 16px !important;
        box-shadow: none !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {
        color: var(--drika-text) !important;
        -webkit-text-fill-color: var(--drika-text) !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"] {
        background: #ffffff !important;
        color: var(--drika-text) !important;
        border-radius: 16px !important;
    }

    li[role="option"],
    li[role="option"] div,
    li[role="option"] span {
        color: var(--drika-text) !important;
        background: #ffffff !important;
    }

    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background: var(--drika-surface-soft) !important;
    }

    div[data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 16px !important;
        border-color: rgba(236, 72, 153, 0.20) !important;
        color: var(--drika-text) !important;
    }

    div.stButton > button,
    div.stFormSubmitButton > button,
    div.stDownloadButton > button {
        background: linear-gradient(135deg, var(--drika-pink), var(--drika-pink-dark)) !important;
        color: #ffffff !important;
        border: 1px solid transparent !important;
        border-radius: 999px !important;
        min-height: 3rem !important;
        font-weight: 800 !important;
        box-shadow: 0 12px 26px rgba(219, 39, 119, 0.22) !important;
    }

    div.stButton > button *,
    div.stFormSubmitButton > button *,
    div.stDownloadButton > button * {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover,
    div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, var(--drika-pink-dark), var(--drika-pink-deep)) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        transform: translateY(-1px);
    }

    div[data-testid="stExpander"] {
        background: transparent !important;
        border: 1px solid rgba(246, 182, 212, 0.42) !important;
        border-radius: 14px !important;
        box-shadow: none !important;
    }

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary * {
        color: var(--drika-text) !important;
        font-weight: 600 !important;
    }

    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] span,
    div[data-testid="stCheckbox"] p {
        color: var(--drika-text) !important;
    }

    audio {
        width: 100%;
        border-radius: 999px;
        margin-top: 0.5rem;
    }

    hr {
        border-color: rgba(246, 182, 212, 0.35);
    }

    .drika-footer {
        text-align: center;
        color: var(--drika-muted);
        font-size: 0.86rem;
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not require_password():
    st.stop()

fish_api_key = get_secret_value("FISH_AUDIO_API_KEY", "")

st.markdown(
    """
    <div class="drika-hero">
        <div class="drika-title">🎙️ Vozes da Drika</div>
        <div class="drika-subtitle">
            Drika, fiz este cantinho para você criar vozes, campanhas e ideias com mais facilidade.<br>
            Um presente simples, feito com carinho, para transformar seus textos em áudio sempre que quiser.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not fish_api_key:
    st.error("A chave FISH_AUDIO_API_KEY não está configurada nos Secrets do app.")
    st.stop()

preferred_order = [
    "Feminino",
    "Masculino",
    "Personagem / Real / Experimental",
    "Neutro / Outros",
]

available_categories = [
    category for category in preferred_order
    if category in FISH_VOICE_GROUPS and FISH_VOICE_GROUPS[category]
]

if not available_categories:
    st.error("Catálogo de vozes vazio.")
    st.stop()

st.markdown("### 1. Escolha a voz")

voice_category = st.selectbox(
    "Tipo de voz",
    options=available_categories,
    index=0,
)

voice_options = FISH_VOICE_GROUPS.get(voice_category, {})
voice_labels = sorted_labels(list(voice_options.keys()))

selected_voice_label = st.selectbox(
    "Voz",
    options=voice_labels,
    index=0,
)

selected_reference_id = voice_options[selected_voice_label]

if voice_category == "Personagem / Real / Experimental":
    st.info("Essa categoria é melhor para testes. Para campanhas comerciais, prefira vozes femininas, masculinas, narradoras ou locutores genéricos.")

style_options = {
    "Natural": "",
    "Energia de campanha": "[excited] ",
    "Comercial calorosa": "[warmly] ",
    "TikTok energético": "[excited] [fast] ",
    "Narração emocional": "[softly] ",
    "Review sincero": "[naturally] ",
    "Sussurrado": "[whispering] ",
    "Dramático": "[dramatic] ",
}

voice_style = st.selectbox(
    "Estilo de leitura",
    options=list(style_options.keys()),
    index=0,
)

custom_prefix = st.text_input(
    "Ajuste opcional de emoção",
    value="",
    placeholder="Ex: [excited] [laughing]",
)

selected_prefix = custom_prefix.strip() or style_options[voice_style]

st.markdown("### 2. Ouça uma prévia")

preview_text = st.text_area(
    "Texto curto para testar a voz",
    value=(
        "Oi, Drika! Este é um teste rápido da sua nova voz de campanha. "
        "Escolha a voz, ouça a prévia e transforme suas ideias em áudio com facilidade."
    ),
    height=120,
)

final_preview_text = apply_fish_style(preview_text, selected_prefix)
preview_file = get_preview_file(selected_reference_id, final_preview_text)

col_preview_1, col_preview_2 = st.columns([1, 1])

with col_preview_1:
    force_preview = st.checkbox("Recriar prévia", value=False)

with col_preview_2:
    preview_cached = os.path.isfile(preview_file)
    if preview_cached:
        st.caption("Prévia já salva para essa voz.")

with st.expander("Ver texto enviado na prévia"):
    st.code(final_preview_text or "", language="text")

if st.button("▶️ Ouvir prévia da voz", use_container_width=True):
    if not final_preview_text:
        st.error("Digite um texto de prévia.")
    else:
        try:
            if os.path.isfile(preview_file) and not force_preview:
                st.session_state["drika_preview_file"] = preview_file
                st.success("Prévia carregada.")
            else:
                with st.spinner("Gerando prévia..."):
                    fish_audio.tts(
                        api_key=fish_api_key,
                        text=final_preview_text,
                        reference_id=selected_reference_id,
                        output_file=preview_file,
                    )

                st.session_state["drika_preview_file"] = preview_file
                st.success("Prévia gerada com sucesso.")
        except Exception as error:
            st.error(f"Falha ao gerar prévia: {error}")

render_audio_result("drika_preview_file", "Baixar prévia MP3")

st.markdown("### 3. Gere o áudio final")

campaign_text = st.text_area(
    "Texto final do áudio",
    value=(
        "Oi, Drika! Este app foi feito para você criar áudios, testar vozes e dar vida às suas ideias. "
        "Que ele ajude nas suas campanhas, nos seus projetos e em tudo que você quiser comunicar com carinho e criatividade."
    ),
    height=190,
)

final_campaign_text = apply_fish_style(campaign_text, selected_prefix)

with st.expander("Ver texto enviado no áudio final"):
    st.code(final_campaign_text or "", language="text")

if st.button("🎧 Gerar áudio final", type="primary", use_container_width=True):
    if not final_campaign_text:
        st.error("Digite o texto final antes de gerar.")
    else:
        try:
            output_file = build_output_file("vozes_da_drika", "mp3")

            with st.spinner("Gerando áudio final..."):
                fish_audio.tts(
                    api_key=fish_api_key,
                    text=final_campaign_text,
                    reference_id=selected_reference_id,
                    output_file=output_file,
                )

            st.session_state["drika_final_file"] = output_file
            st.success("Áudio final gerado com sucesso.")
        except Exception as error:
            st.error(f"Falha ao gerar áudio final: {error}")

render_audio_result("drika_final_file", "Baixar áudio final MP3")

st.markdown('<div class="drika-footer">Vozes da Drika · feito com carinho</div>', unsafe_allow_html=True)
