import streamlit as st
import hmac
from supabase import create_client, Client
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DEL ENTORNO
# ==========================================
st.set_page_config(page_title="HCE - Medicina General", page_icon="⚕️", layout="wide")

# ==========================================
# 2. MOTOR DE AUTENTICACIÓN Y SEGURIDAD (MULTI-USUARIO)
# ==========================================
def verificar_autenticacion() -> bool:
    if st.session_state.get("autenticado", False):
        return True

    st.title("🔒 Portal de Acceso Restringido")
    st.markdown("Sistema de Historia Clínica Electrónica - Control de Acceso")
    
    with st.form("formulario_login"):
        usuario = st.text_input("Identificador de Usuario:").strip()
        contrasena = st.text_input("Clave de Acceso:", type="password").strip()
        submit = st.form_submit_button("Iniciar Sesión", type="primary")

        if submit:
            try:
                # Extracción de la matriz de credenciales desde la bóveda de Streamlit
                matriz_usuarios = st.secrets["credenciales"]
                
                if usuario in matriz_usuarios:
                    pass_valida = hmac.compare_digest(contrasena, matriz_usuarios[usuario])
                    
                    if pass_valida:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_activo"] = usuario # Registro de trazabilidad
                        st.rerun()
                    else:
                        st.error("Brecha de Seguridad: Contraseña inválida. Acceso denegado.")
                else:
                    st.error("Brecha de Seguridad: Identificador de usuario no reconocido.")
            except KeyError:
                st.error("Falla Crítica: El bloque [credenciales] no está definido en secrets.toml.")
                
    return False

# ------------------------------------------
# BARRERA LÓGICA DE EJECUCIÓN
# ------------------------------------------
if not verificar_autenticacion():
    st.stop()

# ==========================================
# 3. MOTORES DE DATOS Y CATÁLOGOS ESTÁTICOS
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
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

# ==========================================
# 4. MATRIZ DE PERFILES Y EXPORTACIÓN PDF
# ==========================================
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

def generar_receta_pdf(id_paciente, nombres, edad, fecha, plan_terapeutico, perfil_medico):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RECETA MEDICA", ln=True, align='C')
    
    # Inyección de metadatos del perfil activo
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"{perfil_medico['nombre']} - {perfil_medico['especialidad']}", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, perfil_medico['subtitulo'], ln=True, align='C')
    
    pdf.line(10, 35, 200, 35)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 8, "Fecha:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, fecha, ln=False)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(20, 8, "ID/Cedula:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, id_paciente, ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 8, "Paciente:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 8, nombres, ln=False)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 8, "Edad:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, str(edad), ln=True)
    pdf.line(10, 60, 200, 60)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Rp. / Indicaciones:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 8, plan_terapeutico)
    pdf.ln(30)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f"Firma y Sello: {perfil_medico['nombre']}", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 5. TOPOLOGÍA DE NAVEGACIÓN (PESTAÑAS)
# ==========================================
st.title("⚕️ Sistema Integrado de Historia Clínica")

# Identificación visual de la sesión activa
usuario_actual = st.session_state.get("usuario_activo", "luis_pesantes")
perfil_activo = PERFILES_MEDICOS.get(usuario_actual, PERFILES_MEDICOS["luis_pesantes"])
st.caption(f"Sesión activa: {perfil_activo['nombre']}")
st.markdown("---")

tab_ingreso, tab_consulta = st.tabs(["📝 Ingreso y Síntesis Médica", "🔍 Auditoría Longitudinal del Paciente"])

lista_cie10 = cargar_catalogo_cie10_csv()

# ------------------------------------------
# NODO A: ESCRITURA Y EMISIÓN
# ------------------------------------------
with tab_ingreso:
    with st.form("formulario_hce_general", clear_on_submit=True):
        st.subheader("1. Filiación y Antecedentes")
        col_fil_1, col_fil_2 = st.columns(2)
        with col_fil_1:
            id_paciente = st.text_input("Cédula / ID (Obligatorio):").strip()
            nombres = st.text_input("Apellidos y Nombres:").strip()
            sexo = st.selectbox("Sexo Biológico:", ["Masculino", "Femenino"])
            edad = st.number_input("Edad:", min_value=0, max_value=120, step=1)
        with col_fil_2:
            antecedentes_personales = st.text_area("APP:", height=80).strip()
            antecedentes_familiares = st.text_area("APF:", height=80).strip()

        st.markdown("---")
        st.subheader("2. Signos Vitales y Evolución")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1: pa = st.text_input("PA (mmHg):", placeholder="120/80").strip()
        with col_v2: fc = st.number_input("FC (lpm):", min_value=0, step=1)
        with col_v3: temp = st.number_input("Temp (°C):", format="%.1f", step=0.1)

        motivo_consulta = st.text_input("Motivo de Consulta:").strip()
        enfermedad_actual = st.text_area("Enfermedad Actual:", height=100).strip()
        
        col_clin_1, col_clin_2 = st.columns(2)
        with col_clin_1:
            nodo_s = st.text_area("Subjetivo (S):", height=120).strip()
            nodo_o = st.text_area("Objetivo (O):", height=120).strip()
        with col_clin_2:
            nodo_a = st.text_area("Apreciación (A):", height=120).strip()
            nodo_p = st.text_area("Plan de Tratamiento / Receta (P):", height=120).strip()
            
        cie_10_seleccion = st.selectbox(
            "Diagnóstico CIE-10 Principal (Normativa Técnica):", 
            options=lista_cie10, 
            index=None,
            placeholder="Haga clic aquí y escriba el código o patología para filtrar..."
        )

        submitted = st.form_submit_button("Guardar Historia y Procesar Receta", type="primary")

    if submitted:
        if not id_paciente or not nodo_p:
            st.error("Error Lógico: La Cédula y el Plan de Tratamiento (P) son mandatorios.")
        else:
            try:
                cie_10_final = cie_10_seleccion if cie_10_seleccion else "No especificado"

                paciente_data = {
                    "id_paciente": id_paciente, "nombres": nombres, "edad": edad, "sexo": sexo,
                    "antecedentes_personales": antecedentes_personales, "antecedentes_familiares": antecedentes_familiares
                }
                supabase.table("pacientes").upsert(paciente_data).execute()

                evolucion_data = {
                    "id_paciente": id_paciente, "motivo_consulta": motivo_consulta, "enfermedad_actual": enfermedad_actual,
                    "presion_arterial": pa, "frecuencia_cardiaca": fc, "temperatura": temp,
                    "nodo_s": nodo_s, "nodo_o": nodo_o, "nodo_a": nodo_a, "nodo_p": nodo_p, "cie_10": cie_10_final
                }
                supabase.table("evoluciones").insert(evolucion_data).execute()
                
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                nombres_impresion = nombres if nombres else "Paciente No Registrado"
                
                # Ejecución del motor PDF con inyección del perfil activo
                pdf_bytes = generar_receta_pdf(id_paciente, nombres_impresion, edad, fecha_actual, nodo_p, perfil_activo)
                
                st.success(f"Protocolo Exitoso: Registro consolidado. Documento firmado por {perfil_activo['nombre']}.")
                st.download_button("📥 Descargar Receta Médica (PDF)", data=pdf_bytes, file_name=f"Receta_{id_paciente}.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"Falla transaccional: {e}")

# ------------------------------------------
# NODO B: LECTURA Y AUDITORÍA (QUERY)
# ------------------------------------------
with tab_consulta:
    st.subheader("Motor de Búsqueda Clínica")
    
    col_busqueda, col_vacia = st.columns([1, 2])
    with col_busqueda:
        busqueda_id = st.text_input("Ingrese la Cédula / ID del Paciente:").strip()
        btn_buscar = st.button("Ejecutar Extracción de Datos", type="primary")

    if btn_buscar and busqueda_id:
        try:
            res_paciente = supabase.table("pacientes").select("*").eq("id_paciente", busqueda_id).execute()
            
            if not res_paciente.data:
                st.warning("El ID ingresado no posee registros en la base de datos central.")
            else:
                paciente = res_paciente.data[0]
                st.markdown("### Filiación y Perfil de Riesgo")
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.info(f"**Paciente:** {paciente.get('nombres', 'N/A')}\n\n**Edad:** {paciente.get('edad', 'N/A')} años\n\n**Sexo Biológico:** {paciente.get('sexo', 'N/A')}")
                with col_info2:
                    st.error(f"**APP:** {paciente.get('antecedentes_personales', 'Sin registros')}")
                    st.warning(f"**APF:** {paciente.get('antecedentes_familiares', 'Sin registros')}")
                
                st.markdown("---")
                
                st.markdown("### Línea de Tiempo Clínica (Controles Previos)")
                res_evol = supabase.table("evoluciones").select("*").eq("id_paciente", busqueda_id).order("fecha", desc=True).execute()
                
                if not res_evol.data:
                    st.info("No existen evoluciones clínicas documentadas para este paciente.")
                else:
                    for evol in res_evol.data:
                        raw_date = evol.get("fecha", "")
                        fmt_date = raw_date[:10] if raw_date else "Fecha desconocida"
                        
                        with st.expander(f"🗓️ Control: {fmt_date} | Motivo: {evol.get('motivo_consulta', 'No especificado')} | CIE-10: {evol.get('cie_10', 'N/A')}"):
                            st.write(f"**Enfermedad Actual:** {evol.get('enfermedad_actual', 'N/A')}")
                            st.markdown("**Triaje Vital:**")
                            st.code(f"PA: {evol.get('presion_arterial','N/A')} | FC: {evol.get('frecuencia_cardiaca','N/A')} | Temp: {evol.get('temperatura','N/A')}")
                            
                            st.markdown("**Matriz SOAP:**")
                            st.write(f"**S:** {evol.get('nodo_s', '')}")
                            st.write(f"**O:** {evol.get('nodo_o', '')}")
                            st.write(f"**A:** {evol.get('nodo_a', '')}")
                            st.write(f"**P:** {evol.get('nodo_p', '')}")
                            
        except Exception as e:
            st.error(f"Falla en la recuperación de telemetría: {e}")
