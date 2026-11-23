import os
import json
import base64
from pathlib import Path

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="VibeMatch", page_icon="✨", layout="wide")
DATA_PATH = Path(__file__).parent / "celebrities.json"

st.title("✨ VibeMatch")
st.caption("Recherche de proximités d’esthétique — prototype expérimental")
st.info(
    "Cette version analyse les éléments de style visibles (coiffure, vêtements, "
    "palette, maquillage et accessoires). Elle ne réalise pas d’identification "
    "ni de comparaison biométrique des visages."
)

def load_profiles():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_style(image_bytes, mime_type, api_key):
    client = OpenAI(api_key=api_key)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    prompt = """
Analyse uniquement le STYLE VISUEL non biométrique visible dans cette image.
Décris : coiffure (couleur, longueur, texture), vêtements, palette de couleurs,
maquillage visible, accessoires et impression esthétique générale.
N'analyse pas la géométrie du visage, l'identité, l'origine, l'âge, ni les
ressemblances physiques avec une personne réelle. Ne déduis aucune caractéristique
personnelle sensible.
Retourne strictement un objet JSON avec ces clés :
{"hair":[],"clothing":[],"palette":[],"makeup":[],"accessories":[],"vibe":[],"summary":""}
Utilise des tags courts en français. Si une catégorie n'est pas visible, retourne [].
"""
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:{mime_type};base64,{encoded}"}
            ]
        }]
    )
    raw = response.output_text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)

def norm(value):
    return str(value).strip().lower()

def tags(profile):
    keys = ["hair", "clothing", "palette", "makeup", "accessories", "vibe"]
    return {norm(item) for key in keys for item in profile.get(key, [])}

def rank_profiles(style, profiles):
    keys = ["hair", "clothing", "palette", "makeup", "accessories", "vibe"]
    query = {norm(item) for key in keys for item in style.get(key, [])}
    ranked = []
    for profile in profiles:
        candidate = tags(profile)
        if not candidate:
            continue
        common = query & candidate
        union = query | candidate
        score = len(common) / len(union) if union else 0.0
        ranked.append((score, profile, sorted(common)))
    return sorted(ranked, key=lambda item: item[0], reverse=True)

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "Clé API OpenAI", type="password",
        value=os.getenv("OPENAI_API_KEY", "")
    )
    st.caption("La clé est saisie dans cette session et n'est pas enregistrée dans le dépôt.")
    profiles = load_profiles()
    st.write(f"Base actuelle : {len(profiles)} profils")

uploaded = st.file_uploader("Importer une photo", type=["jpg", "jpeg", "png", "webp"])

if uploaded:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image(uploaded, caption="Photo importée", use_container_width=True)
    with col2:
        st.subheader("Analyse")
        if st.button("Analyser et rechercher", type="primary", disabled=not api_key):
            try:
                with st.spinner("Analyse des éléments de style…"):
                    style = analyze_style(
                        uploaded.getvalue(), uploaded.type or "image/jpeg", api_key
                    )
                    st.session_state["style"] = style
                    st.session_state["matches"] = rank_profiles(style, profiles)
            except Exception as exc:
                st.error(f"Analyse impossible : {exc}")
        if not api_key:
            st.warning("Ajoute une clé API dans la barre latérale pour lancer l’analyse.")

if "style" in st.session_state:
    style = st.session_state["style"]
    st.divider()
    st.subheader("Portrait esthétique extrait")
    st.write(style.get("summary", ""))
    columns = st.columns(3)
    for column, key, label in zip(
        columns, ["hair", "clothing", "vibe"], ["Cheveux", "Vêtements", "Ambiance"]
    ):
        with column:
            st.markdown(f"**{label}**")
            st.write(", ".join(style.get(key, [])) or "Non renseigné")
    with st.expander("Tous les attributs"):
        st.json(style)

    st.subheader("Profils partageant des éléments de style")
    st.caption("Classement expérimental par correspondance de tags, pas un score de ressemblance.")
    for score, profile, common in st.session_state.get("matches", [])[:10]:
        with st.container(border=True):
            left, right = st.columns([1, 4])
            with left:
                if profile.get("image_url"):
                    st.image(profile["image_url"], use_container_width=True)
                else:
                    st.markdown("### ✨")
            with right:
                st.markdown(f"**{profile['name']}** · {profile.get('profession', 'Personnalité')}")
                st.write(profile.get("description", ""))
                st.caption("Attributs de style communs : " + (", ".join(common) or "aucun tag exact"))
                if profile.get("source"):
                    st.markdown(f"[Source]({profile['source']})")

with st.expander("Comment enrichir la base ?"):
    st.write(
        "Modifie celebrities.json en ajoutant des profils, des tags descriptifs "
        "et des URL d’images pour lesquelles tu disposes des droits d’utilisation."
    )
