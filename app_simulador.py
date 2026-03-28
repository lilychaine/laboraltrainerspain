import json
import os
import random
import streamlit as st

# ============================================================
# SIMULADOR DE PRÁCTICA LABORAL Y SEGURIDAD SOCIAL
# Versión estable:
# - métricas superiores con st.metric()
# - sin recortes de cards
# - sin mezclar base normativa con la pregunta
# - la referencia legal solo aparece después de responder
# - mantiene el banco completo: usa el archivo válido con más casos
# ============================================================

CANDIDATE_FILES = [
    "simulador_base_final.json",
    "simulador_base.json",
]
ERRORS_FILE = "errores_simulador.json"

st.set_page_config(
    page_title="Simulador de práctica laboral",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------
# CARGA DE DATOS
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


@st.cache_data
def load_questions():
    candidates = []
    for path in CANDIDATE_FILES:
        data = load_json_file(path)
        candidates.append((path, data, len(data)))

    candidates.sort(key=lambda x: x[2], reverse=True)
    best_path, best_data, best_n = candidates[0]

    if best_n == 0:
        st.error("No se encontró ningún banco válido. Sube simulador_base_limpio.json o simulador_base.json.")
        st.stop()

    required_keys = {
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
        "texto_base",
    }

    cleaned = []
    for row in best_data:
        if not isinstance(row, dict):
            continue
        if required_keys - set(row.keys()):
            continue

        cleaned.append(
            {
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
                "referencia_legal": str(row["referencia_legal"]),
                "texto_base": str(row["texto_base"]),
            }
        )

    if not cleaned:
        st.error("El archivo encontrado no contiene registros válidos.")
        st.stop()

    return cleaned, best_path


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


questions, active_data_file = load_questions()

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
        return "Nivel muy sólido. Tu criterio operativo está bien orientado a un entorno real de gestión laboral."
    if pct >= 75:
        return "Buen nivel. Hay una base práctica clara, aunque conviene reforzar precisión en algunos trámites."
    if pct >= 60:
        return "Nivel intermedio. Ya identificas parte de la lógica operativa, pero todavía hay áreas de mejora relevantes."
    return "Conviene reforzar la base, especialmente en altas, bajas, cotización y recaudación."


def store_error_question(q):
    errors = load_errors()
    if not any(str(x.get("id", "")) == str(q["id"]) for x in errors):
        errors.append(q)
        save_errors(errors)


def start_mode(mode_name, source_questions, n_questions=None):
    session_questions = unique_by_id(source_questions.copy())
    random.shuffle(session_questions)

    if n_questions is not None:
        session_questions = session_questions[: min(n_questions, len(session_questions))]

    st.session_state.mode = mode_name
    st.session_state.session_questions = session_questions
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.show_feedback = False
    st.session_state.selected_option = None
    st.session_state.finished = False
    st.session_state.session_results = []
    st.session_state.last_answered_id = None


def reset_to_menu():
    st.session_state.mode = "menu"
    st.session_state.session_questions = []
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.show_feedback = False
    st.session_state.selected_option = None
    st.session_state.finished = False
    st.session_state.session_results = []
    st.session_state.last_answered_id = None


def init_state():
    if "mode" not in st.session_state:
        reset_to_menu()


init_state()

# ------------------------------------------------------------
# COMPONENTES UI
# ------------------------------------------------------------
def render_top_metrics(mode_text, progress_text, score_value):
    c1, c2, c3 = st.columns(3, gap="small")

    with c1:
        st.metric("Modalidad", mode_text, border=True)
    with c2:
        st.metric("Progreso", progress_text, border=True)
    with c3:
        st.metric("Aciertos", str(score_value), border=True)


def render_menu():
    st.title("Simulador de práctica laboral y Seguridad Social")
    st.caption(
        "Entrenamiento orientado a gestión operativa de personas, contratación, cotización, recaudación y control administrativo."
    )

    c1, c2 = st.columns(2, gap="large")

    with c1:
        with st.container(border=True):
            st.subheader("Modo simulacro")
            st.write("Sesión mixta con casos aleatorios y evaluación final.")
            if st.button("Empezar simulacro de 20 casos", width="stretch", key="menu_simulacro"):
                start_mode("simulacro", questions, n_questions=20)
                st.rerun()

        st.write("")

        with st.container(border=True):
            st.subheader("Repaso guiado")
            st.write("Práctica secuencial con feedback completo tras cada respuesta.")
            if st.button("Empezar repaso guiado", width="stretch", key="menu_repaso"):
                start_mode("repaso", questions, n_questions=None)
                st.rerun()

    with c2:
        errors = load_errors()

        with st.container(border=True):
            st.subheader("Repaso de errores")
            st.write(f"Errores guardados: **{len(errors)}**")

            if errors:
                if st.button("Reestudiar errores", width="stretch", key="menu_errores"):
                    start_mode("errores", errors, n_questions=None)
                    st.rerun()
            else:
                st.info("Todavía no hay errores guardados.")

            if st.button("Vaciar errores guardados", width="stretch", key="menu_vaciar"):
                save_errors([])
                st.success("Errores eliminados.")
                st.rerun()

        st.write("")

        with st.container(border=True):
            st.subheader("Banco disponible")
            st.write(f"Archivo activo: **{active_data_file}**")
            st.write(f"Casos cargados: **{len(questions)}**")

            temas = get_topic_counts(questions)
            for tema, n in sorted(temas.items(), key=lambda x: (-x[1], x[0])):
                st.write(f"- {tema}: {n}")


def render_question():
    if not st.session_state.session_questions:
        st.warning("No hay casos disponibles para este modo.")
        if st.button("Volver al menú", width="stretch", key="empty_back"):
            reset_to_menu()
            st.rerun()
        return

    if st.session_state.current_index >= len(st.session_state.session_questions):
        st.session_state.finished = True
        st.rerun()
        return

    q = st.session_state.session_questions[st.session_state.current_index]
    option_map = build_option_map(q)
    total = len(st.session_state.session_questions)
    current_num = st.session_state.current_index + 1

    render_top_metrics(
        st.session_state.mode.title(),
        f"{current_num}/{total}",
        st.session_state.score,
    )

    st.write("")

    with st.container(border=True):
        st.markdown(f"**Materia:** {q['materia']}")
        st.markdown(f"**Tema:** {q['tema']}")
        st.divider()
        st.markdown("**Situación práctica**")
        st.write(q["situacion"])
        st.markdown("**Pregunta**")
        st.write(q["pregunta"])

    st.write("")

    if not st.session_state.show_feedback:
        with st.form(key=f"form_{q['id']}"):
            selected = st.radio(
                "Selecciona la opción correcta:",
                options=["A", "B", "C", "D"],
                format_func=lambda x: f"{x}. {option_map[x]}",
            )

            c1, c2 = st.columns(2, gap="small")
            submit_answer = c1.form_submit_button("Responder", width="stretch")
            back_menu = c2.form_submit_button("Volver al menú", width="stretch")

        if back_menu:
            reset_to_menu()
            st.rerun()

        if submit_answer:
            st.session_state.selected_option = selected
            st.session_state.show_feedback = True
            st.session_state.last_answered_id = q["id"]

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
        selected = st.session_state.selected_option
        correct = q["respuesta_correcta"]

        if selected == correct:
            st.success("Respuesta correcta")
            with st.container(border=True):
                st.write(f"**Tu respuesta:** {selected}. {option_map[selected]}")
                st.write(f"**Respuesta correcta:** {correct}. {option_map[correct]}")
                st.write(q["feedback_correcto"])
        else:
            st.error("Respuesta incorrecta")
            with st.container(border=True):
                st.write(f"**Tu respuesta:** {selected}. {option_map[selected]}")
                st.write(f"**Respuesta correcta:** {correct}. {option_map[correct]}")
                st.write(q["feedback_error"])

        st.write("")

        with st.expander("Ver explicación legal y base normativa", expanded=True):
            st.write(f"**Referencia legal:** {q['referencia_legal']}")
            st.write(q["texto_base"])

        st.write("")

        c1, c2 = st.columns(2, gap="small")
        if c1.button("Continuar", width="stretch", key=f"next_{q['id']}"):
            st.session_state.current_index += 1
            st.session_state.show_feedback = False
            st.session_state.selected_option = None
            st.session_state.last_answered_id = None

            if st.session_state.current_index >= len(st.session_state.session_questions):
                st.session_state.finished = True

            st.rerun()

        if c2.button("Volver al menú", width="stretch", key=f"back_after_{q['id']}"):
            reset_to_menu()
            st.rerun()


def render_final():
    total = len(st.session_state.session_questions)
    score = st.session_state.score
    errors = total - score
    pct = round((score / total) * 100) if total > 0 else 0

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
    if c1.button("Repetir", width="stretch", key="repeat_mode"):
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

    if c2.button("Volver al menú principal", width="stretch", key="final_menu"):
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
