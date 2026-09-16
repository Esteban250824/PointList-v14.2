"""
pages/techniques_page.py - v14.0
PointList Técnicas de Estudio Rediseñado:
- Fase 1: Catálogo visual de técnicas de estudio
- Fase 2: Vista de Detalle y Guía metodológica completa para TODAS las técnicas
- Fase 3: Aplicación Práctica Interactivas para cada técnica (Pomodoro, Mapas Mentales, Método Cornell, Repaso Espaciado, Feynman, Tarjetas de Memoria)
"""

import flet as ft
import threading
import time
import os
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class StudyMethodsPage(BasePage):
    """Página de técnicas rediseñada v14.0 con Fase 2 refinada y Fase 3 interactiva completa."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        self._db = db
        self._techniques: list = []
        self._selected_category = "Todos"
        self._list_ref = ft.Ref[ft.Column]()
        self._current_view = "list"  # list, detail, apply
        
        # Variables del temporizador Pomodoro
        self._timer_running = False
        self._timer_paused = False
        self._remaining_seconds = 1500  # 25 minutos por defecto
        self._total_seconds = 1500
        self._timer_thread = None
        self._timer_display = ft.Ref[ft.Text]()
        self._start_btn = ft.Ref[ft.ElevatedButton]()
        self._pause_btn = ft.Ref[ft.ElevatedButton]()
        self._reset_btn = ft.Ref[ft.ElevatedButton]()
        self._time_input = ft.Ref[ft.TextField]()
        
        # Tareas personalizables
        self._tasks: list = []
        self._task_input = ft.Ref[ft.TextField]()
        self._tasks_column = ft.Ref[ft.Column]()

        # Procedimiento personalizable Pomodoro
        self._pomodoro_steps = [
            {"id": 0, "title": "1. Elige una tarea", "desc": "Selecciona la tarea específica en la que te vas a enfocar.", "completed": False},
            {"id": 1, "title": "2. Elimina distracciones", "desc": "Silencia notificaciones, cierra pestañas secundarias y evita interrupciones.", "completed": False},
            {"id": 2, "title": "3. Trabaja durante 25 minutos", "desc": "Enfócate por completo sin hacer multitarea hasta que suene la alarma.", "completed": False},
            {"id": 3, "title": "4. Descansa 5 minutos", "desc": "Párate, estírate, hidrátate y despeja tu mente.", "completed": False},
            {"id": 4, "title": "5. Replicar el ciclo", "desc": "Después de 4 pomodoros completados, toma un descanso largo de 15 a 30 minutos.", "completed": False},
        ]
        self._new_step_title = ft.Ref[ft.TextField]()
        self._new_step_desc = ft.Ref[ft.TextField]()
        self._steps_list_column = ft.Column(spacing=10)

    def _render_view(self, content: ft.Control):
        """Actualiza la vista sin romper el contenedor de navegación."""
        from services.navigation_service import NavigationController
        if NavigationController.content_container:
            NavigationController.content_container.content = content
            try:
                self.page.update()
            except:
                pass
        else:
            self.page.controls.clear()
            self.page.add(content)
            try:
                self.page.update()
            except:
                pass

    def _load_techniques(self):
        """Carga técnicas desde BD o caché y asegura todas las herramientas incluyendo Flashcards NotebookLM."""
        from services.navigation_service import NavigationController
        raw_list = NavigationController.cache.get("tecnicas") or self._db.obtener_tecnicas() or []
        
        # Eliminar herramientas desintegradas como generador de imágenes
        self._techniques = [t for t in raw_list if not any(k in t.get("titulo", "").lower() for k in ["imagen", "pointbit ia", "diagrama ia"])]
        
        titles = [t.get("titulo", "").lower() for t in self._techniques]
        
        # Asegurar Tarjetas de Memoria (Flashcards) NotebookLM
        if not any("flashcard" in t or "tarjeta" in t for t in titles):
            self._techniques.append({
                "id": "flashcards_notebooklm",
                "titulo": "Tarjetas de Memoria (Flashcards) NotebookLM",
                "categoria": "Recuerdo Activo & IA",
                "descripcion": "Crea y practica con mazos inteligentes de preguntas, respuestas y pistas mnemotécnicas impulsados por IA.",
            })

        # Asegurar Método Cornell
        if not any("cornell" in t for t in titles):
            self._techniques.append({
                "id": "cornell_notes",
                "titulo": "Método de Notas Cornell",
                "categoria": "Apuntes & Análisis",
                "descripcion": "Organiza tus apuntes de clase en 3 columnas clave: Pistas, Notas principales y Resumen final.",
            })

        NavigationController.cache["tecnicas"] = self._techniques

    def _technique_icon(self, title: str):
        title_lower = (title or "").lower()
        if "pomodoro" in title_lower:
            return ft.Icons.TIMER_OUTLINED
        if "mapa" in title_lower:
            return ft.Icons.ACCOUNT_TREE_OUTLINED
        if "feynman" in title_lower:
            return ft.Icons.PSYCHOLOGY_OUTLINED
        if "smart" in title_lower or "cornell" in title_lower:
            return ft.Icons.LIGHTBULB_OUTLINE
        if "sq3r" in title_lower or "lectura" in title_lower:
            return ft.Icons.MENU_BOOK_OUTLINED
        if "repet" in title_lower or "espaciado" in title_lower:
            return ft.Icons.AUTORENEW
        if "tarjeta" in title_lower or "flashcard" in title_lower:
            return ft.Icons.COPY_OUTLINED
        return ft.Icons.SCHOOL_OUTLINED

    def _get_technique_info(self, title: str) -> dict:
        """Obtiene la metadata enriquecida para cada técnica."""
        title_lower = (title or "").lower()
        if "pomodoro" in title_lower:
            return {
                "key": "pomodoro",
                "title": self.translate("tech_pomodoro_detail_title"),
                "icon_color": "#EA580C",
                "icon_bg": "#FFEDD5",
                "icon": ft.Icons.TIMER_OUTLINED,
                "text_color": "#EA580C",
                "subtitle": self.translate("tech_pomodoro_subtitle"),
                "what_is": self.translate("tech_pomodoro_what_is"),
                "steps": [
                    self.translate("tech_pomodoro_step_1"),
                    self.translate("tech_pomodoro_step_2"),
                    self.translate("tech_pomodoro_step_3"),
                    self.translate("tech_pomodoro_step_4"),
                    self.translate("tech_pomodoro_step_5"),
                ],
                "how_steps": [
                    (ft.Icons.CONTENT_PASTE, self.translate("tech_pomodoro_how_1_title"), self.translate("tech_pomodoro_how_1_desc")),
                    (ft.Icons.SCHEDULE, self.translate("tech_pomodoro_how_2_title"), self.translate("tech_pomodoro_how_2_desc")),
                    (ft.Icons.ADS_CLICK, self.translate("tech_pomodoro_how_3_title"), self.translate("tech_pomodoro_how_3_desc")),
                    (ft.Icons.LOCAL_CAFE_OUTLINED, self.translate("tech_pomodoro_how_4_title"), self.translate("tech_pomodoro_how_4_desc")),
                ],
                "bullets": [
                    self.translate("tech_pomodoro_bullet_focus"),
                    self.translate("tech_pomodoro_bullet_fatigue"),
                    self.translate("tech_pomodoro_bullet_recommended"),
                ],
            }
        elif "mapa" in title_lower:
            return {
                "key": "mindmap",
                "title": self.translate("tech_mindmap_title"),
                "icon_color": "#7C3AED",
                "icon_bg": "#F3E8FF",
                "icon": ft.Icons.ACCOUNT_TREE_OUTLINED,
                "text_color": "#7C3AED",
                "subtitle": self.translate("tech_mindmap_subtitle"),
                "what_is": self.translate("tech_mindmap_what_is"),
                "steps": [
                    self.translate("tech_mindmap_step_1"),
                    self.translate("tech_mindmap_step_2"),
                    self.translate("tech_mindmap_step_3"),
                    self.translate("tech_mindmap_step_4"),
                    self.translate("tech_mindmap_step_5"),
                ],
                "bullets": [
                    self.translate("tech_mindmap_bullet_1"),
                    self.translate("tech_mindmap_bullet_2"),
                    self.translate("tech_mindmap_bullet_3"),
                ],
            }
        elif "cornell" in title_lower:
            return {
                "key": "cornell",
                "icon_color": "#0D9488",
                "icon_bg": "#CCFBF1",
                "icon": ft.Icons.ASSIGNMENT_OUTLINED,
                "text_color": "#0D9488",
                "subtitle": "Sistema estructurado de toma de apuntes dividido en Pistas, Notas y Resumen.",
                "what_is": "El Método Cornell divide la página en tres secciones: notas principales durante la clase, columna izquierda de pistas o preguntas clave, y un resumen final de 2 a 3 oraciones en el pie de página.",
                "steps": [
                    "Divide tu hoja en 3 secciones (Pistas, Notas y Resumen).",
                    "Toma notas concisas en el área principal durante la lectura o clase.",
                    "Formula preguntas clave en la columna izquierda.",
                    "Escribe un resumen sintetizado de 3 líneas al final.",
                    "Cubre el área de notas y ponte a prueba respondiendo las pistas."
                ],
                "bullets": ["Facilita la autoevaluación", "Organización clara de apuntes", "Recomendado: Durante y post clase"]
            }
        elif "espaciado" in title_lower or "repet" in title_lower:
            return {
                "key": "spaced",
                "title": self.translate("tech_spaced_title"),
                "icon_color": "#4F46E5",
                "icon_bg": "#EEF2FF",
                "icon": ft.Icons.AUTORENEW,
                "text_color": "#4F46E5",
                "subtitle": self.translate("tech_spaced_subtitle"),
                "what_is": self.translate("tech_spaced_what_is"),
                "steps": [
                    self.translate("tech_spaced_step_1"),
                    self.translate("tech_spaced_step_2"),
                    self.translate("tech_spaced_step_3"),
                    self.translate("tech_spaced_step_4"),
                    self.translate("tech_spaced_step_5"),
                ],
                "bullets": [
                    self.translate("tech_spaced_bullet_1"),
                    self.translate("tech_spaced_bullet_2"),
                    self.translate("tech_spaced_bullet_3"),
                ],
            }
        elif "feynman" in title_lower:
            return {
                "key": "feynman",
                "title": self.translate("tech_feynman_title"),
                "icon_color": "#9A3412",
                "icon_bg": "#FBEBDF",
                "icon": ft.Icons.PSYCHOLOGY_OUTLINED,
                "text_color": "#9A3412",
                "subtitle": self.translate("tech_feynman_subtitle"),
                "what_is": self.translate("tech_feynman_what_is"),
                "steps": [
                    self.translate("tech_feynman_step_1"),
                    self.translate("tech_feynman_step_2"),
                    self.translate("tech_feynman_step_3"),
                    self.translate("tech_feynman_step_4"),
                    self.translate("tech_feynman_step_5"),
                ],
                "bullets": [
                    self.translate("tech_feynman_bullet_1"),
                    self.translate("tech_feynman_bullet_2"),
                    self.translate("tech_feynman_bullet_3"),
                ],
            }
        elif "smart" in title_lower:
            return {
                "key": "smart",
                "title": self.translate("tech_smart_title"),
                "icon_color": "#0284C7",
                "icon_bg": "#E0F2FE",
                "icon": ft.Icons.LIGHTBULB_OUTLINE,
                "text_color": "#0284C7",
                "subtitle": self.translate("tech_smart_subtitle"),
                "what_is": self.translate("tech_smart_what_is"),
                "steps": [
                    self.translate("tech_smart_step_1"),
                    self.translate("tech_smart_step_2"),
                    self.translate("tech_smart_step_3"),
                    self.translate("tech_smart_step_4"),
                    self.translate("tech_smart_step_5"),
                ],
                "bullets": [
                    self.translate("tech_smart_bullet_1"),
                    self.translate("tech_smart_bullet_2"),
                    self.translate("tech_smart_bullet_3"),
                ],
            }
        elif "tarjeta" in title_lower or "flashcard" in title_lower or "memoria" in title_lower:
            return {
                "key": "flashcards",
                "icon_color": "#0284C7",
                "icon_bg": "#E0F2FE",
                "icon": ft.Icons.COPY_OUTLINED,
                "text_color": "#0284C7",
                "subtitle": "Tarjetas de recuerdo activo (Flashcards) con IA estilo NotebookLM.",
                "what_is": "Técnica de recuerdo activo (Active Recall) donde la IA genera tarjetas interactivas de preguntas, respuestas explicativas y pistas mnemotécnicas.",
                "steps": [
                    "Ingresa el tema o asignatura que estás estudiando.",
                    "Haz clic en 'Generar Mazo con IA'.",
                    "Lee la pregunta e intenta recordar la respuesta antes de voltear.",
                    "Usa las Pistas NotebookLM si necesitas una ayuda mnemotécnica.",
                    "Ponte a prueba repitiendo el mazo regularmente."
                ],
                "bullets": ["Recuerdo activo con IA", "Pistas mnemotécnicas", "Recomendado: Diario / Pre-examen"]
            }
        elif "sq3r" in title_lower or "lectura" in title_lower:
            return {
                "key": "sq3r",
                "title": self.translate("tech_sq3r_title"),
                "icon_color": "#16A34A",
                "icon_bg": "#DCFCE7",
                "icon": ft.Icons.MENU_BOOK_OUTLINED,
                "text_color": "#16A34A",
                "subtitle": self.translate("tech_sq3r_subtitle"),
                "what_is": self.translate("tech_sq3r_what_is"),
                "steps": [
                    self.translate("tech_sq3r_step_1"),
                    self.translate("tech_sq3r_step_2"),
                    self.translate("tech_sq3r_step_3"),
                    self.translate("tech_sq3r_step_4"),
                    self.translate("tech_sq3r_step_5"),
                ],
                "bullets": [
                    self.translate("tech_sq3r_bullet_1"),
                    self.translate("tech_sq3r_bullet_2"),
                    self.translate("tech_sq3r_bullet_3"),
                ],
            }

        return {
            "key": "generic",
            "icon_color": "#16A34A",
            "icon_bg": "#DCFCE7",
            "icon": ft.Icons.SCHOOL_OUTLINED,
            "text_color": "#16A34A",
            "subtitle": "Método efectivo para organizar el estudio y optimizar tu rendimiento escolar.",
            "what_is": "Un método estructurado que combina preparación, enfoque activo y autoevaluación para absorber conocimientos con claridad.",
            "steps": [
                "Define el objetivo exacto de tu sesión.",
                "Prepara tus materiales sin elementos distractores.",
                "Aplica el método de estudio de forma enfocada.",
                "Evalúa tu progreso y haz anotaciones clave.",
                "Planifica la siguiente sesión de refuerzo."
            ],
            "bullets": ["Técnica de aprendizaje activo", "Mejora el rendimiento", "Recomendado: 20-30 min"]
        }

    def _build_technique_card(self, tech: dict) -> ft.Container:
        colors = self._get_theme_colors()
        is_dark = self.page and self.page.theme_mode == ft.ThemeMode.DARK
        title = tech.get("titulo", "")
        info = self._get_technique_info(title)
        display_title = info.get("title", title)
        display_description = info["subtitle"] if info.get("key") != "generic" else tech.get("descripcion", info["subtitle"])

        def _show_detail(e):
            self._current_view = "detail"
            self._show_technique_detail(tech)

        bullet_controls = [
            ft.Text(b, size=11, color=colors["text_muted"], weight="w500") for b in info["bullets"]
        ]

        card_header = ft.Row([
            ft.Container(
                width=52, height=52,
                bgcolor=info["icon_bg"],
                border_radius=12,
                alignment=ft.alignment.center,
                content=ft.Icon(info["icon"], color=info["icon_color"], size=24)
            ),
            ft.Container(width=10),
            ft.Column([
                ft.Text(display_title, size=16, weight="bold", color=colors["text"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(display_description, size=11, color=colors["text_muted"], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ], expand=True, spacing=2),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        card_footer = ft.Container(
            border=ft.border.only(top=ft.border.BorderSide(1, colors["border"])),
            padding=ft.padding.only(top=10, bottom=2),
            alignment=ft.alignment.center,
            content=ft.Row([
                ft.Text(self.translate("techniques_view_detail"), size=13, weight="bold", color=info["text_color"]),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=info["text_color"])
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            on_click=_show_detail,
            ink=True,
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=18, vertical=18),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=-2, color=ft.Colors.with_opacity(0.18 if is_dark else 0.06, ft.Colors.BLACK)),
            on_click=_show_detail,
            ink=True,
            content=ft.Column([
                card_header,
                ft.Container(height=12),
                ft.Column(bullet_controls, spacing=4),
                ft.Container(height=14),
                card_footer
            ], spacing=0),
        )

    def _show_technique_detail(self, tech: dict):
        """Muestra la fase 2 con diseño diferenciado para Pomodoro y técnicas generales."""
        colors = self._get_theme_colors()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        raw_title = tech.get("titulo", "Técnica")
        info = self._get_technique_info(raw_title)
        title = info.get("title", raw_title)
        navbar = self._build_navbar(title)
        is_pomodoro = info["key"] == "pomodoro"
        card_bg = colors["surface"]
        border_color = colors["border"]
        muted = colors["text_secondary"]
        page_bg = colors["background"]

        def _apply_technique(e):
            self._current_view = "apply"
            self._show_technique_apply(tech)

        def _back(e):
            self._current_view = "list"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")

        def _step_icon(icon, index, heading, text):
            return ft.Column(
                [
                    ft.Container(
                        width=34,
                        height=34,
                        border_radius=17,
                        bgcolor="#57E249",
                        alignment=ft.alignment.center,
                        content=ft.Text(str(index), color="white", weight="bold", size=14),
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        width=88,
                        height=88,
                        border_radius=44,
                        bgcolor="#D4FFD8" if not is_dark else "#14532D",
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, size=42, color="#000000" if not is_dark else "#F8FAFC"),
                    ),
                    ft.Container(height=14),
                    ft.Text(heading, size=13, weight="bold", color=colors["text"], text_align=ft.TextAlign.CENTER),
                    ft.Text(text, size=12, color=muted, text_align=ft.TextAlign.CENTER, width=150),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            )

        def _benefit_card(text):
            return ft.Container(
                height=84,
                padding=ft.padding.symmetric(horizontal=18),
                border_radius=12,
                bgcolor="#ECFFE7" if not is_dark else "#12351E",
                border=ft.border.all(1, "#A7DDA0" if not is_dark else "#2F6B3B"),
                content=ft.Row(
                    [
                        ft.Container(
                            width=48,
                            height=48,
                            border_radius=24,
                            bgcolor="#B8FFC1" if not is_dark else "#166534",
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.Icons.CHECK, color="#22C55E", size=30),
                        ),
                        ft.Container(width=14),
                        ft.Text(text, size=16, weight="bold", color=muted, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        def _procedure_row(idx, step):
            if " - " in step:
                prefix, body = step.split(" - ", 1)
            elif ":" in step:
                prefix, body = step.split(":", 1)
                prefix = f"{prefix}:"
            else:
                prefix, body = f"Paso {idx}:", step
            return ft.Container(
                height=56,
                padding=ft.padding.symmetric(horizontal=16),
                border_radius=10,
                bgcolor=card_bg,
                border=ft.border.all(1, "#9CA3AF" if not is_dark else "#475569"),
                content=ft.Row(
                    [
                        ft.Container(
                            width=46,
                            height=46,
                            border_radius=23,
                            bgcolor="#0A469D",
                            alignment=ft.alignment.center,
                            content=ft.Text(str(idx), color="white", size=22, weight="bold"),
                        ),
                        ft.Container(width=16),
                        ft.Text(prefix, size=15, color=colors["text"], weight="bold"),
                        ft.Text(body.strip(), size=15, color=muted, weight="bold", expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

        if is_pomodoro:
            hero_card = ft.Container(
                padding=ft.padding.symmetric(horizontal=42, vertical=48),
                bgcolor=card_bg,
                border_radius=22,
                border=ft.border.all(1, border_color),
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    width=190,
                                    height=190,
                                    border_radius=14,
                                    bgcolor="#EBFFED" if not is_dark else "#12351E",
                                    alignment=ft.alignment.center,
                                    content=ft.Icon(ft.Icons.ACCESS_TIME, size=150, color="#000000" if not is_dark else "#F8FAFC"),
                                ),
                                ft.Container(width=28),
                                ft.Column(
                                    [
                                        ft.Text(title, size=44, weight="bold", color=colors["text"]),
                                        ft.Container(height=18),
                                        ft.Text(info["subtitle"], size=15, color=colors["text"], width=520),
                                        ft.Container(height=34),
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=12, vertical=7),
                                            border_radius=7,
                                            bgcolor="#CAFFD2" if not is_dark else "#14532D",
                                            content=ft.Row(
                                                [
                                                    ft.Icon(ft.Icons.AUTO_AWESOME, color="#57E249", size=22),
                                                    ft.Text(info["bullets"][1], size=14, color="#16A34A", weight="w600"),
                                                ],
                                                spacing=8,
                                            ),
                                        ),
                                        ft.Container(height=18),
                                        ft.ElevatedButton(
                                            f"{self.translate('tech_apply')}  →",
                                            bgcolor="#57E249",
                                            color="white",
                                            height=52,
                                            width=260,
                                            style=ft.ButtonStyle(
                                                shape=ft.RoundedRectangleBorder(radius=14),
                                                text_style=ft.TextStyle(size=18, weight="bold"),
                                            ),
                                            on_click=_apply_technique,
                                        ),
                                    ],
                                    spacing=0,
                                    expand=True,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.VerticalDivider(width=34, color=border_color),
                        ft.Row(
                            [
                                ft.Container(width=64, height=64, border_radius=8, bgcolor="#EDFDF0" if not is_dark else "#12351E"),
                                ft.Container(width=14),
                                ft.Column(
                                    [
                                        ft.Text(self.translate("tech_what_is"), size=16, weight="bold", color=colors["text"]),
                                        ft.Text(info["what_is"], size=14, color=colors["text"], width=470),
                                    ],
                                    spacing=8,
                                    expand=True,
                                ),
                            ],
                            expand=True,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

            how_card = ft.Container(
                expand=2,
                padding=ft.padding.all(34),
                bgcolor=card_bg,
                border_radius=14,
                border=ft.border.all(1, border_color),
                content=ft.Column(
                    [
                        ft.Text(self.translate("tech_how_used"), size=30, weight="bold", color=colors["text"]),
                        ft.Container(height=24),
                        ft.Row(
                            [
                                _step_icon(icon, index, heading, text)
                                for index, (icon, heading, text) in enumerate(info["how_steps"], start=1)
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        ),
                    ],
                    spacing=0,
                ),
            )

            cycle_card = ft.Container(
                expand=1,
                padding=ft.padding.all(22),
                bgcolor="#0A2348",
                border_radius=14,
                content=ft.Column(
                    [
                        ft.Text(self.translate("tech_pomodoro_cycle_title"), size=18, weight="bold", color="white", text_align=ft.TextAlign.CENTER),
                        ft.Container(height=20),
                        ft.Row(
                            [
                                ft.Text(self.translate("tech_pomodoro_cycle_left"), color="white", size=12, text_align=ft.TextAlign.CENTER),
                                ft.Container(
                                    width=190,
                                    height=190,
                                    border_radius=95,
                                    bgcolor="#57E249",
                                    alignment=ft.alignment.center,
                                    content=ft.Container(
                                        width=84,
                                        height=84,
                                        border_radius=42,
                                        bgcolor="#0A2348",
                                        alignment=ft.alignment.center,
                                        content=ft.Icon(ft.Icons.AUTORENEW, color="white", size=44),
                                    ),
                                ),
                                ft.Text(self.translate("tech_pomodoro_cycle_right"), color="white", size=12, text_align=ft.TextAlign.CENTER),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=8),
                        ft.Text(self.translate("tech_pomodoro_cycle_bottom"), color="#57E249", size=12, weight="bold", text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

            bottom_bar = ft.Container(
                padding=ft.padding.symmetric(horizontal=34, vertical=22),
                bgcolor="#F3F6FC" if not is_dark else "#111827",
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=12, spread_radius=-4, color=ft.Colors.BLACK26),
                content=ft.Row(
                    [
                        ft.IconButton(ft.Icons.PLAY_ARROW, icon_color="#57E249", icon_size=42),
                        ft.Column(
                            [
                                ft.Text(self.translate("tech_video_title"), size=18, weight="bold", color=colors["text"]),
                                ft.Text(self.translate("tech_video_subtitle"), size=16, color=colors["text"]),
                            ],
                            spacing=2,
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            f"{self.translate('tech_apply')}  →",
                            bgcolor="#57E249",
                            color="white",
                            height=64,
                            width=320,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16), text_style=ft.TextStyle(size=24, weight="bold")),
                            on_click=_apply_technique,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )

            body = ft.Column(
                [
                    hero_card,
                    ft.Container(height=24),
                    ft.Row([how_card, ft.Container(width=20), cycle_card], vertical_alignment=ft.CrossAxisAlignment.STRETCH),
                    ft.Container(height=24),
                    bottom_bar,
                ],
                scroll=get_scroll_mode("AUTO"),
                expand=True,
                spacing=0,
            )
        else:
            benefits = info["bullets"][:3]
            while len(benefits) < 3:
                benefits.append("Mejora tu organización de estudio")

            header = ft.Row(
                [
                    ft.Container(
                        width=120,
                        height=100,
                        border_radius=14,
                        bgcolor="#E5E7EB" if not is_dark else "#334155",
                        alignment=ft.alignment.center,
                        content=ft.Icon(info["icon"], size=72, color="#0A469D"),
                    ),
                    ft.Container(width=24),
                    ft.Column(
                        [
                            ft.Text(title, size=44, weight="bold", color=colors["text"]),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=14, vertical=8),
                                border_radius=8,
                                bgcolor="#F0F0F4" if not is_dark else "#1E293B",
                                content=ft.Text(tech.get("categoria", "Recientes"), size=15, weight="bold", color="#5B4DFF"),
                            ),
                        ],
                        spacing=12,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

            about_card = ft.Container(
                expand=1,
                bgcolor=card_bg,
                border_radius=14,
                border=ft.border.all(1, border_color),
                content=ft.Column(
                    [
                        ft.Container(
                            padding=ft.padding.all(24),
                            content=ft.Column(
                                [
                                    ft.Text(self.translate("tech_what_is"), size=22, weight="bold", color=colors["text"]),
                                    ft.Container(height=28),
                                    ft.Text(info["what_is"], size=15, weight="bold", color=muted),
                                ],
                                spacing=0,
                            ),
                        ),
                        ft.Divider(height=1, color=border_color),
                        ft.Container(
                            padding=ft.padding.all(24),
                            content=ft.Column(
                                [
                                    ft.Text(self.translate("tech_key_benefits"), size=22, weight="bold", color=colors["text"]),
                                    ft.Container(height=22),
                                    ft.Column([_benefit_card(b) for b in benefits], spacing=24),
                                ],
                                spacing=0,
                            ),
                        ),
                    ],
                    spacing=0,
                ),
            )

            procedure_card = ft.Container(
                expand=1.4,
                bgcolor=card_bg,
                border_radius=14,
                border=ft.border.all(1, border_color),
                content=ft.Column(
                    [
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=24, vertical=22),
                            content=ft.Column(
                                [
                                    ft.Text(self.translate("tech_step_procedure"), size=22, weight="bold", color=colors["text"]),
                                    ft.Text(self.translate("tech_step_subtitle"), size=15, weight="bold", color=muted),
                                ],
                                spacing=2,
                            ),
                        ),
                        ft.Divider(height=1, color=border_color),
                        ft.Container(
                            padding=ft.padding.all(24),
                            content=ft.Column([_procedure_row(i, step) for i, step in enumerate(info["steps"], start=1)], spacing=26),
                        ),
                    ],
                    spacing=0,
                ),
            )

            body = ft.Column(
                [
                    ft.GestureDetector(
                        on_tap=_back,
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.ARROW_BACK, size=24, color="#0A2348" if not is_dark else "#F8FAFC"),
                                ft.Text(self.translate("tech_back_catalog"), size=24, weight="bold", color="#0A2348" if not is_dark else "#F8FAFC"),
                            ],
                            spacing=8,
                        ),
                    ),
                    ft.Container(height=32),
                    header,
                    ft.Container(height=30),
                    ft.Row([about_card, ft.Container(width=28), procedure_card], vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(height=26),
                    ft.Row(
                        [
                            ft.OutlinedButton(f"←  {self.translate('tech_back')}", width=150, height=44, on_click=_back),
                            ft.Container(expand=True),
                            ft.ElevatedButton(
                                f"{self.translate('tech_apply')}  →",
                                bgcolor="#0A469D",
                                color="white",
                                width=260,
                                height=48,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), text_style=ft.TextStyle(size=16, weight="bold")),
                                on_click=_apply_technique,
                            ),
                        ]
                    ),
                ],
                scroll=get_scroll_mode("AUTO"),
                expand=True,
                spacing=0,
            )

        detail_content = ft.Column(
            [
                navbar,
                ft.Container(
                    expand=True,
                    bgcolor=page_bg,
                    padding=ft.padding.symmetric(horizontal=46, vertical=34),
                    content=body,
                ),
            ],
            expand=True,
            spacing=0,
        )

        self._render_view(detail_content)

    # ─────────────────────────────────────────────────────────────────────────────
    # FUNCIONALIDADES INTERACTIVAS PARA FASE 3
    # ─────────────────────────────────────────────────────────────────────────────

    def _add_task(self, e):
        task_text = self._task_input.current.value.strip() if self._task_input.current else ""
        if not task_text: return
        task = {"id": len(self._tasks), "text": task_text, "completed": False}
        self._tasks.append(task)
        if self._task_input.current: self._task_input.current.value = ""
        self._refresh_tasks_list()

    def _toggle_task(self, task_id):
        for task in self._tasks:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
        self._refresh_tasks_list()

    def _delete_task(self, task_id):
        self._tasks = [t for t in self._tasks if t["id"] != task_id]
        self._refresh_tasks_list()

    def _refresh_tasks_list(self):
        if not self._tasks_column.current: return
        colors = self._get_theme_colors()
        task_controls = []
        for task in self._tasks:
            task_controls.append(
                ft.Row([
                    ft.Checkbox(value=task["completed"], on_change=lambda e, tid=task["id"]: self._toggle_task(tid)),
                    ft.Text(task["text"], size=13, color=colors["text_secondary"] if task["completed"] else colors["text"]),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, icon_size=16, on_click=lambda e, tid=task["id"]: self._delete_task(tid)),
                ], spacing=6)
            )
        try:
            self._tasks_column.current.controls = task_controls
            self._tasks_column.current.update()
        except: pass

    def _update_timer_display(self):
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        try:
            if self._timer_display.current:
                self._timer_display.current.value = time_str
                self._timer_display.current.update()
        except: pass

    def _run_timer(self):
        while self._timer_running and self._remaining_seconds > 0:
            if not self._timer_paused:
                self._remaining_seconds -= 1
                self._update_timer_display()
            time.sleep(1)
        if self._remaining_seconds == 0:
            self._timer_running = False
            try:
                if self._start_btn.current:
                    self._start_btn.current.text = "Iniciar"
                    self._start_btn.current.update()
            except: pass

    def _start_timer(self, e):
        if not self._timer_running:
            self._timer_running = True
            self._timer_paused = False
            try:
                if self._start_btn.current:
                    self._start_btn.current.text = "Pausar"
                    self._start_btn.current.update()
            except: pass
            self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
            self._timer_thread.start()

    def _pause_timer(self, e):
        if self._timer_running:
            self._timer_paused = not self._timer_paused
            try:
                if self._start_btn.current:
                    self._start_btn.current.text = "Reanudar" if self._timer_paused else "Pausar"
                    self._start_btn.current.update()
            except: pass

    def _reset_timer(self, e):
        self._timer_running = False
        self._timer_paused = False
        self._remaining_seconds = self._total_seconds
        self._update_timer_display()
        try:
            if self._start_btn.current:
                self._start_btn.current.text = "Iniciar"
                self._start_btn.current.update()
        except: pass

    def _build_step_row_control(self, step: dict) -> ft.Control:
        colors = self._get_theme_colors()
        def _on_change(e): step["completed"] = e.control.value
        return ft.Row([
            ft.Checkbox(value=step["completed"], on_change=_on_change, active_color="#16A34A"),
            ft.Column([
                ft.Text(step["title"], size=14, weight="bold", color=colors["text"]),
                ft.Text(step["desc"], size=11, color=colors["text_secondary"]),
            ], spacing=2, expand=True),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _show_technique_apply(self, tech: dict):
        """Muestra la herramienta interactiva de aplicación práctica (Fase 3 Completa)."""
        colors = self._get_theme_colors()
        is_dark = self.page and self.page.theme_mode == ft.ThemeMode.DARK
        title = tech.get("titulo", "Técnica")
        info = self._get_technique_info(title)
        key = info["key"]
        navbar = self._build_navbar(f"Aplicar: {title}")

        from services.navigation_service import NavigationController
        if key == "flashcards":
            NavigationController.update_view("Flashcards")
            return
        elif key == "pomodoro":
            NavigationController.update_view("Pomodoro")
            return

        def _back(e):
            self._timer_running = False
            self._current_view = "detail"
            self._show_technique_detail(tech)

        def _finish(e):
            self._timer_running = False
            self._current_view = "list"
            NavigationController.update_view("Tecnicas")

        # ─── HERRAMIENTA 1: MAPAS MENTALES ESTILO NOTEBOOKLM CON IA ─────────
        if key == "mindmap":
            nodes_column = ft.Column(spacing=10)
            main_topic = ft.TextField(hint_text="Tema o asignatura (ej: Fotosíntesis, Revolución Industrial)", border_radius=10, bgcolor=colors["surface"], expand=True)
            ai_loading = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color="#7C3AED")
            summary_container = ft.Container(visible=False)

            def _generate_mindmap_ai(e):
                topic = main_topic.value.strip()
                if not topic:
                    self._show_info("Ingresa un tema para generar el mapa mental con la IA de NotebookLM.")
                    return
                ai_loading.visible = True
                try: self.page.update()
                except: pass

                def _bg_gen():
                    try:
                        from services.chatbot_service import chatbot
                        data = chatbot.generar_mapa_mental_ia(topic)
                        
                        summary_text = data.get("resumen_ejecutivo", "")
                        if summary_text:
                            summary_container.content = ft.Container(
                                padding=14, bgcolor="#F3E8FF", border_radius=12,
                                border=ft.border.all(1, "#D8B4FE"),
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.AUTO_AWESOME, color="#7C3AED", size=18),
                                        ft.Text("Resumen Ejecutivo NotebookLM", size=13, weight="bold", color="#6B21A8"),
                                    ]),
                                    ft.Text(summary_text, size=12, color="#4C1D95", italic=True)
                                ], spacing=6)
                            )
                            summary_container.visible = True

                        branch_controls = []
                        for b in data.get("ramas", []):
                            title = b.get("titulo", "Rama")
                            points = b.get("puntos", [])
                            pts_rows = [ft.Row([ft.Text("•", color="#7C3AED", weight="bold"), ft.Text(pt, size=12, color=colors["text"], expand=True)]) for pt in points]
                            
                            branch_card = ft.Container(
                                padding=14, bgcolor=colors["surface"], border_radius=12,
                                border=ft.border.all(1, "#E2E8F0"),
                                content=ft.Column([
                                    ft.Row([
                                        ft.Icon(ft.Icons.ACCOUNT_TREE, color="#7C3AED", size=18),
                                        ft.Text(title, size=14, weight="bold", color="#7C3AED", expand=True),
                                    ]),
                                    ft.Container(height=4),
                                    ft.Column(pts_rows, spacing=4),
                                ], spacing=4)
                            )
                            branch_controls.append(branch_card)

                        nodes_column.controls = branch_controls

                    except Exception as ex:
                        nodes_column.controls = [ft.Text(f"⚠️ Error al generar: {str(ex)}", color="red")]
                    finally:
                        ai_loading.visible = False
                        try: self.page.update()
                        except: pass

                threading.Thread(target=_bg_gen, daemon=True).start()

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Creador de Mapas Mentales estilo NotebookLM", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Ingresa cualquier tema para que la IA genere un mapa mental completo con resumen ejecutivo y ramas jerárquicas:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    ft.Row([
                        main_topic,
                        ft.ElevatedButton("✨ Generar con IA", bgcolor="#7C3AED", color="white", on_click=_generate_mindmap_ai),
                        ai_loading,
                    ], spacing=10),
                    ft.Container(height=14),
                    summary_container,
                    ft.Container(height=10),
                    nodes_column,
                ], spacing=0)
            )

        # ─── HERRAMIENTA 2: MÉTODO CORNELL ───────────────────────────────────
        elif key == "cornell":
            cues_field = ft.TextField(hint_text="Pistas / Preguntas clave...", multiline=True, min_lines=8, border_radius=10, expand=True)
            notes_field = ft.TextField(hint_text="Notas de clase concisas...", multiline=True, min_lines=8, border_radius=10, expand=True)
            summary_field = ft.TextField(hint_text="Resumen final en 3 oraciones...", multiline=True, min_lines=3, border_radius=10)

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Plantilla Interactiva de Hoja Cornell", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Completa las 3 secciones estándar para tus apuntes:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    ft.Row([
                        ft.Column([ft.Text("Columna de Pistas (25%)", size=12, weight="bold"), cues_field], expand=1),
                        ft.Container(width=12),
                        ft.Column([ft.Text("Notas Principales (75%)", size=12, weight="bold"), notes_field], expand=2),
                    ]),
                    ft.Container(height=12),
                    ft.Text("Resumen Final (Pie de página)", size=12, weight="bold"),
                    summary_field,
                ], spacing=0)
            )

        # ─── HERRAMIENTA 3: REPASO ESPACIADO ──────────────────────────────────
        elif key == "spaced":
            topic_input = ft.TextField(hint_text="Asignatura o Tema a repasar...", border_radius=10, expand=True)
            schedule_col = ft.Column(spacing=8)

            def _calc_schedule(e):
                topic = topic_input.value.strip() or "Tema de Estudio"
                schedule_col.controls = [
                    ft.Container(padding=12, bgcolor="#EEF2FF", border_radius=10, content=ft.Row([ft.Text(f"📅 1er Repaso (Día 1 - Mañana): Repasar {topic}", size=13, weight="bold", color="#4F46E5")])),
                    ft.Container(padding=12, bgcolor="#EEF2FF", border_radius=10, content=ft.Row([ft.Text(f"📅 2do Repaso (Día 3): Test rápido de 10 min sobre {topic}", size=13, weight="bold", color="#4F46E5")])),
                    ft.Container(padding=12, bgcolor="#EEF2FF", border_radius=10, content=ft.Row([ft.Text(f"📅 3er Repaso (Día 7): Autoevaluación de conceptos de {topic}", size=13, weight="bold", color="#4F46E5")])),
                    ft.Container(padding=12, bgcolor="#EEF2FF", border_radius=10, content=ft.Row([ft.Text(f"📅 4to Repaso (Día 14): Explicación rápida de {topic}", size=13, weight="bold", color="#4F46E5")])),
                    ft.Container(padding=12, bgcolor="#EEF2FF", border_radius=10, content=ft.Row([ft.Text(f"📅 5to Repaso (Día 30): Fijación permanente de {topic}", size=13, weight="bold", color="#4F46E5")])),
                ]
                try: self.page.update()
                except: pass

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Calculadora de Calendario de Repetición Espaciada", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Ingresa el tema que estudiaste hoy para generar tus 5 fechas clave de repaso:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    ft.Row([topic_input, ft.ElevatedButton("Generar calendario", bgcolor="#4F46E5", color="white", on_click=_calc_schedule)]),
                    ft.Container(height=14),
                    schedule_col,
                ], spacing=0)
            )

        # ─── HERRAMIENTA 4: TÉCNICA FEYNMAN CON IA ───────────────────────────
        elif key == "feynman":
            f_concept = ft.TextField(hint_text="1. Nombre del concepto complejo (ej: Mecánica Cuántica, Inflación)...", border_radius=10, expand=True)
            f_simple = ft.TextField(hint_text="2. Explicación simplificada como para un niño de 8 años...", multiline=True, min_lines=4, border_radius=10)
            f_gaps = ft.TextField(hint_text="3. Vacíos o aspectos complejos a reforzar...", multiline=True, min_lines=3, border_radius=10)
            f_analogy = ft.TextField(hint_text="4. Analogía o metáfora sencilla...", border_radius=10)
            ai_loading_f = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color="#9A3412")

            def _generate_feynman_ai(e):
                c = f_concept.value.strip()
                if not c:
                    self._show_info("Ingresa el nombre de un concepto para simplificarlo con IA.")
                    return
                ai_loading_f.visible = True
                try: self.page.update()
                except: pass

                def _bg_fey():
                    try:
                        from services.chatbot_service import chatbot
                        res = chatbot.generar_feynman_ia(c)
                        f_simple.value = res.get("explicacion", "")
                    except Exception as ex:
                        f_simple.value = f"Error al simplificar con IA: {str(ex)}"
                    finally:
                        ai_loading_f.visible = False
                        try: self.page.update()
                        except: pass

                threading.Thread(target=_bg_fey, daemon=True).start()

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Simulador Interactivo Feynman con IA", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Ingresa cualquier tema complejo para que la IA lo simplifique en lenguaje claro:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    ft.Row([
                        f_concept,
                        ft.ElevatedButton("✨ Simplificar con IA", bgcolor="#9A3412", color="white", on_click=_generate_feynman_ai),
                        ai_loading_f,
                    ], spacing=10),
                    ft.Container(height=10),
                    f_simple, ft.Container(height=8),
                    f_gaps, ft.Container(height=8),
                    f_analogy,
                ], spacing=0)
            )

        # ─── HERRAMIENTA 5: TARJETAS DE MEMORIA (FLASHCARDS) ESTILO NOTEBOOKLM ─────────
        elif key == "flashcards":
            fc_topic = ft.TextField(hint_text="Tema para generar flashcards con IA (ej: Revolución Industrial, Geometría)", border_radius=10, expand=True)
            ai_loading_fc = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=2, color="#0284C7")
            
            deck = [
                {"pregunta": "¿Qué es la fotosíntesis?", "respuesta": "Proceso mediante el cual las plantas convierten CO2 y agua en glucosa y oxígeno usando luz solar.", "pista": "Ocurre en las hojas verdes gracias a la clorofila."},
                {"pregunta": "¿Cuál es la función de los ribosomas?", "respuesta": "Sintetizar proteínas en la célula a partir de la información del ARN.", "pista": "Son las fábricas de proteínas celulares."},
            ]
            current_card_idx = [0]
            show_back = [False]

            card_question_text = ft.Text(deck[0]["pregunta"], size=15, weight="bold", color="#0284C7", text_align=ft.TextAlign.CENTER)
            card_hint_text = ft.Text("💡 Pista NotebookLM: " + deck[0].get("pista", "Toca 'Voltear' para ver la respuesta"), size=11, color="#0369A1", italic=True)
            card_status_text = ft.Text("Tarjeta 1 de 2", size=12, color=colors["text_secondary"])

            def _update_card_ui():
                idx = current_card_idx[0]
                total = len(deck)
                if idx < 0 or idx >= total: return
                card_status_text.value = f"Tarjeta {idx + 1} de {total}"
                pista_val = deck[idx].get("pista", "Recuerda la clave vista en clase.")
                if show_back[0]:
                    card_question_text.value = f"💡 RESPUESTA:\n{deck[idx]['respuesta']}"
                    card_question_text.color = "#047857"
                    card_hint_text.value = f"💡 Pista NotebookLM: {pista_val}"
                else:
                    card_question_text.value = f"❓ PREGUNTA:\n{deck[idx]['pregunta']}"
                    card_question_text.color = "#0284C7"
                    card_hint_text.value = f"💡 Pista NotebookLM: {pista_val}"
                try: self.page.update()
                except: pass

            def _toggle_flip(e=None):
                show_back[0] = not show_back[0]
                _update_card_ui()

            def _next_card(e=None):
                if current_card_idx[0] < len(deck) - 1:
                    current_card_idx[0] += 1
                    show_back[0] = False
                    _update_card_ui()

            def _prev_card(e=None):
                if current_card_idx[0] > 0:
                    current_card_idx[0] -= 1
                    show_back[0] = False
                    _update_card_ui()

            def _generate_flashcards_ai(e):
                t = fc_topic.value.strip()
                if not t:
                    self._show_info("Ingresa un tema para generar el mazo de flashcards con IA.")
                    return
                ai_loading_fc.visible = True
                try: self.page.update()
                except: pass

                def _bg_fc():
                    try:
                        from services.chatbot_service import chatbot
                        new_deck = chatbot.generar_flashcards_ia(t, cantidad=5)
                        if new_deck:
                            deck.clear()
                            deck.extend(new_deck)
                            current_card_idx[0] = 0
                            show_back[0] = False
                    except Exception as ex:
                        deck.clear()
                        deck.append({"pregunta": "Error de IA", "respuesta": str(ex)})
                    finally:
                        ai_loading_fc.visible = False
                        _update_card_ui()

                threading.Thread(target=_bg_fc, daemon=True).start()

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Entrenador de Tarjetas de Memoria (Flashcards) con IA", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Ingresa una asignatura para que la IA cree un mazo completo de preguntas y respuestas:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    ft.Row([
                        fc_topic,
                        ft.ElevatedButton("✨ Generar Mazo con IA", bgcolor="#0284C7", color="white", on_click=_generate_flashcards_ai),
                        ai_loading_fc,
                    ], spacing=10),
                    ft.Container(height=16),
                    ft.Row([card_status_text], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=8),
                    ft.GestureDetector(
                        on_tap=_toggle_flip,
                        content=ft.Container(
                            height=170, bgcolor="#E0F2FE", border_radius=14, alignment=ft.alignment.center, padding=20,
                            border=ft.border.all(1, "#7DD3FC"),
                            content=ft.Column([
                                ft.Icon(ft.Icons.STYLE, color="#0284C7", size=32),
                                card_question_text,
                                ft.Container(height=6),
                                card_hint_text,
                            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ),
                    ft.Container(height=14),
                    ft.Row([
                        ft.ElevatedButton("← Anterior", bgcolor=colors["background"], color=colors["text"], on_click=_prev_card),
                        ft.ElevatedButton("🔄 Voltear Tarjeta", bgcolor="#0284C7", color="white", on_click=_toggle_flip),
                        ft.ElevatedButton("Siguiente →", bgcolor=colors["background"], color=colors["text"], on_click=_next_card),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=0)
            )

        # ─── HERRAMIENTA 6: MÉTODO SMART (DISEÑO EXACTO IMAGEN ADJUNTA) ───────
        elif key == "smart":
            # Campos de entrada interactivos con valores persistentes
            s_val = ft.Ref[ft.TextField]()
            m_val = ft.Ref[ft.TextField]()
            a_val = ft.Ref[ft.TextField]()
            r_val = ft.Ref[ft.TextField]()
            t_val = ft.Ref[ft.TextField]()

            def smart_card(letter, title, subtitle, hint, strip_color, bg_badge, fg_badge, text_ref):
                return ft.Container(
                    bgcolor=colors["surface"],
                    border_radius=14,
                    border=ft.border.all(1, "#E2E8F0"),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Row([
                        # Franja de color izquierda
                        ft.Container(width=6, bgcolor=strip_color),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=16, vertical=12),
                            expand=True,
                            content=ft.Row([
                                # Círculo con la letra
                                ft.Container(
                                    width=40, height=40, border_radius=20, bgcolor=bg_badge,
                                    alignment=ft.alignment.center,
                                    content=ft.Text(letter, size=18, weight="bold", color=fg_badge)
                                ),
                                # Título y subtítulo
                                ft.Column([
                                    ft.Text(title, size=14, weight="bold", color=colors["text"]),
                                    ft.Text(subtitle, size=11, color=colors["text_secondary"])
                                ], spacing=1, expand=True),
                                # Campo de texto de respuesta
                                ft.TextField(
                                    ref=text_ref,
                                    hint_text=hint,
                                    border_radius=10,
                                    width=380,
                                    height=42,
                                    bgcolor="#F8FAFC" if not is_dark else "#1E293B",
                                    content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                ),
                                # Chevron icon
                                ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color="#94A3B8", size=22)
                            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                        )
                    ], spacing=0)
                )

            card_s = smart_card("S", "S - Específico", "¿Qué tema o tarea exacta vas a realizar?", "Escribe aquí tu respuesta...", "#1E293B", "#1E293B", "white", s_val)
            card_m = smart_card("M", "M - Medible", "¿Cómo comprobarás el éxito? (ej: 10 ejercicios resueltos)", "Escribe aquí tu respuesta...", "#4ADE80", "#DCFCE7", "#16A34A", m_val)
            card_a = smart_card("A", "A - Alcanzable", "¿Cuentas con el tiempo y apuntes necesarios?", "Escribe aquí tu respuesta...", "#C084FC", "#F3E8FF", "#9333EA", a_val)
            card_r = smart_card("R", "R - Relevante", "¿Para qué examen o meta te prepara?", "Escribe aquí tu respuesta...", "#FB923C", "#FFEDD5", "#EA580C", r_val)
            card_t = smart_card("T", "T - Tiempo", "¿En cuántos minutos u horas lo terminarás?", "Escribe aquí tu respuesta...", "#2DD4BF", "#CCFBF1", "#0D9488", t_val)

            sub_header = ft.Row([
                ft.Container(
                    width=36, height=36, border_radius=10, bgcolor=colors["background"],
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.TRACK_CHANGES, color=colors["text"], size=20)
                ),
                ft.Column([
                    ft.Text("Planificador de Objetivos SMART", size=15, weight="bold", color=colors["text"]),
                    ft.Text("Formula tu meta de estudio de forma rigurosa completando cada criterio.", size=11, color=colors["text_secondary"])
                ], spacing=1)
            ], spacing=10)

            interactive_widget = ft.Column([
                sub_header,
                ft.Container(height=14),
                card_s,
                card_m,
                card_a,
                card_r,
                card_t,
            ], spacing=12)

        # ─── HERRAMIENTA 7: MÉTODO SQ3R ─────────────────────────────────────
        elif key == "sq3r":
            sq_survey = ft.TextField(hint_text="1. Survey: Hojea el capítulo y anota títulos y subtítulos clave...", multiline=True, min_lines=2, border_radius=10)
            sq_question = ft.TextField(hint_text="2. Question: Convierte 3 títulos en preguntas que responderás...", multiline=True, min_lines=2, border_radius=10)
            sq_read = ft.TextField(hint_text="3. Read: Lee analíticamente buscando las respuestas...", multiline=True, min_lines=2, border_radius=10)
            sq_recite = ft.TextField(hint_text="4. Recite: Responde las preguntas con tus propias palabras...", multiline=True, min_lines=2, border_radius=10)
            sq_review = ft.TextField(hint_text="5. Review: Revisa y autoevalúa tu nivel de retención...", multiline=True, min_lines=2, border_radius=10)

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Guía Interactiva de Lectura Comprensiva SQ3R", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Aplica las 5 fases secuenciales de lectura analítica:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    sq_survey, ft.Container(height=8),
                    sq_question, ft.Container(height=8),
                    sq_read, ft.Container(height=8),
                    sq_recite, ft.Container(height=8),
                    sq_review,
                ], spacing=0)
            )

        # ─── HERRAMIENTA 8: GENERADOR DE IMÁGENES POINTBIT IA ───────────────
        elif key == "pointbit_image":
            img_prompt_input = ft.TextField(hint_text="¿Qué imagen o diagrama educativo deseas generar? (ej: Célula vegetal, El corazón humano)", border_radius=10, expand=True)
            img_loading = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=3, color="#EC4899")
            img_container = ft.Container(visible=False)

            def _generate_image_ai(e):
                p = img_prompt_input.value.strip()
                if not p:
                    self._show_info("Ingresa la descripción de la imagen educativa que deseas generar.")
                    return
                img_loading.visible = True
                try: self.page.update()
                except: pass

                def _bg_img():
                    try:
                        from services.chatbot_service import chatbot
                        img_url = chatbot.generar_imagen_pointbit_ia(p)
                        img_container.content = ft.Column([
                            ft.Container(height=10),
                            ft.Text(f"🎨 Diagrama Generado: {p}", size=14, weight="bold", color=colors["text"]),
                            ft.Container(height=8),
                            ft.Image(src=img_url, width=700, height=440, fit=ft.ImageFit.CONTAIN, border_radius=12),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        img_container.visible = True
                    except Exception as ex:
                        img_container.content = ft.Text(f"⚠️ Error al generar imagen: {str(ex)}", color="red")
                        img_container.visible = True
                    finally:
                        img_loading.visible = False
                        try: self.page.update()
                        except: pass

                threading.Thread(target=_bg_img, daemon=True).start()

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Generador de Imágenes Educativas de PointBit IA", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Describe cualquier concepto visual o esquema escolar para que PointBit IA cree la ilustración:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    ft.Row([
                        img_prompt_input,
                        ft.ElevatedButton("✨ Generar Imagen con IA", bgcolor="#EC4899", color="white", on_click=_generate_image_ai),
                        img_loading,
                    ], spacing=10),
                    ft.Container(height=14),
                    img_container,
                ], spacing=0)
            )

        # ─── HERRAMIENTA POR DEFECTO: POMODORO PERSONALIZABLE ───────────────
        else:
            self._steps_list_column.controls = [self._build_step_row_control(s) for s in self._pomodoro_steps]
            
            def _open_edit_time_dialog(e):
                time_field = ft.TextField(
                    value=str(self._total_seconds // 60),
                    label="Minutos de enfoque",
                    text_size=14,
                    border_radius=8,
                    width=160,
                    autofocus=True,
                )
                def _apply_time(e):
                    try:
                        m = int(time_field.value.strip())
                        if m > 0:
                            self._total_seconds = m * 60
                            self._remaining_seconds = self._total_seconds
                            self._update_timer_display()
                            self._reset_timer(None)
                    except: pass
                    self.page.close(dlg)

                dlg = ft.AlertDialog(
                    modal=False,
                    title=ft.Text("Modificar tiempo de enfoque", size=16, weight="bold"),
                    content=ft.Container(content=time_field, padding=10),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                        ft.ElevatedButton("Aplicar", bgcolor="#16A34A", color="white", on_click=_apply_time),
                    ]
                )
                self.page.open(dlg)

            # Tareas personalizables
            task_add_row = ft.Row([
                ft.TextField(ref=self._task_input, hint_text="Añadir nueva tarea personalizable...", border_radius=10, expand=True, on_submit=self._add_task),
                ft.ElevatedButton("➕ Añadir", bgcolor="#16A34A", color="white", on_click=self._add_task)
            ], spacing=10)

            timer_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Temporizador Pomodoro", size=18, weight="bold", color=colors["text"]),
                        ft.Container(expand=True),
                        ft.IconButton(ft.Icons.EDIT, icon_color="#16A34A", tooltip="Modificar minutos", on_click=_open_edit_time_dialog),
                    ]),
                    ft.Container(height=14),
                    ft.Container(
                        width=180, height=180, border_radius=90, bgcolor=colors["background"], border=ft.border.all(6, "#16A34A"),
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Text(ref=self._timer_display, value="25:00", size=42, weight="bold", color=colors["text"]),
                            ft.Text("Enfoque", size=12, color=colors["text_secondary"]),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Container(height=16),
                    ft.Row([
                        ft.ElevatedButton(ref=self._start_btn, text="Iniciar", bgcolor="#16A34A", color="white", expand=True, on_click=self._start_timer),
                        ft.ElevatedButton(ref=self._pause_btn, text="Pausar", bgcolor=colors["background"], color=colors["text"], expand=True, on_click=self._pause_timer),
                        ft.ElevatedButton(ref=self._reset_btn, text="Reiniciar", bgcolor=colors["background"], color=colors["text"], expand=True, on_click=self._reset_timer),
                    ], spacing=8)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )

            interactive_widget = ft.Row([
                ft.Container(
                    expand=True, padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                    content=ft.Column([
                        ft.Text("Mis Tareas de la Sesión", size=18, weight="bold", color=colors["text"]),
                        ft.Container(height=6),
                        task_add_row,
                        ft.Container(height=10),
                        ft.Column(ref=self._tasks_column, controls=[]),
                        ft.Divider(height=24),
                        ft.Text("Guía del Procedimiento", size=16, weight="bold", color=colors["text"]),
                        ft.Container(height=6),
                        self._steps_list_column,
                    ])
                ),
                ft.Container(width=16),
                ft.Container(width=300, content=timer_widget),
            ], vertical_alignment=ft.CrossAxisAlignment.START)

        # Header superior con Consejo integrado (Fiel a la imagen)
        advice_box = ft.Container(
            padding=14,
            bgcolor="#F0FDF4",
            border_radius=14,
            border=ft.border.all(1, "#DCFCE7"),
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color="#16A34A", size=18),
                ft.Column([
                    ft.Text("Consejo", size=12, weight="bold", color="#15803D"),
                    ft.Text("Completa cada criterio con atencion y honestidad. Entre más especifico seas, mejores serán tus resultados.", size=10.5, color="#166534")
                ], spacing=1, expand=True)
            ], spacing=10)
        )

        header_section = ft.Row([
            ft.Container(
                width=64, height=64, border_radius=16, bgcolor=colors["background"],
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.ASSIGNMENT_TURNED_IN_OUTLINED, color="#1E3A8A", size=32)
            ),
            ft.Column([
                ft.Text(f"Fase 3: Aplicación Práctica de {title}", size=24, weight="bold", color=colors["text"]),
                ft.Text("Utiliza esta herramienta interactiva durante tu sesión de estudio.", size=13, color=colors["text_secondary"]),
            ], spacing=2, expand=True),
            ft.Container(width=340, content=advice_box)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=16)

        apply_view_content = ft.Column([
            navbar,
            ft.Container(
                expand=True, padding=ft.padding.symmetric(horizontal=32, vertical=20),
                content=ft.Column([
                    ft.GestureDetector(
                        on_tap=_back,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK, size=18, color="#1E3A8A"),
                            ft.Text("Volver al detalle de la técnica", size=13, weight="bold", color="#1E3A8A"),
                        ], spacing=6)
                    ),
                    ft.Container(height=16),
                    header_section,
                    ft.Container(height=24),
                    interactive_widget,
                    ft.Container(height=24),
                    ft.Row([
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "➔ Completar sesión",
                            bgcolor="#4ADE80" if key == "smart" else "#16A34A",
                            color="white",
                            height=46,
                            width=220,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                            on_click=_finish
                        ),
                    ]),
                    ft.Container(height=30),
                ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)
            )
        ], expand=True, spacing=0)

        self._render_view(apply_view_content)

    def _on_search_change(self, e):
        term = e.control.value.lower().strip()
        filtered = [
            t for t in self._techniques
            if term in (t.get("titulo") or "").lower() or term in (t.get("descripcion") or "").lower()
        ]
        self._grid_container.controls = [
            ft.Container(
                col={"sm": 12, "md": 6, "lg": 4},
                content=self._build_technique_card(t)
            ) for t in filtered
        ]
        try: self._grid_container.update()
        except: pass

    def build(self) -> ft.Control:
        self._load_techniques()
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("nav_techniques"))

        # HERO BANNER
        hero = ft.Container(
            bgcolor=colors["surface"],
            padding=ft.padding.symmetric(horizontal=36, vertical=24),
            border=ft.border.all(1, colors["border"]),
            border_radius=20,
            content=ft.Row([
                ft.Column([
                    ft.Text(self.translate("techniques_title"), size=32, weight="bold", color=colors["text"]),
                    ft.Container(height=4),
                    ft.Text(
                        self.translate("techniques_subtitle"),
                        size=14, color=colors["text_secondary"], max_lines=2
                    ),
                ], expand=True, spacing=0),
                ft.Image(
                    src=os.path.join("assets", "figma_assets", "books_apple.jpg"),
                    width=130,
                    height=130,
                    fit=ft.ImageFit.CONTAIN,
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        search_field = ft.TextField(
            hint_text=self.translate("techniques_search"),
            prefix_icon=ft.Icons.SEARCH,
            width=320,
            height=44,
            border_radius=10,
            bgcolor=colors["surface"],
            color=colors["text"],
            border_color=colors["border"],
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_change=self._on_search_change,
        )

        # GRID DE TÉCNICAS
        self._grid_container = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    col={"sm": 12, "md": 6, "lg": 4},
                    content=self._build_technique_card(t)
                ) for t in self._techniques
            ],
            spacing=20,
            run_spacing=20,
        )

        return ft.Column([
            navbar,
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Container(padding=ft.padding.only(left=28, right=28, top=24), content=hero),
                    ft.Container(
                        padding=ft.padding.only(left=28, right=28, top=20, bottom=30),
                        content=ft.Column([
                            search_field,
                            ft.Container(height=16),
                            self._grid_container,
                            ft.Container(height=30),
                        ], spacing=0, expand=True)
                    )
                ], scroll=get_scroll_mode("AUTO"), expand=True)
            )
        ], expand=True, spacing=0)
