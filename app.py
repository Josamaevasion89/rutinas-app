import urllib.parse
from datetime import datetime, timedelta
import unicodedata
import pandas as pd
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="RUTINAS W360",
    page_icon="🏋️‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# CSS PERSONALIZADO
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Ocultar UI de Streamlit y GitHub */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Título centrado */
    .header-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #1E293B;
        margin-bottom: 15px;
    }

    /* Nombre del Ejercicio Centrado */
    .exercise-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* Botón Generar Rutina compacto */
    div.stButton > button[key="btn_generar"] {
        width: 100% !important;
        padding: 8px 16px !important;
        font-size: 15px !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
    }

    /* Tarjetas de Métricas Secundarias Centradas */
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

    /* Botones generales */
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
# 3. CARGA DE DATOS Y LÓGICA DE NEGOCIO
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
    if texto is None or not isinstance(texto, str):
        texto = str(texto) if texto is not None else ""
    texto = texto.lower().strip()
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


def obtener_prescripcion(nivel, categoria):
    cat = normalizar_texto(categoria)

    if str(nivel) == "Básico":
        num_series = 3
        reps_texto = "10-12 reps" if "core" not in cat else "30 seg trabajo"
    elif str(nivel) == "Intermedio":
        num_series = 4
        reps_texto = "12-15 reps" if "core" not in cat else "45 seg trabajo"
    else:
        num_series = 4
        reps_texto = "15-20 reps" if "core" not in cat else "60 seg trabajo"

    return f"{num_series} series × {reps_texto}"


def generar_link_google_calendar(
    titulo, descripcion, duracion_minutos=60, fecha_inicio=None
):
    if fecha_inicio is None:
        manana = datetime.now() + timedelta(days=1)
        fecha_inicio = manana.replace(hour=10, minute=0, second=0, microsecond=0)

    fecha_fin = fecha_inicio + timedelta(minutes=int(duracion_minutos))
    fmt = "%Y%m%dT%H%M%SZ"
    dates_str = f"{fecha_inicio.strftime(fmt)}/{fecha_fin.strftime(fmt)}"

    params = {
        "action": "TEMPLATE",
        "text": str(titulo),
        "details": str(descripcion),
        "dates": dates_str,
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"


# Componente HTML del Temporizador (Fondo claro con alto contraste)
def renderizar_temporizador_15s(paso_id):
    st.components.v1.html(
        """
        <div id="timer-box" onclick="startTimer()" style="
            background-color: #f8fafc;
            border-radius: 12px;
            padding: 14px;
            text-align: center;
            cursor: pointer;
            user-select: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin: 10px 0;
            border: 2px solid #2563eb;
            transition: all 0.3s ease;
        ">
            <div id="timer-label" style="
                color: #475569;
                font-size: 0.85rem;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-bottom: 4px;
                font-family: system-ui, -apple-system, sans-serif;
            ">
                ⏱️ TOCA PARA INICIAR DESCANSO
            </div>
            <div id="timer-display" style="
                color: #16a34a;
                font-size: 2.8rem;
                font-weight: 900;
                font-family: monospace, monospace;
                line-height: 1;
            ">
                15s
            </div>
        </div>

        <script>
            let interval = null;
            let count = 15;
            let running = false;

            function startTimer() {
                if (running) return;
                
                running = true;
                count = 15;
                
                const display = document.getElementById("timer-display");
                const label = document.getElementById("timer-label");
                const box = document.getElementById("timer-box");

                label.innerText = "PRÓXIMA REPETICIÓN EN...";
                display.innerText = count + "s";
                display.style.color = "#16a34a";
                box.style.borderColor = "#2563eb";

                interval = setInterval(() => {
                    count--;
                    display.innerText = count + "s";

                    // Al llegar a 10s o menos, cambia a rojo
                    if (count <= 10) {
                        display.style.color = "#dc2626";
                        box.style.borderColor = "#dc2626";
                    } else {
                        display.style.color = "#16a34a";
                        box.style.borderColor = "#2563eb";
                    }

                    // Al terminar, restablece el estado inicial
                    if (count <= 0) {
                        clearInterval(interval);
                        running = false;
                        
                        label.innerText = "⏱️ TOCA PARA INICIAR DESCANSO";
                        display.innerText = "15s";
                        display.style.color = "#16a34a";
                        box.style.borderColor = "#2563eb";
                    }
                }, 1000);
            }
        </script>
        """,
        height=110,
        key=f"timer_comp_{paso_id}",
    )


# Inicialización de variables de sesión
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

# -----------------------------------------------------------------------------
# 4. CABECERA PRINCIPAL Y CONFIGURADOR DE RUTINA
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
            niveles_disponibles = df_ejercicios["Nivel"].dropna().unique().tolist() if "Nivel" in df_ejercicios.columns else []
            if not niveles_disponibles:
                niveles_disponibles = ["Básico", "Intermedio", "Avanzado"]
            nivel_seleccionado = st.selectbox(
                "Nivel de Progresión", niveles_disponibles
            )

        with col_n2:
            opciones_tren = [OPCION_BLANCO, "Tren superior", "Tren inferior", "Core"]
            tren_seleccionado = st.selectbox("Estructura Corporal", opciones_tren)

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

        duraciones_opciones = ["20 min", "30 min", "45 min", "60 min"]
        duracion_seleccionada = st.select_slider(
            "⏱️ Tiempo de duración del entrenamiento",
            options=duraciones_opciones,
            value="30 min",
        )

        duracion_minutos_total = int(str(duracion_seleccionada).split()[0])
        TIEMPO_ESTIRAMIENTOS_MIN = 10
        duracion_fuerza_min = max(5, duracion_minutos_total - TIEMPO_ESTIRAMIENTOS_MIN)

        if st.button(
            "⚡ Generar rutina personalizada",
            key="btn_generar",
            type="primary",
            use_container_width=True,
        ):
            df_filtrado = df_ejercicios.copy()

            if "Nivel" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["Nivel"].astype(str) == str(nivel_seleccionado)]

            if tren_seleccionado != OPCION_BLANCO:
                tren_norm = normalizar_texto(tren_seleccionado)
                cols_categoria = [
                    c for c in df_filtrado.columns if any(k in str(c).lower() for k in ["tren", "categoria", "grupo", "zona"])
                ]
                if cols_categoria:
                    col_cat = cols_categoria[0]
                    df_filtrado = df_filtrado[
                        df_filtrado[col_cat].apply(lambda x: tren_norm in normalizar_texto(str(x)))
                    ]

            if objetivo_seleccionado != OPCION_BLANCO:
                obj_norm = normalizar_texto(objetivo_seleccionado)
                cols_objetivo = [
                    c for c in df_filtrado.columns if any(k in str(c).lower() for k in ["objetivo", "dolor", "enfoque", "patologia"])
                ]
                if cols_objetivo:
                    col_obj = cols_objetivo[0]
                    df_filtrado = df_filtrado[
                        df_filtrado[col_obj].apply(lambda x: obj_norm in normalizar_texto(str(x)))
                    ]

            if df_filtrado.empty:
                st.warning(
                    "⚠️ No se encontraron ejercicios exactamente con esos filtros. Se utilizarán ejercicios compatibles."
                )
                if "Nivel" in df_ejercicios.columns:
                    df_filtrado = df_ejercicios[df_ejercicios["Nivel"].astype(str) == str(nivel_seleccionado)]
                else:
                    df_filtrado = df_ejercicios.copy()

            ejercicios_objetivo = max(2, int(round(duracion_fuerza_min / 4)))
            cantidad_final = min(ejercicios_objetivo, len(df_filtrado))
            
            if cantidad_final > 0:
                df_rutina = df_filtrado.sample(n=cantidad_final).reset_index(drop=True)
            else:
                df_rutina = df_ejercicios.head(2).reset_index(drop=True)

            st.session_state.df_rutina = df_rutina
            st.session_state.tiempo_estimado = duracion_fuerza_min
            st.session_state.paso_actual = 0
            st.session_state.nivel_seleccionado = nivel_seleccionado
            st.session_state.modo_entrenamiento = False
            st.rerun()

    st.markdown("---")

    # -------------------------------------------------------------------------
    # RESUMEN DE TIEMPOS
    # -------------------------------------------------------------------------
    if st.session_state.df_rutina is not None and not st.session_state.df_rutina.empty:
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
                    <div class="sub-metric-title">🏋️ Fuerza</div>
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

        nombres_ejercicios = ", ".join(df_rutina["Nombre"].astype(str).tolist()) if "Nombre" in df_rutina.columns else "Ejercicios varios"
        titulo_evento = f"🏋️‍♂️ Rutina W360 ({tiempo_total_sesion} min) - {st.session_state.usuario_actual}"
        descripcion_evento = (
            f"Sesión de entrenamiento personal:\n\n"
            f"📋 Ejercicios: {nombres_ejercicios}\n\n"
            f"🔗 Acceso: https://rutinas-app.streamlit.app"
        )
        link_calendar = generar_link_google_calendar(
            titulo=titulo_evento,
            descripcion=descripcion_evento,
            duracion_minutos=tiempo_total_sesion,
        )

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            st.link_button(
                "📅 Google Calendar",
                link_calendar,
                use_container_width=True,
            )
        with col_act2:
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

elif st.session_state.df_rutina is not None and st.session_state.modo_entrenamiento:
    st.components.v1.html(
        """
        <script>
            window.parent.scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """,
        height=0,
    )

    df_rutina = st.session_state.df_rutina
    total_ejercicios = len(df_rutina)
    paso_actual = st.session_state.paso_actual

    if paso_actual < total_ejercicios:
        row = df_rutina.iloc[paso_actual]
        nivel_sel = st.session_state.nivel_seleccionado

        nombre_ej = str(row.get("Nombre", f"Ejercicio {paso_actual + 1}"))
        st.markdown(
            f'<div class="exercise-title">{nombre_ej}</div>',
            unsafe_allow_html=True,
        )

        series_reps = obtener_prescripcion(nivel_sel, row.get("Tren", ""))

        patron = str(row.get("Patron Movimiento", row.get("Patrón", "-")))
        material = str(row.get("Material", "-"))
        grupo_m = str(row.get("Grupo Muscular", row.get("Tren", "-")))

        st.markdown(
            f'<div class="exercise-details"><b>Patrón:</b> {patron} &nbsp;|&nbsp; <b>Material:</b> {material} &nbsp;|&nbsp; <b>Estructura:</b> {grupo_m}</div>',
            unsafe_allow_html=True,
        )

        # DESCRIPCIÓN TÉCNICA
        desc_excel = str(row.get("Descripcion", row.get("Instrucciones", "")))
        texto_base = "Mantén la postura alineada, el abdomen activo, realiza un movimiento controlado sin balanceos bruscos y realiza constantemente una respiración fluida y no la bloquees."
        
        if desc_excel and desc_excel != "-":
            texto_descripcion = f"{desc_excel}<br><br>💡 <b>Técnica:</b> {texto_base}"
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

        # IMÁGENES
        columnas_fotos = ["Imagen_1", "Imagen_2", "Imagen_3", "Imagen_4"]
        urls_validas = [
            str(row[col])
            for col in columnas_fotos
            if col in row and pd.notna(row[col]) and str(row[col]).strip() != "-" and str(row[col]).strip()
        ]

        if urls_validas:
            cols_img = st.columns(len(urls_validas))
            for index, url in enumerate(urls_validas):
                with cols_img[index]:
                    st.image(url, caption=f"Paso {index + 1}", use_container_width=True)

        # PRESCRIPCIÓN DE TRABAJO
        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-card-subtitle">Prescripción de Trabajo</div>
                <div class="highlight-card-desc">{series_reps}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # TEMPORIZADOR INTERACTIVO 15S (Clave única por paso para reinicio automático)
        renderizar_temporizador_15s(paso_actual)

        st.markdown("---")

        # NAVEGACIÓN
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

        # BARRA DE PROGRESIÓN
        progreso_porcentaje = float((paso_actual + 1) / total_ejercicios) if total_ejercicios > 0 else 1.0
        porcentaje_num = int(progreso_porcentaje * 100)

        if porcentaje_num <= 25:
            emoji_progreso = "🚀"
        elif porcentaje_num <= 50:
            emoji_progreso = "🔥"
        elif porcentaje_num <= 75:
            emoji_progreso = "⚡"
        else:
            emoji_progreso = "💪"

        texto_porcentaje = f'<div class="progress-percentage">{porcentaje_num}% completado</div>' if total_ejercicios > 6 else ""

        st.markdown(
            f"""
            <div class="progress-card">
                <div class="progress-header">
                    <div class="progress-label">{emoji_progreso} Ejercicio {paso_actual + 1} de {total_ejercicios}</div>
                    {texto_porcentaje}
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
                "🏁 Finalizar Entrenamiento", type="primary", use_container_width=True
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
        if st.button("🔄 Volver al Menú", type="primary", use_container_width=True):
            st.session_state.paso_actual = 0
            st.session_state.modo_entrenamiento = False
            st.rerun()
