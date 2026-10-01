"""footpred — modèle statistique de prédiction des matchs de football (projet académique).

Utilisation rapide :
    from footpred import preparer
    pred = preparer()                      # télécharge les données, calcule les ratings, entraîne le modèle final
    pred.simulation("Arsenal", "Chelsea")
"""
from .data import charger_matchs
from .features import construire
from .models import ModeleComplet, Modele1X2, ModeleButs, grille
from .predict import Predicteur
from . import config, evaluation, journal

__version__ = "4.0.0"


def preparer(source=None, cache="data/Matches.csv"):
    """Charge les données, construit les variables et entraîne le modèle final sur toutes les saisons."""
    d = construire(charger_matchs(source, cache))
    return Predicteur(d)
