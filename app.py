import streamlit as st
import pandas as pd
import calendar
from datetime import date
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Planificador SMN Pro", layout="wide")

class Agente:
    def __init__(self, nombre, lim):
        self.nombre = nombre
        self.lim = lim
        self.horas = 0
        self.conteo = {'M': 0, 'T': 0}
        self.bloqueos = set()
        self.pref_m, self.pref_t = set(), set()
        self.disp_m, self.disp_t = set(range(7)), set(range(7))

    def configurar(self, d_m, d_t, p_m, p_t, bloq):
        mapa = {"Lu":0, "Ma":1, "Mi":2, "Ju":3, "Vi":4, "Sá":5, "Do":6}
        self.disp_m = {mapa[d] for d in d_m}
        self.disp_t = {mapa[d] for d in d_t}
        self.pref_m = {int(d) for d in p_m}
        self.pref_t = {int(d) for d in p_t}
        if bloq:
            self.bloqueos = {int(d.strip()) for d in bloq.split(',') if d.strip().isdigit()}

# --- LÓGICA DE CÁLCULO ---
def calcular_turnos(nombres, config, limite, mes, anio):
    agentes = {n: Agente(n, limite) for n in nombres}
    for n, c in config.items(): agentes[n].configurar(c['dm'], c['dt'], c['pm'], c['pt'], c['bloq'])
    
    dias_tot = calendar.monthrange(anio, mes)[1]
    grilla = {date(anio, mes, d): {'Dia': ["Lu","Ma","Mi","Ju","Vi","Sá","Do"][date(anio, mes, d).weekday()], 'M': 'SIN CUBRIR', 'T': 'SIN CUBRIR'} for d in range(1, dias_tot + 1)}
    
    for d in range(1, dias_tot + 1):
        f = date(anio, mes, d)
        for t in ['M', 'T']:
            # 1. Candidatos válidos (respetan límites, bloqueos y disponibilidad semanal)
            cands = [a for a in agentes.values() if a.horas + 9 <= a.lim and d not in a.bloqueos and (t=='M' and f.weekday() in a.disp_m or t=='T' and f.weekday() in a.disp_t)]
            
            # 2. Si no hay candidatos, FORZAR al que menos turnos tenga (ignorar disponibilidad para no dejar hueco)
            if not cands:
                cands = list(agentes.values())

            # 3. Ordenar: 1. Total turnos (Equidad), 2. Preferencia, 3. Horas
            cands.sort(key=lambda x: (x.conteo['M'] + x.conteo['T'], 0 if (t=='M' and d in x.pref_m) or (t=='T' and d in x.pref_t) else 1, x.horas))
            
            el = cands[0]
            grilla[f][t] = el.nombre
            el.horas += 9
            el.conteo[t] += 1
            
    return grilla, agentes

# --- INTERFAZ ---
st.title("🗓️ Planificador de Turnos (Equidad Garantizada)")
fecha_sel = st.date_input("Seleccionar mes", date(2026, 6, 1))
mes, anio = fecha_sel.month, fecha_sel.year

with st.sidebar:
    st.header("⚙️ Configuración")
    limite = st.number_input("Límite Horas", value=130)
    nombres = ["Sanchez", "Barros", "Garcia", "Ricartez"]
    config = {n: {} for n in nombres}
    for nom in nombres:
        with st.expander(f"Agente: {nom}"):
            config[nom] = {
                'dm': st.multiselect("Mañana", ["Lu","Ma","Mi","Ju","Vi","Sá","Do"], default=["Lu","Ma","Mi","Ju","Vi"], key=f"m_{nom}"),
                'dt': st.multiselect("Tarde", ["Lu","Ma","Mi","Ju","Vi","Sá","Do"], default=["Lu","Ma","Mi","Ju","Vi"], key=f"t_{nom}"),
                'pm': st.multiselect("Pref M", list(range(1, 32)), key=f"pm_{nom}"),
                'pt': st.multiselect("Pref T", list(range(1, 32)), key=f"pt_{nom}"),
                'bloq': st.text_input("Días NO trabajar", key=f"b_{nom}")
            }

if st.sidebar.button("📊 Calcular Turnos"):
    grilla, agentes = calcular_turnos(nombres, config, limite, mes, anio)
    st.session_state.update({"grilla": pd.DataFrame(grilla).T, "resumen": pd.DataFrame({n: {'Turnos M': a.conteo['M'], 'Turnos T': a.conteo['T']} for n, a in agentes.items()}).T, "calculado": True})
    st.rerun()

if st.session_state.get("calculado"):
    st.table(st.session_state.grilla)
    st.table(st.session_state.resumen)
