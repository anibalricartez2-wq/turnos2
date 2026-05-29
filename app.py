import streamlit as st
import pandas as pd
import calendar
from datetime import date
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Planificador SMN", layout="wide")

if "calculado" not in st.session_state:
    st.session_state.update({"calculado": False, "grilla": None, "resumen": None})

class Agente:
    def __init__(self, nombre, lim):
        self.nombre = nombre
        self.lim = lim
        self.horas = 0
        self.conteo = {'M': 0, 'T': 0}
        self.pref_m, self.pref_t = set(), set()
        self.disp_m, self.disp_t = set(range(7)), set(range(7))

    def configurar(self, d_m, d_t, p_m, p_t):
        mapa = {"Lu":0, "Ma":1, "Mi":2, "Ju":3, "Vi":4, "Sá":5, "Do":6}
        self.disp_m = {mapa[d] for d in d_m}
        self.disp_t = {mapa[d] for d in d_t}
        self.pref_m = {int(d) for d in p_m}
        self.pref_t = {int(d) for d in p_t}

def generar_pdf(df, resumen, limite, mes, anio):
    pdf = FPDF()
    # PÁGINA 1: GRILLA
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Cronograma {calendar.month_name[mes]} {anio}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 8)
    for col in ["Fecha", "Día", "Mañana", "Tarde"]: pdf.cell(45, 7, col, 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    for i, row in df.iterrows():
        pdf.cell(45, 7, f"{i.day}/{i.month}", 1)
        pdf.cell(45, 7, str(row['Dia']), 1)
        pdf.cell(45, 7, str(row['M']), 1)
        pdf.cell(45, 7, str(row['T']), 1, ln=True)
    
    # PÁGINA 2: RESUMEN
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Resumen de Turnos Asignados", ln=True, align="C")
    pdf.ln(10)
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

st.title("🗓️ Planificador de Turnos SMN")
fecha_sel = st.date_input("Seleccionar mes", date(2026, 6, 1))
mes, anio = fecha_sel.month, fecha_sel.year

st.subheader(f"Calendario: {calendar.month_name[mes]}")
cal = calendar.HTMLCalendar(firstweekday=0)
st.markdown(cal.formatmonth(anio, mes), unsafe_allow_html=True)

# Configuración
nombres = ["Sanchez", "Barros", "Garcia", "Ricartez"]
config = {}
with st.sidebar:
    st.header("⚙️ Configuración")
    limite = st.number_input("Límite Horas Mensuales", value=130)
    for nom in nombres:
        with st.expander(f"Agente: {nom}"):
            config[nom] = {
                'dm': st.multiselect("Mañana", ["Lu","Ma","Mi","Ju","Vi","Sá","Do"], default=["Lu","Ma","Mi","Ju","Vi"], key=f"m_{nom}"),
                'dt': st.multiselect("Tarde", ["Lu","Ma","Mi","Ju","Vi","Sá","Do"], default=["Lu","Ma","Mi","Ju","Vi"], key=f"t_{nom}"),
                'pm': st.multiselect("Pref M", list(range(1, 32)), key=f"pm_{nom}"),
                'pt': st.multiselect("Pref T", list(range(1, 32)), key=f"pt_{nom}")
            }

if st.sidebar.button("📊 Calcular"):
    agentes = {n: Agente(n, limite) for n in nombres}
    for n, c in config.items(): agentes[n].configurar(c['dm'], c['dt'], c['pm'], c['pt'])
    
    dias_tot = calendar.monthrange(anio, mes)[1]
    grilla = {date(anio, mes, d): {'Dia': ["Lu","Ma","Mi","Ju","Vi","Sá","Do"][date(anio, mes, d).weekday()], 'M': 'SIN CUBRIR', 'T': 'SIN CUBRIR'} for d in range(1, dias_tot + 1)}
    
    for d in range(1, dias_tot + 1):
        f = date(anio, mes, d)
        for t in ['M', 'T']:
            cands = [a for a in agentes.values() if a.horas + 9 <= a.lim and (t=='M' and f.weekday() in a.disp_m or t=='T' and f.weekday() in a.disp_t)]
            if cands:
                cands.sort(key=lambda x: (0 if (t=='M' and d in x.pref_m) or (t=='T' and
