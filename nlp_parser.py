import streamlit as st
import pandas as pd
import json
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

def _init_gemini_client():
    try:
        return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    except KeyError:
        return None

gemini_client = _init_gemini_client()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _inferencia_resiliente(prompt: str) -> str:
    respuesta = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return respuesta.text

def estructurar_telemetria_laboratorio(texto_crudo: str) -> pd.DataFrame:
    if gemini_client is None:
        st.error("El motor NLP se encuentra inactivo. Verifique sus credenciales.")
        return pd.DataFrame(columns=["Biomarcador", "Resultado", "Unidad", "Rango de Referencia"])
        
    prompt_ingenieria = f"""
    Actúa como un algoritmo experto en extracción de datos de laboratorio clínico.
    Analiza el texto médico proporcionado y extrae únicamente los parámetros evaluados.
    Debes devolver un arreglo de objetos JSON estructurados exactamente así:
    [
      {{"Biomarcador": "Nombre", "Resultado": "Valor numérico o cualitativo", "Unidad": "Unidad de medida si existe", "Rango de Referencia": "Rango de normalidad si existe"}}
    ]
    Si un valor no existe, usa un string vacío "". Excluye nombres de pacientes, médicos, direcciones o cabeceras del laboratorio.

    Texto a procesar:
    {texto_crudo}
    """
    try:
        texto_json = _inferencia_resiliente(prompt_ingenieria)
        matriz_diccionarios = json.loads(texto_json)
        return pd.DataFrame(matriz_diccionarios)
    except Exception as e:
        st.error(f"Falla crítica de red: El motor NLP no respondió tras múltiples intentos. Error: {e}")
        return pd.DataFrame(columns=["Biomarcador", "Resultado", "Unidad", "Rango de Referencia"])
