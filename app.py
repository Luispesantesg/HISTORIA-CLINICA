import streamlit as st
from datetime import datetime
import pandas as pd
import fitz  
import tempfile
import os

from auth import verificar_autenticacion
from database import supabase, cargar_catalogo_cie10_csv, PERFILES_MEDICOS
from pdf_engine import generar_receta_pdf, generar_certificado_excel_pdf
from nlp_parser import estructurar_telemetria_laboratorio

# ==========================================
# CONFIGURACIÓN DEL ENTORNO
# ==========================================
st.set_page_config(page_title="HCE - Medicina General y Ocupacional", page_icon="⚕️", layout="wide")

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if not verificar_autenticacion():
    st.stop()

# ==========================================
# LÓGICA REACTIVA LOCAL
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
# TOPOLOGÍA DE NAVEGACIÓN Y HUD
# ==========================================
st.title("⚕️ Sistema Integrado de Historia Clínica")

usuario_actual = st.session_state.get("usuario_activo", "luis_pesantes")
perfil_activo = PERFILES_MEDICOS.get(usuario_actual, PERFILES_MEDICOS["luis_pesantes"])
st.caption(f"Sesión activa: {perfil_activo['nombre']}")
st.markdown("---")

tab_ingreso, tab_consulta, tab_ocupacional = st.tabs([
    "📝 Medicina General", 
    "🔍 Auditoría Longitudinal",
    "⚙️ Salud Ocupacional (Formatos)"
])

lista_cie10 = cargar_catalogo_cie10_csv()
fv = st.session_state.form_version

# ------------------------------------------
# NODO A: ESCRITURA Y EMISIÓN (MEDICINA GENERAL)
# ------------------------------------------
with tab_ingreso:
    if "pdf_reciente" in st.session_state:
        st.success(f"Protocolo Exitoso: Registro consolidado. Documento firmado por {st.session_state['medico_reciente']}.")
        st.download_button("📥 Descargar Receta Médica (PDF)", 
                           data=st.session_state["pdf_reciente"], 
                           file_name=st.session_state["nombre_pdf_reciente"], 
                           mime="application/pdf")
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
                if sys_val >= 140 or dia_val >= 90: st.error(f"PAM: {pam_val} mmHg (Riesgo HTA)")
                else: st.success(f"PAM: {pam_val} mmHg")
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
            st.warning(f"⚠️ **Alerta Pediátrica:** IMC {imc_val}")
            imc_texto_db = f"[Antropometría] IMC: {imc_val} (Pediátrico)"
        else:
            if imc_val < 18.5: estrato = "Bajo peso"
            elif imc_val < 24.9: estrato = "Normopeso"
            elif imc_val < 29.9: estrato = "Sobrepeso"
            elif imc_val < 34.9: estrato = "Obesidad I"
            elif imc_val < 39.9: estrato = "Obesidad II"
            else: estrato = "Obesidad III"
            st.info(f"IMC de **{imc_val}** - Estratificación: **{estrato}**")
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
            
        cie_10_seleccion = st.selectbox("Diagnóstico CIE-10 Principal:", options=lista_cie10, index=None, key=f"val_cie10_{fv}")

    st.markdown("---")
    with st.container(border=True):
        st.subheader("4. Panel Estructurado de Laboratorio asistido por IA")
        archivo_lab = st.file_uploader("Cargar reporte de laboratorio (Formato PDF exclusivo):", type=["pdf"], key=f"val_pdf_file_{fv}")
        
        key_df_lab = f"df_lab_state_{fv}"
        if key_df_lab not in st.session_state:
            st.session_state[key_df_lab] = pd.DataFrame(columns=["Biomarcador", "Resultado", "Unidad", "Rango de Referencia"])

        if archivo_lab is not None:
            if st.button("⚙️ Ejecutar Extracción Automatizada (NLP)", type="secondary"):
                with st.spinner("Conectando con el motor de inferencia..."):
                    ruta_fisica = ""
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(archivo_lab.getvalue())
                            ruta_fisica = tmp_file.name
                        
                        doc = fitz.open(ruta_fisica)
                        paginas = [pagina.get_text() for pagina in doc if pagina.get_text()]
                        texto_crudo = "\n".join(paginas)
                        doc.close()
                        
                        if not texto_crudo.strip():
                            st.error("Diagnóstico Crítico: El archivo físico no contiene caracteres legibles.")
                        else:
                            df_generado = estructurar_telemetria_laboratorio(texto_crudo)
                            st.session_state[key_df_lab] = df_generado
                            st.success("Protocolo NLP Exitoso.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Falla en el pipeline: {e}")
                    finally:
                        if ruta_fisica and os.path.exists(ruta_fisica):
                            os.remove(ruta_fisica)

        st.caption("ℹ️ Revise los datos extraídos por la IA.")
        df_lab_interactivo = st.data_editor(st.session_state[key_df_lab], num_rows="dynamic", width='stretch', hide_index=True, key=f"editor_json_lab_{fv}")

    submitted = st.button("Guardar Historia y Procesar Receta", type="primary", width='stretch')

    if submitted:
        if not id_paciente or not nodo_p:
            st.error("Error Lógico: El Documento de Identidad y el Plan de Tratamiento son mandatorios.")
        else:
            try:
                cie_10_final = cie_10_seleccion if cie_10_seleccion else "No especificado"
                nodo_o_final = f"{imc_texto_db}\n{nodo_o}" if imc_texto_db else nodo_o
                df_filtrado = df_lab_interactivo.dropna(how='all')
                matriz_lab_json = df_filtrado.to_dict(orient="records")

                paciente_data = {
                    "id_paciente": id_paciente, "nombres": nombres, "edad": edad, "sexo": sexo,
                    "antecedentes_personales": antecedentes_personales, "antecedentes_familiares": antecedentes_familiares
                }
                supabase.table("pacientes").upsert(paciente_data).execute()

                evolucion_data = {
                    "id_paciente": id_paciente, "motivo_consulta": motivo_consulta, "enfermedad_actual": enfermedad_actual,
                    "presion_arterial": pa, "frecuencia_cardiaca": fc, "temperatura": temp,
                    "peso": float(peso_kg), "talla": float(talla_m),
                    "nodo_s": nodo_s, "nodo_o": nodo_o_final, "nodo_a": nodo_a, "nodo_p": nodo_p, 
                    "cie_10": cie_10_final, "nodo_laboratorio": matriz_lab_json 
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
                st.error(f"Falla transaccional: {e}")

# ------------------------------------------
# NODO B: LECTURA Y AUDITORÍA (QUERY + ANALÍTICA)
# ------------------------------------------
with tab_consulta:
    st.subheader("Motor de Búsqueda Clínico")
    col_busqueda, col_vacia = st.columns([1, 2])
    with col_busqueda:
        busqueda_id = st.text_input("Ingrese el Documento del Paciente:").strip()
        btn_buscar = st.button("Ejecutar Extracción", type="primary", width='stretch')

    if btn_buscar and busqueda_id:
        try:
            res_paciente = supabase.table("pacientes").select("*").eq("id_paciente", busqueda_id).execute()
            if not res_paciente.data:
                st.warning("El Documento ingresado no posee registros.")
            else:
                paciente = res_paciente.data[0]
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.info(f"**Paciente:** {paciente.get('nombres', 'N/A')}\n\n**Edad:** {paciente.get('edad', 'N/A')} años")
                with col_info2:
                    st.error(f"**APP:** {paciente.get('antecedentes_personales', 'Sin registros')}")
                
                st.markdown("---")
                res_evol = supabase.table("evoluciones").select("*").eq("id_paciente", busqueda_id).order("fecha", desc=True).execute()
                
                if not res_evol.data:
                    st.info("No existen evoluciones clínicas documentadas.")
                else:
                    st.markdown("#### Línea de Tiempo Clínica")
                    for evol in res_evol.data:
                        raw_date = evol.get("fecha", "")
                        fmt_date = raw_date[:10] if raw_date else "Fecha desconocida"
                        with st.expander(f"🗓️ Control: {fmt_date} | Motivo: {evol.get('motivo_consulta', 'N/A')}"):
                            st.write(f"**Enfermedad Actual:** {evol.get('enfermedad_actual', 'N/A')}")
                            st.write(f"**S:** {evol.get('nodo_s', '')}\n\n**O:** {evol.get('nodo_o', '')}\n\n**A:** {evol.get('nodo_a', '')}\n\n**P:** {evol.get('nodo_p', '')}")
                            lab_historico = evol.get('nodo_laboratorio')
                            if isinstance(lab_historico, list):
                                st.dataframe(pd.DataFrame(lab_historico), width='stretch', hide_index=True)
                
                st.markdown("---")
                st.markdown("### ⚙️ Historial de Salud Ocupacional")
                res_oc = supabase.table("evaluaciones_ocupacionales").select("*").eq("id_paciente", busqueda_id).order("fecha", desc=True).execute()
                if not res_oc.data:
                    st.info("No existen evaluaciones de aptitud documentadas.")
                else:
                    for eval_oc in res_oc.data:
                        raw_date_oc = eval_oc.get("fecha", "")
                        fmt_date_oc = raw_date_oc[:10] if raw_date_oc else "Fecha desconocida"
                        with st.expander(f"👷 Evaluación: {fmt_date_oc} | Cargo: {eval_oc.get('cargo', 'N/A')} | Dictamen: {eval_oc.get('dictamen', 'N/A')}"):
                            st.write(f"**Observaciones:** {eval_oc.get('observaciones', 'Ninguna')}")

        except Exception as e:
            st.error(f"Falla crítica: {e}")

# ------------------------------------------
# NODO C: SALUD OCUPACIONAL (RENDER TABULAR HTML)
# ------------------------------------------
with tab_ocupacional:
    if "pdf_ocupacional_reciente" in st.session_state:
        st.success("Protocolo Exitoso: Certificado de Aptitud Normativo emitido.")
        st.download_button("📥 Descargar Formato Excel (PDF)",
                           data=st.session_state["pdf_ocupacional_reciente"],
                           file_name=st.session_state["nombre_pdf_ocupacional_reciente"],
                           mime="application/pdf",
                           key=f"btn_dw_ocup_{fv}")
        st.markdown("---")

    st.subheader("Generador de Certificado Ocupacional (Formato Matriz)")
    
    with st.container(border=True):
        st.markdown("**A. Datos del Establecimiento**")
        col_oc_1, col_oc_2, col_oc_3 = st.columns(3)
        institucion_oc = col_oc_1.text_input("Institución del Sistema:", value="MSP", key=f"val_inst_{fv}").strip()
        ruc_oc = col_oc_2.text_input("RUC:", key=f"val_ruc_{fv}").strip()
        ciiu_oc = col_oc_3.text_input("CIIU:", key=f"val_ciiu_{fv}").strip()
        centro_trabajo_oc = st.text_input("Establecimiento / Centro de Trabajo:", key=f"val_centro_{fv}").strip()

    with st.container(border=True):
        st.markdown("**B. Datos del Empleado**")
        id_pac_oc_val = st.session_state.get(f"val_id_{fv}", "")
        nom_oc_val = st.session_state.get(f"val_nombres_{fv}", "")
        
        col_ne_1, col_ne_2 = st.columns(2)
        id_paciente_oc = col_ne_1.text_input("Identificación (CI):", value=id_pac_oc_val, key=f"val_id_oc_{fv}").strip()
        nombres_oc = col_ne_2.text_input("Apellidos y Nombres:", value=nom_oc_val, key=f"val_nom_oc_{fv}").strip()
        cargo_oc = st.text_input("Puesto de Trabajo / Cargo (Obligatorio):", key=f"val_cargo_oc_{fv}").strip()

    with st.container(border=True):
        st.markdown("**C. Evaluación y Aptitud**")
        tipo_evaluacion_oc = st.radio("Tipo de Evaluación:", ["INGRESO", "PERIÓDICO", "REINTEGRO", "RETIRO"], horizontal=True, key=f"val_tipo_ev_{fv}")
        dictamen_oc = st.selectbox("Dictamen de Aptitud Médica:", ["APTO", "APTO EN OBSERVACIÓN", "APTO CON LIMITACIONES", "NO APTO"], key=f"val_dictamen_{fv}")
        obs_oc = st.text_area("Recomendaciones / Observaciones:", height=100, key=f"val_obs_oc_{fv}").strip()

    submitted_oc = st.button("Renderizar Formato y Guardar Evaluación", type="primary", width='stretch', key=f"btn_sub_oc_{fv}")

    if submitted_oc:
        if not id_paciente_oc or not cargo_oc:
            st.error("Error Lógico: Identificación y Cargo son mandatorios.")
        else:
            try:
                fecha_actual_oc = datetime.now().strftime("%Y-%m-%d")
                
                # 1. Empaquetamiento de telemetría para Jinja2
                datos_certificado = {
                    "institucion": institucion_oc.upper(),
                    "ruc": ruc_oc,
                    "ciiu": ciiu_oc,
                    "centro_trabajo": centro_trabajo_oc.upper(),
                    "nombres": nombres_oc.upper(),
                    "id_paciente": id_paciente_oc,
                    "cargo": cargo_oc.upper(),
                    "fecha_emision": fecha_actual_oc,
                    "tipo_evaluacion": tipo_evaluacion_oc,
                    "dictamen": dictamen_oc,
                    "observaciones": obs_oc.upper(),
                    "medico_nombre": perfil_activo['nombre'],
                    "medico_codigo": "MSP-12345" # Parametrizable a futuro en la matriz de perfiles
                }

                # 2. Transacción a Supabase (Conservando el esquema compatible existente)
                evaluacion_data = {
                    "id_paciente": id_paciente_oc,
                    "cargo": cargo_oc,
                    "dictamen": dictamen_oc,
                    "observaciones": obs_oc
                }
                supabase.table("evaluaciones_ocupacionales").insert(evaluacion_data).execute()

                # 3. Generación del Binario HTML a PDF
                pdf_bytes_oc = generar_certificado_excel_pdf(datos_certificado)

                st.session_state["pdf_ocupacional_reciente"] = pdf_bytes_oc
                st.session_state["nombre_pdf_ocupacional_reciente"] = f"Aptitud_Matriz_{id_paciente_oc}.pdf"
                st.session_state.form_version += 1
                st.rerun()

            except Exception as e:
                st.error(f"Falla transaccional o de renderizado: {e}")
