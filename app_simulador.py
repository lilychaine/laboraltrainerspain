import json
import os
import random
import streamlit as st

DATA_FILE = "simulador_base_limpio.json"
ERRORS_FILE = "errores_simulador_base_limpio.json"

st.set_page_config(
    page_title="Simulador de práctica laboral",
    page_icon="📘",
    layout="wide"
)

# ------------------------------------------------------------
# CARGA
# ------------------------------------------------------------
@st.cache_data
def load_questions():
    if not os.path.exists(DATA_FILE):
        st.error(f"No existe el archivo requerido: {DATA_FILE}")
        st.stop()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        st.error("El archivo JSON está vacío o no tiene el formato esperado.")
        st.stop()

    required_keys = {
        "id", "materia", "tema", "situacion", "pregunta",
        "opcion_a", "opcion_b", "opcion_c", "opcion_d",
        "respuesta_correcta", "feedback_correcto", "feedback_error",
        "referencia_legal", "texto_base"
    }

    for i, row in enumerate(data):
        missing = required_keys - set(row.keys())
        if missing:
            st.error(f"Faltan campos en el registro {i + 1}: {', '.join(sorted(missing))}")
            st.stop()

    return data

def load_errors():
    if not os.path.exists(ERRORS_FILE):
        return []
    try:
        with open(ERRORS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_errors(errors):
    with open(ERRORS_FILE, "w", encoding="utf-8") as f:
        json.dump(errors, f, ensure_ascii=False, indent=2)

questions = load_questions()

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def build_option_map(q):
    return {
        "A": q["opcion_a"],
        "B": q["opcion_b"],
        "C": q["opcion_c"],
        "D": q["opcion_d"]
    }

def get_performance_message(pct):
    if pct >= 90:
        return "Nivel muy sólido. Tu criterio operativo está bien orientado a un entorno real de gestión laboral."
    if pct >= 75:
        return "Buen nivel. Hay una base práctica clara, aunque conviene reforzar precisión en algunos trámites."
    if pct >= 60:
        return "Nivel intermedio. Ya identificas parte de la lógica operativa, pero todavía hay áreas de mejora relevantes."
    return "Conviene reforzar la base, especialmente en altas, bajas, cotización y recaudación."

def start_mode(mode_name, source_questions, n_questions=None):
    session_questions = source_questions.copy()
    random.shuffle(session_questions)

    if n_questions is not None:
        session_questions = session_questions[:min(n_questions, len(session_questions))]

    st.session_state.mode = mode_name
    st.session_state.session_questions = session_questions
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.show_feedback = False
    st.session_state.selected_option = None
    st.session_state.finished = False
    st.session_state.session_results = []

def reset_to_menu():
    st.session_state.mode = "menu"
    st.session_state.session_questions = []
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.show_feedback = False
    st.session_state.selected_option = None
    st.session_state.finished = False
    st.session_state.session_results = []

def init_state():
    if "mode" not in st.session_state:
        reset_to_menu()

init_state()

# ------------------------------------------------------------
# ESTILOS
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1.5rem;
    max-width: 1100px;
}

.card {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    background: #ffffff;
}

.ok-box {
    border: 1px solid #b7ebc6;
    background: #f0fff4;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
}

.bad-box {
    border: 1px solid #f4b4b4;
    background: #fff5f5;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
}

.metric-box {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    background: #fafafa;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# MENÚ
# ------------------------------------------------------------
def render_menu():
    st.title("Simulador de práctica laboral y Seguridad Social")
    st.caption(
        "Entrenamiento orientado a gestión operativa de personas, contratación, cotización, recaudación y control administrativo."
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Modo simulacro")
        st.write("Sesión mixta con casos aleatorios y evaluación final.")
        if st.button("Empezar simulacro de 20 casos", use_container_width=True):
            start_mode("simulacro", questions, n_questions=20)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Repaso guiado")
        st.write("Práctica secuencial con feedback completo.")
        if st.button("Empezar repaso guiado", use_container_width=True):
            start_mode("repaso", questions, n_questions=None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        errors = load_errors()
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Repaso de errores")
        st.write(f"Errores guardados: {len(errors)}")

        if errors:
            if st.button("Reestudiar errores", use_container_width=True):
                start_mode("errores", errors, n_questions=None)
                st.rerun()
        else:
            st.info("Todavía no hay errores guardados.")

        if st.button("Vaciar errores guardados", use_container_width=True):
            save_errors([])
            st.success("Errores eliminados.")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Banco disponible")
        st.write(f"Casos cargados: **{len(questions)}**")

        temas = {}
        for q in questions:
            temas[q["tema"]] = temas.get(q["tema"], 0) + 1

        for tema, n in sorted(temas.items(), key=lambda x: (-x[1], x[0])):
            st.write(f"- {tema}: {n}")

        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# MOTOR DE PREGUNTAS
# ------------------------------------------------------------
def store_error_question(q):
    errors = load_errors()
    if not any(x["id"] == q["id"] for x in errors):
        errors.append(q)
        save_errors(errors)

def render_question():
    q = st.session_state.session_questions[st.session_state.current_index]
    option_map = build_option_map(q)
    total = len(st.session_state.session_questions)
    current_num = st.session_state.current_index + 1

    top1, top2, top3 = st.columns([1, 1, 1])
    with top1:
        st.markdown(
            f'<div class="metric-box"><b>Modo</b><br>{st.session_state.mode.title()}</div>',
            unsafe_allow_html=True
        )
    with top2:
        st.markdown(
            f'<div class="metric-box"><b>Progreso</b><br>{current_num} / {total}</div>',
            unsafe_allow_html=True
        )
    with top3:
        st.markdown(
            f'<div class="metric-box"><b>Aciertos</b><br>{st.session_state.score}</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"**Materia:** {q['materia']}")
    st.markdown(f"**Tema:** {q['tema']}")
    st.markdown(f"**Referencia base:** {q['referencia_legal']}")
    st.markdown("---")
    st.markdown("**Situación práctica**")
    st.write(q["situacion"])
    st.markdown("**Pregunta**")
    st.write(q["pregunta"])
    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.show_feedback:
        selected = st.radio(
            "Selecciona la opción correcta:",
            options=["A", "B", "C", "D"],
            format_func=lambda x: f"{x}. {option_map[x]}",
            key=f"radio_{q['id']}"
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Responder", use_container_width=True):
                st.session_state.selected_option = selected
                st.session_state.show_feedback = True

                is_correct = selected == q["respuesta_correcta"]
                if is_correct:
                    st.session_state.score += 1
                else:
                    store_error_question(q)

                st.session_state.session_results.append({
                    "id": q["id"],
                    "tema": q["tema"],
                    "correcta": is_correct
                })
                st.rerun()

        with c2:
            if st.button("Volver al menú", use_container_width=True):
                reset_to_menu()
                st.rerun()

    else:
        selected = st.session_state.selected_option
        correct = q["respuesta_correcta"]

        if selected == correct:
            st.markdown('<div class="ok-box">', unsafe_allow_html=True)
            st.markdown("### ✅ Respuesta correcta")
            st.write(f"**Tu respuesta:** {selected}. {option_map[selected]}")
            st.write(f"**Respuesta correcta:** {correct}. {option_map[correct]}")
            st.write(q["feedback_correcto"])
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="bad-box">', unsafe_allow_html=True)
            st.markdown("### ❌ Respuesta incorrecta")
            st.write(f"**Tu respuesta:** {selected}. {option_map[selected]}")
            st.write(f"**Respuesta correcta:** {correct}. {option_map[correct]}")
            st.write(q["feedback_error"])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Texto base detectado**")
        st.write(q["texto_base"])
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Continuar", use_container_width=True):
                st.session_state.current_index += 1
                st.session_state.show_feedback = False
                st.session_state.selected_option = None

                if st.session_state.current_index >= len(st.session_state.session_questions):
                    st.session_state.finished = True

                st.rerun()

        with c2:
            if st.button("Volver al menú", use_container_width=True):
                reset_to_menu()
                st.rerun()

# ------------------------------------------------------------
# PANTALLA FINAL
# ------------------------------------------------------------
def render_final():
    total = len(st.session_state.session_questions)
    score = st.session_state.score
    errors = total - score
    pct = round((score / total) * 100) if total > 0 else 0

    st.title("Resultado final")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-box"><b>Aciertos</b><br>{score}</div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div class="metric-box"><b>Errores</b><br>{errors}</div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f'<div class="metric-box"><b>Rendimiento</b><br>{pct}%</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Interpretación")
    st.write(get_performance_message(pct))
    st.markdown('</div>', unsafe_allow_html=True)

    fallados = {}
    for r in st.session_state.session_results:
        if not r["correcta"]:
            fallados[r["tema"]] = fallados.get(r["tema"], 0) + 1

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Temas a reforzar")
    if fallados:
        for tema, n in sorted(fallados.items(), key=lambda x: (-x[1], x[0])):
            st.write(f"- {tema}: {n} error(es)")
    else:
        st.write("No hubo errores en esta sesión.")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Repetir", use_container_width=True):
            if st.session_state.mode == "simulacro":
                start_mode("simulacro", questions, n_questions=20)
            elif st.session_state.mode == "repaso":
                start_mode("repaso", questions, n_questions=None)
            else:
                errors_list = load_errors()
                if errors_list:
                    start_mode("errores", errors_list, n_questions=None)
                else:
                    reset_to_menu()
            st.rerun()

    with c2:
        if st.button("Volver al menú principal", use_container_width=True):
            reset_to_menu()
            st.rerun()

# ------------------------------------------------------------
# RENDER PRINCIPAL
# ------------------------------------------------------------
if st.session_state.mode == "menu":
    render_menu()
elif st.session_state.finished:
    render_final()
else:
    render_question()
