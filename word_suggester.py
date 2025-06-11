# word_suggester.py
import config

class WordSuggester:
    def __init__(self, filepath=config.SPANISH_WORDS_FILE):
        self.words = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and len(word) > 1 and word.isalpha():
                        self.words.append(word)
            if self.words:
                 print(f"Cargadas {len(self.words)} palabras desde {filepath}")
            else:
                 print(f"Advertencia: No se cargaron palabras válidas desde {filepath}")
        except FileNotFoundError:
            print(f"Advertencia: Archivo de palabras '{filepath}' no encontrado. Las sugerencias no funcionarán.")
        except Exception as e:
            print(f"Error cargando palabras: {e}")

    def get_suggestions(self, current_word_prefix, count=config.SUGGESTION_COUNT):
        if not current_word_prefix or not self.words:
            return []

        current_word_prefix = current_word_prefix.lower()
        suggestions = [word for word in self.words if word.startswith(current_word_prefix)]

        suggestions.sort(key=len)
        return suggestions[:count]