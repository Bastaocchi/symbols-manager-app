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
# Mapeamento de setores SPDR com números
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
    """Extrai todas as tags individuais do DataFrame, separando por vírgula, espaço, etc."""
    all_tags = set()
    if 'TAGS' in df.columns:
        for tags_cell in df['TAGS'].dropna():
            if str(tags_cell).strip():
                # Separar por vírgula, ponto e vírgula, pipe ou espaço simples
                import re
                tags_list = re.split(r'[,;|\s]+', str(tags_cell))
                for tag in tags_list:
                    tag = tag.strip()
                    if tag:
                        all_tags.add(tag)
    return sorted(list(all_tags))
    """Remove acentos e converte para minúsculo para busca flexível"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    return text

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

def add_symbol_to_sheet(symbol_data):
    """Adiciona um novo símbolo à planilha"""
    try:
        # Obter dados atuais para pegar as colunas
        current_data = worksheet.get_all_records()
        df_current = pd.DataFrame(current_data)
        
        if len(df_current) == 0:
            st.error("Não foi possível obter a estrutura da planilha")
            return False
            
        # Criar nova linha com os dados
        new_row = []
        for col in df_current.columns:
            if col in symbol_data:
                new_row.append(symbol_data[col])
            else:
                new_row.append("")  # Valor vazio para colunas não fornecidas
        
        # Adicionar a nova linha na planilha
        worksheet.append_row(new_row)
        st.success(f"Símbolo {symbol_data.get('Symbol', 'N/A')} adicionado com sucesso!")
        return True
        
    except Exception as e:
        st.error(f"Erro ao adicionar símbolo: {str(e)}")
        return False

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
    st.markdown('<h6 style="text-align:left; font-size:1rem; margin-bottom:1rem; color: #ccc;">Gerenciador de Símbolos</h6>', unsafe_allow_html=True)

    # Botão Recarregar
    if st.button("🔄 Recarregar Planilha"):
        st.cache_data.clear()
        st.rerun()

    df = load_symbols()

    tab1, tab2, tab3, tab4 = st.tabs(["Visualizar", "Adicionar", "Tags", "Resumo"])

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
                "Filtrar por Setor SPDR:",
                ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"]
            )
        with col3:
            # Filtro de tags individuais
            all_individual_tags = get_all_tags(df)
            tag_filter = st.selectbox(
                "Filtrar por Tag:",
                ["Todas"] + all_individual_tags
            )

        # --- Busca global ---
        search_term = st.text_input("🔍 Buscar em qualquer coluna:")

        # --- Aplicar filtros ---
        filtered_df = df.copy()
        if sector_filter != "Todos" and 'Sector_SPDR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sector_SPDR'] == sector_filter]
        if etf_filter != "Todos" and 'Sector_SPDR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sector_SPDR'] == etf_filter]
        if tag_filter != "Todas" and 'TAGS' in filtered_df.columns:
            # Filtrar linhas que contêm a tag específica
            mask = filtered_df['TAGS'].apply(
                lambda tags_cell: tag_filter in [tag.strip() for tag in re.split(r'[,;|\s]+', str(tags_cell)) if tag.strip()]
                if pd.notna(tags_cell) else False
            )
            filtered_df = filtered_df[mask]
        if search_term:
            # Normalizar o termo de busca (remover acentos e converter para minúsculo)
            normalized_search = normalize_text(search_term)
            
            # Aplicar busca flexível - normaliza cada célula e compara
            mask = filtered_df.apply(
                lambda row: row.apply(
                    lambda cell: normalized_search in normalize_text(cell)
                ).any(), 
                axis=1
            )
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

    # TAB ADICIONAR
    with tab2:
        st.subheader("Adicionar Novo Símbolo")
        
        # Formulário para adicionar novo símbolo
        with st.form("add_symbol_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                symbol = st.text_input("Símbolo *", placeholder="Ex: AAPL")
                company = st.text_input("Nome da Empresa *", placeholder="Ex: Apple Inc")
                tradingview_sector = st.text_input("TradingView Setor", placeholder="Ex: Technology")
                tradingview_industry = st.text_input("TradingView Indústria", placeholder="Ex: Consumer Electronics")
                
            with col2:
                # Selectbox para setores SPDR com nomes descritivos
                sector_options = [f"{code} - {info['name']}" if code else "Não selecionado" 
                                for code, info in SECTOR_MAPPING.items()]
                
                selected_sector = st.selectbox(
                    "Setor SPDR",
                    sector_options,
                    help="Selecione um setor SPDR"
                )
                
                # Extrair o código do setor selecionado para salvar no formato completo
                if selected_sector == "Não selecionado":
                    sector_spdr_value = ""
                else:
                    sector_spdr_value = selected_sector  # Salva "XLV - Health Care"
                
                tags = st.text_input("Tags", placeholder="Ex: tech, growth")
            
            st.markdown("**Campos obrigatórios marcados com ***")
            
            # Botões do formulário
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submitted = st.form_submit_button("✅ Adicionar Símbolo", use_container_width=True)
            with col_btn2:
                clear_form = st.form_submit_button("🗑️ Limpar Formulário", use_container_width=True)
            
            if submitted:
                # Validação dos campos obrigatórios
                if not symbol.strip():
                    st.error("❌ Campo 'Símbolo' é obrigatório!")
                elif not company.strip():
                    st.error("❌ Campo 'Nome da Empresa' é obrigatório!")
                elif symbol.upper() in df['Symbol'].str.upper().values:
                    st.error(f"❌ Símbolo '{symbol.upper()}' já existe na planilha!")
                else:
                    # Preparar dados para adicionar
                    symbol_data = {
                        'Symbol': symbol.upper().strip(),
                        'Company': company.strip(),
                        'TradingView_Sector': tradingview_sector.strip(),
                        'TradingView_Industry': tradingview_industry.strip(),
                        'Sector_SPDR': sector_spdr_value,
                        'TAGS': tags.strip()
                    }
                    
                    # Adicionar à planilha
                    if add_symbol_to_sheet(symbol_data):
                        st.balloons()
                        st.info("💡 Clique em 'Recarregar Planilha' no topo da página para ver o novo símbolo na lista")
            
            if clear_form:
                st.rerun()
        
        # Seção de informações
        st.markdown("---")
        st.subheader("ℹ️ Informações")
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown("""
            **Campos Obrigatórios:**
            - **Símbolo**: Código do ativo (ex: AAPL, MSFT)
            - **Nome da Empresa**: Nome completo da empresa
            """)
            
        with col_info2:
            st.markdown("""
            **Dicas:**
            - Use símbolos em MAIÚSCULO
            - Verifique se o símbolo já não existe
            - Preencha o máximo de campos possível
            """)
        
        # Estatísticas de adição
        if 'Sector_SPDR' in df.columns:
            st.markdown("**📊 Setores Disponíveis:**")
            sectors = df['Sector_SPDR'].value_counts()
            for sector, count in sectors.head(5).items():
                if sector and str(sector).strip():
                    st.text(f"• {sector}: {count} símbolos")

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

    # TAB RESUMO
    with tab4:
        st.subheader("Resumo dos Dados")
        
        # Métricas principais
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Total de Símbolos", len(df))
        with col2: st.metric("Setores SPDR", len(df['Sector_SPDR'].dropna().unique()) if 'Sector_SPDR' in df.columns else 0)
        with col3: st.metric("Indústrias", len(df['TradingView_Industry'].dropna().unique()) if 'TradingView_Industry' in df.columns else 0)
        with col4: st.metric("Com Tags", len(df[df['TAGS'].str.strip() != ""]) if 'TAGS' in df.columns else 0)
        with col5: st.metric("Status", "Carregado", delta="Online")
        
        st.markdown("---")
        
        # Seções detalhadas
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Top 10 Setores SPDR")
            if 'Sector_SPDR' in df.columns:
                sectors = df['Sector_SPDR'].value_counts().head(10)
                for sector, count in sectors.items():
                    if sector and str(sector).strip():
                        st.text(f"• {sector}: {count} símbolos")
            
            st.markdown("---")
            
            st.subheader("🏷️ Tags Mais Usadas")
            if 'TAGS' in df.columns:
                tags = df[df['TAGS'].str.strip() != '']['TAGS'].value_counts().head(10)
                for tag, count in tags.items():
                    if tag and str(tag).strip():
                        st.text(f"• {tag}: {count} símbolos")
        
        with col_right:
            st.subheader("🏭 Top 10 Indústrias")
            if 'TradingView_Industry' in df.columns:
                industries = df['TradingView_Industry'].value_counts().head(10)
                for industry, count in industries.items():
                    if industry and str(industry).strip():
                        st.text(f"• {industry}: {count} símbolos")
            
            st.markdown("---")
            
            st.subheader("📈 Estatísticas Gerais")
            st.text(f"• Símbolos com tags: {len(df[df['TAGS'].str.strip() != '']) if 'TAGS' in df.columns else 0}")
            st.text(f"• Símbolos sem tags: {len(df[df['TAGS'].str.strip() == '']) if 'TAGS' in df.columns else 0}")
            if 'Company' in df.columns:
                st.text(f"• Empresas únicas: {len(df['Company'].dropna().unique())}")
            if 'Symbol' in df.columns:
                st.text(f"• Símbolos únicos: {len(df['Symbol'].dropna().unique())}")

if __name__ == "__main__":
    main()
