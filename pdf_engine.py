from fpdf import FPDF

# ... (Mantenga aquí su función generar_receta_pdf sin cambios) ...

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
    
    # Fila 1 - Cabeceras
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(50, 5, "INSTITUCION:", border="LTR")
    pdf.cell(40, 5, "RUC:", border="LTR")
    pdf.cell(30, 5, "CIIU:", border="LTR")
    pdf.cell(0, 5, "ESTABLECIMIENTO:", border="LTR", ln=True)
    
    # Fila 1 - Datos
    pdf.set_font("Arial", '', 8)
    pdf.cell(50, 6, datos.get('institucion', ''), border="LBR")
    pdf.cell(40, 6, datos.get('ruc', ''), border="LBR")
    pdf.cell(30, 6, datos.get('ciiu', ''), border="LBR")
    pdf.cell(0, 6, datos.get('centro_trabajo', ''), border="LBR", ln=True)
    
    # Fila 2 - Cabeceras
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(80, 5, "APELLIDOS Y NOMBRES:", border="LTR")
    pdf.cell(40, 5, "IDENTIFICACION (CI):", border="LTR")
    pdf.cell(0, 5, "PUESTO DE TRABAJO:", border="LTR", ln=True)
    
    # Fila 2 - Datos
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
    # Lógica condicional para renderizar la X en la casilla correcta
    pdf.cell(20, 8, f"[{'X' if ev=='INGRESO' else ' '}] ING", border="TB")
    pdf.cell(20, 8, f"[{'X' if ev=='PERIÓDICO' else ' '}] PER", border="TB")
    pdf.cell(20, 8, f"[{'X' if ev=='REINTEGRO' else ' '}] REIN", border="TB")
    pdf.cell(0, 8, f"[{'X' if ev=='RETIRO' else ' '}] RET", border="RTB", ln=True)
    
    pdf.ln(5)
    
    # =========================================
    # SECCION C
    # =========================================
    header_gris(" C. APTITUD MEDICA PARA EL TRABAJO")
    
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 6, " Después de la valoración médica ocupacional se certifica que la persona en mención es calificada como:", border="LTR")
    
    dic = datos.get('dictamen', '')
    pdf.set_font("Arial", 'B', 9)
    aptitudes = f"[{'X' if dic=='APTO' else ' '}] APTO     [{'X' if dic=='APTO EN OBSERVACIÓN' else ' '}] APTO EN OBSERV.     [{'X' if dic=='APTO CON LIMITACIONES' else ' '}] APTO CON LIMIT.     [{'X' if dic=='NO APTO' else ' '}] NO APTO"
    pdf.cell(0, 8, aptitudes, border="LBR", align='C', ln=True)
    
    pdf.ln(5)
    
    # =========================================
    # SECCION D
    # =========================================
    header_gris(" D. RECOMENDACIONES / OBSERVACIONES")
    
    pdf.set_font("Arial", '', 9)
    # Dejamos espacio en blanco para que el cuadro tenga altura de bloque de texto
    pdf.multi_cell(0, 5, " " + datos.get('observaciones', '') + "\n\n\n", border="LTR")
    
    legal_text = "Con este documento certifico que el trabajador se ha sometido a la evaluación médica requerida para el puesto laboral y se le ha informado sobre los riesgos relacionados con el trabajo emitiendo recomendaciones relacionadas con su estado de salud. La presente certificación se expide con base en el formulario de Evaluación Ocupacional, el cual tiene carácter confidencial."
    pdf.set_font("Arial", '', 7)
    pdf.multi_cell(0, 4, legal_text, border="LBR")
    
    pdf.ln(25)
    
    # =========================================
    # SECCION E (Firmas y Sellos)
    # =========================================
    pdf.set_font("Arial", 'B', 9)
    y = pdf.get_y()
    
    # Dibujo de líneas de firma (Coordenadas exactas)
    pdf.line(30, y, 80, y)
    pdf.line(130, y, 180, y)
    
    pdf.cell(95, 5, "FIRMA Y SELLO MEDICO", ln=False, align='C')
    pdf.cell(95, 5, "FIRMA O HUELLA DEL TRABAJADOR", ln=True, align='C')
    
    pdf.set_font("Arial", '', 8)
    pdf.cell(95, 5, datos.get('medico_nombre', ''), ln=False, align='C')
    pdf.cell(95, 5, f"CI: {datos.get('id_paciente', '')}", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')
