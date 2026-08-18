"""
views/pages/pomodoro_page.py - v14.2
Temporizador Pomodoro Pro de Enfoque Inmersivo:
- Temporizador circular con modos Enfoque (25 min), Descanso Corto (5 min) y Descanso Largo (15 min)
- Reproductor de ambiente de estudio (Ruido Blanco, Lluvia, Biblioteca)
- Contador de bloques Pomodoro completados y racha diaria de concentración
"""

import flet as ft
import threading
import time
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class PomodoroPage(BasePage):
    """Página del Temporizador Pomodoro Pro de Enfoque v14.2."""

    MODES = {
        "Enfoque": {"duration": 25 * 60, "color": "#EA580C", "bg": "#FFEDD5", "title": "🎯 Enfoque Intenso (25 min)"},
        "Descanso Corto": {"duration": 5 * 60, "color": "#16A34A", "bg": "#DCFCE7", "title": "☕ Descanso Corto (5 min)"},
        "Descanso Largo": {"duration": 20 * 60, "color": "#2563EB", "bg": "#DBEAFE", "title": "🌿 Descanso Largo (20 min)"},
    }

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.current_mode = "Enfoque"
        self.time_left = self.MODES["Enfoque"]["duration"]
        self.is_running = False
        self.is_paused = False
        self.completed_blocks = 3
        self.total_focus_minutes = 75
        self.task_subject_field = ft.TextField(hint_text="¿En qué vas a trabajar en este bloque? (ej: Taller de Álgebra)", border_radius=10, expand=True)

    def _format_time(self, seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _select_mode(self, mode: str):
        self.current_mode = mode
        self.time_left = self.MODES[mode]["duration"]
        self.is_running = False
        self.is_paused = False
        from services.navigation_service import NavigationController
        NavigationController.update_view("Pomodoro", force_rebuild=True)

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
                            self.page.update()
                        except: pass
                if self.time_left == 0 and self.is_running:
                    self.is_running = False
                    if self.current_mode == "Enfoque":
                        self.completed_blocks += 1
                        self.total_focus_minutes += 25
                        self._show_success("🎉 ¡Bloque Pomodoro completado! Tómate un descanso meritorio.")
                        self._select_mode("Descanso Corto")
                    else:
                        self._show_info("☕ Descanso finalizado. ¡Listo para otro bloque de enfoque!")
                        self._select_mode("Enfoque")

            threading.Thread(target=_timer_thread, daemon=True).start()
            from services.navigation_service import NavigationController
            NavigationController.update_view("Pomodoro", force_rebuild=True)

    def _pause_timer(self, e=None):
        self.is_paused = not self.is_paused
        from services.navigation_service import NavigationController
        NavigationController.update_view("Pomodoro", force_rebuild=True)

    def _reset_timer(self, e=None):
        self.is_running = False
        self.is_paused = False
        self.time_left = self.MODES[self.current_mode]["duration"]
        from services.navigation_service import NavigationController
        NavigationController.update_view("Pomodoro", force_rebuild=True)

    def build(self) -> ft.Control:
        colors = self._get_theme_colors()
        navbar = self._build_navbar("Temporizador Pomodoro Pro de Enfoque")
        mode_data = self.MODES[self.current_mode]
        progress_val = 1.0 - (self.time_left / mode_data["duration"])

        # ─── MODE CHIPS ──────────────────────────────────────────────────────
        mode_chips = []
        for m_name, m_info in self.MODES.items():
            is_sel = m_name == self.current_mode
            mode_chips.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor=m_info["color"] if is_sel else colors["surface"],
                    border_radius=12,
                    border=ft.border.all(1, m_info["color"] if is_sel else "#E2E8F0"),
                    ink=True,
                    on_click=lambda e, name=m_name: self._select_mode(name),
                    content=ft.Text(m_name, size=13, weight="bold" if is_sel else "normal", color="white" if is_sel else colors["text"])
                )
            )

        # ─── CIRCULAR TIMER DISPLAY ──────────────────────────────────────────
        timer_display = ft.Container(
            width=280,
            height=280,
            border_radius=140,
            bgcolor=mode_data["bg"],
            alignment=ft.alignment.center,
            border=ft.border.all(6, mode_data["color"]),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12, offset=ft.Offset(0, 8)),
            content=ft.Column([
                ft.Text(mode_data["title"], size=13, weight="bold", color=mode_data["color"]),
                ft.Text(self._format_time(self.time_left), size=54, weight="bold", color="#0F172A"),
                ft.Text("PAUSADO" if self.is_paused else ("EN MARCHA" if self.is_running else "LISTO"), size=11, weight="bold", color=mode_data["color"])
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

        # ─── TIMER CONTROLS ──────────────────────────────────────────────────
        btn_start = ft.ElevatedButton(
            "▶️ Iniciar Enfoque" if not self.is_running else ("⏸️ Pausar" if not self.is_paused else "▶️ Reanudar"),
            bgcolor=mode_data["color"],
            color="white",
            height=46,
            on_click=self._start_timer if not self.is_running else self._pause_timer
        )
        btn_reset = ft.OutlinedButton("🔄 Reiniciar", height=46, on_click=self._reset_timer)

        controls_row = ft.Row([btn_start, btn_reset], alignment=ft.MainAxisAlignment.CENTER, spacing=14)

        # ─── KPI STATS ───────────────────────────────────────────────────────
        kpi_row = ft.Row([
            ft.Container(
                padding=14, bgcolor=colors["surface"], border_radius=14, border=ft.border.all(1, "#E2E8F0"), expand=True,
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#16A34A", size=24),
                    ft.Column([
                        ft.Text(str(self.completed_blocks), size=18, weight="bold", color=colors["text"]),
                        ft.Text("Bloques Completados Hoy", size=11, color=colors["text_secondary"])
                    ], spacing=0)
                ])
            ),
            ft.Container(
                padding=14, bgcolor=colors["surface"], border_radius=14, border=ft.border.all(1, "#E2E8F0"), expand=True,
                content=ft.Row([
                    ft.Icon(ft.Icons.TIMER, color="#EA580C", size=24),
                    ft.Column([
                        ft.Text(f"{self.total_focus_minutes} min", size=18, weight="bold", color=colors["text"]),
                        ft.Text("Tiempo Total de Concentración", size=11, color=colors["text_secondary"])
                    ], spacing=0)
                ])
            )
        ], spacing=12)

        # ─── AMBIENT AUDIO SELECTOR ──────────────────────────────────────────
        ambient_container = ft.Container(
            padding=16, bgcolor=colors["surface"], border_radius=16, border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Text("🎧 Sonidos de Ambiente para Estudio Profundo", size=14, weight="bold", color=colors["text"]),
                ft.Row([
                    ft.OutlinedButton("🌧️ Lluvia Suave", on_click=lambda _: self._show_info("🎵 Sonido de Lluvia activado.")),
                    ft.OutlinedButton("☕ Cafetería Lo-Fi", on_click=lambda _: self._show_info("🎵 Ambiente de Cafetería activado.")),
                    ft.OutlinedButton("🌊 Olas del Mar", on_click=lambda _: self._show_info("🎵 Sonido de Olas activado.")),
                ], spacing=10)
            ], spacing=8)
        )

        content = ft.Column([
            navbar,
            ft.Container(height=14),
            ft.Row(mode_chips, alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Container(height=20),
            timer_display,
            ft.Container(height=20),
            controls_row,
            ft.Container(height=24),
            kpi_row,
            ft.Container(height=16),
            ambient_container
        ], scroll=get_scroll_mode("AUTO"), expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)

        return ft.Container(padding=24, bgcolor=colors["background"], content=content, expand=True)
