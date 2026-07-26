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
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# CSS PERSONALIZADO (OPTIMIZADO PARA MÓVIL Y CENTRADO)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Ocultar UI de Streamlit y GitHub */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Título centrado con emojis */
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
        margin-bottom: 15px;
    }

    /* Botón Generar Rutina compacto */
    div.stButton > button[key="btn_generar"] {
        width: 100% !important;
        padding: 8px 16px !important;
        font-size: 15px !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
    }

    /* Tarjeta Destacada Estilo Estilo "Tiempo Total" para Prescripción y Descanso */
    .highlight-card {
        text-align: center;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        padding: 14px;
        margin: 15px 0;
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
    .highlight-card-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #38bdf8;
        margin-top: 2px;
    }
    .highlight-card-desc {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 4px;
    }

    /* Botón de Tiempo: Pequeño, Centrado y Fondo Verde */
    .timer-btn-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin: 15px 0;
    }
    div.stButton > button[key="btn_tiempo"] {
        background-color: #16a34a !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        padding: 8px 24px !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* Pantalla del Temporizador (Verde y Rojo) */
    .timer-green {
        font-size: 3.5rem;
        font-weight: 800;
        color: #16a34a;
        text-align: center;
        margin: 10px 0;
    }
    .timer-red {
        font-size: 3.5rem;
        font-weight: 800;
        color: #dc2626;
        text-align: center;
        margin: 10px 0;
    }

    /* Centrado de detalles del ejercicio */
    .exercise-details {
        text-align: center;
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 15px;
    }

    /* Botones generales rectangulares redondeados */
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

if not st.session_state.modo_entrenamiento:
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

        if st.button(
            "⚡ Generar rutina personalizada",
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
    # RESUMEN DE TIEMPOS CENTRADO Y BOTONES
    # -------------------------------------------------------------------------
    if st.session_state.df_rutina is not None:
        df_rutina = st.session_state.df_rutina
        tiempo_ejercicios = st.session_state.tiempo_estimado
        tiempo_total_sesion = tiempo_ejercicios + TIEMPO_ESTIRAMIENTOS_MIN

        st.markdown(
            "<h4 style='text-align: center; color: #16a34a;'>🔥 Rutina generada con éxito</h4>",
            unsafe_allow_html=True,
        )

        # Métricas (2 arriba, 1 destacado abajo)
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("🏋️ Fuerza", f"{tiempo_ejercicios} min")
        c_m2.metric("🧘 Abs / Estiramientos", f"{TIEMPO_ESTIRAMIENTOS_MIN} min")

        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-card-subtitle">Tiempo Total Sesión</div>
                <div class="highlight-card-value">{tiempo_total_sesion} min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Enlace para Calendar
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

        # Botones de Acción Horizontales Paralelos
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
# 5. MODO ENTRENAMIENTO GUIADO (CON AUTO-SCROLL AL INICIO)
# -----------------------------------------------------------------------------

elif st.session_state.df_rutina is not None and st.session_state.modo_entrenamiento:
    # AUTO-SCROLL JS: Fuerza a la pantalla del móvil a subir arriba al cambiar de paso
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
    total_pasos = total_ejercicios + 1
    paso_actual = st.session_state.paso_actual

    progreso_porcentaje = min(float(paso_actual / total_pasos), 1.0)
    st.progress(progreso_porcentaje)

    if paso_actual < total_ejercicios:
        st.markdown(
            f"<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>Ejercicio <b>{paso_actual + 1} de {total_ejercicios}</b></div>",
            unsafe_allow_html=True,
        )
    elif paso_actual == total_ejercicios:
        st.markdown(
            "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>Bloque Final de Estiramientos</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if paso_actual < total_ejercicios:
        row = df_rutina.iloc[paso_actual]
        nivel_sel = st.session_state.nivel_seleccionado

        # Nombre del ejercicio CENTRADO
        st.markdown(
            f'<div class="exercise-title">{row["Nombre"]}</div>',
            unsafe_allow_html=True,
        )

        series_reps, descanso_seg, _ = obtener_prescripcion_y_tiempo(
            nivel_sel, row.get("Grupo Muscular", "")
        )

        # Detalles del ejercicio CENTRADOS
        patron = row.get('Patron Movimiento', row.get('Patrón', '-'))
        material = row.get('Material', '-')
        grupo_m = row.get('Grupo Muscular', '-')
        
        st.markdown(
            f'<div class="exercise-details"><b>Patrón:</b> {patron} &nbsp;|&nbsp; <b>Material:</b> {material} &nbsp;|&nbsp; <b>Grupo:</b> {grupo_m}</div>',
            unsafe_allow_html=True,
        )

        # IMÁGENES DEL EJERCICIO
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

        # TARJETA DESTACADA "TIEMPO DE DESCANSO" (Estilo "Tiempo Total")
        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-card-subtitle">Prescripción & Descanso</div>
                <div class="highlight-card-desc">{series_reps}</div>
                <div class="highlight-card-value">⏱️ {descanso_seg} seg descanso</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # BOTÓN DE TIEMPO CENTRADO PEQUEÑO CON FONDO VERDE
        col_btn_center = st.columns([1, 2, 1])
        with col_btn_center[1]:
            timer_pressed = st.button("⏱️ TIEMPO", key="btn_tiempo", use_container_width=True)

        if timer_pressed:
            ph = st.empty()

            for t in range(descanso_seg, -1, -1):
                color_class = "timer-red" if t <= 10 else "timer-green"
                ph.markdown(
                    f'<div class="{color_class}">{t}s</div>',
                    unsafe_allow_html=True,
                )
                time.sleep(1)

            ph.markdown(
                "<h3 style='text-align: center; color: #16a34a;'>🔔 ¡Tiempo finalizado!</h3>",
                unsafe_allow_html=True,
            )

            # Sonido Web Audio API en móviles
            st.components.v1.html(
                """
                <script>
                function playBeep() {
                    try {
                        var ctx = new (window.AudioContext || window.webkitAudioContext)();
                        var osc = ctx.createOscillator();
                        var gain = ctx.createGain();
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(880, ctx.currentTime);
                        gain.gain.setValueAtTime(1, ctx.currentTime);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start();
                        osc.stop(ctx.currentTime + 0.8);
                    } catch(e) {
                        console.log("Audio not allowed");
                    }
                }
                playBeep();
                </script>
                """,
                height=0,
            )

        st.markdown("---")

        # Navegación entre ejercicios
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
