import streamlit as st
import datetime

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="HCE - Salud Ocupacional", layout="wide")
st.title("⚕️ Sistema Integrado de Historia Clínica")
st.markdown("---")

# --- MÓDULO DE INGRESO DE DATOS (NODO DE CONTROL) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Perfil Demográfico y Ocupacional")
    id_paciente = st.text_input("ID / Cédula del Paciente:")
    edad = st.number_input("Edad:", min_value=0, max_value=120, step=1)
    sexo = st.selectbox("Sexo:", ["Masculino", "Femenino"])
    riesgo_ocupacional = st.text_input("Exposición / Riesgo Ocupacional:")
    aptitud_laboral = st.selectbox("Aptitud Laboral:", ["Apto", "Apto con restricciones", "No Apto", "En Evaluación"])

with col2:
    st.subheader("2. Evolución Clínica (SOAP)")
    nodo_s = st.text_area("Subjetivo (S):", placeholder="Sintomatología referida por el paciente...")
    nodo_o = st.text_area("Objetivo (O):", placeholder="Signos vitales y exploración física...")
    nodo_a = st.text_area("Apreciación (A):", placeholder="Análisis clínico y diagnóstico...")
    nodo_p = st.text_area("Plan (P):", placeholder="Tratamiento, exámenes y recomendaciones...")
    cie_10 = st.text_input("Codificación CIE-10 Principal:")

# --- MOTOR DE VALIDACIÓN Y REGISTRO ---
if st.button("Guardar Evolución Clínica", type="primary"):
    if not id_paciente or not nodo_p:
        st.error("Error Lógico: El ID del paciente y el Plan Terapéutico son campos obligatorios.")
    else:
        # Aquí se conectaría la API de Supabase para inyectar los datos en PostgreSQL
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        st.success(f"Protocolo Completado: Evolución de paciente {id_paciente} registrada con éxito.")
        
        # Visualización de la Nota Clínica Generada
        st.info("Resumen de Exportación HL7 / Registro Clínico:")
        st.markdown(f"""
        **Fecha:** {fecha_actual} | **CIE-10:** {cie_10}
        * **Paciente:** {id_paciente} ({edad} años, {sexo})
        * **Riesgo Ocupacional:** {riesgo_ocupacional} | **Aptitud:** {aptitud_laboral}
        * **(S):** {nodo_s}
        * **(O):** {nodo_o}
        * **(A):** {nodo_a}
        * **(P):** {nodo_p}
        """)