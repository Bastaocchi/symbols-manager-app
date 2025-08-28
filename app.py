import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf

# Configuração da página
st.set_page_config(
    page_title="Gerenciador de Símbolos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para interface moderna
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
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #2196F3;
    }
    table {
        table-layout: fixed;
        width: 100%;
    }
    th, td {
        max-width: 180px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
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
        st.info("💡 Dica: Verifique se a planilha está pública (qualquer pessoa com link pode visualizar)")
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

            with col1:
                st.metric("📈 Total de Símbolos", total_symbols)
            with col2:
                st.metric("🏭 Setores SPDR", unique_spdr_sectors)
            with col3:
                st.metric("🔬 Indústrias", unique_industries)
            with col4:
                st.metric("🏷️ Com Tags", symbols_with_tags)
            with col5:
                st.metric("✅ Status", "Carregado", delta="Online")
        else:
            st.error("❌ Não foi possível carregar os dados do Google Sheets")
            return
    else:
        st.warning("⚠️ Por favor, insira a URL do Google Sheets")
        return

    # Tabs principais
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visualizar", "➕ Adicionar", "🏷️ Gerenciar Tags", "📊 Estatísticas Detalhadas"])

    # ========================
    # 📋 Aba 1 - Visualizar
    # ========================
    with tab1:
        st.subheader("📋 Visualizar Símbolos")

        # Filtros
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            sector_filter = st.selectbox(
                "Filtrar por Setor:",
                ["Todos"] + sorted(df['Sector_SPDR'].dropna().unique().tolist()) if 'Sector_SPDR' in df.columns else ["Todos"],
                key="sector_filter_tab1"
            )

        with col2:
            etf_filter = st.selectbox(
                "Filtrar por ETF:",
                ["Todos"] + sorted(df['ETF_Symbol'].dropna().unique().tolist()) if 'ETF_Symbol' in df.columns else ["Todos"],
                key="etf_filter_tab1"
            )

        with col3:
            tag_filter = st.selectbox(
                "Filtrar por Tag:",
                ["Todas"] + sorted([tag for tag in df['Tag'].dropna().unique() if tag.strip()]) if 'Tag' in df.columns else ["Todas"],
                key="tag_filter_tab1"
            )

        with col4:
            search_term = st.text_input("🔍 Buscar Symbol/Company:", key="search_tab1")

        # Aplicar filtros
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

        # Mostrar resultados
        st.info(f"📊 Mostrando {len(filtered_df)} de {len(df)} símbolos")

        display_columns = ['Symbol', 'Company', 'Sector_SPDR', 'ETF_Symbol', 'Tag']
        available_columns = [col for col in display_columns if col in filtered_df.columns]

        if len(filtered_df) > 0:
            display_df = filtered_df[available_columns].copy()

            # Limitar texto da Company (opcional)
            if 'Company' in display_df.columns:
                display_df['Company'] = display_df['Company'].str[:100]

            html_table = display_df.to_html(escape=False, index=False)
            html_table = html_table.replace('<table', '<table style="font-size: 15px; width: 100%;"')
            html_table = html_table.replace('<th', '<th style="font-size: 16px; font-weight: bold; padding: 10px; background-color: #2196F3; color: white;"')
            html_table = html_table.replace('<td', '<td style="font-size: 14px; padding: 8px; border-bottom: 1px solid #ddd;"')

            st.markdown(html_table, unsafe_allow_html=True)

            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"symbols_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("🔍 Nenhum símbolo encontrado com os filtros aplicados")

    # ========================
    # ➕ Aba 2 - Adicionar
    # ========================
    with tab2:
        st.subheader("➕ Adicionar Novo Símbolo")

        col1, col2 = st.columns(2)

        with col1:
            new_symbol = st.text_input("Ticker (Ex: AAPL):", key="new_symbol").upper()
            new_company = st.text_input("Nome da Empresa:", key="new_company")
            new_tag = st.text_input("Tag (opcional):", key="new_tag")

        with col2:
            if 'Sector_SPDR' in df.columns:
                sectors = sorted(df['Sector_SPDR'].dropna().unique())
                new_sector_spdr = st.selectbox("Setor SPDR:", [""] + sectors, key="new_sector")

            if 'ETF_Symbol' in df.columns:
                etfs = sorted(df['ETF_Symbol'].dropna().unique())
                new_etf = st.selectbox("ETF Symbol:", [""] + etfs, key="new_etf")

        if new_symbol:
            if st.button(f"🔍 Validar {new_symbol}"):
                with st.spinner(f"Validando {new_symbol}..."):
                    if validate_ticker(new_symbol):
                        st.success(f"✅ {new_symbol} é válido!")
                        info = get_ticker_info(new_symbol)
                        if info:
                            st.info(f"📋 Informações encontradas: {info['company']} - {info['sector']}")
                    else:
                        st.error(f"❌ {new_symbol} não foi encontrado no Yahoo Finance")

        if st.button("➕ Adicionar Símbolo"):
            if new_symbol:
                st.success(f"✅ {new_symbol} seria adicionado!")
                st.info("💡 Em produção, isso atualizaria seu Google Sheets automaticamente")
            else:
                st.error("❌ Digite um símbolo válido")

    # ========================
    # 🏷️ Aba 3 - Gerenciar Tags
    # ========================
    with tab3:
        st.subheader("🏷️ Gerenciar Tags")

        if 'Tag' in df.columns:
            tag_counts = df['Tag'].value_counts()
            tag_counts = tag_counts[tag_counts.index != ""]

            if len(tag_counts) > 0:
                st.write("**Tags existentes:**")

                cols = st.columns(min(3, len(tag_counts)))
                for i, (tag, count) in enumerate(tag_counts.head(9).items()):
                    with cols[i % 3]:
                        st.metric(f"#{tag}", count)

                st.subheader("✏️ Editor de Tags em Lote")

                col1, col2 = st.columns(2)

                with col1:
                    bulk_sector = st.selectbox(
                        "Selecionar por Setor:",
                        [""] + sorted(df['Sector_SPDR'].dropna().unique().tolist()),
                        key="bulk_sector"
                    )

                with col2:
                    new_bulk_tag = st.text_input("Nova Tag para aplicar:", key="bulk_tag")

                if bulk_sector and new_bulk_tag:
                    affected_symbols = df[df['Sector_SPDR'] == bulk_sector]['Symbol'].tolist()
                    st.info(f"📊 Isso aplicaria a tag '{new_bulk_tag}' para {len(affected_symbols)} símbolos do setor {bulk_sector}")

                    if st.button("🔄 Aplicar Tag em Lote"):
                        st.success(f"✅ Tag '{new_bulk_tag}' aplicada a {len(affected_symbols)} símbolos!")
                        st.info("💡 Em produção, isso atualizaria seu Google Sheets")
            else:
                st.info("📝 Nenhuma tag encontrada. Comece adicionando tags aos seus símbolos!")

        st.subheader("💡 Sugestões de Tags")
        suggestions = {
            "🎯 Estratégia": ["daytrade", "swing", "long-term", "scalping"],
            "📊 Watchlist": ["favorites", "earnings", "breakout", "momentum"],
            "⚠️ Risco": ["high-vol", "conservative", "speculative", "blue-chip"],
            "📈 Estilo": ["growth", "value", "dividend", "penny"],
            "🔄 Status": ["active", "watchlist", "sold", "researching"]
        }
        for category, tags in suggestions.items():
            st.write(f"**{category}:** {', '.join(tags)}")

    # ========================
    # 📊 Aba 4 - Estatísticas
    # ========================
    with tab4:
        st.subheader("📊 Estatísticas Detalhadas")

        if 'Sector_SPDR' in df.columns:
            st.subheader("📊 Distribuição por Setor SPDR")
            sector_dist = df['Sector_SPDR'].value_counts()
            chart_data = []
            for sector, count in sector_dist.head(10).items():
                percentage = (count / len(df)) * 100
                chart_data.append({
                    'Setor': sector,
                    'Quantidade': count,
                    'Percentual': f"{percentage:.1f}%"
                })
            chart_df = pd.DataFrame(chart_data)
            st.dataframe(chart_df, use_container_width=True)

        if 'ETF_Symbol' in df.columns:
            st.subheader("📊 Distribuição por ETF")
            etf_dist = df['ETF_Symbol'].value_counts().head(10)
            etf_data = []
            for etf, count in etf_dist.items():
                percentage = (count / len(df)) * 100
                etf_data.append({
                    'ETF': etf,
                    'Quantidade': count,
                    'Percentual': f"{percentage:.1f}%"
                })
            etf_df = pd.DataFrame(etf_data)
            st.dataframe(etf_df, use_container_width=True)

if __name__ == "__main__":
    main()
