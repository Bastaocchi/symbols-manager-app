# 📊 Gerenciador de Símbolos

Aplicação Streamlit para gerenciar símbolos de ações, setores, ETFs e tags personalizadas.

## ✨ Funcionalidades

- **📋 Visualizar** - Filtros por setor, ETF, tags e busca
- **➕ Adicionar** - Novos símbolos com validação automática  
- **🏷️ Gerenciar Tags** - Editor de tags individual e em lote
- **📊 Estatísticas** - Distribuições por setor e ETF

## 🚀 Como usar

1. **Conectar Google Sheets**: Cole a URL da sua planilha pública
2. **Visualizar dados**: Use filtros para encontrar símbolos específicos
3. **Adicionar símbolos**: Valida automaticamente no Yahoo Finance
4. **Gerenciar tags**: Organize seus símbolos com tags personalizadas

## 📱 Deploy

Deploy automático no Streamlit Cloud:
- Conecte seu repositório GitHub
- Selecione `app.py` como arquivo principal
- Deploy automático em ~2 minutos

## 🛠️ Tecnologias

- **Streamlit** - Interface web
- **Pandas** - Manipulação de dados
- **yFinance** - Validação de tickers
- **Google Sheets** - Fonte de dados

## 📊 Estrutura dos dados

O app espera uma planilha Google Sheets com as colunas:
- `Symbol` - Ticker da ação
- `Company` - Nome da empresa
- `TradingView_Sector` - Setor 
- `TradingView_Industry` - Indústria
- `Sector_SPDR` - Classificação SPDR
- `ETF_Symbol` - ETF correspondente
- `Sector_Number` - Número do setor
- `Tag` - Tags personalizadas

---

*Desenvolvido para gerenciamento profissional de carteiras de ações.*
