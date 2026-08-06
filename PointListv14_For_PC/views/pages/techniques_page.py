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
        """Carga técnicas desde BD o caché."""
        from services.navigation_service import NavigationController
        if NavigationController.cache.get("tecnicas"):
            self._techniques = NavigationController.cache["tecnicas"]
        else:
            self._techniques = self._db.obtener_tecnicas() or []
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
                "bullets": ["Aumenta la concentración", "Ideal para evitar la fatiga", "Recomendado: 25 min + 5 min de descanso"]
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
                "bullets": ["Mejora la comprensión visual", "Ideal para esquematizar materias", "Recomendado: 20-30 min"]
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
        elif "sq3r" in title_lower or "lectura" in title_lower:
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
        title = tech.get("titulo", "")
        info = self._get_technique_info(title)

        def _show_detail(e):
            self._current_view = "detail"
            self._show_technique_detail(tech)

        bullet_controls = [
            ft.Text(b, size=11, color="#64748B", weight="w500") for b in info["bullets"]
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
                ft.Text(title, size=16, weight="bold", color="#0F172A", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(tech.get("descripcion", info["subtitle"]), size=11, color="#64748B", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ], expand=True, spacing=2),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        card_footer = ft.Container(
            border=ft.border.only(top=ft.border.BorderSide(1, "#E2E8F0")),
            padding=ft.padding.only(top=10, bottom=2),
            alignment=ft.alignment.center,
            content=ft.Row([
                ft.Text("Ver detalle y guía", size=13, weight="bold", color=info["text_color"]),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=info["text_color"])
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            on_click=_show_detail,
            ink=True,
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=18, vertical=18),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=-2, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
            content=ft.Column([
                card_header,
                ft.Container(height=12),
                ft.Column(bullet_controls, spacing=4),
                ft.Container(height=14),
                card_footer
            ], spacing=0),
        )

    def _show_technique_detail(self, tech: dict):
        """Muestra pantalla de detalle de técnica (Fase 2 Rediseñada e Innovadora)."""
        colors = self._get_theme_colors()
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

        step_rows = []
        for idx, step_str in enumerate(info["steps"], start=1):
            step_rows.append(
                ft.Container(
                    padding=ft.padding.all(12),
                    bgcolor="#F8FAFC",
                    border_radius=12,
                    border=ft.border.all(1, "#E2E8F0"),
                    content=ft.Row([
                        ft.Container(
                            width=32, height=32, border_radius=16,
                            bgcolor=info["icon_color"],
                            alignment=ft.alignment.center,
                            content=ft.Text(str(idx), color="white", weight="bold", size=14)
                        ),
                        ft.Container(width=10),
                        ft.Text(step_str, size=13, color="#0F172A", weight="w500", expand=True)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )

        left_card = ft.Container(
            expand=True,
            padding=ft.padding.all(24),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=56, height=56, border_radius=28,
                        bgcolor=info["icon_bg"],
                        alignment=ft.alignment.center,
                        content=ft.Icon(info["icon"], size=28, color=info["icon_color"]),
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(title, size=24, weight="bold", color=colors["text"]),
                        ft.Text(tech.get("categoria", "Técnica de Estudio"), size=12, color=info["text_color"], weight="bold"),
                    ], spacing=2, expand=True)
                ]),
                ft.Container(height=16),
                ft.Text("¿Qué es?", size=16, weight="bold", color=colors["text"]),
                ft.Container(height=6),
                ft.Text(info["what_is"], size=13, color=colors["text_secondary"]),
                ft.Container(height=18),
                ft.Text("Beneficios clave", size=16, weight="bold", color=colors["text"]),
                ft.Container(height=6),
                ft.Column([
                    ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color="#16A34A", size=16), ft.Text(b, size=12, color=colors["text"])])
                    for b in info["bullets"]
                ], spacing=6),
            ], spacing=0)
        )

        right_card = ft.Container(
            expand=True,
            padding=ft.padding.all(24),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Text("Procedimiento paso a paso", size=18, weight="bold", color=colors["text"]),
                ft.Text("Sigue estos 5 pasos recomendados para aprovechar al máximo esta técnica:", size=12, color=colors["text_secondary"]),
                ft.Container(height=14),
                ft.Column(step_rows, spacing=10),
            ], spacing=0)
        )

        detail_content = ft.Column([
            navbar,
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=32, vertical=20),
                content=ft.Column([
                    ft.GestureDetector(
                        on_tap=_back,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK, size=20, color="#4F46E5"),
                            ft.Text("Volver al catálogo", size=13, weight="bold", color="#4F46E5"),
                        ], spacing=6)
                    ),
                    ft.Container(height=16),
                    ft.Row([
                        left_card,
                        ft.Container(width=20),
                        right_card,
                    ], vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(height=24),
                    ft.Row([
                        ft.ElevatedButton(
                            "← Volver",
                            bgcolor=ft.Colors.GREY_300,
                            color="#0F172A",
                            width=140,
                            height=46,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=_back,
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Aplicar técnica →",
                            bgcolor="#08015C",
                            color=ft.Colors.WHITE,
                            width=220,
                            height=46,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=_apply_technique,
                        ),
                    ]),
                    ft.Container(height=30),
                ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)
            )
        ], expand=True, spacing=0)

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
        def _on_change(e): step["completed"] = e.control.value
        return ft.Row([
            ft.Checkbox(value=step["completed"], on_change=_on_change, active_color="#16A34A"),
            ft.Column([
                ft.Text(step["title"], size=14, weight="bold", color="#0F172A"),
                ft.Text(step["desc"], size=11, color="#64748B"),
            ], spacing=2, expand=True),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _show_technique_apply(self, tech: dict):
        """Muestra la herramienta interactiva de aplicación práctica (Fase 3 Completa)."""
        colors = self._get_theme_colors()
        title = tech.get("titulo", "Técnica")
        info = self._get_technique_info(title)
        key = info["key"]
        navbar = self._build_navbar(f"Aplicar: {title}")

        def _back(e):
            self._timer_running = False
            self._current_view = "detail"
            self._show_technique_detail(tech)

        def _finish(e):
            self._timer_running = False
            self._current_view = "list"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")

        # ─── HERRAMIENTA 1: MAPAS MENTALES ──────────────────────────────────
        if key == "mindmap":
            nodes_column = ft.Column(spacing=8)
            main_topic = ft.TextField(hint_text="Tema central (ej: Sistema Nervioso)", border_radius=10, bgcolor=colors["surface"])
            branch_input = ft.TextField(hint_text="Añadir rama o subtema...", border_radius=10, bgcolor=colors["surface"], expand=True)

            nodes_list = []
            def _add_branch(e):
                val = branch_input.value.strip()
                if val:
                    nodes_list.append(val)
                    branch_input.value = ""
                    _refresh_nodes()

            def _refresh_nodes():
                nodes_column.controls = [
                    ft.Container(
                        padding=10, bgcolor="#F3E8FF", border_radius=10,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ACCOUNT_TREE, color="#7C3AED", size=18),
                            ft.Text(b, size=13, weight="bold", color="#7C3AED", expand=True),
                        ])
                    ) for b in nodes_list
                ]
                try: self.page.update()
                except: pass

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Creador Interactivo de Mapas Mentales", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Define el concepto central y agrega ramas de forma organizada:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    main_topic,
                    ft.Container(height=10),
                    ft.Row([branch_input, ft.ElevatedButton("Agregar rama", bgcolor="#7C3AED", color="white", on_click=_add_branch)]),
                    ft.Container(height=14),
                    ft.Text("Estructura del Mapa Mental:", size=14, weight="bold", color=colors["text"]),
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

        # ─── HERRAMIENTA 4: TÉCNICA FEYNMAN ──────────────────────────────────
        elif key == "feynman":
            f_concept = ft.TextField(hint_text="1. Nombre del concepto complejo...", border_radius=10)
            f_simple = ft.TextField(hint_text="2. Explícalo como a un niño de 5 años...", multiline=True, min_lines=4, border_radius=10)
            f_gaps = ft.TextField(hint_text="3. ¿En qué partes dudaste o te trabaste?...", multiline=True, min_lines=3, border_radius=10)
            f_analogy = ft.TextField(hint_text="4. Crea una analogía o metáfora sencilla...", border_radius=10)

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Simulador Interactivo Feynman", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Simplifica conceptos difíciles completando los 4 pasos:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    f_concept, ft.Container(height=8),
                    f_simple, ft.Container(height=8),
                    f_gaps, ft.Container(height=8),
                    f_analogy,
                ], spacing=0)
            )

        # ─── HERRAMIENTA 5: TARJETAS DE MEMORIA (FLASHCARDS) ─────────────────
        elif key == "flashcards":
            fc_front = ft.TextField(hint_text="Frente: Pregunta o Término...", border_radius=10)
            fc_back = ft.TextField(hint_text="Reverso: Respuesta o Definición...", border_radius=10)
            fc_status = ft.Text("Tarjeta 1 de 1", size=12, color=colors["text_secondary"])

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Entrenador de Tarjetas de Memoria (Flashcards)", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Crea y repasa tus tarjetas de recuerdo activo:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    fc_front, ft.Container(height=8),
                    fc_back, ft.Container(height=14),
                    ft.Container(
                        height=140, bgcolor="#E0F2FE", border_radius=14, alignment=ft.alignment.center, padding=20,
                        content=ft.Column([
                            ft.Icon(ft.Icons.COPY_OUTLINED, color="#0284C7", size=28),
                            ft.Text("¿Qué es la fotosíntesis?", size=16, weight="bold", color="#0284C7"),
                            ft.Text("(Toca para revelar el reverso)", size=11, color="#0369A1"),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ], spacing=0)
            )

        # ─── HERRAMIENTA 6: MÉTODO SMART ─────────────────────────────────────
        elif key == "smart":
            s_field = ft.TextField(hint_text="S - Específico: ¿Qué tema o tarea exacta vas a realizar?", border_radius=10)
            m_field = ft.TextField(hint_text="M - Medible: ¿Cómo comprobarás el éxito? (ej: 10 ejercicios resueltos)", border_radius=10)
            a_field = ft.TextField(hint_text="A - Alcanzable: ¿Cuentas con el tiempo y apuntes necesarios?", border_radius=10)
            r_field = ft.TextField(hint_text="R - Relevante: ¿Para qué examen o meta te prepara?", border_radius=10)
            t_field = ft.TextField(hint_text="T - Tiempo: ¿En cuántos minutos u horas lo terminarás?", border_radius=10)

            interactive_widget = ft.Container(
                padding=24, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
                content=ft.Column([
                    ft.Text("Planificador de Objetivos SMART", size=18, weight="bold", color=colors["text"]),
                    ft.Text("Formula tu meta de estudio de forma rigurosa completando cada criterio:", size=12, color=colors["text_secondary"]),
                    ft.Container(height=14),
                    s_field, ft.Container(height=8),
                    m_field, ft.Container(height=8),
                    a_field, ft.Container(height=8),
                    r_field, ft.Container(height=8),
                    t_field,
                ], spacing=0)
            )

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
                        width=180, height=180, border_radius=90, bgcolor="#F8FAFC", border=ft.border.all(6, "#16A34A"),
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Text(ref=self._timer_display, value="25:00", size=42, weight="bold", color="#0F172A"),
                            ft.Text("Enfoque", size=12, color="#64748B"),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    ),
                    ft.Container(height=16),
                    ft.Row([
                        ft.ElevatedButton(ref=self._start_btn, text="Iniciar", bgcolor="#16A34A", color="white", expand=True, on_click=self._start_timer),
                        ft.ElevatedButton(ref=self._pause_btn, text="Pausar", bgcolor="#F1F5F9", color="#0F172A", expand=True, on_click=self._pause_timer),
                        ft.ElevatedButton(ref=self._reset_btn, text="Reiniciar", bgcolor="#F1F5F9", color="#0F172A", expand=True, on_click=self._reset_timer),
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

        apply_view_content = ft.Column([
            navbar,
            ft.Container(
                expand=True, padding=ft.padding.symmetric(horizontal=32, vertical=20),
                content=ft.Column([
                    ft.GestureDetector(
                        on_tap=_back,
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_BACK, size=20, color="#4F46E5"),
                            ft.Text("Volver al detalle de la técnica", size=13, weight="bold", color="#4F46E5"),
                        ], spacing=6)
                    ),
                    ft.Container(height=16),
                    ft.Text(f"Fase 3: Aplicación Práctica de {title}", size=24, weight="bold", color=colors["text"]),
                    ft.Text("Utiliza esta herramienta interactiva durante tu sesión de estudio:", size=13, color=colors["text_secondary"]),
                    ft.Container(height=20),
                    interactive_widget,
                    ft.Container(height=24),
                    ft.Row([
                        ft.ElevatedButton("← Volver a la Guía", bgcolor=ft.Colors.GREY_300, color="#0F172A", height=44, on_click=_back),
                        ft.Container(expand=True),
                        ft.ElevatedButton("¡Completar sesión! 🎉", bgcolor="#16A34A", color="white", height=44, on_click=_finish),
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
            border=ft.border.all(1, "#E2E8F0"),
            border_radius=20,
            content=ft.Row([
                ft.Column([
                    ft.Text("Técnicas de estudio", size=32, weight="bold", color="#0F172A"),
                    ft.Container(height=4),
                    ft.Text(
                        "Explora métodos interactivos para acelerar tu aprendizaje y dominar cualquier materia.",
                        size=14, color="#64748B", max_lines=2
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
            hint_text="Buscar técnicas...",
            prefix_icon=ft.Icons.SEARCH,
            width=320,
            height=44,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border_color="#E2E8F0",
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
