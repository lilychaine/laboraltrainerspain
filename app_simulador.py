import json
import os
import random
import streamlit as st

DATA_FILE = "simulador_base_final.json"
ERRORS_FILE = "errores_simulador.json"

st.set_page_config(
    page_title="Simulador de práctica laboral",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------
# CARGA
# ------------------------------------------------------------
def load_questions():
    if not os.path.exists(DATA_FILE):
        st.error(f"No se encontró {DATA_FILE}")
        st.stop()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"No se pudo leer {DATA_FILE}: {e}")
        st.stop()

    if isinstance(data, dict):
        if "questions" in data and isinstance(data["questions"], list):
            data = data["questions"]
        else:
            st.error("El JSON no tiene formato válido. Debe ser una lista de preguntas.")
            st.stop()

    if not isinstance(data, list):
        st.error("El JSON no tiene formato válido. Debe ser una lista.")
        st.stop()

    required = {
        "id",
        "materia",
        "tema",
        "situacion",
        "pregunta",
        "opcion_a",
        "opcion_b",
        "opcion_c",
        "opcion_d",
        "respuesta_correcta",
        "feedback_correcto",
        "feedback_error",
        "referencia_legal",
    }

    cleaned = []
    seen = set()

    for i, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            continue
        if required - set(row.keys()):
            continue

        qid = str(row["id"]).strip()
        if not qid or qid in seen:
            continue
        seen.add(qid)

        cleaned.append(
            {
                "id": qid,
                "materia": str(row["materia"]).strip(),
                "tema": str(row["tema"]).strip(),
                "situacion": str(row["situacion"]).strip(),
                "pregunta": str(row["pregunta"]).strip(),
                "opcion_a": str(row["opcion_a"]).strip(),
                "opcion_b": str(row["opcion_b"]).strip(),
                "opcion_c": str(row["opcion_c"]).strip(),
                "opcion_d": str(row["opcion_d"]).strip(),
                "respuesta_correcta": str(row["respuesta_correcta"]).strip().upper(),
                "feedback_correcto": str(row["feedback_correcto"]).strip(),
                "feedback_error": str(row["feedback_error"]).strip(),
                "referencia_legal": str(row["referencia_legal"]).strip(),
            }
        )

    if len(cleaned) == 0:
        st.error("No hay preguntas válidas en el banco.")
        st.stop()

    return cleaned


def load_errors():
    if not os.path.exists(ERRORS_FILE):
        return []

    try:
        with open(ERRORS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def save_errors(errors):
    try:
        with open(ERRORS_FILE, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


QUESTIONS = load_questions()

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def get_topic_counts(items):
    counts = {}
    for item in items:
        tema = item["tema"]
        counts[tema] = counts.get(tema, 0) + 1
    return counts


def build_option_map(q):
    return {
        "A": q["opcion_a"],
        "B": q["opcion_b"],
        "C": q["opcion_c"],
        "D": q["opcion_d"],
    }


def normalize_feedback(text):
    text = str(text).strip()
    if text.lower().startswith("correcto."):
        text = text[len("correcto."):].strip()
    if text.lower().startswith("incorrecto."):
        text = text[len("incorrecto."):].strip()
    return text


def get_performance_message(pct):
    if pct >= 90:
        return "Nivel muy sólido. Tu criterio operativo es fuerte y consistente."
    if pct >= 75:
        return "Buen nivel. Hay base práctica clara, aunque conviene afinar algunos detalles."
    if pct >= 60:
        return "Nivel intermedio. Ya identificas buena parte de la lógica, pero todavía hay margen de mejora."
    return "Conviene reforzar la base operativa antes de confiar en automatismos."


def unique_by_id(items):
    seen = set()
    out = []
    for item in items:
        qid = str(item.get("id", ""))
        if qid and qid not in seen:
            seen.add(qid)
            out.append(item)
    return out


def start_mode(mode_name, source_questions, n_questions=None):
    if not isinstance(source_questions, list):
        st.error("El banco de preguntas no tiene formato válido.")
        st.stop()

    data = unique_by_id(source_questions.copy())
    random.shuffle(data)

    if n_questions is not None:
        data = data[: min(n_questions, len(data))]

    st.session_state.mode = mode_name
    st.session_state.data = data
    st.session_state.i = 0
    st.session_state.score = 0
    st.session_state.feedback = False
    st.session_state.sel = None
    st.session_state.session_results = []


def reset_app():
    st.session_state.mode = "menu"
    st.session_state.data = []
    st.session_state.i = 0
    st.session_state.score = 0
    st.session_state.feedback = False
    st.session_state.sel = None
    st.session_state.session_results = []


def store_error_question(q):
    errors = load_errors()
    if not any(str(x.get("id", "")) == str(q["id"]) for x in errors):
        errors.append(q)
        save_errors(errors)


if "mode" not in st.session_state:
    reset_app()

# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container {
    max-width: 1120px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}
div[data-testid="stRadio"] label {
    align-items: flex-start !important;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
def render_top_metrics():
    total = len(st.session_state.data)
    current = st.session_state.i + 1 if total > 0 else 0

    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.metric("Modalidad", st.session_state.mode.title(), border=True)
    with c2:
        st.metric("Progreso", f"{current}/{total}", border=True)
    with c3:
        st.metric("Aciertos", st.session_state.score, border=True)


def render_menu():
    st.title("Simulador de práctica laboral y Seguridad Social")
    st.caption("Entrenamiento orientado a gestión operativa de personas, contratación, cotización, recaudación y control administrativo.")

    left, right = st.columns(2, gap="large")

    with left:
        with st.container(border=True):
            st.subheader("Modo simulacro")
            st.write("Sesión mixta con casos aleatorios y evaluación final.")
            if st.button("Empezar simulacro de 20 casos", use_container_width=True, key="btn_simulacro"):
                start_mode("simulacro", QUESTIONS, 20)
                st.rerun()

        st.write("")

        with st.container(border=True):
            st.subheader("Repaso guiado")
            st.write("Práctica secuencial con feedback completo tras cada respuesta.")
            if st.button("Empezar repaso guiado", use_container_width=True, key="btn_repaso"):
                start_mode("repaso", QUESTIONS, None)
                st.rerun()

    with right:
        errors = load_errors()

        with st.container(border=True):
            st.subheader("Repaso de errores")
            st.write(f"Errores guardados: **{len(errors)}**")

            if len(errors) > 0:
                if st.button("Reestudiar errores", use_container_width=True, key="btn_errores"):
                    start_mode("errores", errors, None)
                    st.rerun()
            else:
                st.info("Todavía no hay errores guardados.")

            if st.button("Vaciar errores guardados", use_container_width=True, key="btn_vaciar"):
                save_errors([])
                st.success("Errores eliminados.")
                st.rerun()

        st.write("")

        with st.container(border=True):
            st.subheader("Banco disponible")
            st.write(f"Casos cargados: **{len(QUESTIONS)}**")

            temas = get_topic_counts(QUESTIONS)
            for tema, n in sorted(temas.items(), key=lambda x: (-x[1], x[0])):
                st.write(f"- {tema}: {n}")


def render_question():
    if not st.session_state.data:
        st.warning("No hay casos disponibles para este modo.")
        if st.button("Volver al menú", use_container_width=True):
            reset_app()
            st.rerun()
        return

    if st.session_state.i >= len(st.session_state.data):
        st.session_state.mode = "final"
        st.rerun()
        return

    q = st.session_state.data[st.session_state.i]
    opts = build_option_map(q)

    render_top_metrics()
    st.write("")

    st.subheader("Caso práctico")
    st.caption(f"{q['materia']} · {q['tema']}")

    with st.container(border=True):
        st.markdown("**Situación práctica**")
        st.write(q["situacion"])

    st.write("")

    with st.container(border=True):
        st.markdown("**Pregunta**")
        st.write(q["pregunta"])

    st.write("")

    if not st.session_state.feedback:
        with st.form(key=f"form_{q['id']}"):
            selected = st.radio(
                "Selecciona la opción correcta:",
                ["A", "B", "C", "D"],
                format_func=lambda x: f"{x}. {opts[x]}"
            )

            c1, c2 = st.columns(2, gap="small")
            send = c1.form_submit_button("Responder", use_container_width=True)
            back = c2.form_submit_button("Volver al menú", use_container_width=True)

        if back:
            reset_app()
            st.rerun()

        if send:
            st.session_state.sel = selected
            st.session_state.feedback = True

            is_correct = selected == q["respuesta_correcta"]
            if is_correct:
                st.session_state.score += 1
            else:
                store_error_question(q)

            st.session_state.session_results.append(
                {
                    "id": q["id"],
                    "tema": q["tema"],
                    "correcta": is_correct,
                }
            )
            st.rerun()

    else:
        selected = st.session_state.sel
        correct = q["respuesta_correcta"]

        if selected == correct:
            st.success("Decisión adecuada")
        else:
            st.error("Decisión incorrecta")

        with st.container(border=True):
            st.write(f"**Tu respuesta:** {selected}. {opts[selected]}")
            st.write(f"**Respuesta correcta:** {correct}. {opts[correct]}")

        st.write("")

        with st.container(border=True):
            st.subheader("Explicación legal")
            if selected == correct:
                st.write(normalize_feedback(q["feedback_correcto"]))
            else:
                st.write(normalize_feedback(q["feedback_error"]))

            if q["referencia_legal"]:
                st.write(f"**Referencia legal:** {q['referencia_legal']}")

        st.write("")

        c1, c2 = st.columns(2, gap="small")
        if c1.button("Continuar", use_container_width=True, key=f"next_{q['id']}"):
            st.session_state.i += 1
            st.session_state.feedback = False
            st.session_state.sel = None

            if st.session_state.i >= len(st.session_state.data):
                st.session_state.mode = "final"

            st.rerun()

        if c2.button("Volver al menú", use_container_width=True, key=f"menu_{q['id']}"):
            reset_app()
            st.rerun()


def render_final():
    total = len(st.session_state.data)
    score = st.session_state.score
    errors = total - score
    pct = int((score / total) * 100) if total > 0 else 0

    st.title("Resultado final")

    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        st.metric("Aciertos", score, border=True)
    with c2:
        st.metric("Errores", errors, border=True)
    with c3:
        st.metric("Rendimiento", f"{pct}%", border=True)

    st.write("")

    with st.container(border=True):
        st.subheader("Interpretación")
        st.write(get_performance_message(pct))

    st.write("")

    fallados = {}
    for r in st.session_state.session_results:
        if not r["correcta"]:
            tema = r["tema"]
            fallados[tema] = fallados.get(tema, 0) + 1

    with st.container(border=True):
        st.subheader("Temas a reforzar")
        if fallados:
            for tema, n in sorted(fallados.items(), key=lambda x: (-x[1], x[0])):
                st.write(f"- {tema}: {n} error(es)")
        else:
            st.write("No hubo errores en esta sesión.")

    st.write("")

    c1, c2 = st.columns(2, gap="small")
    if c1.button("Repetir", use_container_width=True, key="btn_repeat"):
        if st.session_state.mode == "repaso":
            start_mode("repaso", QUESTIONS, None)
        elif st.session_state.mode == "errores":
            err = load_errors()
            if len(err) > 0:
                start_mode("errores", err, None)
            else:
                start_mode("simulacro", QUESTIONS, 20)
        else:
            start_mode("simulacro", QUESTIONS, 20)
        st.rerun()

    if c2.button("Volver al menú principal", use_container_width=True, key="btn_final_menu"):
        reset_app()
        st.rerun()


# ------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------
if st.session_state.mode == "menu":
    render_menu()
elif st.session_state.mode == "final":
    render_final()
else:
    render_question()
