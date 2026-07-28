import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RUTINAS W360",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* UI Estándar de Streamlit */
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
        font-size: 1.6rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* Tarjetas y Contenedores */
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

    .exercise-details {
        text-align: center;
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 10px;
    }

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
# 3. CARGA DE DATOS Y LÓGICA AUXILIAR
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
        st.session_state.inicio_entrenamiento = None
        st.session_state.modo_estiramientos = False
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
    return any(p in nombre_norm for p in palabras_unilaterales)


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
        return 2 if es_core_movilidad else 3 if es_multiarticular_pesado else 2
    elif duracion_total_min <= 30:
        return 2 if es_core_movilidad else 3
    else:
        return 3 if es_core_movilidad else 4 if es_multiarticular_pesado else 3


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
        reps_texto = (
            "8-10 reps / lado"
            if es_ejercicio_unilateral(row)
            else "10-12 reps"
        )

    return f"{num_series} series × {reps_texto}"


def es_ejercicio_gluteo(row_dict):
    campos = [
        str(row_dict.get("Grupo Muscular", "")),
        str(row_dict.get("Tren", "")),
        str(row_dict.get("Nombre", "")),
        str(row_dict.get("Musculo Principal", "")),
    ]
    texto_total = " ".join([normalizar_texto(c) for c in campos])
    return any(
        p in texto_total
        for p in [
            "gluteo",
            "gluteos",
            "hip thrust",
            "puente de gluteo",
            "patada de gluteo",
            "abduccion",
        ]
    )


def es_ejercicio_abdominal_core(row_dict):
    campos = [
        str(row_dict.get("Grupo Muscular", "")),
        str(row_dict.get("Tren", "")),
        str(row_dict.get("Nombre", "")),
        str(row_dict.get("Musculo Principal", "")),
    ]
    texto_total = " ".join([normalizar_texto(c) for c in campos])
    return any(
        p in texto_total
        for p in [
            "core",
            "abdominal",
            "abdominales",
            "plancha",
            "crunch",
            "rueda abdominal",
            "sit up",
        ]
    )


def seleccionar_y_estructurar_rutina(df_candidatos, df_base, cantidad_deseada):
    todos_registros = df_base.to_dict("records")
    candidatos_registros = df_candidatos.to_dict("records")

    gluteos_candidatos = [
        r for r in candidatos_registros if es_ejercicio_gluteo(r)
    ] or [r for r in todos_registros if es_ejercicio_gluteo(r)]

    ej_gluteo = (
        pd.DataFrame(gluteos_candidatos).sample(n=1).to_dict("records")[0]
        if gluteos_candidatos
        else candidatos_registros[0]
    )

    core_candidatos = [
        r
        for r in candidatos_registros
        if es_ejercicio_abdominal_core(r) and r != ej_gluteo
    ] or [
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

    usados = [ej_gluteo] + ejercicios_core
    cuantos_intermedios = max(0, cantidad_deseada - len(usados))

    resto_candidatos = [
        r
        for r in candidatos_registros
        if r not in usados and not es_ejercicio_abdominal_core(r)
    ]
    if len(resto_candidatos) < cuantos_intermedios:
        resto_base = [
            r
            for r in todos_registros
            if r not in usados and not es_ejercicio_abdominal_core(r)
        ]
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

    intermedios_ordenados = []
    while intermedios:
        if not intermedios_ordenados:
            intermedios_ordenados.append(intermedios.pop(0))
            continue

        ult_grupo = normalizar_texto(
            str(intermedios_ordenados[-1].get("Grupo Muscular", ""))
        )
        cand_idx = next(
            (
                idx
                for idx, item in enumerate(intermedios)
                if normalizar_texto(str(item.get("Grupo Muscular", "")))
                != ult_grupo
            ),
            -1,
        )

        if cand_idx != -1:
            intermedios_ordenados.append(intermedios.pop(cand_idx))
        else:
            intermedios_ordenados.append(intermedios.pop(0))

    rutina_final = [ej_gluteo] + intermedios_ordenados + ejercicios_core
    return pd.DataFrame(rutina_final)


def obtener_rutina_estiramientos(df_base, cantidad=4):
    todos = df_base.to_dict("records")
    estiramientos = [
        r
        for r in todos
        if any(
            k in normalizar_texto(str(r.get("Nombre", "")))
            or k
            in normalizar_texto(
                str(r.get("Grupo Muscular", r.get("Tren", "")))
            )
            for k in ["estiramiento", "movilidad", "flexibilidad", "relax"]
        )
    ]
    if len(estiramientos) < cantidad:
        estiramientos = todos

    cant_elegir = min(cantidad, len(estiramientos))
    return pd.DataFrame(estiramientos).sample(n=cant_elegir)


# Inicialización de estado
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
if "inicio_entrenamiento" not in st.session_state:
    st.session_state.inicio_entrenamiento = None
if "modo_estiramientos" not in st.session_state:
    st.session_state.modo_estiramientos = False
if "df_estiramientos" not in st.session_state:
    st.session_state.df_estiramientos = None
if "inicio_estiramientos" not in st.session_state:
    st.session_state.inicio_estiramientos = None

# -----------------------------------------------------------------------------
# 4. CONFIGURADOR DE RUTINA
# -----------------------------------------------------------------------------

st.markdown(
    '<div class="header-title" id="inicio-app">🏋️‍♂️ RUTINAS W360 🏋️‍♂️</div>',
    unsafe_allow_html=True,
)

OPCION_BLANCO = "--- Sin filtro (Cualquiera) ---"

if (
    not st.session_state.modo_entrenamiento
    and not st.session_state.modo_estiramientos
):
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

        # -----------------------------------------------------------------------------
        # BLOQUE: SELECTOR DE DURACIÓN CON ALTO IMPACTO VISUAL
        # -----------------------------------------------------------------------------

        # Estilo CSS adicional para el banner
        st.markdown(
            """
            <style>
            .time-banner-selected {
                background: #0f172a;
                border: 3px solid #22c55e;
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                margin: 15px 0;
                box-shadow: 0 0 15px rgba(34, 197, 94, 0.3);
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        # Título del selector
        st.markdown(
            "<p style='text-align: center; font-weight: 900; color: #0f172a; font-size: 1.1rem; margin-bottom: 8px;'>⏱️ TIEMPO DE DURACIÓN DEL ENTRENAMIENTO</p>",
            unsafe_allow_html=True,
        )

        # Renderizado de las 4 columnas de botones
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        opciones_tiempo = ["20 min", "30 min", "45 min", "60 min"]
        cols = [col_t1, col_t2, col_t3, col_t4]

        for idx, tiempo_opt in enumerate(opciones_tiempo):
            with cols[idx]:
                es_activo = st.session_state.duracion_elegida == tiempo_opt
                if es_activo:
                    # Estilo si está seleccionado (Verde fluorescente, borde grueso, sombra neón y efecto escala)
                    st.markdown(
                        f"""
                        <style>
                        div.stButton > button[key="btn_time_{tiempo_opt}"] {{
                            background-color: #22c55e !important;
                            color: #ffffff !important;
                            border: 3px solid #15803d !important;
                            font-weight: 900 !important;
                            font-size: 1.2rem !important;
                            box-shadow: 0 0 14px rgba(34, 197, 94, 0.8) !important;
                            transform: scale(1.03);
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    # Estilo si NO está seleccionado (Fondo oscuro, texto naranja)
                    st.markdown(
                        f"""
                        <style>
                        div.stButton > button[key="btn_time_{tiempo_opt}"] {{
                            background-color: #0f172a !important;
                            color: #f97316 !important;
                            border: 1px solid #334155 !important;
                            font-weight: 700 !important;
                            font-size: 1rem !important;
                        }}
                        div.stButton > button[key="btn_time_{tiempo_opt}"]:hover {{
                            background-color: #ea580c !important;
                            color: #ffffff !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                if st.button(
                    tiempo_opt, key=f"btn_time_{tiempo_opt}", use_container_width=True
                ):
                    st.session_state.duracion_elegida = tiempo_opt
                    st.rerun()

        # BANNER INFERIOR DE CONFIRMACIÓN VISUAL
        st.markdown(
            f"""
            <div class="time-banner-selected">
                <span style="color: #94a3b8; font-weight: 800; font-size: 0.85rem; letter-spacing: 1px; text-transform: uppercase;">DURACIÓN SELECCIONADA</span><br>
                <span style="color: #22c55e; font-weight: 900; font-size: 1.8rem; letter-spacing: 0.5px;">
                    🎯 {st.session_state.duracion_elegida.upper()}
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

        if st.button("🚀 Comenzar Ahora", type="primary", use_container_width=True):
            st.session_state.modo_entrenamiento = True
            st.session_state.paso_actual = 0
            st.session_state.inicio_entrenamiento = datetime.now()
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
        texto_descripcion = (
            f"{desc_excel}<br><br>💡 <b>Técnica:</b> {texto_base}"
            if (desc_excel and desc_excel != "-")
            else texto_base
        )

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

        with st.container():
            if urls_validas:
                cols_img = st.columns(len(urls_validas))
                for index, url in enumerate(urls_validas):
                    with cols_img[index]:
                        st.image(
                            url,
                            caption=f"Paso {index + 1}",
                            use_container_width=True,
                            key=f"img_{paso_actual}_{index}",
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

        st.markdown("---")

        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if paso_actual > 0:
                if st.button(
                    "⬅️ Anterior",
                    key=f"btn_prev_{paso_actual}",
                    use_container_width=True,
                ):
                    st.session_state.paso_actual -= 1
                    st.rerun()

        with col_nav2:
            if st.button(
                "✅ ➔ Siguiente ejercicio",
                key=f"btn_next_{paso_actual}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.paso_actual += 1
                st.rerun()

        # BARRA DE PROGRESO
        porcentaje_progreso = int(((paso_actual + 1) / total_ejercicios) * 100)
        st.markdown(
            f"""
            <div class="progress-card">
                <div class="progress-header">
                    <span class="progress-label">Ejercicio {paso_actual + 1} de {total_ejercicios}</span>
                    <span class="progress-percentage">{porcentaje_progreso}% completado</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(porcentaje_progreso / 100)

    else:
        # -----------------------------------------------------------------------------
        # BLOQUE: PANTALLA FINAL DE FUERZA Y LANZADOR DE ESTIRAMIENTOS
        # -----------------------------------------------------------------------------

        # Lanza la animación de globos en la pantalla
        st.balloons()

        # Título de felicitación
        st.markdown(
            """
            <div style="text-align: center; padding: 15px 0;">
                <h2 style="color: #16a34a; font-size: 2.1rem; font-weight: 800;">🎉 ¡BLOQUE DE FUERZA COMPLETADO! 🎉</h2>
                <h3 style="color: #1e293b; font-size: 1.3rem;">¡Excelente esfuerzo en tu entrenamiento!</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tarjeta informativa sobre los beneficios de estirar
        st.markdown(
            """
            <div style="background-color: #f0fdf4; border-left: 5px solid #22c55e; border-radius: 10px; padding: 16px; margin: 15px 0;">
                <h4 style="color: #15803d; margin-top: 0;">🧘‍♂️ ¿Por qué es vital realizar los estiramientos finales?</h4>
                <p style="color: #334155; font-size: 0.95rem; line-height: 1.6;">
                    • <b>Normalización del tono muscular:</b> Reduce la hipertonía y contracturas post-esfuerzo.<br>
                    • <b>Recuperación hemodinámica:</b> Facilita el retorno venoso y acelera la eliminación de metabólicos.<br>
                    • <b>Prevención de rigidez articular:</b> Preserva el rango de movimiento articular saludable.<br>
                    • <b>Activación parasimpática:</b> Ayuda al sistema nervioso a pasar de un estado de estrés a la recuperación.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Botón para activar la sesión de 10 minutos de estiramientos
        if st.button(
            "🧘 EMPEZAR ESTIRAMIENTOS (10 MIN)",
            type="primary",
            use_container_width=True,
        ):
            # Genera 4 estiramientos aleatorios de la base de datos
            st.session_state.df_estiramientos = obtener_rutina_estiramientos(
                df_ejercicios, cantidad=4
            )
            st.session_state.modo_estiramientos = True
            st.session_state.modo_entrenamiento = False
            st.session_state.inicio_estiramientos = datetime.now()
            st.rerun()

        st.markdown("---")

        # Opción alternativa para salir directamente sin estirar
        if st.button("🔄 Finalizar y volver al inicio", use_container_width=True):
            st.session_state.paso_actual = 0
            st.session_state.df_rutina = None
            st.session_state.modo_entrenamiento = False
            st.session_state.inicio_entrenamiento = None
            st.session_state.modo_estiramientos = False
            st.rerun()

# -----------------------------------------------------------------------------
# 6. MÓDULO EXCLUSIVO DE ESTIRAMIENTOS (10 MINUTOS)
# -----------------------------------------------------------------------------
elif st.session_state.modo_estiramientos:
    st.markdown(
        "<h2 style='text-align: center; color: #16a34a;'>🧘 BLOQUE DE ESTIRAMIENTOS FINALES</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #64748b;'>Mantén cada posición de forma suave, respirando profundo y sin dolor punzante.</p>",
        unsafe_allow_html=True,
    )

    df_est = st.session_state.df_estiramientos
    for idx, (_, row) in enumerate(df_est.iterrows()):
        st.markdown(
            f"### {idx + 1}. {row.get('Nombre', 'Estiramiento Guiado')}"
        )
        st.write(
            f"⏱️ **Tiempo sugerido:** 2 series × 30-45 segundos por zona."
        )

        desc = str(
            row.get("Descripcion", "Realiza una extensión/flexión suave.")
        )
        st.caption(desc)

        img_col = [
            str(row[c])
            for c in ["Imagen_1", "Imagen_2"]
            if c in row
            and pd.notna(row[c])
            and str(row[c]).strip() not in ["-", ""]
        ]
        if img_col:
            st.image(
                img_col[0],
                use_container_width=True,
                key=f"img_est_{idx}",
            )

        st.markdown("---")

    if st.button(
        "🏆 Finalizar sesión completa", type="primary", use_container_width=True
    ):
        st.session_state.paso_actual = 0
        st.session_state.df_rutina = None
        st.session_state.modo_entrenamiento = False
        st.session_state.inicio_entrenamiento = None
        st.session_state.modo_estiramientos = False
        st.success("¡Excelente trabajo! Sesión finalizada con éxito.")
        st.rerun()
