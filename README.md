
# PulseAgenda (Streamlit + Supabase)

Este pacote inclui um app Streamlit com autenticação via Supabase, páginas de Agenda/Tarefas,
recorrência de itens, entrada rápida, Pomodoro, configurações, exportação e scripts de workers.

## Como usar
1) Instale deps: `pip install -r requirements.txt`
2) Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha as chaves.
3) Rode as migrações: cole o conteúdo de `sql/migrations.sql` no Supabase SQL Editor.
4) Inicie: `streamlit run Home.py`
