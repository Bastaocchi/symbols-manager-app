import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Gerenciador de Símbolos",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# CSS GLOBAL
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}
table, th, td {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    border: none !important;
    outline: none !important;
}
table {
    width: 100% !important;
    table-layout: fixed !important;
    border-collapse: collapse !important;
}
th {
    background-color: #2a323b !important;
    color: white !important;
    font-size: 20px !important;
    font-weight: bold !important;
    text-align: center !important;
    padding: 12px !important;
}
td {
    font-size: 18px !important;
    text-align: center !important;
    color: #eee !important;
    padding: 10px !important;
}
tr:nth-child(odd) { background-color: #15191f !important; }
tr:nth-child(even) { background-color: #1b1f24 !important; }
th:nth-child(1), td:nth-child(1) { width: 100px !important; }
th:nth-child(2) { width: 200px !important; text-align: center !important; }
td:nth-child(2) {
    width: 200px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    text-align: left !important;
}
th:nth-child(3), td:nth-child(3) { width: 220px !important; }
th:nth-child(4), td:nth-child(4) { width: 120px !important; }
th:nth-child(5), td:nth-child(5) {
    width: 220px !important;
    font-size: 22px !important;
    color: #ffcc00 !important;
}
div.stButton > button {
    background-color: #2a2f36 !important;
    color: #ffffff !important;
    border: 1px solid #444 !important;
    border-radius: 6px !important;
    padding: 8px 20px !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    font-family: 'Segoe UI', sans-serif !important;
}
div.stButton > button:hover {
    background-color: #3a3f47 !important;
    border-color: #666 !important;
    cursor: pointer;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    color: #ff9900 !important;
    font-weight: 600 !important;
    border-bottom: 3px solid #ff9900 !important;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="false"] {
    color: #aaa !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CONEXÃO COM GOOGLE SHEETS
# =========================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["google_sheets"]), scope)
client = gspread.authorize(creds)

# ID da planilha
SHEET_ID = "1NMCkkcrTFOm1ZoOiImzzRRFd6NEn5kMPTkuc5j_3DcQ"
worksheet = client.open_by_key(SHEET_ID).sheet1  # pega primeira aba

# =========================
# FUNÇÕES AUXILIARES
# =========================
def load_symbols():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if "Tag" not in df.columns:
        df["Tag"] = ""
    return df

def update_tag(symbol, tag_value):
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    if "Symbol" not in df.columns:
        st.error("Sua planilha não tem a coluna 'Symbol'")
        return
    try:
        row_idx = df.index[df["Symbol"] == symbol][0] + 2  # +2 por causa do header
        col_idx = df.columns.get_loc("Tag") + 1
        worksheet.update_cell(row_idx, col_idx, tag_value)
        st.success(f"Tag '{tag_value}' adicionada ao símbolo {symbol}")
    except IndexError:
        st.error("Símbolo não encontrado na planilha")

# =========================
# MAIN APP
# =========================
def main():
    st.markdown('<h1 style="text-align:center; font-size:3rem; margin-bottom:2rem;">Gerenciador de Símbolos</h1>', unsafe_allow_html=True)

    df = load_symbols()

    st.markdown("---")
    st.subheader("Resumo dos Dados")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Total de Símbolos", len(df))
    with col2: st.metric("Setores SPDR", len(df['Sector_SPDR'].dropna().unique()) if 'Sector_SPDR' in df.columns else 0)
    with col3: st.metric("Indústrias", len(df['TradingView_Industry'].dropna().unique()) if 'TradingView_Industry' in df.columns else 0)
    with col4: st.metric("Com Tags", len(df[df['Tag'].str.strip() != ""]) if 'Tag' in df.columns else 0)
    with col5: st.metric("Status", "Carregado", delta="Online")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Visualizar", "Adicionar", "Tags"])

    # TAB VISUALIZAR
    with tab1:
        st.subheader("Visualizar Símbolos")
        st.dataframe(df)

    # TAB ADICIONAR (rascunho)
    with tab2:
        st.subheader("Adicionar Novo Símbolo")
        st.info("Funcionalidade em construção")

    # TAB TAGS LIVRES
    with tab3:
        st.subheader("Gerenciar Tags")
        if len(df) > 0:
            symbol_choice = st.selectbox("Escolha o símbolo:", df["Symbol"].unique())
            new_tag = st.text_input("Digite a tag (livre):")
            if st.button("Aplicar Tag"):
                if new_tag.strip():
                    update_tag(symbol_choice, new_tag.strip())
                else:
                    st.error("Digite uma tag válida")

if __name__ == "__main__":
    main()
