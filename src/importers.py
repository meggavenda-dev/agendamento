import pandas as pd

def parse_clinics_excel(file) -> list[dict]:
    df = pd.read_excel(file, engine="openpyxl")
    # Esperado: IDCLINICA, NomePJ
    df = df.rename(columns={"IDCLINICA": "clinic_id", "NomePJ": "legal_name"})
    df = df[["clinic_id", "legal_name"]].dropna()
    df["clinic_id"] = df["clinic_id"].astype(int)
    df["legal_name"] = df["legal_name"].astype(str).str.strip()

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "clinic_id": int(r["clinic_id"]),
            "legal_name": r["legal_name"],
            "status": "Prospect"
        })
    return rows
