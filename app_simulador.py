import json
import os
import random
import streamlit as st

# ============================================================
# CONFIG
# ============================================================

DATA_FILE = "simulador_base_final.json"
ERRORS_FILE = "errores_simulador.json"

st.set_page_config(
    page_title="Simulador laboral",
    layout="wide"
)

# ============================================================
# CARGA DATOS
# ============================================================

def load_questions():
    if not os.path.exists(DATA_FILE):
        st.error("No se encontró el archivo de preguntas")
        st.stop()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def load_errors():
    if not os.path.exists(ERRORS_FILE):
        return []
    with open(ERRORS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_errors(errors):
    with open(ERRORS_FILE, "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2)


questions = load_questions()

# ============================================================
# HELPERS
# ============================================================

def build_options(q):
    return {
        "A": q["opcion_a"],
        "B": q["opcion_b"],
        "C": q["opcion_c"],
        "D": q["opcion_d"],
    }


def start_mode(mode, source, n=None):
    data = source.copy()
    random.shuffle(data)

    if n:
        data = data[:n]

    st.session_state.mode = mode
    st.session_state.data = data
    st.session_state.i = 0
    st.session_state.score = 0
    st.session_state.feedback = False
    st.session_state.sel = None


def reset():
    st.session_state.mode = "menu"
    st.session_state.data = []
    st.session_state.i = 0
    st.session_state.score = 0
    st.session_state.feedback = False
    st.session_state.sel = None


if "mode" not in st.session_state:
    reset()

# ============================================================
# UI
# ============================================================

def metrics():
    c1, c2, c3 = st.columns(3)
    c1.metric("Modalidad", st.session_state.mode)
    c2.metric("Progreso", f"{st.session_state.i+1}/{len(st.session_state.data)}")
    c3.metric("Aciertos", st.session_state.score)


def menu():
    st.title("Simulador de práctica laboral")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Simulacro (20 casos)", use_container_width=True):
            start_mode("simulacro", questions, 20)
            st.rerun()

        if st.button("Repaso guiado", use_container_width=True):
            start_mode("repaso", questions)
            st.rerun()

    with col2:
        errors = load_errors()

        if errors:
            if st.button("Repasar errores", use_container_width=True):
                start_mode("errores", errors)
                st.rerun()

        if st.button("Borrar errores", use_container_width=True):
            save_errors([])
            st.success("Errores eliminados")

        st.write(f"Total casos: {len(questions)}")


def question():
    q = st.session_state.data[st.session_state.i]
    opts = build_options(q)

    metrics()

    st.markdown("### Caso práctico")
    st.caption(f"{q['materia']} · {q['tema']}")

    st.markdown("**Situación práctica**")
    st.write(q["situacion"])

    st.markdown("**Pregunta**")
    st.write(q["pregunta"])

    if not st.session_state.feedback:

        sel = st.radio(
            "Selecciona:",
            ["A", "B", "C", "D"],
            format_func=lambda x: f"{x}. {opts[x]}"
        )

        if st.button("Responder"):
            st.session_state.sel = sel
            st.session_state.feedback = True

            if sel == q["respuesta_correcta"]:
                st.session_state.score += 1
            else:
                errors = load_errors()
                if q not in errors:
                    errors.append(q)
                    save_errors(errors)

            st.rerun()

        if st.button("Volver al menú"):
            reset()
            st.rerun()

    else:
        sel = st.session_state.sel
        correct = q["respuesta_correcta"]

        if sel == correct:
            st.success("Decisión adecuada")
        else:
            st.error("Decisión incorrecta")

        st.write(f"**Tu respuesta:** {sel}. {opts[sel]}")
        st.write(f"**Respuesta correcta:** {correct}. {opts[correct]}")

        st.markdown("### Explicación")

        if sel == correct:
            st.write(q["feedback_correcto"])
        else:
            st.write(q["feedback_error"])

        if st.button("Continuar"):
            st.session_state.i += 1
            st.session_state.feedback = False

            if st.session_state.i >= len(st.session_state.data):
                st.session_state.mode = "final"

            st.rerun()

        if st.button("Volver al menú"):
            reset()
            st.rerun()


def final():
    total = len(st.session_state.data)
    score = st.session_state.score
    pct = int(score / total * 100)

    st.title("Resultado")

    c1, c2, c3 = st.columns(3)
    c1.metric("Aciertos", score)
    c2.metric("Errores", total - score)
    c3.metric("Rendimiento", f"{pct}%")

    if st.button("Repetir"):
        start_mode("simulacro", questions, 20)
        st.rerun()

    if st.button("Menú"):
        reset()
        st.rerun()

# ============================================================
# ROUTER
# ============================================================

if st.session_state.mode == "menu":
    menu()
elif st.session_state.mode == "final":
    final()
else:
    question()
