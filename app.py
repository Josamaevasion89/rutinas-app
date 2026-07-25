import unicodedata
import pandas as pd
import streamlit as st

# 1. Configuración de la página
st.set_page_config(
    page_title="Generador de Rutinas Pro", page_icon="🏋️‍♂️", layout="wide"
)

# -----------------------------------------------------------------------------
# GESTIÓN DE ACCESO Y AUTENTICACIÓN (Membresía / Login)
# -----------------------------------------------------------------------------
# Base de datos simulada de clientes activos (Usuario: Contraseña)
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


# Si el usuario NO está autenticado, detiene la app en la pantalla de Login
if not st.session_state.autenticado:
    pantalla_login()
    st.stop()

# -----------------------------------------------------------------------------
# APLICACIÓN PRINCIPAL (Solo accesible si está logueado)
# -----------------------------------------------------------------------------

# Botón para Cerrar Sesión en la barra lateral
st.sidebar.markdown(f"👤 **Usuario:** `{st.session_state.usuario_actual}`")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.rerun()

st.sidebar.markdown("---")


# Función auxiliar para quitar acentos y normalizar texto
def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


# Cargar datos con caché
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

    columnas_requeridas = ["Nivel", "Grupo Muscular", "Nombre"]
    faltantes = [
        col for col in columnas_requeridas if col not in df_ejercicios.columns
    ]
    if faltantes:
        st.error(
            f"El Excel no contiene las siguientes columnas requeridas: {', '.join(faltantes)}"
        )
        st.stop()

except Exception as e:
    st.error(
        f"Error al cargar 'ejercicios.xlsx'. Asegúrate de que el archivo existe y está cerrado. Detalle: {e}"
    )
    st.stop()


# Prescripción y Tiempos
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


# Header
st.title("🏋️‍♂️ Generador Inteligente de Rutinas Combinadas")
st.markdown("---")

# Estilos CSS
st.markdown(
    """
    <style>
    div[data-testid="stImage"] img {
        height: 220px;
        object-fit: contain !important;
        background-color: #f9f9f9;
        border-radius: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Filtros Laterales
st.sidebar.header("🎯 Parámetros del Entrenamiento")

niveles_disponibles = df_ejercicios["Nivel"].dropna().unique().tolist()
nivel_seleccionado = st.sidebar.selectbox(
    "Nivel de Progresión", niveles_disponibles
)

st.sidebar.subheader("Estructura de la Rutina")
st.sidebar.write("Elige la cantidad deseada de ejercicios:")

num_piernas = st.sidebar.number_input("Ejercicios de Piernas", 0, 10, value=2)
num_pecho = st.sidebar.number_input("Ejercicios de Pecho", 0, 10, value=2)
num_gluteos = st.sidebar.number_input("Ejercicios de Glúteos", 0, 10, value=2)
num_abs = st.sidebar.number_input("Ejercicios de Abdominales", 0, 10, value=4)

solicitudes = {
    "Piernas": num_piernas,
    "Pecho": num_pecho,
    "Gluteos": num_gluteos,
    "Abdominales": num_abs,
}

TIEMPO_MAXIMO_TOTAL_MIN = 60
TIEMPO_ESTIRAMIENTOS_MIN = 10
TIEMPO_MAXIMO_RUTINA_MIN = TIEMPO_MAXIMO_TOTAL_MIN - TIEMPO_ESTIRAMIENTOS_MIN

# Estado de sesión
if "df_rutina" not in st.session_state:
    st.session_state.df_rutina = None
if "tiempo_estimado" not in st.session_state:
    st.session_state.tiempo_estimado = 0
if "ajustado" not in st.session_state:
    st.session_state.ajustado = False

# Generación
if st.sidebar.button("⚡ Generar Rutina Personalizada", type="primary"):
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
        se_ha_recortado = False

        for idx, row in df_rutina.iterrows():
            _, tiempo_ej_seg, _, _ = obtener_prescripcion_y_tiempo(
                nivel_seleccionado, row.get("Grupo Muscular", "")
            )

            if (
                tiempo_total_seg + tiempo_ej_seg
            ) / 60 <= TIEMPO_MAXIMO_RUTINA_MIN:
                tiempo_total_seg += tiempo_ej_seg
                indices_a_conservar.append(idx)
            else:
                se_ha_recortado = True

        st.session_state.df_rutina = df_rutina.loc[indices_a_conservar]
        st.session_state.tiempo_estimado = round(tiempo_total_seg / 60)
        st.session_state.ajustado = se_ha_recortado
    else:
        st.session_state.df_rutina = pd.DataFrame()
        st.session_state.tiempo_estimado = 0
        st.session_state.ajustado = False

# Render
if st.session_state.df_rutina is not None:
    if not st.session_state.df_rutina.empty:
        df_rutina = st.session_state.df_rutina
        tiempo_ejercicios = st.session_state.tiempo_estimado
        tiempo_total_sesion = tiempo_ejercicios + TIEMPO_ESTIRAMIENTOS_MIN

        st.success(
            f"🔥 ¡Rutina Lista! {len(df_rutina)} ejercicios seleccionados."
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("⏱️ Ejercicios Fuerza/Abs", f"{tiempo_ejercicios} min")
        c2.metric("🧘 Estiramientos", f"{TIEMPO_ESTIRAMIENTOS_MIN} min")
        c3.metric(
            "⏳ Tiempo Total Estimado",
            f"{tiempo_total_sesion} min",
            f"Máx {TIEMPO_MAXIMO_TOTAL_MIN} min",
        )

        if st.session_state.ajustado:
            st.warning(
                "⚠️ **Ajuste automático:** Se recortaron ejercicios para no exceder los 60 min."
            )

        st.markdown("---")

        for idx, (_, row) in enumerate(df_rutina.iterrows(), start=1):
            id_ejercicio = row.get("ID_Ejercicio", f"EJ-{idx}")
            st.subheader(f"🔹 {idx}. {row['Nombre']} ({id_ejercicio})")

            prescripcion, t_seg, _, _ = obtener_prescripcion_y_tiempo(
                nivel_seleccionado, row.get("Grupo Muscular", "")
            )
            st.info(
                f"📋 **Prescripción:** {prescripcion} | ⏱️ *Duración est.:* ~{round(t_seg/60, 1)} min"
            )

            col_det1, col_det2, col_det3 = st.columns(3)
            col_det1.write(
                f"**Patrón:** {row.get('Patron Movimiento', row.get('Patrón', '-'))}"
            )
            col_det2.write(f"**Material:** {row.get('Material', '-')}")
            col_det3.write(
                f"**Grupo:** {row.get('Grupo Muscular', 'No especificado')}"
            )

            columnas_fotos = ["Imagen_1", "Imagen_2", "Imagen_3", "Imagen_4"]
            urls_validas = [
                row[col]
                for col in columnas_fotos
                if col in row and pd.notna(row[col]) and str(row[col]).strip()
            ]

            if urls_validas:
                st.write("**Secuencia del ejercicio:**")
                cols_img = st.columns(len(urls_validas))
                for index, url in enumerate(urls_validas):
                    with cols_img[index]:
                        st.image(
                            url,
                            caption=f"Paso {index + 1}",
                            use_container_width=True,
                        )
            else:
                st.caption("📷 Sin imágenes asignadas a este ejercicio.")

            st.markdown("---")

        st.subheader("🧘 Bloque de Enfriamiento y Estiramientos (10 min)")
        st.markdown(
            """
        - 🧘‍♂️ **Isquiotibiales y Cuádriceps:** 2 series de 30 seg por pierna.
        - 🧘‍♀️ **Pectorales:** 2 series de 30 seg contra pared/esquina.
        - 🧘‍♂️ **Glúteos (Piriforme):** 2 series de 30 seg por lado.
        - 🧘‍♀️ **Zona Lumbar / Abdominal (Cobra):** 2 series de 30 seg suave.
        """
        )