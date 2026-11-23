# Trouve ton sosie

Une expérience web ludique en plusieurs étapes, construite avec Streamlit.

## Parcours utilisateur

1. **Accueil** : Monsieur Flash, photographe du studio, invite la personne dans la cabine.
2. **Shooting** : import de 1 à 3 photos ; consentement explicite avant l'envoi des photos à l'API OpenAI.
3. **Portrait-robot** : l'IA propose des caractéristiques physiques visibles ; l'utilisateur peut tout confirmer, corriger ou laisser en « à confirmer ».
4. **Recherche** : génération de pistes de célébrités et de sosies venus d'un autre univers (fiction, art, figures historiques).
5. **Tirage** : galerie de résultats, raisons des rapprochements et liens vers les sources.

## Déploiement sur Streamlit Community Cloud

- Repository : KidPoggi/vibematch
- Branch : main
- Main file : app.py

Dans les Secrets Streamlit, tu peux ajouter OPENAI_API_KEY = "ta-cle-api".
Sinon, chaque utilisateur peut saisir sa propre clé API dans les réglages du studio. Les appels API sont facturés par OpenAI selon l'utilisation.

## Images de célébrités

L'application recherche des images via l'API Wikimedia Commons et affiche les liens de source, l'auteur et la licence quand ces informations sont disponibles. Elle propose aussi un lien vers Google Images pour chaque candidat, mais ne copie ni ne télécharge automatiquement les résultats Google Images.

## Confidentialité

- Les photos sont redimensionnées en mémoire pour l'analyse.
- Elles ne sont pas enregistrées dans le dépôt GitHub ni dans une base de données par cette application.
- Elles sont envoyées à l'API OpenAI après consentement ; le traitement est soumis aux conditions et paramètres de données OpenAI.
- Les résultats restent des suggestions de ressemblance ludiques. Aucun score de probabilité ou pourcentage artificiel n'est affiché.
- L'application ne demande pas et ne déduit pas l'origine ethnique ou d'autres caractéristiques sensibles.

## Lancer localement

pip install -r requirements.txt
streamlit run app.py
