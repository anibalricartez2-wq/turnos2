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
        self.pref_m, self.pref_t = set(), set() # Preferencias para M y T
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

# --- UI ---
st.title("🗓️ Planificador de Turnos SMN")
nombres = ["Sanchez", "Barros", "Garcia", "Ricartez"]
lista_dias = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
config = {}

st.sidebar.header("⚙️ Configuración")
mes = st.sidebar.slider("Mes", 1, 12, 6)
limite_input = st.sidebar.number_input("Límite Horas", 130)

for nom in nombres:
    with st.sidebar.expander(f"Agente: {nom}"):
        config[nom] = {
            'dm': st.multiselect("Mañana (Semana)", lista_dias, default=lista_dias, key=f"m_{nom}"),
            'dt': st.multiselect("Tarde (Semana)", lista_dias, default=lista_dias, key=f"t_{nom}"),
            'pref_m': st.multiselect("Pref. Mañana (Días del mes)", list(range(1, 32)), key=f"pm_{nom}"),
            'pref_t': st.multiselect("Pref. Tarde (Días del mes)", list(range(1, 32)), key=f"pt_{nom}"),
            'bloq': st.text_input("Bloqueos", key=f"b_{nom}")
        }

if st.sidebar.button("📊 Calcular"):
    agentes = {n: Agente(n, limite_input) for n in nombres}
    for n, c in config.items():
        agentes[n].configurar(c['dm'], c['dt'], c['pref_m'], c['pref_t'])
        if c['bloq']:
            for d in c['bloq'].split(','): 
                if d.strip().isdigit(): agentes[n].bloqueos.add(date(2026, mes, int(d.strip())))
    
    _, dias_mes = calendar.monthrange(2026, mes)
    grilla = {date(2026, mes, d): {'Dia': lista_dias[date(2026, mes, d).weekday()], 'M': 'SIN CUBRIR', 'T': 'SIN CUBRIR'} for d in range(1, dias_mes + 1)}
        
    for d in range(1, dias_mes + 1):
        f = date(2026, mes, d)
        for t in ['M', 'T']:
            cands = [a for a in agentes.values() if a.esta_disponible(f, t, grilla)]
            if cands:
                # Prioridad mejorada: Preferencia (0) > Horas > Conteo
                cands.sort(key=lambda x: (
                    0 if (t == 'M' and d in x.pref_m) or (t == 'T' and d in x.pref_t) else 1, 
                    x.horas, 
                    x.conteo[t]
                ))
                el = cands[0]
                grilla[f][t] = el.nombre
                el.horas += 9
                el.conteo[t] += 1
    
    st.session_state.update({"grilla": pd.DataFrame(grilla).T, "calculado": True})
    st.rerun()

if st.session_state.get("calculado"):
    st.table(st.session_state["grilla"])
