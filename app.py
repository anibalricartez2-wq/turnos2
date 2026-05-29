# --- PDF CORREGIDO (Seguro ante errores de tipo) ---
def generar_pdf(df, resumen, limite, mes, anio):
    # Validamos que el resumen sea un DataFrame válido
    if resumen is None or not isinstance(resumen, pd.DataFrame):
        resumen = pd.DataFrame() 

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Cronograma {calendar.month_name[mes]} {anio}", ln=True, align="C")
    pdf.ln(10)
    
    # Tabla Grilla
    pdf.set_font("Arial", "B", 8)
    for col in ["Fecha", "Día", "Mañana", "Tarde"]: pdf.cell(45, 7, col, 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    for i, row in df.iterrows():
        pdf.cell(45, 7, f"{i.day}/{i.month}", 1)
        pdf.cell(45, 7, str(row['Dia']), 1)
        pdf.cell(45, 7, str(row['M']), 1)
        pdf.cell(45, 7, str(row['T']), 1, ln=True)
    
    # Tabla Resumen (Solo si no está vacía)
    if not resumen.empty:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Resumen de Asignaciones", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        for col in ["Agente", "Horas", "Turnos M", "Turnos T"]: pdf.cell(45, 7, col, 1)
        pdf.ln()
        pdf.set_font("Arial", "", 10)
        for n, row in resumen.iterrows():
            pdf.cell(45, 7, str(n), 1)
            pdf.cell(45, 7, str(int(row['Horas'])), 1)
            pdf.cell(45, 7, str(int(row['Turnos M'])), 1)
            pdf.cell(45, 7, str(int(row['Turnos T'])), 1, ln=True)
    
    buffer = BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer
