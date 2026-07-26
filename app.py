import time
import urllib.parse
from datetime import datetime, timedelta
import unicodedata
import pandas as pd
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="RUTINAS W360",
    page_icon="🏋️‍♂️",
    layout="wide",
)

# -----------------------------------------------------------------------------
# CSS PERSONALIZADO (ESTILO W360: BORDES REDONDEADOS, TARJETAS Y CENTRADO)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Ocultar elementos de Streamlit y GitHub */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Tipografía para el título principal */
    .titulo-w360 {
        font-size: 1.6rem !important;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #1E293B;
        margin-bottom: 0.5rem;
    }

    /* Botón de Generar Rutina (Súper Redondeado) */
    div.stButton > button[key="btn_generar"] {
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: 700 !important;
        margin: 0 auto;
        display: block;
    }

    /* Botones de acción rectangulares con bordes suavemente redondeados */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* Tarjeta de Prescripción atractiva */
    .prescripcion-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
        border: 1px solid #cbd5e1;
    }
    .prescripcion-series {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
    }
    .prescripcion-descanso {
        font-size: 0.95rem;
        color: #475569;
        margin-top: 0.3rem;
    }

    /* Centrado del Temporizador */
    .temp-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin: 1rem 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# GESTIÓN DE ACCESO Y AUTENTICACIÓN
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
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            "<h2 style='text-align: center;'>🔒 Acceso W360</h2>",
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
# LÓGICA DE DATOS
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
    if not isinstance(texto, str):
        return ""
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
        if "patron" in col.lower() or "patrón" in col.lower():
            df[col] = df[col].fillna("-")
    if "Material" in df.columns:
        df["Material"] = df["Material"].fillna("-")
    return df


try:
    df_ejercicios = cargar_ejercicios()
except Exception as e:
    st.error(f"Error al cargar 'ejercicios.xlsx': {e}")
    st.stop()


def obtener_prescripcion_y_tiempo(nivel, grupo_muscular):
    grupo = normalizar_texto(str(grupo_muscular))

    if "gluteo" in grupo:
        descanso_seg = 30
    elif "abdom" in grupo:
        descanso_seg = 15
    else:
        descanso_seg = 60 if nivel == "Básico" else 45

    if nivel == "Básico":
        num_series = 3
        reps_texto = "10-12 reps" if "abdom" not in grupo else "30 seg trabajo"
        tiempo_ejecucion_serie = 35
    elif nivel == "Intermedio":
        num_series = 4
        reps_texto = "12-15 reps" if "abdom" not in grupo else "45 seg trabajo"
        tiempo_ejecucion_serie = 40
    else:
        num_series = 4
        reps_texto = "15-20 reps" if "abdom" not in grupo else "60 seg trabajo"
        tiempo_ejecucion_serie = 45

    tiempo_ejercicio_seg = (num_series * tiempo_ejecucion_serie) + (
        (num_series - 1) * descanso_seg
    ) + 30
    series_reps = f"{num_series} series × {reps_texto}"

    return series_reps, descanso_seg, tiempo_ejercicio_seg


def generar_link_google_calendar(
    titulo, descripcion, duracion_minutos=60, fecha_inicio=None
):
    if fecha_inicio is None:
        manana = datetime.now() + timedelta(days=1)
        fecha_inicio = manana.replace(hour=10, minute=0, second=0, microsecond=0)

    fecha_fin = fecha_inicio + timedelta(minutes=duracion_minutos)
    fmt = "%Y%m%dT%H%M%SZ"
    dates_str = f"{fecha_inicio.strftime(fmt)}/{fecha_fin.strftime(fmt)}"

    params = {
        "action": "TEMPLATE",
        "text": titulo,
        "details": descripcion,
        "dates": dates_str,
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"


# Estado de Sesión
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
# CONFIGURADOR DE RUTINA
# -----------------------------------------------------------------------------

if not st.session_state.modo_entrenamiento:
    st.markdown("<div class='titulo-w360'>RUTINAS W360</div>", unsafe_allow_html=True)

    with st.expander(
        "⚙️ Configurar Parámetros", expanded=(st.session_state.df_rutina is None)
    ):
        col_n1, col_n2 = st.columns([1, 2])

        with col_n1:
            niveles_disponibles = df_ejercicios["Nivel"].dropna().unique().tolist()
            nivel_seleccionado = st.selectbox(
                "Nivel de Progresión", niveles_disponibles
            )

        with col_n2:
            st.write("**Ejercicios por grupo muscular:**")
            c_p, c_c, c_g, c_a = st.columns(4)
            num_piernas = c_p.number_input("Piernas", 0, 10, value=2)
            num_pecho = c_c.number_input("Pecho", 0, 10, value=2)
            num_gluteos = c_g.number_input("Glúteos", 0, 10, value=2)
            num_abs = c_a.number_input("Abs", 0, 10, value=4)

        solicitudes = {
            "Piernas": num_piernas,
            "Pecho": num_pecho,
            "Gluteos": num_gluteos,
            "Abdominales": num_abs,
        }

        TIEMPO_MAXIMO_TOTAL_MIN = 60
        TIEMPO_ESTIRAMIENTOS_MIN = 10
        TIEMPO_MAXIMO_RUTINA_MIN = TIEMPO_MAXIMO_TOTAL_MIN - TIEMPO_ESTIRAMIENTOS_MIN

        _, col_btn_centrado, _ = st.columns([1, 2, 1])
        with col_btn_centrado:
            if st.button(
                "⚡ Generar Rutina Personalizada",
                key="btn_generar",
                type="primary",
                use_container_width=True,
            ):
                rutina_lista = []
                df_temp = df_ejercicios.copy()
                df_temp["_grupo_norm"] = df_temp["Grupo Muscular"].apply(normalizar_texto)

                for grupo, cantidad in solicitudes.items():
                    if cantidad > 0:
                        grupo_busqueda = normalizar_texto(grupo)
                        df_grupo = df_temp[
                            (df_temp["_grupo_norm"].str.contains(grupo_busqueda, na=False))
                            & (df_temp["Nivel"] == nivel_seleccionado)
                        ]
                        if not df_grupo.empty:
                            muestra = df_grupo.sample(n=min(cantidad, len(df_grupo)))
                            rutina_lista.append(muestra)

                if rutina_lista:
                    df_rutina = pd.concat(rutina_lista).reset_index(drop=True)
                    tiempo_total_seg = 0
                    indices_a_conservar = []

                    for idx, row in df_rutina.iterrows():
                        _, _, tiempo_ej_seg = obtener_prescripcion_y_tiempo(
                            nivel_seleccionado, row.get("Grupo Muscular", "")
                        )
                        if (
                            tiempo_total_seg + tiempo_ej_seg
                        ) / 60 <= TIEMPO_MAXIMO_RUTINA_MIN:
                            tiempo_total_seg += tiempo_ej_seg
                            indices_a_conservar.append(idx)

                    st.session_state.df_rutina = df_rutina.loc[indices_a_conservar].reset_index(drop=True)
                    st.session_state.tiempo_estimado = round(tiempo_total_seg / 60)
                    st.session_state.paso_actual = 0
                    st.session_state.nivel_seleccionado = nivel_seleccionado
                    st.session_state.modo_entrenamiento = False
                    st.rerun()

    st.markdown("---")

    # -------------------------------------------------------------------------
    # FASE 1: RESUMEN DE TIEMPOS Y ACCIONES HORIZONTALES
    # -------------------------------------------------------------------------
    if st.session_state.df_rutina is not None:
        df_rutina = st.session_state.df_rutina
        tiempo_ejercicios = st.session_state.tiempo_estimado
        tiempo_total_sesion = tiempo_ejercicios + TIEMPO_ESTIRAMIENTOS_MIN

        st.success("🔥 **Rutina generada con éxito**")

        # Tiempos desglosados en Horizontal
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("🏋️ Fuerza / Abs", f"{tiempo_ejercicios} min")
        col_t2.metric("🧘 Estiramientos", f"{TIEMPO_ESTIRAMIENTOS_MIN} min")
        col_t3.metric("⏱️ Tiempo Total", f"{tiempo_total_sesion} min")

        st.markdown("<br>", unsafe_allow_html=True)

        # Evento de Calendar
        nombres_ejercicios = ", ".join(df_rutina["Nombre"].tolist())
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

        # Botones de Acción Horizontal Rectangulares
        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            st.link_button(
                "📅 Agendar en Google Calendar",
                link_calendar,
                use_container_width=True,
            )
        with col_act2:
            if st.button(
                "🚀 Comenzar Entrenamiento Ahora",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.modo_entrenamiento = True
                st.session_state.paso_actual = 0
                st.rerun()

# -----------------------------------------------------------------------------
# FASE 2: MODO ENTRENAMIENTO GUIADO (RUTINAS W360)
# -----------------------------------------------------------------------------

elif st.session_state.df_rutina is not None and st.session_state.modo_entrenamiento:
    st.markdown("<div class='titulo-w360'>RUTINAS W360</div>", unsafe_allow_html=True)

    df_rutina = st.session_state.df_rutina
    total_ejercicios = len(df_rutina)
    total_pasos = total_ejercicios + 1
    paso_actual = st.session_state.paso_actual

    progreso_porcentaje = min(float(paso_actual / total_pasos), 1.0)
    st.progress(progreso_porcentaje)

    if paso_actual < total_ejercicios:
        st.caption(f"Ejercicio **{paso_actual + 1} de {total_ejercicios}**")
    elif paso_actual == total_ejercicios:
        st.caption("Bloque Final de Estiramientos")
    else:
        st.caption("¡Completado!")

    st.markdown("---")

    if paso_actual < total_ejercicios:
        row = df_rutina.iloc[paso_actual]
        nivel_sel = st.session_state.nivel_seleccionado

        # Nombre del ejercicio (SIN nomenclaturas ni IDs al final)
        st.subheader(f"{row['Nombre']}")

        series_reps, descanso_seg, _ = obtener_prescripcion_y_tiempo(
            nivel_sel, row.get("Grupo Muscular", "")
        )

        # Prescripción Visual Atractiva (Arriba Series, Abajo Tiempo)
        st.markdown(
            f"""
            <div class="prescripcion-card">
                <div class="prescripcion-series">{series_reps}</div>
                <div class="prescripcion-descanso">⏱️ Descanso: {descanso_seg} segundos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Información complementaria en 3 columnas
        c_d1, c_d2, c_d3 = st.columns(3)
        c_d1.write(f"**Patrón:** {row.get('Patron Movimiento', row.get('Patrón', '-'))}")
        c_d2.write(f"**Material:** {row.get('Material', '-')}")
        c_d3.write(f"**Grupo:** {row.get('Grupo Muscular', '-')}")

        columnas_fotos = ["Imagen_1", "Imagen_2", "Imagen_3", "Imagen_4"]
        urls_validas = [
            row[col]
            for col in columnas_fotos
            if col in row and pd.notna(row[col]) and str(row[col]).strip()
        ]

        if urls_validas:
            cols_img = st.columns(len(urls_validas))
            for index, url in enumerate(urls_validas):
                with cols_img[index]:
                    st.image(url, caption=f"Paso {index + 1}", use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # TEMPORIZADOR CENTRADO Y SÍNTESIS DE ALARMA WEB AUDIO API
        # ---------------------------------------------------------------------
        st.markdown("<div class='temp-container'>", unsafe_allow_html=True)
        col_temp_left, col_temp_center, col_temp_right = st.columns([1, 2, 1])

        with col_temp_center:
            if st.button("⏱️ TIEMPO", use_container_width=True):
                ph = st.empty()
                for t in range(descanso_seg, -1, -1):
                    ph.markdown(
                        f"<h1 style='text-align: center; color: #E11D48; font-size: 3rem;'>{t} s</h1>",
                        unsafe_allow_html=True,
                    )
                    time.sleep(1)

                ph.markdown(
                    "<h3 style='text-align: center; color: #16A34A;'>🔔 ¡Tiempo finalizado!</h3>",
                    unsafe_allow_html=True,
                )

                # Web Audio API: Sonido Beep Nativo en Navegador (Compatible iOS/Android/PC)
                st.components.v1.html(
                    """
                    <script>
                    function playBeep() {
                        try {
                            var ctx = new (window.AudioContext || window.webkitAudioContext)();
                            var osc = ctx.createOscillator();
                            var gain = ctx.createGain();
                            osc.type = 'sine';
                            osc.frequency.setValueAtTime(880, ctx.currentTime); // Tono de 880Hz (La)
                            gain.gain.setValueAtTime(1, ctx.currentTime);
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start();
                            osc.stop(ctx.currentTime + 0.8); // Duración de 0.8 segundos
                        } catch(e) {
                            console.log("Audio not supported or blocked");
                        }
                    }
                    playBeep();
                    </script>
                    """,
                    height=0,
                )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Botones de Navegación de Ejercicios
        col_nav1, col_nav2 = st.columns([1, 1])

        with col_nav1:
            if paso_actual > 0:
                if st.button("⬅️ Anterior", use_container_width=True):
                    st.session_state.paso_actual -= 1
                    st.rerun()

        with col_nav2:
            if st.button(
                "✅ Siguiente ejercicio ➔", type="primary", use_container_width=True
            ):
                st.session_state.paso_actual += 1
                st.rerun()

    elif paso_actual == total_ejercicios:
        st.subheader("🧘 Bloque de Enfriamiento y Estiramientos (10 min)")
        st.markdown(
            """
        * 🧘‍♂️ **Isquiotibiales y Cuádriceps:** 2 series de 30 seg por pierna.
        * 🧘‍♀️ **Pectorales:** 2 series de 30 seg contra pared.
        * 🧘‍♂️ **Glúteos:** 2 series de 30 seg por lado.
        * 🧘‍♀️ **Cobra / Lumbar:** 2 series de 30 seg suave.
        """
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

    else:
        st.balloons()
        st.success("🎉 ¡Entrenamiento completado con éxito!")
        st.markdown("---")
        if st.button("🔄 Volver al Menú", type="primary", use_container_width=True):
            st.session_state.paso_actual = 0
            st.session_state.modo_entrenamiento = False
            st.rerun()
