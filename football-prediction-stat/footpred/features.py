"""Variables d'avant-match (sans fuite) pour les 5 grands championnats.

Toutes les moyennes glissantes sont décalées d'un match (shift(1)) : la ligne d'un match ne contient que de l'information
disponible avant son coup d'envoi. tests/test_fuite.py le vérifie automatiquement.
"""
import difflib
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from . import config as C
from .ratings import PiRatings, GasRatings


@dataclass
class Donnees:
    X: pd.DataFrame                  # une ligne par match (index = mid), variables + résultats
    L: pd.DataFrame                  # table longue : une ligne par (équipe, match)
    D: pd.DataFrame                  # matchs des 5 ligues
    pi: PiRatings
    gas: GasRatings
    c_L: pd.Series                   # buts par tir cadré, par (ligue, saison), estimé sur les saisons antérieures
    date_max: pd.Timestamp = field(default=None)

    # ---------- état d'une équipe pour prédire un match à venir ----------
    def etat(self, equipe: str) -> dict:
        t = self.L[self.L.team == equipe].sort_values("date")
        if t.empty:
            proches = difflib.get_close_matches(equipe, self.L.team.unique(), 5)
            raise ValueError(f"Équipe inconnue : « {equipe} ». Noms proches : {proches}")
        last = t.tail(C.FENETRE_FORME)
        lg = t.Division.iloc[-1]
        s_cur = int(self.D.Season.max())
        joues = int(((self.D.HomeTeam == equipe) | (self.D.AwayTeam == equipe))[self.D.Season == s_cur].sum())
        n_eq = self.D[(self.D.Division == lg) & (self.D.Season == s_cur)].HomeTeam.nunique() or 20
        lgm = self.D[self.D.Division == lg].tail(C.FENETRE_LIGUE)
        return {"elo": t.elo.dropna().iloc[-1], "Q": last.xg_f.mean() - last.xg_a.mean(), "O": last.xg_f.mean() + last.xg_a.mean(),
                "pi": self.pi.note(equipe), "lg": lg, "date": t.date.iloc[-1].date(),
                "lg_mh": lgm.FTHome.mean(), "lg_ma": lgm.FTAway.mean(), "restants": 2 * (n_eq - 1) - joues}

    def variables_match(self, dom: str, ext: str, elo_dom=None, elo_ext=None) -> tuple[dict, dict, dict]:
        """Construit le vecteur de variables d'un match à venir (même définition que pour l'apprentissage)."""
        a, b = self.etat(dom), self.etat(ext)
        ea, eb = elo_dom or a["elo"], elo_ext or b["elo"]
        v = {"dElo": (ea - eb) / 100, "dQ": a["Q"] - b["Q"], "Otot": a["O"] + b["O"] - C.OUVERTURE_CENTRE,
             "pi_diff": a["pi"][0] - b["pi"][1], "pi_diff_avg": np.mean(a["pi"]) - np.mean(b["pi"])}
        v["absElo"] = abs(v["dElo"])
        for lg in C.LIGUES:
            if lg != C.LIGUE_REF:
                v[f"lg_{lg}"] = float(a["lg"] == lg)
        v["g_lh"], v["g_la"] = self.gas.log_lambdas(dom, ext, a["lg"])
        v["lg_mh_c"], v["lg_ma_c"] = a["lg_mh"] - C.CENTRE_BUTS[0], a["lg_ma"] - C.CENTRE_BUTS[1]
        v["_elo_dom"], v["_elo_ext"] = ea, eb
        return v, a, b


def construire(raw: pd.DataFrame) -> Donnees:
    # 1. ratings sur toutes les ligues, ordre chronologique
    R = raw.dropna(subset=["HomeTeam", "AwayTeam"]).sort_values("MatchDate", kind="stable").reset_index(drop=True)
    pi, gas = PiRatings(), GasRatings()
    R[["pi_hh", "pi_ha", "pi_ah", "pi_aa"]] = pi.calculer(R)
    R[["g_lh", "g_la"]] = gas.calculer(R)

    # 2. 5 grands championnats, table longue équipe-match
    D = R[R.Division.isin(C.LIGUES) & (R.Season >= C.SAISON_MIN)].dropna(subset=["FTResult"]).reset_index(drop=True)
    D["mid"] = np.arange(len(D)); D["y"] = D.FTResult.map({"H": 0, "D": 1, "A": 2})

    def side(home):
        s, o = ("Home", "Away") if home else ("Away", "Home")
        return pd.DataFrame({"mid": D.mid, "date": D.MatchDate, "Division": D.Division, "team": D[f"{s}Team"], "home": int(home),
                             "gf": D[f"FT{s}"], "ga": D[f"FT{o}"], "sot_f": D[f"{s}Target"], "sot_a": D[f"{o}Target"], "elo": D[f"{s}Elo"]})
    L = pd.concat([side(True), side(False)]).sort_values(["team", "date", "mid"]).reset_index(drop=True)
    # xG approché = c × tirs cadrés ; c (buts par tir cadré) estimé sur les SAISONS PRÉCÉDENTES de la ligue uniquement
    H5 = R[R.Division.isin(C.LIGUES)].dropna(subset=["FTHome", "HomeTarget"])
    tot = pd.DataFrame({"g": H5.FTHome + H5.FTAway, "t": H5.HomeTarget + H5.AwayTarget, "Division": H5.Division, "Season": H5.Season}) \
        .groupby(["Division", "Season"]).sum()
    prev = tot.groupby(level=0).cumsum() - tot
    c_L = (prev.g / prev.t.where(prev.t > 0)).fillna(C.CONVERSION_DEFAUT)
    cs = pd.Series(list(zip(D.Division, D.Season)), index=D.mid).map(c_L)
    L["xg_f"], L["xg_a"] = L.sot_f * L.mid.map(cs), L.sot_a * L.mid.map(cs)
    g = L.groupby("team")
    mf = g.xg_f.transform(lambda x: x.shift(1).rolling(C.FENETRE_FORME, min_periods=5).mean())
    ma = g.xg_a.transform(lambda x: x.shift(1).rolling(C.FENETRE_FORME, min_periods=5).mean())
    L["Q"], L["O"] = mf - ma, mf + ma

    # 3. variables du match
    H, A = L[L.home == 1].set_index("mid"), L[L.home == 0].set_index("mid")
    X = D.set_index("mid")
    X["dElo"] = (X.HomeElo - X.AwayElo) / 100; X["absElo"] = X.dElo.abs()
    X["dQ"] = H.Q - A.Q; X["Otot"] = H.O + A.O - C.OUVERTURE_CENTRE
    X["pi_diff"] = X.pi_hh - X.pi_aa; X["pi_diff_avg"] = (X.pi_hh + X.pi_ha) / 2 - (X.pi_ah + X.pi_aa) / 2
    for lg in C.LIGUES:
        if lg != C.LIGUE_REF:
            X[f"lg_{lg}"] = (X.Division == lg).astype(float)
    Dm = D.sort_values(["Division", "MatchDate", "mid"])
    for c, col in (("lg_mh", "FTHome"), ("lg_ma", "FTAway")):
        Dm[c] = Dm.groupby("Division")[col].transform(lambda x: x.shift(1).rolling(C.FENETRE_LIGUE, min_periods=150).mean())
    X = X.join(Dm.set_index("mid")[["lg_mh", "lg_ma"]])
    X["lg_mh_c"], X["lg_ma_c"] = X.lg_mh - C.CENTRE_BUTS[0], X.lg_ma - C.CENTRE_BUTS[1]
    X = X.dropna(subset=C.FE_B)
    return Donnees(X=X, L=L, D=D, pi=pi, gas=gas, c_L=c_L, date_max=raw.MatchDate.max())
