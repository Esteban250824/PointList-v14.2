"""
views/pages/pomodoro_page.py - v15.0
Temporizador Pomodoro Pro de Enfoque Inmersivo + Área de Tareas Personalizadas:
- Temporizador en tiempo real segundo a segundo
- Encabezado con '← Volver', 'Aplicar la Técnica Pomodoro' y tarjeta superior de 'Consejo'
- Sección de 'Tareas Personalizadas de Enfoque' con creación rápida de tareas y lista de verificación (checkboxes)
- Columna izquierda 'Procedimiento' con pasos 1-5 (tiempos modificables)
- Tarjeta oscura 'Temporizador' con fondo #0B192C, arco neón verde y botones funcionales
- Banner inferior con botón '¡Termine!'
"""

import flet as ft
import threading
import time
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class PomodoroPage(BasePage):
    """Página del Temporizador Pomodoro Pro de Enfoque v15.0."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.focus_minutes = 25
        self.break_minutes = 5
        self.long_break_minutes = 15
        self.current_mode = "Enfoque"
        self.time_left = self.focus_minutes * 60
        self.is_running = False
        self.is_paused = False
        self.timer_text_ref = ft.Ref[ft.Text]()
        self.next_break_text_ref = ft.Ref[ft.Text]()
        self.custom_tasks = [
            {"text": "Resolver ejercicios de prueba", "completed": False},
            {"text": "Repasar apuntes principales", "completed": False}
        ]
        self.custom_tasks_column = ft.Column(spacing=6)

    def _format_time(self, seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _start_timer(self, e=None):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            
            def _timer_thread():
                while self.is_running and self.time_left > 0:
                    time.sleep(1)
                    if not self.is_paused:
                        self.time_left -= 1
                        try:
                            if self.timer_text_ref.current:
                                self.timer_text_ref.current.value = self._format_time(self.time_left)
                                self.timer_text_ref.current.update()
                        except: pass

                if self.time_left == 0 and self.is_running:
                    self.is_running = False
                    if self.current_mode == "Enfoque":
                        self._show_success("🎉 ¡Bloque Pomodoro completado! Tómate un descanso meritorio.")
                        self.current_mode = "Descanso"
                        self.time_left = self.break_minutes * 60
                    else:
                        self._show_info("☕ Descanso finalizado. ¡Listo para otro bloque de enfoque!")
                        self.current_mode = "Enfoque"
                        self.time_left = self.focus_minutes * 60
                    try:
                        if self.timer_text_ref.current:
                            self.timer_text_ref.current.value = self._format_time(self.time_left)
                            self.timer_text_ref.current.update()
                    except: pass

            threading.Thread(target=_timer_thread, daemon=True).start()
            try:
                if self.timer_text_ref.current:
                    self.timer_text_ref.current.value = self._format_time(self.time_left)
                    self.timer_text_ref.current.update()
            except: pass

    def _pause_timer(self, e=None):
        if self.is_running:
            self.is_paused = not self.is_paused

    def _reset_timer(self, e=None):
        self.is_running = False
        self.is_paused = False
        self.time_left = (self.focus_minutes if self.current_mode == "Enfoque" else self.break_minutes) * 60
        try:
            if self.timer_text_ref.current:
                self.timer_text_ref.current.value = self._format_time(self.time_left)
                self.timer_text_ref.current.update()
        except: pass

    def _update_timer_ui(self):
        try:
            if self.timer_text_ref.current:
                self.timer_text_ref.current.value = self._format_time(self.time_left)
                self.timer_text_ref.current.update()
        except: pass
        from services.navigation_service import NavigationController
        NavigationController.update_view("Pomodoro", force_rebuild=True)

    def _add_custom_task(self, task_input_field):
        val = task_input_field.value.strip()
        if not val: return
        self.custom_tasks.append({"text": val, "completed": False})
        task_input_field.value = ""
        try: task_input_field.update()
        except: pass
        self._render_custom_tasks()

    def _render_custom_tasks(self):
        colors = self._get_theme_colors()
        controls = []
        for idx, t in enumerate(self.custom_tasks):
            def _toggle(e, i=idx):
                self.custom_tasks[i]["completed"] = e.control.value
                self._render_custom_tasks()

            def _del(e, i=idx):
                self.custom_tasks.pop(i)
                self._render_custom_tasks()

            controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    bgcolor="#F8FAFC" if not t["completed"] else "#F1F5F9",
                    border_radius=8,
                    content=ft.Row([
                        ft.Checkbox(value=t["completed"], on_change=lambda e, i=idx: _toggle(e, i), active_color="#22C55E"),
                        ft.Text(t["text"], size=12, color=colors["text_secondary"] if t["completed"] else colors["text"], expand=True),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color="#EF4444", on_click=lambda e, i=idx: _del(e, i))
                    ], spacing=6)
                )
            )
        self.custom_tasks_column.controls = controls
        try: self.custom_tasks_column.update()
        except: pass

    def _open_edit_settings_dialog(self, e=None):
        focus_f = ft.TextField(label="Tiempo de Enfoque (minutos)", value=str(self.focus_minutes), border_radius=10)
        break_f = ft.TextField(label="Tiempo de Descanso (minutos)", value=str(self.break_minutes), border_radius=10)

        def _save(e):
            try:
                self.focus_minutes = max(1, int(focus_f.value))
                self.break_minutes = max(1, int(break_f.value))
                self._reset_timer()
                self.page.close(dlg)
                self._show_success("⏱️ Tiempos de Pomodoro actualizados correctamente.")
            except:
                self._show_error("Ingresa números válidos.")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Modificar Tiempos de Pomodoro", size=16, weight="bold"),
            content=ft.Column([
                ft.Text("Personaliza la duración de tus bloques de trabajo y descanso:"),
                ft.Container(height=8),
                focus_f,
                break_f,
            ], spacing=6, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Guardar", bgcolor="#22C55E", color="white", on_click=_save)
            ]
        )
        self.page.open(dlg)

    def build(self) -> ft.Control:
        colors = self._get_theme_colors()
        from services.navigation_service import NavigationController
        navbar = self._build_navbar("Pomodoro Pro")

        # ─── HEADER BAR WITH VOLVER BUTTON & TITLE ────────────────────────────
        btn_back = ft.OutlinedButton(
            "← Volver",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=lambda e: NavigationController.update_view("Tecnicas")
        )

        title_header = ft.Column([
            btn_back,
            ft.Container(height=6),
            ft.Text("Aplicar la Técnica Pomodoro", size=28, weight="bold", color=colors["text"]),
            ft.Text("Sigue cada paso y administra tu tiempo de estudio.", size=13, color=colors["text_secondary"]),
        ], spacing=2)

        # ─── TOP RIGHT CONSEJO BOX ───────────────────────────────────────────
        advice_box = ft.Container(
            padding=16,
            bgcolor="#F0FDF4",
            border_radius=16,
            border=ft.border.all(1, "#DCFCE7"),
            content=ft.Row([
                ft.Container(
                    width=40, height=40, border_radius=20, bgcolor="#DCFCE7",
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color="#16A34A", size=22)
                ),
                ft.Column([
                    ft.Text("Consejo", size=13, weight="bold", color="#15803D"),
                    ft.Text("Mantener un enfoque y evitar cambiar de tarea durante el tiempo de estudio mejora tu productividad.", size=11, color="#166534")
                ], spacing=1, expand=True)
            ], spacing=12)
        )

        header_row = ft.Row([
            title_header,
            ft.Container(expand=True),
            ft.Container(width=340, content=advice_box)
        ], vertical_alignment=ft.CrossAxisAlignment.START)

        # ─── LEFT COLUMN: PROCEDIMIENTO Y TAREAS PERSONALIZADAS ───────────────
        def step_item(num_str, icon, title, desc, editable=False):
            return ft.Row([
                ft.Container(
                    width=32, height=32, border_radius=16, bgcolor="#DCFCE7",
                    alignment=ft.alignment.center,
                    content=ft.Text(num_str, size=13, weight="bold", color="#16A34A")
                ),
                ft.Container(
                    width=36, height=36, border_radius=10, bgcolor="#F8FAFC",
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon, color="#475569", size=18)
                ),
                ft.Column([
                    ft.Row([
                        ft.Text(title, size=13, weight="bold", color=colors["text"]),
                        ft.IconButton(ft.Icons.EDIT, icon_size=14, icon_color="#0284C7", tooltip="Modificar tiempo", on_click=self._open_edit_settings_dialog) if editable else ft.Container()
                    ], spacing=4),
                    ft.Text(desc, size=11, color=colors["text_secondary"]),
                ], spacing=1, expand=True)
            ], spacing=10)

        # Campo de añadir tarea personalizada de enfoque
        task_input_field = ft.TextField(hint_text="Añade tu tarea personalizada de estudio...", border_radius=10, expand=True, height=40, content_padding=ft.padding.symmetric(horizontal=10, vertical=4))
        btn_add_task = ft.ElevatedButton("➕ Añadir", bgcolor="#22C55E", color="white", height=40, on_click=lambda e: self._add_custom_task(task_input_field))

        self._render_custom_tasks()

        procedimiento_box = ft.Container(
            padding=20,
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Text("Procedimiento", size=16, weight="bold", color=colors["text"]),
                ft.Text("Sigue estos pasos para aplicar la técnica.", size=11, color=colors["text_secondary"]),
                ft.Container(height=8),
                step_item("1", ft.Icons.VOLUME_OFF_OUTLINED, "Elimina distracciones", "Elige un lugar tranquilo en el que vas a trabajar."),
                ft.Divider(height=1, color="#F1F5F9"),
                step_item("2", ft.Icons.PHONELINK_OFF_OUTLINED, "Elimina distracciones", "Silencia notificaciones y evita interrupciones."),
                ft.Divider(height=1, color="#F1F5F9"),
                step_item("3", ft.Icons.ASSIGNMENT_TURNED_IN_OUTLINED, f"Trabaja durante {self.focus_minutes} minutos", "Enfócate por completo hasta que suene la alarma.", editable=True),
                ft.Divider(height=1, color="#F1F5F9"),
                step_item("4", ft.Icons.FREE_BREAKFAST_OUTLINED, f"Descansa {self.break_minutes} minutos", "Relájate y despeja tu mente.", editable=True),
                ft.Divider(height=1, color="#F1F5F9"),
                step_item("5", ft.Icons.AUTORENEW, "Repetir el ciclo", f"Después de 4 pomodoros, toma un descanso largo de {self.long_break_minutes} a 30 minutos."),
                ft.Divider(height=16, color="#E2E8F0"),
                ft.Text("📌 Tareas Personalizadas de la Sesión", size=14, weight="bold", color=colors["text"]),
                ft.Row([task_input_field, btn_add_task], spacing=8),
                ft.Container(height=6),
                self.custom_tasks_column,
                ft.Container(height=10),
                ft.Container(
                    padding=10, bgcolor="#F8FAFC", border_radius=10,
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color="#64748B", size=16),
                        ft.Text("Recuerda: El enfoque constante es la clave para mejores resultados.", size=11, color="#64748B")
                    ], spacing=8)
                )
            ], spacing=6)
        )

        # ─── RIGHT COLUMN: TEMPORIZADOR (DARK BLUE CONTAINER #0B192C) ────────
        timer_box = ft.Container(
            padding=24,
            bgcolor="#0B192C",
            border_radius=20,
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Text("Temporizador", size=16, weight="bold", color="white"),
                    ft.Container(expand=True),
                    ft.Text(f"Tiempo de {self.current_mode.lower()}", size=12, color="#94A3B8")
                ]),
                ft.Container(height=16),
                # Circulo Arco Neon Verde / Purpura
                ft.Container(
                    width=220,
                    height=220,
                    border_radius=110,
                    border=ft.border.all(8, "#22C55E" if self.current_mode == "Enfoque" else "#7C3AED"),
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Text(ref=self.timer_text_ref, value=self._format_time(self.time_left), size=48, weight="bold", color="white"),
                        ft.Text(f"Tiempo de {self.current_mode.lower()}", size=12, color="#22C55E" if self.current_mode == "Enfoque" else "#A78BFA", weight="bold")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
                ),
                ft.Container(height=20),
                # Controles ▶ Iniciar (Verde), ⏸️ Pausar, 🔄 Reiniciar
                ft.Row([
                    ft.ElevatedButton(
                        "▶ Iniciar" if not self.is_running else ("⏸️ Pausar" if not self.is_paused else "▶ Reanudar"),
                        bgcolor="#22C55E",
                        color="white",
                        height=42,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=self._start_timer if not self.is_running else self._pause_timer
                    ),
                    ft.OutlinedButton(
                        "⏸️ Pausar",
                        style=ft.ButtonStyle(color="white", shape=ft.RoundedRectangleBorder(radius=10)),
                        height=42,
                        on_click=self._pause_timer
                    ),
                    ft.OutlinedButton(
                        "🔄 Reiniciar",
                        style=ft.ButtonStyle(color="white", shape=ft.RoundedRectangleBorder(radius=10)),
                        height=42,
                        on_click=self._reset_timer
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Container(height=16),
                ft.Divider(color="#1E293B", height=1),
                ft.Container(height=8),
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.FREE_BREAKFAST, color="#22C55E", size=16),
                        ft.Text("Siguiente descanso", size=12, color="white", weight="bold"),
                    ], spacing=6),
                    ft.Container(expand=True),
                    ft.Text(f"{self.break_minutes:02d}:00", size=13, color="#22C55E", weight="bold")
                ])
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        )

        main_grid = ft.Row([
            ft.Container(width=450, content=procedimiento_box),
            timer_box
        ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)

        # ─── BANNER INFERIOR "¡TERMINE!" ─────────────────────────────────────
        bottom_banner = ft.Container(
            padding=16,
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Row([
                ft.Container(
                    width=36, height=36, border_radius=18, bgcolor="#DCFCE7",
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.AUTORENEW, color="#16A34A", size=20)
                ),
                ft.Column([
                    ft.Text("¿Listo para comenzar?", size=14, weight="bold", color=colors["text"]),
                    ft.Text("Concéntrate y aprovecha al máximo tu tiempo de estudio.", size=12, color=colors["text_secondary"])
                ], spacing=1),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "¡Termine!",
                    bgcolor="#0B192C",
                    color="white",
                    height=44,
                    width=140,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda e: (self._reset_timer(), NavigationController.update_view("Tecnicas"))
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
        )

        body_content = ft.Column([
            header_row,
            ft.Container(height=20),
            main_grid,
            ft.Container(height=20),
            bottom_banner
        ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)

        return ft.Column([
            navbar,
            ft.Container(padding=24, bgcolor=colors["background"], content=body_content, expand=True)
        ], expand=True, spacing=0)
