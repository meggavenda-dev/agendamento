# -*- coding: utf-8 -*-
import pandas as pd


def parse_clinics_excel(file) -> list[dict]:
    """Lê um Excel no padrão mínimo (IDCLINICA, NomePJ)."""
    df = pd.read_excel(file, engine="openpyxl")
    df = df.rename(columns={"IDCLINICA": "clinic_id", "NomePJ": "legal_name"})
    if "clinic_id" not in df.columns or "legal_name" not in df.columns:
        raise ValueError("Excel precisa ter colunas IDCLINICA e NomePJ")

    df = df[["clinic_id", "legal_name"]].dropna()
    df["clinic_id"] = (
        df["clinic_id"].astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.strip()
        .astype(int)
    )
    df["legal_name"] = df["legal_name"].astype(str).str.strip()

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "clinic_id": int(r["clinic_id"]),
            "legal_name": r["legal_name"],
            "lead_status": "Novo",
            "interest_level": "Médio",
            "probability": 0.30,
        })
    return rows
