# main.py
import pygame
import cv2
import config
from eye_tracker import EyeTracker
from calibration import Calibration
from keyboard_ui import Key, Keyboard
from word_suggester import WordSuggester
import time
# Importa pyttsx3 para síntesis de voz (TTS)
try:
    import pyttsx3
except ImportError:
    print("Advertencia: La librería pyttsx3 no está instalada. La función de leer texto no estará disponible.")
    pyttsx3 = None
import threading

# --- Clase SuggestionBox ---
class SuggestionBox:
    """
    Representa una caja de sugerencia de palabra.
    """
    def __init__(self, text, x, y, width, height, font):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.is_hovered = False

    def draw(self, screen):
        """
        Dibuja la caja de sugerencia en pantalla.
        """
        color = config.SUGGESTION_HIGHLIGHT_COLOR if self.is_hovered else config.SUGGESTION_BG_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, config.BLACK, self.rect, 1, border_radius=5)
        text_surface = self.font.render(self.text, True, config.SUGGESTION_FONT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        # Recorta el texto si es demasiado largo
        if text_rect.width > self.rect.width - 10:
            avg_char_w = self.font.size("a")[0] if self.font.size("a")[0] > 0 else 10
            max_chars = int((self.rect.width - 10) / avg_char_w) if avg_char_w > 0 else 0
            disp_text = self.text[:max_chars - 3] + "..." if max_chars > 3 else self.text[:max_chars] if max_chars > 0 else ""
            text_surface = self.font.render(disp_text, True, config.SUGGESTION_FONT_COLOR)
            text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_gazed(self, gaze_pos):
        """
        Determina si la mirada está sobre esta caja.
        """
        if gaze_pos:
            return self.rect.collidepoint(gaze_pos)
        return False

# --- Clase principal de la aplicación ---
class EyeTyperApp:
    """
    Clase principal que gestiona la lógica del teclado por mirada.
    """
    def __init__(self):
        # Inicialización de Pygame y recursos
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.display.set_caption("EyeTyper - Escritura por Mirada (MediaPipe)")
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_text_area = pygame.font.Font(config.DEFAULT_FONT_NAME, config.FONT_SIZE_TEXT_AREA)
        self.font_suggestion = pygame.font.Font(config.DEFAULT_FONT_NAME, config.FONT_SIZE_SUGGESTION)
        self.font_info = pygame.font.Font(config.DEFAULT_FONT_NAME, config.FONT_SIZE_INFO)
        
        # Carga de sonidos para retroalimentación auditiva
        try:
            self.sound_letter = pygame.mixer.Sound("letra.wav")
            self.sound_function = pygame.mixer.Sound("borrar.wav")
        except pygame.error as e:
            print(f"Error al cargar los sonidos: {e}")
            self.sound_letter = None
            self.sound_function = None

        # Inicialización del motor de voz (TTS)
        if pyttsx3:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            spanish_voice_id = next((voice.id for voice in voices if 'spanish' in voice.name.lower()), None)
            if spanish_voice_id:
                self.tts_engine.setProperty('voice', spanish_voice_id)
            self.tts_engine.setProperty('rate', 150)
        else:
            self.tts_engine = None

        # Inicialización del rastreador ocular
        try:
            self.eye_tracker = EyeTracker()
        except IOError as e:
            self._show_error_and_exit(f"Error de Webcam/MediaPipe: {e}")
        
        # Inicialización del teclado, sugerencias y calibración
        self.keyboard = Keyboard(config.SCREEN_WIDTH)
        self.word_suggester = WordSuggester()
        self.typed_text = ""
        self.suggestion_boxes = []
        self.gazed_key_object = None
        self.gazed_suggestion_object = None
        self._setup_suggestion_box_positions()
        self._define_total_interaction_area()
        self.calibration = Calibration(self.eye_tracker, self.screen, self.get_total_interaction_area_rect)
        
        # Variables de estado de la aplicación
        self.app_state = "NAVIGATING"  # NAVIGATING o FROZEN
        self.dwell_start_time = 0
        self.current_dwell_item = None
        self.frozen_item = None
        self.frozen_position = None
        self.frozen_start_time = 0
        self.DWELL_TO_FREEZE_MS = 800  # Tiempo de fijación para congelar selección
        self.ACTION_WINDOW_MS = 1000   # Tiempo para realizar acción tras congelar
        self.running = True

    def _speak_text(self, text_to_speak):
        """
        Utiliza el motor TTS para leer el texto en voz alta.
        """
        if not self.tts_engine:
            return
        try:
            self.tts_engine.say(text_to_speak)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error en el motor de TTS: {e}")

    def _handle_state_and_selection(self):
        """
        Lógica de navegación y selección por mirada y parpadeo.
        """
        now = time.time() * 1000
        gazed_item = self.gazed_suggestion_object if self.gazed_suggestion_object else self.gazed_key_object
        if self.app_state == "NAVIGATING":
            if gazed_item:
                if gazed_item != self.current_dwell_item:
                    self.current_dwell_item = gazed_item
                    self.dwell_start_time = now
                else:
                    if now - self.dwell_start_time > self.DWELL_TO_FREEZE_MS:
                        self.app_state = "FROZEN"
                        self.frozen_item = gazed_item
                        self.frozen_position = self.eye_tracker.get_gaze_screen_coordinates()
                        self.frozen_start_time = now
            else:
                self.current_dwell_item = None
        elif self.app_state == "FROZEN":
            if now - self.frozen_start_time > self.ACTION_WINDOW_MS:
                self.app_state = "NAVIGATING"
                self.frozen_item = None
            if self.eye_tracker.is_blinking():
                self._execute_click(self.frozen_item)
                self.app_state = "NAVIGATING"
                self.frozen_item = None

    def _execute_click(self, selected_item):
        """
        Ejecuta la acción correspondiente al elemento seleccionado (tecla o sugerencia).
        """
        if not selected_item:
            return

        if isinstance(selected_item, Key):
            # Si es la tecla especial LEER, lee el texto en voz alta
            if hasattr(selected_item, 'char') and selected_item.char == 'LEER':
                if self.sound_function:
                    self.sound_function.play()
                if self.typed_text.strip():
                    # Usa un hilo para no congelar la interfaz mientras habla
                    tts_thread = threading.Thread(target=self._speak_text, args=(self.typed_text,), daemon=True)
                    tts_thread.start()
            else:
                # Otras teclas: función o letra normal
                if selected_item.is_special:
                    if self.sound_function:
                        self.sound_function.play()
                else:
                    if self.sound_letter:
                        self.sound_letter.play()
                # Actualiza el texto escrito
                self.typed_text = self.keyboard.handle_input(selected_item, self.typed_text)

        elif isinstance(selected_item, SuggestionBox):
            # Si selecciona una sugerencia, reemplaza la palabra actual
            if self.sound_function:
                self.sound_function.play()
            words = self.typed_text.rstrip().split(' ')
            if words and self.typed_text and not self.typed_text.endswith(' '):
                words[-1] = selected_item.text
                self.typed_text = " ".join(words) + " "
            else:
                self.typed_text += ("" if self.typed_text and (self.typed_text.endswith(" ") or self.typed_text.endswith("\n")) else " ") + selected_item.text + " "
        
        self._update_suggestions_display()

    def _update_gaze(self):
        """
        Actualiza la posición de la mirada y determina el elemento bajo la mirada.
        """
        if self.app_state == "FROZEN" and self.frozen_position:
            self.eye_tracker.set_gaze_coordinates(self.frozen_position[0], self.frozen_position[1])
        else:
            self.eye_tracker.update_frame()
            raw_gaze = self.eye_tracker.get_raw_gaze_ratio()
            if raw_gaze:
                screen_coords_mapped = self.calibration.map_gaze_to_screen(raw_gaze)
                self.eye_tracker.set_gaze_coordinates(
                    screen_coords_mapped[0] if screen_coords_mapped else None,
                    screen_coords_mapped[1] if screen_coords_mapped else None
                )
        gaze_coords = self.eye_tracker.get_gaze_screen_coordinates()
        self.gazed_key_object = self.keyboard.get_key_at_gaze(gaze_coords)
        self.gazed_suggestion_object = None
        if not self.gazed_key_object:
            for s_box in self.suggestion_boxes:
                if s_box.is_gazed(gaze_coords):
                    self.gazed_suggestion_object = s_box
                    break
        self.keyboard.update_hover_state(self.gazed_key_object)
        for s_box in self.suggestion_boxes:
            s_box.is_hovered = (s_box == self.gazed_suggestion_object)
            
    def _draw_gaze_pointer(self):
        """
        Dibuja el puntero de la mirada en pantalla.
        """
        gaze_coords = self.eye_tracker.get_gaze_screen_coordinates()
        if gaze_coords:
            color = config.GREEN if self.app_state == "FROZEN" else config.GAZE_POINTER_COLOR
            pygame.draw.circle(self.screen, color, gaze_coords, config.GAZE_POINTER_RADIUS, 0)
            pygame.draw.circle(self.screen, config.WHITE, gaze_coords, config.GAZE_POINTER_RADIUS, 1)

    def run_app(self):
        """
        Bucle principal de la aplicación.
        """
        if not hasattr(self, 'eye_tracker'):
            return
        self._run_calibration_sequence()
        self._update_suggestions_display()
        while self.running:
            self._handle_events()
            self._update_gaze()
            self._handle_state_and_selection()
            self._draw()
            self.clock.tick(config.FPS)
        if self.tts_engine:
            self.tts_engine.stop()
        self.eye_tracker.release()
        pygame.quit()

    # Métodos auxiliares para áreas de interacción, sugerencias, eventos y dibujo
    def get_total_interaction_area_rect(self):
        return self.total_interaction_rect

    def _define_total_interaction_area(self):
        """
        Define el área total de interacción (teclado + sugerencias).
        """
        kb_phys_rect = self.keyboard.get_bounding_rect()
        inter_top = self.suggestion_box_start_y - config.KEYBOARD_INTERACTION_PADDING
        inter_bot = kb_phys_rect.bottom + config.KEYBOARD_INTERACTION_PADDING
        inter_left = kb_phys_rect.left - config.KEYBOARD_INTERACTION_PADDING
        inter_right = kb_phys_rect.right + config.KEYBOARD_INTERACTION_PADDING
        self.total_interaction_rect = pygame.Rect(inter_left, inter_top, inter_right - inter_left, inter_bot - inter_top)

    def _setup_suggestion_box_positions(self):
        """
        Calcula y almacena las posiciones de las cajas de sugerencias.
        """
        self.suggestion_box_start_y = (config.TEXT_AREA_Y + config.TEXT_AREA_HEIGHT + config.SUGGESTION_AREA_Y_OFFSET_FROM_TEXT_AREA)
        total_sug_w_avail = config.TEXT_AREA_WIDTH
        s_w_ind = (total_sug_w_avail - (config.SUGGESTION_COUNT - 1) * config.SUGGESTION_BOX_MARGIN) / config.SUGGESTION_COUNT if config.SUGGESTION_COUNT > 0 else total_sug_w_avail
        curr_sx = config.TEXT_AREA_X
        self.base_suggestion_rects = []
        for i in range(config.SUGGESTION_COUNT):
            rect = pygame.Rect(curr_sx + i * (s_w_ind + config.SUGGESTION_BOX_MARGIN), self.suggestion_box_start_y, s_w_ind, config.SUGGESTION_BOX_HEIGHT)
            self.base_suggestion_rects.append(rect)

    def _show_error_and_exit(self, message):
        """
        Muestra un mensaje de error y termina la aplicación.
        """
        self.screen.fill(config.DARK_GRAY)
        error_font = pygame.font.Font(config.DEFAULT_FONT_NAME, 28)
        lines = message.split('\n')
        y_offset = (config.SCREEN_HEIGHT - len(lines) * 35) // 2
        for line in lines:
            text_surface = error_font.render(line, True, config.RED)
            text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH / 2, y_offset))
            self.screen.blit(text_surface, text_rect)
            y_offset += 35
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    pygame.quit()
                    exit()

    def _run_calibration_sequence(self):
        """
        Ejecuta la secuencia de calibración ocular.
        """
        if not self.calibration.run():
            self._show_error_and_exit("Calibración fallida o cancelada.")

    def _handle_events(self):
        """
        Maneja eventos de teclado y cierre de ventana.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_c:
                    print("Forzando recalibración...")
                    self._run_calibration_sequence()

    def _update_suggestions_display(self):
        """
        Actualiza las sugerencias de palabras según el texto escrito.
        """
        words_in_text = self.typed_text.split(' ')
        current_word_prefix = ""
        if self.typed_text and not self.typed_text.endswith(' ') and not self.typed_text.endswith('\n'):
            current_word_prefix = words_in_text[-1]
        self.current_suggestions_text = self.word_suggester.get_suggestions(current_word_prefix)
        self.suggestion_boxes = []
        for i, sug_text in enumerate(self.current_suggestions_text):
            if i < len(self.base_suggestion_rects):
                rect = self.base_suggestion_rects[i]
                self.suggestion_boxes.append(SuggestionBox(sug_text, rect.x, rect.y, rect.width, rect.height, self.font_suggestion))

    def _draw_text_area(self):
        """
        Dibuja el área de texto donde se muestra lo escrito.
        """
        pygame.draw.rect(self.screen, config.TEXT_AREA_COLOR, (config.TEXT_AREA_X, config.TEXT_AREA_Y, config.TEXT_AREA_WIDTH, config.TEXT_AREA_HEIGHT))
        pygame.draw.rect(self.screen, config.BLACK, (config.TEXT_AREA_X, config.TEXT_AREA_Y, config.TEXT_AREA_WIDTH, config.TEXT_AREA_HEIGHT), 2)
        lines_to_display = []
        padding = 10
        available_width = config.TEXT_AREA_WIDTH - 2 * padding
        for text_line in self.typed_text.split('\n'):
            words = text_line.split(' ')
            current_line_text = ""
            for word in words:
                test_line = current_line_text + word + " "
                if self.font_text_area.size(test_line)[0] <= available_width:
                    current_line_text = test_line
                else:
                    lines_to_display.append(current_line_text.strip())
                    current_line_text = word + " "
            lines_to_display.append(current_line_text.strip())
        y_offset = config.TEXT_AREA_Y + padding
        line_height = self.font_text_area.get_linesize()
        max_lines_in_area = (config.TEXT_AREA_HEIGHT - 2 * padding) // line_height if line_height > 0 else 0
        start_display_line = max(0, len(lines_to_display) - max_lines_in_area)
        for i in range(start_display_line, len(lines_to_display)):
            line_surface = self.font_text_area.render(lines_to_display[i], True, config.BLACK)
            self.screen.blit(line_surface, (config.TEXT_AREA_X + padding, y_offset))
            y_offset += line_height

    def _draw_all_suggestions(self):
        """
        Dibuja todas las cajas de sugerencias.
        """
        for s_box in self.suggestion_boxes:
            s_box.draw(self.screen)

    def _draw_debug_info(self):
        """
        Dibuja información de depuración (frame de cámara, estado de mayúsculas, etc).
        """
        annotated_frame = self.eye_tracker.get_annotated_frame()
        if annotated_frame is not None and annotated_frame.size > 0:
            try:
                h, w = annotated_frame.shape[:2]
                if h > 0 and w > 0:
                    target_h = 120
                    aspect_ratio = w / h
                    target_w = int(target_h * aspect_ratio)
                    resized_frame = cv2.resize(annotated_frame, (target_w, target_h))
                    pygame_frame = pygame.surfarray.make_surface(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1))
                    self.screen.blit(pygame_frame, (config.SCREEN_WIDTH - target_w - 10, 10))
            except Exception as e:
                print(f"Error al dibujar frame de depuración: {e}")
        caps_status = "Mayús: ON" if self.keyboard.caps_lock_on else "Mayús: OFF"
        caps_surf = self.font_info.render(caps_status, True, config.WHITE)
        self.screen.blit(caps_surf, (10, config.SCREEN_HEIGHT - 30))
        if self.eye_tracker.raw_gaze_ratio:
            raw_text = f"Raw Gaze: ({self.eye_tracker.raw_gaze_ratio[0]:.2f}, {self.eye_tracker.raw_gaze_ratio[1]:.2f})"
            text_s_raw = self.font_info.render(raw_text, True, config.BLUE)
            self.screen.blit(text_s_raw, (10, config.SCREEN_HEIGHT - 60))

    def _draw(self):
        """
        Dibuja todos los elementos de la interfaz gráfica.
        """
        self.screen.fill(config.DARK_GRAY)
        self.keyboard.draw(self.screen)
        self._draw_text_area()
        self._draw_all_suggestions()
        self._draw_debug_info()
        if self.calibration.is_calibrated:
            self._draw_gaze_pointer()
        pygame.display.flip()

# --- Punto de entrada principal ---
if __name__ == '__main__':
    app = EyeTyperApp()
    if hasattr(app, 'running'):
        app.run_app()