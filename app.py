import streamlit as st
import hmac
from supabase import create_client, Client
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import fitz  # NUEVO MOTOR: PyMuPDF (Sustituye a pdfplumber y a io)

# ==========================================
# 1. CONFIGURACIÓN DEL ENTORNO
# ==========================================
st.set_page_config(page_title="HCE - Medicina General", page_icon="⚕️", layout="wide")

# Inicialización de la Semilla Dimensional
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

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
    pdf.cell(32, 8, "ID/Documento:", border=0) 
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
# 5. LÓGICA REACTIVA Y CALLBACKS
# ==========================================
def buscar_paciente_por_id():
    fv = st.session_state.form_version
    key_id = f"val_id_{fv}"
    id_ingresado = st.session_state.get(key_id, "").strip()
    
    if id_ingresado:
        try:
            res = supabase.table("pacientes").select("*").eq("id_paciente", id_ingresado).execute()
            if res.data:
                paciente = res.data[0]
                st.session_state[f"val_nombres_{fv}"] = paciente.get("nombres", "")
                st.session_state[f"val_edad_{fv}"] = int(paciente.get("edad", 0))
                st.session_state[f"val_app_{fv}"] = paciente.get("antecedentes_personales", "")
                st.session_state[f"val_apf_{fv}"] = paciente.get("antecedentes_familiares", "")
                
                sexo_db = paciente.get("sexo", "Masculino")
                if sexo_db in ["Masculino", "Femenino"]:
                    st.session_state[f"val_sexo_{fv}"] = sexo_db
                    
                st.toast(f"Telemetría recuperada: Datos de {paciente.get('nombres')} sincronizados.", icon="✅")
        except Exception as e:
            st.toast(f"Error en la extracción de telemetría: {e}", icon="⚠️")

# ==========================================
# 6. TOPOLOGÍA DE NAVEGACIÓN Y HUD
# ==========================================
st.title("⚕️ Sistema Integrado de Historia Clínica")

usuario_actual = st.session_state.get("usuario_activo", "luis_pesantes")
perfil_activo = PERFILES_MEDICOS.get(usuario_actual, PERFILES_MEDICOS["luis_pesantes"])
st.caption(f"Sesión activa: {perfil_activo['nombre']}")
st.markdown("---")

tab_ingreso, tab_consulta = st.tabs(["📝 Ingreso y Síntesis Médica", "🔍 Auditoría Longitudinal del Paciente"])
lista_cie10 = cargar_catalogo_cie10_csv()

fv = st.session_state.form_version

# ------------------------------------------
# NODO A: ESCRITURA Y EMISIÓN
# ------------------------------------------
with tab_ingreso:
    if "pdf_reciente" in st.session_state:
        st.success(f"Protocolo Exitoso: Registro consolidado. Documento firmado por {st.session_state['medico_reciente']}.")
        st.download_button("📥 Descargar Receta Médica (PDF)", 
                           data=st.session_state["pdf_reciente"], 
                           file_name=st.session_state["nombre_pdf_reciente"], 
                           mime="application/pdf",
                           type="secondary")
        st.markdown("---")

    st.subheader("1. Filiación y Antecedentes")
    col_fil_1, col_fil_2 = st.columns(2)
    with col_fil_1:
        id_paciente = st.text_input("Documento de Identidad (Obligatorio):", key=f"val_id_{fv}", on_change=buscar_paciente_por_id).strip()
        nombres = st.text_input("Apellidos y Nombres:", key=f"val_nombres_{fv}").strip()
        sexo = st.selectbox("Sexo Biológico:", ["Masculino", "Femenino"], key=f"val_sexo_{fv}")
        edad = st.number_input("Edad (Años):", min_value=0, max_value=120, step=1, key=f"val_edad_{fv}")
    with col_fil_2:
        antecedentes_personales = st.text_area("APP:", height=80, key=f"val_app_{fv}").strip()
        antecedentes_familiares = st.text_area("APF:", height=80, key=f"val_apf_{fv}").strip()

    st.markdown("---")
    st.subheader("2. Signos Vitales y Antropometría")
    col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
    
    with col_v1: 
        pa = st.text_input("PA (mmHg):", placeholder="120/80", key=f"val_pa_{fv}").strip()
        if pa and "/" in pa:
            try:
                sys_str, dia_str = pa.split("/")
                sys_val, dia_val = int(sys_str), int(dia_str)
                pam_val = round((sys_val + 2 * dia_val) / 3, 1)
                
                if sys_val >= 140 or dia_val >= 90:
                    st.error(f"PAM: {pam_val} mmHg (Riesgo HTA)")
                else:
                    st.success(f"PAM: {pam_val} mmHg")
            except ValueError:
                st.warning("Formato PA inválido")
                
    with col_v2: fc = st.number_input("FC (lpm):", min_value=0, step=1, key=f"val_fc_{fv}")
    with col_v3: temp = st.number_input("Temp (°C):", format="%.1f", step=0.1, key=f"val_temp_{fv}")
    with col_v4: peso_kg = st.number_input("Peso (kg):", format="%.2f", min_value=0.0, step=0.1, key=f"val_peso_{fv}")
    with col_v5: talla_m = st.number_input("Talla (m):", format="%.2f", min_value=0.0, step=0.01, key=f"val_talla_{fv}")

    imc_texto_db = ""
    if talla_m > 0 and peso_kg > 0:
        imc_val = round(peso_kg / (talla_m ** 2), 2)
        
        if edad < 19:
            st.warning(f"⚠️ **Alerta Pediátrica:** El IMC calculado es **{imc_val}**. La estratificación estática está deshabilitada. Requiere validación manual.")
            imc_texto_db = f"[Antropometría] IMC: {imc_val} (Pediátrico)"
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
    
    with st.container(border=True):
        st.subheader("3. Matriz Clínica Estructurada")
        motivo_consulta = st.text_input("Motivo de Consulta:", key=f"val_motivo_{fv}").strip()
        enfermedad_actual = st.text_area("Enfermedad Actual:", height=100, key=f"val_ea_{fv}").strip()
        
        col_clin_1, col_clin_2 = st.columns(2)
        with col_clin_1:
            nodo_s = st.text_area("Subjetivo (S):", height=120, key=f"val_s_{fv}").strip()
            nodo_o = st.text_area("Objetivo (O):", height=120, key=f"val_o_{fv}").strip()
        with col_clin_2:
            nodo_a = st.text_area("Apreciación (A):", height=120, key=f"val_a_{fv}").strip()
            nodo_p = st.text_area("Plan de Tratamiento / Receta (P):", height=120, key=f"val_p_{fv}").strip()
            
        cie_10_seleccion = st.selectbox(
            "Diagnóstico CIE-10 Principal (Normativa Técnica):", 
            options=lista_cie10, 
            index=None,
            placeholder="Haga clic aquí y escriba el código o patología para filtrar...",
            key=f"val_cie10_{fv}"
        )

    # ==========================================
    # NUEVO MÓDULO: INGESTA DE LABORATORIO (PyMuPDF)
    # ==========================================
    st.markdown("---")
    with st.container(border=True):
        st.subheader("4. Panel de Exámenes de Laboratorio e Imagen")
        
        archivo_lab = st.file_uploader("Cargar reporte de laboratorio (Formato PDF exclusivo):", type=["pdf"], key=f"val_pdf_{fv}")
        texto_extraido_lab = ""
        
        if archivo_lab is not None:
            with st.spinner("Iniciando motor de abstracción C++ (PyMuPDF)..."):
                try:
                    # Inyección directa de bytes al motor avanzado
                    stream_bytes = archivo_lab.read()
                    doc = fitz.open(stream=stream_bytes, filetype="pdf")
                    
                    paginas = []
                    # Extracción agresiva ignorando estructuras complejas
                    for pagina in doc:
                        texto = pagina.get_text()
                        if texto:
                            paginas.append(texto)
                    
                    texto_extraido_lab = "\n".join(paginas)
                    
                    if not texto_extraido_lab.strip():
                        st.error("Falla Crítica de Compilación: El documento presenta un cifrado no resoluble o es una imagen plana oculta bajo una máscara PDF.")
                    else:
                        st.toast("Extracción de telemetría exitosa vía PyMuPDF.", icon="✅")
                        
                except Exception as e:
                    st.error(f"Excepción de tiempo de ejecución en el análisis del archivo: {e}")

        nodo_laboratorio = st.text_area(
            "Síntesis de Laboratorio (Valores Críticos / Alterados):", 
            value=texto_extraido_lab,
            height=150, 
            help="Edite el texto extraído y conserve únicamente los hallazgos patológicos o relevantes para la auditoría clínica.",
            key=f"val_lab_resumen_{fv}"
        )

    submitted = st.button("Guardar Historia y Procesar Receta", type="primary", use_container_width=True)

    if submitted:
        if not id_paciente or not nodo_p:
            st.error("Error Lógico: El Documento de Identidad y el Plan de Tratamiento (P) son mandatorios.")
        else:
            try:
                cie_10_final = cie_10_seleccion if cie_10_seleccion else "No especificado"
                nodo_o_final = f"{imc_texto_db}\n{nodo_o}" if imc_texto_db else nodo_o

                paciente_data = {
                    "id_paciente": id_paciente, "nombres": nombres, "edad": edad, "sexo": sexo,
                    "antecedentes_personales": antecedentes_personales, "antecedentes_familiares": antecedentes_familiares
                }
                supabase.table("pacientes").upsert(paciente_data).execute()

                evolucion_data = {
                    "id_paciente": id_paciente, "motivo_consulta": motivo_consulta, "enfermedad_actual": enfermedad_actual,
                    "presion_arterial": pa, "frecuencia_cardiaca": fc, "temperatura": temp,
                    "peso": peso_kg, "talla": talla_m,
                    "nodo_s": nodo_s, "nodo_o": nodo_o_final, "nodo_a": nodo_a, "nodo_p": nodo_p, 
                    "cie_10": cie_10_final,
                    "nodo_laboratorio": nodo_laboratorio
                }
                supabase.table("evoluciones").insert(evolucion_data).execute()
                
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                nombres_impresion = nombres if nombres else "Paciente No Registrado"
                
                pdf_bytes = generar_receta_pdf(id_paciente, nombres_impresion, edad, fecha_actual, nodo_p, perfil_activo)
                
                st.session_state["pdf_reciente"] = pdf_bytes
                st.session_state["nombre_pdf_reciente"] = f"Receta_{id_paciente}.pdf"
                st.session_state["medico_reciente"] = perfil_activo['nombre']
                
                st.session_state.form_version += 1
                st.rerun()

            except Exception as e:
                st.error(f"Falla transaccional a nivel de base de datos: {e}. Verifique la existencia de la columna 'nodo_laboratorio'.")

# ------------------------------------------
# NODO B: LECTURA Y AUDITORÍA (QUERY + ANALÍTICA)
# ------------------------------------------
with tab_consulta:
    st.subheader("Motor de Búsqueda y Análisis Clínico")
    
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
                
                res_evol = supabase.table("evoluciones").select("*").eq("id_paciente", busqueda_id).order("fecha", desc=True).execute()
                
                if not res_evol.data:
                    st.info("No existen evoluciones clínicas documentadas para este paciente.")
                else:
                    df_evol = pd.DataFrame(res_evol.data)
                    
                    if not df_evol.empty and 'peso' in df_evol.columns:
                        df_evol['fecha_dt'] = pd.to_datetime(df_evol['fecha'])
                        df_evol_sorted = df_evol.sort_values('fecha_dt')
                        
                        df_peso = df_evol_sorted[df_evol_sorted['peso'] > 0][['fecha_dt', 'peso']]
                        
                        if not df_peso.empty and len(df_peso) > 1:
                            st.markdown("### 📈 Monitor Epidemiológico: Fluctuación Ponderal")
                            df_peso['Fecha'] = df_peso['fecha_dt'].dt.strftime('%d/%m/%Y')
                            df_peso = df_peso.set_index('Fecha')
                            
                            peso_actual = float(df_peso['peso'].iloc[-1])
                            peso_previo = float(df_peso['peso'].iloc[-2])
                            delta_peso = round(peso_actual - peso_previo, 2)
                            
                            col_metric, col_chart = st.columns([1, 3])
                            with col_metric:
                                st.metric(label="Peso (Último Control)", value=f"{peso_actual} kg", delta=f"{delta_peso} kg", delta_color="inverse")
                            with col_chart:
                                st.line_chart(df_peso['peso'])
                            st.markdown("---")

                    st.markdown("### Línea de Tiempo Clínica (Controles Previos)")
                    for evol in res_evol.data:
                        raw_date = evol.get("fecha", "")
                        fmt_date = raw_date[:10] if raw_date else "Fecha desconocida"
                        
                        with st.expander(f"🗓️ Control: {fmt_date} | Motivo: {evol.get('motivo_consulta', 'No especificado')} | CIE-10: {evol.get('cie_10', 'N/A')}"):
                            st.write(f"**Enfermedad Actual:** {evol.get('enfermedad_actual', 'N/A')}")
                            st.markdown("**Triaje Vital:**")
                            
                            peso_hist = evol.get('peso')
                            talla_hist = evol.get('talla')
                            str_peso = f"{peso_hist} kg" if peso_hist is not None and peso_hist > 0 else "N/A"
                            str_talla = f"{talla_hist} m" if talla_hist is not None and talla_hist > 0 else "N/A"
                            
                            st.code(f"PA: {evol.get('presion_arterial','N/A')} | FC: {evol.get('frecuencia_cardiaca','N/A')} | Temp: {evol.get('temperatura','N/A')} | Peso: {str_peso} | Talla: {str_talla}")
                            
                            st.markdown("**Matriz SOAP y Complementarios:**")
                            st.write(f"**S:** {evol.get('nodo_s', '')}")
                            st.write(f"**O:** {evol.get('nodo_o', '')}")
                            st.write(f"**A:** {evol.get('nodo_a', '')}")
                            st.write(f"**P:** {evol.get('nodo_p', '')}")
                            
                            lab_historico = evol.get('nodo_laboratorio')
                            if lab_historico:
                                st.info(f"**🔬 Síntesis de Laboratorio:**\n{lab_historico}")
                            
        except Exception as e:
            st.error(f"Falla en la recuperación de telemetría: {e}")
