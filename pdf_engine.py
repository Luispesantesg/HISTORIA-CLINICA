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
    
    return pdf.output(dest='S').encode('latin-1', 'replace')


def generar_certificado_aptitud_pdf(id_paciente: str, nombres: str, edad: int, fecha: str, cargo: str, dictamen: str, observaciones: str, perfil_medico: dict) -> bytes:
    """Renderiza el documento legal de Aptitud Médica Ocupacional."""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabecera Normativa
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "CERTIFICADO DE APTITUD MEDICA OCUPACIONAL", ln=True, align='C')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, f"{perfil_medico['nombre']} - {perfil_medico['especialidad']}", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, perfil_medico['subtitulo'], ln=True, align='C')
    pdf.line(10, 35, 200, 35)
    pdf.ln(10)
    
    # Datos de Filiación y Laborales
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, "Fecha de Emision:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, fecha, ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, "Paciente / Empleado:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 8, nombres, ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, "ID/Documento:", border=0) 
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 8, id_paciente, ln=False)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 8, "Edad:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, str(edad), ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, "Puesto de Trabajo:", border=0)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, cargo, ln=True)
    
    pdf.line(10, 80, 200, 80)
    pdf.ln(10)
    
    # Dictamen y Resoluciones
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "DICTAMEN MEDICO:", ln=True)
    
    # Codificación de color basada en el dictamen (Estética Formal)
    if "No Apto" in dictamen:
        pdf.set_text_color(200, 0, 0)
    elif "Restricciones" in dictamen or "Aplazada" in dictamen:
        pdf.set_text_color(200, 100, 0)
    else:
        pdf.set_text_color(0, 100, 0)
        
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, dictamen.upper(), ln=True, align='C')
    
    # Restaurar color negro para observaciones
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Observaciones / Restricciones:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, observaciones if observaciones else "Ninguna observacion adicional documentada.")
    
    # Firma y Sello
    pdf.ln(30)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Firma y Sello Medico", ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, perfil_medico['nombre'], ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')
