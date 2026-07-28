import time
import unicodedata
import urllib.parse
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RUTINAS W360",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# CSS PERSONALIZADO Y ESTILOS
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Ocultar UI estándar de Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Títulos */
    .header-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #1E293B;
        margin-bottom: 15px;
    }

    .exercise-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* Botón Generar Rutina */
    div.stButton > button[key="btn_generar"] {
        width: 100% !important;
        padding: 10px 16px !important;
        font-size: 16px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
    }

    /* Métricas Secundarias */
    .sub-metric-card {
        text-align: center;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .sub-metric-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
    }
    .sub-metric-value {
        font-size: 1.4rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 2px;
    }

    /* Tarjeta Destacada Prescripción */
    .highlight-card {
        text-align: center;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        padding: 14px;
        margin: 10px 0;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
    }
    .highlight-card-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .highlight-card-desc {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4px;
    }

    /* Tarjeta de Descripción Técnica */
    .description-card {
        background-color: #f1f5f9;
        border-left: 4px solid #0284c7;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0 15px 0;
        font-size: 0.92rem;
        color: #334155;
        line-height: 1.5;
    }

    /* Detalle del Ejercicio */
    .exercise-details {
        text-align: center;
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 10px;
    }

    /* Barra de Progresión */
    .progress-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 12px 16px;
        margin-top: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .progress-label {
        font-size: 0.9rem;
        font-weight: 800;
        color: #0f172a;
    }
    .progress-percentage {
        font-size: 0.85rem;
        font-weight: 800;
        color: #0284c7;
        background-color: #e0f2fe;
        padding: 2px 8px;
        border-radius: 10px;
    }

    /* Estilo botón/tarjeta Cronómetro */
    div.stButton > button[key^="btn_card_timer_"] {
        width: 100% !important;
        background-color: #fef08a !important;
        border: 2px solid #facc15 !important;
        border-radius: 14px !important;
        padding: 16px 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        cursor: pointer !important;
        color: #854d0e !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
        line-height: 1.4 !important;
        transition: transform 0.1s ease, background-color 0.1s ease !important;
    }
    div.stButton > button[key^="btn_card_timer_"]:hover {
        background-color: #fde047 !important;
        border-color: #eab308 !important;
        color: #713f12 !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. GESTIÓN DE ACCESO Y LOGIN
# -----------------------------------------------------------------------------
USUARIOS_ACTIVOS = {
    "Josama": "1980",
    "cliente_demo": "fitness2026",
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = ""


def pantalla_login():
    st.markdown("---")
    st.markdown(
        "<div class='header-title'>🔒 Acceso RUTINAS W360</div>",
        unsafe_allow_html=True,
    )
    st.write("Ingresa tus credenciales para continuar:")

    usuario_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión", type="primary", use_container_width=True):
        if (
            usuario_input in USUARIOS_ACTIVOS
            and USUARIOS_ACTIVOS[usuario_input] == password_input
        ):
            st.session_state.autenticado = True
            st.session_state.usuario_actual = usuario_input
            st.success(f"¡Bienvenido/a, {usuario_input}!")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


if not st.session_state.autenticado:
    pantalla_login()
    st.stop()

# -----------------------------------------------------------------------------
# 3. CARGA DE DATOS Y LÓGICA AUXILIAR AVANZADA
# -----------------------------------------------------------------------------

col_usr1, col_usr2 = st.columns([3, 1])
with col_usr1:
    st.caption(f"👤 **Cliente:** `{st.session_state.usuario_actual}`")
with col_usr2:
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.paso_actual = 0
        st.session_state.df_rutina = None
        st.session_state.modo_entrenamiento = False
        st.rerun()


def normalizar_texto(texto):
    if texto is None or pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


@st.cache_data
def cargar_ejercicios():
    df = pd.read_excel("ejercicios.xlsx")
    for col in df.columns:
        df[col] = df[col].fillna("-")
    return df


try:
    df_ejercicios = cargar_ejercicios()
except Exception as e:
    st.error(f"Error al cargar 'ejercicios.xlsx': {e}")
    st.stop()


def es_ejercicio_unilateral(row):
    if row is None or not isinstance(row, pd.Series):
        return False

    for col in row.index:
        col_norm = normalizar_texto(str(col))
        val_norm = normalizar_texto(str(row[col]))
        if any(k in col_norm for k in ["lateralidad", "unilateral", "tipo"]):
            if any(
                u in val_norm
                for u in [
                    "unilateral",
                    "1 pierna",
                    "1 brazo",
                    "monopodal",
                    "si",
                    "por lado",
                ]
            ):
                return True

    nombre_norm = normalizar_texto(str(row.get("Nombre", "")))
    palabras_unilaterales = [
        "unilateral",
        "a 1 pierna",
        "a 1 brazo",
        "a una mano",
        "a una pierna",
        "1 brazo",
        "1 pierna",
        "alterno",
        "monopodal",
        "zancada",
        "zancadas",
        "lunge",
    ]
    if any(p in nombre_norm for p in palabras_unilaterales):
        return True

    return False


def calcular_series_fisiologicas(duracion_total_min, nivel, row):
    nombre_norm = normalizar_texto(str(row.get("Nombre", "")))
    cat_norm = normalizar_texto(
        str(row.get("Grupo Muscular", row.get("Tren", "")))
    )

    es_multiarticular_pesado = any(
        k in nombre_norm
        for k in [
            "sentadilla",
            "peso muerto",
            "press",
            "dominadas",
            "remo",
            "hip thrust",
            "zancada",
        ]
    )
    es_core_movilidad = any(
        k in cat_norm or k in nombre_norm
        for k in ["core", "plancha", "abdominal", "movilidad", "estiramiento"]
    )

    if duracion_total_min <= 20:
        if es_core_movilidad:
            return 2
        elif es_multiarticular_pesado:
            return 3
        else:
            return 2
    elif duracion_total_min <= 30:
        if es_core_movilidad:
            return 2
        elif es_multiarticular_pesado:
            return 3
        else:
            return 3
    else:  # 45 o 60 min
        if es_core_movilidad:
            return 3
        elif es_multiarticular_pesado:
            return 4
        else:
            return 3


def obtener_prescripcion_profesional(duracion_total_min, nivel, row=None):
    if row is None:
        return "3 series × 10-12 reps"

    num_series = calcular_series_fisiologicas(duracion_total_min, nivel, row)
    cat = normalizar_texto(str(row.get("Tren", "")))

    if "core" in cat or "core" in normalizar_texto(
        str(row.get("Grupo Muscular", ""))
    ):
        reps_texto = "30-45 seg trabajo"
    else:
        if es_ejercicio_unilateral(row):
            reps_texto = "8-10 reps / lado"
        else:
            reps_texto = "10-12 reps"

    return f"{num_series} series × {reps_texto}"


def es_ejercicio_gluteo(row_dict):
    """Detecta si un ejercicio pertenece al grupo muscular de glúteos."""
    campos = [
        str(row_dict.get("Grupo Muscular", "")),
        str(row_dict.get("Tren", "")),
        str(row_dict.get("Nombre", "")),
        str(row_dict.get("Musculo Principal", "")),
        str(row_dict.get("Musculo", "")),
    ]
    texto_total = " ".join([normalizar_texto(c) for c in campos])
    palabras_gluteo = [
        "gluteo",
        "gluteos",
        "hip thrust",
        "puente de gluteo",
        "patada de gluteo",
        "abduccion",
    ]
    return any(p in texto_total for p in palabras_gluteo)


def es_ejercicio_abdominal_core(row_dict):
    """Detecta si un ejercicio pertenece al grupo de abdominales/core."""
    campos = [
        str(row_dict.get("Grupo Muscular", "")),
        str(row_dict.get("Tren", "")),
        str(row_dict.get("Nombre", "")),
        str(row_dict.get("Musculo Principal", "")),
        str(row_dict.get("Musculo", "")),
    ]
    texto_total = " ".join([normalizar_texto(c) for c in campos])
    palabras_core = [
        "core",
        "abdominal",
        "abdominales",
        "plancha",
        "crunch",
        "rueda abdominal",
        "sit up",
    ]
    return any(p in texto_total for p in palabras_core)


def seleccionar_y_estructurar_rutina(df_candidatos, df_base, cantidad_deseada):
    """Garantiza:

    1. Inicio OBLIGATORIO con Glúteos.
    2. Final OBLIGATORIO del bloque de fuerza con Abdominales/Core.
    3. Alternancia en ejercicios intermedios.
    """
    todos_registros = df_base.to_dict("records")
    candidatos_registros = df_candidatos.to_dict("records")

    # 1. Búsqueda prioritaria de un ejercicio de Glúteo
    gluteos_candidatos = [
        r for r in candidatos_registros if es_ejercicio_gluteo(r)
    ]
    if not gluteos_candidatos:
        gluteos_candidatos = [
            r for r in todos_registros if es_ejercicio_gluteo(r)
        ]

    if gluteos_candidatos:
        ej_gluteo = (
            pd.DataFrame(gluteos_candidatos).sample(n=1).to_dict("records")[0]
        )
    else:
        ej_gluteo = (
            candidatos_registros[0]
            if candidatos_registros
            else todos_registros[0]
        )

    # 2. Búsqueda prioritaria de ejercicios de Core/Abdominales
    core_candidatos = [
        r
        for r in candidatos_registros
        if es_ejercicio_abdominal_core(r) and r != ej_gluteo
    ]
    if not core_candidatos:
        core_candidatos = [
            r
            for r in todos_registros
            if es_ejercicio_abdominal_core(r) and r != ej_gluteo
        ]

    cant_core = 1 if cantidad_deseada <= 4 else 2
    ejercicios_core = []
    if core_candidatos:
        cant_tomar = min(cant_core, len(core_candidatos))
        ejercicios_core = (
            pd.DataFrame(core_candidatos)
            .sample(n=cant_tomar)
            .to_dict("records")
        )

    # 3. Ejercicios intermedios
    usados = [ej_gluteo] + ejercicios_core
    cuantos_intermedios = max(0, cantidad_deseada - len(usados))

    resto_candidatos = [r for r in candidatos_registros if r not in usados]
    if len(resto_candidatos) < cuantos_intermedios:
        resto_base = [r for r in todos_registros if r not in usados]
        resto_candidatos.extend(
            [r for r in resto_base if r not in resto_candidatos]
        )

    intermedios = []
    if resto_candidatos and cuantos_intermedios > 0:
        cant_interm = min(cuantos_intermedios, len(resto_candidatos))
        intermedios = (
            pd.DataFrame(resto_candidatos)
            .sample(n=cant_interm)
            .to_dict("records")
        )

    # Alternar grupo muscular en intermedios
    intermedios_ordenados = []
    while intermedios:
        if not intermedios_ordenados:
            intermedios_ordenados.append(intermedios.pop(0))
            continue

        ult_grupo = normalizar_texto(
            str(intermedios_ordenados[-1].get("Grupo Muscular", ""))
        )
        cand_idx = -1
        for idx, item in enumerate(intermedios):
            if (
                normalizar_texto(str(item.get("Grupo Muscular", "")))
                != ult_grupo
            ):
                cand_idx = idx
                break

        if cand_idx != -1:
            intermedios_ordenados.append(intermedios.pop(cand_idx))
        else:
            intermedios_ordenados.append(intermedios.pop(0))

    # Estructura Final Garantizada: [GLÚTEO] + [INTERMEDIOS] + [ABDOMINALES]
    rutina_final = [ej_gluteo] + intermedios_ordenados + ejercicios_core
    return pd.DataFrame(rutina_final)


def renderizar_temporizador_15s(paso_id):
    """Crono interactivo unificado sin tags HTML visibles en la etiqueta del botón.

    Conserva la pausa de 3.5s tras el final.
    """
    key_timer_activo = f"timer_activo_{paso_id}"
    key_timer_inicio = f"timer_inicio_{paso_id}"

    if key_timer_activo not in st.session_state:
        st.session_state[key_timer_activo] = False

    duracion = 15

    if not st.session_state[key_timer_activo]:
        texto_boton = "⏱️ DESCANSO ENTRE SERIES: 15s\n👇 (Toca aquí para iniciar cuenta atrás)"
        if st.button(
            texto_boton,
            key=f"btn_card_timer_{paso_id}",
            use_container_width=True,
        ):
            st.session_state[key_timer_activo] = True
            st.session_state[key_timer_inicio] = datetime.now()
            st.rerun()

    else:
        tiempo_transcurrido = (
            datetime.now() - st.session_state[key_timer_inicio]
        ).total_seconds()
        tiempo_restante = max(0, int(duracion - tiempo_transcurrido))

        if tiempo_restante > 0:
            color_numero = "#16a34a" if tiempo_restante > 10 else "#dc2626"
            st.markdown(
                f"""
                <div style="background-color: #fef08a; border-radius: 14px; padding: 14px; text-align: center; border: 2px solid #facc15; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 10px;">
                    <div style="color: #854d0e; font-size: 0.85rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">PRÓXIMA REPETICIÓN EN...</div>
                    <div style="color: {color_numero}; font-size: 2.8rem; font-weight: 900; font-family: monospace; line-height: 1;">{tiempo_restante}s</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(1)
            st.rerun()
        else:
            st.markdown(
                """
                <div style="background-color: #22c55e; border-radius: 14px; padding: 16px; text-align: center; border: 2px solid #16a34a; box-shadow: 0 4px 12px rgba(0,0,0,0.12); margin-bottom: 10px;">
                    <div style="color: #ffffff; font-size: 0.85rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">¡TIEMPO AGOTADO!</div>
                    <div style="color: #ffffff; font-size: 2.6rem; font-weight: 900; font-family: monospace; line-height: 1;">GOOOO! 🚀</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(3.5)
            st.session_state[key_timer_activo] = False
            st.rerun()


# Variables de sesión iniciales
if "paso_actual" not in st.session_state:
    st.session_state.paso_actual = 0
if "df_rutina" not in st.session_state:
    st.session_state.df_rutina = None
if "tiempo_estimado" not in st.session_state:
    st.session_state.tiempo_estimado = 0
if "nivel_seleccionado" not in st.session_state:
    st.session_state.nivel_seleccionado = "Básico"
if "modo_entrenamiento" not in st.session_state:
    st.session_state.modo_entrenamiento = False
if "duracion_elegida" not in st.session_state:
    st.session_state.duracion_elegida = "30 min"

# -----------------------------------------------------------------------------
# 4. CONFIGURADOR DE RUTINA Y CABECERA
# -----------------------------------------------------------------------------

st.markdown(
    '<div class="header-title" id="inicio-app">🏋️‍♂️ RUTINAS W360 🏋️‍♂️</div>',
    unsafe_allow_html=True,
)

OPCION_BLANCO = "--- Sin filtro (Cualquiera) ---"

if not st.session_state.modo_entrenamiento:
    with st.expander(
        "⚙️ Configurar Parámetros", expanded=(st.session_state.df_rutina is None)
    ):
        col_n1, col_n2, col_n3 = st.columns([1, 1, 1])

        with col_n1:
            niveles_base = ["Básico", "Intermedio", "Avanzado"]
            if "Nivel" in df_ejercicios.columns:
                extra_niveles = [
                    str(n).strip()
                    for n in df_ejercicios["Nivel"].dropna().unique()
                    if str(n).strip() not in ["-", ""]
                ]
                for n in extra_niveles:
                    if n not in niveles_base:
                        niveles_base.append(n)

            nivel_seleccionado = st.selectbox(
                "Nivel de Exigencia", niveles_base
            )

        with col_n2:
            opciones_tren = [
                OPCION_BLANCO,
                "Tren superior",
                "Tren inferior",
                "Core",
            ]
            tren_seleccionado = st.selectbox(
                "Estructura Corporal", opciones_tren
            )

        with col_n3:
            opciones_objetivo = [
                OPCION_BLANCO,
                "Dolor lumbar",
                "Dolor cervical",
                "Dolor torácico",
                "Postural",
                "Bajar peso",
                "Dolor rodilla",
                "Dolor hombro",
            ]
            objetivo_seleccionado = st.selectbox(
                "Objetivo / Dolor", opciones_objetivo
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align: center; font-weight: 700; color: #475569; margin-bottom: 8px;'>⏱️ Tiempo de duración del entrenamiento</p>",
            unsafe_allow_html=True,
        )

        col_t1, col_t2, col_t3, col_t4 = st.columns(4)

        opciones_tiempo = ["20 min", "30 min", "45 min", "60 min"]
        cols = [col_t1, col_t2, col_t3, col_t4]

        for idx, tiempo_opt in enumerate(opciones_tiempo):
            with cols[idx]:
                es_activo = st.session_state.duracion_elegida == tiempo_opt
                if es_activo:
                    st.markdown(
                        f"""
                        <style>
                        div.stButton > button[key="btn_time_{tiempo_opt}"] {{
                            background-color: #0284c7 !important;
                            color: white !important;
                            border: 1px solid #0369a1 !important;
                            font-weight: 800 !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                if st.button(
                    tiempo_opt,
                    key=f"btn_time_{tiempo_opt}",
                    use_container_width=True,
                ):
                    st.session_state.duracion_elegida = tiempo_opt
                    st.rerun()

        st.markdown(
            f"""
            <div style="text-align: center; margin-top: 10px; margin-bottom: 10px;">
                <span style="background-color: #0284c7; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 800; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(2,132,199,0.2);">
                    SELECCIONADO: {st.session_state.duracion_elegida.upper()}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        duracion_minutos_total = int(
            str(st.session_state.duracion_elegida).split()[0]
        )
        TIEMPO_ESTIRAMIENTOS_MIN = 10
        duracion_fuerza_min = max(
            5, duracion_minutos_total - TIEMPO_ESTIRAMIENTOS_MIN
        )

        if st.button(
            "⚡ Generar rutina personalizada",
            key="btn_generar",
            type="primary",
            use_container_width=True,
        ):
            df_filtrado = df_ejercicios.copy()

            if "Nivel" in df_filtrado.columns:
                nivel_norm_sel = normalizar_texto(nivel_seleccionado)
                df_filtrado = df_filtrado[
                    df_filtrado["Nivel"].apply(
                        lambda x: nivel_norm_sel in normalizar_texto(str(x))
                    )
                ]

            if tren_seleccionado != OPCION_BLANCO:
                tren_norm = normalizar_texto(tren_seleccionado)
                cols_categoria = [
                    c
                    for c in df_filtrado.columns
                    if any(
                        k in str(c).lower()
                        for k in ["tren", "categoria", "grupo", "zona"]
                    )
                ]
                if cols_categoria:
                    col_cat = cols_categoria[0]
                    df_filtrado = df_filtrado[
                        df_filtrado[col_cat].apply(
                            lambda x: tren_norm in normalizar_texto(str(x))
                        )
                    ]

            if objetivo_seleccionado != OPCION_BLANCO:
                obj_norm = normalizar_texto(objetivo_seleccionado)
                cols_objetivo = [
                    c
                    for c in df_filtrado.columns
                    if any(
                        k in str(c).lower()
                        for k in [
                            "objetivo",
                            "dolor",
                            "enfoque",
                            "patologia",
                        ]
                    )
                ]
                if cols_objetivo:
                    col_obj = cols_objetivo[0]
                    df_filtrado = df_filtrado[
                        df_filtrado[col_obj].apply(
                            lambda x: obj_norm in normalizar_texto(str(x))
                        )
                    ]

            if df_filtrado.empty:
                st.warning(
                    "⚠️ No hay suficientes ejercicios específicos con todos esos filtros. Mostrando ejercicios generales compatibles."
                )
                df_filtrado = df_ejercicios.copy()

            ejercicios_objetivo = max(2, int(round(duracion_fuerza_min / 4.5)))

            # Algoritmo de estructuración biomecánica garantizado
            df_rutina = seleccionar_y_estructurar_rutina(
                df_filtrado, df_ejercicios, ejercicios_objetivo
            )

            st.session_state.df_rutina = df_rutina
            st.session_state.tiempo_estimado = duracion_fuerza_min
            st.session_state.paso_actual = 0
            st.session_state.nivel_seleccionado = nivel_seleccionado
            st.session_state.modo_entrenamiento = False
            st.rerun()

    st.markdown("---")

    if (
        st.session_state.df_rutina is not None
        and not st.session_state.df_rutina.empty
    ):
        df_rutina = st.session_state.df_rutina
        tiempo_ejercicios = st.session_state.tiempo_estimado
        tiempo_total_sesion = tiempo_ejercicios + TIEMPO_ESTIRAMIENTOS_MIN

        st.markdown(
            "<h4 style='text-align: center; color: #16a34a;'>🔥 Rutina generada con éxito</h4>",
            unsafe_allow_html=True,
        )

        c_m1, c_m2 = st.columns(2)
        with c_m1:
            st.markdown(
                f"""
                <div class="sub-metric-card">
                    <div class="sub-metric-title">🏋️ Fuerza ({len(df_rutina)} ej.)</div>
                    <div class="sub-metric-value">{tiempo_ejercicios} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_m2:
            st.markdown(
                f"""
                <div class="sub-metric-card">
                    <div class="sub-metric-title">🧘 Estiramientos</div>
                    <div class="sub-metric-value">{TIEMPO_ESTIRAMIENTOS_MIN} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-card-subtitle">Tiempo Total Sesión</div>
                <div class="highlight-card-value" style="font-size: 1.8rem; font-weight: 800; color: #38bdf8;">{tiempo_total_sesion} min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "🚀 Comenzar Ahora",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.modo_entrenamiento = True
            st.session_state.paso_actual = 0
            st.rerun()

# -----------------------------------------------------------------------------
# 5. MODO ENTRENAMIENTO GUIADO
# -----------------------------------------------------------------------------

elif (
    st.session_state.df_rutina is not None
    and st.session_state.modo_entrenamiento
):
    df_rutina = st.session_state.df_rutina
    total_ejercicios = len(df_rutina)
    paso_actual = st.session_state.paso_actual

    if paso_actual < total_ejercicios:
        row = df_rutina.iloc[paso_actual]

        nombre_ej = str(row.get("Nombre", f"Ejercicio {paso_actual + 1}"))
        st.markdown(
            f'<div class="exercise-title">{nombre_ej}</div>',
            unsafe_allow_html=True,
        )

        duracion_min_total = int(
            str(st.session_state.duracion_elegida).split()[0]
        )
        series_reps = obtener_prescripcion_profesional(
            duracion_min_total, st.session_state.nivel_seleccionado, row=row
        )

        cols_obj = [
            c
            for c in row.index
            if any(
                k in str(c).lower()
                for k in ["objetivo", "dolor", "enfoque", "patologia"]
            )
        ]
        val_objetivo = (
            str(row[cols_obj[0]])
            if cols_obj and pd.notna(row[cols_obj[0]])
            else "-"
        )

        material = str(row.get("Material", "-"))
        grupo_m = str(row.get("Grupo Muscular", row.get("Tren", "-")))

        st.markdown(
            f'<div class="exercise-details"><b>Objetivo:</b> {val_objetivo} &nbsp;|&nbsp; <b>Material:</b> {material} &nbsp;|&nbsp; <b>Estructura:</b> {grupo_m}</div>',
            unsafe_allow_html=True,
        )

        desc_excel = str(row.get("Descripcion", row.get("Instrucciones", "")))
        texto_base = "Mantén la postura alineada, el abdomen activo, realiza un movimiento controlado sin balanceos bruscos y mantén una respiración fluida."

        if desc_excel and desc_excel != "-":
            texto_descripcion = (
                f"{desc_excel}<br><br>💡 <b>Técnica:</b> {texto_base}"
            )
        else:
            texto_descripcion = texto_base

        st.markdown(
            f"""
            <div class="description-card">
                <b>📌 Ejecución paso a paso:</b><br>{texto_descripcion}
            </div>
            """,
            unsafe_allow_html=True,
        )

        columnas_fotos = ["Imagen_1", "Imagen_2", "Imagen_3", "Imagen_4"]
        urls_validas = [
            str(row[col])
            for col in columnas_fotos
            if col in row
            and pd.notna(row[col])
            and str(row[col]).strip() not in ["-", ""]
        ]

        if urls_validas:
            cols_img = st.columns(len(urls_validas))
            for index, url in enumerate(urls_validas):
                with cols_img[index]:
                    st.image(
                        url, caption=f"Paso {index + 1}", use_container_width=True
                    )

        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-card-subtitle">Prescripción de Trabajo</div>
                <div class="highlight-card-desc">{series_reps}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Crono interactivo
        renderizar_temporizador_15s(paso_actual)

        st.markdown("---")

        col_nav1, col_nav2 = st.columns([1, 1])

        with col_nav1:
            if paso_actual > 0:
                if st.button("⬅️ Anterior", use_container_width=True):
                    st.session_state.paso_actual -= 1
                    st.rerun()

        with col_nav2:
            if st.button(
                "✅ ➔ Siguiente ejercicio",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.paso_actual += 1
                st.rerun()

        progreso_porcentaje = (
            float((paso_actual + 1) / total_ejercicios)
            if total_ejercicios > 0
            else 1.0
        )
        porcentaje_num = int(progreso_porcentaje * 100)

        st.markdown(
            f"""
            <div class="progress-card">
                <div class="progress-header">
                    <div class="progress-label">🔥 Ejercicio {paso_actual + 1} de {total_ejercicios}</div>
                    <div class="progress-percentage">{porcentaje_num}% completado</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(progreso_porcentaje, 1.0))

    elif paso_actual == total_ejercicios:
        st.markdown(
            '<div class="exercise-title">🧘 Bloque de Enfriamiento y Estiramientos</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
        <div style="text-align: center;">
            <p>🧘‍♂️ <b>Isquiotibiales y Cuádriceps:</b> 2 series de 30 seg por pierna.</p>
            <p>🧘‍♀️ <b>Pectorales:</b> 2 series de 30 seg contra pared.</p>
            <p>🧘‍♂️ <b>Glúteos:</b> 2 series de 30 seg por lado.</p>
            <p>🧘‍♀️ <b>Cobra / Lumbar:</b> 2 series de 30 seg suave.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅️ Anterior", use_container_width=True):
                st.session_state.paso_actual -= 1
                st.rerun()
        with col_nav2:
            if st.button(
                "🏁 Finalizar Entrenamiento",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.paso_actual += 1
                st.rerun()

        st.markdown(
            """
            <div class="progress-card">
                <div class="progress-header">
                    <div class="progress-label">🏁 Bloque Final: Estiramientos</div>
                    <div class="progress-percentage">100% completado</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(1.0)

    else:
        st.balloons()
        st.markdown(
            "<h3 style='text-align: center; color: #16a34a;'>🎉 ¡Entrenamiento completado con éxito!</h3>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button(
            "🔄 Volver al Menú", type="primary", use_container_width=True
        ):
            st.session_state.paso_actual = 0
            st.session_state.modo_entrenamiento = False
            st.rerun()
