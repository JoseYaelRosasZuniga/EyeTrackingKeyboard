import pygame

# --- General ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30

# --- Colores (RGB) ---
BLACK = (0, 0, 0); WHITE = (255, 255, 255); GRAY = (200, 200, 200); LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (50, 50, 50); GREEN = (0, 200, 0); BLUE = (0, 0, 200); RED = (200, 0, 0)
HIGHLIGHT_COLOR = (100, 200, 100)
SUGGESTION_HIGHLIGHT_COLOR = (100, 100, 200)

# --- Fuentes ---
pygame.init()
DEFAULT_FONT_NAME = None
FONT_SIZE_KEY = 38
FONT_SIZE_TEXT_AREA = 28
FONT_SIZE_SUGGESTION = 26
FONT_SIZE_INFO = 20

# --- Teclado ---
KEY_WIDTH = 90; KEY_HEIGHT = 90; KEY_MARGIN = 6; KEY_BORDER_RADIUS = 11
KEYBOARD_INTERACTION_PADDING = 15
KEYBOARD_START_Y_OFFSET_FROM_SUGGESTIONS = 20

KEYBOARD_LAYOUT = [
    ['LEER','q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'BACKSPACE'], # <--- TU CAMBIO APLICADO
    ['CAPS', 'z', 'x', 'c', 'v', 'b', 'n', 'm'],
    ['ESPACIO']
]

# --- Área de Texto ---
TEXT_AREA_X = 50; TEXT_AREA_Y = 50; TEXT_AREA_WIDTH = SCREEN_WIDTH - 100
TEXT_AREA_HEIGHT = 80; TEXT_AREA_COLOR = LIGHT_GRAY

# --- Sugerencias ---
SUGGESTION_AREA_Y_OFFSET_FROM_TEXT_AREA = 10
SUGGESTION_COUNT = 3
SUGGESTION_BOX_HEIGHT = 50
SUGGESTION_BOX_MARGIN = 10
SUGGESTION_BG_COLOR = (210, 210, 210)
SUGGESTION_FONT_COLOR = BLACK


# --- Puntero de Mirada ---
GAZE_POINTER_RADIUS = 9
GAZE_POINTER_COLOR = RED
GAZE_POINTER_CROSSHAIR_LENGTH = 15
GAZE_POINTER_COLOR_CALIBRATING = (255, 165, 0)

# --- AJUSTES DE VELOCIDAD (Tus valores) ---
GAZE_SMOOTHING_FACTOR = 0.07
GAZE_SENSITIVITY_SCALER = 1.7

# --- Calibración ---
CALIBRATION_POINT_RADIUS = 18
CALIBRATION_DURATION_PER_POINT_MS = 2500

# Esta variable ya no se usa en esta versión simplificada, pero la dejamos por si acaso
VERTICAL_SENSITIVITY_MULTIPLIER = 1.6 

# --- Detección de Parpadeo / Selección ---
USE_BLINK_FOR_SELECTION = True
DWELL_TIME_MS = 900 # Tiempo de permanencia para seleccionar (si USE_BLINK_FOR_SELECTION es False)


# --- Archivo de Palabras ---
SPANISH_WORDS_FILE = "palabras_es.txt"

# --- Opciones de Depuración ---
SHOW_DEBUG_FACE_MESH = True