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

# CSS global
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    table {
        table-layout: fixed;
        width: 100%;
        border-collapse: collapse;
    }
    th {
        font-size: 18px;
        font-weight: bold;
        padding: 12px;
        background-color: #444;
        color: white;
        text-align: center;
        border: 1px solid #ddd;
    }
    td {
        font-size: 16px;
        padding: 10px;
        text-align: center;
        border: 1px solid #ddd;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Função para carregar dados do Google Sheets
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

        try:
            df = pd.read_csv(csv_url, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_url, encoding='latin1')
        except:
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
        st.info("💡 Verifique se a planilha está pública")
        return None

# Função para validar ticker
@st.cache_data(ttl=3600)
def validate_ticker(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('regularMarketPrice') is not None or info.get('symbol') == symbol
    except:
        return False

# Função para obter informações do ticker
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

def render_html_table(df):
    html_table = df.to_html(escape=False, index=False)
    return html_table

def main():
    st.markdown('<h1 class="main-header">Gerenciador de Símbolos</h1>', unsafe_allow_html=True)
    st.markdown("**Gerencie seus tickers, setores e tags para análise**")

    # Configurações no topo
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
        if st.button("🔄 Recarregar do Sheets", type="primary"):
            st.cache_data.clear()
            st.rerun()

    # Carregar dados
    if sheet_url:
        df = load_symbols_from_sheets(sheet_url)
        if df is not None:
            st.markdown("---")
            st.subheader("📊 Resumo dos Dados")

            col1, col2, col3, col4, col5 = st.columns(5)
            total_symbols = len(df)
            unique_sectors = len(df['TradingView_Sector'].dropna().unique()) if 'TradingView_Sector' in df.columns else 0
            unique_industries = len(df['TradingView_Industry'].dropna().unique()) if 'TradingView_Industry' in df.columns else 0
            symbols_with_tags = len(df[df['Tag'].str.strip() != ""]) if 'Tag' in df.columns else 0
            unique_spdr_sectors = len(df['Sector_SPDR'].dropna().unique()) if 'Sector_SPDR' in df.columns else 0

            with col1: st.metric("📈 Total de Símbolos", total_symbols)
            with col2: st.metric("🏭 Setores SPDR", unique_spdr_sectors)
            with col3: st.metric("🔬 Indústrias", unique_industries)
            with col4: st.metric("🏷️ Com Tags", symbols_with_tags)
            with col5: st.metric("✅ Status", "Carregado", delta="Online")
        else:
            st.error("❌ Não foi possível carregar os dados do Google Sheets")
            return
    else:
        st.warning("⚠️ Por favor, insira a URL do Google Sheets")
        return

    # Tabs principais
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visualizar", "➕ Adicionar", "🏷️ Gerenciar Tags", "📊 Estatísticas Detalhadas"])

    # 📋 Aba Visualizar
    with tab1:
        st.subheader("📋 Visualizar Símbolos")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sector_filter = st.selectbox("Filtrar por Setor:", ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"])
        with col2:
            etf_filter = st.selectbox("Filtrar por ETF:", ["Todos"] + sorted(df['ETF_Symbol'].dropna().unique().tolist()) if 'ETF_Symbol' in df.columns else ["Todos"])
        with col3:
            tag_filter = st.selectbox("Filtrar por Tag:", ["Todas"] + sorted([tag for tag in df['Tag'].dropna().unique() if tag.strip()]) if 'Tag' in df.columns else ["Todas"])
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
        available_columns = [col for col in display_columns if col in filtered_df.columns]

        if len(filtered_df) > 0:
            display_df = filtered_df[available_columns].copy()
            if 'Company' in display_df.columns:
                display_df['Company'] = display_df['Company'].str[:100]

            st.markdown(render_html_table(display_df), unsafe_allow_html=True)

            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"symbols_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("🔍 Nenhum símbolo encontrado com os filtros aplicados")

    # 📊 Estatísticas
    with tab4:
        st.subheader("📊 Estatísticas Detalhadas")

        if 'Sector_SPDR' in df.columns:
            st.subheader("📊 Distribuição por Setor SPDR")
            sector_dist = df['Sector_SPDR'].value_counts().head(10)
            chart_data = pd.DataFrame({
                "Setor": sector_dist.index,
                "Quantidade": sector_dist.values,
                "Percentual": (sector_dist.values / len(df) * 100).round(1).astype(str) + "%"
            })
            st.markdown(render_html_table(chart_data), unsafe_allow_html=True)

        if 'ETF_Symbol' in df.columns:
            st.subheader("📊 Distribuição por ETF")
            etf_dist = df['ETF_Symbol'].value_counts().head(10)
            etf_data = pd.DataFrame({
                "ETF": etf_dist.index,
                "Quantidade": etf_dist.values,
                "Percentual": (etf_dist.values / len(df) * 100).round(1).astype(str) + "%"
            })
            st.markdown(render_html_table(etf_data), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
