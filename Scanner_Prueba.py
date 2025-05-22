import cv2
from pyzbar import pyzbar
from tkinter import Tk, Label, StringVar, font, Frame
from PIL import Image, ImageTk
import os

# Obtener la ruta absoluta del directorio actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONOS_DIR = os.path.join(BASE_DIR, "iconos")

# Configuración de íconos con rutas absolutas
ICONOS_DISCAPACIDAD = {
    "Discapacidad Visual": os.path.join(ICONOS_DIR, "Visual.png"),
    "Discapacidad Física": os.path.join(ICONOS_DIR, "Fisico.png"),
    "Discapacidad Auditiva": os.path.join(ICONOS_DIR, "Auditiva.png"),
    "Discapacidad Intelectual": os.path.join(ICONOS_DIR, "Intelectual.png"),
    "default": os.path.join(ICONOS_DIR, "Default.png")
}

ICONO_TERCERA_EDAD = os.path.join(ICONOS_DIR, "3raEdad.png")

def cargar_icono(ruta, tamaño=(64, 64)):
    """Carga un ícono con mejor manejo de errores"""
    try:
        print(f"Intentando cargar: {ruta}")  # Para depuración
        if os.path.exists(ruta):
            img = Image.open(ruta)
            img = img.resize(tamaño, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            print(f"¡Archivo no encontrado!: {ruta}")
            # Crear un ícono de respaldo rojo
            from PIL import ImageDraw
            img = Image.new('RGB', tamaño, (255, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((15, 20), "X", fill=(255, 255, 255))
            return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error al cargar ícono: {str(e)}")
        # Crear un ícono de respaldo azul
        img = Image.new('RGB', tamaño, (0, 0, 255))
        return ImageTk.PhotoImage(img)

def parse_qr_data(data):
    """Versión final que procesa el campo 'Tercera edad' correctamente"""
    try:
        # Forzar decodificación UTF-8
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        qr_info = {}
        for line in data.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                qr_info[key.strip()] = value.strip()
        
        # Normalizar discapacidad
        discapacidad = qr_info.get('Discapacidad', 'No especificada')
        discapacidad = {
            'Discapacidad Fisica': 'Discapacidad Física',
            'Discapacidad Fﾃｭsica': 'Discapacidad Física'
        }.get(discapacidad, discapacidad)
        
        # Procesar campo 'Tercera edad'
        tercera_edad = qr_info.get('Tercera edad', 'No').strip().lower()
        es_tercera_edad = tercera_edad in ('sí', 'si', 's', 'yes', 'true', '1')
        
        return (
            discapacidad,
            es_tercera_edad,  # True/False
            qr_info.get('Ruta de bus', 'No especificada').replace(" Ruta", "").strip(),
            qr_info.get('Ruta de bus', '').split()[-1] if qr_info.get('Ruta de bus') else ""
        )
    except Exception as e:
        print(f"Error procesando QR: {str(e)}")
        return "", False, "", ""
    
def scan_qr(iconos_disc, icono_tercera_edad):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        info_var.set("Error: No se puede acceder a la cámara")
        return
    
    # Configurar manejo de cierre
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(cap))
    
    def update_frame():
        ret, frame = cap.read()
        
        if not ret:
            info_var.set("Error: No se puede leer la cámara")
            return
        
        # Procesamiento del frame
        process_frame(frame)
        
        # Mostrar frame
        cv2.imshow("Escaner QR - Sistema de Transporte", frame)
        
        # Continuar el bucle
        root.after(10, update_frame)
    
    def process_frame(frame):
        qr_codes = pyzbar.decode(frame)
    
        for qr in qr_codes:
            data = qr.data.decode('utf-8')
            discapacidad, es_tercera_edad, cooperativa, numero_ruta = parse_qr_data(data)
        
            # Actualizar interfaz
            update_ui(discapacidad, es_tercera_edad, cooperativa, numero_ruta, qr, frame)
    
    def update_ui(discapacidad, es_tercera_edad, cooperativa, numero_ruta, qr, frame):
        cooperativa_var.set(cooperativa)
        ruta_var.set(numero_ruta)
    
        # Actualizar ícono de discapacidad
        icono_disc = iconos_disc.get(discapacidad, iconos_disc["default"])
        icono_disc_label.config(image=icono_disc)
        icono_disc_label.image = icono_disc
    
        # Mostrar ícono de tercera edad solo si es True, de lo contrario mostrar ícono default
        if es_tercera_edad:
            icono_edad_label.config(image=icono_tercera_edad)
            icono_edad_label.image = icono_tercera_edad
        else:
            icono_edad_label.config(image=iconos_disc["default"])  # Mostrar ícono default cuando no es tercera edad
            icono_edad_label.image = iconos_disc["default"]
    
        # Dibujar detección
        (x, y, w, h) = qr.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "QR Detectado", (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    def on_close(cap):
        cap.release()
        cv2.destroyAllWindows()
        root.quit()
    
    # Iniciar bucle
    update_frame()

# Configuración de la ventana principal
root = Tk()
root.title("Sistema de Transporte - Escáner QR")
root.geometry("800x600")
root.configure(bg='black')

# Cargar íconos con verificación
print("\nCargando íconos...")  # Depuración
iconos_discapacidad = {k: cargar_icono(v) for k, v in ICONOS_DISCAPACIDAD.items()}
icono_tercera_edad_img = cargar_icono(ICONO_TERCERA_EDAD)

# Verificación de íconos cargados
print("\nResultado de carga de íconos:")  # Depuración
for nombre, icono in iconos_discapacidad.items():
    print(f"{nombre}: {'OK' if icono else 'FALLÓ'}")
print(f"Tercera edad: {'OK' if icono_tercera_edad_img else 'FALLÓ'}\n")

# Marco superior para íconos
iconos_frame = Frame(root, bg='black')
iconos_frame.pack(fill='x', pady=20)

# Ícono de discapacidad (izquierda)
icono_disc_label = Label(iconos_frame, bg='black')
icono_disc_label.pack(side='left', padx=50)

# Ícono de tercera edad (derecha)
icono_edad_label = Label(iconos_frame, bg='black')
icono_edad_label.pack(side='right', padx=50)

# Nombre de la cooperativa (centrado)
cooperativa_var = StringVar()
cooperativa_var.set("")
Label(root, textvariable=cooperativa_var, font=('Helvetica', 18), 
      bg='black', fg='white').pack(pady=10)

# Número de ruta
ruta_frame = Frame(root, bg='black')
ruta_frame.pack(pady=20)

Label(ruta_frame, text="Ruta", font=('Helvetica', 14), 
      bg='black', fg='white').pack(side='left', padx=10)

ruta_var = StringVar()
ruta_var.set("")
Label(ruta_frame, textvariable=ruta_var, font=('Helvetica', 72, 'bold'), 
      bg='black', fg='white').pack(side='left')

# Mensaje inicial
info_var = StringVar()
#info_var.set("Acerca un código QR a la cámara...")
Label(root, textvariable=info_var, font=('Helvetica', 12), 
      bg='black', fg='white').pack(pady=20)

# Iniciar escaneo
root.after(100, lambda: scan_qr(iconos_discapacidad, icono_tercera_edad_img))

root.mainloop()