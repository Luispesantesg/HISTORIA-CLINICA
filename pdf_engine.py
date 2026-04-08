from fpdf import FPDF

def generar_receta_pdf(id_paciente: str, nombres: str, edad: int, fecha: str, plan_terapeutico: str, perfil_medico: dict) -> bytes:
    """Renderiza el documento legal de Receta Médica Estándar."""
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
    
    return bytes(pdf.output())


def generar_certificado_excel_pdf(datos: dict) -> bytes:
    """Renderiza la matriz de Aptitud Ocupacional simulando Excel usando geometría pura nativa."""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "CERTIFICADO - EVALUACION MEDICA OCUPACIONAL", ln=True, align='C')
    pdf.ln(5)
    
    # Motor de sombreado para cabeceras tipo Excel
    def header_gris(texto):
        pdf.set_fill_color(217, 217, 217) # Gris estándar de Excel
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, texto, border=1, fill=True, ln=True)

    # =========================================
    # SECCION A
    # =========================================
    header_gris(" A. DATOS DEL ESTABLECIMIENTO - DATOS DEL USUARIO")
    
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(50, 5, "INSTITUCION:", border="LTR")
    pdf.cell(40, 5, "RUC:", border="LTR")
    pdf.cell(30, 5, "CIIU:", border="LTR")
    pdf.cell(0, 5, "ESTABLECIMIENTO:", border="LTR", ln=True)
    
    pdf.set_font("Arial", '', 8)
    pdf.cell(50, 6, datos.get('institucion', ''), border="LBR")
    pdf.cell(40, 6, datos.get('ruc', ''), border="LBR")
    pdf.cell(30, 6, datos.get('ciiu', ''), border="LBR")
    pdf.cell(0, 6, datos.get('centro_trabajo', ''), border="LBR", ln=True)
    
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(80, 5, "APELLIDOS Y NOMBRES:", border="LTR")
    pdf.cell(40, 5, "IDENTIFICACION (CI):", border="LTR")
    pdf.cell(0, 5, "PUESTO DE TRABAJO:", border="LTR", ln=True)
    
    pdf.set_font("Arial", '', 8)
    pdf.cell(80, 6, datos.get('nombres', ''), border="LBR")
    pdf.cell(40, 6, datos.get('id_paciente', ''), border="LBR")
    pdf.cell(0, 6, datos.get('cargo', ''), border="LBR", ln=True)
    
    pdf.ln(5)
    
    # =========================================
    # SECCION B
    # =========================================
    header_gris(" B. DATOS GENERALES")
    
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(50, 8, " FECHA DE EMISION:", border=1)
    pdf.set_font("Arial", '', 8)
    pdf.cell(35, 8, datos.get('fecha_emision', ''), border=1)
    
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(30, 8, " EVALUACION:", border="LTB")
    
    ev = datos.get('tipo_evaluacion', '')
    pdf.set_font("Arial", '', 8)
    pdf.cell(20, 8, f"[{'X' if ev=='INGRESO' else ' '}] ING", border="TB")
    pdf.cell(20, 8, f"[{'X' if ev=='PERIÓDICO' else ' '}] PER", border="TB")
    pdf.cell(20, 8, f"[{'X' if ev=='REINTEGRO' else ' '}] REIN", border="TB")
    pdf.cell(0, 8, f"[{'X' if ev=='RETIRO' else ' '}] RET", border="RTB", ln=True)
    
    pdf.ln(5)
    
    # =========================================
    # SECCION C (CORREGIDA - CADENA COMPRIMIDA)
    # =========================================
    header_gris(" C. APTITUD MEDICA PARA EL TRABAJO")
    
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, " Despues de la valoracion medica ocupacional se certifica que la persona en mencion es calificada como:", border="LTR")
    
    dic = datos.get('dictamen', '')
    pdf.set_font("Arial", 'B', 8)
    
    # Evaluación lógica estricta para inyectar la X
    chk1 = 'X' if dic == 'APTO' else ' '
    chk2 = 'X' if dic == 'APTO EN OBSERVACIÓN' else ' '
    chk3 = 'X' if dic == 'APTO CON LIMITACIONES' else ' '
    chk4 = 'X' if dic == 'NO APTO' else ' '
    
    # Cadena optimizada tipográficamente para no desbordar
    aptitudes = f"[{chk1}] APTO      [{chk2}] EN OBSERVACION      [{chk3}] CON LIMITACIONES      [{chk4}] NO APTO"
    
    # Impresión en un solo bloque al ancho total (0) garantizando que no se escape de la hoja
    pdf.cell(0, 8, aptitudes, border="LBR", align='C', ln=True)
    
    pdf.ln(5)
    
    # =========================================
    # SECCION D
    # =========================================
    header_gris(" D. RECOMENDACIONES / OBSERVACIONES")
    
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5, " " + datos.get('observaciones', '') + "\n\n\n", border="LTR")
    
    legal_text = "Con este documento certifico que el trabajador se ha sometido a la evaluacion medica requerida para el puesto laboral y se le ha informado sobre los riesgos relacionados con el trabajo emitiendo recomendaciones relacionadas con su estado de salud. La presente certificacion se expide con base en el formulario de Evaluacion Ocupacional, el cual tiene caracter confidencial."
    pdf.set_font("Arial", '', 7)
    pdf.multi_cell(0, 4, legal_text, border="LBR")
    
    pdf.ln(25)
    
    # =========================================
    # SECCION E
    # =========================================
    pdf.set_font("Arial", 'B', 9)
    y = pdf.get_y()
    
    pdf.line(30, y, 80, y)
    pdf.line(130, y, 180, y)
    
    pdf.cell(95, 5, "FIRMA Y SELLO MEDICO", ln=False, align='C')
