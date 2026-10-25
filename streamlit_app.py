import os
import streamlit as st
from google import genai

# Configuración de la página
st.set_page_config(
    page_title="Capacitador Óptico IA", page_icon="👓", layout="wide"
)

# --- CONTROL DE ACCESO ---
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if not st.session_state.autenticado:
  st.title("🔐 Acceso a la Plataforma - Capacitador Óptico")
  password_ingresada = st.text_input(
      "Ingresa la contraseña de la aplicación:", type="password"
  )
  password_secreta = st.secrets.get("APP_PASSWORD", "Infinito2026")

  if password_ingresada == password_secreta:
    st.session_state.autenticado = True
    st.rerun()
  elif password_ingresada:
    st.error("Contraseña incorrecta.")
  st.stop()

# --- APLICACIÓN PRINCIPAL (UNA VEZ AUTENTICADO) ---

# Menú lateral para elegir el módulo (¡Adiós a subir y bajar la pantalla!)
st.sidebar.title("📚 Módulos de Capacitación")
modulo_seleccionado = st.sidebar.selectbox(
    "Selecciona el área de entrenamiento:",
    [
        "1. Lectura e Inversión de Recetas",
        "2. Morfología y Espesores",
        "3. Tipos de Cristales y Tratamientos",
        "4. Simulador Infinito de Pacientes (Roleplay)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Tip:** Escribe tu consulta abajo en el chat. La caja de escritura"
    " siempre se queda fija al pie de la página para mayor comodidad."
)

# Título dinámico según el módulo
st.title("👓 Plataforma de Capacitación y Simulador Óptico")

# Inicializar cliente de IA
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

# Manejo de historiales de chat independientes por cada módulo para que no se mezcle nada
if "mensajes_m1" not in st.session_state:
  st.session_state.mensajes_m1 = [{
      "role": "assistant",
      "content": (
          "¡Hola! Estás en el **Módulo 1**. Pregúntame sobre transposición de"
          " cilindros, fórmulas bicilíndricas o representación en cruz"
          " astigmática."
      ),
  }]
if "mensajes_m2" not in st.session_state:
  st.session_state.mensajes_m2 = [{
      "role": "assistant",
      "content": (
          "¡Hola! Estás en el **Módulo 2**. Consúltame sobre espesores de"
          " cristales, índices de refracción, calibres y adaptación"
          " morfológica (puente, patillas, DNP)."
      ),
  }]
if "mensajes_m3" not in st.session_state:
  st.session_state.mensajes_m3 = [{
      "role": "assistant",
      "content": (
          "¡Hola! Estás en el **Módulo 3**. Aquí vemos la diferencia entre stock"
          " y laboratorio, familias de lentes y recomendación de"
          " tratamientos."
      ),
  }]
if "mensajes_m4" not in st.session_state:
  st.session_state.mensajes_m4 = [{
      "role": "assistant",
      "content": (
          "¡Hola! Estás en el **Módulo 4 (Gimnasio de Mostrador)**. Escribe"
          " 'Iniciar simulación' para que genere un paciente aleatorio con"
          " receta, presupuesto y personalidad."
      ),
  }]

# Mapear el historial activo según el módulo elegido en la barra lateral
if "1." in modulo_seleccionado:
  historial_activo = st.session_state.mensasis_activo = (
      st.session_state.mensajes_m1
  )
  tag_modulo = "MÓDULO 1"
  st.subheader("📌 Módulo 1: Lectura e Inversión de Recetas")
elif "2." in modulo_seleccionado:
  historial_activo = st.session_state.mensajes_m2
  tag_modulo = "MÓDULO 2"
  st.subheader("📌 Módulo 2: Morfología, Armazón e Índice de Refracción")
elif "3." in modulo_seleccionado:
  historial_activo = st.session_state.mensajes_m3
  tag_modulo = "MÓDULO 3"
  st.subheader("📌 Módulo 3: Tipos de Cristales y Recomendación de Producto")
else:
  historial_activo = st.session_state.mensajes_m4
  tag_modulo = "MÓDULO 4"
  st.subheader("📌 Módulo 4: Simulador Infinito de Pacientes (Roleplay)")

# Mostrar el historial de la conversación actual
for mensaje in historial_activo:
  with st.chat_message(mensaje["role"]):
    st.markdown(mensaje["content"])

# --- CAJA DE TEXTO FIJA ABAJO (STREAMLIT CHAT INPUT) ---
# Esta caja NUNCA se mueve de abajo, solucionando tu problema de desplazamiento.
if prompt_usuario := st.chat_input(
    "Escribe tu consulta o respuesta aquí..."
):
  # Agregar mensaje del usuario al historial activo
  historial_activo.append({"role": "user", "content": prompt_usuario})
  with st.chat_message("user"):
    st.markdown(prompt_usuario)

  # Generar respuesta de la IA
  with st.chat_message("assistant"):
    with st.spinner("El capacitador IA está analizando tu caso..."):
      try:
        # Construir historial para contexto fluido
        contenido_prompt = f"[{tag_modulo}] {prompt_usuario}"

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contenido_prompt,
            config={"system_instruction": system_instruction},
        )
        respuesta_ia = response.text
      except Exception as e:
        respuesta_ia = (
            "Error al conectar con la IA. Verifica tu clave en los Secrets."
            f" Detalle: {e}"
        )

      st.markdown(respuesta_ia)
      historial_activo.append({"role": "assistant", "content": respuesta_ia})
