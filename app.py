with tab1:
    st.subheader("📋 Visualizar Símbolos")
    
    # CSS para limitar largura das colunas
    st.markdown("""
    <style>
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
        display_df = filtered_df[available_columns].copy()
        
        # Limitar texto de Company (opcional, já temos CSS que corta com "...")
        if 'Company' in display_df.columns:
            display_df['Company'] = display_df['Company'].str[:100]
        
        html_table = display_df.to_html(escape=False, index=False)
        html_table = html_table.replace('<table', '<table style="font-size: 15px; width: 100%;"')
        html_table = html_table.replace('<th', '<th style="font-size: 16px; font-weight: bold; padding: 10px; background-color: #2196F3; color: white;"')
        html_table = html_table.replace('<td', '<td style="font-size: 14px; padding: 8px; border-bottom: 1px solid #ddd;"')
        
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
