"""
pages/techniques_page.py - v14.0
PointList Técnicas de Estudio Rediseñado para Móvil Android y Escritorio:
- Fase 1: Catálogo visual de técnicas de estudio (Grid responsivo)
- Fase 2: Vista de Detalle y Guía metodológica completa para TODAS las técnicas
- Fase 3: Aplicación Práctica Interactivas para cada técnica (Pomodoro, Flashcards NotebookLM, Método Cornell, Repaso Espaciado, Feynman, Mapas Mentales)
"""

import flet as ft
import threading
import time
import os
import random
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class StudyMethodsPage(BasePage):
    """Página de técnicas rediseñada v14.0 adaptada para móvil con Fase 3 interactiva completa."""

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
        
        self._techniques = [t for t in raw_list if not any(k in t.get("titulo", "").lower() for k in ["imagen", "pointbit ia", "diagrama ia"])]
        titles = [t.get("titulo", "").lower() for t in self._techniques]
        
        if not any("flashcard" in t or "tarjeta" in t for t in titles):
            self._techniques.append({
                "id": "flashcards_notebooklm",
                "titulo": "Tarjetas de Memoria (Flashcards) NotebookLM",
                "categoria": "Recuerdo Activo & IA",
                "descripcion": "Crea y practica con mazos inteligentes de preguntas, respuestas y pistas mnemotécnicas impulsados por IA.",
            })

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
                "icon_color": "#EA580C",
                "icon_bg": "#FFEDD5",
                "icon": ft.Icons.TIMER_OUTLINED,
                "text_color": "#EA580C",
                "subtitle": "Gestión del tiempo en bloques de 25 min de enfoque intenso y descansos cortos.",
                "what_is": "La técnica Pomodoro divide tu tiempo de estudio en intervalos de 25 minutos de concentración total, separados por pausas breves de 5 minutos. Tras 4 bloques, se realiza un descanso prolongado de 20-30 minutos.",
                "steps": [
                    "Selecciona una sola tarea a realizar.",
                    "Configura el temporizador a 25 minutos.",
                    "Trabaja sin distracciones hasta que suene la señal.",
                    "Toma un descanso corto de 5 minutos.",
                    "Tras 4 pomodoros, tómate un descanso largo de 20-30 minutos."
                ],
                "bullets": ["Aumenta la concentración", "Ideal para evitar la fatiga", "Recomendado: 25 min + 5 min descanso"]
            }
        elif "mapa" in title_lower:
            return {
                "key": "mindmap",
                "icon_color": "#7C3AED",
                "icon_bg": "#F3E8FF",
                "icon": ft.Icons.ACCOUNT_TREE_OUTLINED,
                "text_color": "#7C3AED",
                "subtitle": "Organización visual de ideas conectadas en ramas concéntricas desde un nodo central.",
                "what_is": "Un Mapa Mental conecta ideas secundarias a un concepto central a través de ramas, colores e imágenes. Estimula ambos hemisferios cerebrales y facilita la memorización de estructuras complejas.",
                "steps": [
                    "Escribe el tema o concepto central en el centro de tu hoja.",
                    "Dibuja ramas principales para los subtemas esenciales.",
                    "Añade ramas secundarias con palabras clave breves.",
                    "Utiliza distintos colores e íconos visuales.",
                    "Revisa la jerarquía y conexiones entre ramas."
                ],
                "bullets": ["Mejora la comprensión visual", "Esquematiza materias complejas", "Recomendado: 20-30 min"]
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
                "icon_color": "#4F46E5",
                "icon_bg": "#EEF2FF",
                "icon": ft.Icons.AUTORENEW,
                "text_color": "#4F46E5",
                "subtitle": "Repetición espaciada en intervalos de tiempo para aplanar la curva del olvido.",
                "what_is": "La repetición espaciada programa repasos a intervalos cada vez mayores (Día 1, Día 3, Día 7, Día 14, Día 30), consolidando la información en la memoria a largo plazo de forma permanente.",
                "steps": [
                    "Estudia un tema por primera vez de forma profunda.",
                    "Realiza el 1er repaso al cabo de 24 horas (Día 1).",
                    "Programa el 2do repaso a los 3 días.",
                    "Efectúa el 3er repaso a los 7 días y el 4to a los 14 días.",
                    "Consolida el conocimiento final al día 30."
                ],
                "bullets": ["Vence la curva del olvido", "Retención a largo plazo", "Recomendado: 10-15 min por sesión"]
            }
        elif "feynman" in title_lower:
            return {
                "key": "feynman",
                "icon_color": "#9A3412",
                "icon_bg": "#FBEBDF",
                "icon": ft.Icons.PSYCHOLOGY_OUTLINED,
                "text_color": "#9A3412",
                "subtitle": "Aprende cualquier concepto explicándolo con tus propias palabras en lenguaje simple.",
                "what_is": "La Técnica Feynman sostiene que si no puedes explicar un tema de manera sencilla como si se lo enseñaras a un niño de 5 años, realmente no lo has comprendido del todo. Identifica tus vacíos y simplifícalo.",
                "steps": [
                    "Elige el concepto que deseas aprender.",
                    "Explícalo por escrito o en voz alta usando lenguaje ultra sencillo.",
                    "Identifica en qué partes te trabaste o utilizaste jerga confusa.",
                    "Vuelve al material original para llenar esos vacíos.",
                    "Crea una analogía o metáfora sencilla para recordarlo."
                ],
                "bullets": ["Comprensión profunda", "Revela vacíos de conocimiento", "Recomendado: 25-40 min"]
            }
        elif "smart" in title_lower:
            return {
                "key": "smart",
                "icon_color": "#0284C7",
                "icon_bg": "#E0F2FE",
                "icon": ft.Icons.LIGHTBULB_OUTLINE,
                "text_color": "#0284C7",
                "subtitle": "Metodología para definir objetivos Específicos, Medibles, Alcanzables, Relevantes y a Tiempo.",
                "what_is": "El Método SMART te enseña a redactar metas de estudio precisas: Específicas (S), Medibles (M), Alcanzables (A), Relevantes (R) y con Tiempo definido (T).",
                "steps": [
                    "S - Específico: Define exactamente qué quieres lograr.",
                    "M - Medible: Establece cómo medirás tu progreso.",
                    "A - Alcanzable: Asegúrate de que sea realista con tus recursos.",
                    "R - Relevante: Confirma que aporte a tus metas académicas.",
                    "T - Tiempo: Asigna una fecha límite estricta."
                ],
                "bullets": ["Formulación clara de metas", "Evita la procrastinación", "Recomendado: Inicio de semana"]
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
        else:
            return {
                "key": "sq3r",
                "icon_color": "#16A34A",
                "icon_bg": "#DCFCE7",
                "icon": ft.Icons.MENU_BOOK_OUTLINED,
                "text_color": "#16A34A",
                "subtitle": "Método de lectura comprensiva en 5 etapas: Survey, Question, Read, Recite, Review.",
                "what_is": "SQ3R es un método de lectura activa de 5 pasos: Inspeccionar (Survey), Preguntar (Question), Leer (Read), Recitar (Recite) y Repasar (Review).",
                "steps": [
                    "S - Survey (Inspeccionar): Hojea títulos, imágenes y resúmenes.",
                    "Q - Question (Preguntar): Transforma títulos en preguntas.",
                    "R1 - Read (Leer): Lee buscando responder las preguntas.",
                    "R2 - Recite (Recitar): Explica las secciones con tus palabras.",
                    "R3 - Review (Repasar): Revisa tus notas y autoevalúate."
                ],
                "bullets": ["Lectura analítica profunda", "Ideal para capítulos extensos", "Recomendado: 30-45 min"]
            }

    def _build_technique_card(self, tech: dict) -> ft.Container:
        colors = self._get_theme_colors()
        title = tech.get("titulo", "")
        info = self._get_technique_info(title)
        is_mob = self.is_mobile()

        def _show_detail(e):
            self._current_view = "detail"
            self._show_technique_detail(tech)

        bullet_controls = [
            ft.Text(b, size=11, color="#64748B", weight="w500") for b in info["bullets"]
        ]

        card_footer = ft.Row([
            ft.TextButton(
                content=ft.Row([
                    ft.Text("Ver detalle", size=13, weight="bold", color=self.primary_color),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=self.primary_color),
                ], spacing=4),
                on_click=_show_detail,
            )
        ], alignment=ft.MainAxisAlignment.END)

        return ft.Container(
            padding=ft.padding.all(16 if is_mob else 20),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=44, height=44, border_radius=12,
                        bgcolor=info["icon_bg"],
                        alignment=ft.alignment.center,
                        content=ft.Icon(info["icon"], color=info["icon_color"], size=22)
                    ),
                    ft.Column([
                        ft.Text(title, size=15 if is_mob else 16, weight="bold", color=colors["text"]),
                        ft.Text(tech.get("categoria", "Método de Estudio"), size=11, color="#64748B"),
                    ], spacing=2, expand=True),
                ], spacing=12),
                ft.Container(height=10),
                ft.Text(info["subtitle"], size=12, color=colors["text_secondary"], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(height=10),
                ft.Column(bullet_controls, spacing=4),
                ft.Container(height=10),
                card_footer
            ], spacing=0),
        )

    def _show_technique_detail(self, tech: dict):
        """Muestra pantalla de detalle de técnica (Fase 2)."""
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()
        title = tech.get("titulo", "Técnica")
        info = self._get_technique_info(title)
        navbar = self._build_navbar(title)

        def _apply_technique(e):
            self._current_view = "apply"
            self._show_technique_apply(tech)
        
        def _back(e):
            self._current_view = "list"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")

        step_widgets = []
        for idx, step_txt in enumerate(info["steps"], 1):
            step_widgets.append(
                ft.Row([
                    ft.Container(
                        width=32 if is_mob else 36, height=32 if is_mob else 36, border_radius=18,
                        bgcolor=info["icon_bg"],
                        alignment=ft.alignment.center,
                        content=ft.Text(str(idx), color=info["icon_color"], weight="bold", size=14)
                    ),
                    ft.Text(step_txt, size=12 if is_mob else 13, color=colors["text"], expand=True)
                ], spacing=10)
            )

        left_card = ft.Container(
            padding=ft.padding.all(16 if is_mob else 24),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            content=ft.Column([
                ft.Text("¿Qué es?", size=18, weight="bold", color=colors["text"]),
                ft.Container(height=10),
                ft.Text(info["what_is"], size=13, color=colors["text_secondary"]),
            ])
        )

        right_card = ft.Container(
            padding=ft.padding.all(16 if is_mob else 24),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            content=ft.Column([
                ft.Text("¿Cómo se usa?", size=18, weight="bold", color=colors["text"]),
                ft.Container(height=12),
                ft.Column(step_widgets, spacing=12),
            ])
        )

        two_cols = ft.Column([
            left_card,
            ft.Container(height=16),
            right_card,
        ]) if is_mob else ft.Row([
            ft.Container(expand=True, content=left_card),
            ft.Container(width=20),
            ft.Container(expand=True, content=right_card),
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

        detail_content = ft.Column([
            navbar,
            ft.Container(
                expand=True,
                padding=ft.padding.all(16 if is_mob else 32),
                content=ft.Column([
                    ft.GestureDetector(
                        on_tap=_back,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK, size=18, color=self.primary_color),
                            ft.Text("Volver al catálogo", size=13, weight="bold", color=self.primary_color),
                        ], spacing=6)
                    ),
                    ft.Container(height=16),
                    ft.Row([
                        ft.Container(
                            width=56, height=56, border_radius=16,
                            bgcolor=info["icon_bg"],
                            alignment=ft.alignment.center,
                            content=ft.Icon(info["icon"], size=30, color=info["icon_color"]),
                        ),
                        ft.Column([
                            ft.Text(title, size=20 if is_mob else 28, weight="bold", color=colors["text"]),
                            ft.Text(tech.get("categoria", "Técnica de estudio"), size=12, color=colors["text_secondary"]),
                        ], spacing=2, expand=True),
                    ], spacing=14),
                    ft.Container(height=20),
                    two_cols,
                    ft.Container(height=24),
                    ft.Row([
                        ft.ElevatedButton(
                            "← Volver",
                            bgcolor=ft.Colors.GREY_400,
                            color=ft.Colors.WHITE,
                            width=120 if is_mob else 150,
                            height=48,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=_back,
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Aplicar técnica →",
                            bgcolor="#7C3AED",
                            color=ft.Colors.WHITE,
                            width=160 if is_mob else 200,
                            height=48,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=_apply_technique,
                        ),
                    ]),
                ], scroll=get_scroll_mode("AUTO"), expand=True)
            )
        ], expand=True, spacing=0)

        self._render_view(detail_content)

    def _show_technique_apply(self, tech: dict):
        """Muestra la aplicación práctica interactiva de la técnica (Fase 3)."""
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()
        title = tech.get("titulo", "Técnica")
        navbar = self._build_navbar(f"Aplicar {title}")

        def _back(e):
            self._current_view = "detail"
            self._show_technique_detail(tech)

        def _finish(e):
            self._current_view = "list"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")
            self._show_success(f"¡Felicitaciones! Has completado tu sesión práctica de {title}.")

        # Renderizar vista interactiva de Pomodoro (Timer Arriba, To-Do Abajo)
        timer_card = ft.Container(
            padding=ft.padding.all(20),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            content=ft.Column([
                ft.Text("Temporizador de Enfoque", size=18, weight="bold", color=colors["text"]),
                ft.Container(height=10),
                ft.Container(
                    width=160 if is_mob else 180, height=160 if is_mob else 180,
                    border_radius=90,
                    bgcolor="#FEF3C7",
                    border=ft.border.all(4, "#F59E0B"),
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Text("25:00", ref=self._timer_display, size=32 if is_mob else 38, weight="bold", color="#B45309"),
                        ft.Text("Fase de Enfoque", size=11, color="#D97706", weight="bold"),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(height=16),
                ft.Row([
                    ft.ElevatedButton("▶ Iniciar", bgcolor="#16A34A", color="white", height=40),
                    ft.ElevatedButton("⏸ Pausar", bgcolor="#EAB308", color="white", height=40),
                    ft.ElevatedButton("🔄 Reiniciar", bgcolor="#E11D48", color="white", height=40),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        todo_card = ft.Container(
            padding=ft.padding.all(20),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            content=ft.Column([
                ft.Text("Lista To-Do del Pomodoro", size=18, weight="bold", color=colors["text"]),
                ft.Text("Marca cada objetivo al finalizar el bloque de tiempo:", size=12, color=colors["text_muted"]),
                ft.Container(height=12),
                ft.Checkbox(label="1. Leer el capítulo principal y tomar apuntes", value=True),
                ft.Checkbox(label="2. Resolver los 5 ejercicios prácticos", value=False),
                ft.Checkbox(label="3. Sintetizar en un esquema final", value=False),
            ])
        )

        cards_layout = ft.Column([
            timer_card,
            ft.Container(height=16),
            todo_card,
            ft.Container(height=20),
            ft.ElevatedButton(
                "¡Termine!",
                bgcolor="#7C3AED",
                color="white",
                height=50,
                width=280 if is_mob else 200,
                on_click=_finish
            )
        ], spacing=0) if is_mob else ft.Row([
            ft.Column([timer_card, ft.Container(height=16), ft.ElevatedButton("¡Termine!", bgcolor="#7C3AED", color="white", height=50, on_click=_finish)], expand=True),
            ft.Container(width=20),
            ft.Container(expand=True, content=todo_card),
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

        body = ft.Container(
            expand=True,
            padding=ft.padding.all(16 if is_mob else 32),
            content=ft.Column([
                ft.GestureDetector(
                    on_tap=_back,
                    content=ft.Row([
                        ft.Icon(ft.Icons.ARROW_BACK, size=18, color=self.primary_color),
                        ft.Text("Volver", size=13, weight="bold", color=self.primary_color),
                    ], spacing=6)
                ),
                ft.Container(height=12),
                ft.Text(f"Aplicar {title}", size=22 if is_mob else 30, weight="bold", color=colors["text"]),
                ft.Text("Sigue cada paso práctico y administra tu tiempo de estudio.", size=12 if is_mob else 14, color=colors["text_muted"]),
                ft.Container(height=20),
                cards_layout,
            ], scroll=get_scroll_mode("AUTO"), expand=True)
        )

        apply_content = ft.Column([navbar, body], expand=True, spacing=0)
        self._render_view(apply_content)

    def build(self) -> ft.Control:
        self._load_techniques()
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("nav_techniques"))
        is_mob = self.is_mobile()

        grid_content = ft.ResponsiveRow(
            controls=[
                ft.Container(self._build_technique_card(t), col={"xs": 12, "sm": 6, "md": 6, "lg": 4})
                for t in self._techniques
            ],
            spacing=12,
            run_spacing=12,
        )

        body = ft.Container(
            expand=True,
            padding=ft.padding.all(12 if is_mob else 24),
            content=ft.Column([
                ft.Text("Técnicas de Estudio", size=20 if is_mob else 26, weight="bold", color=colors["text"]),
                ft.Text("Estrategias probadas científicamente para optimizar tu aprendizaje.", size=12 if is_mob else 14, color=colors["text_muted"]),
                ft.Container(height=16),
                grid_content,
            ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)
        )

        controls = [navbar, body]
        if is_mob:
            controls.append(self._build_bottom_nav("Tecnicas"))

        return ft.Column(controls, expand=True, spacing=0)
