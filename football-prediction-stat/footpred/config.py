"""Paramètres du modèle. Tous ont été fixés AVANT le test final 2021-2026 (voir docs/methodologie.md)."""

DATA_URL = "https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/data/Matches.csv"

LIGUES = {"E0": "Premier League", "SP1": "Liga", "I1": "Serie A", "D1": "Bundesliga", "F1": "Ligue 1"}
LIGUE_REF = "E0"                      # ligue de référence des indicatrices (effet ligue = 0)
SAISON_MIN = 2005                     # première saison utilisée pour l'apprentissage (2005/06)

# Pondération temporelle : un match d'il y a DEMI_VIE saisons pèse 2 fois moins
DEMI_VIE = 4

# pi-ratings (Constantinou & Fenton 2013) — paramètres de l'article
PI = dict(lr=0.035, gamma=0.7, b=10, c=3)

# Ratings de buts à score GAS (Koopman & Lit 2019) — réglés par vraisemblance sur 2006-2015
GAS = dict(eta=0.0125, eta_l=0.0001, shrink=0.5, mu0=0.262364264467491, ha0=0.15)   # mu0 = log(1.3)

# xG approché : fenêtre de forme (matchs) et centrage de l'ouverture
FENETRE_FORME = 10
CONVERSION_DEFAUT = 0.30          # buts par tir cadré si aucune saison antérieure n'est disponible
OUVERTURE_CENTRE = 5.5
# Niveau de buts de la ligue : 380 derniers matchs, centré
FENETRE_LIGUE = 380
CENTRE_BUTS = (1.5, 1.15)

# Grille des scores
GMAX = 10

# Variables
FE_V3 = ["dElo", "absElo", "dQ", "Otot", "pi_diff", "pi_diff_avg", "lg_SP1", "lg_I1", "lg_D1", "lg_F1"]
FE = FE_V3 + ["g_lh", "g_la"]                         # modèle 1X2 (v4)
FE_B = FE + ["lg_mh_c", "lg_ma_c"]                    # modèle de buts (v4)
FE_B_V3 = FE_V3 + ["lg_mh_c", "lg_ma_c"]

# Découpage du protocole
SAISONS_TEST = [2021, 2022, 2023, 2024, 2025]
