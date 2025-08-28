import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import unicodedata
import re

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
th:nth-child(2) { width: 400px !important; text-align: center !important; }
td:nth-child(2) {
    width: 400px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    text-align: center !important;
}
th:nth-child(3), td:nth-child(3) { width: 250px !important; }
th:nth-child(4), td:nth-child(4) { width: 300px !important; }
th:nth-child(5), td:nth-child(5) { width: 200px !important; }
th:nth-child(6), td:nth-child(6) { 
    width: 250px !important;
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

/* Aumentar fonte dos formulários */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    font-size: 18px !important;
    font-family: 'Segoe UI', sans-serif !important;
}

.stTextInput label,
.stSelectbox label,
.stNumberInput label {
    font-size: 16px !important;
    font-weight: 500 !important;
}

.stForm {
    font-size: 16px !important;
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
SECTOR_MAPPING = {
    "": {"number": 0, "name": "Não selecionado"},
    "XLC": {"number": 1, "name": "Communication Services"},
    "XLY": {"number": 2, "name": "Consumer Discretionary"},
    "XLP": {"number": 3, "name": "Consumer Staples"},
    "XLE": {"number": 4, "name": "Energy"},
    "XLF": {"number": 5, "name": "Financials"},
    "XLV": {"number": 6, "name": "Health Care"},
    "XLI": {"number": 7, "name": "Industrials"},
    "XLB": {"number": 8, "name": "Materials"},
    "XLRE": {"number": 9, "name": "Real Estate"},
    "XLK": {"number": 10, "name": "Technology"},
    "XLU": {"number": 11, "name": "Utilities"}
}

def get_all_tags(df):
    all_tags = set()
    if 'TAGS' in df.columns:
        for tags_cell in df['TAGS'].dropna():
            if str(tags_cell).strip():
                tags_list = re.split(r'[,;|\s]+', str(tags_cell))
                for tag in tags_list:
                    tag = tag.strip()
                    if tag:
                        all_tags.add(tag)
    return sorted(list(all_tags))

def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text

def load_symbols():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    df = df[[col for col in df.columns if not col.startswith("Column")]]
    df = df.rename(columns={c: "TAGS" for c in df.columns if c.lower() in ["tag", "tags"]})
    if "TAGS" not in df.columns:
        df["TAGS"] = ""
    return df

def add_symbol_to_sheet(symbol_data):
    try:
        current_data = worksheet.get_all_records()
        df_current = pd.DataFrame(current_data)
        if len(df_current) == 0:
            st.error("Não foi possível obter a estrutura da planilha")
            return False
        new_row = [symbol_data.get(col, "") for col in df_current.columns]
        worksheet.append_row(new_row)
        st.success(f"Símbolo {symbol_data.get('Symbol', 'N/A')} adicionado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar símbolo: {str(e)}")
        return False

def update_tag(symbol, tag_value):
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    df = df.rename(columns={c: "TAGS" for c in df.columns if c.lower() in ["tag", "tags"]})
    if "TAGS" not in df.columns:
        st.error("A planilha não contém a coluna 'TAGS'.")
        return
    try:
        row_idx = df.index[df["Symbol"] == symbol][0] + 2
        col_idx = df.columns.get_loc("TAGS") + 1
        worksheet.update_cell(row_idx, col_idx, tag_value)
        st.success(f"Tag '{tag_value}' adicionada ao símbolo {symbol}")
    except IndexError:
        st.error(f"Símbolo {symbol} não encontrado na planilha")

# =========================
# MAIN APP
# =========================
def main():
    st.markdown('<h6 style="text-align:left; font-size:1rem; margin-bottom:1rem; color: #ccc;">Gerenciador de Símbolos</h6>', unsafe_allow_html=True)

    if st.button("🔄 Recarregar Planilha"):
        st.cache_data.clear()
        st.rerun()

    df = load_symbols()
    tab1, tab2, tab3, tab4 = st.tabs(["Visualizar", "Adicionar", "Tags", "Resumo"])

    with tab1:
        st.subheader("Visualizar Símbolos")
        col1, col2, col3 = st.columns(3)
        with col1:
            sector_filter = st.selectbox("Filtrar por Setor:", ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"])
        with col2:
            etf_filter = st.selectbox("Filtrar por Setor SPDR:", ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"])
        with col3:
            all_individual_tags = get_all_tags(df)
            tag_filter = st.selectbox("Filtrar por Tag:", ["Todas"] + all_individual_tags)

        search_term = st.text_input("🔍 Buscar em qualquer coluna:")

        filtered_df = df.copy()
        if sector_filter != "Todos" and 'Sector_SPDR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sector_SPDR'] == sector_filter]
        if etf_filter != "Todos" and 'Sector_SPDR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sector_SPDR'] == etf_filter]
        if tag_filter != "Todas" and 'TAGS' in filtered_df.columns:
            mask = filtered_df['TAGS'].apply(lambda tags_cell: tag_filter in [tag.strip() for tag in re.split(r'[,;|\s]+', str(tags_cell)) if tag.strip()] if pd.notna(tags_cell) else False)
            filtered_df = filtered_df[mask]
        if search_term:
            normalized_search = normalize_text(search_term)
            mask = filtered_df.apply(lambda row: row.apply(lambda cell: normalized_search in normalize_text(cell)).any(), axis=1)
            filtered_df = filtered_df[mask]

        st.info(f"Mostrando {len(filtered_df)} de {len(df)} símbolos")

        if len(filtered_df) > 0:
            html_table = "<table style='width:100%; border-collapse: collapse;'>"
            html_table += "<tr>"
            for col in filtered_df.columns:
                col_str = str(col) if pd.notna(col) else ""
                html_table += f"<th style='background-color: #2a323b; color: white; font-size: 20px; font-weight: bold; text-align: center; padding: 14px; border: 1px solid #444;'>{col_str}</th>"
            html_table += "</tr>"

            for idx, row in filtered_df.iterrows():
                bg_color = "#15191f" if idx % 2 == 0 else "#1b1f24"
                html_table += f"<tr style='background-color: {bg_color};'>"
                for col in filtered_df.columns:
                    value = str(row[col]) if pd.notna(row[col]) else ""
                    color = "#ffcc00" if str(col) == "TAGS" else "#eee"
                    html_table += f"<td style='font-size: 18px; text-align: center; color: {color}; padding: 12px; border: 1px solid #444;'>{value}</td>"
                html_table += "</tr>"

            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)

    # tab2, tab3, tab4 (sem mudanças, mantém igual ao que você já tem)

if __name__ == "__main__":
    main()
