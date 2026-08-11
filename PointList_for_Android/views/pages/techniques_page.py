"""
pages/techniques_page.py - v13.5
PointList Técnicas Rediseñado
Pomodoro con tareas personalizables, checkboxes y ajuste de tiempo
"""

import flet as ft
import threading
import time
from views.pages.base_page import BasePage
from utils.flet_compat import create_chip, get_scroll_mode

class StudyMethodsPage(BasePage):
    """Página de técnicas rediseñada v13.5 con Pomodoro personalizable."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        self._db = db
        self._techniques: list = []
        self._selected_category = "Todos"
        self._list_ref = ft.Ref[ft.Column]()
        self._current_view = "list"  # list, detail, apply
        
        # Variables del temporizador
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
        self._pomodoro_count = 1
        
        # Tareas personalizables
        self._tasks: list = []
        self._task_input = ft.Ref[ft.TextField]()
        self._tasks_column = ft.Ref[ft.Column]()

        # Procedimiento personalizable
        self._pomodoro_steps = [
            {"id": 0, "title": "1. Elige una tarea específica", "desc": "Define el objetivo exacto en el que te vas a enfocar.", "completed": False},
            {"id": 1, "title": "2. Elimina distracciones", "desc": "Silencia notificaciones del celular y despeja tu escritorio.", "completed": False},
            {"id": 2, "title": "3. Trabaja enfocado 25 minutos", "desc": "Mantén la concentración total hasta que suene el temporizador.", "completed": False},
            {"id": 3, "title": "4. Descansa 5 minutos", "desc": "Levántate, estírate o toma agua para despejar la mente.", "completed": False},
            {"id": 4, "title": "5. Repite el ciclo Pomodoro", "desc": "Después de 4 ciclos completos, toma un descanso largo de 15 a 30 minutos.", "completed": False},
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
        """Carga técnicas."""
        from services.navigation_service import NavigationController
        if NavigationController.cache.get("tecnicas"):
            self._techniques = NavigationController.cache["tecnicas"]
        else:
            self._techniques = self._db.obtener_tecnicas() or []
            NavigationController.cache["tecnicas"] = self._techniques

    def _is_pomodoro(self, tech: dict) -> bool:
        return "pomodoro" in (tech.get("titulo", "") or "").lower()

    def _technique_icon(self, title: str):
        title_lower = (title or "").lower()
        if "pomodoro" in title_lower:
            return ft.Icons.TIMER_OUTLINED
        if "mapa" in title_lower:
            return ft.Icons.ACCOUNT_TREE_OUTLINED
        if "feynman" in title_lower:
            return ft.Icons.PSYCHOLOGY_OUTLINED
        if "smart" in title_lower:
            return ft.Icons.LIGHTBULB_OUTLINE
        if "sq3r" in title_lower:
            return ft.Icons.MENU_BOOK_OUTLINED
        if "repet" in title_lower:
            return ft.Icons.AUTORENEW
        return ft.Icons.SCHOOL_OUTLINED

    def _build_technique_card(self, tech: dict) -> ft.Container:
        colors = self._get_theme_colors()
        title = tech.get("titulo", "")
        
        def _show_detail(e):
            self._current_view = "detail"
            self._show_technique_detail(tech)

        # Mapeo de detalles según el título de la técnica
        details_map = {
            "mapas mentales": {
                "icon_color": "#7C3AED",
                "icon_bg": "#F3E8FF",
                "icon": ft.Icons.PSYCHOLOGY,
                "bullets": ["Mejora la comprensión", "Ideal para materias teóricas", "Tiempo recomendado: 15-30 min"],
                "text_color": "#7C3AED"
            },
            "cornell": {
                "icon_color": "#0D9488",
                "icon_bg": "#CCFBF1",
                "icon": ft.Icons.ASSIGNMENT_OUTLINED,
                "bullets": ["Mejora el repaso", "Ideal para clases y lecturas", "Tiempo recomendado: 15-30 min"],
                "text_color": "#0D9488"
            },
            "espaciado": {
                "icon_color": "#4F46E5",
                "icon_bg": "#EEF2FF",
                "icon": ft.Icons.DONE_ALL_ROUNDED,
                "bullets": ["Mejora el repaso", "Ideal para clases y lecturas", "Tiempo recomendado: 10-20 min"],
                "text_color": "#4F46E5"
            },
            "pomodoro": {
                "icon_color": "#EA580C",
                "icon_bg": "#FFEDD5",
                "icon": ft.Icons.TIMER_OUTLINED,
                "bullets": ["Aumenta la concentración", "Ideal para cualquier materia", "Tiempo recomendado: 25 min + 5 min de descanso"],
                "text_color": "#EA580C"
            },
            "feynman": {
                "icon_color": "#9A3412",
                "icon_bg": "#FBEBDF",
                "icon": ft.Icons.LIGHTBULB_OUTLINE,
                "bullets": ["Mejora la comprensión profunda", "Ideal para temas complejos", "Tiempo recomendado: 30-45 min"],
                "text_color": "#9A3412"
            },
            "tarjetas de memoria": {
                "icon_color": "#0284C7",
                "icon_bg": "#E0F2FE",
                "icon": ft.Icons.COPY_OUTLINED,
                "bullets": ["Mejora la memoria", "Ideal para definiciones y conceptos", "Tiempo recomendado: 10-15 min diarios"],
                "text_color": "#0284C7"
            }
        }

        # Fallback
        info = {
            "icon_color": "#4F46E5",
            "icon_bg": "#EEF2FF",
            "icon": ft.Icons.SCHOOL_OUTLINED,
            "bullets": ["Técnica de aprendizaje", "Ayuda a repasar mejor", "Recomendado: 15-30 min"],
            "text_color": "#4F46E5"
        }
        title_lower = title.lower()
        for k, v in details_map.items():
            if k in title_lower:
                info = v
                break

        # Filas de viñetas (bullets)
        bullet_controls = []
        for bullet in info["bullets"]:
            bullet_controls.append(
                ft.Text(bullet, size=11, color="#64748B", weight="w500")
            )

        card_header = ft.Row([
            ft.Container(
                width=52, height=52,
                bgcolor=info["icon_bg"],
                border_radius=10,
                alignment=ft.alignment.center,
                content=ft.Icon(info["icon"], color=info["icon_color"], size=24)
            ),
            ft.Container(width=10),
            ft.Column([
                ft.Text(title, size=15, weight="bold", color="#0F172A", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(tech.get("descripcion", ""), size=11, color="#64748B", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ], expand=True, spacing=2),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        card_footer = ft.Container(
            border=ft.border.only(top=ft.border.BorderSide(1, "#E2E8F0")),
            padding=ft.padding.only(top=10, bottom=2),
            alignment=ft.alignment.center,
            content=ft.Row([
                ft.Text("Ver más", size=13, weight="bold", color=info["text_color"]),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=info["text_color"])
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            on_click=_show_detail,
        )

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=16),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                card_header,
                ft.Container(height=8),
                ft.Column(bullet_controls, spacing=4),
                ft.Container(height=12),
                card_footer
            ], spacing=0),
        )

    def _show_technique_detail(self, tech: dict):
        """Muestra pantalla de detalle de técnica (Técnica 2)."""
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()
        title = tech.get("titulo", "Técnica")
        navbar = self._build_navbar(title)


        if not self._is_pomodoro(tech):
            def _back_from_generic(e):
                self._current_view = "list"
                from services.navigation_service import NavigationController
                NavigationController.update_view("Tecnicas")

            detail_content = ft.Column([
                navbar,
                ft.Container(
                    expand=True,
                    padding=ft.padding.all(32),
                    content=ft.Column([
                        ft.GestureDetector(
                            on_tap=_back_from_generic,
                            content=ft.Row([
                                ft.Icon(ft.Icons.ARROW_BACK, size=24, color=self.primary_color),
                                ft.Text("Volver", size=14, weight="bold", color=self.primary_color),
                            ], spacing=10),
                        ),
                        ft.Container(height=24),
                        ft.Container(
                            padding=ft.padding.all(28),
                            bgcolor=colors["surface"],
                            border_radius=16,
                            content=ft.Column([
                                ft.Row([
                                    ft.Container(
                                        width=76, height=76, border_radius=38,
                                        bgcolor="#E9FFF8",
                                        alignment=ft.alignment.center,
                                        content=ft.Icon(self._technique_icon(title), size=40, color="black"),
                                    ),
                                    ft.Column([
                                        ft.Text(title, size=30, weight="bold", color=colors["text"]),
                                        ft.Text(tech.get("categoria", "Técnica de estudio"), size=13, color=colors["text_secondary"]),
                                    ], spacing=4, expand=True),
                                ], spacing=18),
                                ft.Container(height=24),
                                ft.Text("Descripción", size=18, weight="bold", color=colors["text"]),
                                ft.Text(tech.get("descripcion", "Explora esta técnica y adapta sus pasos a tu rutina de estudio."), size=15, color=colors["text_secondary"]),
                                ft.Container(height=24),
                                ft.Text("Cómo aprovecharla", size=18, weight="bold", color=colors["text"]),
                                ft.Text("Define un objetivo claro, prepara tus materiales, aplica el método durante una sesión corta y revisa qué funcionó al terminar.", size=15, color=colors["text_secondary"]),
                            ], spacing=0),
                        ),
                    ], scroll=get_scroll_mode("AUTO"), expand=True),
                ),
            ], expand=True, spacing=0)
            self._render_view(detail_content)
            return
        
        def _apply_technique(e):
            self._current_view = "apply"
            self._show_technique_apply(tech)
        
        def _back(e):
            self._current_view = "list"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")

        detail_content = ft.Column([
            navbar,
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Container(height=20),
                    ft.Text(title, size=32, weight="bold", color=colors["text"]),
                    ft.Text("Una técnica de gestión del tiempo que te ayuda a trabajar en bloques enfocados con descanso cortos para ser más productivo", 
                           size=14, color=colors["text_secondary"]),
                    ft.Container(height=30),
                    
                    # Dos columnas o columna responsiva según dispositivo
                    ft.Column([
                        ft.Container(
                            padding=ft.padding.all(16 if is_mob else 20),
                            bgcolor=colors["surface"],
                            border_radius=16,
                            content=ft.Column([
                                ft.Text("¿Qué es?", size=18, weight="bold", color=colors["text"]),
                                ft.Container(height=10),
                                ft.Text(
                                    "La técnica Pomodoro es un método de estudio que divide el tiempo en bloques de 25 minutos de concentración total, llamados 'pomodoros'. Después de cada bloque, se toma un descanso de 5 minutos. Al completar cuatro bloques, se realiza un descanso más largo de 30 minutos. Esta técnica ayuda a mantener el enfoque, evitar distracciones y organizar mejor el tiempo de estudio.",
                                    size=13, color=colors["text_secondary"]
                                )
                            ])
                        ),
                        ft.Container(height=16 if is_mob else 0, width=0 if is_mob else 20),
                        ft.Container(
                            padding=ft.padding.all(16 if is_mob else 20),
                            bgcolor=colors["surface"],
                            border_radius=16,
                            content=ft.Column([
                                ft.Text("¿Cómo se usa?", size=18, weight="bold", color=colors["text"]),
                                ft.Container(height=10),
                                ft.Column([
                                    ft.Row([
                                        ft.Container(
                                            width=32 if is_mob else 40, height=32 if is_mob else 40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("1", color="white", weight="bold", size=14 if is_mob else 16)
                                        ),
                                        ft.Text("Elige una tarea que quieras realizar.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=32 if is_mob else 40, height=32 if is_mob else 40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("2", color="white", weight="bold", size=14 if is_mob else 16)
                                        ),
                                        ft.Text("Configura el temporizador a 25 minutos.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=32 if is_mob else 40, height=32 if is_mob else 40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("3", color="white", weight="bold", size=14 if is_mob else 16)
                                        ),
                                        ft.Text("Trabaja en la tarea hasta que suene la alarma.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=32 if is_mob else 40, height=32 if is_mob else 40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("4", color="white", weight="bold", size=14 if is_mob else 16)
                                        ),
                                        ft.Text("Toma un descanso de 5 minutos.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=32 if is_mob else 40, height=32 if is_mob else 40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("5", color="white", weight="bold", size=14 if is_mob else 16)
                                        ),
                                        ft.Text("Después de 4 Pomodoros, toma un descanso largo de 15-30 minutos.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                ], spacing=12)
                            ])
                        ),
                    ]) if is_mob else ft.Row([
                        ft.Container(
                            expand=True,
                            padding=ft.padding.all(20),
                            bgcolor=colors["surface"],
                            border_radius=16,
                            content=ft.Column([
                                ft.Text("¿Qué es?", size=18, weight="bold", color=colors["text"]),
                                ft.Container(height=10),
                                ft.Text(
                                    "La técnica Pomodoro es un método de estudio que divide el tiempo en bloques de 25 minutos de concentración total, llamados 'pomodoros'. Después de cada bloque, se toma un descanso de 5 minutos al completar cuatro bloques, se realiza un descanso más largo de 30 minutos. Esta técnica ayuda a mantener el enfoque, evitar distracciones y organizar mejor el tiempo de estudio.",
                                    size=13, color=colors["text_secondary"]
                                )
                            ])
                        ),
                        ft.Container(width=20),
                        ft.Container(
                            expand=True,
                            padding=ft.padding.all(20),
                            bgcolor=colors["surface"],
                            border_radius=16,
                            content=ft.Column([
                                ft.Text("¿Cómo se usa?", size=18, weight="bold", color=colors["text"]),
                                ft.Container(height=10),
                                ft.Column([
                                    ft.Row([
                                        ft.Container(
                                            width=40, height=40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("1", color="white", weight="bold", size=16)
                                        ),
                                        ft.Text("Elige una tarea que quieras realizar.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=40, height=40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("2", color="white", weight="bold", size=16)
                                        ),
                                        ft.Text("Configura el temporizador a 25 minutos.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=40, height=40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("3", color="white", weight="bold", size=16)
                                        ),
                                        ft.Text("Trabaja en la tarea hasta que suene la alarma.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=40, height=40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("4", color="white", weight="bold", size=16)
                                        ),
                                        ft.Text("Toma un descanso de 5 minutos.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Container(
                                            width=40, height=40, border_radius=20,
                                            bgcolor=self.primary_color,
                                            alignment=ft.alignment.center,
                                            content=ft.Text("5", color="white", weight="bold", size=16)
                                        ),
                                        ft.Text("Después de 4 Pomodoros, toma un descanso largo de 15-30 minutos.", size=12, color=colors["text"], expand=True)
                                    ], spacing=10),
                                ], spacing=15)
                            ])
                        ),
                    ], expand=True),

                    
                    ft.Container(height=30),
                    
                    ft.Container(height=30),
                    ft.Row([
                        ft.ElevatedButton(
                            "← Volver",
                            bgcolor=ft.Colors.GREY_400,
                            color=ft.Colors.WHITE,
                            width=150,
                            height=50,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=9)),
                            on_click=_back,
                        ),
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Aplicar técnica →",
                            bgcolor="#08015c",
                            color=ft.Colors.WHITE,
                            width=200,
                            height=50,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=9)),
                            on_click=_apply_technique,
                        ),
                    ]),
                    ft.Container(height=40),
                ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)
            )
        ], expand=True, spacing=0)

        self._render_view(detail_content)

    def _add_task(self, e):
        """Añade una tarea a la lista."""
        task_text = self._task_input.current.value.strip()
        if not task_text:
            return
        
        task = {"id": len(self._tasks), "text": task_text, "completed": False}
        self._tasks.append(task)
        self._task_input.current.value = ""
        self._refresh_tasks_list()

    def _toggle_task(self, task_id):
        """Marca/desmarca una tarea como completada."""
        for task in self._tasks:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
        self._refresh_tasks_list()

    def _delete_task(self, task_id):
        """Elimina una tarea."""
        self._tasks = [t for t in self._tasks if t["id"] != task_id]
        self._refresh_tasks_list()

    def _refresh_tasks_list(self):
        """Refresca la lista de tareas."""
        if not self._tasks_column.current:
            return
        
        colors = self._get_theme_colors()
        task_controls = []
        
        for task in self._tasks:
            task_controls.append(
                ft.Row([
                    ft.Checkbox(
                        value=task["completed"],
                        on_change=lambda e, tid=task["id"]: self._toggle_task(tid),
                    ),
                    ft.Text(
                        task["text"],
                        size=14,
                        color=colors["text_secondary"] if task["completed"] else colors["text"],
                        weight="bold" if not task["completed"] else "normal",
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda e, tid=task["id"]: self._delete_task(tid),
                    ),
                ], spacing=10)
            )
        
        try:
            self._tasks_column.current.controls = task_controls
            self._tasks_column.current.update()
        except:
            pass

    def _update_timer_display(self):
        """Actualiza la visualización del temporizador."""
        minutes = self._remaining_seconds // 60
        seconds = self._remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        try:
            self._timer_display.current.value = time_str
            self._timer_display.current.update()
        except:
            pass

    def _run_timer(self):
        """Ejecuta el temporizador en background."""
        while self._timer_running and self._remaining_seconds > 0:
            if not self._timer_paused:
                self._remaining_seconds -= 1
                self._update_timer_display()
            time.sleep(1)
        
        if self._remaining_seconds == 0:
            self._timer_running = False
            try:
                self._start_btn.current.text = "Iniciar"
                self._start_btn.current.update()
            except:
                pass

    def _start_timer(self, e):
        """Inicia o reanuda el temporizador."""
        if not self._timer_running:
            self._timer_running = True
            self._timer_paused = False
            try:
                self._start_btn.current.text = "Pausar"
                self._start_btn.current.disabled = False
                self._start_btn.current.update()
            except:
                pass
            self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
            self._timer_thread.start()

    def _pause_timer(self, e):
        """Pausa o reanuda el temporizador."""
        if self._timer_running:
            self._timer_paused = not self._timer_paused
            try:
                self._start_btn.current.text = "Reanudar" if self._timer_paused else "Pausar"
                self._start_btn.current.update()
            except:
                pass

    def _reset_timer(self, e):
        """Reinicia el temporizador."""
        self._timer_running = False
        self._timer_paused = False
        self._remaining_seconds = self._total_seconds
        self._update_timer_display()
        try:
            self._start_btn.current.text = "Iniciar"
            self._start_btn.current.disabled = False
            self._start_btn.current.update()
        except:
            pass

    def _set_custom_time(self, e):
        """Establece tiempo personalizado."""
        try:
            minutes = int(self._time_input.current.value or 25)
            self._total_seconds = minutes * 60
            self._remaining_seconds = self._total_seconds
            self._update_timer_display()
            self._reset_timer(None)
        except:
            pass

    def _build_step_row_control(self, step: dict) -> ft.Control:
        def _on_change(e):
            step["completed"] = e.control.value

        return ft.Row([
            ft.Checkbox(
                value=step["completed"],
                on_change=_on_change,
                active_color="#4F46E5",
            ),
            ft.Container(
                width=8,
                height=36,
                border_radius=4,
                bgcolor=ft.Colors.with_opacity(0.3, "#4F46E5"),
            ),
            ft.Container(width=10),
            ft.Column([
                ft.Text(step["title"], size=15, weight="bold", color="#0F172A"),
                ft.Text(step["desc"], size=11, color="#64748B"),
            ], spacing=2, expand=True),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                icon_size=18,
                tooltip="Eliminar paso",
                on_click=lambda e: self._delete_pomodoro_step(step["id"]),
            ),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _delete_pomodoro_step(self, step_id: int):
        self._pomodoro_steps = [s for s in self._pomodoro_steps if s["id"] != step_id]
        self._refresh_pomodoro_steps()

    def _refresh_pomodoro_steps(self):
        if self._steps_list_column:
            self._steps_list_column.controls = [self._build_step_row_control(s) for s in self._pomodoro_steps]
            try: self._steps_list_column.update()
            except: pass

    def _add_pomodoro_step(self, e):
        title = self._new_step_title.current.value.strip()
        desc = self._new_step_desc.current.value.strip()
        if not title:
            return
        new_id = max([s["id"] for s in self._pomodoro_steps]) + 1 if self._pomodoro_steps else 0
        self._pomodoro_steps.append({
            "id": new_id,
            "title": title,
            "desc": desc,
            "completed": False
        })
        self._new_step_title.current.value = ""
        self._new_step_desc.current.value = ""
        try:
            self._new_step_title.current.update()
            self._new_step_desc.current.update()
        except: pass
        self._refresh_pomodoro_steps()

    def _show_technique_apply(self, tech: dict):
        """Muestra pantalla de aplicación de técnica (Fase 3) - Diseño Figma."""
        if not self._is_pomodoro(tech):
            self._show_technique_detail(tech)
            return

        colors = self._get_theme_colors()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        navbar = self._build_navbar("Aplicar Técnica Pomodoro")
        card_bg = colors["surface"]
        
        def _back(e):
            self._timer_running = False
            self._current_view = "detail"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")
        
        def _finish(e):
            self._timer_running = False
            self._current_view = "list"
            from services.navigation_service import NavigationController
            NavigationController.update_view("Tecnicas")

        # Cargar los pasos iniciales en la columna
        self._steps_list_column.controls = [self._build_step_row_control(s) for s in self._pomodoro_steps]

        add_step_row = ft.Row([
            ft.TextField(
                ref=self._new_step_title,
                hint_text="Paso...",
                text_size=12,
                height=36,
                border_radius=8,
                expand=2,
            ),
            ft.TextField(
                ref=self._new_step_desc,
                hint_text="Descripción...",
                text_size=12,
                height=36,
                border_radius=8,
                expand=3,
            ),
            ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                icon_color="#4F46E5",
                icon_size=24,
                tooltip="Agregar paso",
                on_click=self._add_pomodoro_step,
            ),
        ], spacing=8)

        procedure_card = ft.Container(
            bgcolor=card_bg,
            border_radius=20,
            padding=ft.padding.all(24),
            shadow=ft.BoxShadow(
                blur_radius=20, spread_radius=-4,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.ASSIGNMENT_OUTLINED, color="#4F46E5", size=22),
                        bgcolor=ft.Colors.with_opacity(0.1, "#4F46E5"),
                        width=44, height=44, border_radius=22,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text("Procedimiento", size=22, weight="bold", color="#0F172A"),
                        ft.Text("Sigues estos pasos para aplicar la técnica", size=12, color="#64748B"),
                    ], spacing=2),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(color="#F1F5F9", height=20),
                self._steps_list_column,
                ft.Divider(color="#F1F5F9", height=20),
                add_step_row,
                ft.Divider(color="#F1F5F9", height=20),
                ft.Text("Consejo", size=14, weight="bold", color="#0F172A"),
                ft.Text(
                    "Mantén el enfoque y evita revisar el celular durante el tiempo de estudio",
                    size=12, color="#64748B",
                ),
            ], spacing=10),
        )

        def _open_edit_time_dialog(e):
            time_field = ft.TextField(
                value=str(self._total_seconds // 60),
                label="Minutos de enfoque",
                text_size=14,
                border_radius=8,
                width=150,
                autofocus=True,
            )
            
            def _apply_time(e):
                try:
                    minutes = int(time_field.value.strip())
                    if minutes > 0:
                        self._total_seconds = minutes * 60
                        self._remaining_seconds = self._total_seconds
                        self._update_timer_display()
                        self._reset_timer(None)
                except:
                    pass
                self.page.close(dlg)
                
            dlg = ft.AlertDialog(
                title=ft.Text("Modificar tiempo", size=16, weight="bold"),
                content=ft.Container(
                    content=time_field,
                    padding=10,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                    ft.ElevatedButton("Aplicar", bgcolor="#4F46E5", color="white", on_click=_apply_time),
                ],
            )
            self.page.open(dlg)

        # Temporizador circular
        timer_card = ft.Container(
            bgcolor=card_bg,
            border_radius=20,
            padding=ft.padding.all(28),
            shadow=ft.BoxShadow(
                blur_radius=20, spread_radius=-4,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column([
                ft.Row([
                    ft.Text("Temporizador", size=18, weight="bold", color="#0F172A"),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_size=18,
                        icon_color="#4F46E5",
                        tooltip="Modificar tiempo",
                        on_click=_open_edit_time_dialog,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=16),
                # Relój circular
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Container(
                        width=220, height=220,
                        border_radius=110,
                        bgcolor="#F8FAFC",
                        border=ft.border.all(8, "#4F46E5"),
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Text(
                                ref=self._timer_display,
                                value="25:00",
                                size=52,
                                weight="bold",
                                color="#0F172A",
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text("Tiempo de enfoque", size=12, color="#64748B", text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
                    )
                ),
                ft.Container(height=24),
                # Botones de control
                ft.Row([
                    ft.ElevatedButton(
                        ref=self._start_btn,
                        text="Iniciar",
                        bgcolor="#4F46E5",
                        color=ft.Colors.WHITE,
                        expand=True,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=self._start_timer,
                    ),
                    ft.ElevatedButton(
                        ref=self._pause_btn,
                        text="Pausar",
                        bgcolor="#F1F5F9",
                        color="#0F172A",
                        expand=True,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=self._pause_timer,
                    ),
                    ft.ElevatedButton(
                        ref=self._reset_btn,
                        text="Reiniciar",
                        bgcolor="#F1F5F9",
                        color="#0F172A",
                        expand=True,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=self._reset_timer,
                    ),
                ], spacing=10),
                ft.Container(height=16),
                # Siguiente descanso
                ft.Container(
                    bgcolor="#F8FAFC",
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    content=ft.Row([
                        ft.Text("Siguiente descanso", size=14, weight="bold", color="#0F172A"),
                        ft.Container(expand=True),
                        ft.Text("05:00", size=14, weight="bold", color="#4F46E5"),
                    ])
                ),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        )

        is_mob = self.is_mobile()
        if is_mob:
            cards_layout = ft.Column([
                timer_card,
                ft.Container(height=20),
                procedure_card,
                ft.Container(height=20),
                ft.ElevatedButton(
                    "¡Termine!",
                    bgcolor="#08015c",
                    color=ft.Colors.WHITE,
                    width=280,
                    height=52,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    on_click=_finish,
                )
            ], spacing=0)
        else:
            cards_layout = ft.Row([
                ft.Column([
                    timer_card,
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "¡Termine!",
                        bgcolor="#08015c",
                        color=ft.Colors.WHITE,
                        expand=True,
                        height=52,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=_finish,
                    ),
                ], expand=True, spacing=0),
                ft.Container(width=30),
                ft.Container(expand=True, content=procedure_card),
            ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START, spacing=0)


        body = ft.Container(
            expand=True,
            bgcolor="#F8FAFC",
            padding=ft.padding.all(16 if is_mob else 40),
            content=ft.Column([
                # Volver
                ft.GestureDetector(
                    on_tap=_back,
                    content=ft.Row([
                        ft.Icon(ft.Icons.ARROW_BACK, size=18, color="#4F46E5"),
                        ft.Text("Volver", size=13, color="#4F46E5"),
                    ], spacing=6)
                ),
                ft.Container(height=12),
                ft.Text("Aplicar la Técnica Pomodoro", size=22 if is_mob else 32, weight="bold", color="#0F172A"),
                ft.Text("Sigue cada paso y administra tu tiempo de estudio.", size=12 if is_mob else 14, color="#64748B"),
                ft.Container(height=20),
                cards_layout,
            ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)
        )


        apply_content = ft.Column([navbar, body], expand=True, spacing=0)
        self._render_view(apply_content)

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
        import os
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("nav_techniques"))

        is_mob = self.is_mobile()

        # HERO BANNER (Figma design) - Adaptable a móvil
        hero = ft.Container(
            bgcolor=colors["surface"],
            padding=ft.padding.all(16 if is_mob else 24),
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            content=ft.Row([
                ft.Column([
                    ft.Text("Técnicas de estudio", size=20 if is_mob else 32, weight="bold", color=colors["text"]),
                    ft.Container(height=4),
                    ft.Text(
                        "Explora diferentes métodos para mejorar tu aprendizaje.",
                        size=12 if is_mob else 14, color=colors["text_muted"], max_lines=2
                    ),
                ], expand=True, spacing=0),
                ft.Image(
                    src=os.path.join("assets", "figma_assets", "books_apple.jpg"),
                    width=80 if is_mob else 140,
                    height=80 if is_mob else 140,
                    fit=ft.ImageFit.CONTAIN,
                ) if not is_mob else ft.Container(),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        search_field = ft.TextField(
            hint_text="Buscar técnicas...",
            prefix_icon=ft.Icons.SEARCH,
            expand=is_mob,
            width=None if is_mob else 320,
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
            spacing=16,
            run_spacing=16,
        )

        main_body = ft.Container(
            expand=True,
            content=ft.Column([
                ft.Container(padding=ft.padding.only(left=12 if is_mob else 28, right=12 if is_mob else 28, top=12 if is_mob else 28), content=hero),
                ft.Container(
                    padding=ft.padding.only(left=12 if is_mob else 28, right=12 if is_mob else 28, top=16, bottom=24),
                    content=ft.Column([
                        search_field,
                        ft.Container(height=12),
                        self._grid_container,
                        ft.Container(height=24),
                    ], spacing=0, expand=True)
                )
            ], scroll=get_scroll_mode(self.page), expand=True)
        )

        controls = [navbar, main_body]
        if is_mob:
            controls.append(self._build_bottom_nav("Tecnicas"))

        return ft.Column(controls, expand=True, spacing=0)

