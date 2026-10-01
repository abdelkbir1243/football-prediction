# Déployer l'application sur Streamlit Community Cloud (gratuit)

L'application `app.py` propose quatre pages :
- **Prédire un match** : probabilités 1X2, buts attendus, marchés, carte des scores, fiabilité, comparaison optionnelle aux cotes ;
- **Prédire une journée** : tableau de plusieurs matchs, téléchargeable en CSV horodaté ;
- **Performance du modèle** : les résultats du test 2021-2026 ;
- **Méthode** : la méthodologie et ses formules.

## 1. Tester en local
```bash
pip install -r requirements.txt
streamlit run app.py
```
L'application s'ouvre sur http://localhost:8501. Le premier chargement prend environ 30 s (téléchargement de 50 Mo, calcul des ratings, entraînement).

## 2. Mettre le projet sur GitHub
Le dépôt doit être **public** pour l'offre gratuite. Voir `docs/guide_utilisation.md` §A.

## 3. Déployer
1. Aller sur https://share.streamlit.io et se connecter avec son compte GitHub.
2. Cliquer sur **Create app**, puis **Deploy a public app from GitHub**.
3. Renseigner :
   - Repository : `abdelkbir1243/football-prediction-stat`
   - Branch : `main`
   - Main file path : `app.py`
   - App URL : au choix, par exemple `prediction-foot-v4`
4. Dans **Advanced settings**, choisir Python 3.11 ou 3.12.
5. Cliquer sur **Deploy**. La première installation prend 2 à 4 minutes.

L'application obtient une adresse du type `https://prediction-foot-v4.streamlit.app`.

## 4. Fonctionnement en production
- **Données** : elles sont retéléchargées au plus toutes les 12 heures, ou quand on clique sur le bouton « Recharger les données ». Le modèle est alors réentraîné automatiquement.
- **Mémoire** : environ 500 Mo au démarrage, dans les limites de l'offre gratuite.
- **Mise en veille** : l'application s'endort après quelques jours sans visite. Le premier visiteur la réveille en environ 1 minute.
- **Mise à jour du code** : chaque `git push` sur `main` redéploie l'application automatiquement.
- **Suivi des prédictions** : le disque de Streamlit Cloud n'est pas permanent. Pour le suivi hebdomadaire officiel, télécharge le CSV de la page « Prédire une journée », ou utilise le notebook 04, qui enregistre le journal sur Google Drive.

## 5. Problèmes fréquents

| Symptôme | Solution |
|---|---|
| `ModuleNotFoundError: footpred` | Vérifier que `app.py` est à la racine du dépôt, à côté du dossier `footpred/` |
| Erreur de mémoire | Redémarrer l'application (menu ⋮ → Reboot) ; le chargement se limite déjà aux colonnes utiles |
| Données anciennes | Le dataset source est mis à jour avec quelques jours de décalage : cliquer sur « Recharger les données » |
| Équipe absente de la liste | La liste contient les équipes de la saison en cours (et de la saison précédente en début de saison) |
