import streamlit as st
import pandas as pd
import os

# ===============================
# CONFIGURAÇÃO INICIAL
# ===============================
FILE_PATH = "symbols.xlsx"

if not os.path.exists(FILE_PATH):
    df_init = pd.DataFrame(columns=["SYMBOL", "TAGS"])
    df_init.to_excel(FILE_PATH, index=False)

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def load_data():
    return pd.read_excel(FILE_PATH)

def save_data(df):
    df.to_excel(FILE_PATH, index=False)

def add_symbols(symbols):
    df = load_data()
    for symbol in symbols:
        if symbol not in df["SYMBOL"].values:
            df = pd.concat([df, pd.DataFrame({"SYMBOL": [symbol], "TAGS": [""]})], ignore_index=True)
    save_data(df)

def update_tag(symbols, new_tag):
    df = load_data()
    for symbol in symbols:
        if symbol in df["SYMBOL"].values:
            idx = df.index[df["SYMBOL"] == symbol][0]
            current_tags = str(df.at[idx, "TAGS"])
            if current_tags.strip() == "" or current_tags.lower() == "nan":
                df.at[idx, "TAGS"] = new_tag
            else:
                # evita tags duplicadas
                tags_list = [t.strip() for t in current_tags.split(",")]
                if new_tag not in tags_list:
                    tags_list.append(new_tag)
                df.at[idx, "TAGS"] = ", ".join(tags_list)
    save_data(df)

def clear_tags(symbols):
    df = load_data()
    for symbol in symbols:
        if symbol in df["SYMBOL"].values:
            idx = df.index[df["SYMBOL"] == symbol][0]
            df.at[idx, "TAGS"] = ""
    save_data(df)

# ===============================
# INTERFACE STREAMLIT
# ===============================
def main():
    st.title("📊 Symbols Manager - Tags por múltiplos símbolos")

    menu = ["Ver Símbolos", "Adicionar Símbolos", "Gerenciar Tags"]
    choice = st.sidebar.radio("Menu", menu)

    df = load_data()

    if choice == "Ver Símbolos":
        st.subheader("Lista de Símbolos")
        st.dataframe(df)

    elif choice == "Adicionar Símbolos":
        st.subheader("Adicionar novos símbolos")
        symbols_input = st.text_area("Digite os símbolos separados por vírgula:")
        if st.button("Adicionar"):
            symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
            add_symbols(symbols)
            st.success(f"Símbolos adicionados: {', '.join(symbols)}")

    elif choice == "Gerenciar Tags":
        st.subheader("Adicionar/Remover Tags de Múltiplos Símbolos")

        symbols_input = st.text_area("Digite os símbolos separados por vírgula:")
        new_tag = st.text_input("Nova Tag")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Adicionar Tag"):
                if symbols_input and new_tag:
                    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
                    update_tag(symbols, new_tag.strip())
                    st.success(f"Tag '{new_tag}' adicionada a: {', '.join(symbols)}")
                else:
                    st.warning("Informe símbolos e a tag.")

        with col2:
            if st.button("🗑️ Limpar Tags"):
                if symbols_input:
                    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
                    clear_tags(symbols)
                    st.success(f"Tags removidas de: {', '.join(symbols)}")
                else:
                    st.warning("Informe símbolos para limpar as tags.")

        st.write("### Visualização Atualizada")
        st.dataframe(load_data())

if __name__ == "__main__":
    main()
