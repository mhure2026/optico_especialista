import os
import streamlit as st
from google import genai

# Configuración de la página
st.set_page_config(
    page_title="Capacitador Óptico IA", page_icon="👓", layout="wide"
)

# --- CONTROL DE ACCESO ---
st.title("🔐 Acceso a la Plataforma - Capacitador Óptico")
password_ingresada = st.text_input(
    "Ingresa la contraseña de la aplicación:", type="password"
)

# Obtener la contraseña desde los Secrets de Streamlit
password_secreta = st.secrets.get("APP_PASSWORD", "Infinito2026")

# Validar contraseña: si no coincide, frena y no muestra nada más
if password_ingresada != password_secreta:
  st.warning(
      "🔒 Por favor, ingresa la contraseña correcta para desbloquear la"
      " aplicación."
  )
  st.stop()

# --- SÓLO SE MUESTRA SI LA CONTRASEÑA ES CORRECTA ---
st.success("¡Acceso concedido con éxito!")
st.title("👓 Plataforma de Capacitación y Simulador Óptico")
st.write(
    "Entrenamiento integral para ópticos recién graduados: teoría, taller,"
    " morfología y ventas."
)

# Inicializar el cliente de Google GenAI
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key)

# System Instructions con los 4 módulos
system_instruction = """PROMPTING SYSTEM: Capacitador y Simulador de Óptica Técnica y Comercial

ROL Y OBJETIVO GENERAL:
Sos un Capacitador Experto en Optometría, Óptica Técnica y Ventas en Mostrador. Tu objetivo es entrenar a ópticos recién graduados para que dominen la interpretación de recetas, la transposición de fórmulas, la selección de armazones/cristales según la morfología y graduación del paciente, y el manejo de ventas mediante simulaciones interactivas.

MÓDULOS DE CONOCIMIENTO Y FUNCIONALIDADES:
MÓDULO 1: Lectura e Inversión de Recetas (Transposición)
MÓDULO 2: Asesoría Morfológica, Armazón e Índice de Refracción
MÓDULO 3: Tipos de Cristales y Recomendación de Producto
MÓDULO 4: Simulador Infinito de Pacientes (Roleplay de Ventas)

Mantiene un tono pedagógico, profesional, dinámico y muy claro."""

# Pestañas de la interfaz basadas en tus módulos
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1. Recetas y Transposición",
        "2. Morfología y Espesores",
        "3. Tipos y Cristales",
        "4. Simulador de Pacientes",
    ]
)


def consultar_ia(prompt_usuario, modulo_seleccionado):
  with st.spinner("El capacitador IA está analizando tu consulta..."):
    try:
      # Actualizado al modelo correcto requerido por la API
      response = client.models.generate_content(
          model="gemini-3.8-flash",
          contents=f"[{modulo_seleccionado}] {prompt_usuario}",
          config={"system_instruction": system_instruction},
      )
      return response.text
    except Exception as e:
      return (
          "Error al conectar con la IA. Verifica tu GEMINI_API_KEY en los"
          f" Secrets. Detalle: {e}"
      )


with tab1:
  st.header("Módulo 1: Lectura e Inversión de Recetas")
  st.write(
      "Practicá cilindros positivos, negativos, bicilíndricas y representación"
      " en cruz."
  )
  pregunta_m1 = st.text_area(
      "Escribe tu caso o duda de receta:",
      key="q1",
      placeholder="Ej: ¿Cómo transpongo +2.00 -1.50 x 90?",
  )
  if st.button("Consultar Módulo 1"):
    if pregunta_m1:
      st.markdown(consultar_ia(pregunta_m1, "MÓDULO 1"))

with tab2:
  st.header("Módulo 2: Morfología, Armazón e Índice de Refracción")
  st.write(
      "Calculá espesores según calibre, DNP, altura y morfología facial (puente"
      " y patillas)."
  )
  pregunta_m2 = st.text_area(
      "Escribe tu consulta de taller y armazones:",
      key="q2",
      placeholder=(
          "Ej: ¿Qué espesor de borde tendrá una miopía de -6.00 en un armazón"
          " de 50mm?"
      ),
  )
  if st.button("Consultar Módulo 2"):
    if pregunta_m2:
      st.markdown(consultar_ia(pregunta_m2, "MÓDULO 2"))

with tab3:
  st.header("Módulo 3: Tipos de Cristales y Recomendación")
  st.write("Diferencia stock vs. laboratorio y elegí los mejores tratamientos.")
  pregunta_m3 = st.text_area(
      "Escribe tu duda sobre cristales:",
      key="q3",
      placeholder=(
          "Ej: ¿Cuándo conviene un multifocal tallado digital versus uno"
          " estándar?"
      ),
  )
  if st.button("Consultar Módulo 3"):
    if pregunta_m3:
      st.markdown(consultar_ia(pregunta_m3, "MÓDULO 3"))

with tab4:
  st.header("Módulo 4: Simulador Infinito de Pacientes (Roleplay)")
  st.write(
      "Entrená el cierre de venta interactuando con un paciente generado por"
      " IA."
  )
  if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = []

  if st.button("Generar nuevo paciente aleatorio"):
    prompt_inicial = (
        "Inicia una simulación del Módulo 4. Genera un paciente aleatorio con"
        " receta, presupuesto y personalidad, y preséntate en el mostrador"
        " pidiendo asesoramiento."
    )
    respuesta = consultar_ia(prompt_inicial, "MÓDULO 4")
    st.session_state.historial_chat = [("Paciente", respuesta)]

  for remitente, texto in st.session_state.historial_chat:
    with st.chat_message(remitente):
      st.markdown(texto)

  respuesta_usuario = st.chat_input("Responde al paciente como óptico...")
  if respuesta_usuario:
    st.session_state.historial_chat.append(("Óptico", respuesta_usuario))
    with st.chat_message("Óptico"):
      st.markdown(respuesta_usuario)

    prompt_continuacion = f"El óptico respondió: {respuesta_usuario}. Sigue interpretando al paciente, reacciona a su venta y dale feedback si corresponde."
    respuesta_paciente = consultar_ia(prompt_continuacion, "MÓDULO 4")
    st.session_state.historial_chat.append(("Paciente", respuesta_paciente))
    with st.chat_message("Paciente"):
      st.markdown(respuesta_paciente)
