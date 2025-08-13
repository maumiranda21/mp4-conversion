import streamlit as st
import os
from moviepy.editor import VideoFileClip
import zipfile
import io
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
# Usamos st.set_page_config() para establecer el tema oscuro por defecto y otros detalles.
st.set_page_config(
    layout="centered",
    page_title="Video a Audio",
    page_icon="🎵",
    initial_sidebar_state="auto",
)

# --- ESTILOS CSS PERSONALIZADOS ---
# Inyectamos CSS para redondear las esquinas de los elementos de la interfaz.
def apply_custom_css():
    """
    Aplica CSS para redondear las esquinas de botones, contenedores y otros elementos.
    """
    st.markdown("""
        <style>
            /* Redondea los botones */
            .stButton > button {
                border-radius: 15px;
            }
            /* Redondea el contenedor del cargador de archivos */
            div[data-testid="stFileUploader"] {
                border: 2px dashed #4A4A4A;
                border-radius: 15px;
                padding: 1rem;
            }
            /* Redondea los contenedores principales y expanders */
            div[data-testid="stVerticalBlock"], div[data-testid="stExpander"] {
                border-radius: 15px;
            }
            /* Redondea el botón de descarga */
            div[data-testid="stDownloadButton"] > button {
                border-radius: 15px;
            }
            /* Estilo para los mensajes de éxito y advertencia */
            div[data-testid="stAlert"] {
                border-radius: 15px;
            }
        </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES PRINCIPALES ---

def convert_to_audio(video_path, output_audio_path):
    """
    Convierte un archivo de video a audio (MP3) usando moviepy.
    """
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        if audio_clip:
            audio_clip.write_audiofile(output_audio_path, codec='mp3')
            audio_clip.close()
        video_clip.close()
        return True
    except Exception as e:
        st.error(f"Error al procesar el archivo {os.path.basename(video_path)}: {e}")
        return False

def reset_app_state():
    """
    Reinicia el estado de la aplicación para permitir una nueva carga de archivos.
    Limpia los archivos procesados y subidos de la sesión.
    """
    # Elimina los archivos de la sesión para limpiar la interfaz
    if 'processed_files' in st.session_state:
        del st.session_state['processed_files']
    if 'uploaded_files' in st.session_state:
        del st.session_state['uploaded_files']
    st.success("¡Listo para empezar de nuevo! Sube nuevos archivos.")
    time.sleep(2) # Pequeña pausa para que el usuario lea el mensaje
    st.rerun()

# --- INTERFAZ DE LA APLICACIÓN ---

apply_custom_css()

st.title("🎬 → 🎵 Conversor de Video a Audio")
st.markdown("Sube uno o varios videos (`.mp4`, `.mov`, `.avi`) y conviértelos a formato de audio `.mp3` con un solo clic.")

# Contenedor para la subida de archivos
with st.container():
    uploaded_files = st.file_uploader(
        "Arrastra y suelta tus videos aquí",
        type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        accept_multiple_files=True,
        key="file_uploader"
    )

# Columnas para los botones de acción
col1, col2 = st.columns([1, 1])

with col1:
    convert_button = st.button("✨ Convertir a Audio", use_container_width=True, type="primary", disabled=not uploaded_files)

with col2:
    if st.button("🔄 Volver a empezar", use_container_width=True):
        reset_app_state()

# --- LÓGICA DE PROCESAMIENTO Y DESCARGA ---

if convert_button and uploaded_files:
    # Crear directorios temporales si no existen
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    output_audio_paths = []
    
    with st.spinner('Convirtiendo videos... Esto puede tardar unos momentos.'):
        for uploaded_file in uploaded_files:
            # Guardar el archivo subido en un directorio temporal
            video_path = os.path.join(temp_dir, uploaded_file.name)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Definir la ruta del archivo de audio de salida
            file_name, _ = os.path.splitext(uploaded_file.name)
            output_audio_path = os.path.join(temp_dir, f"{file_name}.mp3")

            # Realizar la conversión
            if convert_to_audio(video_path, output_audio_path):
                output_audio_paths.append(output_audio_path)
            
            # Limpiar el archivo de video temporal después de la conversión
            os.remove(video_path)

    if output_audio_paths:
        st.session_state['processed_files'] = output_audio_paths
        st.rerun() # Volver a ejecutar para mostrar los botones de descarga

# Mostrar los botones de descarga si hay archivos procesados
if 'processed_files' in st.session_state and st.session_state['processed_files']:
    st.success("✅ ¡Conversión completada con éxito!")

    processed_files = st.session_state['processed_files']

    # Si es un solo archivo, mostrar un botón de descarga simple
    if len(processed_files) == 1:
        single_file_path = processed_files[0]
        file_name = os.path.basename(single_file_path)
        with open(single_file_path, "rb") as file:
            st.download_button(
                label=f"📥 Descargar {file_name}",
                data=file,
                file_name=file_name,
                mime="audio/mpeg",
                use_container_width=True
            )
        # Limpiar el archivo después de crear el botón de descarga
        os.remove(single_file_path)

    # Si son varios archivos, comprimirlos en un ZIP
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in processed_files:
                zip_file.write(file_path, os.path.basename(file_path))
        
        zip_buffer.seek(0)
        st.download_button(
            label="📥 Descargar todos los audios (.zip)",
            data=zip_buffer,
            file_name="audios_convertidos.zip",
            mime="application/zip",
            use_container_width=True
        )
        # Limpiar todos los archivos de audio temporales
        for file_path in processed_files:
            os.remove(file_path)
    
    # Limpiar el estado de la sesión para evitar que los botones se muestren de nuevo
    del st.session_state['processed_files']

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Creado con ❤️ usando Streamlit</div>", unsafe_allow_html=True)
