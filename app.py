import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import time

# Configuração da página
st.set_page_config(
    page_title="Gerenciador de Símbolos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .success-msg {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-msg {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Função para carregar dados do Google Sheets
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_symbols_from_sheets(sheet_url):
    """Carrega símbolos do Google Sheets"""
    try:
        # Converter URL para formato CSV
        if '/edit' in sheet_url:
            csv_url = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
            csv_url = csv_url.replace('/edit', '/export?format=csv')
        else:
            csv_url = sheet_url
        
        df = pd.read_csv(csv_url)
        
        # Renomear Column 1 para Tag se existir
        if 'Column 1' in df.columns:
            df = df.rename(columns={'Column 1': 'Tag'})
        
        # Adicionar coluna Tag se não existir
        if 'Tag' not in df.columns:
            df['Tag'] = ""
        
        # Limpar dados
        df = df.fillna("")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar Google Sheets: {e}")
        return None

# Função para validar ticker
@st.cache_data(ttl=3600)  # Cache por 1 hora
def validate_ticker(symbol):
    """Valida se ticker existe no Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('regularMarketPrice') is not None or info.get('symbol') == symbol
    except:
        return False

# Função para obter informações do ticker
@st.cache_data(ttl=3600)
def get_ticker_info(symbol):
    """Obtém informações básicas do ticker"""
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
    
    # Sidebar
    st.sidebar.header("⚙️ Configurações")
    
    # URL do Google Sheets
    sheet_url = st.sidebar.text_input(
        "🔗 URL do Google Sheets:",
        value="https://docs.google.com/spreadsheets/d/1NMCkkcrTFOm1ZoOiImzzRRFd6NEn5kMPTkuc5j_3DcQ/edit?gid=744859441#gid=744859441",
        help="Cole a URL do seu Google Sheets público"
    )
    
    # Botão para recarregar dados
    if st.sidebar.button("🔄 Recarregar do Sheets"):
        st.cache_data.clear()
        st.rerun()
    
    # Separador
    st.sidebar.markdown("---")
    
    # Carregar dados
    if sheet_url:
        df = load_symbols_from_sheets(sheet_url)
        
        if df is not None:
            st.sidebar.success(f"✅ {len(df)} símbolos carregados")
            
            # Estatísticas na sidebar
            st.sidebar.subheader("📊 Estatísticas")
            total_symbols = len(df)
            unique_sectors = len(df['TradingView_Sector'].dropna().unique()) if 'TradingView_Sector' in df.columns else 0
            unique_industries = len(df['TradingView_Industry'].dropna().unique()) if 'TradingView_Industry' in df.columns else 0
            symbols_with_tags = len(df[df['Tag'].str.strip() != ""]) if 'Tag' in df.columns else 0
            
            st.sidebar.metric("Total de Símbolos", total_symbols)
            st.sidebar.metric("Setores Únicos", unique_sectors)
            st.sidebar.metric("Indústrias Únicas", unique_industries)
            st.sidebar.metric("Com Tags", symbols_with_tags)
        else:
            st.error("❌ Não foi possível carregar os dados do Google Sheets")
            return
    else:
        st.warning("⚠️ Por favor, insira a URL do Google Sheets na sidebar")
        return
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Visualizar", "➕ Adicionar", "🏷️ Gerenciar Tags", "📊 Estatísticas"])
    
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
        
        # Preparar dados para exibição
        display_columns = ['Symbol', 'Company', 'Sector_SPDR', 'ETF_Symbol', 'Tag']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        if len(filtered_df) > 0:
            # Criar tabela HTML customizada
            display_df = filtered_df[available_columns].copy()
            
            # Limitar Company name para não quebrar layout
            if 'Company' in display_df.columns:
                display_df['Company'] = display_df['Company'].str[:50] + '...'
            
            html_table = display_df.to_html(escape=False, index=False)
            html_table = html_table.replace('<table', '<table style="font-size: 16px; width: 100%;"')
            html_table = html_table.replace('<th', '<th style="font-size: 18px; font-weight: bold; padding: 12px; background-color: #2196F3; color: white;"')
            html_table = html_table.replace('<td', '<td style="font-size: 16px; padding: 10px; border-bottom: 1px solid #ddd;"')
            
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Botão de download
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"symbols_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("🔍 Nenhum símbolo encontrado com os filtros aplicados")
    
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
        
        # Botão de validação
        if new_symbol:
            if st.button(f"🔍 Validar {new_symbol}"):
                with st.spinner(f"Validando {new_symbol}..."):
                    if validate_ticker(new_symbol):
                        st.success(f"✅ {new_symbol} é válido!")
                        
                        # Tentar obter informações automáticas
                        info = get_ticker_info(new_symbol)
                        if info:
                            st.info(f"📋 Informações encontradas: {info['company']} - {info['sector']}")
                    else:
                        st.error(f"❌ {new_symbol} não foi encontrado no Yahoo Finance")
        
        # Botão para adicionar (simulação - em produção salvaria no Google Sheets)
        if st.button("➕ Adicionar Símbolo"):
            if new_symbol:
                st.success(f"✅ {new_symbol} seria adicionado!")
                st.info("💡 Em produção, isso atualizaria seu Google Sheets automaticamente")
            else:
                st.error("❌ Digite um símbolo válido")
    
    with tab3:
        st.subheader("🏷️ Gerenciar Tags")
        
        if 'Tag' in df.columns:
            # Estatísticas de tags
            tag_counts = df['Tag'].value_counts()
            tag_counts = tag_counts[tag_counts.index != ""]  # Remover tags vazias
            
            if len(tag_counts) > 0:
                st.write("**Tags existentes:**")
                
                # Mostrar tags em colunas
                cols = st.columns(min(3, len(tag_counts)))
                for i, (tag, count) in enumerate(tag_counts.head(9).items()):
                    with cols[i % 3]:
                        st.metric(f"#{tag}", count)
                
                # Editor de tags em lote
                st.subheader("✏️ Editor de Tags em Lote")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Selecionar símbolos por filtro
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
        
        # Sugestões de tags
        st.subheader("💡 Sugestões de Tags")
        
        suggestions = {
            "🎯 Estratégia": ["dayrade", "swing", "long-term", "scalping"],
            "📊 Watchlist": ["favorites", "earnings", "breakout", "momentum"],
            "⚠️ Risco": ["high-vol", "conservative", "speculative", "blue-chip"],
            "📈 Estilo": ["growth", "value", "dividend", "penny"],
            "🔄 Status": ["active", "watchlist", "sold", "researching"]
        }
        
        for category, tags in suggestions.items():
            st.write(f"**{category}:** {', '.join(tags)}")
    
    with tab4:
        st.subheader("📊 Estatísticas Detalhadas")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total de Símbolos", len(df))
        
        with col2:
            unique_companies = len(df['Company'].dropna().unique()) if 'Company' in df.columns else 0
            st.metric("🏢 Empresas Únicas", unique_companies)
        
        with col3:
            if 'Sector_SPDR' in df.columns:
                unique_sectors = len(df['Sector_SPDR'].dropna().unique())
                st.metric("🏭 Setores", unique_sectors)
        
        with col4:
            if 'Tag' in df.columns:
                tagged_symbols = len(df[df['Tag'].str.strip() != ""])
                st.metric("🏷️ Com Tags", tagged_symbols)
        
        # Distribuição por setor
        if 'Sector_SPDR' in df.columns:
            st.subheader("📊 Distribuição por Setor SPDR")
            sector_dist = df['Sector_SPDR'].value_counts()
            
            # Criar gráfico de barras simples com HTML
            chart_data = []
            for sector, count in sector_dist.head(10).items():
                percentage = (count / len(df)) * 100
                chart_data.append({
                    'Setor': sector,
                    'Quantidade': count,
                    'Percentual': f"{percentage:.1f}%"
                })
            
            chart_df = pd.DataFrame(chart_data)
            
            # Tabela HTML customizada
            html_chart = chart_df.to_html(escape=False, index=False)
            html_chart = html_chart.replace('<table', '<table style="font-size: 16px; width: 100%;"')
            html_chart = html_chart.replace('<th', '<th style="font-size: 18px; font-weight: bold; padding: 12px; background-color: #4CAF50; color: white;"')
            html_chart = html_chart.replace('<td', '<td style="font-size: 16px; padding: 10px; border-bottom: 1px solid #ddd;"')
            
            st.markdown(html_chart, unsafe_allow_html=True)
        
        # Distribuição por ETF
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
            
            # Tabela HTML customizada
            html_etf = etf_df.to_html(escape=False, index=False)
            html_etf = html_etf.replace('<table', '<table style="font-size: 16px; width: 100%;"')
            html_etf = html_etf.replace('<th', '<th style="font-size: 18px; font-weight: bold; padding: 12px; background-color: #FF9800; color: white;"')
            html_etf = html_etf.replace('<td', '<td style="font-size: 16px; padding: 10px; border-bottom: 1px solid #ddd;"')
            
            st.markdown(html_etf, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
