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
# 2. MOTOR DE AUTENTICACIÓN Y SEGURIDAD
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
                matriz_usuarios = st.secrets["credenciales"]
                if usuario in matriz_usuarios:
                    pass_valida = hmac.compare_digest(contrasena, matriz_usuarios[usuario])
                    if pass_valida:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_activo"] = usuario
                        st.rerun()
                    else:
                        st.error("Brecha de Seguridad: Contraseña inválida. Acceso denegado.")
                else:
                    st.error("Brecha de Seguridad: Identificador de usuario no reconocido.")
            except KeyError:
                st.error("Falla Crítica: El bloque [credenciales] no está definido en secrets.toml.")
    return False

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
    pdf.cell(20, 8, "ID/Documento:", border=0)
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
# 5. TOPOLOGÍA DE NAVEGACIÓN REACTIVA
# ==========================================
st.title("⚕️ Sistema Integrado de Historia Clínica")

usuario_actual = st.session_state.get("usuario_activo", "luis_pesantes")
perfil_activo = PERFILES_MEDICOS.get(usuario_actual, PERFILES_MEDICOS["luis_pesantes"])
st.caption(f"Sesión activa: {perfil_activo['nombre']}")
st.markdown("---")

tab_ingreso, tab_consulta = st.tabs(["📝 Ingreso y Síntesis Médica", "🔍 Auditoría Longitudinal del Paciente"])
lista_cie10 = cargar_catalogo_cie10_csv()

# ------------------------------------------
# NODO A: ESCRITURA Y EMISIÓN (HUD EN TIEMPO REAL)
# ------------------------------------------
with tab_ingreso:
    st.subheader("1. Filiación y Antecedentes")
    col_fil_1, col_fil_2 = st.columns(2)
    with col_fil_1:
        id_paciente = st.text_input("Documento de Identidad (Obligatorio):").strip()
        nombres = st.text_input("Apellidos y Nombres:").strip()
        sexo = st.selectbox("Sexo Biológico:", ["Masculino", "Femenino"])
        edad = st.number_input("Edad (Años):", min_value=0, max_value=120, step=1)
    with col_fil_2:
        antecedentes_personales = st.text_area("APP:", height=80).strip()
        antecedentes_familiares = st.text_area("APF:", height=80).strip()

    st.markdown("---")
    st.subheader("2. Signos Vitales y Antropometría")
    col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
    with col_v1: pa = st.text_input("PA (mmHg):", placeholder="120/80").strip()
    with col_v2: fc = st.number_input("FC (lpm):", min_value=0, step=1)
    with col_v3: temp = st.number_input("Temp (°C):", format="%.1f", step=0.1)
    with col_v4: peso_kg = st.number_input("Peso (kg):", format="%.2f", min_value=0.0, step=0.1)
    with col_v5: talla_m = st.number_input("Talla (m):", format="%.2f", min_value=0.0, step=0.01)

    # ==========================================
    # HUD VISUAL: RADAR BIOMÉTRICO (SE ACTIVA AL TECLEAR)
    # ==========================================
    imc_texto_db = ""
    if talla_m > 0 and peso_kg > 0:
        imc_val = round(peso_kg / (talla_m ** 2), 2)
        
        if edad < 19:
            st.warning(f"⚠️ **Alerta Pediátrica:** El IMC calculado es **{imc_val}**. La estratificación estática está deshabilitada. Requiere validación manual en curvas de crecimiento OMS según edad y sexo.")
            imc_texto_db = f"[Antropometría] IMC: {imc_val} - Riesgo Metabólico: Paciente pediátrico (Validar en curvas OMS)"
        else:
            if imc_val < 18.5: estrato, color = "Bajo peso", "🔵"
            elif imc_val < 24.9: estrato, color = "Normopeso", "🟢"
            elif imc_val < 29.9: estrato, color = "Sobrepeso", "🟡"
            elif imc_val < 34.9: estrato, color = "Obesidad I", "🟠"
            elif imc_val < 39.9: estrato, color = "Obesidad II", "🔴"
            else: estrato, color = "Obesidad III", "🟣"
            
            st.info(f"{color} **Radar Antropométrico:** IMC de **{imc_val}** - Estratificación OMS: **{estrato}**")
            imc_texto_db = f"[Antropometría] IMC: {imc_val} ({estrato})"

    st.markdown("---")
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

    # Botón maestro fuera del formulario
    submitted = st.button("Guardar Historia y Procesar Receta", type="primary", use_container_width=True)

    if submitted:
        if not id_paciente or not nodo_p:
            st.error("Error Lógico: El Documento de Identidad y el Plan de Tratamiento (P) son mandatorios.")
        else:
            try:
                cie_10_final = cie_10_seleccion if cie_10_seleccion else "No especificado"

                # Fusión automática de telemetría biométrica
                nodo_o_final = f"{imc_texto_db}\n{nodo_o}" if imc_texto_db else nodo_o

                paciente_data = {
                    "id_paciente": id_paciente, "nombres": nombres, "edad": edad, "sexo": sexo,
                    "antecedentes_personales": antecedentes_personales, "antecedentes_familiares": antecedentes_familiares
                }
                supabase.table("pacientes").upsert(paciente_data).execute()

                evolucion_data = {
                    "id_paciente": id_paciente, "motivo_consulta": motivo_consulta, "enfermedad_actual": enfermedad_actual,
                    "presion_arterial": pa, "frecuencia_cardiaca": fc, "temperatura": temp,
                    "nodo_s": nodo_s, "nodo_o": nodo_o_final, "nodo_a": nodo_a, "nodo_p": nodo_p, "cie_10": cie_10_final
                }
                supabase.table("evoluciones").insert(evolucion_data).execute()
                
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                nombres_impresion = nombres if nombres else "Paciente No Registrado"
                
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
        busqueda_id = st.text_input("Ingrese el Documento del Paciente:").strip()
        btn_buscar = st.button("Ejecutar Extracción de Datos", type="primary")

    if btn_buscar and busqueda_id:
        try:
            res_paciente = supabase.table("pacientes").select("*").eq("id_paciente", busqueda_id).execute()
            
            if not res_paciente.data:
                st.warning("El Documento ingresado no posee registros en la base de datos central.")
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
