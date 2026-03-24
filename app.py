from supabase import create_client, Client

# --- INICIALIZACIÓN SECRETA DEL CLIENTE SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- MOTOR DE VALIDACIÓN Y REGISTRO EN POSTGRESQL ---
if st.button("Guardar Evolución Clínica", type="primary"):
    if not id_paciente or not nodo_p:
        st.error("Error Lógico: El ID del paciente y el Plan Terapéutico son campos obligatorios.")
    else:
        try:
            # 1. Intentar registrar al paciente (ignora si ya existe gracias a la lógica lógica relacional)
            paciente_data = {
                "id_paciente": id_paciente, "edad": edad, "sexo": sexo,
                "riesgo_ocupacional": riesgo_ocupacional, "aptitud_laboral": aptitud_laboral
            }
            supabase.table("pacientes").upsert(paciente_data).execute()

            # 2. Registrar la evolución clínica SOAP
            evolucion_data = {
                "id_paciente": id_paciente, "nodo_s": nodo_s, "nodo_o": nodo_o,
                "nodo_a": nodo_a, "nodo_p": nodo_p, "cie_10": cie_10
            }
            supabase.table("evoluciones").insert(evolucion_data).execute()

            st.success(f"Protocolo Completado: Evolución de paciente {id_paciente} registrada permanentemente en base de datos.")
            
        except Exception as e:
            st.error(f"Falla Crítica de Conexión o Integridad de Datos: {e}")
