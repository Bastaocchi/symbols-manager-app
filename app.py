import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf

# Configuração da página
st.set_page_config(
    page_title="Gerenciador de Símbolos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===== CSS GLOBAL =====
st.markdown("""
<style>
/* Fonte geral da tabela */
table, th, td {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    border: none !important;
    outline: none !important;
}

/* Forçar tabela a ocupar a tela */
table {
    width: 100% !important;
    table-layout: fixed !important;
    border-collapse: collapse !important;
}

/* Cabeçalho */
th {
    background-color: #2a323b !important;
    color: white !important;
    font-size: 20px !important;
    font-weight: bold !important;
    text-align: center !important;
    padding: 12px !important;
}

/* Células */
td {
    font-size: 18px !important;
    text-align: center !important;
    color: #eee !important;
    padding: 10px !important;
}

/* Linhas zebra */
tr:nth-child(odd) {
    background-color: #15191f !important;
}
tr:nth-child(even) {
    background-color: #1b1f24 !important;
}

/* Symbol */
th:nth-child(1), td:nth-child(1) {
    width: 100px !important;
}

/* Company */
th:nth-child(2), td:nth-child(2) {
    min-width: 200px !important;
    max-width: 200px !important;
    width: 200px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    text-align: left !important;
}

/* Sector SPDR */
th:nth-child(3), td:nth-child(3) {
    width: 220px !important;
}

/* ETF Symbol */
th:nth-child(4), td:nth-child(4) {
    width: 120px !important;
}

/* Tag */
th:nth-child(5), td:nth-child(5) {
    min-width: 220px !important;
    max-width: 220px !important;
    width: 220px !important;
    font-size: 22px !important;
    color: #ffcc00 !important;
}
</style>
""", unsafe_allow_html=True)

# ===== Funções auxiliares =====
@st.cache_data(ttl=300)
def load_symbols_from_sheets(sheet_url):
    try:
        if '/edit' in sheet_url:
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            if 'gid=' in sheet_url:
                gid = sheet_url.split('gid=')[1].split('#')[0].split('&')[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            else:
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            csv_url = sheet_url

        df = pd.read_csv(csv_url)
        if 'Column 1' in df.columns:
            df = df.rename(columns={'Column 1': 'Tag'})
        if 'Tag' not in df.columns:
            df['Tag'] = ""
        df = df.fillna("")
        df = df.dropna(how='all')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Google Sheets: {e}")
        return None

@st.cache_data(ttl=3600)
def validate_ticker(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('regularMarketPrice') is not None or info.get('symbol') == symbol
    except:
        return False

@st.cache_data(ttl=3600)
def get_ticker_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            'company': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'market_cap': info.get('marketCap', 0)
        }
    except:
        return None

# ===== Renderizador simples =====
def render_html_table_visualizar(df):
    return df.to_html(escape=False, index=False)

# ===== MAIN =====
def main():
    st.markdown('<h1 style="text-align:center; font-size:3rem; margin-bottom:2rem;">📊 Gerenciador de Símbolos</h1>', unsafe_allow_html=True)

    # Configurações
    st.subheader("⚙️ Configurações")
    col1, col2 = st.columns([3, 1])
    with col1:
        sheet_url = st.text_input(
            "🔗 URL do Google Sheets:",
            value="https://docs.google.com/spreadsheets/d/1NMCkkcrTFOm1ZoOiImzzRRFd6NEn5kMPTkuc5j_3DcQ/edit?gid=744859441#gid=744859441",
            help="Cole a URL do seu Google Sheets público"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Recarregar", type="primary"):
            st.cache_data.clear()
            st.rerun()

    if not sheet_url:
        st.warning("⚠️ Insira a URL do Google Sheets")
        return

    df = load_symbols_from_sheets(sheet_url)
    if df is None:
        return

    # Resumo
    st.markdown("---")
    st.subheader("📊 Resumo dos Dados")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("📈 Total de Símbolos", len(df))
    with col2: st.metric("🏭 Setores SPDR", len(df['Sector_SPDR'].dropna().unique()) if 'Sector_SPDR' in df.columns else 0)
    with col3: st.metric("🔬 Indústrias", len(df['TradingView_Industry'].dropna().unique()) if 'TradingView_Industry' in df.columns else 0)
    with col4: st.metric("🏷️ Com Tags", len(df[df['Tag'].str.strip() != ""]) if 'Tag' in df.columns else 0)
    with col5: st.metric("✅ Status", "Carregado", delta="Online")

    # Tabs
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visualizar", "➕ Adicionar", "🏷️ Tags", "📊 Estatísticas"])

    # ===== Visualizar =====
    with tab1:
        st.subheader("📋 Visualizar Símbolos")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sector_filter = st.selectbox("Filtrar Setor", ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"])
        with col2:
            etf_filter = st.selectbox("Filtrar ETF", ["Todos"] + sorted(df['ETF_Symbol'].dropna().unique().tolist()) if 'ETF_Symbol' in df.columns else ["Todos"])
        with col3:
            tag_filter = st.selectbox("Filtrar Tag", ["Todas"] + sorted([t for t in df['Tag'].dropna().unique() if t.strip()]) if 'Tag' in df.columns else ["Todas"])
        with col4:
            search_term = st.text_input("🔍 Buscar Symbol/Company:")

        filtered_df = df.copy()
        if sector_filter != "Todos" and 'Sector_SPDR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Sector_SPDR'] == sector_filter]
        if etf_filter != "Todos" and 'ETF_Symbol' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['ETF_Symbol'] == etf_filter]
        if tag_filter != "Todas" and 'Tag' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Tag'] == tag_filter]
        if search_term:
            mask = (
                filtered_df['Symbol'].str.contains(search_term, case=False, na=False) |
                filtered_df['Company'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]

        st.info(f"📊 Mostrando {len(filtered_df)} de {len(df)} símbolos")

        display_columns = ['Symbol', 'Company', 'Sector_SPDR', 'ETF_Symbol', 'Tag']
        available_columns = [c for c in display_columns if c in filtered_df.columns]

        if len(filtered_df) > 0:
            display_df = filtered_df[available_columns].copy()

            st.markdown(render_html_table_visualizar(display_df), unsafe_allow_html=True)

            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"symbols_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Nenhum símbolo encontrado.")

    # ===== Outras abas =====
    with tab2:
        st.subheader("➕ Adicionar Novo Símbolo")
        st.info("🔧 Aba em desenvolvimento")

    with tab3:
        st.subheader("🏷️ Gerenciar Tags")
        st.info("🔧 Aba em desenvolvimento")

    with tab4:
        st.subheader("📊 Estatísticas Detalhadas")
        st.write("🔧 Em breve gráficos bonitos aqui 😉")

if __name__ == "__main__":
    main()
