import json
import random

import google.generativeai as genai
import streamlit as st

st.set_page_config(page_title="Academia Óptica", page_icon="👓")
MODEL = "gemini-3.6-flash"  # cambiar si querés otro modelo de Gemini

# ---------- Acceso protegido ----------
if not st.session_state.get("ok"):
    clave = st.text_input("Clave de acceso", type="password")
    if clave and clave == st.secrets["APP_PASSWORD"]:
        st.session_state.ok = True
        st.rerun()
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

REGLAS = (
    "REGLAS ABSOLUTAS: nunca nombres marcas comerciales ni precios. "
    "Hablá de gamas: económica, intermedia o alta gama, y de prestaciones "
    "(campo visual, corredor, espesor, peso, tratamientos, materiales)."
)

OCUPACIONES = [
    "oficinista que pasa 9 horas frente a la PC", "chofer de colectivo",
    "docente", "jubilado que lee mucho y usa el celular", "estudiante universitario",
    "electricista", "ama de casa que cose y cocina", "contador",
    "operario de fábrica", "peluquera", "médico que maneja de noche",
]
QUEJAS = [
    "Me cuesta leer el menú en los restaurantes, siento que se me acortaron los brazos.",
    "Los lentes que tengo me marean cuando bajo escaleras.",
    "Vengo porque se me rompieron los anteojos y necesito unos nuevos ya.",
    "Me duele la cabeza a la tarde cuando trabajo con la computadora.",
    "Mis anteojos son muy gruesos y pesados, se me marcan en la nariz.",
    "Mi hijo no ve el pizarrón y la maestra me mandó a que lo traiga.",
    "De noche, manejando, veo halos y me encandilo.",
]
PRESUPUESTOS = ["ajustado", "medio", "sin límite pero quiere que valga la pena"]
ARMAZONES = [
    "acetato grueso", "metal fino", "armazón al aire (perforado)",
    "TR90 deportivo", "nylon (semi al aire)", "inyección importada liviana",
]
HABILIDADES = ["anamnesis", "indicación de cristal", "tratamientos y filtros",
               "armazón y montaje", "comunicación"]


def r25(x):
    return round(x * 4) / 4


def fmt(esf, cil, eje):
    c = f" {cil:+.2f} x {eje}°" if cil else ""
    return f"{esf:+.2f}{c}"


def nuevo_caso():
    edad = random.randint(8, 78)
    tipo = random.choices(["miope", "hipermétrope", "astigmático"], [4, 3, 3])[0]
    esf = {"miope": r25(random.uniform(-9, -0.75)),
           "hipermétrope": r25(random.uniform(0.5, 5)),
           "astigmático": r25(random.uniform(-2, 2))}[tipo]
    cil = random.choice([0, -0.5, -0.75, -1.0, -1.5, -2.5, -3.5]) if tipo == "astigmático" or random.random() < .4 else 0
    eje = random.choice([0, 10, 45, 90, 135, 170, 180]) if cil else 0
    aniso = random.choice([0, 0, 0.25, 0.5, 1.5])
    od, oi = (esf, cil, eje), (r25(esf + aniso), cil, eje)
    add = 0.0
    if edad >= 40:
        add = min(3.0, r25(0.75 + (edad - 40) * 0.045 + random.choice([-.25, 0, 0.25])))
    ee = [e + c / 2 for e, c, _ in (od, oi)]  # equivalente esférico
    return {
        "edad": edad, "od": od, "oi": oi, "add": add,
        "ee_max": round(max(abs(x) for x in ee), 2),
        "ocupacion": random.choice(OCUPACIONES), "queja": random.choice(QUEJAS),
        "presupuesto": random.choice(PRESUPUESTOS), "armazon": random.choice(ARMAZONES),
    }


def receta_txt(c):
    t = f"OD {fmt(*c['od'])}\nOI {fmt(*c['oi'])}"
    return t + (f"\nAdición {c['add']:+.2f}" if c["add"] else "")


def llamar(system, history, texto, json_mode=False):
    cfg = {"response_mime_type": "application/json"} if json_mode else None
    m = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system, generation_config=cfg)
    return m.start_chat(history=history).send_message(texto).text


def system_paciente(c):
    return f"""Sos un paciente en una óptica argentina. Hablás natural, en rioplatense, con frases cortas.
Datos tuyos (NO los revelés todos juntos; contestá solo lo que el óptico pregunte):
- Edad: {c['edad']} años. Ocupación: {c['ocupacion']}.
- Motivo de consulta: {c['queja']}
- Presupuesto: {c['presupuesto']} (solo lo decís si te lo preguntan o si te ofrecen algo que no te cierra).
- Armazón que elegiste: {c['armazon']}.
- Receta: {receta_txt(c)}
Si el óptico te explica mal o con mucho tecnicismo, decilo ("no entendí"). Si te recomienda algo sensato, respondé con dudas reales.
No des consejos ópticos ni digas qué cristal te conviene: eso lo decide el óptico. {REGLAS}"""


def evaluar(c, msgs):
    charla = "\n".join(f"{'ÓPTICO' if m['role']=='user' else 'PACIENTE'}: {m['content']}" for m in msgs)
    prompt = f"""Sos un instructor de ópticos con criterio clínico. Evaluá la atención.
CASO: edad {c['edad']}, ocupación {c['ocupacion']}, motivo: {c['queja']}, presupuesto {c['presupuesto']},
armazón {c['armazon']}, equivalente esférico máximo {c['ee_max']} D.
RECETA:\n{receta_txt(c)}
CONVERSACIÓN:\n{charla}

{REGLAS}
Devolvé SOLO un JSON con esta forma:
{{"puntajes": {{{', '.join(f'"{h}": 0-10' for h in HABILIDADES)}}},
 "nota_global": 0-10, "aciertos": ["..."], "errores": ["..."],
 "indicacion_ideal": "qué cristal (tipo de diseño por gama, índice, material), tratamientos y filtros convenía y por qué, según receta, armazón y ocupación",
 "para_estudiar": ["tema 1", "tema 2"]}}
Sé exigente y concreto; si el óptico no preguntó algo clave, marcalo como error."""
    return json.loads(llamar("Respondé únicamente JSON válido.", [], prompt, json_mode=True))


# ---------- Estado ----------
ss = st.session_state
ss.setdefault("caso", None)
ss.setdefault("msgs", [])
ss.setdefault("resultado", None)
ss.setdefault("historial", [])

st.title("👓 Academia Óptica")
st.caption("Módulo 1 · Atención de pacientes simulados")

with st.sidebar:
    if ss.historial:
        st.metric("Casos atendidos", len(ss.historial))
        st.metric("Promedio", round(sum(h["nota_global"] for h in ss.historial) / len(ss.historial), 1))
    if st.button("Nuevo paciente", use_container_width=True):
        ss.caso, ss.msgs, ss.resultado = nuevo_caso(), [], None
        st.rerun()

if not ss.caso:
    st.info("Tocá **Nuevo paciente** en el menú lateral para empezar.")
    st.stop()

c = ss.caso
with st.expander("📄 Lo que ves: receta y armazón elegido", expanded=True):
    st.text(f"Paciente de unos {c['edad']} años\n{receta_txt(c)}\nArmazón elegido: {c['armazon']}")
    st.caption("Ocupación, motivo y presupuesto los tenés que averiguar vos.")

if not ss.msgs:
    ss.msgs.append({"role": "model", "content": c["queja"]})

for m in ss.msgs:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        st.write(m["content"])

if ss.resultado:
    r = ss.resultado
    st.subheader(f"Nota global: {r['nota_global']}/10")
    for h, p in r["puntajes"].items():
        st.progress(min(int(p), 10) / 10, text=f"{h}: {p}/10")
    st.success("**Aciertos**\n\n" + "\n".join(f"- {x}" for x in r["aciertos"]))
    st.error("**Errores**\n\n" + "\n".join(f"- {x}" for x in r["errores"]))
    st.info("**Indicación ideal**\n\n" + r["indicacion_ideal"])
    st.write("**Para estudiar:** " + ", ".join(r["para_estudiar"]))
    st.stop()

if texto := st.chat_input("Atendé al paciente..."):
    ss.msgs.append({"role": "user", "content": texto})
    hist = [{"role": m["role"], "parts": [m["content"]]} for m in ss.msgs[:-1]]
    ss.msgs.append({"role": "model", "content": llamar(system_paciente(c), hist, texto)})
    st.rerun()

if len(ss.msgs) > 2 and st.button("✅ Terminar atención y evaluar"):
    with st.spinner("El instructor está evaluando..."):
        ss.resultado = evaluar(c, ss.msgs)
        ss.historial.append(ss.resultado)
    st.rerun()
