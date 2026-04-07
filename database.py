import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"Error de configuración: Credencial {e} no encontrada en secrets.toml.")
        st.stop()

# Exportación de la instancia global del cliente
try:
    supabase: Client = init_connection()
except Exception as e:
    st.error(f"Falla crítica en la inicialización de la base de datos: {e}")
    st.stop()

@st.cache_data
def cargar_catalogo_cie10_csv() -> list:
    try:
        df = pd.read_csv("cie10_completo.csv", dtype=str)
        df['CODIGO'] = df['CODIGO'].fillna("").str.strip()
        df['DESCRIPCION'] = df['DESCRIPCION'].fillna("").str.strip()
        df['DIAGNOSTICO_COMPLETO'] = df['CODIGO'] + " - " + df['DESCRIPCION']
        return df['DIAGNOSTICO_COMPLETO'].tolist()
    except FileNotFoundError:
        return ["Error - Archivo 'cie10_completo.csv' no detectado en el servidor."]

PERFILES_MEDICOS = {
    "luis_pesantes": {
        "nombre": "Dr. Luis M. Pesantes",
        "especialidad": "Médico General",
        "subtitulo": "Magíster en Salud Ocupacional"
    },
    "cinthia_garcia": {
        "nombre": "Dra. Cinthia Anabel García Dávila",
        "especialidad": "Médico General", 
        "subtitulo": "Atención Médica Integral" 
    }
}