"""
pages/assignments_page.py - v20.0 Módulo de Asignaciones y Tareas (Estilo Google Classroom)
Permite a los profesores crear y calificar tareas, y a los estudiantes consultar y entregar sus asignaciones con archivos adjuntos.
"""

import flet as ft
import threading
import time
import os
import copy
import random
from datetime import date, datetime, timedelta
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class AssignmentsPage(BasePage):
    """Página de Asignaciones y Tareas v20.0 (Estilo Google Classroom)."""

    SUBJECTS = [
        "Informática", "Matemáticas", "Inglés", "Valores",
        "Física", "Historia", "Química", "Biología", "Español", "Arte",
    ]

    DEFAULT_ASSIGNMENTS = [
        {
            "id": "asig_101",
            "titulo": "Taller #2: Ecuaciones Diferenciales y Aplicaciones",
            "asignatura": "Matemáticas",
            "profesor": "Prof. Carlos Mendoza",
            "estudiante_id": "todos",
            "estudiante_nombre": "Todos los estudiantes",
            "fecha_entrega": (date.today() + timedelta(days=3)).isoformat(),
            "hora_entrega": "23:59",
            "instrucciones": "Resolver los ejercicios de la página 45 a la 50 del libro guía. Presentar el procedimiento completo de forma clara.",
            "puntuacion_maxima": 5.0,
            "estado": "Pendiente", # Pendiente, Entregado, Calificado
            "entrega_texto": "",
            "archivo_adjunto": "",
            "calificacion": None,
            "retroalimentacion": "",
        },
        {
            "id": "asig_102",
            "titulo": "Proyecto Final: Sistema de Gestión en Python",
            "asignatura": "Informática",
            "profesor": "Prof. Ana Martínez",
            "estudiante_id": "todos",
            "estudiante_nombre": "Todos los estudiantes",
            "fecha_entrega": (date.today() + timedelta(days=7)).isoformat(),
            "hora_entrega": "18:00",
            "instrucciones": "Desarrollar una aplicación de consola o GUI en Python aplicando POO y persistencia de datos. Incluir archivo README.",
            "puntuacion_maxima": 5.0,
            "estado": "Pendiente",
            "entrega_texto": "",
            "archivo_adjunto": "",
            "calificacion": None,
            "retroalimentacion": "",
        },
        {
            "id": "asig_103",
            "titulo": "Informe de Laboratorio: Reacciones Químicas",
            "asignatura": "Química",
            "profesor": "Prof. Roberto Gómez",
            "estudiante_id": "todos",
            "estudiante_nombre": "Todos los estudiantes",
            "fecha_entrega": (date.today() - timedelta(days=1)).isoformat(),
            "hora_entrega": "12:00",
            "instrucciones": "Redactar el informe correspondiente a la práctica de laboratorio #4 incluyendo tabla de observaciones y conclusiones.",
            "puntuacion_maxima": 5.0,
            "estado": "Calificado",
            "entrega_texto": "Adjunto el informe detallado con gráficos y tablas de resultados.",
            "archivo_adjunto": "Informe_Laboratorio_Quimica.pdf",
            "calificacion": 4.8,
            "retroalimentacion": "Excelente trabajo en la discusión de resultados y tablas completas.",
        },
    ]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        self._rol = str(self._user.get("rol") or self._user.get("role") or "").lower()
        self._is_profesor = "profesor" in self._rol or "docente" in self._rol or "maestro" in self._rol or "admin" in self._rol or self._user.get("es_profesor", False)
        
        self._assignments: list = []
        self._filter_status = "Todas" # Todas, Pendientes, Entregadas, Calificadas
        self._search_term = ""
        
        self._assignments_grid_ref = ft.Ref[ft.Container]()
        self._search_ref = ft.Ref[ft.TextField]()
        self._file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.page.overlay.append(self._file_picker)
        self._pending_file_path = ""
        self._pending_file_name = ""

    def _load_assignments(self):
        """Carga asignaciones desde caché o BD. Si está vacío, usa predeterminadas."""
        from services.navigation_service import NavigationController
        cached = NavigationController.cache.get("assignments", [])
        if cached:
            self._assignments = copy.deepcopy(cached)
        else:
            db_data = self._db.obtener_asignaciones(self._uid) if hasattr(self._db, "obtener_asignaciones") and self._uid else []
            if db_data:
                self._assignments = copy.deepcopy(db_data)
            else:
                self._assignments = copy.deepcopy(self.DEFAULT_ASSIGNMENTS)
            NavigationController.cache["assignments"] = copy.deepcopy(self._assignments)

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            self._pending_file_path = e.files[0].path
            self._pending_file_name = e.files[0].name
            self._show_info(f"Archivo adjuntado: {self._pending_file_name}")

    def _get_filtered_assignments(self) -> list:
        result = list(self._assignments)
        
        # Filtro por estado
        if self._filter_status == "Pendientes":
            result = [a for a in result if a.get("estado") == "Pendiente"]
        elif self._filter_status == "Entregadas":
            result = [a for a in result if a.get("estado") == "Entregado"]
        elif self._filter_status == "Calificadas":
            result = [a for a in result if a.get("estado") == "Calificado"]
            
        # Filtro por búsqueda
        if self._search_term.strip():
            term = self._search_term.strip().lower()
            result = [
                a for a in result
                if term in a.get("titulo", "").lower()
                or term in a.get("asignatura", "").lower()
                or term in a.get("instrucciones", "").lower()
            ]
        return result

    def _open_create_assignment_dialog(self, e=None):
        """Modal interactivo para que el profesor cree una nueva asignación / tarea."""
        all_users = self._db.obtener_todos_los_usuarios() or []
        students = [u for u in all_users if "profesor" not in str(u.get("rol", "")).lower() and u.get("id") != self._uid]
        
        student_options = [ft.dropdown.Option("todos", text="👥 Todos los estudiantes de la comunidad")]
        for s in students:
            student_options.append(
                ft.dropdown.Option(
                    key=str(s["id"]),
                    text=f"👤 {s.get('name') or s.get('nombre') or s.get('email')}"
                )
            )

        title_input = ft.TextField(
            label="Título de la Asignación",
            hint_text="Ej: Taller #3 - Ecuaciones de Segundo Grado",
            border_radius=10,
            autofocus=True,
        )

        subject_dropdown = ft.Dropdown(
            label="Asignatura",
            options=[ft.dropdown.Option(s) for s in self.SUBJECTS],
            value=self.SUBJECTS[0],
            border_radius=10,
        )

        assignee_dropdown = ft.Dropdown(
            label="Asignar a",
            options=student_options,
            value="todos",
            border_radius=10,
        )

        due_date_input = ft.TextField(
            label="Fecha de Entrega (AAAA-MM-DD)",
            value=(date.today() + timedelta(days=5)).isoformat(),
            border_radius=10,
        )

        due_time_input = ft.TextField(
            label="Hora Límite",
            value="23:59",
            border_radius=10,
        )

        instructions_input = ft.TextField(
            label="Instrucciones y Requisitos",
            hint_text="Describe detalladamente los objetivos y criterios de evaluación de la tarea...",
            border_radius=10,
            multiline=True,
            min_lines=3,
            max_lines=4,
        )

        max_grade_input = ft.TextField(
            label="Puntuación Máxima",
            value="5.0",
            border_radius=10,
        )

        def _save_assignment(e):
            t_title = title_input.value.strip()
            if not t_title:
                self._show_info("Ingresa un título para la asignación.")
                return

            sel_assignee_key = assignee_dropdown.value
            if sel_assignee_key == "todos":
                st_name = "Todos los estudiantes"
            else:
                match_st = next((s for s in students if str(s["id"]) == str(sel_assignee_key)), None)
                st_name = match_st.get("name") if match_st else "Estudiante"

            new_asig = {
                "id": f"asig_{int(time.time())}_{random.randint(100, 999)}",
                "titulo": t_title,
                "asignatura": subject_dropdown.value,
                "profesor": self._user.get("name", "Profesor"),
                "estudiante_id": sel_assignee_key,
                "estudiante_nombre": st_name,
                "fecha_entrega": due_date_input.value.strip() or date.today().isoformat(),
                "hora_entrega": due_time_input.value.strip() or "23:59",
                "instrucciones": instructions_input.value.strip() or "Sin instrucciones específicas.",
                "puntuacion_maxima": float(max_grade_input.value.strip() or 5.0),
                "estado": "Pendiente",
                "entrega_texto": "",
                "archivo_adjunto": "",
                "calificacion": None,
                "retroalimentacion": "",
            }

            self._assignments.insert(0, new_asig)
            from services.navigation_service import NavigationController
            NavigationController.cache["assignments"] = copy.deepcopy(self._assignments)

            def _save_bg():
                try:
                    if hasattr(self._db, "guardar_asignacion"):
                        self._db.guardar_asignacion(new_asig)
                except: pass
            threading.Thread(target=_save_bg, daemon=True).start()

            self.page.close(dlg)
            self._refresh_ui()
            self._show_info(f"Asignación publicada con éxito: '{t_title}'")

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, color="#7C3AED", size=24),
                ft.Text("Crear Nueva Asignación / Tarea", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=500, height=440,
                content=ft.Column([
                    ft.Text("Publica una tarea para que tus estudiantes la completen y envíen:", size=12, color="#64748B"),
                    ft.Container(height=8),
                    title_input,
                    ft.Container(height=6),
                    ft.Row([subject_dropdown, assignee_dropdown], spacing=10),
                    ft.Container(height=6),
                    ft.Row([due_date_input, due_time_input, max_grade_input], spacing=10),
                    ft.Container(height=6),
                    instructions_input,
                ], spacing=0, scroll=get_scroll_mode("AUTO"), expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Publicar Asignación", bgcolor="#7C3AED", color="white", on_click=_save_assignment),
            ]
        )
        self.page.open(dlg)

    def _open_submit_dialog(self, assignment: dict):
        """Modal para que el estudiante entregue su solución / tarea."""
        self._pending_file_path = assignment.get("archivo_adjunto", "")
        self._pending_file_name = os.path.basename(self._pending_file_path) if self._pending_file_path else ""

        response_input = ft.TextField(
            label="Respuesta / Comentarios de la Entrega",
            value=assignment.get("entrega_texto", ""),
            hint_text="Escribe aquí tu solución, notas o enlaces de interés...",
            border_radius=10,
            multiline=True,
            min_lines=3,
            max_lines=5,
        )

        file_status_text = ft.Text(
            f"📎 Archivo: {self._pending_file_name}" if self._pending_file_name else "📎 Sin archivo adjunto",
            size=12, color="#7C3AED" if self._pending_file_name else "#64748B", weight="bold"
        )

        def _pick_file(e):
            self._file_picker.pick_files(
                allowed_extensions=["pdf", "docx", "zip", "png", "jpg", "py", "txt"]
            )
            def check_loop():
                time.sleep(0.5)
                if self._pending_file_name:
                    file_status_text.value = f"📎 Archivo adjuntado: {self._pending_file_name}"
                    file_status_text.color = "#16A34A"
                    try: file_status_text.update()
                    except: pass
            threading.Thread(target=check_loop, daemon=True).start()

        def _do_submit(e):
            ans = response_input.value.strip()
            if not ans and not self._pending_file_name:
                self._show_info("Ingresa una respuesta en texto o adjunta un archivo.")
                return

            assignment["estado"] = "Entregado"
            assignment["entrega_texto"] = ans
            assignment["archivo_adjunto"] = self._pending_file_name or self._pending_file_path
            assignment["fecha_respuesta"] = datetime.now().strftime("%Y-%m-%d %H:%M")

            from services.navigation_service import NavigationController
            NavigationController.cache["assignments"] = copy.deepcopy(self._assignments)

            self.page.close(dlg)
            self._refresh_ui()
            self._show_info(f"¡Tarea '{assignment.get('titulo')}' entregada con éxito! 🚀")

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.UPLOAD_FILE, color="#7C3AED", size=24),
                ft.Text("Entregar Asignación", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=460, height=360,
                content=ft.Column([
                    ft.Text(assignment.get("titulo", ""), size=14, weight="bold", color="#0F172A"),
                    ft.Text(f"Asignatura: {assignment.get('asignatura')} • Límite: {assignment.get('fecha_entrega')}", size=11, color="#64748B"),
                    ft.Divider(height=16),
                    response_input,
                    ft.Container(height=10),
                    ft.Row([
                        ft.OutlinedButton(
                            "Adjuntar Archivo",
                            icon=ft.Icons.ATTACH_FILE,
                            on_click=_pick_file
                        ),
                        ft.Container(width=10),
                        file_status_text,
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0, expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Entregar Tarea", bgcolor="#16A34A", color="white", on_click=_do_submit),
            ]
        )
        self.page.open(dlg)

    def _open_grade_dialog(self, assignment: dict):
        """Modal para que el profesor califique la tarea entregada."""
        grade_input = ft.TextField(
            label="Calificación (0.0 a 5.0)",
            value=str(assignment.get("calificacion") or 5.0),
            border_radius=10,
            autofocus=True,
        )
        feedback_input = ft.TextField(
            label="Retroalimentación / Comentarios del Profesor",
            value=assignment.get("retroalimentacion", ""),
            border_radius=10,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        def _do_grade(e):
            try:
                g_val = float(grade_input.value.strip().replace(",", "."))
                if not (0.0 <= g_val <= 5.0):
                    self._show_info("La nota debe estar entre 0.0 y 5.0")
                    return
            except ValueError:
                self._show_info("Ingresa una nota válida (ej: 4.8)")
                return

            assignment["calificacion"] = round(g_val, 1)
            assignment["retroalimentacion"] = feedback_input.value.strip() or "Sin comentarios."
            assignment["estado"] = "Calificado"

            from services.navigation_service import NavigationController
            NavigationController.cache["assignments"] = copy.deepcopy(self._assignments)

            self.page.close(dlg)
            self._refresh_ui()
            self._show_info(f"Tarea calificada: {round(g_val, 1)} / 5.0")

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.STARS, color="#EAB308", size=24),
                ft.Text("Calificar Tarea Entregada", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=440, height=360,
                content=ft.Column([
                    ft.Text(assignment.get("titulo", ""), size=14, weight="bold", color="#0F172A"),
                    ft.Text(f"Estudiante: {assignment.get('estudiante_nombre')}", size=11, color="#64748B"),
                    ft.Container(height=8),
                    ft.Container(
                        padding=10, bgcolor="#F8FAFC", border_radius=8, border=ft.border.all(1, "#E2E8F0"),
                        content=ft.Column([
                            ft.Text("Respuesta recibida:", size=11, weight="bold", color="#475569"),
                            ft.Text(assignment.get("entrega_texto") or "Sin texto de entrega", size=11, color="#0F172A"),
                            ft.Text(f"📎 Archivo: {assignment.get('archivo_adjunto')}" if assignment.get('archivo_adjunto') else "", size=11, color="#7C3AED", weight="bold"),
                        ], spacing=2)
                    ),
                    ft.Container(height=10),
                    grade_input,
                    ft.Container(height=8),
                    feedback_input,
                ], spacing=0, expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Guardar Calificación", bgcolor="#7C3AED", color="white", on_click=_do_grade),
            ]
        )
        self.page.open(dlg)

    def _delete_assignment(self, assignment: dict):
        aid = assignment.get("id")
        self._assignments = [a for a in self._assignments if a.get("id") != aid]
        from services.navigation_service import NavigationController
        NavigationController.cache["assignments"] = copy.deepcopy(self._assignments)
        self._refresh_ui()
        self._show_info("Asignación eliminada.")

    def _build_assignment_card(self, asig: dict, colors: dict) -> ft.Container:
        estado = asig.get("estado", "Pendiente")
        
        if estado == "Calificado":
            badge_bg = "#DCFCE7"
            badge_color = "#16A34A"
            badge_icon = ft.Icons.CHECK_CIRCLE
            badge_text = f"Calificado ({asig.get('calificacion')} / 5.0)"
        elif estado == "Entregado":
            badge_bg = "#DBEAFE"
            badge_color = "#2563EB"
            badge_icon = ft.Icons.UNARCHIVE
            badge_text = "Entregado 🚀"
        else:
            badge_bg = "#FEF3C7"
            badge_color = "#D97706"
            badge_icon = ft.Icons.SCHEDULE
            badge_text = "Pendiente"

        action_buttons = []
        if self._is_profesor:
            if estado == "Entregado":
                action_buttons.append(
                    ft.ElevatedButton(
                        "Calificar",
                        icon=ft.Icons.GRADE,
                        bgcolor="#7C3AED",
                        color="white",
                        height=32,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda e, curr=asig: self._open_grade_dialog(curr)
                    )
                )
            action_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color="#EF4444",
                    icon_size=18,
                    tooltip="Eliminar asignación",
                    on_click=lambda e, curr=asig: self._delete_assignment(curr)
                )
            )
        else:
            if estado == "Pendiente":
                action_buttons.append(
                    ft.ElevatedButton(
                        "🚀 Entregar Tarea",
                        bgcolor="#16A34A",
                        color="white",
                        height=34,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda e, curr=asig: self._open_submit_dialog(curr)
                    )
                )
            else:
                action_buttons.append(
                    ft.OutlinedButton(
                        "Ver Entrega",
                        icon=ft.Icons.VISIBILITY,
                        height=34,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda e, curr=asig: self._open_submit_dialog(curr)
                    )
                )

        return ft.Container(
            padding=ft.padding.all(16),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.BLACK12, offset=ft.Offset(0, 1)),
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor=badge_bg,
                        border_radius=8,
                        content=ft.Row([
                            ft.Icon(badge_icon, color=badge_color, size=14),
                            ft.Text(badge_text, size=11, weight="bold", color=badge_color),
                        ], spacing=4)
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        bgcolor="#F1F5F9",
                        border_radius=6,
                        content=ft.Text(asig.get("asignatura", "General"), size=10, weight="bold", color="#475569")
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Text(asig.get("titulo", ""), size=15, weight="bold", color=colors["text"]),
                ft.Container(height=4),
                ft.Text(asig.get("instrucciones", ""), size=12, color=colors["text_secondary"], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Divider(height=16, color="#F1F5F9"),
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color="#64748B"),
                            ft.Text(f"Entrega: {asig.get('fecha_entrega')} ({asig.get('hora_entrega', '23:59')})", size=11, color="#64748B"),
                        ], spacing=4),
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON_OUTLINE, size=12, color="#64748B"),
                            ft.Text(f"Profesor: {asig.get('profesor', 'Docente')}", size=11, color="#64748B"),
                        ], spacing=4),
                    ], spacing=2, expand=True),
                    ft.Row(action_buttons, spacing=6),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=0)
        )

    def _refresh_ui(self):
        filtered = self._get_filtered_assignments()
        colors = self._get_theme_colors()

        if not filtered:
            self._assignments_grid_ref.current.content = ft.Container(
                padding=ft.padding.all(40),
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.Icons.ASSIGNMENT_TURNED_IN_OUTLINED, size=56, color="#94A3B8"),
                    ft.Text("No hay asignaciones para mostrar", size=15, weight="bold", color="#64748B"),
                    ft.Text("Las tareas asignadas por tus profesores aparecerán aquí.", size=12, color="#94A3B8"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
            )
        else:
            cards = [self._build_assignment_card(a, colors) for a in filtered]
            self._assignments_grid_ref.current.content = ft.Column(
                cards, spacing=12, scroll=get_scroll_mode("AUTO"), expand=True
            )

        try: self.page.update()
        except: pass

    def build(self) -> ft.Control:
        self._load_assignments()
        colors = self._get_theme_colors()
        navbar = self._build_navbar("Asignaciones y Tareas")

        # KPI Header Cards
        total_count = len(self._assignments)
        pending_count = len([a for a in self._assignments if a.get("estado") == "Pendiente"])
        done_count = len([a for a in self._assignments if a.get("estado") == "Entregado"])
        graded_count = len([a for a in self._assignments if a.get("estado") == "Calificado"])

        def kpi_card(title, count, icon, bg, text_color):
            return ft.Container(
                padding=ft.padding.all(14),
                bgcolor=colors["surface"],
                border_radius=14,
                border=ft.border.all(1, "#E2E8F0"),
                expand=True,
                content=ft.Row([
                    ft.Container(
                        width=40, height=40, border_radius=10, bgcolor=bg,
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=text_color, size=20)
                    ),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(str(count), size=18, weight="bold", color=colors["text"]),
                        ft.Text(title, size=11, color=colors["text_secondary"]),
                    ], spacing=0, expand=True)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        kpi_row = ft.Row([
            kpi_card("Total Tareas", total_count, ft.Icons.ASSIGNMENT, "#EEF2FF", "#4F46E5"),
            kpi_card("Pendientes", pending_count, ft.Icons.SCHEDULE, "#FEF3C7", "#D97706"),
            kpi_card("Entregadas", done_count, ft.Icons.UNARCHIVE, "#DBEAFE", "#2563EB"),
            kpi_card("Calificadas", graded_count, ft.Icons.STARS, "#DCFCE7", "#16A34A"),
        ], spacing=12)

        def _sync_gcal(asig):
            try:
                from services.google_service import google_service
                res = google_service.sync_to_google_calendar(
                    title=asig.get("titulo", "Tarea PointList"),
                    due_date=asig.get("fecha_entrega", "2026-08-20"),
                    description=asig.get("instrucciones", "")
                )
                if res["ok"]:
                    self._show_info(f"📅 ¡'{asig.get('titulo')}' sincronizada con Google Calendar!")
            except Exception as ex:
                self._show_info(f"⚠️ Error al sincronizar: {str(ex)}")

        def _open_grade_calculator_modal(e=None):
            val_f = ft.TextField(label="Nota Actual (1.0 - 5.0)", value="4.2", border_radius=10)
            target_f = ft.TextField(label="Nota Objetivo Deseada", value="4.8", border_radius=10)
            result_txt = ft.Text("Se requiere obtener mínimo 4.9 en las tareas restantes.", size=13, weight="bold", color="#0284C7")

            def _recalc(e):
                try:
                    curr = float(val_f.value)
                    targ = float(target_f.value)
                    needed = round((targ * 2) - curr, 1)
                    if needed > 5.0:
                        result_txt.value = f"⚠️ Se necesitaría {needed} (supera 5.0). ¡Empieza con repasos Pomodoro!"
                        result_txt.color = "#DC2626"
                    else:
                        result_txt.value = f"🎯 ¡Necesitas sacar {max(1.0, needed)} en la siguiente entrega para alcanzar {targ}!"
                        result_txt.color = "#16A34A"
                except:
                    result_txt.value = "Ingresa números válidos."
                try: self.page.update()
                except: pass

            val_f.on_change = _recalc
            target_f.on_change = _recalc

            calc_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Icon(ft.Icons.CALCULATE, color="#0284C7"), ft.Text("Predictor de Nota Objetivo", size=16, weight="bold")]),
                content=ft.Column([
                    ft.Text("Calcula la calificación exacta que necesitas en tus próximas asignaciones:"),
                    ft.Container(height=8),
                    val_f,
                    target_f,
                    ft.Container(height=8),
                    result_txt
                ], spacing=6, tight=True),
                actions=[
                    ft.ElevatedButton("Entendido", bgcolor="#0284C7", color="white", on_click=lambda e: self.page.close(calc_dlg))
                ]
            )
            self.page.open(calc_dlg)

        # Action Buttons para Profesor / Estudiante
        calc_btn = ft.OutlinedButton("📊 Predictor de Notas", height=38, on_click=_open_grade_calculator_modal)

        create_btn = ft.Row([
            calc_btn,
            ft.ElevatedButton(
                "➕ Crear Tarea",
                bgcolor="#7C3AED",
                color=ft.Colors.WHITE,
                height=38,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=self._open_create_assignment_dialog,
            ) if self._is_profesor else ft.ElevatedButton(
                "📅 Sincronizar Google Calendar",
                bgcolor="#0284C7",
                color=ft.Colors.WHITE,
                height=38,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=lambda e: _sync_gcal(self._assignments[0] if self._assignments else {}),
            )
        ], spacing=8)

        # Filtros de estado (Todas, Pendientes, Entregadas, Calificadas)
        def _set_filter(st):
            self._filter_status = st
            self._refresh_ui()

        filter_buttons = []
        for status in ["Todas", "Pendientes", "Entregadas", "Calificadas"]:
            is_sel = self._filter_status == status
            filter_buttons.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=self.primary_color if is_sel else "#F1F5F9",
                    border_radius=8,
                    ink=True,
                    on_click=lambda e, st=status: _set_filter(st),
                    content=ft.Text(status, size=12, weight="bold" if is_sel else "normal", color="white" if is_sel else "#475569")
                )
            )

        search_field = ft.TextField(
            ref=self._search_ref,
            hint_text="Buscar tarea por título o asignatura...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            height=40,
            bgcolor=colors["surface"],
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
            on_change=lambda e: (setattr(self, "_search_term", e.control.value), self._refresh_ui()),
            expand=True,
        )

        filter_bar = ft.Container(
            padding=ft.padding.all(14),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, "#E2E8F0"),
            content=ft.Row([
                search_field,
                ft.Container(width=10),
                ft.Row(filter_buttons, spacing=6),
                ft.Container(width=10 if self._is_profesor else 0),
                create_btn,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        self._assignments_grid_ref.current = ft.Container(expand=True)
        self._refresh_ui()

        return ft.Column([
            navbar,
            ft.Container(
                expand=True,
                padding=ft.padding.all(20),
                content=ft.Column([
                    kpi_row,
                    ft.Container(height=16),
                    filter_bar,
                    ft.Container(height=16),
                    self._assignments_grid_ref.current,
                ], spacing=0, expand=True)
            )
        ], expand=True, spacing=0)
