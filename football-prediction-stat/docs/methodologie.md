# Méthodologie du modèle v4

## 1. Données

- **Source** : dataset public *Club-Football-Match-Data* (xgabora), environ 50 Mo et 230 000 matchs de 2000 à aujourd'hui. Il est construit à partir de football-data.co.uk et de ClubElo.
- **Colonnes utilisées** :
  - date, équipes, division ;
  - buts à la mi-temps et en fin de match ;
  - tirs cadrés ;
  - Elo d'avant-match (ClubElo) ;
  - cotes 1X2 et over/under, qui servent **uniquement** de référence d'évaluation.
- **Périmètre de modélisation** : Premier League (E0), Liga (SP1), Serie A (I1), Bundesliga (D1) et Ligue 1 (F1), à partir de la saison 2005/06. Les ratings sont calculés sur **toutes** les ligues du dataset, pour que les promus arrivent déjà avec une note.
- **Saison** : de juillet à juin, notée par son année de début (2025 = 2025/26).

## 2. Ratings dynamiques (mis à jour après chaque match)

### 2.1 ClubElo

Pris tel quel dans le dataset. Variable : ΔElo = (Elo_dom − Elo_ext)/100, et |ΔElo|, car le nul est plus probable quand les forces sont proches.

### 2.2 pi-ratings (Constantinou & Fenton 2013)

Chaque équipe a une note à domicile R_H et une note à l'extérieur R_A. L'écart de buts attendu vaut ê = ψ(R_H,dom) − ψ(R_A,ext), avec ψ(r) = sign(r)·(10^{|r|/3} − 1).

Après le match :
- erreur e = (buts_dom − buts_ext) − ê ;
- erreur amortie s = sign(e)·3·log10(1 + |e|) ;
- mises à jour R_H,dom += λ·s, R_A,ext −= λ·s, et les notes croisées bougent de γ fois ce changement.

Paramètres : λ = 0,035 et γ = 0,7, ceux de l'article.

Variables :
- pi_diff = R_H,dom − R_A,ext ;
- pi_diff_avg = moyenne(R_dom) − moyenne(R_ext).

### 2.3 Ratings de buts à score GAS (Koopman & Lit 2019), apport principal de la v4

Pour un match de la ligue L :

```
log λ_dom = μ_L + h_L + att_dom − déf_ext
log λ_ext = μ_L − h_L + att_ext − déf_dom
```

Après le match, mise à jour par le gradient de la log-vraisemblance de Poisson (le « score ») :

```
att_dom ← att_dom + η (buts_dom − λ_dom)      déf_ext ← déf_ext − η (buts_dom − λ_dom)
att_ext ← att_ext + η (buts_ext − λ_ext)      déf_dom ← déf_dom − η (buts_ext − λ_ext)
μ_L, h_L mis à jour au pas η_L
```

- Quand une équipe change de division (promotion ou relégation), att et déf sont multipliés par 0,5.
- **Réglage** : η = 0,0125, η_L = 0,0001, rétrécissement 0,5. Ces valeurs maximisent la vraisemblance de Poisson des buts sur **2006-2015 uniquement**, donc avant la sélection et le test.
- Variables : g_lh = log λ_dom et g_la = log λ_ext, calculés avant le match.

## 3. Autres variables d'avant-match

- **xG approché** = c_L,s × tirs cadrés. c_L,s est le nombre de buts par tir cadré de la ligue, estimé sur les **saisons antérieures** (0,25 en Premier League, environ 0,30 ailleurs).
- **ΔQ** : qualité de jeu. On prend, pour chaque équipe, la moyenne sur ses 10 derniers matchs de (xG pour − xG contre), puis on fait la différence entre domicile et extérieur.
- **Ouverture** Otot = somme des (xG pour + xG contre) des deux équipes, centrée sur 5,5.
- **Effet ligue** : indicatrices pour SP1, I1, D1 et F1 (la Premier League est la référence).
- **Niveau de buts de la ligue** : moyenne des buts à domicile et à l'extérieur sur les 380 derniers matchs de la ligue, centrée. Utilisé seulement dans le modèle de buts.

Toutes les moyennes glissantes sont décalées d'un match. `tests/test_fuite.py` falsifie un résultat et vérifie que les variables de ce match et des matchs antérieurs ne changent pas. Ce test a d'ailleurs détecté une petite fuite dans une version précédente : c_L était calculé sur toutes les saisons. Elle a été corrigée ; son effet sur la log loss était inférieur à 10⁻⁴.

## 4. Modèles

### 4.1 Résultat 1X2 : régression logistique multinomiale

```
z1 = log[P(1)/P(X)] = β1 · x        z2 = log[P(2)/P(X)] = β2 · x
P(X) = 1 / (1 + e^z1 + e^z2),  P(1) = e^z1 P(X),  P(2) = e^z2 P(X)
```

Estimation par maximum de vraisemblance pondérée, avec un poids w = 0,5^((s_ref − saison)/4) : un match d'il y a 4 saisons compte 2 fois moins.

### 4.2 Buts : Poisson + Dixon-Coles

- log λ_dom = α·x et log λ_ext = α'·x : deux GLM de Poisson avec les mêmes poids.
- P(score i-j) = Pois(i; λ_dom) · Pois(j; λ_ext) · τ(i, j), où τ corrige les scores 0-0, 1-0, 0-1 et 1-1 (Dixon & Coles 1997).
- ρ ≈ −0,055, estimé par maximum de vraisemblance.
- La grille 11×11 donne tous les marchés : over/under, BTTS, cage inviolée, score exact. Une simulation Monte-Carlo de 100 000 tirages vérifie la cohérence.
- **But en 1re mi-temps** : λ_MT = k·(λ_dom + λ_ext), avec k ≈ 0,44 estimé par maximum de vraisemblance. P = 1 − e^(−λ_MT).

### 4.3 Sorties complémentaires

- **Cote juste** = 1/p.
- **Comparaison aux cotes** : les probabilités du marché sont débarrassées de la marge par la méthode de Shin (1993).
- **Indice de fiabilité** : taux de réussite observé de l'issue favorite selon la confiance du modèle, sur le test 2021-2026.

| Confiance du modèle (p max) | ≤ 42 % | 42-50 % | 50-61 % | > 61 % |
|---|---|---|---|---|
| Issue favorite réalisée | 39 % | 46 % | 54 % | 71 % |

## 5. Protocole d'évaluation

| Période | Usage |
|---|---|
| 2006-2015 | Réglage des paramètres des ratings (GAS) |
| 2017/18-2020/21 | Sélection entre modèles candidats |
| **2021/22-2025/26** | **Test final unique**, jamais utilisé pour un choix |

- **Walk-forward** : pour prédire la saison s, on entraîne sur toutes les saisons strictement antérieures.
- **Métriques** :
  - log loss (règle de score propre, critère principal) ;
  - RPS (tient compte de l'ordre 1 < X < 2) ;
  - Brier ;
  - ECE (calibration par déciles) ;
  - taux de bons résultats (indicatif seulement).
- **Significativité** : bootstrap apparié sur les différences match par match (2 000 rééchantillonnages, IC à 95 %).
- **Références** : fréquences des issues, Elo seul, version précédente v3, et cotes des bookmakers (référence externe, jamais utilisées comme variable).

## 6. Ce qui a été testé puis rejeté

| Piste | Résultat | Décision |
|---|---|---|
| Elo-buts et pi « réglés » sur 2015-2020 | Gain en sélection, **non reproduit** en test | Rejeté : surapprentissage de la sélection |
| Forces Dixon-Coles dynamiques (penaltyblog) | Redondantes avec GAS, 100 fois plus lentes | Rejeté |
| Ratings GAP (Wheatcroft) | Pas de gain | Rejeté |
| LightGBM, XGBoost, ensembles | Moins bons que le logit (0,984-0,986) | Rejeté |
| 38 à 112 variables (forme, tirs, corners, repos, confrontations directes) | Plateau, puis dégradation (surapprentissage) | Rejeté |
| Ré-entraînement hebdomadaire | +0,4 ×10⁻³ (non significatif) | Inutile : les ratings se mettent déjà à jour |
| Méthodes des guides de paris | Voir `docs/resultats.md` §7 | Deux idées retenues : niveau de buts de la ligue, marchés dérivés |
