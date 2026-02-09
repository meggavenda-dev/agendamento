# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date

from src.db import clinics_upsert, clinics_get_by_id
from src.importers import parse_clinics_excel
from src.constants import LEAD_STATUSES, INTEREST_LEVELS

st.header("Clínicas")

tab1, tab2 = st.tabs(["Importar Excel", "Cadastro/Editar Manual"])

with tab1:
    st.subheader("Importar clínicas do Excel (IDCLINICA + NomePJ)")
    file = st.file_uploader("Selecione o Excel", type=["xlsx"])
    if file:
        rows = parse_clinics_excel(file)
        st.write(f"Prévia: {len(rows)} registros")
        st.dataframe(rows[:30], use_container_width=True)
        if st.button("Importar / Atualizar no banco", type="primary"):
            clinics_upsert(rows)
            st.success("Importação concluída!")

with tab2:
    st.subheader("Buscar por IDCLINICA")
    clinic_id = st.number_input("IDCLINICA", min_value=1, step=1, format="%d")

    if st.button("Buscar"):
        clinic = clinics_get_by_id(int(clinic_id))
        if not clinic:
            st.warning("Clínica não encontrada. Você pode cadastrar abaixo.")
            clinic = {
                "clinic_id": int(clinic_id),
                "legal_name": "",
                "lead_status": "Novo",
                "interest_level": "Médio",
                "probability": 0.30,
            }
        st.session_state._clinic = clinic

    clinic = st.session_state.get("_clinic")
    if clinic:
        with st.form("clinic_form"):
            st.markdown("### Identificação")
            legal_name = st.text_input("Razão Social (NomePJ)", value=clinic.get("legal_name", ""))
            trade_name = st.text_input("Nome Fantasia", value=clinic.get("trade_name", "") or "")
            cnpj = st.text_input("CNPJ", value=clinic.get("cnpj", "") or "")

            st.markdown("### Comercial")
            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                lead_status = st.selectbox("Status do lead", LEAD_STATUSES, index=LEAD_STATUSES.index(clinic.get("lead_status") or "Novo"))
            with c2:
                interest = st.selectbox("Interesse", INTEREST_LEVELS, index=INTEREST_LEVELS.index(clinic.get("interest_level") or "Médio"))
            with c3:
                probability = st.slider("Probabilidade", 0.0, 1.0, float(clinic.get("probability") or 0.30), 0.05)

            potential_value = st.number_input("Valor potencial mensal (R$)", min_value=0.0, step=500.0, value=float(clinic.get("potential_value") or 0.0))
            competitor = st.text_input("Concorrente atual", value=clinic.get("competitor", "") or "")
            loss_reason = st.text_input("Motivo de perda", value=clinic.get("loss_reason", "") or "")

            st.markdown("### Próxima ação")
            next_action = st.text_input("Próxima ação", value=clinic.get("next_action", "") or "", placeholder="Ex: enviar proposta atualizada")
            # se existir, tenta converter. caso contrário, hoje
            def _date_or_today(v):
                if not v:
                    return date.today()
                try:
                    return date.fromisoformat(str(v))
                except Exception:
                    return date.today()
            next_action_due = st.date_input("Prazo da próxima ação", value=_date_or_today(clinic.get("next_action_due")))

            st.markdown("### Contatos")
            decisor_name = st.text_input("Decisor — nome", value=clinic.get("decisor_name", "") or "")
            decisor_role = st.text_input("Decisor — cargo", value=clinic.get("decisor_role", "") or "")
            decisor_phone = st.text_input("Decisor — telefone", value=clinic.get("decisor_phone", "") or "")
            decisor_whatsapp = st.text_input("Decisor — WhatsApp", value=clinic.get("decisor_whatsapp", "") or "")
            decisor_email = st.text_input("Decisor — e-mail", value=clinic.get("decisor_email", "") or "")

            st.markdown("### Endereço")
            address_street = st.text_input("Logradouro", value=clinic.get("address_street", "") or "")
            address_number = st.text_input("Número", value=clinic.get("address_number", "") or "")
            address_complement = st.text_input("Complemento", value=clinic.get("address_complement", "") or "")
            address_district = st.text_input("Bairro", value=clinic.get("address_district", "") or "")
            address_city = st.text_input("Cidade", value=clinic.get("address_city", "") or "")
            address_state = st.text_input("UF", value=clinic.get("address_state", "") or "")
            address_zip = st.text_input("CEP", value=clinic.get("address_zip", "") or "")

            notes = st.text_area("Observações", value=clinic.get("notes", "") or "", height=120)

            saved = st.form_submit_button("Salvar", type="primary")

        if saved:
            payload = {
                "clinic_id": int(clinic.get("clinic_id")),
                "legal_name": legal_name.strip(),
                "trade_name": trade_name.strip() or None,
                "cnpj": cnpj.strip() or None,
                "lead_status": lead_status,
                "interest_level": interest,
                "probability": float(probability),
                "potential_value": float(potential_value) if potential_value else None,
                "competitor": competitor.strip() or None,
                "loss_reason": loss_reason.strip() or None,
                "next_action": next_action.strip() or None,
                "next_action_due": next_action_due.isoformat() if next_action_due else None,
                "decisor_name": decisor_name.strip() or None,
                "decisor_role": decisor_role.strip() or None,
                "decisor_phone": decisor_phone.strip() or None,
                "decisor_whatsapp": decisor_whatsapp.strip() or None,
                "decisor_email": decisor_email.strip() or None,
                "address_street": address_street.strip() or None,
                "address_number": address_number.strip() or None,
                "address_complement": address_complement.strip() or None,
                "address_district": address_district.strip() or None,
                "address_city": address_city.strip() or None,
                "address_state": address_state.strip() or None,
                "address_zip": address_zip.strip() or None,
                "notes": notes.strip() or None,
            }
            clinics_upsert([payload])
            st.success("Salvo!")
            st.session_state._clinic = {**clinic, **payload}
            st.rerun()
