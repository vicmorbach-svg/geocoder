import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import time
import io

st.set_page_config(page_title="Geocodificador", layout="centered")

st.title("🌍 Geocodificador Automático")
st.markdown("Transforme endereços de texto em **Latitude** e **Longitude**.")

# 1. Upload do arquivo
arquivo = st.file_uploader("Suba sua planilha Excel (.xlsx)", type=['xlsx'])

if arquivo:
    df = pd.read_excel(arquivo)
    st.write("Pré-visualização da sua planilha:")
    st.dataframe(df.head(3))

    st.markdown("---")
    st.markdown("### Configuração das Colunas")

    col1, col2 = st.columns(2)
    with col1:
        col_cidade = st.selectbox("Qual coluna tem o nome da CIDADE?", df.columns)
    with col2:
        col_endereco = st.selectbox("Qual coluna tem o ENDEREÇO (Rua, Número)?", df.columns)

    if st.button("🚀 Iniciar Busca de Coordenadas", type="primary"):
        # Inicializa o buscador
        geolocator = Nominatim(user_agent="corsan_app_geocoder_v1")

        # Cria as colunas vazias
        df['LATITUDE'] = None
        df['LONGITUDE'] = None

        barra_progresso = st.progress(0)
        texto_status = st.empty()

        total_linhas = len(df)
        sucessos = 0

        # Loop passando por cada linha da planilha
        for index, row in df.iterrows():
            cidade = str(row[col_cidade]).strip()
            endereco = str(row[col_endereco]).strip()

            # Ignora linhas vazias
            if endereco.lower() in ['nan', 'none', ''] or cidade.lower() in ['nan', 'none', '']:
                barra_progresso.progress((index + 1) / total_linhas)
                continue

            # Monta a string de busca (Forçamos 'RS, Brasil' para maior precisão)
            busca = f"{endereco}, {cidade}, RS, Brasil"
            texto_status.text(f"Buscando ({index+1}/{total_linhas}): {busca}")

            try:
                # Tenta achar a coordenada (timeout de 10s para internet lenta)
                location = geolocator.geocode(busca, timeout=10)

                if location:
                    df.at[index, 'LATITUDE'] = location.latitude
                    df.at[index, 'LONGITUDE'] = location.longitude
                    sucessos += 1
            except Exception as e:
                pass # Se der erro de conexão, ignora e vai para o próximo

            # PAUSA OBRIGATÓRIA para não ser bloqueado pelo servidor gratuito
            time.sleep(1.5)
            barra_progresso.progress((index + 1) / total_linhas)

        texto_status.text(f"✅ Busca concluída! Encontramos {sucessos} de {total_linhas} endereços.")

        # Prepara o arquivo para download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)

        st.success("Planilha pronta! Clique no botão abaixo para baixar.")
        st.download_button(
            label="📥 Baixar Planilha com Coordenadas",
            data=buffer.getvalue(),
            file_name="enderecos_com_coordenadas.xlsx",
            mime="application/vnd.ms-excel"
        )
