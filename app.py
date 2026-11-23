import os
import re
import json
import base64
import html
from io import BytesIO
from urllib.parse import quote_plus, quote
from difflib import SequenceMatcher

import requests
import streamlit as st
from PIL import Image
from openai import OpenAI

st.set_page_config(page_title="Trouve ton sosie", page_icon="📸", layout="wide", initial_sidebar_state="collapsed")

MASCOT = """
<svg viewBox="0 0 280 320" role="img" aria-label="Monsieur Flash, photographe du studio">
  <ellipse cx="145" cy="298" rx="88" ry="12" fill="#2b171a" opacity=".14"/>
  <path d="M82 276 Q89 222 118 205 L181 205 Q205 229 215 280 L194 290 L93 290 Z" fill="#bd6948" stroke="#392126" stroke-width="6" stroke-linejoin="round"/>
  <path d="M117 208 Q138 237 172 213 L190 244 Q160 270 117 240 Z" fill="#6d2434" stroke="#392126" stroke-width="5"/>
  <path d="M123 210 L112 276 L92 282 Q95 248 99 228 Z" fill="#e8c69a" stroke="#392126" stroke-width="5"/>
  <path d="M181 211 Q207 231 222 263 L205 278 Q187 252 169 237 Z" fill="#e8c69a" stroke="#392126" stroke-width="5"/>
  <path d="M88 281 Q72 295 48 286 Q39 279 51 272 L92 267 Z" fill="#e8c69a" stroke="#392126" stroke-width="5"/>
  <path d="M203 275 Q225 288 245 276 Q253 270 242 264 L210 260 Z" fill="#e8c69a" stroke="#392126" stroke-width="5"/>
  <path d="M114 118 Q104 83 130 62 Q163 42 193 72 Q212 93 201 151 Q195 190 166 204 Q129 202 112 172 Z" fill="#efc99d" stroke="#392126" stroke-width="6" stroke-linejoin="round"/>
  <path d="M111 111 Q91 75 119 49 Q151 20 190 48 Q207 61 205 91 Q179 75 162 89 Q135 108 111 111 Z" fill="#332126" stroke="#392126" stroke-width="6" stroke-linejoin="round"/>
  <path d="M117 62 Q150 28 187 52 Q194 58 195 70 Q158 55 123 85 Z" fill="#6d2434"/>
  <path d="M105 49 Q121 13 173 19 Q211 22 220 48 Q180 38 150 56 Q120 68 105 49 Z" fill="#7b2938" stroke="#392126" stroke-width="6" stroke-linejoin="round"/>
  <path d="M111 51 Q151 17 204 39" fill="none" stroke="#e8b45f" stroke-width="5" stroke-linecap="round"/>
  <path d="M122 122 Q135 112 148 120" fill="none" stroke="#392126" stroke-width="5" stroke-linecap="round"/>
  <path d="M164 119 Q178 111 190 119" fill="none" stroke="#392126" stroke-width="5" stroke-linecap="round"/>
  <circle cx="137" cy="137" r="19" fill="none" stroke="#392126" stroke-width="6"/>
  <circle cx="178" cy="137" r="19" fill="none" stroke="#392126" stroke-width="6"/>
  <path d="M156 136 L159 136" stroke="#392126" stroke-width="6"/>
  <circle cx="139" cy="138" r="4" fill="#392126"/>
  <circle cx="178" cy="138" r="4" fill="#392126"/>
  <path d="M157 145 Q150 166 166 166 Q174 166 177 160" fill="none" stroke="#a85e42" stroke-width="5" stroke-linecap="round"/>
  <path d="M147 181 Q164 193 181 178" fill="none" stroke="#7b2938" stroke-width="5" stroke-linecap="round"/>
  <path d="M105 217 Q78 231 57 249 L76 264 Q101 249 122 239" fill="#efc99d" stroke="#392126" stroke-width="5"/>
  <path d="M51 248 Q38 237 29 246 Q26 259 45 267 L69 263" fill="#efc99d" stroke="#392126" stroke-width="5"/>
  <rect x="18" y="195" width="54" height="47" rx="8" fill="#282126" stroke="#392126" stroke-width="5" transform="rotate(-10 18 195)"/>
  <circle cx="46" cy="218" r="14" fill="#b8754e" stroke="#e8b45f" stroke-width="5"/>
</svg>
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');
:root { --wine:#4b202b; --cream:#f7efdf; --paper:#fff9ed; --ink:#2e2021; --copper:#bd6948; --gold:#e8b45f; }
.stApp { background:radial-gradient(circle at 85% 6%,#f3dfbd 0,transparent 25%),linear-gradient(135deg,#f4ead8 0%,#f8f1e5 52%,#efe1cc 100%); color:var(--ink); }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1160px; padding-top:1.1rem; padding-bottom:4rem; }
h1,h2,h3 { font-family:'Fraunces',Georgia,serif !important; color:var(--wine) !important; letter-spacing:-.025em; }
p,label,div,span { font-family:'DM Sans',Arial,sans-serif; }
.stMarkdown p { color:var(--ink); }
hr { border-color:#dfcbb2; }
[data-testid="stSidebar"] { background:#f2e4cf; border-right:1px solid #dfcbb2; }
.stButton button,.stFormSubmitButton button,.stDownloadButton button { border-radius:999px !important; border:1px solid #6d2938 !important; background:#6d2938 !important; color:#fff7e8 !important; font-weight:700 !important; min-height:2.8rem; padding:.55rem 1.25rem; transition:transform .15s ease,box-shadow .15s ease; }
.stButton button:hover,.stFormSubmitButton button:hover { transform:translateY(-2px); box-shadow:0 7px 18px #4b202b22; background:#8b3947 !important; border-color:#8b3947 !important; }
button[kind="secondary"] { background:#fff8ec !important; color:#5a2732 !important; }
.stTextInput input,.stSelectbox [data-baseweb="select"],.stMultiSelect [data-baseweb="select"] { border-radius:14px !important; background:#fffaf1 !important; }
[data-testid="stFileUploaderDropzone"] { background:#fff8ec; border:2px dashed #c68b67; border-radius:20px; }
[data-testid="stFileUploaderDropzone"] button { background:#6d2938 !important; color:#fff !important; }
.card { background:rgba(255,250,241,.88); border:1px solid #e4cfb4; border-radius:24px; padding:1.35rem 1.45rem; box-shadow:0 12px 34px rgba(75,32,43,.07); }
.hero { background:linear-gradient(115deg,#4b202b 0%,#713344 65%,#8b493d 100%); border-radius:30px; padding:2.4rem; color:#fff6e7; overflow:hidden; box-shadow:0 22px 50px rgba(75,32,43,.18); }
.hero h1 { color:#fff0d2 !important; font-size:clamp(2.6rem,5vw,4.5rem) !important; line-height:.98; margin-bottom:.8rem; }
.hero p { color:#f8e9d2; font-size:1.08rem; max-width:530px; }
.kicker { color:#c77f62; text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:800; }
.hero .kicker { color:#f0bc72; }
.mascot-wrap { display:flex; justify-content:center; align-items:center; min-height:300px; }
.mascot-wrap svg { width:min(100%,290px); height:auto; filter:drop-shadow(0 14px 13px #1b101822); }
.bubble { background:#fff4df; color:#4b202b; border:1px solid #e4c79e; border-radius:22px; padding:1rem 1.1rem; font-weight:600; box-shadow:0 8px 18px #25171a18; position:relative; }
.step-pill { display:inline-block; padding:.42rem .78rem; background:#ead8c1; border:1px solid #dfc4a5; border-radius:999px; color:#6b3a3e; font-size:.76rem; font-weight:800; letter-spacing:.04em; }
.progress-line { height:7px; background:#e6d5bf; border-radius:99px; overflow:hidden; margin:.5rem 0 1.2rem; }
.progress-line span { display:block; height:100%; background:linear-gradient(90deg,#b95f45,#e8b45f); border-radius:99px; }
.result-card { background:#fffaf1; border:1px solid #e5d1b8; border-radius:20px; overflow:hidden; padding:1rem; min-height:100%; }
.mini-note { color:#796568; font-size:.85rem; }
.stAlert { border-radius:16px; }
footer { visibility:hidden; }
</style>
"""

def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)

def flash_says(message, label="M. Flash, photographe officiel"):
    st.markdown(
        f'<div class="bubble"><span class="kicker">{html.escape(label)}</span><br>{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )

def mascot():
    st.markdown(f'<div class="mascot-wrap">{MASCOT}</div>', unsafe_allow_html=True)

def get_api_key():
    saved = ""
    try:
        saved = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        saved = os.getenv("OPENAI_API_KEY", "")
    st.sidebar.markdown("### Réglages du studio")
    key = st.sidebar.text_input("Clé API OpenAI", value=saved, type="password",
                                help="Utilise ta propre clé. Elle n'est jamais enregistrée dans le dépôt.")
    st.sidebar.caption("Les analyses sont facturées par OpenAI selon ton utilisation. Ne partage pas ta clé.")
    return key.strip()

def get_client(api_key):
    if not api_key:
        raise RuntimeError("Ajoute une clé API OpenAI dans les réglages du studio.")
    return OpenAI(api_key=api_key)

def parse_json(text):
    raw = (text or "").strip()
    fence = chr(96) * 3
    if raw.startswith(fence):
        raw = raw.split("\n", 1)[1].rsplit(fence, 1)[0].strip()
    return json.loads(raw)

def normalize_photo(upload):
    image = Image.open(upload).convert("RGB")
    image.thumbnail((1500, 1500))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=86, optimize=True)
    return {"data": buffer.getvalue(), "mime": "image/jpeg"}

def analyze_photos(api_key, photos):
    client = get_client(api_key)
    content = [{
        "type": "input_text",
        "text": (
            "Tu es l'assistant d'un studio photo ludique. Examine les photos fournies ensemble "
            "et décris uniquement les éléments de style non biométriques : coiffure (couleur, "
            "texture, longueur, coupe), barbe ou style de grooming visible, lunettes, accessoires, "
            "vêtements, palette de couleurs, maquillage et allure générale. N'analyse pas la "
            "géométrie du visage, les yeux, le nez, la bouche, la mâchoire, les proportions faciales "
            "ou les empreintes du visage. Ne compare pas les visages à ceux de célébrités. Ne déduis "
            "jamais l'origine, l'ethnicité, la race, la religion, la santé ou d'autres données "
            "sensibles. N'invente pas les détails masqués : écris 'à confirmer' si tu hésites. "
            "Réponds uniquement en JSON valide, en français, avec ces clés chaîne : hair_color, "
            "hair_texture, hair_length, haircut, grooming, eyewear, clothing, palette, makeup, "
            "accessories, overall_style, summary."        )
    }]
    for photo in photos:
        encoded = base64.b64encode(photo["data"]).decode("ascii")
        content.append({"type": "input_image", "image_url": f'data:{photo["mime"]};base64,{encoded}', "detail": "high"})
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_object"}},
        max_output_tokens=1200,
    )
    return parse_json(response.output_text)

def search_lookalikes(api_key, traits, preference, age_range, category):
    client = get_client(api_key)
    prompt = f"""
Tu es le directeur de casting d'un jeu de sosies de style, drôle mais respectueux.
À partir des éléments de style NON BIOMÉTRIQUES confirmés par la personne, propose des
célébrités publiques du monde entier qui partagent une esthétique, une coiffure, un grooming,
des accessoires ou une allure générale comparables. N'analyse pas et ne compare pas les visages :
pas de géométrie faciale, de traits du visage, d'empreintes ou de scores biométriques.
Il s'agit de suggestions de style ludiques, pas de sosies faciaux ni d'identification.
Ne déduis pas l'origine ou l'ethnicité de la personne photographiée.
Préférence de recherche : {preference}
Tranche d'âge de célébrités souhaitée : {age_range}
Univers professionnel souhaité : {category}
Traits confirmés : {json.dumps(traits, ensure_ascii=False)}
Retourne uniquement un objet JSON valide avec :
- celebrities : 6 objets ayant name, profession, country, reason, shared_features (liste de 2 à 4 éléments)
- other_universe : 3 objets ayant name, kind (personnage fictif, œuvre d'art ou personnage historique), reason
Les candidats doivent être réellement connus. Mélange les pays et les univers, sans inventer de
pourcentages de ressemblance. Les explications doivent rester bienveillantes, précises et ludiques.
"""
    response = client.responses.create(
        model="gpt-4.1-mini", input=prompt,
        text={"format": {"type": "json_object"}}, max_output_tokens=2200,
    )
    return parse_json(response.output_text)

def clean_html(value):
    return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()

@st.cache_data(ttl=21600, show_spinner=False)
def commons_photo(person_name):
    endpoint = "https://commons.wikimedia.org/w/api.php"
    headers = {"User-Agent": "TrouveTonSosie/1.0 (lookalike discovery app)"}
    params = {
        "action": "query", "generator": "search", "gsrsearch": f'"{person_name}" portrait',
        "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": 560, "format": "json",
    }
    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=12)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        if not pages:
            params["gsrsearch"] = person_name
            response = requests.get(endpoint, params=params, headers=headers, timeout=12)
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
        tokens = [token.lower() for token in person_name.split() if len(token) > 2]
        candidates = []
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            title = page.get("title", "")
            low_title = title.lower()
            score = sum(2 for token in tokens if token in low_title)
            if "portrait" in low_title or "headshot" in low_title:
                score += 1
            if not info.get("thumburl") or score < max(1, len(tokens)):
                continue
            meta = info.get("extmetadata", {})
            candidates.append({
                "score": score, "image": info.get("thumburl"), "source": info.get("descriptionurl", ""),
                "license": clean_html(meta.get("LicenseShortName", {}).get("value", "Licence à vérifier")),
                "artist": clean_html(meta.get("Artist", {}).get("value", "Auteur non indiqué")),
                "title": title,
            })
        return sorted(candidates, key=lambda item: item["score"], reverse=True)[0] if candidates else None
    except Exception:
        return None

@st.cache_data(ttl=21600, show_spinner=False)
def wikipedia_page(person_name):
    for language in ["fr", "en"]:
        try:
            endpoint = f"https://{language}.wikipedia.org/w/api.php"
            params = {"action": "query", "list": "search", "srsearch": person_name,
                      "srnamespace": 0, "srlimit": 5, "format": "json"}
            response = requests.get(endpoint, params=params, headers={"User-Agent": "TrouveTonSosie/1.0"}, timeout=10)
            response.raise_for_status()
            results = response.json().get("query", {}).get("search", [])
            best, best_score = None, 0
            for item in results:
                title = item.get("title", "")
                score = SequenceMatcher(None, person_name.casefold(), title.casefold()).ratio()
                if person_name.casefold() in title.casefold() or title.casefold() in person_name.casefold():
                    score += .25
                if score > best_score:
                    best, best_score = item, score
            if best and best_score >= .55:
                title = best["title"]
                return {"title": title, "url": f"https://{language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                        "snippet": clean_html(best.get("snippet", ""))}
        except Exception:
            continue
    return None

def google_images_url(name):
    return "https://www.google.com/search?tbm=isch&q=" + quote_plus(name + " portrait")

def render_progress(step):
    labels = ["La cabine", "Le portrait-robot", "Les sosies"]
    active = {"shooting": 0, "confirm": 1, "results": 2}.get(step, -1)
    if active < 0:
        return
    st.markdown(
        '<div style="display:flex;gap:.55rem;flex-wrap:wrap;margin:.5rem 0 1rem">'
        + "".join(f'<span class="step-pill" style="opacity:{1 if i <= active else .48}">{i+1:02d} · {label}</span>'
                  for i, label in enumerate(labels)) + "</div>", unsafe_allow_html=True)
    st.markdown(f'<div class="progress-line"><span style="width:{(active+1)/3*100:.0f}%"></span></div>',
                unsafe_allow_html=True)

def header():
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;padding:.2rem 0 1rem;'
        'border-bottom:1px solid #dfcbb2;margin-bottom:1.4rem">'
        '<div style="font-family:Fraunces,Georgia,serif;font-size:1.35rem;font-weight:700;color:#4b202b">📸 Trouve ton sosie</div>'
        '<div style="font-size:.8rem;color:#795e60;font-weight:700">LE STUDIO DES RESSEMBLANCES · DEPUIS TOUT À L’HEURE</div></div>',
        unsafe_allow_html=True)

def reset_app():
    for key in ["step", "photos", "analysis", "confirmed_traits", "matches", "other_matches"]:
        st.session_state.pop(key, None)
    st.session_state.step = "home"

apply_theme()
api_key = get_api_key()
header()
st.session_state.setdefault("step", "home")
step = st.session_state.step

if step == "home":
    left, right = st.columns([1.15, .85], vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="hero"><div class="kicker">Le studio des ressemblances · cabine n° 01</div>'
            '<h1>Trouve<br>ton sosie !</h1>'
            '<p>Tu as toujours voulu savoir à quelle célébrité tu fais penser ? '
            'Monsieur Flash a dépoussiéré son appareil. Il n’attend plus que toi.</p>'
            '<div style="color:#f3c77e;font-weight:700;margin-top:1.6rem">Des célébrités du monde entier. Des ressemblances inattendues. Zéro jugement.</div></div>',
            unsafe_allow_html=True)
        st.write("")
        if st.button("Entrer dans la cabine photo  →", type="primary", use_container_width=True):
            st.session_state.step = "shooting"
            st.rerun()
        st.caption("1 à 3 photos · quelques questions · une galerie de sosies à découvrir")
    with right:
        mascot()
        flash_says("Approchez, approchez ! J'ai l'œil, le flash et un très léger problème de pellicule.")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="card"><div class="kicker">01 · Le shooting</div><h3>Quelques clichés</h3><p>Trois photos maximum, idéalement avec une bonne lumière. Pas besoin de faire la couverture de Vogue.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><div class="kicker">02 · Le portrait-robot</div><h3>Tu gardes le dernier mot</h3><p>On décrit ton style, ta coiffure et ton allure. Tu confirmes, corriges ou supprimes ce qui ne te ressemble pas.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown("""<div class="card"><div class="kicker">03 · La galerie</div><h3>Les troublantes coïncidences</h3><p>Des célébrités, puis quelques sosies venus d'un autre univers : fiction, animation ou peinture.</p></div>""", unsafe_allow_html=True)

elif step == "shooting":
    render_progress(step)
    left, right = st.columns([.8, 1.2], vertical_alignment="center")
    with left:
        mascot()
        flash_says("Une à trois photos ! De face, de trois-quarts, avec ton vrai sourire. Je promets de ne pas les mettre au mur du bistrot.")
    with right:
        st.markdown('<div class="kicker">Étape 1 · La cabine de shooting</div><h2>Installe-toi, on prend la pose.</h2>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Dépose 1 à 3 photos de toi", type=["jpg", "jpeg", "png", "webp"],
                                    accept_multiple_files=True, key="shooting_photos",
                                    help="Photos nettes, visage visible.")
        if uploaded:
            if len(uploaded) > 3:
                st.warning("Monsieur Flash a seulement trois pinces à linge. On garde les trois premières photos.")
            previews = st.columns(min(len(uploaded), 3))
            for i, file in enumerate(uploaded[:3]):
                with previews[i]:
                    st.image(file, caption=f"Cliché {i+1}", use_container_width=True)
        consent = st.checkbox(
            "J'accepte que mes photos soient envoyées à l'API OpenAI pour analyser les caractéristiques visibles. Elles ne sont pas enregistrées dans le dépôt GitHub.",
            value=False)
        st.caption("Les photos sont conservées en mémoire de session par l'application. Elles servent à décrire les éléments de style visibles, pas à créer une empreinte faciale. Leur traitement par l'API est soumis aux conditions et paramètres de données OpenAI.")
        ready = bool(uploaded) and len(uploaded) <= 3 and consent and bool(api_key)
        if not api_key:
            st.warning("Il faut une clé API OpenAI dans les réglages à gauche pour analyser les photos.")
        if st.button("Faire mon portrait-robot  →", type="primary", disabled=not ready, use_container_width=True):
            try:
                st.session_state.photos = [normalize_photo(file) for file in uploaded[:3]]
                with st.spinner("Monsieur Flash ajuste la lumière et observe les détails…"):
                    st.session_state.analysis = analyze_photos(api_key, st.session_state.photos)
                st.session_state.step = "confirm"
                st.rerun()
            except Exception as exc:
                st.error(f"Le studio a eu un petit raté : {exc}")

elif step == "confirm":
    render_progress(step)
    analysis = st.session_state.get("analysis", {})
    left, right = st.columns([.75, 1.25], vertical_alignment="center")
    with left:
        mascot()
        flash_says("J'ai développé tes clichés ! Voici ce que j'ai noté. Corrige-moi sans pitié : je suis photographe, pas devin.")
        st.markdown('<div class="mini-note">Les détails masqués ou incertains peuvent rester « à confirmer ».</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="kicker">Étape 2 · Le portrait-robot</div><h2>Est-ce bien toi, tout ça ?</h2>', unsafe_allow_html=True)
        st.write(analysis.get("summary", "Voici les détails visibles que j'ai pu relever."))
        with st.form("confirm_traits"):
            col1, col2 = st.columns(2)
            with col1:
                hair_color = st.text_input("Couleur des cheveux", value=analysis.get("hair_color", "à confirmer"))
                hair_texture = st.text_input("Texture des cheveux", value=analysis.get("hair_texture", "à confirmer"))
                hair_length = st.text_input("Longueur des cheveux", value=analysis.get("hair_length", "à confirmer"))
                haircut = st.text_input("Coupe / coiffure", value=analysis.get("haircut", "à confirmer"))
                grooming = st.text_input("Barbe / style de grooming (si visible)", value=analysis.get("grooming", "à confirmer"))
            with col2:
                eyewear = st.text_input("Lunettes / accessoires portés", value=analysis.get("eyewear", "à confirmer"))
                clothing = st.text_input("Style vestimentaire", value=analysis.get("clothing", "à confirmer"))
                palette = st.text_input("Palette de couleurs", value=analysis.get("palette", "à confirmer"))
                makeup = st.text_input("Maquillage (si visible)", value=analysis.get("makeup", "à confirmer"))
                accessories = st.text_input("Autres accessoires", value=analysis.get("accessories", ""))
            overall_style = st.text_input("Allure générale / univers esthétique (facultatif)", value=analysis.get("overall_style", ""))
            st.markdown("**Affinons la recherche**")
            pref1, pref2 = st.columns(2)
            with pref1:
                preference = st.selectbox("Catégorie de célébrités", ["Toutes", "Femmes", "Hommes"])
                age_range = st.selectbox("Âge des célébrités", ["Sans préférence", "20–30 ans", "30–40 ans", "40–50 ans", "50 ans et plus"])
            with pref2:
                category = st.selectbox("Univers", ["Tous les univers", "Cinéma & séries", "Musique", "Mode & culture", "Sport & médias"])
                include_other = st.checkbox("Ajouter des sosies d'un autre univers", value=True)
            submitted = st.form_submit_button("Je valide mon portrait-robot — trouve mes sosies !", type="primary", use_container_width=True)
        if submitted:
            traits = {
                "hair_color": hair_color, "hair_texture": hair_texture, "hair_length": hair_length,
                "haircut": haircut, "grooming": grooming, "eyewear": eyewear,
                "clothing": clothing, "palette": palette, "makeup": makeup,
                "accessories": accessories, "overall_style": overall_style,
            }
            st.session_state.confirmed_traits = traits
            try:
                with st.spinner("Le moteur feuillette ses annuaires internationaux…"):
                    matches = search_lookalikes(api_key, traits, preference, age_range, category)
                    enriched = []
                    for candidate in matches.get("celebrities", [])[:6]:
                        name = str(candidate.get("name", "")).strip()
                        if name:
                            wiki = wikipedia_page(name)
                            commons = commons_photo(name)
                            # Keep only candidates with a public reference we could verify.
                            if wiki or commons:
                                enriched.append({**candidate, "wikipedia": wiki,
                                                 "commons": commons, "google_images": google_images_url(name)})
                    enriched_other = []
                    if include_other:
                        for candidate in matches.get("other_universe", [])[:3]:
                            name = str(candidate.get("name", "")).strip()
                            if name:
                                wiki = wikipedia_page(name)
                                commons = commons_photo(name)
                                if wiki or commons:
                                    enriched_other.append({**candidate, "wikipedia": wiki, "commons": commons,
                                                           "google_images": google_images_url(name)})
                    st.session_state.matches = enriched
                    st.session_state.other_matches = enriched_other
                st.session_state.step = "results"
                st.rerun()
            except Exception as exc:
                st.error(f"Le moteur a perdu le fil de la pellicule : {exc}")
    if st.button("← Retour à la cabine"):
        st.session_state.step = "shooting"
        st.rerun()

elif step == "results":
    render_progress(step)
    left, right = st.columns([.8, 1.2], vertical_alignment="center")
    with left:
        mascot()
        flash_says("Et voilà le tirage ! J'ai fait le tour du monde, vidé trois annuaires et pris un café. Voici les ressemblances à examiner.")
    with right:
        st.markdown('<div class="kicker">Étape 3 · Le grand révélateur</div><h2>Les sosies sont dans la boîte !</h2>', unsafe_allow_html=True)
        st.write("Des rapprochements d'esthétique fondés sur les éléments de style que tu as confirmés. Ce ne sont pas des comparaisons biométriques ni des sosies faciaux.")
    celebrities = st.session_state.get("matches", [])
    if celebrities:
        st.markdown("### Tes sosies de style côté célébrités")
        grid = st.columns(3)
        for index, person in enumerate(celebrities):
            with grid[index % 3]:
                with st.container(border=True):
                    photo = person.get("commons")
                    if photo and photo.get("image"):
                        st.image(photo["image"], use_container_width=True)
                    else:
                        st.markdown('<div style="padding:2rem;text-align:center;background:#f0e2cc;border-radius:14px;font-size:2.5rem">🎞️</div>', unsafe_allow_html=True)
                    st.markdown(f"### {html.escape(str(person.get('name','Candidat')))}")
                    st.caption(f"{html.escape(str(person.get('profession','Personnalité publique')))} · {html.escape(str(person.get('country','International')))}")
                    st.write(person.get("reason", "Une piste à explorer."))
                    shared = person.get("shared_features", [])
                    if shared:
                        st.markdown("**Les points communs relevés**")
                        st.write(" · ".join(str(item) for item in shared[:4]))
                    if photo:
                        st.caption(f"Photo : {photo.get('artist','Auteur non indiqué')} · {photo.get('license','Licence à vérifier')}")
                        if photo.get("source"):
                            st.markdown(f"[Source et licence de l'image]({photo['source']})")
                    wiki = person.get("wikipedia")
                    if wiki:
                        st.markdown(f"[Fiche biographique]({wiki['url']})")
                    st.markdown(f"[Voir d'autres portraits sur Google Images]({person.get('google_images', google_images_url(person.get('name','')))})")
    else:
        st.warning("Le moteur n'a pas proposé de célébrité cette fois. Relance la recherche avec des caractéristiques plus précises.")
    others = st.session_state.get("other_matches", [])
    if others:
        st.markdown("### Et si ton sosie venait d'un autre univers ?")
        st.caption("Personnages de fiction, figures historiques et œuvres d'art : le casting parallèle.")
        cols = st.columns(3)
        for index, item in enumerate(others):
            with cols[index % 3]:
                with st.container(border=True):
                    photo = item.get("commons")
                    if photo and photo.get("image"):
                        st.image(photo["image"], use_container_width=True)
                    else:
                        st.markdown('<div style="padding:2rem;text-align:center;background:#f0e2cc;border-radius:14px;font-size:2.5rem">🎭</div>', unsafe_allow_html=True)
                    st.markdown(f"**{html.escape(str(item.get('name','Personnage')))}**")
                    st.caption(str(item.get("kind", "Autre univers")))
                    st.write(item.get("reason", "Une parenté d'allure inattendue."))
                    if photo and photo.get("source"):
                        st.markdown(f"[Source et licence de l'image]({photo['source']})")
                    st.markdown(f"[Voir les images]({item.get('google_images', google_images_url(item.get('name','')))})")
    left, right = st.columns(2)
    with left:
        if st.button("Recommencer une séance  ↻", use_container_width=True):
            reset_app()
            st.rerun()
    with right:
        result_payload = {
            "portrait_robot": st.session_state.get("confirmed_traits", {}),
            "celebrites": [{"name": p.get("name"), "raison": p.get("reason")} for p in celebrities],
            "autre_univers": [{"name": p.get("name"), "raison": p.get("reason")} for p in others],
        }
        st.download_button("Télécharger mon tirage", data=json.dumps(result_payload, ensure_ascii=False, indent=2),
                           file_name="mes-sosies.json", mime="application/json", use_container_width=True)

st.markdown(
    '<div style="text-align:center;margin-top:3rem;color:#927c70;font-size:.78rem">'
    'Trouve ton sosie · Un jeu de ressemblances, jamais un jugement. '
    'Les photos sont transmises à OpenAI pour analyse uniquement si tu y consens.'
    '</div>', unsafe_allow_html=True)
