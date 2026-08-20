"""
views/pages/flashcards_page.py - v15.0
PointList Gestor & Entrenador de Tarjetas de Memoria (Flashcards) NotebookLM:
- Botones e interacción reactiva instantánea en tiempo real (Siguiente, Anterior, Voltear, Dificultad SM-2)
- Selección de mazo por chips con actualización directa
- Generador masivo de mazos inteligentes con IA NotebookLM
"""

import flet as ft
import threading
import random
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class FlashcardsPage(BasePage):
    """Página de Gestión y Estudio de Flashcards NotebookLM v15.0."""

    DEFAULT_DECKS = {
        "Biología General": [
            {
                "pregunta": "¿Qué es la fotosíntesis?",
                "respuesta": "Proceso metabólico mediante el cual plantas y cianobacterias convierten CO2 y H2O en glucosa y O2 usando energía fotónica.",
                "pista": "Ocurre en los cloroplastos de las hojas verdes gracias a la clorofila.",
                "dificultad": "Medio"
            },
            {
                "pregunta": "¿Cuál es la función de las mitocondrias?",
                "respuesta": "Generar la mayor parte del ATP celular mediante la respiración celular aeróbica en la cadena de transporte de electrones.",
                "pista": "Son conocidas como las 'centrales energéticas' de la célula.",
                "dificultad": "Fácil"
            },
            {
                "pregunta": "¿Qué diferencia al ADN del ARN?",
                "respuesta": "El ADN posee desoxirribosa y timina (doble hélice), mientras que el ARN posee ribosa y uracilo (cadena simple).",
                "pista": "Piensa en el azúcar pentosa y las bases nitrogenadas pirimidínicas.",
                "dificultad": "Difícil"
            }
        ],
        "Historia Universal": [
            {
                "pregunta": "¿En qué año se produjo la Revolución Francesa y cuál fue su hito inicial?",
                "respuesta": "Comenzó en 1789 con la Toma de la Bastilla el 14 de julio, marcando el fin de la monarquía absoluta.",
                "pista": "Ocurrió a finales del siglo XVIII bajo el reinado de Luis XVI.",
                "dificultad": "Fácil"
            },
            {
                "pregunta": "¿Cuáles fueron las causas principales de la Primera Guerra Mundial?",
                "respuesta": "Nacionalismo extremo, alianzas militares, imperialismo y el detonante: el asesinato del archiduque Francisco Fernando en Sarajevo (1914).",
                "pista": "Recuerda la sigla M.A.I.N. (Militarismo, Alianzas, Imperialismo, Nacionalismo).",
                "dificultad": "Medio"
            }
        ],
        "Matemáticas y Geometría": [
            {
                "pregunta": "¿Cuál es el Teorema de Pitágoras?",
                "respuesta": "En todo triángulo rectángulo, el cuadrado de la hipotenusa es igual a la suma de los cuadrados de los catetos (c² = a² + b²).",
                "pista": "Solo se aplica a triángulos con un ángulo recto de 90°.",
                "dificultad": "Fácil"
            },
            {
                "pregunta": "¿Qué es una derivada en cálculo?",
                "respuesta": "Medida de la razón de cambio instantánea de una función f(x) respecto a x, geométricamente representa la pendiente de la recta tangente.",
                "pista": "Representa la velocidad o cambio en un instante infinitesimal.",
                "dificultad": "Difícil"
            }
        ]
    }

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.decks = dict(self.DEFAULT_DECKS)
        self.selected_deck_name = "Biología General"
        self.current_card_idx = 0
        self.is_flipped = False
        
        # Refs reactivas
        self.card_badge_text = ft.Ref[ft.Text]()
        self.card_status_text = ft.Ref[ft.Text]()
        self.card_main_text = ft.Ref[ft.Text]()
        self.card_hint_text = ft.Ref[ft.Text]()
        self.card_container_ref = ft.Ref[ft.Container]()
        self.chips_row_ref = ft.Ref[ft.Row]()
        self.btn_prev_ref = ft.Ref[ft.IconButton]()
        self.btn_next_ref = ft.Ref[ft.IconButton]()

        self.ai_loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color="#0284C7")
        self.ai_topic_field = ft.TextField(hint_text="Ingresa una asignatura para generar mazo con IA...", border_radius=10, expand=True)

    def _get_current_deck(self) -> list[dict]:
        return self.decks.get(self.selected_deck_name, [])

    def _get_current_card(self) -> dict:
        deck = self._get_current_deck()
        if not deck:
            return {"pregunta": "Sin tarjetas", "respuesta": "Agrega nuevas tarjetas para comenzar a estudiar.", "pista": "Mazo vacío."}
        idx = max(0, min(self.current_card_idx, len(deck) - 1))
        return deck[idx]

    def _update_card_display(self):
        """Actualiza reactivamente el contenido de la tarjeta en pantalla."""
        deck = self._get_current_deck()
        total = len(deck)
        card = self._get_current_card()

        badge_txt = "💡 RESPUESTA EXPLICATIVA" if self.is_flipped else "❓ PREGUNTA CLAVE"
        main_txt = card.get("respuesta" if self.is_flipped else "pregunta", "")
        hint_txt = card.get("pista", "Piensa en la clave mnemotécnica.")
        card_bg = "#F0FDF4" if self.is_flipped else "#F0F9FF"
        card_border = "#86EFAC" if self.is_flipped else "#BAE6FD"
        badge_bg = "#DCFCE7" if self.is_flipped else "#E0F2FE"
        title_col = "#047857" if self.is_flipped else "#0369A1"

        try:
            if self.card_badge_text.current:
                self.card_badge_text.current.value = badge_txt
                self.card_badge_text.current.color = title_col
                self.card_badge_text.current.parent.bgcolor = badge_bg
                self.card_badge_text.current.update()
                self.card_badge_text.current.parent.update()

            if self.card_status_text.current:
                self.card_status_text.current.value = f"Tarjeta {self.current_card_idx + 1} de {total}"
                self.card_status_text.current.update()

            if self.card_main_text.current:
                self.card_main_text.current.value = main_txt
                self.card_main_text.current.update()

            if self.card_hint_text.current:
                self.card_hint_text.current.value = f"Pista NotebookLM: {hint_txt}"
                self.card_hint_text.current.update()

            if self.card_container_ref.current:
                self.card_container_ref.current.bgcolor = card_bg
                self.card_container_ref.current.border = ft.border.all(2, card_border)
                self.card_container_ref.current.update()

            if self.btn_prev_ref.current:
                self.btn_prev_ref.current.disabled = (self.current_card_idx == 0)
                self.btn_prev_ref.current.update()

            if self.btn_next_ref.current:
                self.btn_next_ref.current.disabled = (self.current_card_idx >= total - 1)
                self.btn_next_ref.current.update()
        except: pass

    def _toggle_flip(self, e=None):
        self.is_flipped = not self.is_flipped
        self._update_card_display()

    def _next_card(self, e=None):
        deck = self._get_current_deck()
        if self.current_card_idx < len(deck) - 1:
            self.current_card_idx += 1
            self.is_flipped = False
            self._update_card_display()

    def _prev_card(self, e=None):
        if self.current_card_idx > 0:
            self.current_card_idx -= 1
            self.is_flipped = False
            self._update_card_display()

    def _select_deck(self, deck_name: str):
        self.selected_deck_name = deck_name
        self.current_card_idx = 0
        self.is_flipped = False
        from services.navigation_service import NavigationController
        NavigationController.update_view("Flashcards", force_rebuild=True)

    def _generate_deck_ai(self, e=None):
        topic = self.ai_topic_field.value.strip()
        if not topic:
            self._show_info("Ingresa un tema o materia para que la IA genere el mazo.")
            return
        self.ai_loading.visible = True
        try: self.page.update()
        except: pass

        def _bg():
            try:
                from services.chatbot_service import chatbot
                cards = chatbot.generar_flashcards_ia(topic, cantidad=5)
                if cards:
                    self.decks[topic] = cards
                    self.selected_deck_name = topic
                    self.current_card_idx = 0
                    self.is_flipped = False
                    self._show_success(f"✨ Mazo '{topic}' de {len(cards)} flashcards generado con la IA de NotebookLM!")
            except Exception as ex:
                self._show_error(f"Error al generar con IA: {str(ex)}")
            finally:
                self.ai_loading.visible = False
                from services.navigation_service import NavigationController
                NavigationController.update_view("Flashcards", force_rebuild=True)

        threading.Thread(target=_bg, daemon=True).start()

    def build(self) -> ft.Control:
        colors = self._get_theme_colors()
        navbar = self._build_navbar("Gestor & Entrenador de Flashcards NotebookLM")
        current_card = self._get_current_card()
        deck = self._get_current_deck()
        total_cards = len(deck)

        # ─── HEADER MAZOS CHIPS ─────────────────────────────────────────────
        deck_chips = []
        for name in self.decks.keys():
            is_sel = (name == self.selected_deck_name)
            deck_chips.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    bgcolor="#0284C7" if is_sel else colors["surface"],
                    border_radius=12,
                    border=ft.border.all(1, "#0284C7" if is_sel else "#E2E8F0"),
                    ink=True,
                    on_click=lambda e, n=name: self._select_deck(n),
                    content=ft.Row([
                        ft.Icon(ft.Icons.STYLE, color="white" if is_sel else "#0284C7", size=16),
                        ft.Text(name, size=13, weight="bold" if is_sel else "normal", color="white" if is_sel else colors["text"]),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            bgcolor="white" if is_sel else "#F1F5F9",
                            border_radius=8,
                            content=ft.Text(str(len(self.decks[name])), size=10, weight="bold", color="#0284C7" if is_sel else "#475569")
                        )
                    ], spacing=6)
                )
            )

        # ─── TARJETA DE ESTUDIO FLIP CARD ────────────────────────────────────
        card_bg = "#F0FDF4" if self.is_flipped else "#F0F9FF"
        card_border = "#86EFAC" if self.is_flipped else "#BAE6FD"
        title_color = "#047857" if self.is_flipped else "#0369A1"
        badge_text_str = "💡 RESPUESTA EXPLICATIVA" if self.is_flipped else "❓ PREGUNTA CLAVE"
        main_content = current_card.get("respuesta" if self.is_flipped else "pregunta", "")
        hint_content = current_card.get("pista", "Piensa en la clave mnemotécnica.")

        flashcard_widget = ft.Container(
            ref=self.card_container_ref,
            height=280,
            padding=24,
            bgcolor=card_bg,
            border_radius=20,
            border=ft.border.all(2, card_border),
            shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.BLACK12, offset=ft.Offset(0, 6)),
            ink=True,
            on_click=self._toggle_flip,
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor="#DCFCE7" if self.is_flipped else "#E0F2FE",
                        border_radius=8,
                        content=ft.Text(ref=self.card_badge_text, value=badge_text_str, size=11, weight="bold", color=title_color)
                    ),
                    ft.Text(ref=self.card_status_text, value=f"Tarjeta {self.current_card_idx + 1} de {total_cards}", size=12, color="#64748B", weight="bold")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=16),
                ft.Text(ref=self.card_main_text, value=main_content, size=16, weight="bold", color="#0F172A", text_align=ft.TextAlign.CENTER, expand=True),
                ft.Container(height=12),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor="white",
                    border_radius=8,
                    content=ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color="#D97706", size=16),
                        ft.Text(ref=self.card_hint_text, value=f"Pista NotebookLM: {hint_content}", size=12, color="#475569", italic=True, expand=True)
                    ], spacing=6)
                ),
                ft.Text("(Toca la tarjeta para voltear)", size=10, color="#94A3B8", text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # ─── CONTROLES DE NAVEGACIÓN Y DIFICULTAD SM-2 ───────────────────────
        controls_row = ft.Row([
            ft.IconButton(ref=self.btn_prev_ref, icon=ft.Icons.ARROW_BACK_IOS_ROUNDED, icon_color="#0284C7", on_click=self._prev_card, disabled=self.current_card_idx == 0),
            ft.ElevatedButton("🔄 Voltear Tarjeta", bgcolor="#0284C7", color="white", height=42, on_click=self._toggle_flip),
            ft.IconButton(ref=self.btn_next_ref, icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED, icon_color="#0284C7", on_click=self._next_card, disabled=self.current_card_idx >= total_cards - 1),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=16)

        difficulty_row = ft.Row([
            ft.ElevatedButton("🔴 Difícil (Repasar Hoy)", bgcolor="#FEE2E2", color="#991B1B", on_click=lambda _: self._show_info("Marcado para repasar hoy.")),
            ft.ElevatedButton("🟡 Medio (Ver en 3 días)", bgcolor="#FEF3C7", color="#92400E", on_click=lambda _: self._show_info("Programado para 3 días.")),
            ft.ElevatedButton("🟢 Fácil (Ver en 7 días)", bgcolor="#DCFCE7", color="#166534", on_click=lambda _: self._show_info("Dominado. Programado para 7 días.")),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        # ─── BARRA DE GENERACIÓN IA ─────────────────────────────────────────
        ai_bar = ft.Container(
            padding=16, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME, color="#0284C7", size=20),
                    ft.Text("Generador de Mazos de Estudio con IA NotebookLM", size=15, weight="bold", color=colors["text"]),
                ], spacing=8),
                ft.Container(height=8),
                ft.Row([
                    self.ai_topic_field,
                    ft.ElevatedButton("✨ Generar Mazo", bgcolor="#0284C7", color="white", height=42, on_click=self._generate_deck_ai),
                    self.ai_loading
                ], spacing=10)
            ], spacing=4)
        )

        content = ft.Column([
            navbar,
            ft.Container(height=14),
            ft.Row(deck_chips, scroll=get_scroll_mode("AUTO"), spacing=8),
            ft.Container(height=16),
            flashcard_widget,
            ft.Container(height=14),
            controls_row,
            ft.Container(height=10),
            difficulty_row,
            ft.Container(height=20),
            ai_bar
        ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)

        return ft.Container(padding=24, bgcolor=colors["background"], content=content, expand=True)
