import streamlit as st
import pandas as pd
import gspread
from datetime import date

# --- CONFIGURAÇÕES E CONEXÃO ---

# O Streamlit Cloud vai ler as credenciais de 'gsheets_service_account'
# que você configurará nos Secrets da plataforma (Próxima etapa!)
@st.cache_data(ttl=3600) 
def carregar_dados():
    try:
        # 1. Conexão
        creds = st.secrets["gsheets_service_account"]
        gc = gspread.service_account_from_dict(creds)
        
        # 2. Abrir a Planilha (ALERTA: ATUALIZE ESTA URL)
        PLANILHA_URL = "SUA_URL_DO_GOOGLE_SHEETS_AQUI" 
        sh = gc.open_by_url(PLANILHA_URL)
        worksheet = sh.worksheet("Página1") # OU o nome da sua aba
        
        # 3. Carregar para DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Garante que o ID é número para o Dropdown
        df['ID'] = df['ID'].astype(int) 
        
        return df, worksheet
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar dados! Verifique a URL e as credenciais (Secrets). Detalhe: {e}")
        return pd.DataFrame(), None


def atualizar_status(worksheet, proposta_id, novo_status):
    # Procura a linha com o ID (na coluna 1)
    cell = worksheet.find(str(proposta_id), in_column=1)
    
    # Coluna 5 é a coluna 'Status' (A=1, B=2, C=3, D=4, E=5)
    worksheet.update_cell(cell.row, 5, novo_status)


# --- INTERFACE STREAMLIT ---

# Carrega os dados e o objeto de conexão
df, ws = carregar_dados()

st.set_page_config(page_title="Gestão de Propostas", layout="wide")
st.title("Sistema de Gestão de Propostas 🚀")

if ws is not None:
    # --- Coluna para atualização de status ---
    st.header("1. Atualização de Status Rápida")
    
    col1, col2 = st.columns(2)
    
    propostas_list = df['ID'].unique().tolist()
    proposta_selecionada = col1.selectbox("Selecione a Proposta:", propostas_list)
    
    status_options = ['Em Andamento', 'Concluído', 'Atrasado', 'Cancelado']
    novo_status = col2.selectbox("Novo Status:", status_options)

    if st.button("SALVAR NOVO STATUS", type="primary"):
        try:
            # Chama a função para escrever no Sheets
            atualizar_status(ws, proposta_selecionada, novo_status)
            
            st.success(f"Proposta {proposta_selecionada} atualizada para '{novo_status}' com sucesso!")
            
            # Recarrega a página para mostrar o novo status
            st.cache_data.clear() # Limpa o cache para ler a nova versão
            st.rerun() 
            
        except Exception as e:
            st.error(f"Falha ao salvar: Verifique se o ID existe e se o Sheets está compartilhado com o email de serviço. Detalhe: {e}")

    st.markdown("---")

    # --- Dashboard de Visualização Geral ---
    st.header("2. Prazos e Status dos Colaboradores")
    
    # Tabela Completa
    st.subheader("Visão Detalhada das Propostas")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Gráfico de Status por Colaborador
    st.subheader("Status por Colaborador")
    status_counts = df.groupby('Colaborador')['Status'].value_counts().unstack(fill_value=0)
    st.bar_chart(status_counts)
