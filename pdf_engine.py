from fpdf import FPDF
from xhtml2pdf import pisa
import io
from jinja2 import Template

def generar_receta_pdf(id_paciente: str, nombres: str, edad: int, fecha: str, plan_terapeutico: str, perfil_medico: dict) -> bytes:
    """Renderiza el documento legal de Receta Médica Estándar (FPDF)."""
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

def generar_certificado_excel_pdf(datos: dict) -> bytes:
    """Renderiza un PDF con estructura tabular rígida simulando el Excel normativo (HTML/CSS)."""
    
    html_template = """
    <html>
    <head>
        <style>
            @page { size: A4; margin: 1.5cm; }
            body { font-family: Helvetica, Arial, sans-serif; font-size: 11px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th, td { border: 1px solid #000; padding: 6px; text-align: left; vertical-align: middle; }
            .header-gray { background-color: #D9D9D9; font-weight: bold; font-size: 12px; }
            .title { text-align: center; font-size: 15px; font-weight: bold; padding-bottom: 15px; }
            .center { text-align: center; }
        </style>
    </head>
    <body>
        <div class="title">CERTIFICADO - EVALUACIÓN MÉDICA OCUPACIONAL</div>
        
        <table>
            <tr><td colspan="4" class="header-gray">A. DATOS DEL ESTABLECIMIENTO - DATOS DEL USUARIO</td></tr>
            <tr>
                <td><b>INSTITUCIÓN:</b><br>{{ institucion }}</td>
                <td><b>RUC:</b><br>{{ ruc }}</td>
                <td><b>CIIU:</b><br>{{ ciiu }}</td>
                <td><b>ESTABLECIMIENTO:</b><br>{{ centro_trabajo }}</td>
            </tr>
            <tr>
                <td colspan="2"><b>APELLIDOS Y NOMBRES:</b><br>{{ nombres }}</td>
                <td><b>IDENTIFICACIÓN (CI):</b><br>{{ id_paciente }}</td>
                <td><b>PUESTO DE TRABAJO:</b><br>{{ cargo }}</td>
            </tr>
        </table>

        <table>
            <tr><td colspan="2" class="header-gray">B. DATOS GENERALES</td></tr>
            <tr>
                <td style="width: 50%;"><b>FECHA DE EMISIÓN:</b> {{ fecha_emision }}</td>
                <td style="width: 50%;">
                    <b>EVALUACIÓN:</b> 
                    [{{ 'X' if tipo_evaluacion == 'INGRESO' else ' ' }}] INGRESO &nbsp;
                    [{{ 'X' if tipo_evaluacion == 'PERIÓDICO' else ' ' }}] PERIÓDICO &nbsp;
                    [{{ 'X' if tipo_evaluacion == 'RETIRO' else ' ' }}] RETIRO
                </td>
            </tr>
        </table>

        <table>
            <tr><td class="header-gray">C. APTITUD MÉDICA PARA EL TRABAJO</td></tr>
            <tr>
                <td>Después de la valoración médica ocupacional se certifica que la persona en mención es calificada como:<br><br>
                    <div class="center">
                        <b>[{{ 'X' if dictamen == 'APTO' else ' ' }}] APTO</b> &nbsp;&nbsp;&nbsp;
                        <b>[{{ 'X' if dictamen == 'APTO EN OBSERVACIÓN' else ' ' }}] APTO EN OBSERVACIÓN</b> &nbsp;&nbsp;&nbsp;
                        <b>[{{ 'X' if dictamen == 'APTO CON LIMITACIONES' else ' ' }}] APTO CON LIMITACIONES</b> &nbsp;&nbsp;&nbsp;
                        <b>[{{ 'X' if dictamen == 'NO APTO' else ' ' }}] NO APTO</b>
                    </div>
                </td>
            </tr>
        </table>

        <table>
            <tr><td class="header-gray">D. RECOMENDACIONES/OBSERVACIONES</td></tr>
            <tr><td style="height: 100px; vertical-align: top;">{{ observaciones }}</td></tr>
            <tr>
                <td style="font-size: 10px; text-align: justify; padding: 10px;">
                    Con este documento certifico que el trabajador se ha sometido a la evaluación médica requerida para el puesto laboral y se le ha informado sobre los riesgos relacionados con el trabajo emitiendo recomendaciones relacionadas con su estado de salud. La presente certificación se expide con base en el formulario de Evaluación Ocupacional, el cual tiene carácter confidencial.
                </td>
            </tr>
        </table>

        <table style="border: none; margin-top: 50px;">
            <tr style="border: none;">
                <td style="border: none; text-align: center; width: 50%;">
                    __________________________________<br>
                    <b>FIRMA Y SELLO MÉDICO</b><br>
                    {{ medico_nombre }}
                </td>
                <td style="border: none; text-align: center; width: 50%;">
                    __________________________________<br>
                    <b>FIRMA O HUELLA DEL TRABAJADOR</b><br>
                    CI: {{ id_paciente }}
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_renderizado = template.render(**datos)
    
    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_renderizado), dest=buffer)
    
    if pisa_status.err:
        raise RuntimeError("Fallo interno en la conversión de HTML a PDF tabular.")
        
    return buffer.getvalue()
