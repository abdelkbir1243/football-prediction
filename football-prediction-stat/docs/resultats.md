# Résultats

Tous les chiffres ci-dessous sont reproductibles avec `python scripts/reproduire.py`. Les tables CSV se trouvent dans `results/tables/` et les figures dans `results/figures/`.
Log loss : plus bas = mieux. Δ exprimé en ×10⁻³. IC = intervalle de confiance à 95 % obtenu par bootstrap apparié.

## 1. Test final 1X2, 2021/22 → 2025/26 (8 821 matchs, walk-forward)

| Modèle | Log loss | RPS | Brier | ECE | Bon résultat | Skill score |
|---|---|---|---|---|---|---|
| Fréquences | 1,0737 | 0,2300 | 0,6497 | 0,010 | 43,5 % | 0 % |
| Elo seul | 0,9864 | 0,2001 | 0,5882 | 0,013 | 52,4 % | 8,1 % |
| v3 | 0,9823 | 0,1990 | 0,5854 | 0,013 | 52,9 % | 8,5 % |
| **v4** | **0,9818** | **0,1989** | **0,5849** | **0,011** | 52,6 % | **8,6 %** |
| Cotes | 0,9722 | 0,1957 | 0,5783 | 0,015 | 53,7 % | 9,5 % |

| Comparaison | Δ log loss | IC 95 % | Conclusion |
|---|---|---|---|
| v4 − v3 (1X2) | −0,52 | [−1,70 ; +0,69] | non significatif |
| v4 − Elo seul | −4,55 | [−6,83 ; −2,21] | **significatif** |
| v4 − cotes | +9,64 | [+6,76 ; +12,32] | le marché reste meilleur |
| v4 − v3 (score exact) | −5,17 | [−7,53 ; −2,76] | **significatif** |
| v4 − v3 (over 2,5) | −4,24 | [−6,00 ; −2,48] | **significatif** |

## 2. Marchés de buts (même test)

| | LL score exact | LL over 2,5 | LL BTTS | Buts prévus / match |
|---|---|---|---|---|
| v3 | 2,9119 | 0,6802 | 0,6857 | 2,805 |
| **v4** | **2,9067** | **0,6759** | **0,6839** | 2,808 |
| Cotes over/under | — | 0,6717 | — | — |
| Réel | — | — | — | 2,808 |

La calibration de l'over 2,5 est bonne. Par quintile de probabilité annoncée : 42 % annoncé → 41 % observé, 48 → 48, 52 → 53, 56 → 59, 65 → 66.

## 3. Stabilité par ligue et par saison (log loss 1X2)

| Ligue | Elo seul | v3 | v4 | Cotes |
|---|---|---|---|---|
| Bundesliga | 0,9906 | 0,9866 | 0,9862 | 0,9763 |
| Liga | 0,9828 | 0,9787 | 0,9770 | 0,9675 |
| Ligue 1 | 1,0006 | 0,9952 | 0,9942 | 0,9837 |
| Premier League | 0,9794 | 0,9746 | 0,9737 | 0,9606 |
| Serie A | 0,9809 | 0,9788 | 0,9801 | 0,9750 |

| Saison | Elo seul | v3 | v4 | Cotes |
|---|---|---|---|---|
| 2021/22 | 0,9903 | 0,9886 | 0,9862 | 0,9778 |
| 2022/23 | 0,9867 | 0,9832 | 0,9878 | 0,9805 |
| 2023/24 | 0,9719 | 0,9679 | 0,9664 | 0,9567 |
| 2024/25 | 0,9855 | 0,9806 | 0,9782 | 0,9650 |
| 2025/26 | 0,9972 | 0,9911 | 0,9902 | 0,9802 |

v4 est meilleur que v3 dans 4 ligues sur 5 et 4 saisons sur 5. Contrairement à une idée reçue, la Ligue 1 et la Liga ne sont pas plus prévisibles que la Premier League.

## 4. Laboratoire : saison 2025/26

**Modèle figé au 1er juillet 2025** (1 737 matchs) :

| | Log loss | RPS | Bon résultat |
|---|---|---|---|
| Elo seul | 0,9972 | 0,2035 | 51,2 % |
| v3 | 0,9911 | 0,2015 | 51,5 % |
| v4 | 0,9902 | 0,2011 | 51,1 % |
| Cotes | 0,9802 | 0,1980 | 53,3 % |

**Saison rejouée semaine par semaine** (37 semaines, ré-entraînement chaque lundi) :

| Indicateur | Valeur |
|---|---|
| Log loss avec ré-entraînement hebdomadaire | 0,9906 |
| Log loss du modèle figé | 0,9902 |
| Gain du ré-entraînement | +0,40 ×10⁻³, IC [−0,23 ; +1,01] : nul |
| Écart avec les cotes | +10,3 ×10⁻³, IC [+3,6 ; +17,1] |
| Semaines où v4 bat les cotes | 16 / 37 (43 %) |

Conclusion : les ratings se mettent à jour après chaque match. Ré-estimer les coefficients chaque semaine n'apporte rien, un ré-entraînement par saison suffit.

## 5. Efficience du marché : stratégies simulées (test 2021-2026)

Rendement moyen par mise de 1 :

| Stratégie | Paris | Gagnés | Rendement | IC 95 % |
|---|---|---|---|---|
| Value v4 contre la cote moyenne, seuil 0 % | 9 209 | 31,7 % | −5,8 % | [−8,9 ; −2,3] |
| Value v4 contre la cote moyenne, seuil 5 % | 5 512 | 29,1 % | −8,4 % | [−12,7 ; −4,1] |
| Value v4 contre la cote moyenne, seuil 10 % | 3 099 | 26,6 % | −10,7 % | [−16,7 ; −4,5] |
| Value v4 contre la cote moyenne, seuil 20 % | 1 109 | 19,8 % | −21,1 % | [−31,6 ; −11,0] |
| Value v4 contre la meilleure cote, seuil 0 % | 13 011 | 31,3 % | −2,0 % | [−5,0 ; +1,2] |
| Toujours le favori | 8 821 | 53,7 % | −2,2 % | [−4,2 ; −0,3] |
| Toujours le nul | 8 821 | 25,4 % | −2,5 % | [−6,0 ; +1,1] |
| Toujours l'outsider | 8 821 | 20,7 % | −10,4 % | [−14,4 ; −6,3] |

Expérience complémentaire : un modèle v4 qui reçoit aussi les cotes en entrée atteint une log loss de 0,9713, contre 0,9722 pour les cotes seules. L'écart est non significatif (IC [−2,2 ; +0,4] ×10⁻³). Le meilleur rendement simulé avec ce modèle est de +2,6 %, IC [−6,3 % ; +11,5 %] : **aucune stratégie n'est démontrée gagnante**. Le seul biais net est le biais favori-outsider.

## 6. Nombre de variables et surapprentissage (test 2021-2026)

| Variables | Méthode | LL sur l'entraînement | LL sur le test |
|---|---|---|---|
| Elo seul (2) | logit | 0,981 | 0,9864 |
| **v4 (12)** | logit | 0,975 | **0,9819** |
| v4 + forme, tirs, corners, repos (38) | logit régularisé | 0,972 | 0,9813 |
| v4 + forme, tirs, corners, repos (38) | LightGBM | 0,949 | 0,9841 |
| Tout (112) | logit | 0,966 | 0,9840 |
| Tout (112) | logit régularisé | 0,969 | 0,9835 |
| Tout (112) | LightGBM | 0,959 | 0,9847 |

Quand on ajoute des variables, l'erreur sur l'entraînement baisse mais l'erreur sur le test remonte : c'est la signature du surapprentissage. Les variables supplémentaires sont redondantes avec les ratings. Pour progresser, il faudrait de l'**information nouvelle** (compositions, blessures, vrais xG), pas plus de paramètres.

## 7. Méthodes des guides de paris confrontées aux données (2005-2025)

| Affirmation | Mesure | Verdict |
|---|---|---|
| « Surebet français » gagne 8 fois sur 10 | réussite 79,4 %, rendement −4,3 % | vrai en fréquence, perdant en moyenne |
| Toute cote domicile > 2,17 est une value | victoire à domicile 30,3 %, rendement −6,4 % | faux |
| Poisson « attaque × défense » (Kit foot) | log loss 1,013 contre 0,983 pour le modèle | utile mais dépassé ; son étape 1 est intégrée |
| BTTS : Bundesliga 56,7 %, Ligue 1 48,7 % | 57,1 % et 50,1 % | confirmé |
| « BTTS non » rapporte 37 % de plus que « moins de 2,5 » | 47,6 % contre 48,8 % | faux |
| BTTS plus faible à 15 h en Premier League | à cotes égales, p = 0,32 | non confirmé |
| 70 % des matchs ont un but en 1re mi-temps | 70,0 % | confirmé, marché ajouté |
| « Fin de série » après deux 0-0 à la pause | 67,5 % contre 70,0 %, p = 0,33 | faux (sophisme du joueur) |
| Écarter les fins de saison | skill score de 7,1 % en mai contre 8,9 % le reste de l'année | plutôt confirmé : alerte ajoutée |
| Stratégie anti-favoris | favori −2,8 %, outsider −11,3 % | faux (biais favori-outsider) |

## 8. Historique des versions (log loss sur le test 2021-2026)

| Version | Contenu | Log loss 1X2 |
|---|---|---|
| v1 | Logit sur ΔElo + ΔQ | 0,9844 |
| v2 | Ensemble XGBoost, LightGBM, CatBoost et logit, avec 100+ variables | ≈ 0,984-0,986 (plateau) |
| v3 | + pi-ratings, ouverture, \|ΔElo\|, ligue, pondération temporelle, marchés dérivés | 0,9823 |
| **v4** | + ratings de buts GAS ; correction de la fuite sur c_L | **0,9818** (buts : −5 ×10⁻³) |
