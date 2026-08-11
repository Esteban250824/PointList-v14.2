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
        """Carga notas desde BD o caché. Si está vacío, usa notas de demostración de Figma."""
        from services.navigation_service import NavigationController
        cached_notes = NavigationController.cache.get("notes", [])
        if cached_notes:
            self._notas = copy.deepcopy(cached_notes)
        else:
            db_notes = self._db.obtener_notas(self._uid) if self._uid else []
            if db_notes:
                self._notas = copy.deepcopy(db_notes)
            else:
                self._notas = copy.deepcopy(self.DEFAULT_NOTES)
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

    def _create_kpi_card(self, icon, value, label, color, subtitle):
        """Crea una tarjeta KPI adaptable para cualquier resolución de pantalla."""
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=8 if is_mob else 14, vertical=8 if is_mob else 12),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, colors["border"]),
            expand=True,
            content=ft.Row([
                ft.Container(
                    width=34 if is_mob else 44, height=34 if is_mob else 44, border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.15, color),
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon, color=color, size=16 if is_mob else 22)
                ),
                ft.Container(width=5 if is_mob else 10),
                ft.Column([
                    ft.Text(label, size=9.5 if is_mob else 11, color=colors["text_secondary"], weight="w500", max_lines=2, overflow=ft.TextOverflow.VISIBLE),
                    ft.Text(str(value), size=16 if is_mob else 22, weight="bold", color=colors["text"]),
                    ft.Text(subtitle, size=8.5 if is_mob else 10, color=colors["text_muted"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _refresh_kpi_view(self):
        """Actualiza los 4 KPIs superiores en grid 2x2 para móviles o fila para escritorio."""
        if not self._notas:
            self.kpi_row.content = ft.Container(height=100)
            return

        total_subjects = len(set(n.get("asignatura") for n in self._notas))
        avg_grade = sum(float(n.get("calificacion", 0)) for n in self._notas) / len(self._notas)

        best_note = max(self._notas, key=lambda n: float(n.get("calificacion", 0)))
        worst_note = min(self._notas, key=lambda n: float(n.get("calificacion", 0)))

        best_grade = float(best_note.get("calificacion", 0))
        best_subj = best_note.get("asignatura", "")

        worst_grade = float(worst_note.get("calificacion", 0))
        worst_subj = worst_note.get("asignatura", "")

        c1 = self._create_kpi_card(ft.Icons.BOOK_ROUNDED, total_subjects, "Asignaturas", "#8B5CF6", "Inscritas")
        c2 = self._create_kpi_card(ft.Icons.SHOW_CHART, f"{avg_grade:.1f}", "Promedio", "#10B981", "Sobre 5.0")
        c3 = self._create_kpi_card(ft.Icons.BAR_CHART, f"{best_grade:.1f}", "Mejor Nota", "#3B82F6", best_subj)
        c4 = self._create_kpi_card(ft.Icons.TRENDING_DOWN, f"{worst_grade:.1f}", "Más baja", "#EF4444", worst_subj)

        is_mob = self.is_mobile()
        if is_mob:
            self.kpi_row.content = ft.Column([
                ft.Row([c1, c2], spacing=10),
                ft.Row([c3, c4], spacing=10),
            ], spacing=10)
        else:
            self.kpi_row.content = ft.Row([c1, c2, c3, c4], spacing=12, expand=True)


    def _create_bar_chart(self):
        """Crea gráfica de barras por asignatura idéntica a Figma."""
        if not self._notas:
            return ft.Container(height=240)
        
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
        
        is_mob = self.is_mobile()
        bars = []
        labels = []
        for idx, (subj, avg) in enumerate(sorted(subject_avg.items())):
            color = grade_color(avg)
            label_text = (subj[:4] + ".") if (is_mob and len(subj) > 5) else subj
            bars.append(
                ft.BarChartGroup(
                    x=idx,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, to_y=avg, width=14 if is_mob else 24,
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
                        content=ft.Text(label_text, size=9 if is_mob else 11, color="#475569", weight="w500"),
                        alignment=ft.alignment.center
                    )
                )
            )

        chart = ft.BarChart(
            bar_groups=bars,
            border=ft.border.all(0, ft.Colors.TRANSPARENT),
            left_axis=ft.ChartAxis(labels_size=20 if is_mob else 24, title=ft.Text("", size=10)),
            bottom_axis=ft.ChartAxis(
                labels=labels,
                labels_size=24 if is_mob else 32,
            ),
            min_y=0, max_y=5.0,
            interactive=True,
            expand=True,
            horizontal_grid_lines=ft.ChartGridLines(
                color="#E2E8F0", width=1, interval=1
            ),
        )

        return chart


    def _refresh_chart_view(self):
        """Reemplaza la sección 'Promedio por asignatura' con 'Próximos eventos' (esta semana y semana entrante)."""
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()

        from services.navigation_service import NavigationController
        cached_events = NavigationController.cache.get("events", [])
        if cached_events:
            real_events = copy.deepcopy(cached_events)
        else:
            real_events = self._db.obtener_eventos(self._uid) if self._uid else []
            if real_events:
                NavigationController.cache["events"] = copy.deepcopy(real_events)

        now = datetime.now()
        # Inicio de la semana actual (Lunes) y fin de la semana entrante (Domingo de la próxima semana)
        start_of_this_week = (now - timedelta(days=now.weekday())).date()
        end_of_next_week = start_of_this_week + timedelta(days=13)

        parsed_events = []
        months_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

        if real_events:
            for ev in real_events:
                try:
                    raw_dt = ev.get("fecha_inicio")
                    dt_obj = None
                    if isinstance(raw_dt, datetime):
                        dt_obj = raw_dt
                    elif isinstance(raw_dt, date):
                        dt_obj = datetime.combine(raw_dt, datetime.min.time())
                    elif isinstance(raw_dt, str):
                        clean_str = raw_dt.replace("Z", "+00:00").strip()
                        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y"):
                            try:
                                dt_obj = datetime.strptime(clean_str[:19], fmt)
                                break
                            except Exception:
                                pass
                        if not dt_obj:
                            try:
                                dt_obj = datetime.fromisoformat(clean_str)
                            except Exception:
                                pass

                    if dt_obj and start_of_this_week <= dt_obj.date() <= end_of_next_week:
                        tipo = ev.get("tipo_evento", "General")
                        tipo_lower = str(tipo).lower()
                        title_lower = str(ev.get("titulo", "")).lower()

                        if "examen" in tipo_lower or "examen" in title_lower or "química" in title_lower:
                            badge_color = "#10B981"
                            badge_bg = "#DCFCE7"
                        elif "tarea" in tipo_lower or "informática" in title_lower or "entrega" in title_lower:
                            badge_color = "#8B5CF6"
                            badge_bg = "#F3E8FF"
                        else:
                            badge_color = "#EF4444"
                            badge_bg = "#FEE2E2"

                        time_str = dt_obj.strftime("%I:%M %p") if (dt_obj.hour or dt_obj.minute) else "Todo el día"
                        date_str = f"{dt_obj.day} de {months_es[dt_obj.month - 1]}"

                        is_this_week = dt_obj.date() <= (start_of_this_week + timedelta(days=6))
                        week_tag = "Esta semana" if is_this_week else "Semana entrante"

                        parsed_events.append({
                            "title": ev.get("titulo", "Evento"),
                            "date": date_str,
                            "time": time_str,
                            "color": badge_color,
                            "bg": badge_bg,
                            "dt": dt_obj,
                            "week_tag": week_tag,
                        })
                except Exception:
                    continue

        parsed_events.sort(key=lambda x: x["dt"])

        # Si no hay eventos guardados en esta ventana de 2 semanas, mostrar demostración precisa de esta semana y la entrante
        if not parsed_events:
            demo_d1 = now + timedelta(days=1)
            demo_d2 = now + timedelta(days=3)
            demo_d3 = start_of_this_week + timedelta(days=8)  # Próxima semana
            demo_d4 = start_of_this_week + timedelta(days=11) # Próxima semana

            parsed_events = [
                {
                    "title": "Examen de Química Orgánica",
                    "date": f"{demo_d1.day} de {months_es[demo_d1.month - 1]}",
                    "time": "09:00 AM",
                    "color": "#10B981",
                    "bg": "#DCFCE7",
                    "week_tag": "Esta semana" if demo_d1.date() <= (start_of_this_week + timedelta(days=6)) else "Semana entrante",
                },
                {
                    "title": "Entrega de informe de Informática",
                    "date": f"{demo_d2.day} de {months_es[demo_d2.month - 1]}",
                    "time": "11:59 PM",
                    "color": "#8B5CF6",
                    "bg": "#F3E8FF",
                    "week_tag": "Esta semana" if demo_d2.date() <= (start_of_this_week + timedelta(days=6)) else "Semana entrante",
                },
                {
                    "title": "Examen Parcial de Matemáticas",
                    "date": f"{demo_d3.day} de {months_es[demo_d3.month - 1]}",
                    "time": "10:00 AM",
                    "color": "#EF4444",
                    "bg": "#FEE2E2",
                    "week_tag": "Semana entrante",
                },
                {
                    "title": "Laboratorio de Física",
                    "date": f"{demo_d4.day} de {months_es[demo_d4.month - 1]}",
                    "time": "02:30 PM",
                    "color": "#2563EB",
                    "bg": "#DBEAFE",
                    "week_tag": "Semana entrante",
                },
            ]

        event_cards = []
        for ev in parsed_events[:4]:
            event_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6},
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                    bgcolor=colors["surface"],
                    border_radius=12,
                    border=ft.border.all(1, colors["border"]),
                    shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK)),
                    content=ft.Row([
                        ft.Container(
                            width=40, height=40, border_radius=10,
                            bgcolor=ev["bg"],
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.Icons.CALENDAR_MONTH, color=ev["color"], size=20)
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(ev["week_tag"], size=9, weight="bold", color=ev["color"]),
                                    bgcolor=ev["bg"],
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    border_radius=4,
                                ),
                                ft.Text(ev["time"], size=10, color=colors["text_muted"], weight="w500"),
                            ], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=2),
                            ft.Text(ev["title"], size=12.5, weight="bold", color=colors["text"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(ev["date"], size=10.5, color=colors["text_secondary"]),
                        ], spacing=1, expand=True),
                    ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                )
            )

        events_grid = ft.ResponsiveRow(controls=event_cards, spacing=12, run_spacing=12)

        header_row = ft.Row([
            ft.Row([
                ft.Container(
                    width=36, height=36, border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.12, "#10B981"),
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.EVENT_NOTE, color="#10B981", size=20),
                ),
                ft.Container(width=8),
                ft.Column([
                    ft.Text("Próximos Eventos", size=16, weight="bold", color=colors["text"]),
                    ft.Text("Eventos de esta semana y la semana entrante", size=11, color=colors["text_muted"]),
                ], spacing=0),
            ], spacing=0),
            ft.IconButton(
                icon=ft.Icons.ARROW_FORWARD,
                icon_color="#10B981",
                tooltip="Ver en Calendario",
                on_click=self._go_to_calendar,
            ) if is_mob else ft.TextButton(
                "Ver en Calendario",
                icon=ft.Icons.ARROW_FORWARD,
                icon_color="#10B981",
                style=ft.ButtonStyle(color="#10B981"),
                on_click=self._go_to_calendar,
            )
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)


        self.chart_container.content = ft.Container(
            content=ft.Column([
                header_row,
                ft.Container(height=14),
                events_grid,
            ], spacing=0),
            padding=ft.padding.all(18 if is_mob else 20),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            shadow=ft.BoxShadow(blur_radius=12, spread_radius=-2, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        )

    def _create_note_card(self, note):
        """Crea tarjeta de nota idéntica a la de Figma con protección Solo Lectura para estudiantes."""
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
        profesor_nombre = note.get("profesor", "")
        is_teacher_assigned = bool(profesor_nombre or note.get("profesor_id"))

        def _do_delete(e):
            nid = note.get("id")
            if nid:
                self._notas = [n for n in self._notas if n.get("id") != nid]
                from services.navigation_service import NavigationController
                NavigationController.cache["notes"] = self._notas
                self._refresh_ui_full()
                import threading
                threading.Thread(target=lambda: self._db.eliminar_nota(nid, self._uid) if hasattr(self._db, 'eliminar_nota') else None, daemon=True).start()

        # Si es un estudiante y la nota fue puesta por un profesor -> SOLO LECTURA (sin opción de eliminar)
        can_delete = not (self._rol == "estudiante" and is_teacher_assigned)

        teacher_badge = ft.Container()
        if is_teacher_assigned:
            teacher_badge = ft.Row([
                ft.Icon(ft.Icons.LOCK, size=11, color="#10B981"),
                ft.Text(f"Profesor: {profesor_nombre or 'Docente'}", size=10, weight="bold", color="#10B981")
            ], spacing=2)

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 1)),
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
                        teacher_badge,
                    ], expand=True, spacing=1),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        icon_size=18,
                        icon_color="#94A3B8",
                        items=[
                            ft.PopupMenuItem(icon=ft.Icons.DELETE_OUTLINE, text="Eliminar", on_click=_do_delete),
                        ]
                    ) if can_delete else ft.Icon(ft.Icons.LOCK_OUTLINED, size=16, color="#94A3B8", tooltip="Nota asignada por profesor (Solo Lectura)")
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                ft.Text(comment, size=11, color="#64748B", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ], spacing=0)
        )

    def _show_assign_grade_modal(self, e=None):
        """Modal exclusivo para que profesores asignen calificaciones a estudiantes."""
        colors = self._get_theme_colors()
        estudiantes = self._db.obtener_estudiantes() or []

        if not estudiantes:
            dlg = ft.AlertDialog(
                title=ft.Text("Sin Estudiantes Registrados"),
                content=ft.Text("No hay estudiantes registrados en la base de datos para asignar calificaciones."),
                actions=[ft.TextButton("Entendido", on_click=lambda e: self.page.close(dlg))]
            )
            self.page.open(dlg)
            return

        student_options = [ft.dropdown.Option(key=str(s["id"]), text=f"{s['nombre']} ({s['email']})") for s in estudiantes]
        student_dropdown = ft.Dropdown(label="Seleccionar Estudiante", options=student_options, border_radius=10)

        subject_options = [ft.dropdown.Option(text=s) for s in self.SUBJECTS]
        subject_dropdown = ft.Dropdown(label="Asignatura", options=subject_options, border_radius=10, value=self.SUBJECTS[0])

        grade_field = ft.TextField(label="Calificación (0.0 - 5.0)", hint_text="Ej: 4.8", border_radius=10, keyboard_type=ft.KeyboardType.NUMBER)
        comment_field = ft.TextField(label="Comentario pedagógico", hint_text="Ej: Excelente esfuerzo en el proyecto...", border_radius=10, multiline=True)

        def _do_save_grade(e):
            sid = student_dropdown.value
            subj = subject_dropdown.value
            gval = grade_field.value.strip()
            comment = comment_field.value.strip()

            if not sid:
                student_dropdown.error_text = "Selecciona un estudiante"
                try: student_dropdown.update()
                except: pass
                return

            try:
                gfloat = float(gval)
                if not (0.0 <= gfloat <= 5.0): raise ValueError()
            except:
                grade_field.error_text = "Ingresa un número entre 0.0 y 5.0"
                try: grade_field.update()
                except: pass
                return

            fecha_actual = date.today().strftime("%Y-%m-%d")
            res = self._db.guardar_nota(int(sid), self._uid, subj, gfloat, fecha_actual, comment)

            self.page.close(dlg)
            if res and res.get("ok"):
                from services.navigation_service import NavigationController
                NavigationController.cache.pop("notes", None)
                self._load_notas()
                self._refresh_ui_full()

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.SCHOOL, color="#10B981"),
                ft.Text("Asignar Calificación a Estudiante", weight="bold", size=18)
            ]),
            content=ft.Container(
                width=450,
                height=360,
                content=ft.Column([
                    student_dropdown,
                    ft.Container(height=8),
                    subject_dropdown,
                    ft.Container(height=8),
                    grade_field,
                    ft.Container(height=8),
                    comment_field,
                ], spacing=0, scroll=get_scroll_mode("AUTO"))
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Guardar Nota", bgcolor="#10B981", color="white", on_click=_do_save_grade)
            ]
        )
        self.page.open(dlg)


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
                        padding=ft.padding.all(30),
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=36, color=ft.Colors.GREY_400),
                            ft.Text("No se encontraron calificaciones", color=ft.Colors.GREY_500, size=12),
                        ], horizontal_alignment="center")
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

    def _show_expanded_notes_dialog(self):
        """Modal expandido de calificaciones en 4 columnas (idéntico a la Imagen 2 de Figma)."""
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
            modal_grid_ref.current.update()
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
                width=920,
                height=600,
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
        pass

    def _build_left_sidebar(self, colors):
        """Sidebar izquierda de navegación estilo Figma."""
        from services.navigation_service import NavigationController

        def nav_item(label, icon, active=False, target="Notas"):
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE if active else "#475569", size=18),
                    ft.Text(label, color=ft.Colors.WHITE if active else "#1F2937",
                            size=13, weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL),
                ], spacing=10),
                bgcolor="#0A1E3D" if active else ft.Colors.TRANSPARENT,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                on_click=lambda e, t=target: NavigationController.update_view(t),
            )

        promedio_card = ft.Container(
            padding=ft.padding.all(14),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SCHOOL, color="#8B5CF6", size=18),
                    ft.Text("Promedio General", size=11, weight="bold", color="#0F172A"),
                ], spacing=6),
                ft.Container(height=4),
                ft.Text("4.30", size=24, weight="bold", color="#8B5CF6"),
                ft.Row([
                    ft.Icon(ft.Icons.ARROW_UPWARD, color="#10B981", size=12),
                    ft.Text("0.25 vs mes anterior", size=10, color="#64748B"),
                ], spacing=2),
                ft.Container(height=6),
                ft.ProgressBar(value=0.86, color="#8B5CF6", bgcolor="#F3E8FF", height=6),
                ft.Container(height=6),
                ft.Row([
                    ft.Container(width=8, height=8, border_radius=4, bgcolor="#10B981"),
                    ft.Text("Buen desempeño", size=10, color="#475569", weight="w500"),
                ], spacing=6)
            ], spacing=0)
        )

        return ft.Container(
            width=200,
            bgcolor=colors["surface"],
            border=ft.border.only(right=ft.BorderSide(1, "#E2E8F0")),
            padding=ft.padding.all(16),
            content=ft.Column([
                nav_item("Calificaciones", ft.Icons.BAR_CHART_OUTLINED, active=True, target="Notas"),
                nav_item("Asignaturas", ft.Icons.BOOK_OUTLINED, target="Notas"),
                nav_item("Calendario", ft.Icons.CALENDAR_MONTH_OUTLINED, target="Calendario"),
                nav_item("Mensajes", ft.Icons.CHAT_OUTLINED, target="Mensajeria"),
                nav_item("Ajustes", ft.Icons.SETTINGS_OUTLINED, target="Perfil"),
                ft.Container(expand=True),
                promedio_card
            ], spacing=6)
        )

    def _build_right_sidebar(self, colors):
        """Sidebar derecha simplificada con consejo del día y consejos académicos."""
        selected_tip = random.choice(self.TIPS_LIST)
        tip_card = ft.Container(
            padding=ft.padding.all(14),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color="#8B5CF6", size=20),
                    ft.Text("Consejo de Estudio", size=13, weight="bold", color="#0F172A"),
                ], spacing=6),
                ft.Container(height=8),
                ft.Text(selected_tip, size=11, color="#64748B"),
            ], spacing=0)
        )

        return ft.Container(
            width=240,
            bgcolor=colors["surface"],
            border=ft.border.only(left=ft.BorderSide(1, "#E2E8F0")),
            padding=ft.padding.all(16),
            content=ft.Column([
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

        left_sidebar = self._build_left_sidebar(colors)
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

        header_actions = [
            ft.IconButton(
                icon=ft.Icons.ZOOM_OUT_MAP,
                icon_size=18,
                icon_color="#64748B",
                tooltip="Expandir",
                on_click=lambda e: self._show_expanded_notes_dialog(),
            )
        ]
        if self._rol == "profesor":
            header_actions.insert(0, ft.ElevatedButton(
                icon=ft.Icons.ADD,
                text="Asignar Calificación",
                bgcolor="#10B981",
                color="white",
                on_click=self._show_assign_grade_modal
            ))

        tus_calificaciones_card = ft.Container(
            padding=ft.padding.all(16),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Column([
                ft.Row([
                    ft.Text("Notas de Estudiantes" if self._rol == "profesor" else "Tus calificaciones", size=15, weight="bold", color="#0F172A"),
                    ft.Container(expand=True),
                    ft.Row(controls=header_actions, spacing=8),
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
        ], spacing=0, expand=True)

        is_mob = self.is_mobile()
        if is_mob:
            main_body = ft.Container(
                expand=True,
                padding=ft.padding.all(12),
                content=ft.Column([center_content, right_sidebar], scroll=get_scroll_mode(self.page))
            )
        else:
            main_body = ft.Container(
                expand=True,
                padding=ft.padding.all(20),
                content=ft.Row([
                    left_sidebar,
                    ft.Container(width=16),
                    ft.Container(expand=True, content=center_content),
                    ft.Container(width=16),
                    right_sidebar,
                ], spacing=0, expand=True)
            )

        controls = [navbar, main_body]
        if is_mob:
            controls.append(self._build_bottom_nav("Notas"))

        return ft.Column(controls=controls, expand=True, spacing=0)

