import os, json, datetime
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    cred_json = json.loads(os.environ["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(cred_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    ref = db.collection("quiniela").document("data")

    doc = ref.get()
    if not doc.exists:
        print("❌ No hay datos en Firebase")
        return

    data = doc.to_dict()
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    filename = f"backup_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Backup guardado: {filename}")
    print(f"   Usuarios: {data.get('users', [])}")
    print(f"   Resultados guardados: {len(data.get('results', {}))}")
    print(f"   Pronósticos: {list(data.get('preds', {}).keys())}")

if __name__ == "__main__":
    main()
