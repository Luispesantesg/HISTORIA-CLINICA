import streamlit as st
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURACIÓN DEL ENTORNO Y SEGURIDAD
# ==========================================
st.set_page_config(page_title="HCE - Salud Ocupacional", page_icon="⚕️", layout="wide")

# Inicialización del cliente Supabase
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Falla crítica en la inicialización de la base de datos: {e}")
    st.stop() # Interrupción forzada del sistema si la conexión es comprometida

# ==========================================
# 2. INTERFAZ GRÁFICA Y PUNTO DE CONTROL (FORMULARIO)
# ==========================================
st.title("⚕️ Sistema Integrado de Historia Clínica y Salud Ocupacional")
st.markdown("---")

# Implementación de st.form: Garantiza que los datos se envíen en bloque y limpia la pantalla tras el éxito
with st.form("formulario_hce", clear_on_submit=True):
    
    col_demografica, col_clinica = st.columns(2)

    # Nodo 1: Variables de Medicina del Trabajo
    with col_demografica:
        st.subheader("1. Perfil Demográfico y Ocupacional")
        id_paciente = st.text_input("ID / Cédula del Paciente (Obligatorio):").strip()
        edad = st.number_input("Edad:", min_value=0, max_value=120, step=1)
        sexo = st.selectbox("Sexo:", ["Masculino", "Femenino"])
        
        st.markdown("#### Matriz de Riesgo Laboral")
        riesgo_ocupacional = st.text_input("Exposición / Riesgo Ocupacional principal:").strip()
        aptitud_laboral = st.selectbox("Aptitud Laboral Actual:", 
                                       ["Apto", "Apto con restricciones", "No Apto", "En Evaluación Médica"])

    # Nodo 2: Variables Clínicas Basadas en Evidencia (SOAP)
    with col_clinica:
        st.subheader("2. Evolución Clínica (SOAP)")
        nodo_s = st.text_area("Subjetivo (S):", height=100).strip()
        nodo_o = st.text_area("Objetivo (O):", height=100).strip()
        nodo_a = st.text_area("Apreciación (A):", height=100).strip()
        nodo_p = st.text_area("Plan (P) (Obligatorio):", height=100).strip()
        cie_10 = st.text_input("Codificación CIE-10 Principal:").strip()

    st.markdown("---")
    
    # Motor de ejecución integrado al formulario
    submitted = st.form_submit_button("Guardar Evolución en Base de Datos", type="primary")

# ==========================================
# 3. TRANSACCIONES SQL (POST-VALIDACIÓN)
# ==========================================
if submitted:
    # Verificación de integridad referencial
    if not id_paciente or not nodo_p:
        st.error("Error de Integridad Lógica: La cédula del paciente y el Plan Terapéutico (P) son mandatorios. Transacción abortada.")
    else:
        try:
            # Transacción A: Matriz Demográfica/Ocupacional (Upsert)
            paciente_data = {
                "id_paciente": id_paciente, "edad": edad, "sexo": sexo,
                "riesgo_ocupacional": riesgo_ocupacional, "aptitud_laboral": aptitud_laboral
            }
            supabase.table("pacientes").upsert(paciente_data).execute()

            # Transacción B: Registro de Evolución Clínica
            evolucion_data = {
                "id_paciente": id_paciente, "nodo_s": nodo_s, "nodo_o": nodo_o,
                "nodo_a": nodo_a, "nodo_p": nodo_p, "cie_10": cie_10
            }
            supabase.table("evoluciones").insert(evolucion_data).execute()

            st.success(f"Protocolo Completado: Evolución clínica del paciente ID {id_paciente} registrada permanentemente en el servidor seguro. Los campos han sido purgados.")
            
        except Exception as e:
            st.error(f"Falla en la transacción SQL o interrupción del servidor: {e}")
