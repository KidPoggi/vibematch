# VibeMatch

Prototype Streamlit de recherche de proximités d'esthétique.

## Fonctionnalités
- Import d'une photo.
- Analyse du style non biométrique : coiffure, vêtements, palette, maquillage, accessoires et ambiance.
- Classement expérimental de profils selon les tags de style communs.

## Limites
Cette application ne réalise pas d'identification, de reconnaissance faciale ni de comparaison biométrique. Les résultats ne sont pas des scores scientifiques de ressemblance.

## Déploiement Streamlit Community Cloud
1. Connecter ce dépôt à https://share.streamlit.io/
2. Choisir `app.py` comme fichier principal.
3. Dans les paramètres de l'application, ajouter un secret :
   `OPENAI_API_KEY = "ta-cle-api"`
4. Déployer.

## Exécution locale
```bash
pip install -r requirements.txt
streamlit run app.py
```
