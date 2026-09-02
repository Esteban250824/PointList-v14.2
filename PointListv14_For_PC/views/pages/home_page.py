"""
pages/home_page.py
PointList v13.5
Página principal de la aplicación con diseño de Dashboard Figma completo,
soporte para modo oscuro dinámico y multi-idioma (i18n).
"""

import flet as ft
import copy
from datetime import datetime
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class HomePage(BasePage):
    """Página de inicio con vista general del estado académico del usuario."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._db = None
        self._user = None
        self.file_picker = ft.FilePicker()
        if self.page and hasattr(self.page, "overlay"):
            self.page.overlay.append(self.file_picker)

    def _get_db_and_user(self):
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db   = db
        self._user = NavigationController.get_current_user()

    def build(self) -> ft.Control:
        self._get_db_and_user()
        from services.navigation_service import NavigationController
        colors = self._get_theme_colors()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK

        user_name = self._user.get("nombre_usuario", self._user.get("name", "Juan"))
        is_mobile = (self.page.width or 1200) < 900

        # ─── Cabecera Superior (Navbar) ──────────────────────────────────────
        navbar = self._build_navbar(self.translate("nav_home"))

        notes = None
        if self._user and self._user.get("id"):
            try:
                notes = self._db.obtener_notas(self._user.get("id"))
                if notes:
                    NavigationController.cache["notes"] = copy.deepcopy(notes)
            except Exception as e:
                print(f"[HomePage] Error leyendo notas de PostgreSQL: {e}")

        if not notes:
            notes = NavigationController.cache.get("notes", [])

        events = None
        if self._user and self._user.get("id"):
            try:
                events = self._db.obtener_eventos(self._user.get("id"))
            except: pass
        if not events:
            events = NavigationController.cache.get("calendar_events", [])

        grades = [float(n.get("calificacion", 0)) for n in notes]
        avg_grade = (sum(grades) / len(grades)) if grades else 0.0
        unique_subjects = list(set([n.get("asignatura", "") for n in notes if n.get("asignatura")]))
        num_subjects = len(unique_subjects)

        excelentes = sum(1 for g in grades if g >= 4.5)
        buenas = sum(1 for g in grades if 3.0 <= g < 4.5)
        bajas = sum(1 for g in grades if g < 3.0)
        total_grades = len(grades)

        num_events = len(events) if events else 4

        # ─── Fila de 4 Tarjetas de Estadísticas ─────────────────────────────
        # ─── Fila de 4 Tarjetas de Estadísticas (Accesos Directos) ─────────────
        def build_stat_card(num, title, extra, icon, bg_color_light, bg_color_dark, text_color_light, text_color_dark, icon_bg_light, icon_bg_dark, on_click=None):
            bg_col = bg_color_dark if is_dark else bg_color_light
            txt_col = text_color_dark if is_dark else text_color_light
            ic_bg = icon_bg_dark if is_dark else icon_bg_light
            return ft.Container(
                bgcolor=bg_col,
                border_radius=16,
                padding=16,
                expand=True,
                border=ft.border.all(1, colors["border"]),
                ink=True if on_click else False,
                on_click=on_click,
                tooltip=f"Ver {title}",
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=txt_col, size=24),
                        bgcolor=ic_bg,
                        width=48,
                        height=48,
                        border_radius=24,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(num, size=26, weight=ft.FontWeight.BOLD, color=colors["stat_num"]),
                        ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=colors["stat_num"]),
                        ft.Text(extra, size=11, color=colors["text_muted"]),
                    ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        stats_row = ft.Row([
            build_stat_card(str(num_subjects), self.translate("stat_subjects"), self.translate("stat_subjects_sub"), ft.Icons.BOOK, "#F3E8FF", "#2E1065", "#7C3AED", "#C084FC", "#E9D5FF", "#3B0764", on_click=lambda e: NavigationController.update_view("Materias")),
            build_stat_card(f"{avg_grade:.1f}", self.translate("stat_average"), self.translate("stat_average_sub"), ft.Icons.SHOW_CHART, "#DCFCE7", "#064E3B", "#15803D", "#4ADE80", "#BBF7D0", "#022C22", on_click=lambda e: NavigationController.update_view("Notas")),
            build_stat_card("85%", self.translate("stat_tasks"), self.translate("stat_tasks_sub"), ft.Icons.CHECKLIST, "#E0F2FE", "#1E3A8A", "#4338CA", "#818CF8", "#E0E7FF", "#172554", on_click=lambda e: NavigationController.update_view("Asignaciones")),
            build_stat_card(str(num_events), self.translate("stat_events"), self.translate("stat_events_sub"), ft.Icons.CALENDAR_MONTH, "#FEE2E2", "#7F1D1D", "#B91C1C", "#FCA5A5", "#FECACA", "#450A0A", on_click=lambda e: NavigationController.update_view("Calendario")),
        ], spacing=16)

        # ─── Grid de 3 Columnas: Detalles de Dashboard ──────────────────────
        # Columna 1: Técnicas de estudio recomendadas
        def build_tech_row(title, desc, icon, icon_color, icon_bg_light, icon_bg_dark):
            ic_bg = icon_bg_dark if is_dark else icon_bg_light
            return ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=18),
                    bgcolor=ic_bg,
                    width=32,
                    height=32,
                    border_radius=16,
                    alignment=ft.alignment.center
                ),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(desc, size=9.5, color=colors["text_muted"]),
                ], spacing=1, expand=True)
            ])

        tecnicas_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            width=None,
            height=240,
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Text(self.translate("tech_recommended"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Container(expand=True),
                    ft.TextButton(self.translate("tech_view_all"), style=ft.ButtonStyle(padding=0), on_click=lambda e: NavigationController.update_view("Tecnicas"))
                ]),
                ft.Container(height=4),
                build_tech_row(self.translate("tech_mindmaps_title"), self.translate("tech_mindmaps_desc"), ft.Icons.PSYCHOLOGY, "#7C3AED", "#F3E8FF", "#3B0764"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_tech_row(self.translate("tech_cornell_title"), self.translate("tech_cornell_desc"), ft.Icons.ASSIGNMENT, "#0D9488", "#CCFBF1", "#042F2E"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_tech_row(self.translate("tech_spaced_title"), self.translate("tech_spaced_desc"), ft.Icons.DONE_ALL, "#4F46E5", "#EEF2FF", "#1E1B4B"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_tech_row(self.translate("tech_pomodoro_title"), self.translate("tech_pomodoro_desc"), ft.Icons.TIMER, "#EF4444", "#FEE2E2", "#450A0A"),
            ], spacing=4)
        )

        # Columna 2: Distribución de calificaciones
        pie_chart = ft.PieChart(
            sections=[
                ft.PieChartSection(value=excelentes if excelentes > 0 else 0.001, color="#10B981", radius=18),
                ft.PieChartSection(value=buenas if buenas > 0 else 0.001, color="#8B5CF6", radius=18),
                ft.PieChartSection(value=bajas if bajas > 0 else 0.001, color="#EF4444", radius=18),
            ],
            sections_space=2,
            center_space_radius=30,
            expand=True
        )

        chart_stack = ft.Stack([
            pie_chart,
            ft.Container(
                content=ft.Column([
                    ft.Text(str(total_grades), size=20, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(self.translate("chart_total"), size=10, color=colors["text_muted"]),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                alignment=ft.alignment.center
            )
        ], width=110, height=110)

        def build_legend_item(color, label, val_str):
            return ft.Row([
                ft.Container(width=10, height=10, border_radius=5, bgcolor=color),
                ft.Container(width=8),
                ft.Text(label, size=11, color=colors["text"], weight=ft.FontWeight.W_500),
                ft.Container(expand=True),
                ft.Text(val_str, size=11, color=colors["text_muted"])
            ])

        total_denom = total_grades if total_grades > 0 else 1
        dist_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            height=240,
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Text(self.translate("chart_distribution"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Container(expand=True),
                    ft.TextButton(self.translate("tech_view_details"), on_click=lambda e: NavigationController.update_view("Notas"))
                ]),
                ft.Container(height=4),
                ft.Row([
                    chart_stack,
                    ft.Container(width=8),
                    ft.Column([
                        build_legend_item("#10B981", self.translate("chart_excellent"), f"{excelentes} ({excelentes/total_denom*100:.1f}%)"),
                        build_legend_item("#8B5CF6", self.translate("chart_good"), f"{buenas} ({buenas/total_denom*100:.1f}%)"),
                        build_legend_item("#EF4444", self.translate("chart_low"), f"{bajas} ({bajas/total_denom*100:.1f}%)"),
                    ], spacing=8, expand=True)
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=6)
        )

        # Columna 3: Asignaturas
        def build_subject_row(name, desc, badge_color):
            return ft.Row([
                ft.Container(width=10, height=32, border_radius=6, bgcolor=badge_color),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(name, size=12, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(desc, size=9.5, color=colors["text_muted"]),
                ], spacing=1, expand=True)
            ])

        asignaturas_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            height=240,
            expand=True,
            content=ft.Column([
                ft.Row([
                    ft.Text(self.translate("sidebar_asignaturas"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Container(expand=True),
                    ft.TextButton(self.translate("tech_view_all"), style=ft.ButtonStyle(padding=0), on_click=lambda e: NavigationController.update_view("Materias"))
                ]),
                ft.Container(height=4),
                build_subject_row(self.translate("subj_math"), self.translate("subj_math_desc"), "#F472B6"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_subject_row(self.translate("subj_cs"), self.translate("subj_cs_desc"), "#3B82F6"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_subject_row(self.translate("subj_eng"), self.translate("subj_eng_desc"), "#A78BFA"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_subject_row(self.translate("subj_phys"), self.translate("subj_phys_desc"), "#4ADE80"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_subject_row(self.translate("subj_values"), self.translate("subj_values_desc"), "#F59E0B"),
            ], spacing=3, scroll=ft.ScrollMode.HIDDEN)
        )

        grid_row = ft.Row([
            tecnicas_box,
            dist_box,
            asignaturas_box
        ], spacing=16)

        # ─── Sección Inferior: Tareas Próximas ─────────────────────────────
        def build_task_row(title, course, is_green):
            icon_color = "#16A34A" if is_green else "#2563EB"
            icon_bg = ("#064E3B" if is_dark else "#DCFCE7") if is_green else ("#1E3A8A" if is_dark else "#DBEAFE")
            return ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.CHECKLIST, color=icon_color, size=16),
                    bgcolor=icon_bg,
                    width=28,
                    height=28,
                    border_radius=14,
                    alignment=ft.alignment.center
                ),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(course, size=9.5, color=colors["text_muted"]),
                ], spacing=1, expand=True)
            ])

        tareas_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            content=ft.Column([
                ft.Row([
                    ft.Text(self.translate("tasks_upcoming"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Container(expand=True),
                    ft.TextButton(self.translate("tech_view_all"), style=ft.ButtonStyle(padding=0), on_click=lambda e: NavigationController.update_view("Asignaciones"))
                ]),
                ft.Container(height=4),
                build_task_row(self.translate("task_report"), self.translate("subj_cs"), True),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_task_row(self.translate("task_derivatives"), self.translate("subj_math"), False),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_task_row(self.translate("task_essay"), self.translate("subj_values"), True),
            ], spacing=4)
        )

        # ─── Principal de Contenido ───
        dashboard_content = ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor=colors["background"],
            content=ft.Column([
                ft.Column([
                    ft.Text(self.translate("welcome_user").format(name=user_name), size=28, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(self.translate("welcome_subtitle"), size=14, color=colors["text_secondary"]),
                ], spacing=2),
                ft.Container(height=12),
                stats_row,
                ft.Container(height=12),
                grid_row,
                ft.Container(height=12),
                tareas_box
            ], spacing=0, scroll=get_scroll_mode(self.page))
        )

        main_layout = ft.Row([dashboard_content], expand=True, spacing=0)

        return ft.Column(
            controls=[
                navbar,
                main_layout
            ],
            expand=True,
            spacing=0,
        )
