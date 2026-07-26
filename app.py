import streamlit as st
import pandas as pd
import datetime
import time
import urllib.parse
from PIL import Image
import io

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS UI
# ==========================================
st.set_page_config(
    page_title="Rehab & Fitness Pro App",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Estilos personalizados */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #F9FAFB;
        border-radius: 10px;
        padding: 1.2rem;
        border: 1px solid #E5E7EB;
        margin-bottom: 1rem;
    }
    .badge-pain {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-pathology {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTIÓN DE SESIÓN Y LOGIN (MEMBRESÍAS)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "Free"
if "username" not in st.session_state:
    st.session_state.username = ""

# Usuarios de prueba (puedes conectarlo a una base de datos real)
USER_DB = {
    "paciente1": {"password": "123", "tier": "Premium", "name": "Carlos M."},
    "terapeuta": {"password": "admin", "tier": "Pro Clinica", "name": "Dr. Osteópata"},
    "usuario": {"password": "123", "tier": "Básico", "name": "Juan P."}
}

def login_screen():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso a la Plataforma</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submit:
                if user_input in USER_DB and USER_DB[user_input]["password"] == pass_input:
                    st.session_state.authenticated = True
                    st.session_state.username = USER_DB[user_input]["name"]
                    st.session_state.user_tier = USER_DB[user_input]["tier"]
                    st.success("¡Bienvenido/a!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

# ==========================================
# 3. CARGA DE DATOS DE EXCEL
# ==========================================
@st.cache_data
def get_mock_data():
    """Genera datos de prueba si no hay un archivo Excel cargado."""
    return pd.DataFrame([
        {
            "ID": "EJ01",
            "Nombre": "Puente de Glúteo Isométrico",
            "Categoria": "Fuerza / Estabilidad",
            "Grupo_Muscular": "Cadera / Core",
            "Patologia": "Lumbalgia",
            "Dolor_Max_Recomendado": 4,
            "Series": 3,
            "Repeticiones": "10 reps (sostener 5s)",
            "Descanso_Seg": 45,
            "Imagen_URL": "https://via.placeholder.com/400x250.png?text=Puente+de+Glutaeo",
            "Instrucciones": "Mantener pelvis neutra, contraer glúteos sin hiperextender la zona lumbar."
        },
        {
            "ID": "EJ02",
            "Nombre": "Movilización Neurodinámica Nervio Ciático",
            "Categoria": "Movilidad",
            "Grupo_Muscular": "Cadera / Pierna",
            "Patologia": "Ciatalgia",
            "Dolor_Max_Recomendado": 3,
            "Series": 2,
            "Repeticiones": "15 oscilaciones suaves",
            "Descanso_Seg": 30,
            "Imagen_URL": "https://via.placeholder.com/400x250.png?text=Neurodinamia+Ciatico",
            "Instrucciones": "Movimiento rítmico de tobillo coordinado con flexión cervical sin provocar dolor agudo."
        },
        {
            "ID": "EJ03",
            "Nombre": "Rotación Externa de Hombro con Banda",
            "Categoria": "Fuerza",
            "Grupo_Muscular": "Hombro / Manguito Rotador",
            "Patologia": "Tendinopatía Manguito Rotador",
            "Dolor_Max_Recomendado": 5,
            "Series": 3,
            "Repeticiones": "12 reps",
            "Descanso_Seg": 60,
            "Imagen_URL": "https://via.placeholder.com/400x250.png?text=Rotacion+Hombro",
            "Instrucciones": "Mantener codo pegado al cuerpo a 90°. Controlar la fase excéntrica."
        },
        {
            "ID": "EJ04",
            "Nombre": "Cat-Cow (Gato-Camello)",
            "Categoria": "Movilidad / Flexibilidad",
            "Grupo_Muscular": "Columna Vertebral",
            "Patologia": "Rigidez Lumbar",
            "Dolor_Max_Recomendado": 2,
            "Series": 3,
            "Repeticiones": "10 ciclos",
            "Descanso_Seg": 30,
            "Imagen_URL": "https://via.placeholder.com/400x250.png?text=Cat-Cow",
            "Instrucciones": "Mover articulación por articulación sincronizando con la respiración."
        }
    ])

def load_exercise_database(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            return df
        except Exception as e:
            st.error(f"Error al leer el archivo Excel: {e}")
            return get_mock_data()
    return get_mock_data()

# ==========================================
# 4. UTILIDADES: GOOGLE CALENDAR Y ALARMA
# ==========================================
def generate_google_calendar_url(title, description, start_dt, duration_minutes=45):
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
    
    fmt = "%Y%m%dT%H%M%SZ"
    dates_str = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
    
    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": description,
        "dates": dates_str
    }
    return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"

def play_sound_alarm():
    # Reproduce una alerta sonora usando HTML5 Web Audio API sin depender de archivos locales
    audio_script = """
        <script>
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        function beep(freq, duration) {
            var osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.value = freq;
            osc.connect(ctx.destination);
            osc.start();
            setTimeout(function() { osc.stop(); }, duration);
        }
        beep(880, 500);
        setTimeout(function() { beep(1174.66, 700); }, 200);
        </script>
    """
    st.components.v1.html(audio_script, height=0)

# ==========================================
# 5. APLICACIÓN PRINCIPAL
# ==========================================
def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"👤 **Usuario:** {st.session_state.username}")
        st.markdown(f"⭐ **Membresía:** `{st.session_state.user_tier}`")
        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        st.header("📂 Carga de Datos")
        uploaded_excel = st.file_uploader("Subir Excel de Ejercicios (.xlsx)", type=["xlsx", "xls"])
        
        st.divider()
        st.header("🎯 Filtros Clinico-Deportivos")
        
        df_exercises = load_exercise_database(uploaded_excel)
        
        # Filtros
        patologias = ["Todas"] + list(df_exercises["Patologia"].dropna().unique())
        selected_patologia = st.selectbox("Filtrar por Patología / Condición", patologias)
        
        max_pain_level = st.slider(
            "Nivel Máximo de Dolor Tolerable (EVA 0-10)",
            min_value=0, max_value=10, value=5,
            help="Filtra ejercicios cuya intensidad no supere la tolerancia del usuario."
        )
        
        grupos_musculares = ["Todos"] + list(df_exercises["Grupo_Muscular"].dropna().unique())
        selected_grupo = st.selectbox("Grupo Muscular / Zona Target", grupos_musculares)

    # Filtrar DataFrame
    filtered_df = df_exercises.copy()
    if selected_patologia != "Todas":
        filtered_df = filtered_df[filtered_df["Patologia"] == selected_patologia]
    
    filtered_df = filtered_df[filtered_df["Dolor_Max_Recomendado"] <= max_pain_level]
    
    if selected_grupo != "Todos":
        filtered_df = filtered_df[filtered_df["Grupo_Muscular"] == selected_grupo]

    # Main Interface
    st.markdown('<div class="main-header">🏋️‍♂️ Prescripción de Ejercicio & Rehabilitación</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Selecciona ejercicios, personaliza la sesión y ejecuta con cronómetro integrado.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Generador de Rutina", "⏱️ Modo Entrenamiento / Cronómetro", "📅 Agendar en Calendar"])

    # ---------------------------------------------------------
    # TAB 1: GENERADOR DE RUTINA
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Ejercicios Disponibles según Parámetros")
        st.caption(f"Se encontraron **{len(filtered_df)}** ejercicios compatibles.")

        if filtered_df.empty:
            st.warning("No hay ejercicios que coincidan con el nivel de dolor o criterios seleccionados.")
        else:
            selected_indices = []
            for idx, row in filtered_df.iterrows():
                with st.container():
                    col_img, col_info, col_select = st.columns([1.5, 3, 1])
                    
                    with col_img:
                        if pd.notna(row.get("Imagen_URL")):
                            st.image(row["Imagen_URL"], use_container_width=True)
                        else:
                            st.info("Sin Imagen")

                    with col_info:
                        st.markdown(f"### {row['Nombre']}")
                        st.markdown(f"**Categoría:** {row['Categoria']} | **Zona:** {row['Grupo_Muscular']}")
                        st.markdown(f"<span class='badge-pathology'>Patología: {row['Patologia']}</span> "
                                    f"<span class='badge-pain'>Límite Dolor: {row['Dolor_Max_Recomendado']}/10</span>", unsafe_allow_html=True)
                        st.write(f"📝 **Instrucciones:** {row['Instrucciones']}")
                        st.write(f"📊 **Dosis recomendada:** {row['Series']} series x {row['Repeticiones']}")

                    with col_select:
                        st.write("")
                        st.write("")
                        if st.checkbox("Añadir a Sesión", key=f"chk_{row['ID']}"):
                            selected_indices.append(idx)
                    
                    st.divider()

            # Guardar rutina seleccionada
            if selected_indices:
                st.session_state.current_routine = filtered_df.loc[selected_indices]
                st.success(f"¡{len(selected_indices)} ejercicios añadidos a la rutina activa!")

    # ---------------------------------------------------------
    # TAB 2: CRONÓMETRO Y MODO ENTRENAMIENTO
    # ---------------------------------------------------------
    with tab2:
        st.subheader("⏱️ Ejecución & Tiempos de Descanso")
        
        if "current_routine" in st.session_state and not st.session_state.current_routine.empty:
            routine = st.session_state.current_routine
            st.info(f"Rutina activa cargada con {len(routine)} ejercicios.")
            
            selected_ex_name = st.selectbox("Selecciona ejercicio para ejecutar:", routine["Nombre"].tolist())
            ex_data = routine[routine["Nombre"] == selected_ex_name].iloc[0]
            
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"### {ex_data['Nombre']}")
                st.write(f"🎯 **Series y Reps:** {ex_data['Series']} series | {ex_data['Repeticiones']}")
                st.write(f"💡 **Técnica:** {ex_data['Instrucciones']}")
            
            with col_b:
                st.markdown("#### Cronómetro de Descanso")
                default_rest = int(ex_data.get("Descanso_Seg", 45))
                rest_time = st.number_input("Segundos de descanso:", min_value=5, max_value=300, value=default_rest, step=5)
                
                if st.button("▶️ Iniciar Descanso", use_container_width=True):
                    timer_placeholder = st.empty()
                    for seconds in range(rest_time, 0, -1):
                        timer_placeholder.metric(label="Tiempo Restante", value=f"{seconds}s")
                        time.sleep(1)
                    
                    timer_placeholder.markdown("<h2 style='color: green; text-align: center;'>¡TIEMPO! 🔔</h2>", unsafe_allow_html=True)
                    play_sound_alarm()
                    st.balloons()
        else:
            st.info("Ve a la pestaña 'Generador de Rutina' y selecciona ejercicios para activar el temporizador.")

    # ---------------------------------------------------------
    # TAB 3: AGENDAR EN GOOGLE CALENDAR
    # ---------------------------------------------------------
    with tab3:
        st.subheader("📅 Planificar y Agendar Sesión")
        
        if "current_routine" in st.session_state and not st.session_state.current_routine.empty:
            routine = st.session_state.current_routine
            
            col1, col2 = st.columns(2)
            with col1:
                date_input = st.date_input("Fecha de la sesión", datetime.date.today())
                time_input = st.time_input("Hora de inicio", datetime.time(10, 0))
                duration_input = st.number_input("Duración total estimada (min)", value=45, step=5)
            
            with col2:
                session_title = f"Sesión de Ejercicios - {st.session_state.username}"
                
                # Detalle de la rutina
                exercise_list_str = "\n".join([f"- {row['Nombre']} ({row['Series']}x{row['Repeticiones']})" for _, row in routine.iterrows()])
                session_desc = f"Rutina Personalizada:\n\n{exercise_list_str}\n\nPrescrito en plataforma Rehab & Fitness."
                
                start_datetime = datetime.datetime.combine(date_input, time_input)
                
                gcal_url = generate_google_calendar_url(
                    title=session_title,
                    description=session_desc,
                    start_dt=start_datetime,
                    duration_minutes=duration_input
                )
                
                st.write("")
                st.write("")
                st.markdown(f'''
                    <a href="{gcal_url}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #4285F4;
                            color: white;
                            padding: 12px 20px;
                            border: none;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: bold;
                            cursor: pointer;
                            width: 100%;">
                            📅 Agendar en Google Calendar
                        </button>
                    </a>
                ''', unsafe_allow_html=True)
        else:
            st.info("Primero selecciona ejercicios en la pestaña 'Generador de Rutina' para agendar la sesión.")

# ==========================================
# 6. EJECUCIÓN DEL FLUJO
# ==========================================
if not st.session_state.authenticated:
    login_screen()
else:
    main_app()
