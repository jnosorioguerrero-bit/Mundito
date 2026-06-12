import os, json, requests
import firebase_admin
from firebase_admin import credentials, firestore

# ── Configuración ──────────────────────────────────────────────────────────────
FDATA_TOKEN = os.environ["FDATA_TOKEN"]
FDATA_URL   = "https://api.football-data.org/v4/competitions/WC/matches?season=2026"

# Mapeo nombre football-data.org → nombre en la quiniela
TEAM_MAP = {
    "Mexico":                   "México",
    "South Africa":              "Sudáfrica",
    "Korea Republic":            "Corea del Sur",
    "Czech Republic":            "Rep. Checa",
    "Canada":                    "Canadá",
    "Bosnia and Herzegovina":    "Bosnia y Herz.",
    "United States":             "Estados Unidos",
    "Qatar":                     "Catar",
    "Switzerland":               "Suiza",
    "Morocco":                   "Marruecos",
    "Haiti":                     "Haití",
    "Scotland":                  "Escocia",
    "Turkey":                    "Turquía",
    "Germany":                   "Alemania",
    "Curaçao":                   "Curazao",
    "Netherlands":               "Países Bajos",
    "Japan":                     "Japón",
    "Ivory Coast":               "Costa de Marfil",
    "Sweden":                    "Suecia",
    "Tunisia":                   "Túnez",
    "Spain":                     "España",
    "Cape Verde":                "Cabo Verde",
    "Belgium":                   "Bélgica",
    "Egypt":                     "Egipto",
    "Saudi Arabia":              "Arabia Saudita",
    "Iran":                      "Irán",
    "New Zealand":               "Nueva Zelanda",
    "France":                    "Francia",
    "Iraq":                      "Irak",
    "Norway":                    "Noruega",
    "Algeria":                   "Argelia",
    "Jordan":                    "Jordania",
    "Portugal":                  "Portugal",
    "DR Congo":                  "RD Congo",
    "England":                   "Inglaterra",
    "Croatia":                   "Croacia",
    "Panama":                    "Panamá",
    "Uzbekistan":                "Uzbekistán",
    "Colombia":                  "Colombia",
    "Venezuela":                 "Venezuela",
    "Ecuador":                   "Ecuador",
    "Brazil":                    "Brasil",
    "Australia":                 "Australia",
    "Paraguay":                  "Paraguay",
    "Serbia":                    "Serbia",
    "Kenya":                     "Kenia",
    "Nigeria":                   "Nigeria",
    "Chile":                     "Chile",
    "Argentina":                 "Argentina",
    "Austria":                   "Austria",
    "Ghana":                     "Ghana",
    "Uruguay":                   "Uruguay",
    "Senegal":                   "Senegal",
}

# Partidos de la quiniela: (home, away) → id
QUINIELA_MATCHES = {
    ("México","Sudáfrica"):         "a1",
    ("Corea del Sur","Rep. Checa"): "a2",
    ("Canadá","Bosnia y Herz."):    "b1",
    ("Estados Unidos","Paraguay"):  "d1",
    ("Catar","Suiza"):              "b2",
    ("Brasil","Marruecos"):         "c1",
    ("Haití","Escocia"):            "c2",
    ("Australia","Turquía"):        "d2",
    ("Alemania","Curazao"):         "e1",
    ("Países Bajos","Japón"):       "f1",
    ("Costa de Marfil","Ecuador"):  "e2",
    ("Suecia","Túnez"):             "f2",
    ("España","Cabo Verde"):        "h1",
    ("Bélgica","Egipto"):           "g1",
    ("Arabia Saudita","Uruguay"):   "h2",
    ("Irán","Nueva Zelanda"):       "g2",
    ("Francia","Senegal"):          "i1",
    ("Irak","Noruega"):             "i2",
    ("Argentina","Argelia"):        "j1",
    ("Austria","Jordania"):         "j2",
    ("Portugal","RD Congo"):        "k1",
    ("Inglaterra","Croacia"):       "l1",
    ("Ghana","Panamá"):             "l2",
    ("Uzbekistán","Colombia"):      "k2",
    ("Rep. Checa","Sudáfrica"):     "a3",
    ("Suiza","Bosnia y Herz."):     "b3",
    ("Canadá","Catar"):             "b4",
    ("México","Corea del Sur"):     "a4",
    ("Turquía","Paraguay"):         "d3",
    ("Escocia","Marruecos"):        "c3",
    ("Brasil","Haití"):             "c4",
    ("Estados Unidos","Australia"): "d4",
    ("Túnez","Japón"):              "f3",
    ("Países Bajos","Suecia"):      "f4",
    ("Alemania","Costa de Marfil"): "e3",
    ("Ecuador","Curazao"):          "e4",
    ("España","Arabia Saudita"):    "h3",
    ("Bélgica","Irán"):             "g3",
    ("Cabo Verde","Uruguay"):       "h4",
    ("Nueva Zelanda","Egipto"):     "g4",
    ("Francia","Irak"):             "i3",
    ("Noruega","Senegal"):          "i4",
    ("Argentina","Austria"):        "j3",
    ("Argelia","Jordania"):         "j4",
    ("Portugal","Uzbekistán"):      "k3",
    ("Colombia","RD Congo"):        "k4",
    ("Inglaterra","Ghana"):         "l3",
    ("Croacia","Panamá"):           "l4",
    ("Sudáfrica","Corea del Sur"):  "a5",
    ("México","Rep. Checa"):        "a6",
    ("Catar","Bosnia y Herz."):     "b5",
    ("Suiza","Canadá"):             "b6",
    ("Marruecos","Haití"):          "c5",
    ("Escocia","Brasil"):           "c6",
    ("Paraguay","Australia"):       "d5",
    ("Turquía","Estados Unidos"):   "d6",
    ("Curazao","Costa de Marfil"):  "e5",
    ("Ecuador","Alemania"):         "e6",
    ("Japón","Suecia"):             "f5",
    ("Túnez","Países Bajos"):       "f6",
    ("Egipto","Nueva Zelanda"):     "g5",
    ("Irán","Bélgica"):             "g6",
    ("Panamá","Inglaterra"):        "l5",
    ("Croacia","Ghana"):            "l6",
    ("Colombia","Portugal"):        "k5",
    ("RD Congo","Uzbekistán"):      "k6",
    ("Jordania","Argentina"):       "j5",
    ("Argelia","Austria"):          "j6",
    ("Arabia Saudita","Cabo Verde"):"h3",
    ("Uruguay","España"):           "h4",
    ("Senegal","Francia"):          "i3",
    ("Noruega","Irak"):             "i4",
}

def normalize(name):
    return TEAM_MAP.get(name, name)

def main():
    # ── Inicializar Firebase ───────────────────────────────────────────────────
    cred_json = json.loads(os.environ["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(cred_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    ref = db.collection("quiniela").document("data")

    # ── Leer estado actual de Firebase ────────────────────────────────────────
    doc = ref.get()
    state = doc.to_dict() if doc.exists else {}
    results = state.get("results", {})

    # ── Consultar football-data.org ────────────────────────────────────────────
    resp = requests.get(FDATA_URL, headers={"X-Auth-Token": FDATA_TOKEN}, timeout=15)
    resp.raise_for_status()
    matches = resp.json().get("matches", [])

    finished = [
        m for m in matches
        if m["status"] == "FINISHED"
        and m["score"]["fullTime"]["home"] is not None
        and m["score"]["fullTime"]["away"] is not None
    ]

    print(f"Partidos terminados en la API: {len(finished)}")

    # ── Mapear y detectar cambios ─────────────────────────────────────────────
    updated = False
    for fm in finished:
        h_name = normalize(fm["homeTeam"]["name"])
        a_name = normalize(fm["awayTeam"]["name"])
        h_score = fm["score"]["fullTime"]["home"]
        a_score = fm["score"]["fullTime"]["away"]

        match_id = QUINIELA_MATCHES.get((h_name, a_name))
        if not match_id:
            print(f"  ⚠️  Sin mapeo: {h_name} vs {a_name}")
            continue

        existing = results.get(match_id)
        if not existing or existing.get("h") != h_score or existing.get("a") != a_score:
            results[match_id] = {"h": h_score, "a": a_score}
            updated = True
            print(f"  ✓ {h_name} {h_score}-{a_score} {a_name}  [{match_id}]")
        else:
            print(f"  = {h_name} {h_score}-{a_score} {a_name}  (sin cambio)")

    # ── Guardar en Firebase si hubo cambios ───────────────────────────────────
    if updated:
        import datetime
        ref.update({
            "results": results,
            "lastSync": datetime.datetime.utcnow().isoformat() + "Z"
        })
        print("Firebase actualizado ✓")
    else:
        print("Sin cambios, no se escribió en Firebase.")

if __name__ == "__main__":
    main()
