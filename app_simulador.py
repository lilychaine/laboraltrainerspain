import json
import os
import random
import streamlit as st

# ============================================================
# SIMULADOR DE PRÁCTICA LABORAL Y SEGURIDAD SOCIAL
# - métricas nativas (no se cortan)
# - sin normativa en el enunciado
# - feedback limpio:
#     • Tu respuesta
#     • Respuesta correcta
#     • Explicación legal + referencia
# - SIN texto base ni desplegables
# ============================================================

CANDIDATE_FILES = [
    "simulador_base_final.json",
]
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
def load_json_file(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def load_questions():
    path = CANDIDATE_FILES[0]
    data = load_json_file(path)

    if len(data) == 0:
        st.error("No se encontró simulador_base_final.json o está vacío.")
        st.stop()

    required_keys = {
        "id", "materia", "tema", "situacion", "pregunta",
        "opcion_a", "opcion_b", "opcion_c", "opcion_d",
        "respuesta_correcta", "feedback_correcto", "feedback_error",
        "referencia_legal"
    }

    cleaned = []
    for row in data:
        if not isinstance(row, dict):
            continue
        if required_keys - set(row.keys()):
            continue

        cleaned.append({
            "id": str(row["id"]),
            "materia": str(row["materia"]),
            "tema": str(row["tema"]),
            "situacion": str(row["situacion"]),
            "pregunta": str(row["pregunta"]),
            "opcion_a": str(row["opcion_a"]),
            "opcion_b": str(row["opcion_b"]),
            "opcion_c": str(row["opcion_c"]),
            "opcion_d": str(row["opcion_d"]),
            "respuesta_correcta": str(row["respuesta_correcta"]).strip().upper(),
            "feedback_correcto": str(row["feedback_correcto"]),
            "feedback_error": str(row["feedback_error"]),
            "referencia_legal": str(row.get("referencia_legal", "")),
        })

    return cleaned


def load_errors():
    if not os.path.exists(ERRORS_FILE):
        return []
    try:
        with open(ERRORS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_errors(errors):
    try:
        with open(ERRORS_FILE, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


questions = load_questions()

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def unique_by_id(items):
    seen = set()
    out = []
    for item in items:
        item_id = str(item.get("id", ""))
        if item_id and item_id not in seen:
            seen.add(item_id)
            out.append(item)
    return out


def build_option_map(q):
    return {
        "A": q["opcion_a"],
        "B": q["opcion_b"],
        "C": q["opcion_c"],
        "D": q["opcion_d"],
    }


def get_topic_counts(items):
    counts = {}
    for item in items:
        tema = str(item.get("tema", "Sin tema"))
        counts[tema] = counts.get(tema, 0) + 1
    return counts


def get_performance_message(pct):
    if pct >= 90:
        return "Nivel muy sólido. Tu criterio operativo es adecuado para un entorno real."
    if pct >= 75:
        return "Buen nivel. Refuerza algunos detalles técnicos."
    if pct >= 60:
        return "Nivel intermedio. Aún hay margen de mejora."
    return "Conviene reforzar la base en gestión laboral."


def store_error_question(q):
    errors = load_errors()
    if not any(str(x.get("id", "")) == str(q["id"]) for x in errors):
        errors.append(q)
        save_errors(errors)


def start_mode(mode_name, source_questions, n_questions=None):
    session_questions = unique_by_id(source_questions.copy())
    random.shuffle(session_questions)

    if n_questions:
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


if "mode" not in st.session_state:
    reset_to_menu()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
def render_metrics(mode, progress, score):
    c1, c2, c3 = st.columns(3)
    c1.metric("Modalidad", mode)
    c2.metric("Progreso", progress)
    c3.metric("Aciertos", score)


def render_menu():
    st.title("Simulador de práctica laboral")
    st.caption("Entrenamiento práctico en gestión laboral y Seguridad Social")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Simulacro (20 casos)", use_container_width=True):
            start_mode("simulacro", questions, 20)
            st.rerun()

        if st.button("Repaso guiado", use_container_width=True):
            start_mode("repaso", questions)
            st.rerun()

    with c2:
        errors = load_errors()

        if errors:
            if st.button("Repasar errores", use_container_width=True):
                start_mode("errores", errors)
                st.rerun()

        if st.button("Borrar errores", use_container_width=True):
            save_errors([])
            st.success("Errores eliminados")
            st.rerun()

        st.write(f"Casos disponibles: {len(questions)}")


def render_question():
    q = st.session_state.session_questions[st.session_state.current_index]
    option_map = build_option_map(q)

    total = len(st.session_state.session_questions)
    current = st.session_state.current_index + 1

    render_metrics(
        st.session_state.mode,
        f"{current}/{total}",
        st.session_state.score
    )

    st.write("")

    st.subheader("Situación práctica")
    st.write(q["situacion"])

    st.subheader("Pregunta")
    st.write(q["pregunta"])

    if not st.session_state.show_feedback:
        selected = st.radio(
            "Selecciona una opción:",
            ["A", "B", "C", "D"],
            format_func=lambda x: f"{x}. {option_map[x]}"
        )

        if st.button("Responder"):
            st.session_state.selected_option = selected
            st.session_state.show_feedback = True

            if selected == q["respuesta_correcta"]:
                st.session_state.score += 1
            else:
                store_error_question(q)

            st.rerun()

        if st.button("Volver al menú"):
            reset_to_menu()
            st.rerun()

    else:
        selected = st.session_state.selected_option
        correct = q["respuesta_correcta"]

        if selected == correct:
            st.success("Decisión adecuada")
        else:
            st.error("Decisión incorrecta")

        st.write(f"**Tu respuesta:** {selected}. {option_map[selected]}")
        st.write(f"**Respuesta correcta:** {correct}. {option_map[correct]}")

        st.markdown("### Explicación legal")

        if selected == correct:
            st.write(q["feedback_correcto"])
        else:
            st.write(q["feedback_error"])

        if q["referencia_legal"]:
            st.write(f"**Referencia legal:** {q['referencia_legal']}")

        if st.button("Continuar"):
            st.session_state.current_index += 1
            st.session_state.show_feedback = False

            if st.session_state.current_index >= total:
                st.session_state.finished = True

            st.rerun()

        if st.button("Volver al menú"):
            reset_to_menu()
            st.rerun()


def render_final():
    total = len(st.session_state.session_questions)
    score = st.session_state.score
    pct = int((score / total) * 100)

    st.title("Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Aciertos", score)
    c2.metric("Errores", total - score)
    c3.metric("Rendimiento", f"{pct}%")

    st.write(get_performance_message(pct))

    if st.button("Repetir"):
        start_mode(st.session_state.mode, questions, 20)
        st.rerun()

    if st.button("Volver al menú"):
        reset_to_menu()
        st.rerun()


# ------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------
if st.session_state.mode == "menu":
    render_menu()
elif st.session_state.finished:
    render_final()
else:
    render_question()
