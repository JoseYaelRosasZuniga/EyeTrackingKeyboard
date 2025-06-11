# keyboard_ui.py
import pygame
import config

class Key:
    # ... (Clase Key sin cambios) ...
    def __init__(self, char, x, y, width, height, font, is_special=False):
        self.char = char
        self.display_char = char
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.is_special = is_special
        self.is_hovered = False
        if self.char == ' ': self.display_char = "ESPACIO"

    def draw(self, screen):
        color = config.HIGHLIGHT_COLOR if self.is_hovered else config.GRAY
        pygame.draw.rect(screen, color, self.rect, border_radius=config.KEY_BORDER_RADIUS)
        pygame.draw.rect(screen, config.BLACK, self.rect, 2, border_radius=config.KEY_BORDER_RADIUS)
        text_surface = self.font.render(self.display_char, True, config.BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_gazed(self, gaze_pos):
        if gaze_pos: return self.rect.collidepoint(gaze_pos)
        return False

class Keyboard:
    def __init__(self, screen_width): # Pasamos screen_width para centrar bien
        self.keys = []
        self.font = pygame.font.Font(config.DEFAULT_FONT_NAME, config.FONT_SIZE_KEY)
        self.caps_lock_on = False
        self.screen_width = screen_width # Guardamos screen_width
        
        # Calculamos la posición Y de inicio del teclado dinámicamente
        self.keyboard_start_y = (config.TEXT_AREA_Y +
                                 config.TEXT_AREA_HEIGHT +
                                 config.SUGGESTION_AREA_Y_OFFSET_FROM_TEXT_AREA +
                                 config.SUGGESTION_BOX_HEIGHT +
                                 config.KEYBOARD_START_Y_OFFSET_FROM_SUGGESTIONS)
        
        self._setup_keys()
        self.bounding_rect = self._calculate_bounding_rect() # Bounding box solo del teclado físico

    def _get_key_width(self, char_code):
        # ... (Sin cambios) ...
        if char_code in ['BACKSPACE', 'ENTER', 'CAPS', 'SHIFT']: return config.KEY_WIDTH * 2.5
        if char_code == 'ESPACIO': return config.KEY_WIDTH * 6
        return config.KEY_WIDTH

    def _setup_keys(self):
        self.keys = []
        start_y_absolute = self.keyboard_start_y # Usar la Y calculada
        
        key_full_height = config.KEY_HEIGHT + config.KEY_MARGIN

        for row_idx, row_chars in enumerate(config.KEYBOARD_LAYOUT):
            # Centrar cada fila
            total_row_width = sum(self._get_key_width(char) + config.KEY_MARGIN for char in row_chars) - config.KEY_MARGIN
            current_x = (self.screen_width - total_row_width) / 2 # Usar self.screen_width

            for char_code in row_chars:
                key_action_char = char_code; key_display_text = char_code
                is_special = False; current_key_width = self._get_key_width(char_code)
                if char_code == 'BACKSPACE': key_display_text = 'Borrar'; is_special = True; key_action_char = 'Borrar'
                elif char_code == 'ENTER': key_display_text = 'Enter'; is_special = True; key_action_char = 'Enter'
                elif char_code == 'CAPS': key_display_text = 'Mayús'; is_special = True; key_action_char = 'Mayús'
                elif char_code == 'SHIFT': key_display_text = 'Shift'; is_special = True; key_action_char = 'Shift'
                elif char_code == 'ESPACIO': key_display_text = 'ESPACIO'; is_special = True; key_action_char = ' '
                
                key_obj = Key(key_action_char, current_x, start_y_absolute + row_idx * key_full_height,
                              current_key_width, config.KEY_HEIGHT, self.font, is_special)
                key_obj.display_char = key_display_text
                self.keys.append(key_obj)
                current_x += current_key_width + config.KEY_MARGIN
    
    def _calculate_bounding_rect(self):
        if not self.keys: return pygame.Rect(0,0,0,0)
        min_x = min(key.rect.left for key in self.keys)
        max_x = max(key.rect.right for key in self.keys)
        min_y = min(key.rect.top for key in self.keys)
        max_y = max(key.rect.bottom for key in self.keys)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def get_bounding_rect(self): # Devuelve el rect solo de las teclas
        return self.bounding_rect

    def handle_input(self, key_obj, current_text):
        # ... (Sin cambios) ...
        key_char_action = key_obj.char
        if key_char_action == 'Borrar': return current_text[:-1]
        elif key_char_action == 'Enter': return current_text + '\n'
        elif key_char_action == 'Mayús': self.caps_lock_on = not self.caps_lock_on; return current_text
        elif key_char_action == 'Shift': self.caps_lock_on = not self.caps_lock_on; return current_text
        elif key_char_action == ' ': return current_text + ' '
        else:
            char_to_add = key_char_action
            if len(char_to_add) == 1:
                if self.caps_lock_on: char_to_add = char_to_add.upper()
                else: char_to_add = char_to_add.lower()
            return current_text + char_to_add

    def get_key_at_gaze(self, gaze_pos):
        # ... (Sin cambios) ...
        if not gaze_pos: return None
        for key in self.keys:
            if key.is_gazed(gaze_pos): return key
        return None

    def update_hover_state(self, gazed_key_obj):
        # ... (Sin cambios) ...
        for key in self.keys: key.is_hovered = (key == gazed_key_obj)

    def draw(self, screen):
        # ... (Sin cambios) ...
        for key in self.keys: key.draw(screen)