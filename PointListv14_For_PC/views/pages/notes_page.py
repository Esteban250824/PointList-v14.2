"""
pages/notes_page.py - v13.5 Dashboard de Calificaciones
Diseño idéntico a Figma (Vista principal y Modal Expandido en 4 columnas)
"""

import flet as ft
import threading
import time
import copy
import random
from datetime import date, datetime, timedelta
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class NotesPage(BasePage):
    """Página de calificaciones/notas rediseñada v13.5."""

    SUBJECTS = [
        "Informática", "Matemáticas", "Inglés", "Valores",
        "Física", "Historia", "Química", "Biología", "Español", "Arte",
    ]

    TIPS_LIST = [
        "La constancia es la clave del éxito. Sigue así ¡vas por buen camino!",
        "El aprendizaje es un proceso continuo. Dedica 15 minutos diarios a repasar.",
        "La técnica Pomodoro te ayuda a mantener el foco y evitar la fatiga mental.",
        "Tomar descansos regulares mejora drásticamente la retención de memoria.",
        "Explica lo aprendido a alguien más; es la mejor forma de consolidar tu conocimiento.",
        "Organiza tus tareas por orden de prioridad antes de empezar tu día de estudio.",
        "Un espacio de estudio ordenado favorece una mente enfocada y serena.",
        "El descanso y el sueño reparador de 7-8 horas son vitales para fijar la memoria.",
        "Alterna diferentes asignaturas durante el día para mantener la agilidad cognitiva.",
        "Formula preguntas sobre el tema que estudias para activar tu lectura analítica.",
        "Utiliza esquemas visuales y mapas conceptuales para sintetizar temas complejos.",
        "Divide proyectos grandes en pequeñas micro-tareas fáciles de cumplir.",
        "Evita la multitarea: enfócate en una sola actividad a la vez para lograr máxima eficiencia.",
        "Elimina las distracciones digitales silenciando notificaciones mientras estudias.",
        "Premia tu progreso al completar una sesión de estudio exigente.",
        "Revisa tus apuntes 24 horas después de la clase para consolidar la información.",
        "Practica con ejercicios reales e información práctica, no solo lectura pasiva.",
        "Aprender a decir 'no' a distracciones es aprender a decir 'sí' a tus metas.",
        "Visualiza tu éxito académico y mantén una mentalidad de crecimiento.",
        "Revisa y corrige tus errores en exámenes pasados; son tus mejores maestros.",
    ]

    DEFAULT_NOTES = [
        {"id": 1, "asignatura": "Biología", "calificacion": 4.5, "fecha": "2026-05-21", "comentarios": "-"},
        {"id": 2, "asignatura": "Arte", "calificacion": 1.0, "fecha": "2026-05-20", "comentarios": "-"},
        {"id": 3, "asignatura": "Química", "calificacion": 4.7, "fecha": "2026-05-20", "comentarios": "-"},
        {"id": 4, "asignatura": "Valores", "calificacion": 3.8, "fecha": "2026-05-20", "comentarios": "-"},
        {"id": 5, "asignatura": "Biología", "calificacion": 4.9, "fecha": "2026-05-20", "comentarios": "-"},
        {"id": 6, "asignatura": "Informática", "calificacion": 5.0, "fecha": "2026-05-20", "comentarios": "-"},
        {"id": 7, "asignatura": "Física", "calificacion": 4.5, "fecha": "2026-05-19", "comentarios": "-"},
        {"id": 8, "asignatura": "Matemáticas", "calificacion": 3.0, "fecha": "2026-05-18", "comentarios": "-"},
    ]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        self._rol = self._user.get("rol", "estudiante")
        self._notas: list = []
        
        self.selected_view = "grid"
        self.chart_type = "bar"
        self.sort_order = "recent"
        self.search_term = ""
        self.main_search_field = None
        
        self.kpi_row = ft.Container()
        self.chart_container = ft.Container()
        self.notes_grid = ft.Container()
        self.sidebar_container = ft.Container()
        
        self._sync_thread = None
        self._stop_sync = False

    def _load_notas(self):
        """Carga notas directamente desde PostgreSQL. Si no hay conexión o no hay usuario, usa la caché."""
        from services.navigation_service import NavigationController
        if self._uid:
            try:
                db_notes = self._db.obtener_notas(self._uid)
                if db_notes:
                    self._notas = copy.deepcopy(db_notes)
                else:
                    self._notas = copy.deepcopy(NavigationController.cache.get("notes", []))
            except Exception as e:
                print(f"[NotesPage] Error al cargar notas de PostgreSQL: {e}")
                self._notas = copy.deepcopy(NavigationController.cache.get("notes", []))
        else:
            self._notas = copy.deepcopy(NavigationController.cache.get("notes", self.DEFAULT_NOTES))

        NavigationController.cache["notes"] = copy.deepcopy(self._notas)

    def _sync_notes_background(self):
        """Sincroniza notas en background."""
        time.sleep(1)
        while not self._stop_sync:
            try:
                from services.navigation_service import NavigationController
                db_notes = self._db.obtener_notas(self._uid) if self._uid else []
                new_notes = db_notes if db_notes else self.DEFAULT_NOTES
                if new_notes != self._notas:
                    self._notas = copy.deepcopy(new_notes)
                    NavigationController.cache["notes"] = copy.deepcopy(new_notes)
                    self._refresh_ui_full()
            except: pass
            time.sleep(6)

    def _refresh_ui_full(self):
        """Refresca toda la interfaz."""
        self._refresh_kpi_view()
        self._refresh_chart_view()
        self._refresh_notes_view()
        self._refresh_sidebar_view()
        try: self.page.update()
        except: pass

    def _create_kpi_card(self, icon, value, label, color, subtitle=""):
        """Crea una tarjeta KPI estilo Figma."""
        colors = self._get_theme_colors()
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            expand=True,
            content=ft.Row([
                ft.Container(
                    width=48, height=48, border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.15, color),
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon, color=color, size=24)
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(label, size=11, color=colors["text_secondary"], weight="w500"),
                    ft.Text(str(value), size=24, weight="bold", color=colors["text"]),
                    ft.Text(subtitle, size=10, color=colors["text_secondary"]),
                ], spacing=1, expand=True),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _refresh_kpi_view(self):
        """Actualiza los 4 KPIs superiores."""
        if not self._notas:
            self.kpi_row.content = ft.Row([
                self._create_kpi_card(ft.Icons.BOOK_ROUNDED, 0, "Asignaturas", "#8B5CF6", "Inscritas"),
                self._create_kpi_card(ft.Icons.SHOW_CHART, "0.0", "Promedio General", "#10B981", "Sobre 5.0"),
                self._create_kpi_card(ft.Icons.BAR_CHART, "-", "Mejor Calificación", "#3B82F6", "Sin datos"),
                self._create_kpi_card(ft.Icons.TRENDING_DOWN, "-", "Más baja", "#EF4444", "Sin datos"),
            ], spacing=12, expand=True)
            return
        
        total_subjects = len(set(n.get("asignatura") for n in self._notas))
        avg_grade = sum(float(n.get("calificacion", 0)) for n in self._notas) / len(self._notas)
        
        best_note = max(self._notas, key=lambda n: float(n.get("calificacion", 0)))
        worst_note = min(self._notas, key=lambda n: float(n.get("calificacion", 0)))
        
        best_grade = float(best_note.get("calificacion", 0))
        best_subj = best_note.get("asignatura", "")
        
        worst_grade = float(worst_note.get("calificacion", 0))
        worst_subj = worst_note.get("asignatura", "")
        
        self.kpi_row.content = ft.Row([
            self._create_kpi_card(ft.Icons.BOOK_ROUNDED, total_subjects, "Asignaturas", "#8B5CF6", "Inscritas"),
            self._create_kpi_card(ft.Icons.SHOW_CHART, f"{avg_grade:.1f}", "Promedio General", "#10B981", "Sobre 5.0"),
            self._create_kpi_card(ft.Icons.BAR_CHART, f"{best_grade:.1f}", "Mejor Calificación", "#3B82F6", best_subj),
            self._create_kpi_card(ft.Icons.TRENDING_DOWN, f"{worst_grade:.1f}", "Más baja", "#EF4444", worst_subj),
        ], spacing=12, expand=True)

    def _create_bar_chart(self):
        """Crea gráfica de barras por asignatura idéntica a Figma."""
        if not self._notas:
            return ft.Container(
                height=220,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.Icons.BAR_CHART_OUTLINED, size=36, color="#94A3B8"),
                    ft.Container(height=6),
                    ft.Text("Sin calificaciones para graficar promedios", color="#94A3B8", size=13, weight="w500")
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        
        subject_avg = {}
        for note in self._notas:
            subject = note.get("asignatura", "Otras")
            grade = float(note.get("calificacion", 0))
            if subject not in subject_avg: subject_avg[subject] = []
            subject_avg[subject].append(grade)
        
        subject_avg = {subj: sum(grades)/len(grades) for subj, grades in subject_avg.items()}
        
        def grade_color(avg: float) -> str:
            if avg >= 4.0:
                return "#10B981"
            if avg >= 3.0:
                return "#8B5CF6"
            return "#EF4444"
        
        bars = []
        labels = []
        for idx, (subj, avg) in enumerate(sorted(subject_avg.items())):
            color = grade_color(avg)
            bars.append(
                ft.BarChartGroup(
                    x=idx,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, to_y=avg, width=28,
                            color=color,
                            tooltip=f"{subj}: {avg:.1f}",
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                        )
                    ],
                )
            )
            labels.append(
                ft.ChartAxisLabel(
                    idx,
                    ft.Container(
                        content=ft.Text(subj, size=11, color="#475569", weight="w500"),
                        alignment=ft.alignment.center
                    )
                )
            )
        
        chart = ft.BarChart(
            bar_groups=bars,
            border=ft.border.all(0, ft.Colors.TRANSPARENT),
            left_axis=ft.ChartAxis(labels_size=24, title=ft.Text("", size=10)),
            bottom_axis=ft.ChartAxis(
                labels=labels,
                labels_size=32,
            ),
            min_y=0, max_y=5.0,
            interactive=True,
            expand=True,
            horizontal_grid_lines=ft.ChartGridLines(
                color="#E2E8F0", width=1, interval=1
            ),
        )
        
        return chart

    def _create_line_chart(self) -> ft.Control:
        """Crea la gráfica de líneas (LineChart) de evolución del rendimiento por materia y general."""
        notes = self._notas if self._notas else self.DEFAULT_NOTES
        
        filter_subject = getattr(self, "chart_subject_filter", "General")
        if filter_subject != "General":
            notes = [n for n in notes if n.get("asignatura") == filter_subject]

        if not notes:
            return ft.Container(
                alignment=ft.alignment.center,
                height=180,
                content=ft.Text(f"No hay notas suficientes para la gráfica de {filter_subject}", color="#64748B", size=13)
            )

        sorted_notes = sorted(notes, key=lambda x: str(x.get("fecha", "")))
        data_points = []
        labels = []
        
        for idx, n in enumerate(sorted_notes[-10:]):
            val = float(n.get("calificacion", 0))
            data_points.append(ft.LineChartDataPoint(x=idx, y=val))
            lbl_text = n.get("asignatura", "")[:5] if filter_subject == "General" else str(n.get("fecha", ""))[-5:]
            labels.append(
                ft.ChartAxisLabel(
                    idx,
                    ft.Container(
                        content=ft.Text(lbl_text, size=10, color="#475569", weight="bold"),
                        alignment=ft.alignment.center
                    )
                )
            )

        line_data = ft.LineChartData(
            data_points=data_points,
            stroke_width=3,
            color="#0284C7" if filter_subject != "General" else "#7C3AED",
            curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=ft.Colors.with_opacity(0.18, "#0284C7" if filter_subject != "General" else "#7C3AED")
        )

        return ft.LineChart(
            data_series=[line_data],
            border=ft.border.all(0, ft.Colors.TRANSPARENT),
            left_axis=ft.ChartAxis(labels_size=24),
            bottom_axis=ft.ChartAxis(labels=labels, labels_size=28),
            min_y=0, max_y=5.0,
            interactive=True,
            expand=True,
            horizontal_grid_lines=ft.ChartGridLines(color="#E2E8F0", width=1, interval=1)
        )

    def _refresh_chart_view(self):
        """Actualiza la gráfica principal (Barras o Líneas por Materia / General)."""
        colors = self._get_theme_colors()
        curr_chart_type = getattr(self, "chart_type", "bar")
        curr_subj = getattr(self, "chart_subject_filter", "General")

        chart = self._create_line_chart() if curr_chart_type == "line" else self._create_bar_chart()
        
        def _set_chart_mode(mode: str):
            self.chart_type = mode
            self._refresh_chart_view()
            try: self.chart_container.update()
            except: pass

        def _on_subject_select(e):
            self.chart_subject_filter = e.control.value
            self.chart_type = "line"
            self._refresh_chart_view()
            try: self.chart_container.update()
            except: pass

        subj_opts = [ft.dropdown.Option("General", text="📈 General (Evolución)")] + [
            ft.dropdown.Option(s, text=f"📘 {s}") for s in self.SUBJECTS
        ]

        subj_dd = ft.Dropdown(
            options=subj_opts,
            value=curr_subj,
            width=180,
            border_radius=8,
            bgcolor=colors["surface"],
            on_change=_on_subject_select
        )

        btn_bars = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#7C3AED" if curr_chart_type == "bar" else colors["surface"],
            border_radius=8,
            border=ft.border.all(1, "#7C3AED" if curr_chart_type == "bar" else "#CBD5E1"),
            ink=True,
            on_click=lambda e: _set_chart_mode("bar"),
            content=ft.Text("📊 Barras", size=12, weight="bold", color="white" if curr_chart_type == "bar" else colors["text"])
        )

        btn_line = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#7C3AED" if curr_chart_type == "line" else colors["surface"],
            border_radius=8,
            border=ft.border.all(1, "#7C3AED" if curr_chart_type == "line" else "#CBD5E1"),
            ink=True,
            on_click=lambda e: _set_chart_mode("line"),
            content=ft.Text("📈 Líneas de Progreso", size=12, weight="bold", color="white" if curr_chart_type == "line" else colors["text"])
        )

        self.chart_container.content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Rendimiento Académico", size=16, weight="bold", color="#0F172A"),
                    ft.Container(expand=True),
                    subj_dd,
                    btn_bars,
                    btn_line,
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                ft.Container(height=10),
                ft.Container(content=chart, height=220, expand=True)
            ], spacing=0),
            padding=ft.padding.all(20),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
        )

    def _create_note_card(self, note):
        """Crea tarjeta de nota idéntica a la de Figma."""
        grade = float(note.get("calificacion", 0))

        if grade >= 4.0:
            badge_color = "#10B981"
        elif grade >= 3.0:
            badge_color = "#8B5CF6"
        else:
            badge_color = "#EF4444"

        colors = self._get_theme_colors()
        fecha = str(note.get("fecha", ""))
        comment = note.get("comentarios", "") or "-"

        def _do_delete(e):
            nid = note.get("id")
            if nid:
                self._notas = [n for n in self._notas if n.get("id") != nid]
                from services.navigation_service import NavigationController
                NavigationController.cache["notes"] = self._notas
                self._refresh_ui_full()
                import threading
                threading.Thread(target=lambda: self._db.eliminar_nota(nid) if hasattr(self._db, 'eliminar_nota') else None, daemon=True).start()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        width=42, height=42, border_radius=21, bgcolor=badge_color,
                        alignment=ft.alignment.center,
                        content=ft.Text(f"{grade:.1f}", color="white", weight="bold", size=14)
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(note.get("asignatura", ""), size=13, weight="bold", color="#0F172A"),
                        ft.Text(fecha, size=10, color="#64748B"),
                    ], expand=True, spacing=1),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        icon_size=18,
                        icon_color="#94A3B8",
                        items=[
                            ft.PopupMenuItem(icon=ft.Icons.DELETE_OUTLINE, text="Eliminar", on_click=_do_delete),
                        ]
                    )
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                ft.Text(comment, size=11, color="#64748B", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ], spacing=0)
        )

    def _get_filtered_notes(self) -> list:
        """Filtra notas según el término de búsqueda actual."""
        if not self.search_term.strip():
            return self._notas
        term = self.search_term.strip().lower()
        return [
            n for n in self._notas 
            if term in (n.get("asignatura") or "").lower() or term in (n.get("comentarios") or "").lower()
        ]

    def _build_notes_responsive_row(self, notes_list, cols_config=None) -> ft.ResponsiveRow:
        """Crea el grid responsivo para una lista dada de notas."""
        if cols_config is None:
            cols_config = {"xs": 12, "sm": 6, "md": 4, "lg": 4}
            
        if not notes_list:
            return ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(vertical=36, horizontal=20),
                        alignment=ft.alignment.center,
                        col={"xs": 12, "sm": 12, "md": 12, "lg": 12},
                        content=ft.Column([
                            ft.Container(
                                width=56, height=56, border_radius=28,
                                bgcolor="#F1F5F9", alignment=ft.alignment.center,
                                content=ft.Icon(ft.Icons.NOTE_ADD_OUTLINED, size=28, color="#64748B")
                            ),
                            ft.Container(height=10),
                            ft.Text("Aún no tienes calificaciones registradas", color="#0F172A", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text("Tus calificaciones registradas o asignadas por tus profesores aparecerán aquí.", color="#64748B", size=12, text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
                    )
                ]
            )
        return ft.ResponsiveRow(
            controls=[ft.Container(self._create_note_card(n), col=cols_config) for n in notes_list],
            spacing=12,
            run_spacing=12,
        )

    def _refresh_notes_view(self):
        """Actualiza la lista de notas en grid principal (máximo 6 tarjetas)."""
        filtered = self._get_filtered_notes()
        self.notes_grid.content = self._build_notes_responsive_row(filtered[:6])

    def _on_main_search_change(self, e):
        """Manejador para el campo de búsqueda principal."""
        self.search_term = e.control.value
        self._refresh_notes_view()
        try: self.notes_grid.update()
        except: pass

    def _open_add_note_dialog(self, e=None):
        """Abre un modal interactivo para que los profesores asignen calificaciones a un estudiante de la comunidad."""
        all_users = self._db.obtener_todos_los_usuarios() or []
        students = [u for u in all_users if "profesor" not in str(u.get("rol", "")).lower() and u.get("id") != self._uid]
        if not students:
            students = [
                {"id": "est_1", "name": "Juan Pérez", "email": "juan@estudiante.edu"},
                {"id": "est_2", "name": "María Gómez", "email": "maria@estudiante.edu"},
                {"id": "est_3", "name": "Carlos Rodríguez", "email": "carlos@estudiante.edu"},
            ]

        student_dropdown = ft.Dropdown(
            label="Seleccionar Estudiante",
            options=[
                ft.dropdown.Option(
                    key=str(s["id"]),
                    text=f"👤 {s.get('name') or s.get('nombre') or s.get('email')} ({s.get('email', '')})"
                ) for s in students
            ],
            value=str(students[0]["id"]),
            border_radius=10,
            expand=True,
        )

        subject_dropdown = ft.Dropdown(
            label="Asignatura",
            options=[ft.dropdown.Option(s) for s in self.SUBJECTS],
            value=self.SUBJECTS[0],
            border_radius=10,
            expand=True,
        )
        
        grade_input = ft.TextField(
            label="Calificación (0.0 a 5.0)",
            hint_text="Ej: 4.8",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            autofocus=True,
        )

        comments_input = ft.TextField(
            label="Comentarios u Observaciones",
            hint_text="Ej: Excelente desempeño en tareas y examen final",
            border_radius=10,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        def _save_note(e):
            try:
                raw_grade = grade_input.value.strip().replace(",", ".")
                grade_val = float(raw_grade)
                if not (0.0 <= grade_val <= 5.0):
                    self._show_info("La calificación debe estar entre 0.0 y 5.0")
                    return
            except ValueError:
                self._show_info("Por favor ingresa un número válido (ej: 4.5)")
                return

            sel_id = student_dropdown.value
            sel_st = next((s for s in students if str(s["id"]) == str(sel_id)), students[0])
            st_name = sel_st.get("name") or sel_st.get("nombre") or sel_st.get("email") or "Estudiante"

            new_note = {
                "id": f"nota_{int(time.time())}_{random.randint(100, 999)}",
                "estudiante_id": sel_id,
                "estudiante": st_name,
                "asignatura": subject_dropdown.value,
                "calificacion": round(grade_val, 1),
                "fecha": date.today().isoformat(),
                "comentarios": comments_input.value.strip() or "-",
            }

            self._notas.insert(0, new_note)
            from services.navigation_service import NavigationController
            NavigationController.cache["notes"] = copy.deepcopy(self._notas)

            def _save_bg():
                try:
                    if hasattr(self._db, "guardar_nota"):
                        prof_id = self._uid if "profesor" in str(self._rol).lower() else None
                        res = self._db.guardar_nota(
                            uid=sel_id,
                            asignatura=new_note["asignatura"],
                            calificacion=new_note["calificacion"],
                            fecha=new_note["fecha"],
                            comentarios=new_note["comentarios"],
                            profesor_id=prof_id
                        )
                        print(f"[NotesPage] Guardar nota resultado: {res}")
                except Exception as ex:
                    print(f"[NotesPage] Error guardando nota en background: {ex}")
            threading.Thread(target=_save_bg, daemon=True).start()

            self.page.close(dlg)
            self._refresh_ui_full()
            self._show_info(f"Calificación asignada a {st_name}: {subject_dropdown.value} ({round(grade_val, 1)})")

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.GRADE, color="#7C3AED", size=24),
                ft.Text("Asignar Calificación a Estudiante", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=440, height=400,
                content=ft.Column([
                    ft.Text("Selecciona el estudiante y la asignatura para asignar la nota:", size=12, color="#64748B"),
                    ft.Container(height=8),
                    student_dropdown,
                    ft.Container(height=8),
                    subject_dropdown,
                    ft.Container(height=8),
                    grade_input,
                    ft.Container(height=8),
                    comments_input,
                ], spacing=0, expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Guardar Nota", bgcolor="#7C3AED", color="white", on_click=_save_note),
            ]
        )
        self.page.open(dlg)

    def _show_expanded_notes_dialog(self):
        """Modal expandido de calificaciones en 4 columnas."""
        colors = self._get_theme_colors()

        modal_grid_ref = ft.Ref[ft.Container]()
        modal_search_ref = ft.Ref[ft.TextField]()

        def _on_modal_search_change(e):
            self.search_term = e.control.value
            if self.main_search_field:
                self.main_search_field.value = self.search_term
                try: self.main_search_field.update()
                except: pass
            modal_grid_ref.current.content = self._build_notes_responsive_row(
                self._get_filtered_notes(),
                cols_config={"xs": 12, "sm": 6, "md": 4, "lg": 3}
            )
            try: modal_grid_ref.current.update()
            except: pass
            self._refresh_notes_view()
            try: self.notes_grid.update()
            except: pass

        def _close_modal(e):
            self.page.close(dlg)

        modal_header = ft.Row([
            ft.Text("Tus calificaciones", size=20, weight="bold", color="#0F172A"),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.ZOOM_IN_MAP,
                icon_size=20,
                icon_color="#64748B",
                tooltip="Contraer",
                on_click=_close_modal,
            )
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        modal_search = ft.TextField(
            ref=modal_search_ref,
            hint_text="Buscar asignatura...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            value=self.search_term,
            bgcolor=colors["surface"],
            border_color="#E2E8F0",
            on_change=_on_modal_search_change,
        )

        modal_grid_ref.current = ft.Container(
            content=self._build_notes_responsive_row(
                self._get_filtered_notes(),
                cols_config={"xs": 12, "sm": 6, "md": 4, "lg": 3}
            )
        )

        notes_scroll = ft.Column(
            controls=[modal_grid_ref.current],
            scroll=get_scroll_mode("AUTO"),
            expand=True,
        )

        dlg = ft.AlertDialog(
            modal=False,
            bgcolor=colors["surface"],
            content_padding=ft.padding.all(0),
            content=ft.Container(
                width=940,
                height=620,
                bgcolor=colors["surface"],
                padding=ft.padding.all(24),
                border_radius=16,
                content=ft.Column([
                    modal_header,
                    ft.Container(height=12),
                    modal_search,
                    ft.Container(height=16),
                    notes_scroll,
                ], spacing=0, expand=True)
            )
        )

        self.page.open(dlg)

    def _go_to_calendar(self, e):
        from services.navigation_service import NavigationController
        NavigationController.update_view("Calendario")

    def _refresh_sidebar_view(self):
        """Construye los eventos próximos para la barra lateral derecha leyendo eventos de la cache y de la BD."""
        colors = self._get_theme_colors()

        events_list = ft.Column([
            ft.Text("Próximos eventos", size=15, weight="bold", color="#0F172A"),
            ft.Container(height=8),
        ], spacing=8)

        from services.navigation_service import NavigationController
        cached_events = NavigationController.cache.get("events", [])
        if cached_events:
            real_events = copy.deepcopy(cached_events)
        else:
            real_events = self._db.obtener_eventos(self._uid) if self._uid else []
            if real_events:
                NavigationController.cache["events"] = copy.deepcopy(real_events)

        today = date.today()
        start_curr_week = today - timedelta(days=today.weekday())
        end_next_week = start_curr_week + timedelta(days=13)
        months_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

        week_events = []
        if real_events:
            for ev in real_events:
                try:
                    raw_dt = ev.get("fecha_inicio") or ev.get("fecha")
                    if not raw_dt: continue

                    ev_date = None
                    if isinstance(raw_dt, datetime):
                        ev_date = raw_dt.date()
                    elif isinstance(raw_dt, date):
                        ev_date = raw_dt
                    elif isinstance(raw_dt, str):
                        clean_str = raw_dt.split("T")[0].strip()
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                            try:
                                ev_date = datetime.strptime(clean_str[:10], fmt).date()
                                break
                            except Exception: pass
                        if not ev_date:
                            try: ev_date = date.fromisoformat(clean_str[:10])
                            except Exception: pass

                    if ev_date and start_curr_week <= ev_date <= end_next_week:
                        tipo = ev.get("tipo_evento", "General")
                        tipo_lower = str(tipo).lower()
                        title_lower = str(ev.get("titulo", "")).lower()

                        if "examen" in tipo_lower or "examen" in title_lower:
                            badge_color = "#EF4444"
                            badge_bg = "#FEE2E2"
                        else:
                            badge_color = "#3B82F6"
                            badge_bg = "#DBEAFE"

                        date_str = f"{ev_date.day} de {months_es[ev_date.month - 1]}"

                        week_events.append({
                            "title": ev.get("titulo", "Evento"),
                            "date": date_str,
                            "time": "Todo el día",
                            "color": badge_color,
                            "bg": badge_bg,
                            "ev_date": ev_date
                        })
                except Exception:
                    continue

        week_events.sort(key=lambda x: x["ev_date"])

        if not week_events:
            events_list.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=16, horizontal=10),
                    alignment=ft.alignment.center,
                    bgcolor="#F8FAFC",
                    border_radius=10,
                    border=ft.border.all(1, "#E2E8F0"),
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=18, color="#10B981"),
                        ft.Text("bien, no tienes eventos por ahora", size=12, color=colors["text_secondary"], weight=ft.FontWeight.W_500),
                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER)
                )
            )
        else:
            for ev in week_events[:4]:
                events_list.controls.append(
                    ft.Container(
                        padding=ft.padding.all(10),
                        bgcolor=colors["surface"],
                        border_radius=10,
                        border=ft.border.all(1, "#F1F5F9"),
                        content=ft.Row([
                            ft.Container(
                                width=32, height=32, border_radius=8,
                                bgcolor=ev["bg"],
                                alignment=ft.alignment.center,
                                content=ft.Icon(ft.Icons.CALENDAR_TODAY, color=ev["color"], size=16)
                            ),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(ev["title"], size=12, weight="bold", color="#0F172A", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(ev["date"], size=9.5, color="#64748B"),
                            ], spacing=1, expand=True),
                        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                )

        events_list.controls.append(ft.Container(height=8))
        events_list.controls.append(
            ft.OutlinedButton(
                text="Ver Calendario Completo",
                on_click=self._go_to_calendar,
                style=ft.ButtonStyle(
                    color="#475569",
                    side=ft.BorderSide(1, "#E2E8F0"),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                height=34,
            )
        )

        self.sidebar_container.content = events_list

    def _build_right_sidebar(self, colors):
        """Sidebar derecha con: próximos eventos, distribución y consejo."""
        total = len(self._notas) or 0
        excellent = len([n for n in self._notas if float(n.get("calificacion", 0)) >= 4.5])
        good      = len([n for n in self._notas if 3.0 <= float(n.get("calificacion", 0)) < 4.5])
        low       = len([n for n in self._notas if float(n.get("calificacion", 0)) < 3.0])

        def pie_section(value, color):
            return ft.PieChartSection(
                value=value if value > 0 else 0.001,
                color=color,
                radius=20,
            )

        pie = ft.PieChart(
            sections=[
                pie_section(excellent, "#10B981"),
                pie_section(good, "#8B5CF6"),
                pie_section(low, "#EF4444"),
            ],
            sections_space=2,
            center_space_radius=32,
            expand=True,
        )

        chart_stack = ft.Stack([
            pie,
            ft.Container(
                content=ft.Column([
                    ft.Text(str(total), size=16, weight="bold", color="#0F172A"),
                    ft.Text("Total", size=9, color="#64748B"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=0,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
            )
        ], width=88, height=88)

        def legend_row(color, label):
            return ft.Row([
                ft.Container(width=8, height=8, border_radius=2, bgcolor=color),
                ft.Container(width=4),
                ft.Text(label, size=9.5, color="#0F172A", expand=True),
            ])

        total_d = total if total > 0 else 1
        distribution_card = ft.Container(
            padding=ft.padding.all(14),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Text("Distribución de calificaciones", size=13,
                        weight="bold", color="#0F172A"),
                ft.Container(height=10),
                ft.Row([
                    chart_stack,
                    ft.Container(width=6),
                    ft.Column([
                        legend_row("#10B981", f"Excelentes (4.5 - 5.0)\n{excellent} ({excellent/total_d*100:.1f}%)"),
                        legend_row("#8B5CF6", f"Buenas (3.0 - 4.4) {good}\n({good/total_d*100:.1f}%)"),
                        legend_row("#EF4444", f"Bajas (0 - 2.9) {low}\n({low/total_d*100:.1f}%)"),
                    ], spacing=6, expand=True)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], spacing=0)
        )

        selected_tip = random.choice(self.TIPS_LIST)
        tip_card = ft.Container(
            padding=ft.padding.all(12),
            bgcolor="#F8FAFC",
            border_radius=12,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color="#8B5CF6", size=18),
                    ft.Text("Consejo del día", size=12, weight="bold", color="#0F172A"),
                ], spacing=6),
                ft.Container(height=6),
                ft.Text(selected_tip, size=10.5, color="#64748B"),
            ], spacing=0)
        )

        events_card = ft.Container(
            padding=ft.padding.all(14),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=self.sidebar_container,
        )

        return ft.Container(
            width=270,
            bgcolor=ft.Colors.TRANSPARENT,
            border=None,
            padding=ft.padding.all(12),
            content=ft.Column([
                events_card,
                ft.Container(height=12),
                distribution_card,
                ft.Container(height=12),
                tip_card,
            ], spacing=0, scroll=get_scroll_mode("AUTO"))
        )

    def build(self) -> ft.Control:
        self._load_notas()
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("nav_notes"))
        
        self._refresh_kpi_view()
        self._refresh_chart_view()
        self._refresh_notes_view()
        self._refresh_sidebar_view()

        right_sidebar = self._build_right_sidebar(colors)

        # Sección "Tus calificaciones"
        self.main_search_field = ft.TextField(
            hint_text="Buscar asignatura...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            bgcolor=colors["surface"],
            border_color="#E2E8F0",
            on_change=self._on_main_search_change,
            expand=True,
            height=40,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

        is_profesor = "profesor" in str(self._rol).lower() or "docente" in str(self._rol).lower() or "maestro" in str(self._rol).lower() or "admin" in str(self._rol).lower() or self._user.get("es_profesor", False)

        add_note_btn = ft.ElevatedButton(
            "➕ Agregar Nota",
            bgcolor="#7C3AED",
            color=ft.Colors.WHITE,
            height=36,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=self._open_add_note_dialog,
        ) if is_profesor else ft.Container()

        tus_calificaciones_card = ft.Container(
            padding=ft.padding.all(16),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Text("Gestión de Calificaciones" if is_profesor else "Tus calificaciones", size=15, weight="bold", color="#0F172A"),
                    ft.Container(expand=True),
                    add_note_btn,
                    ft.Container(width=6 if is_profesor else 0),
                    ft.IconButton(
                        icon=ft.Icons.ZOOM_OUT_MAP,
                        icon_size=18,
                        icon_color="#64748B",
                        tooltip="Expandir",
                        on_click=lambda e: self._show_expanded_notes_dialog(),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=8),
                self.main_search_field,
                ft.Container(height=12),
                self.notes_grid,
            ], spacing=0)
        )

        center_content = ft.Column([
            self.kpi_row,
            ft.Container(height=16),
            self.chart_container,
            ft.Container(height=16),
            tus_calificaciones_card,
        ], spacing=0, expand=True, scroll=get_scroll_mode("AUTO"))

        is_mobile = self.page.width < 900
        if is_mobile:
            main_body = ft.Container(
                expand=True,
                padding=ft.padding.all(16),
                content=ft.Column([center_content, right_sidebar], scroll=get_scroll_mode("AUTO"))
            )
        else:
            main_body = ft.Container(
                expand=True,
                padding=ft.padding.all(20),
                content=ft.Row([
                    ft.Container(expand=True, content=center_content),
                    ft.Container(width=16),
                    right_sidebar,
                ], spacing=0, expand=True)
            )

        return ft.Column(controls=[navbar, main_body], expand=True, spacing=0)
