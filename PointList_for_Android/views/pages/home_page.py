"""
pages/home_page.py
PointList v13 Mobile Responsive
Página principal de la aplicación con Dashboard adaptativo para teléfonos Android y escritorio.
"""

import flet as ft
from datetime import datetime
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class HomePage(BasePage):
    """Página de inicio con vista general del estado académico del usuario."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._db = None
        self._user = None

    def _get_db_and_user(self):
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()

    def build(self) -> ft.Control:
        self._get_db_and_user()
        from services.navigation_service import NavigationController
        colors = self._get_theme_colors()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        is_mob = self.is_mobile()

        user_name = self._user.get("nombre_usuario", self._user.get("name", "Estudiante"))

        # ─── Cabecera Superior (Navbar) ──────────────────────────────────────
        navbar = self._build_navbar(self.translate("nav_home"))

        # ─── Datos Dinámicos / Caché ──────────────────────────────────────────
        if not self._user or not self._user.get("id"):
            from services.navigation_service import NavigationController
            self._user = NavigationController.get_current_user()

        uid = self._user.get("id") if self._user else None

        notes = NavigationController.cache.get("notes", None)
        if (notes is None or not notes) and self._db and uid:
            try:
                notes = self._db.obtener_notas(uid) or []
                if notes:
                    NavigationController.cache["notes"] = notes
            except:
                notes = []

        events = NavigationController.cache.get("events", None)
        if (events is None or not events) and self._db and uid:
            try:
                events = self._db.obtener_agenda(uid) or []
                if events:
                    NavigationController.cache["events"] = events
            except:
                events = []

        if notes:
            grades = [float(n.get("calificacion", 0)) for n in notes]
            avg_grade = sum(grades) / len(grades) if grades else 0.0
            unique_subjects = list(set([n.get("asignatura", "") for n in notes if n.get("asignatura")]))
            num_subjects = len(unique_subjects)


            excelentes = sum(1 for g in grades if g >= 4.5)
            buenas = sum(1 for g in grades if 3.0 <= g < 4.5)
            bajas = sum(1 for g in grades if g < 3.0)
            total_grades = len(grades)
        else:
            avg_grade = 0.0
            num_subjects = 0
            excelentes = 0
            buenas = 0
            bajas = 0
            total_grades = 0

        num_events = len(events)


        # ─── Tarjetas de Estadísticas Adaptables ────────────────────────────
        def build_stat_card(num, title, extra, icon, bg_color_light, bg_color_dark, text_color_light, text_color_dark, icon_bg_light, icon_bg_dark):
            bg_col = bg_color_dark if is_dark else bg_color_light
            txt_col = text_color_dark if is_dark else text_color_light
            ic_bg = icon_bg_dark if is_dark else icon_bg_light
            return ft.Container(
                bgcolor=bg_col,
                border_radius=14,
                padding=ft.padding.symmetric(horizontal=8 if is_mob else 14, vertical=8 if is_mob else 12),
                expand=True,
                border=ft.border.all(1, colors["border"]),
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=txt_col, size=16 if is_mob else 22),
                        bgcolor=ic_bg,
                        width=34 if is_mob else 44,
                        height=34 if is_mob else 44,
                        border_radius=17 if is_mob else 22,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=5 if is_mob else 10),
                    ft.Column([
                        ft.Text(num, size=16 if is_mob else 22, weight=ft.FontWeight.BOLD, color=colors["stat_num"]),
                        ft.Text(title, size=10 if is_mob else 12.5, weight=ft.FontWeight.BOLD, color=colors["stat_num"], max_lines=2, overflow=ft.TextOverflow.VISIBLE),
                        ft.Text(extra, size=8 if is_mob else 10.5, color=colors["text_muted"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=0, alignment=ft.MainAxisAlignment.CENTER, expand=True)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            )

        card1 = build_stat_card(str(num_subjects), self.translate("stat_subjects"), self.translate("stat_subjects_sub"), ft.Icons.BOOK, "#F3E8FF", "#2E1065", "#7C3AED", "#C084FC", "#E9D5FF", "#3B0764")
        card2 = build_stat_card(f"{avg_grade:.1f}", self.translate("stat_average"), self.translate("stat_average_sub"), ft.Icons.SHOW_CHART, "#DCFCE7", "#064E3B", "#15803D", "#4ADE80", "#BBF7D0", "#022C22")
        card3 = build_stat_card("85%", self.translate("stat_tasks"), self.translate("stat_tasks_sub"), ft.Icons.CHECKLIST, "#E0F2FE", "#1E3A8A", "#4338CA", "#818CF8", "#E0E7FF", "#172554")
        card4 = build_stat_card(str(num_events), self.translate("stat_events"), self.translate("stat_events_sub"), ft.Icons.CALENDAR_MONTH, "#FEE2E2", "#7F1D1D", "#B91C1C", "#FCA5A5", "#FECACA", "#450A0A")


        if is_mob:
            stats_layout = ft.Column([
                ft.Row([card1, card2], spacing=10),
                ft.Row([card3, card4], spacing=10),
            ], spacing=10)
        else:
            stats_layout = ft.Row([card1, card2, card3, card4], spacing=16)

        # ─── Bloques de Información (Técnicas, Gráfico, Asignaturas) ─────────
        def build_tech_row(title, desc, icon, icon_color, icon_bg_light, icon_bg_dark):
            ic_bg = icon_bg_dark if is_dark else icon_bg_light
            return ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=icon_color, size=16),
                    bgcolor=ic_bg,
                    width=32,
                    height=32,
                    border_radius=16,
                    alignment=ft.alignment.center
                ),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(title, size=12, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(desc, size=10, color=colors["text_muted"]),
                ], spacing=1, expand=True)
            ])

        tecnicas_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            expand=not is_mob,
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
            ], spacing=6)
        )

        pie_chart = ft.PieChart(
            sections=[
                ft.PieChartSection(value=excelentes if excelentes > 0 else 0.001, color="#10B981", radius=16),
                ft.PieChartSection(value=buenas if buenas > 0 else 0.001, color="#8B5CF6", radius=16),
                ft.PieChartSection(value=bajas if bajas > 0 else 0.001, color="#EF4444", radius=16),
            ],
            sections_space=2,
            center_space_radius=26,
            expand=True
        )

        chart_stack = ft.Stack([
            pie_chart,
            ft.Container(
                content=ft.Column([
                    ft.Text(str(total_grades), size=16, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(self.translate("chart_total"), size=9, color=colors["text_muted"]),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
                alignment=ft.alignment.center
            )
        ], width=90, height=90)

        def build_legend_item(color, label, val_str):
            display_label = label.split(" (")[0] if is_mob else label
            return ft.Row([
                ft.Container(width=8, height=8, border_radius=4, bgcolor=color),
                ft.Container(width=4 if is_mob else 6),
                ft.Text(display_label, size=10 if is_mob else 11, color=colors["text"], weight=ft.FontWeight.W_500, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Container(expand=True),
                ft.Text(val_str, size=10 if is_mob else 11, color=colors["text_muted"])
            ])


        total_denom = total_grades if total_grades > 0 else 1
        dist_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            expand=not is_mob,
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
                        build_legend_item("#10B981", self.translate("chart_excellent"), f"{excelentes} ({excelentes/total_denom*100:.0f}%)"),
                        build_legend_item("#8B5CF6", self.translate("chart_good"), f"{buenas} ({buenas/total_denom*100:.0f}%)"),
                        build_legend_item("#EF4444", self.translate("chart_low"), f"{bajas} ({bajas/total_denom*100:.0f}%)"),
                    ], spacing=6, expand=True)
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=6)
        )

        def build_subject_row(name, desc, badge_color):
            return ft.Row([
                ft.Container(width=8, height=28, border_radius=4, bgcolor=badge_color),
                ft.Container(width=8),
                ft.Column([
                    ft.Text(name, size=12, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(desc, size=10, color=colors["text_muted"]),
                ], spacing=1, expand=True)
            ])

        asignaturas_box = ft.Container(
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            padding=16,
            expand=not is_mob,
            content=ft.Column([
                ft.Row([
                    ft.Text(self.translate("sidebar_asignaturas"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Container(expand=True),
                    ft.TextButton(self.translate("tech_view_all"), style=ft.ButtonStyle(padding=0), on_click=lambda e: NavigationController.update_view("Notas"))
                ]),
                ft.Container(height=4),
                build_subject_row(self.translate("subj_math"), self.translate("subj_math_desc"), "#F472B6"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_subject_row(self.translate("subj_cs"), self.translate("subj_cs_desc"), "#3B82F6"),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_subject_row(self.translate("subj_eng"), self.translate("subj_eng_desc"), "#A78BFA"),
            ], spacing=4)
        )

        if is_mob:
            grid_sections = ft.Column([
                dist_box,
                tecnicas_box,
                asignaturas_box
            ], spacing=12)
        else:
            grid_sections = ft.Row([
                tecnicas_box,
                dist_box,
                asignaturas_box
            ], spacing=16, height=240)

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
                    ft.Text(course, size=10, color=colors["text_muted"]),
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
                    ft.TextButton(self.translate("tech_view_all"), style=ft.ButtonStyle(padding=0), on_click=lambda e: NavigationController.update_view("Notas"))
                ]),
                ft.Container(height=4),
                build_task_row(self.translate("task_report"), self.translate("subj_cs"), True),
                ft.Divider(color=colors["divider"], height=1, thickness=1),
                build_task_row(self.translate("task_derivatives"), self.translate("subj_math"), False),
            ], spacing=4)
        )

        # ─── Principal de Contenido ───
        dashboard_content = ft.Container(
            expand=True,
            padding=ft.padding.all(12 if is_mob else 24),
            bgcolor=colors["background"],
            content=ft.Column([
                ft.Column([
                    ft.Text(self.translate("welcome_user").format(name=user_name), size=20 if is_mob else 26, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(self.translate("welcome_subtitle"), size=13 if is_mob else 14, color=colors["text_secondary"]),
                ], spacing=2),
                ft.Container(height=12),
                stats_layout,
                ft.Container(height=12),
                grid_sections,
                ft.Container(height=12),
                tareas_box
            ], spacing=0, scroll=get_scroll_mode(self.page))
        )

        controls = [navbar, dashboard_content]
        if is_mob:
            controls.append(self._build_bottom_nav("Inicio"))

        return ft.Column(
            controls=controls,
            expand=True,
            spacing=0,
        )
