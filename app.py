import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Planificador Pro", layout="wide")

if "calculado" not in st.session_state:
    st.session_state.update({"calculado": False, "grilla": None, "resumen": None})

class Agente:
    def __init__(self, nombre, lim):
        self.nombre = nombre
        self.lim = lim
        self.horas = 0
        self.conteo = {'M': 0, 'T': 0}
        self.bloqueos = set()
        self.pref_m, self.pref_t = set(), set()
        self.disp_m, self.disp_t = set(range(7)), set(range(7))

    def configurar(self, d_m, d_t, p_m, p_t):
        mapa = {"Lu":0, "Ma":1, "Mi":2, "Ju":3, "Vi":4, "Sá":5, "Do":6}
        self.disp_m = {mapa[d] for d in d_m}
        self.disp_t = {mapa[d] for d in d_t}
        self.pref_m = {int(d) for d in p_m}
        self.pref_t = {int(d) for d in p_t}

    def esta_disponible(self, f, t, grilla):
        if f in self.bloqueos or grilla.get(f, {}).get(t) != 'SIN CUBRIR': return False
        if grilla.get(f, {}).get('M' if t == 'T' else 'T') == self.nombre: return False
        if self.horas + 9 > self.lim: return False
        ds = f.weekday()
        if t == 'M' and ds not in self.disp_m: return False
        if t == 'T' and ds not in self.disp_t: return False
        return True

def generar_pdf(df, resumen, limite, mes, anio):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo_smn.png', 10, 8, 20)
    except: pass
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Cronograma {mes}/{anio} (Limite: {limite}hs)", ln=True, align="C")
    pdf.ln(10)
    # Tabla Principal
    pdf.set_font("Arial", "B", 8)
    for col in ["Fecha", "Dia", "Manana", "Tarde"]: pdf.cell(45, 7, col, 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    for i, row in df.iterrows():
        pdf.cell(45, 7, str(i), 1)
        pdf.cell(45, 7, str(row['Dia']), 1)
        pdf.cell(45, 7, str(row['M']), 1)
        pdf.cell(45, 7, str(row['T']), 1, ln=True)
    # Tabla Resumen
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Resumen de Turnos por Agente", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    for col in ["Agente", "Horas", "Turnos M", "Turnos T"]: pdf.cell(45, 7, col, 1)
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for n, row in resumen.iterrows():
        pdf.cell(45, 7, str(n), 1)
        pdf.cell(45, 7, str(row['Horas']), 1)
        pdf.cell(45, 7, str(row['Turnos M']), 1)
        pdf.cell(45, 7, str(row['Turnos T']), 1, ln=True)
    buffer = BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)
    return buffer

st.title("🗓️ Planificador de Turnos SMN")
nombres = ["Sanchez", "Barros", "Garcia", "Ricartez"]
lista_dias = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
config = {}

st.sidebar.header("⚙️ Configuración")
mes = st.sidebar.slider("Mes", 1, 12, 6)
limite_input = st.sidebar.number_input("Límite Horas Mensuales", min_value=80, max_value=200, value=130)

for nom in nombres:
    with st.sidebar.expander(f"Agente: {nom}"):
        config[nom] = {
            'dm': st.multiselect("Mañana (Semana)", lista_dias
