import streamlit as st
import pandas as pd
import calendar
from datetime import date
from fpdf import FPDF
from io import BytesIO

# Configuración básica de página
st.set_page_config(page_title="Planificador", layout="wide")

st.title("Planificador de Turnos")

# Si no carga nada, el problema suele estar en la configuración inicial
# Vamos a imprimir algo simple para verificar que el código corre
st.write("Cargando sistema...")

# Definición de la clase simple
class Agente:
    def __init__(self, nombre):
        self.nombre = nombre
        self.horas = 0
        self.conteo = {'M': 0, 'T': 0}

# UI Simple para probar si carga
nombres = ["Sanchez", "Barros", "Garcia"]
config = {}
for nom in nombres:
    config[nom] = st.sidebar.text_input(f"Prueba {nom}", value="Test")

if st.sidebar.button("Probar Carga"):
    st.success("¡El código está corriendo correctamente!")
    st.write(config)
else:
    st.info("Configurá los nombres y presioná 'Probar Carga' para verificar.")
