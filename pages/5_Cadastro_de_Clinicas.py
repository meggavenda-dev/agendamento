import streamlit as st
from src.db import clinics_upsert, clinics_get_by_id
from src.importers import parse_clinics_excel

st.header("🏥 Cadastro de Clínicas")

tab1, tab2 = st.tabs(["📥 Importar Excel", "✍️ Cadastro/Editar Manual"])

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
    st.subheader("Buscar por código (IDCLINICA)")
    clinic_id = st.number_input("ID da Clínica", min_value=1, step=1, format="%d")

    
    if st.button("Buscar"):
        clinic = clinics_get_by_id(int(clinic_id))
    
        if not clinic:
            st.warning("Clínica não encontrada. Você pode cadastrar abaixo.")
            clinic = {"clinic_id": int(clinic_id), "legal_name": "", "status": "Prospect"}
    
        with st.form("clinic_form"):
            legal_name = st.text_input("Razão Social (NomePJ)", value=clinic.get("legal_name", ""))
            trade_name = st.text_input("Nome Fantasia", value=clinic.get("trade_name", "") or "")
            cnpj = st.text_input("CNPJ", value=clinic.get("cnpj", "") or "")
            phone = st.text_input("Telefone", value=clinic.get("phone", "") or "")
            email = st.text_input("Email", value=clinic.get("email", "") or "")
            website = st.text_input("Website", value=clinic.get("website", "") or "")
    
            clinic_status = st.selectbox(
                "Status comercial da clínica",
                ["Prospect", "Em negociação", "Ativo", "Perdido"],
                index=["Prospect", "Em negociação", "Ativo", "Perdido"].index(clinic.get("status") or "Prospect")
            )
    
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
                "clinic_id": int(clinic_id),
                "legal_name": legal_name.strip(),
                "trade_name": trade_name.strip() or None,
                "cnpj": cnpj.strip() or None,
                "phone": phone.strip() or None,
                "email": email.strip() or None,
                "website": website.strip() or None,
                "status": clinic_status,
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
            st.success("Clínica salva/atualizada com sucesso!")
            st.rerun()

