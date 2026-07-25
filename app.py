import time
import urllib.parse
from datetime import datetime, timedelta
import unicodedata
import pandas as pd
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Generador de Rutinas Pro & Readaptación",
    page_icon="🏋️‍♂️",
    layout="wide",
)

# -----------------------------------------------------------------------------
# OCULTAR GITHUB, FORK Y MENÚS DE STREAMLIT (ESTILO LIMPIO VIP)
# -----------------------------------------------------------------------------
ocultar_github_css = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    </style>
"""
st.markdown(ocultar_github_css, unsafe_allow_html=True)

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
        st.title("🔒 Acceso Clientes VIP")
        st.write("Ingresa tus credenciales de membresía para continuar:")

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
                st.error("Usuario o contraseña incorrectos / Membresía inactiva.")


if not st.session_state.autenticado:
    pantalla_login()
    st.stop()

# -----------------------------------------------------------------------------
# LÓGICA DE NEGOCIO Y DATOS
# -----------------------------------------------------------------------------

# Header superior
col_usr1, col_usr2 = st.columns([3, 1])
with col_usr1:
    st.caption(f"👤 **Usuario activo:** `{st.session_state.usuario_actual}`")
with col_usr2:
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
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
        reps = "10-12 reps" if "abdom" not in grupo else "30 seg trabajo"
        tiempo_ejecucion_serie = 35
    elif nivel == "Intermedio":
        num_series = 4
        reps = "12-15 reps" if "abdom" not in grupo else "45 seg trabajo"
        tiempo_ejecucion_serie = 40
    else:
        num_series = 4
        reps = "15-20 reps" if "abdom" not in grupo else "60 seg trabajo"
        tiempo_ejecucion_serie = 45

    tiempo_ejercicio_seg = (num_series * tiempo_ejecucion_serie) + (
        (num_series - 1) * descanso_seg
    ) + 30
    prescripcion_texto = (
        f"{num_series} series × {reps} | ⏱️ {descanso_seg} seg descanso"
    )

    return prescripcion_texto, tiempo_ejercicio_seg, num_series, descanso_seg


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
# CONFIGURADOR SUPERIOR
# -----------------------------------------------------------------------------

st.title("🏋️‍♂️ Generador Inteligente de Rutinas")

with st.expander("⚙️ Configurar Parámetros del Entrenamiento", expanded=(st.session_state.df_rutina is None)):
    col_n1, col_n2 = st.columns([1, 2])

    with col_n1:
        niveles_disponibles = df_ejercicios["Nivel"].dropna().unique().tolist()
        nivel_seleccionado = st.selectbox("Nivel de Progresión", niveles_disponibles)

    with col_n2:
        st.write("**Número de ejercicios por grupo muscular:**")
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

    if st.button("⚡ Generar Rutina Personalizada", type="primary", use_container_width=True):
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
                _, tiempo_ej_seg, _, _ = obtener_prescripcion_y_tiempo(
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

# -----------------------------------------------------------------------------
# FASE 1: RESUMEN DE RUTINA & GOOGLE CALENDAR
# -----------------------------------------------------------------------------

if st.session_state.df_rutina is not None and not st.session_state.modo_entrenamiento:
    df_rutina = st.session_state.df_rutina
    tiempo_ejercicios = st.session_state.tiempo_estimado
    tiempo_total_sesion = tiempo_ejercicios + TIEMPO_ESTIRAMIENTOS_MIN

    st.success(f"🔥 **¡Rutina Generada con Éxito!** ({len(df_rutina)} ejercicios seleccionados)")

    m1, m2, m3 = st.columns(3)
    m1.metric("🏋️ Fuerza / Abs", f"{tiempo_ejercicios} min")
    m2.metric("🧘 Estiramientos", f"{TIEMPO_ESTIRAMIENTOS_MIN} min")
    m3.metric("⏱️ Tiempo Total", f"{tiempo_total_sesion} min")

    st.markdown("### 📋 Resumen de Ejercicios Generados")
    for idx, (_, row) in enumerate(df_rutina.iterrows(), start=1):
        prescripcion, _, _, _ = obtener_prescripcion_y_tiempo(
            st.session_state.nivel_seleccionado, row.get("Grupo Muscular", "")
        )
        st.write(f"**{idx}. {row['Nombre']}** — *{row.get('Grupo Muscular', '')}* (`{prescripcion}`)")

    st.markdown("---")

    nombres_ejercicios = ", ".join(df_rutina["Nombre"].tolist())
    titulo_evento = f"🏋️‍♂️ Entrenamiento VIP ({tiempo_total_sesion} min) - {st.session_state.usuario_actual}"
    descripcion_evento = (
        f"Tu sesión de entrenamiento adaptado:\n\n"
        f"📋 Ejercicios: {nombres_ejercicios}\n\n"
        f"🔗 Entra a la app para empezar: https://rutinas-app.streamlit.app"
    )
    link_calendar = generar_link_google_calendar(
        titulo=titulo_evento,
        descripcion=descripcion_evento,
        duracion_minutos=tiempo_total_sesion,
    )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        st.link_button(
            "📅 Agendar en Google Calendar",
            link_calendar,
            type="secondary",
            use_container_width=True,
        )
    with col_btn2:
        if st.button("🚀 COMENZAR ENTRENAMIENTO AHORA", type="primary", use_container_width=True):
            st.session_state.modo_entrenamiento = True
            st.session_state.paso_actual = 0
            st.rerun()

# -----------------------------------------------------------------------------
# FASE 2: MODO ENTRENAMIENTO GUIADO (PASO A PASO + TEMPORIZADOR CON AUDIO)
# -----------------------------------------------------------------------------

elif st.session_state.df_rutina is not None and st.session_state.modo_entrenamiento:
    df_rutina = st.session_state.df_rutina
    total_ejercicios = len(df_rutina)
    total_pasos = total_ejercicios + 1
    paso_actual = st.session_state.paso_actual

    progreso_porcentaje = min(float(paso_actual / total_pasos), 1.0)
    st.progress(progreso_porcentaje)

    if paso_actual < total_ejercicios:
        st.caption(f"📈 **Progreso:** Ejercicio **{paso_actual + 1} de {total_ejercicios}** ({int(progreso_porcentaje * 100)}%)")
    elif paso_actual == total_ejercicios:
        st.caption("🧘 **Progreso:** Bloque Final de Estiramientos")
    else:
        st.caption("🎉 **Progreso:** ¡100% Completado!")

    st.markdown("---")

    if paso_actual < total_ejercicios:
        row = df_rutina.iloc[paso_actual]
        nivel_sel = st.session_state.nivel_seleccionado

        st.subheader(f"🔹 Ejercicio {paso_actual + 1}: {row['Nombre']} ({row.get('ID_Ejercicio', 'EJ')})")

        prescripcion, t_seg, _, descanso_seg = obtener_prescripcion_y_tiempo(
            nivel_sel, row.get("Grupo Muscular", "")
        )
        st.info(f"📋 **Prescripción:** {prescripcion}")

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
            st.write("**Secuencia de Ejecución:**")
            cols_img = st.columns(len(urls_validas))
            for index, url in enumerate(urls_validas):
                with cols_img[index]:
                    st.image(url, caption=f"Paso {index + 1}", use_container_width=True)

        st.markdown("---")

        # TEMPORIZADOR CON ALARMA SONORA
        st.markdown("### ⏱️ Temporizador de Descanso / Trabajo")
        URL_SONIDO_ALARMA = "https://actions.google.com/sounds/v1/alarms/beep_short.ogg"

        if st.button(f"⏳ Iniciar Descanso ({descanso_seg}s)", use_container_width=True):
            ph = st.empty()
            for t in range(descanso_seg, -1, -1):
                ph.metric("Tiempo Restante", f"{t} seg")
                time.sleep(1)

            ph.success("🔔 ¡Tiempo finalizado! Siguiente serie o ejercicio.")

            # Reproducción de audio en el navegador
            st.components.v1.html(
                f"""
                <audio autoplay style="display:none;">
                    <source src="{URL_SONIDO_ALARMA}" type="audio/ogg">
                </audio>
                <script>
                    var audio = document.querySelector('audio');
                    if (audio) {{ audio.play(); }}
                </script>
                """,
                height=0,
            )

        st.markdown("---")
        col_nav1, col_nav2 = st.columns([1, 1])

        with col_nav1:
            if paso_actual > 0:
                if st.button("⬅️ Ejercicio Anterior", use_container_width=True):
                    st.session_state.paso_actual -= 1
                    st.rerun()

        with col_nav2:
            if st.button("✅ Marcar como Realizado ➔ Siguiente", type="primary", use_container_width=True):
                st.session_state.paso_actual += 1
                st.rerun()

    elif paso_actual == total_ejercicios:
        st.subheader("🧘 Bloque de Enfriamiento y Estiramientos (10 min)")
        st.markdown(
            """
        * 🧘‍♂️ **Isquiotibiales y Cuádriceps:** 2 series de 30 seg por pierna.
        * 🧘‍♀️ **Pectorales:** 2 series de 30 seg contra pared/esquina.
        * 🧘‍♂️ **Glúteos (Piriforme):** 2 series de 30 seg por lado.
        * 🧘‍♀️ **Zona Lumbar / Abdominal (Cobra):** 2 series de 30 seg suave.
        """
        )

        st.markdown("---")
        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅️ Ejercicio Anterior", use_container_width=True):
                st.session_state.paso_actual -= 1
                st.rerun()
        with col_nav2:
            if st.button("🏁 Finalizar Entrenamiento Completo", type="primary", use_container_width=True):
                st.session_state.paso_actual += 1
                st.rerun()

    else:
        st.balloons()
        st.success("🎉 ¡ENHORABUENA! Has completado tu entrenamiento de hoy.")
        st.markdown("---")
        if st.button("🔄 Volver al Menú Principal", type="primary", use_container_width=True):
            st.session_state.paso_actual = 0
            st.session_state.modo_entrenamiento = False
            st.rerun()

else:
    st.info("👆 Configura la estructura en la barra superior y pulsa **'Generar Rutina Personalizada'**.")
