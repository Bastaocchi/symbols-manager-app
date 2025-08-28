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
th:nth-child(6), td:nth-child(6) { width: 120px !important; }
th:nth-child(7), td:nth-child(7) { width: 100px !important; }
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

SHEET_ID = "1NMCkkcrTFOm1ZoOiImzzRRFd6NEn5kMPTkuc5j_3DcQ"
worksheet = client.open_by_key(SHEET_ID).sheet1  # primeira aba

# =========================
# FUNÇÕES AUXILIARES
# =========================
def load_symbols():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    # Remover colunas "Column X" extras
    df = df[[col for col in df.columns if not col.startswith("Column")]]

    # Padronizar coluna TAGS
    df = df.rename(columns={c: "TAGS" for c in df.columns if c.lower() in ["tag", "tags"]})
    if "TAGS" not in df.columns:
        df["TAGS"] = ""

    return df

def update_tag(symbol, tag_value):
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    # Padronizar coluna TAGS
    df = df.rename(columns={c: "TAGS" for c in df.columns if c.lower() in ["tag", "tags"]})
    if "TAGS" not in df.columns:
        st.error("A planilha não contém a coluna 'TAGS'.")
        return

    try:
        row_idx = df.index[df["Symbol"] == symbol][0] + 2  # +2 por causa do header
        col_idx = df.columns.get_loc("TAGS") + 1
        worksheet.update_cell(row_idx, col_idx, tag_value)
        st.success(f"Tag '{tag_value}' adicionada ao símbolo {symbol}")
    except IndexError:
        st.error(f"Símbolo {symbol} não encontrado na planilha")

# =========================
# MAIN APP
# =========================
def main():
    st.markdown('<h1 style="text-align:center; font-size:3rem; margin-bottom:2rem;">Gerenciador de Símbolos</h1>', unsafe_allow_html=True)

    # Botão Recarregar
    if st.button("🔄 Recarregar Planilha"):
        st.cache_data.clear()
        st.rerun()

    df = load_symbols()

    st.markdown("---")
    st.subheader("Resumo dos Dados")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Total de Símbolos", len(df))
    with col2: st.metric("Setores SPDR", len(df['Sector_SPDR'].dropna().unique()) if 'Sector_SPDR' in df.columns else 0)
    with col3: st.metric("Indústrias", len(df['TradingView_Industry'].dropna().unique()) if 'TradingView_Industry' in df.columns else 0)
    with col4: st.metric("Com Tags", len(df[df['TAGS'].str.strip() != ""]) if 'TAGS' in df.columns else 0)
    with col5: st.metric("Status", "Carregado", delta="Online")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Visualizar", "Adicionar", "Tags"])

    # TAB VISUALIZAR
    with tab1:
        st.subheader("Visualizar Símbolos")

        # --- Filtros ---
        col1, col2, col3 = st.columns(3)
        with col1:
            sector_filter = st.selectbox(
                "Filtrar por Setor:",
                ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"]
            )
        with col2:
            etf_filter = st.selectbox(
                "Filtrar por ETF:",
                ["Todos"] + sorted(df['ETF_Symbol'].dropna().unique().tolist()) if 'ETF_Symbol' in df.columns else ["Todos"]
            )
        with col3:
            tag_filter = st.selectbox(
                "Filtrar por Tag:",
                ["Todas"] + sorted([t for t in df['TAGS'].dropna().unique() if t.strip()]) if 'TAGS' in df.columns else ["Todas"]
            )

        # --- Busca global ---
        search_term = st.text_input("🔍 Buscar em qualquer coluna:")

        # --- Aplicar filtros ---
        filtered_df = df.copy()
        if sector_filter != "Todos" and 'Sector_SPDR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sector_SPDR'] == sector_filter]
        if etf_filter != "Todos" and 'ETF_Symbol' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['ETF_Symbol'] == etf_filter]
        if tag_filter != "Todas" and 'TAGS' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['TAGS'] == tag_filter]
        if search_term:
            mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        st.info(f"Mostrando {len(filtered_df)} de {len(df)} símbolos")
        
        # Renderizar tabela como HTML para controlar a fonte
        if len(filtered_df) > 0:
            html_table = "<table style='width:100%; border-collapse: collapse;'>"
            
            # Cabeçalho
            html_table += "<tr>"
            for col in filtered_df.columns:
                html_table += f"<th style='background-color: #2a323b; color: white; font-size: 20px; font-weight: bold; text-align: center; padding: 14px; border: 1px solid #444;'>{col}</th>"
            html_table += "</tr>"
            
            # Linhas de dados
            for idx, row in filtered_df.iterrows():
                bg_color = "#15191f" if idx % 2 == 0 else "#1b1f24"
                html_table += f"<tr style='background-color: {bg_color};'>"
                for col in filtered_df.columns:
                    value = str(row[col]) if pd.notna(row[col]) else ""
                    color = "#ffcc00" if col == "TAGS" else "#eee"
                    html_table += f"<td style='font-size: 18px; text-align: center; color: {color}; padding: 12px; border: 1px solid #444;'>{value}</td>"
                html_table += "</tr>"
            
            html_table += "</table>"
            
            # Tabela sem container de scroll - rola junto com a página
            st.markdown(html_table, unsafe_allow_html=True)

    # TAB ADICIONAR (rascunho)
    with tab2:
        st.subheader("Adicionar Novo Símbolo")
        st.info("Funcionalidade em construção")

    # TAB TAGS LIVRES (multi símbolos)
    with tab3:
        st.subheader("Gerenciar Tags")
        if len(df) > 0:
            symbols_choice = st.multiselect("Escolha um ou mais símbolos:", df["Symbol"].unique())
            new_tag = st.text_input("Digite a tag (livre):")

            if st.button("Aplicar Tag"):
                if new_tag.strip() and symbols_choice:
                    for sym in symbols_choice:
                        update_tag(sym, new_tag.strip())
                else:
                    st.error("Selecione pelo menos um símbolo e digite uma tag válida")

if __name__ == "__main__":
    main()
