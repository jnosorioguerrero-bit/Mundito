import os, json, requests, datetime
import firebase_admin
from firebase_admin import credentials, firestore

FDATA_TOKEN = os.environ["FDATA_TOKEN"]
FDATA_URL   = "https://api.football-data.org/v4/competitions/WC/matches?season=2026"

# Mapeo español (quiniela) → inglés (API)
# Solo los que difieren del inglés directo
ES_TO_API = {
    "México":          "Mexico",
    "Sudáfrica":       "South Africa",
    "Corea del Sur":   "South Korea",
    "Rep. Checa":      "Czechia",
    "Canadá":          "Canada",
    "Bosnia y Herz.":  "Bosnia-Herzegovina",
    "Estados Unidos":  "United States",
    "Catar":           "Qatar",
    "Suiza":           "Switzerland",
    "Marruecos":       "Morocco",
    "Haití":           "Haiti",
    "Escocia":         "Scotland",
    "Turquía":         "Turkey",
    "Alemania":        "Germany",
    "Curazao":         "Curaçao",
    "Países Bajos":    "Netherlands",
    "Japón":           "Japan",
    "Costa de Marfil": "Ivory Coast",
    "Suecia":          "Sweden",
    "Túnez":           "Tunisia",
    "España":          "Spain",
    "Cabo Verde":      "Cape Verde",
    "Bélgica":         "Belgium",
    "Egipto":          "Egypt",
    "Arabia Saudita":  "Saudi Arabia",
    "Irán":            "Iran",
    "Nueva Zelanda":   "New Zealand",
    "Francia":         "France",
    "Irak":            "Iraq",
    "Noruega":         "Norway",
    "Argelia":         "Algeria",
    "Jordania":        "Jordan",
    "RD Congo":        "DR Congo",
    "Inglaterra":      "England",
    "Croacia":         "Croatia",
    "Panamá":          "Panama",
    "Uzbekistán":      "Uzbekistan",
    "Brasil":          "Brazil",
    "Uruguay":         "Uruguay",
    "Senegal":         "Senegal",
    "Colombia":        "Colombia",
    "Ecuador":         "Ecuador",
    "Argentina":       "Argentina",
    "Austria":         "Austria",
    "Ghana":           "Ghana",
    "Paraguay":        "Paraguay",
    "Portugal":        "Portugal",
    "Chile":           "Chile",
}

def to_api(name):
    return ES_TO_API.get(name, name)

# Partidos quiniela: (home_api, away_api) → id
QUINIELA_MATCHES = {}
QUINIELA_RAW = [
    ("México","Sudáfrica","a1"), ("Corea del Sur","Rep. Checa","a2"),
    ("Canadá","Bosnia y Herz.","b1"), ("Estados Unidos","Paraguay","d1"),
    ("Catar","Suiza","b2"), ("Brasil","Marruecos","c1"),
    ("Haití","Escocia","c2"), ("Australia","Turquía","d2"),
    ("Alemania","Curazao","e1"), ("Países Bajos","Japón","f1"),
    ("Costa de Marfil","Ecuador","e2"), ("Suecia","Túnez","f2"),
    ("España","Cabo Verde","h1"), ("Bélgica","Egipto","g1"),
    ("Arabia Saudita","Uruguay","h2"), ("Irán","Nueva Zelanda","g2"),
    ("Francia","Senegal","i1"), ("Irak","Noruega","i2"),
    ("Argentina","Argelia","j1"), ("Austria","Jordania","j2"),
    ("Portugal","RD Congo","k1"), ("Inglaterra","Croacia","l1"),
    ("Ghana","Panamá","l2"), ("Uzbekistán","Colombia","k2"),
    ("Rep. Checa","Sudáfrica","a3"), ("Suiza","Bosnia y Herz.","b3"),
    ("Canadá","Catar","b4"), ("México","Corea del Sur","a4"),
    ("Turquía","Paraguay","d3"), ("Escocia","Marruecos","c3"),
    ("Brasil","Haití","c4"), ("Estados Unidos","Australia","d4"),
    ("Túnez","Japón","f3"), ("Países Bajos","Suecia","f4"),
    ("Alemania","Costa de Marfil","e3"), ("Ecuador","Curazao","e4"),
    ("España","Arabia Saudita","h3"), ("Bélgica","Irán","g3"),
    ("Uruguay","Cabo Verde","h4"), ("Nueva Zelanda","Egipto","g4"),
    ("Francia","Irak","i3"), ("Noruega","Senegal","i4"),
    ("Argentina","Austria","j3"), ("Jordania","Argelia","j4"),
    ("Portugal","Uzbekistán","k3"), ("Colombia","RD Congo","k4"),
    ("Inglaterra","Ghana","l3"), ("Panamá","Croacia","l4"),
    ("Sudáfrica","Corea del Sur","a5"), ("México","Rep. Checa","a6"),
    ("Bosnia y Herz.","Catar","b6"), ("Suiza","Canadá","b5"),
    ("Marruecos","Haití","c6"), ("Brasil","Escocia","c5"),
    ("Paraguay","Australia","d5"), ("Turquía","Estados Unidos","d6"),
    ("Curazao","Costa de Marfil","e5"), ("Ecuador","Alemania","e6"),
    ("Japón","Suecia","f5"), ("Túnez","Países Bajos","f6"),
    ("Egipto","Irán","g5"), ("Nueva Zelanda","Bélgica","g6"),
    ("Panamá","Inglaterra","l5"), ("Ghana","Croacia","l6"),
    ("Colombia","Portugal","k5"), ("RD Congo","Uzbekistán","k6"),
    ("Jordania","Argentina","j5"), ("Austria","Argelia","j6"), 
    ("Noruega","Francia","i5"), ("Senegal","Irak","i6"),
    ("Uruguay","España","h5"), ("Cabo Verde","Arabia Saudita","h6"),
]

for h, a, mid in QUINIELA_RAW:
    QUINIELA_MATCHES[(to_api(h), to_api(a))] = mid

def main():
    cred_json = json.loads(os.environ["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(cred_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    ref = db.collection("quiniela").document("data")

    doc = ref.get()
    state = doc.to_dict() if doc.exists else {}
    results = state.get("results", {})

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

    updated = False
    for fm in finished:
        h_api = fm["homeTeam"]["name"]
        a_api = fm["awayTeam"]["name"]
        h_score = fm["score"]["fullTime"]["home"]
        a_score = fm["score"]["fullTime"]["away"]

        match_id = QUINIELA_MATCHES.get((h_api, a_api))
        if not match_id:
            print(f"  ⚠️  Sin mapeo: {h_api} vs {a_api}")
            continue

        existing = results.get(match_id)
        if not existing or existing.get("h") != h_score or existing.get("a") != a_score:
            results[match_id] = {"h": h_score, "a": a_score}
            updated = True
            print(f"  ✓ {h_api} {h_score}-{a_score} {a_api}  [{match_id}]")
        else:
            print(f"  = {h_api} {h_score}-{a_score} {a_api}  (sin cambio)")

    if updated:
        ref.update({
            "results": results,
            "lastSync": datetime.datetime.utcnow().isoformat() + "Z"
        })
        print("Firebase actualizado ✓")
    else:
        print("Sin cambios, no se escribió en Firebase.")

if __name__ == "__main__":
    main()
