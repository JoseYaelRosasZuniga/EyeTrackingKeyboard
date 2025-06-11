# calibration.py
import pygame
import time
import config

class Calibration:
    def __init__(self, eye_tracker, screen, interaction_area_rect_func): # Cambiado
        self.eye_tracker = eye_tracker
        self.screen = screen
        self.font = pygame.font.Font(config.DEFAULT_FONT_NAME, config.FONT_SIZE_INFO)
        self.calibration_data = {
            "h_ratio_for_screen_left_gaze": 0.25,
            "h_ratio_for_screen_right_gaze": 0.75,
            "v_ratio_for_screen_top_gaze": 0.25,
            "v_ratio_for_screen_bottom_gaze": 0.75
        }
        self.is_calibrated = False
        # interaction_area_rect_func es una función que se llamará para obtener el rect actual
        # Esto es útil si el rect puede cambiar (aunque en nuestro caso se define una vez)
        self.get_interaction_area_rect = interaction_area_rect_func


    def _display_message(self, message, duration_sec=2, y_offset=0):
        # ... (Sin cambios) ...
        self.screen.fill(config.DARK_GRAY)
        text_surface = self.font.render(message, True, config.WHITE)
        text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2 + y_offset))
        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()
        pygame.time.wait(int(duration_sec * 1000))

    def _collect_data_at_point(self, point_pos, point_name_display):
        # ... (Sin cambios, la lógica de redibujo y flip es importante aquí) ...
        self.screen.fill(config.DARK_GRAY)
        message_surface = self.font.render(f"Mire el punto: {point_name_display}", True, config.WHITE)
        message_rect = message_surface.get_rect(center=(config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 4)) # Mensaje más arriba
        self.screen.blit(message_surface, message_rect)
        pygame.draw.circle(self.screen, config.GAZE_POINTER_COLOR_CALIBRATING, point_pos, config.CALIBRATION_POINT_RADIUS, 0)
        pygame.draw.circle(self.screen, config.WHITE, point_pos, config.CALIBRATION_POINT_RADIUS, 3)
        pygame.display.flip() # Flip inicial para mostrar el punto antes del bucle
        start_time = time.time()
        collected_h_ratios_for_point, collected_v_ratios_for_point = [], []
        clock = pygame.time.Clock()
        while time.time() - start_time < (config.CALIBRATION_DURATION_PER_POINT_MS / 1000):
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); exit()
            if not self.eye_tracker.update_frame():
                clock.tick(config.FPS); continue
            self.screen.fill(config.DARK_GRAY) # Limpiar pantalla en cada frame del bucle
            self.screen.blit(message_surface, message_rect) # Redibujar mensaje
            pygame.draw.circle(self.screen, config.GAZE_POINTER_COLOR_CALIBRATING, point_pos, config.CALIBRATION_POINT_RADIUS, 0) # Redibujar punto
            pygame.draw.circle(self.screen, config.WHITE, point_pos, config.CALIBRATION_POINT_RADIUS, 3) # Redibujar borde
            raw_gaze = self.eye_tracker.get_raw_gaze_ratio()
            if raw_gaze:
                h_ratio, v_ratio = raw_gaze
                collected_h_ratios_for_point.append(h_ratio)
                collected_v_ratios_for_point.append(v_ratio)
                feedback_x = int(h_ratio * config.SCREEN_WIDTH)
                feedback_y = int(v_ratio * config.SCREEN_HEIGHT)
                pygame.draw.circle(self.screen, config.BLUE, (feedback_x, feedback_y), 5)
            pygame.display.flip() # Actualizar la pantalla completa
            clock.tick(config.FPS)
        if collected_h_ratios_for_point:
            collected_h_ratios_for_point.sort(); median_h_ratio = collected_h_ratios_for_point[len(collected_h_ratios_for_point)//2]
            self.temp_min_h_during_cal = min(self.temp_min_h_during_cal, median_h_ratio)
            self.temp_max_h_during_cal = max(self.temp_max_h_during_cal, median_h_ratio)
        if collected_v_ratios_for_point:
            collected_v_ratios_for_point.sort(); median_v_ratio = collected_v_ratios_for_point[len(collected_v_ratios_for_point)//2]
            self.temp_min_v_during_cal = min(self.temp_min_v_during_cal, median_v_ratio)
            self.temp_max_v_during_cal = max(self.temp_max_v_during_cal, median_v_ratio)

    def run(self):
        self._display_message("Calibración de Teclado y Sugerencias: Mire los puntos.", 2.5)
        self.temp_min_h_during_cal = 1.0; self.temp_max_h_during_cal = 0.0
        self.temp_min_v_during_cal = 1.0; self.temp_max_v_during_cal = 0.0
        
        interaction_rect = self.get_interaction_area_rect() # Obtener el rect actual

        offset = config.CALIBRATION_POINT_RADIUS + 5 
        points_to_calibrate = {
            "ESQUINA SUPERIOR IZQ.": (interaction_rect.left + offset, interaction_rect.top + offset),
            "ESQUINA SUPERIOR DER.": (interaction_rect.right - offset, interaction_rect.top + offset),
            "CENTRO DEL ÁREA": interaction_rect.center,
            "ESQUINA INFERIOR IZQ.": (interaction_rect.left + offset, interaction_rect.bottom - offset),
            "ESQUINA INFERIOR DER.": (interaction_rect.right - offset, interaction_rect.bottom - offset),
        }
        for name, pos in points_to_calibrate.items():
             pos_x = max(0 + offset, min(pos[0], config.SCREEN_WIDTH - offset))
             pos_y = max(0 + offset, min(pos[1], config.SCREEN_HEIGHT - offset))
             self._collect_data_at_point((int(pos_x), int(pos_y)), name) # Asegurar que pos sean enteros

        # ... (resto de la lógica de run sin cambios) ...
        h_gaze_for_screen_left = self.temp_min_h_during_cal
        h_gaze_for_screen_right = self.temp_max_h_during_cal
        v_gaze_for_screen_top = self.temp_min_v_during_cal
        v_gaze_for_screen_bottom = self.temp_max_v_during_cal
        min_h_span = 0.05
        if (h_gaze_for_screen_right - h_gaze_for_screen_left) < min_h_span:
            print(f"Rango H de calibración ({h_gaze_for_screen_left:.2f}-{h_gaze_for_screen_right:.2f}) muy pequeño. Usando defaults.")
            h_gaze_for_screen_left = self.calibration_data["h_ratio_for_screen_left_gaze"]
            h_gaze_for_screen_right = self.calibration_data["h_ratio_for_screen_right_gaze"]
        min_v_span = 0.05
        if (v_gaze_for_screen_bottom - v_gaze_for_screen_top) < min_v_span:
            print(f"Rango V de calibración ({v_gaze_for_screen_top:.2f}-{v_gaze_for_screen_bottom:.2f}) muy pequeño. Usando defaults.")
            v_gaze_for_screen_top = self.calibration_data["v_ratio_for_screen_top_gaze"]
            v_gaze_for_screen_bottom = self.calibration_data["v_ratio_for_screen_bottom_gaze"]
        self.calibration_data["h_ratio_for_screen_left_gaze"] = h_gaze_for_screen_left
        self.calibration_data["h_ratio_for_screen_right_gaze"] = h_gaze_for_screen_right
        self.calibration_data["v_ratio_for_screen_top_gaze"] = v_gaze_for_screen_top
        self.calibration_data["v_ratio_for_screen_bottom_gaze"] = v_gaze_for_screen_bottom
        self._display_message("Calibración completada.", 2)
        self.is_calibrated = True
        print("Datos de calibración finales:")
        print(f"  H (Ratio para Izq -> Ratio para Der): {self.calibration_data['h_ratio_for_screen_left_gaze']:.2f} -> {self.calibration_data['h_ratio_for_screen_right_gaze']:.2f}")
        print(f"  V (Ratio para Arr -> Ratio para Abj): {self.calibration_data['v_ratio_for_screen_top_gaze']:.2f} -> {self.calibration_data['v_ratio_for_screen_bottom_gaze']:.2f}")
        return self.is_calibrated

    def map_gaze_to_screen(self, raw_gaze_ratio):
        if not self.is_calibrated or not raw_gaze_ratio: return None
        current_h_ratio, current_v_ratio = raw_gaze_ratio
        h_cal_left = self.calibration_data["h_ratio_for_screen_left_gaze"]
        h_cal_right = self.calibration_data["h_ratio_for_screen_right_gaze"]
        v_cal_top = self.calibration_data["v_ratio_for_screen_top_gaze"]
        v_cal_bottom = self.calibration_data["v_ratio_for_screen_bottom_gaze"]
        
        calibrated_h_span = (h_cal_right - h_cal_left) * config.GAZE_SENSITIVITY_SCALER
        calibrated_v_span = (v_cal_bottom - v_cal_top) * config.GAZE_SENSITIVITY_SCALER

        # Manejo de spans muy pequeños o nulos después de escalar
        if abs(calibrated_h_span) < 0.01: calibrated_h_span = 0.5 * config.GAZE_SENSITIVITY_SCALER
        if abs(calibrated_v_span) < 0.01: calibrated_v_span = 0.5 * config.GAZE_SENSITIVITY_SCALER
        
        norm_h = (current_h_ratio - h_cal_left) / calibrated_h_span if calibrated_h_span != 0 else 0.5
        norm_v = (current_v_ratio - v_cal_top) / calibrated_v_span if calibrated_v_span != 0 else 0.5
        
        # Mantenemos la opción de invertir norm_h si sigue habiendo problemas de dirección.
        # Si el cálculo de ratio en eye_tracker.py (0=izq, 1=der) y esta normalización son correctas,
        # no debería ser necesario.
        # norm_h = 1.0 - norm_h # Descomentar solo si la dirección horizontal está invertida.

        target_rect = self.get_interaction_area_rect() # Usar la función para obtener el rect
        screen_x = target_rect.left + norm_h * target_rect.width
        screen_y = target_rect.top + norm_v * target_rect.height
        screen_x = max(target_rect.left, min(screen_x, target_rect.right - 1))
        screen_y = max(target_rect.top, min(screen_y, target_rect.bottom - 1))
        return int(screen_x), int(screen_y)