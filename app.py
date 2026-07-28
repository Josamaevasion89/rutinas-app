import textwrap
import unicodedata

import pandas as pd
import streamlit as st

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# =============================================================================
st.set_page_config(
    page_title="RUTINAS W360",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Ocultar elementos predeterminados de la interfaz de Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Títulos y cabeceras */
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

    /* Botón destacado Generar Rutina */
    div.stButton > button[key="btn_generar"] {
        width: 100% !important;
        padding: 10px 16px !important;
        font-size: 16px !important;
        border-radius: 20px !important;
        font-weight: 800 !important;
    }

    /* Tarjetas de Métricas */
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

    /* Tarjetas Destacadas */
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

    .exercise-details {
        text-align: center;
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 10px;
    }

    /* Barra de Progreso */
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

# =============================================================================
# 2. SISTEMA DE AUTENTICACIÓN
# =============================================================================
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

# =============================================================================
# 3. LÓGICA DE NEGOCIO, CARGA DE DATOS Y SELECCIÓN DE EJERCICIOS
# =============================================================================

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
        return 2 if (es_core_movilidad or not es_multiarticular_pesado) else 3
    elif duracion_total_min <= 30:
        return 2 if es_core_movilidad else 3
    else:  # 45 o 60 min
        return 3 if (es_core_movilidad or not es_multiarticular_pesado) else 4


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
    texto_total = " ".join(
        [normalizar_texto(str(v)) for v in row_dict.values()]
    )
    palabras = [
        "gluteo",
        "gluteos",
        "hip thrust",
        "puente de gluteo",
        "puente gluteo",
        "patada de gluteo",
        "patada gluteo",
        "abduccion",
        "frog pump",
        "clamshell",
        "kickback",
    ]
    return any(p in texto_total for p in palabras)


def es_ejercicio_abdominal_core(row_dict):
    texto_total = " ".join(
        [normalizar_texto(str(v)) for v in row_dict.values()]
    )
    palabras = [
        "core",
        "abdominal",
        "abdominales",
        "plancha",
        "crunch",
        "rueda abdominal",
        "sit up",
    ]
    return any(p in texto_total for p in palabras)


def seleccionar_y_estructurar_rutina(df_candidatos, df_base, cantidad_deseada):
    todos = df_base.to_dict("records")
    candidatos = df_candidatos.to_dict("records")

    # 1. Glúteo
    gluteos = [r for r in candidatos if es_ejercicio_gluteo(r)] or [
        r for r in todos if es_ejercicio_gluteo(r)
    ]
    ej_gluteo = (
        pd.DataFrame(gluteos).sample(n=1).to_dict("records")[0]
        if gluteos
        else candidatos[0]
    )

    # 2. Core al final
    cores = [
        r
        for r in candidatos
        if es_ejercicio_abdominal_core(r) and r != ej_gluteo
    ] or [
        r
        for r in todos
        if es_ejercicio_abdominal_core(r) and r != ej_gluteo
    ]
    cant_core = 1 if cantidad_deseada <= 4 else 2
    ejercicios_core = (
        pd.DataFrame(cores)
        .sample(n=min(cant_core, len(cores)))
        .to_dict("records")
        if cores
        else []
    )

    # 3. Fuerza Intermedia
    usados = [ej_gluteo] + ejercicios_core
    cuantos_intermedios = max(0, cantidad_deseada - len(usados))
    resto = [
        r
        for r in candidatos
        if r not in usados
        and not es_ejercicio_abdominal_core(r)
        and not es_ejercicio_gluteo(r)
    ]

    intermedios = (
        pd.DataFrame(resto)
        .sample(n=min(cuantos_intermedios, len(resto)))
        .to_dict("records")
        if resto
        else []
    )

    # Alternancia de grupos musculares
    intermedios_ordenados = []
    while intermedios:
        if not intermedios_ordenados:
            intermedios_ordenados.append(intermedios.pop(0))
            continue
        ult_grupo = normalizar_texto(
            str(intermedios_ordenados[-1].get("Grupo Muscular", ""))
        )
        idx_distinto = next(
            (
                i
                for i, item in enumerate(intermedios)
                if normalizar_texto(str(item.get("Grupo Muscular", "")))
                != ult_grupo
            ),
            0,
        )
        intermedios_ordenados.append(intermedios.pop(idx_distinto))

    rutina_final = [ej_gluteo] + intermedios_ordenados + ejercicios_core
    return pd.DataFrame(rutina_final)


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

# =============================================================================
# 4. CONFIGURADOR Y VISTA PRINCIPAL
# =============================================================================

def render_configurador(df_ejercicios):
    OPCION_BLANCO = "--- Sin filtro (Cualquiera) ---"

    with st.expander(
        "⚙️ Configurar Parámetros", expanded=(st.session_state.df_rutina is None)
    ):
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            niveles_base = ["Básico", "Intermedio", "Avanzado"]
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
            "<p style='text-align: center; font-weight: 900; color: #0f172a; font-size: 1.1rem;'>⏱️ TIEMPO DE DURACIÓN DEL ENTRENAMIENTO</p>",
            unsafe_allow_html=True,
        )

        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        opciones_tiempo = ["20 min", "30 min", "45 min", "60 min"]
        cols = [col_t1, col_t2, col_t3, col_t4]

        for idx, tiempo_opt in enumerate(opciones_tiempo):
            with cols[idx]:
                es_activo = st.session_state.duracion_elegida == tiempo_opt

                if es_activo:
                    # Estilo con fondo verde completo, borde destacado y sombra luminosa
                    st.markdown(
                        f"""
                        <style>
                        div.stButton > button[key="btn_time_{tiempo_opt}"] {{
                            background-color: #22c55e !important;
                            color: #ffffff !important;
                            border: 3px solid #15803d !important;
                            font-weight: 900 !important;
                            box-shadow: 0 0 12px rgba(34, 197, 94, 0.6) !important;
                        }}
                        div.stButton > button[key="btn_time_{tiempo_opt}"]:hover {{
                            background-color: #16a34a !important;
                            color: #ffffff !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    # Estilo por defecto cuando no está activo
                    st.markdown(
                        f"""
                        <style>
                        div.stButton > button[key="btn_time_{tiempo_opt}"] {{
                            background-color: #0f172a !important;
                            color: #f97316 !important;
                            border: 1px solid #334155 !important;
                            font-weight: 800 !important;
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

        duracion_minutos_total = int(
            str(st.session_state.duracion_elegida).split()[0]
        )
        duracion_fuerza_min = max(5, duracion_minutos_total - 10)

        if st.button(
            "⚡ Generar rutina personalizada",
            key="btn_generar",
            type="primary",
            use_container_width=True,
        ):
            df_filtrado = df_ejercicios.copy()

            if "Nivel" in df_filtrado.columns:
                nivel_norm = normalizar_texto(nivel_seleccionado)
                df_filtrado = df_filtrado[
                    df_filtrado["Nivel"].apply(
                        lambda x: nivel_norm in normalizar_texto(str(x))
                    )
                ]

            if tren_seleccionado != OPCION_BLANCO:
                tren_norm = normalizar_texto(tren_seleccionado)
                cols_cat = [
                    c
                    for c in df_filtrado.columns
                    if any(
                        k in str(c).lower()
                        for k in ["tren", "categoria", "grupo", "zona"]
                    )
                ]
                if cols_cat:
                    df_filtrado = df_filtrado[
                        df_filtrado[cols_cat[0]].apply(
                            lambda x: tren_norm in normalizar_texto(str(x))
                        )
                    ]

            if objetivo_seleccionado != OPCION_BLANCO:
                obj_norm = normalizar_texto(objetivo_seleccionado)
                cols_obj = [
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
                if cols_obj:
                    df_filtrado = df_filtrado[
                        df_filtrado[cols_obj[0]].apply(
                            lambda x: obj_norm in normalizar_texto(str(x))
                        )
                    ]

            if df_filtrado.empty:
                st.warning(
                    "⚠️ Sin coincidencias exactas. Aplicando filtros generales."
                )
                df_filtrado = df_ejercicios.copy()

            ejercicios_objetivo = max(2, int(round(duracion_fuerza_min / 4.5)))
            st.session_state.df_rutina = seleccionar_y_estructurar_rutina(
                df_filtrado, df_ejercicios, ejercicios_objetivo
            )
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
        tiempo_fuerza = st.session_state.tiempo_estimado
        st.markdown(
            f"""
            <div class="sub-metric-card"><b>Fuerza:</b> {tiempo_fuerza} min | <b>Estiramientos:</b> 10 min</div>
            <div class="highlight-card"><div class="highlight-card-desc">Duración Total: {tiempo_fuerza + 10} min</div></div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "🚀 Comenzar Ahora", type="primary", use_container_width=True
        ):
            st.session_state.modo_entrenamiento = True
            st.session_state.paso_actual = 0
            st.rerun()
# =============================================================================
# 5. MODO ENTRENAMIENTO GUIADO Y BLOQUE FINAL DE ESTIRAMIENTOS
# =============================================================================

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
            textwrap.dedent(f"""
            <div class="description-card">
                <b>📌 Ejecución paso a paso:</b><br>{texto_descripcion}
            </div>
            """),
            unsafe_allow_html=True,
        )

        # Imágenes
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
            textwrap.dedent(f"""
            <div class="highlight-card">
                <div class="highlight-card-subtitle">Prescripción de Trabajo</div>
                <div class="highlight-card-desc">{series_reps}</div>
            </div>
            """),
            unsafe_allow_html=True,
        )

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

        porcentaje_progreso = int(((paso_actual + 1) / total_ejercicios) * 100)
        st.markdown(
            textwrap.dedent(f"""
            <div class="progress-card">
                <div class="progress-header">
                    <span class="progress-label">PROGRESO DEL ENTRENAMIENTO</span>
                    <span class="progress-percentage">{porcentaje_progreso}%</span>
                </div>
            </div>
            """),
            unsafe_allow_html=True,
        )
        st.progress((paso_actual + 1) / total_ejercicios)

    else:
        # PANTALLA FIN DE ENTRENAMIENTO Y BLOQUE COMPLETO DE ESTIRAMIENTOS
        st.balloons()
        st.markdown(
            textwrap.dedent("""
            <div style="text-align: center; padding: 20px; background-color: #f0fdf4; border-radius: 16px; border: 2px solid #22c55e; margin: 10px 0 20px 0;">
                <h2 style="color: #15803d; margin-bottom: 5px;">🎉 ¡Parte Principal Completada!</h2>
                <p style="color: #166534; font-size: 1.1rem; font-weight: 700;">Has terminado la fase de fuerza. Tómate 10 minutos para la vuelta a la calma.</p>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.markdown(
            textwrap.dedent("""
            <div style="background-color: #0f172a; border-radius: 14px; padding: 16px; border: 2px solid #38bdf8; margin-bottom: 20px;">
                <h3 style="color: #38bdf8; text-align: center; margin-bottom: 5px; font-weight: 800;">🧘 BLOQUE DE ESTIRAMIENTOS Y VUELTA A LA CALMA</h3>
                <p style="color: #94a3b8; text-align: center; font-size: 0.9rem; margin-bottom: 0;">Sostén cada postura sin rebotar, manteniendo una respiración diafragmática profunda (4s inhalar, 6s exhalar).</p>
            </div>
            """),
            unsafe_allow_html=True,
        )

        with st.expander(
            "🦵 1. Cadena Inferior (Isquios, Isquiotibiales y Cadera)", expanded=True
        ):
            st.markdown(
                textwrap.dedent("""
                * **Estiramiento de Isquiotibiales (De pie o sentado):**
                    * *Instrucciones:* Con una pierna adelantada y el talón apoyado, inclina la cadera hacia adelante manteniendo la espalda recta hasta sentir tensión suave en la parte posterior del muslo.
                    * *Dosis:* **2 series × 30-40 segundos** por pierna.
                * **Flexor de Cadera / Psoas (En zancada baja):**
                    * *Instrucciones:* Apoya una rodilla en el suelo e impulsa suavemente la cadera hacia adelante manteniendo el tronco vertical.
                    * *Dosis:* **2 series × 30 segundos** por lado.
                """),
                unsafe_allow_html=True,
            )

        with st.expander("🍑 2. Glúteo y Piramidal", expanded=True):
            st.markdown(
                textwrap.dedent("""
                * **Figura 4 o Glúteo Supino (Tumbado):**
                    * *Instrucciones:* Tumbado boca arriba, cruza el tobillo sobre la rodilla contraria y abraza el muslo por detrás tirando hacia el pecho.
                    * *Dosis:* **2 series × 45 segundos** por lado.
                * **Postura de la Paloma (Yoga):**
                    * *Instrucciones:* Apoya una pierna flexionada por delante en el suelo y extiende la otra hacia atrás. Inclina el torso suavemente hacia adelante.
                    * *Dosis:* **1-2 series × 40 segundos** por lado.
                """),
                unsafe_allow_html=True,
            )

        with st.expander("🧘‍♂️ 3. Lumbar, Espalda y Columna", expanded=True):
            st.markdown(
                textwrap.dedent("""
                * **Gato-Vaca (Movilidad Espinal):**
                    * *Instrucciones:* En cuadrupedia, arquea la columna hacia arriba mirando hacia el ombligo y luego arquea suavemente hacia abajo elevando la mirada.
                    * *Dosis:* **10 repeticiones lentas y fluidas**.
                * **Postura del Niño (Child's Pose):**
                    * *Instrucciones:* Arrodillado, lleva los glúteos hacia los talones y extiende los brazos hacia adelante pegando la frente al suelo.
                    * *Dosis:* **1 minuto de respiración profunda continua**.
                """),
                unsafe_allow_html=True,
            )

        with st.expander(
            "💪 4. Tren Superior (Pectoral y Hombros)", expanded=False
        ):
            st.markdown(
                textwrap.dedent("""
                * **Estiramiento Pectoral en Marco de Puerta / Pared:**
                    * *Instrucciones:* Apoya el antebrazo en la pared o marco a 90° y da un paso adelante girando levemente el torso.
                    * *Dosis:* **2 series × 30 segundos** por lado.
                * **Cruzado de Hombro Posterior:**
                    * *Instrucciones:* Pasa un brazo extendido por delante del pecho y usa el otro brazo para presionarlo suavemente hacia el cuerpo.
                    * *Dosis:* **2 series × 30 segundos** por lado.
                """),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "🔄 Volver al Inicio / Nueva Rutina",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.modo_entrenamiento = False
            st.session_state.paso_actual = 0
            st.session_state.df_rutina = None
            st.rerun()
