"""Application Streamlit du modèle v4.   Lancer en local : streamlit run app.py"""
import datetime as dt
import os
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from footpred import preparer, config as C
from footpred.markets import cote_juste

st.set_page_config(page_title="Prédiction football — modèle v4", page_icon="⚽", layout="wide")
BLEU, GRIS, ORANGE = "#2a78d6", "#8a8984", "#eb6834"


@st.cache_resource(ttl=dt.timedelta(hours=12), show_spinner="Chargement des données, calcul des ratings et entraînement du modèle (≈ 30 s)…")
def charger():
    # données fraîches à chaque rechargement (toutes les 12 h) ; FOOTPRED_SOURCE permet d'utiliser un fichier local
    return preparer(os.environ.get("FOOTPRED_SOURCE", C.DATA_URL), cache=None)


@st.cache_data(ttl=dt.timedelta(hours=12))
def equipes_par_ligue(_date_max):
    X = charger().d.X
    out = {}
    for lg in C.LIGUES:
        x = X[X.Division == lg]
        s = x.Season.max()
        eq = set(x[x.Season == s].HomeTeam) | set(x[x.Season == s].AwayTeam)
        if len(eq) < 16:                                          # début de saison : compléter avec la saison précédente
            eq |= set(x[x.Season == s - 1].HomeTeam)
        out[lg] = sorted(eq)
    return out


pred = charger()
EQ = equipes_par_ligue(str(pred.d.date_max))
TOUTES = sorted({e for v in EQ.values() for e in v})

# ------------------------------------------------------------------ barre latérale
with st.sidebar:
    st.title("⚽ Modèle v4")
    page = st.radio("Navigation", ["Prédire un match", "Prédire une journée", "Performance du modèle", "Méthode"], label_visibility="collapsed")
    retard = (dt.date.today() - pred.d.date_max.date()).days
    st.caption(f"Données au **{pred.d.date_max.date()}**" + (f" · ⚠ {retard} jours de retard" if retard > 7 else ""))
    if st.button("Recharger les données"):
        st.cache_resource.clear(); st.cache_data.clear(); st.rerun()
    st.divider()
    st.caption("Projet académique : estimation probabiliste des résultats. Ce n'est pas un conseil de pari — "
               "le modèle est en moyenne moins précis que les cotes (log loss 0,982 contre 0,972).")


def barre_1x2(r, dom, ext):
    df = pd.DataFrame({"issue": [f"1 · {dom}", "X · nul", f"2 · {ext}"], "p": [r["1"], r["X"], r["2"]], "ordre": [0, 1, 2]})
    base = alt.Chart(df).encode(y=alt.Y("issue:N", sort=alt.SortField("ordre"), title=None), x=alt.X("p:Q", axis=alt.Axis(format="%", tickCount=5), title=None, scale=alt.Scale(domain=[0, 1])),
                                tooltip=[alt.Tooltip("issue:N"), alt.Tooltip("p:Q", format=".1%")])
    return (base.mark_bar(cornerRadiusEnd=4, height=26, color=BLEU) + base.mark_text(align="left", dx=6).encode(text=alt.Text("p:Q", format=".1%"))).properties(height=130)


def carte_scores(M, dom, ext, n=6):
    d = pd.DataFrame([(i, j, M[i, j]) for i in range(n) for j in range(n)], columns=[dom, ext, "p"])
    base = alt.Chart(d).encode(x=alt.X(f"{ext}:O", title=f"Buts {ext}", axis=alt.Axis(labelAngle=0)), y=alt.Y(f"{dom}:O", title=f"Buts {dom}"),
                               tooltip=[alt.Tooltip(f"{dom}:O"), alt.Tooltip(f"{ext}:O"), alt.Tooltip("p:Q", format=".1%")])
    heat = base.mark_rect(stroke="white", strokeWidth=2).encode(color=alt.Color("p:Q", scale=alt.Scale(scheme="blues"), legend=None))
    txt = base.mark_text(fontSize=11).encode(text=alt.Text("p:Q", format=".1%"), color=alt.condition("datum.p > 0.06", alt.value("white"), alt.value("#0b0b0b")))
    return (heat + txt).properties(height=300)


# ------------------------------------------------------------------ page 1
if page == "Prédire un match":
    st.header("Prédire un match")
    c1, c2, c3 = st.columns([1, 1.2, 1.2])
    lg = c1.selectbox("Championnat", list(C.LIGUES), format_func=C.LIGUES.get, index=1)
    AFFICHE = {"SP1": ("Barcelona", "Real Madrid"), "E0": ("Arsenal", "Liverpool"), "I1": ("Inter", "Milan"),
               "D1": ("Bayern Munich", "Dortmund"), "F1": ("Paris SG", "Marseille")}.get(lg, ("", ""))
    dom = c2.selectbox("Équipe à domicile", EQ[lg], index=EQ[lg].index(AFFICHE[0]) if AFFICHE[0] in EQ[lg] else 0)
    autres = [e for e in EQ[lg] if e != dom]
    ext = c3.selectbox("Équipe à l'extérieur", autres, index=autres.index(AFFICHE[1]) if AFFICHE[1] in autres else 0)
    with st.expander("Options : ajuster l'Elo (blessures, rotation…) ou comparer à des cotes"):
        o1, o2 = st.columns(2)
        a, b = pred.d.etat(dom), pred.d.etat(ext)
        elo_d = o1.number_input(f"Elo {dom}", value=float(round(a["elo"])), step=10.0)
        elo_e = o2.number_input(f"Elo {ext}", value=float(round(b["elo"])), step=10.0)
        avec_cotes = st.checkbox("Comparer aux cotes d'un bookmaker")
        cotes = None
        if avec_cotes:
            k1, k2, k3 = st.columns(3)
            cotes = (k1.number_input("Cote 1", 1.01, 50.0, 2.0), k2.number_input("Cote X", 1.01, 50.0, 3.4), k3.number_input("Cote 2", 1.01, 50.0, 3.8))
    try:
        r = pred.predire(dom, ext, elo_dom=elo_d, elo_ext=elo_e, cotes=cotes)
    except ValueError as e:
        st.error(str(e)); st.stop()
    M = r.pop("_M")

    m1, m2, m3, m4 = st.columns(4)
    for col, lab, k in ((m1, f"Victoire {dom}", "1"), (m2, "Match nul", "X"), (m3, f"Victoire {ext}", "2")):
        col.metric(lab, f"{r[k]:.1%}"); col.caption(f"cote juste {cote_juste(r[k]):.2f}")
    m4.metric("Buts attendus", f"{r['buts_dom']:.2f} – {r['buts_ext']:.2f}"); m4.caption(f"total {r['buts_dom'] + r['buts_ext']:.2f}")
    st.altair_chart(barre_1x2(r, dom, ext), width="stretch")

    niveau = {"faible": "🔴", "moyenne": "🟠", "bonne": "🟢", "élevée": "🟢"}[r["fiabilite"]]
    st.info(f"{niveau} **Fiabilité {r['fiabilite']}** — quand le modèle est aussi confiant, son issue favorite s'est réalisée "
            f"**{r['precision_historique']:.0%}** du temps sur 2021-2026.")
    if r["fin_de_saison"]:
        st.warning("Fin de saison : ces matchs sont historiquement moins prévisibles (enjeux, rotations).")

    g1, g2 = st.columns([1, 1.1])
    with g1:
        st.subheader("Marchés")
        lignes = [("Plus de 1,5 but", r["over15"]), ("Plus de 2,5 buts", r["over25"]), ("Plus de 3,5 buts", r["over35"]),
                  ("Les deux équipes marquent", r["btts"]), ("But en 1re mi-temps", r["but_1re_MT"]),
                  (f"Cage inviolée {dom}", r["cs_dom"]), (f"Cage inviolée {ext}", r["cs_ext"])]
        st.dataframe(pd.DataFrame({"Marché": [l[0] for l in lignes], "Probabilité": [100 * l[1] for l in lignes], "Cote juste": [cote_juste(l[1]) for l in lignes]}),
                     hide_index=True, width="stretch",
                     column_config={"Probabilité": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
                                    "Cote juste": st.column_config.NumberColumn(format="%.2f")})
        st.caption("Scores les plus probables : " + " · ".join(f"**{s}** {q:.1%}" for q, s in r["scores"]))
    with g2:
        st.subheader("Probabilité de chaque score")
        st.altair_chart(carte_scores(M, dom, ext), width="stretch")

    if "marche" in r:
        mk = r["marche"]
        st.subheader(f"Comparaison aux cotes (marge du bookmaker {mk['marge']:.1%}, méthode de Shin)")
        st.dataframe(pd.DataFrame({"Issue": ["1", "X", "2"], "Modèle": [r["1"], r["X"], r["2"]], "Marché": [mk["1"], mk["X"], mk["2"]],
                                   "Écart (points)": [100 * (r[k] - mk[k]) for k in ["1", "X", "2"]]}), hide_index=True,
                     column_config={"Modèle": st.column_config.NumberColumn(format="percent"), "Marché": st.column_config.NumberColumn(format="percent"),
                                    "Écart (points)": st.column_config.NumberColumn(format="%+.1f")})
        st.caption("Le marché est en moyenne plus précis que le modèle : un grand écart signale d'abord une information que le modèle n'a pas (blessure, composition).")

    with st.expander("Détail des variables du modèle"):
        v = r["variables"]
        st.write(pd.DataFrame({"valeur": v}).T.round(3))
        st.caption("dElo : écart Elo/100 · dQ : écart de qualité de jeu (xG approché) · Otot : ouverture · pi : pi-ratings · g_lh / g_la : log des buts attendus (ratings GAS)")

# ------------------------------------------------------------------ page 2
elif page == "Prédire une journée":
    st.header("Prédire une journée")
    st.caption("Saisis les affiches (une ligne par match), puis télécharge le tableau horodaté pour ton suivi.")
    if "journee" not in st.session_state:
        st.session_state.journee = pd.DataFrame({"Domicile": ["Arsenal", "Barcelona", "Paris SG"], "Extérieur": ["Chelsea", "Sevilla", "Lyon"]})
    grille_saisie = st.data_editor(st.session_state.journee, num_rows="dynamic", width="stretch",
                                   column_config={"Domicile": st.column_config.SelectboxColumn(options=TOUTES, required=True),
                                                  "Extérieur": st.column_config.SelectboxColumn(options=TOUTES, required=True)})
    lignes = []
    for _, m in grille_saisie.dropna().iterrows():
        if m.Domicile == m.Extérieur:
            continue
        try:
            r = pred.predire(m.Domicile, m.Extérieur); r.pop("_M")
        except ValueError as e:
            st.error(str(e)); continue
        lignes.append({"Domicile": m.Domicile, "Extérieur": m.Extérieur, "1": r["1"], "X": r["X"], "2": r["2"],
                       "Pronostic": ["1", "X", "2"][int(np.argmax([r["1"], r["X"], r["2"]]))],
                       "Buts dom": r["buts_dom"], "Buts ext": r["buts_ext"], "+2,5 buts": r["over25"], "BTTS": r["btts"], "Fiabilité": r["fiabilite"]})
    if lignes:
        T = pd.DataFrame(lignes)
        pc = {c: st.column_config.NumberColumn(format="%.1f %%") for c in ["1", "X", "2", "+2,5 buts", "BTTS"]}
        st.dataframe(T.assign(**{c: 100 * T[c] for c in ["1", "X", "2", "+2,5 buts", "BTTS"]}), hide_index=True, width="stretch", column_config={**pc, "Buts dom": st.column_config.NumberColumn(format="%.2f"),
                                                                                  "Buts ext": st.column_config.NumberColumn(format="%.2f")})
        T.insert(0, "horodatage", dt.datetime.now().strftime("%Y-%m-%d %H:%M")); T.insert(1, "donnees_au", str(pred.d.date_max.date()))
        st.download_button("Télécharger les prédictions (CSV)", T.to_csv(index=False).encode("utf-8"),
                           file_name=f"predictions_{dt.date.today()}.csv", mime="text/csv")

# ------------------------------------------------------------------ page 3
elif page == "Performance du modèle":
    st.header("Performance du modèle — test 2021/22 → 2025/26")
    st.caption("Chaque saison est prédite par un modèle entraîné uniquement sur les saisons précédentes (walk-forward). Log loss : plus bas = mieux.")
    T = pd.read_csv("results/tables/validation_2021_2026_1X2.csv", index_col=0)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Log loss v4", f"{T.loc['v4', 'log loss']:.4f}", f"{T.loc['v4', 'log loss'] - T.loc['Elo seul', 'log loss']:+.4f} vs Elo seul", delta_color="inverse")
    k2.metric("Log loss cotes", f"{T.loc['Cotes', 'log loss']:.4f}")
    k3.metric("Bon résultat v4", f"{T.loc['v4', 'bon résultat']:.1%}")
    k4.metric("Matchs testés", f"{int(T.loc['v4', 'matchs']):,}".replace(",", " "))
    st.dataframe(T.drop(columns="matchs"), width="stretch",
                 column_config={"bon résultat": st.column_config.NumberColumn(format="percent"), "skill vs fréquences": st.column_config.NumberColumn(format="percent")})
    st.image("results/figures/validation_2021_2026.png", width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tests de significativité")
        st.dataframe(pd.read_csv("results/tables/validation_2021_2026_tests.csv", index_col=0).round(2), width="stretch")
    with c2:
        st.subheader("Marchés de buts")
        st.dataframe(pd.read_csv("results/tables/validation_2021_2026_buts.csv", index_col=0).map(lambda v: "—" if pd.isna(v) else f"{v:.4f}"), width="stretch")
    st.subheader("Saison 2025/26 rejouée semaine par semaine")
    st.image("results/figures/hebdo_2025.png", width="stretch")
    st.subheader("Le marché est-il battable ? (stratégies simulées, rendement par mise de 1)")
    S = pd.read_csv("results/tables/strategies_2021_2026_strategies.csv", index_col=0)
    st.dataframe(S, width="stretch", column_config={c: st.column_config.NumberColumn(format="percent") for c in ["gagnés", "rendement", "IC bas", "IC haut"]})
    st.caption("Aucune stratégie n'a un intervalle de confiance entièrement positif : le modèle ne bat pas le marché.")

# ------------------------------------------------------------------ page 4
else:
    st.markdown(open("docs/methodologie.md", encoding="utf-8").read())
