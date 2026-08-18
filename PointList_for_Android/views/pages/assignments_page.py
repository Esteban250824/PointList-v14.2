"""
pages/assignments_page.py - v20.0 Módulo de Asignaciones y Tareas (Estilo Google Classroom)
Permite a los profesores crear y calificar tareas, y a los estudiantes consultar y entregar sus asignaciones con archivos adjuntos.
Adaptado 100% para la versión móvil Android y escritorio.
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
    """Página de Asignaciones y Tareas v20.0 adaptada para móvil (Estilo Google Classroom)."""

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
            "estado": "Pendiente",
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
        self._filter_status = "Todas"
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
        
        if self._filter_status == "Pendientes":
            result = [a for a in result if a.get("estado") == "Pendiente"]
        elif self._filter_status == "Entregadas":
            result = [a for a in result if a.get("estado") == "Entregado"]
        elif self._filter_status == "Calificadas":
            result = [a for a in result if a.get("estado") == "Calificado"]
            
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
        """Modal interactivo para crear una nueva asignación / tarea."""
        all_users = self._db.obtener_todos_los_usuarios() or []
        students = [u for u in all_users if "profesor" not in str(u.get("rol", "")).lower() and u.get("id") != self._uid]
        is_mob = self.is_mobile()

        student_options = [ft.dropdown.Option("todos", text="👥 Todos los estudiantes")]
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
            label="Fecha (AAAA-MM-DD)",
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
            hint_text="Describe detalladamente los objetivos y criterios de evaluación...",
            border_radius=10,
            multiline=True,
            min_lines=3,
            max_lines=4,
        )

        max_grade_input = ft.TextField(
            label="Nota Máxima",
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

        row1 = ft.Column([subject_dropdown, assignee_dropdown], spacing=8) if is_mob else ft.Row([subject_dropdown, assignee_dropdown], spacing=10)
        row2 = ft.Column([due_date_input, due_time_input, max_grade_input], spacing=8) if is_mob else ft.Row([due_date_input, due_time_input, max_grade_input], spacing=10)

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, color="#7C3AED", size=22 if is_mob else 24),
                ft.Text("Crear Nueva Asignación", size=16 if is_mob else 18, weight="bold")
            ]),
            content=ft.Container(
                width=340 if is_mob else 500,
                height=480 if is_mob else 440,
                content=ft.Column([
                    ft.Text("Publica una tarea para tus estudiantes:", size=11 if is_mob else 12, color="#64748B"),
                    ft.Container(height=6),
                    title_input,
                    ft.Container(height=6),
                    row1,
                    ft.Container(height=6),
                    row2,
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
        """Modal para que el estudiante entregue su tarea."""
        self._pending_file_path = assignment.get("archivo_adjunto", "")
        self._pending_file_name = os.path.basename(self._pending_file_path) if self._pending_file_path else ""
        is_mob = self.is_mobile()

        response_input = ft.TextField(
            label="Respuesta / Comentarios de la Entrega",
            value=assignment.get("entrega_texto", ""),
            hint_text="Escribe aquí tu solución o enlaces...",
            border_radius=10,
            multiline=True,
            min_lines=3,
            max_lines=5,
        )

        file_status_text = ft.Text(
            f"📎 Archivo: {self._pending_file_name}" if self._pending_file_name else "📎 Sin archivo adjunto",
            size=11 if is_mob else 12, color="#7C3AED" if self._pending_file_name else "#64748B", weight="bold"
        )

        def _pick_file(e):
            self._file_picker.pick_files(
                allowed_extensions=["pdf", "docx", "zip", "png", "jpg", "py", "txt"]
            )
            def check_loop():
                time.sleep(0.5)
                if self._pending_file_name:
                    file_status_text.value = f"📎 Archivo: {self._pending_file_name}"
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
                ft.Icon(ft.Icons.UPLOAD_FILE, color="#7C3AED", size=22 if is_mob else 24),
                ft.Text("Entregar Asignación", size=16 if is_mob else 18, weight="bold")
            ]),
            content=ft.Container(
                width=340 if is_mob else 460,
                height=380 if is_mob else 360,
                content=ft.Column([
                    ft.Text(assignment.get("titulo", ""), size=13 if is_mob else 14, weight="bold", color="#0F172A"),
                    ft.Text(f"Asignatura: {assignment.get('asignatura')} • Límite: {assignment.get('fecha_entrega')}", size=11, color="#64748B"),
                    ft.Divider(height=14),
                    response_input,
                    ft.Container(height=10),
                    ft.Column([
                        ft.OutlinedButton(
                            "Adjuntar Archivo",
                            icon=ft.Icons.ATTACH_FILE,
                            on_click=_pick_file
                        ),
                        ft.Container(height=4),
                        file_status_text,
                    ]) if is_mob else ft.Row([
                        ft.OutlinedButton(
                            "Adjuntar Archivo",
                            icon=ft.Icons.ATTACH_FILE,
                            on_click=_pick_file
                        ),
                        ft.Container(width=10),
                        file_status_text,
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0, scroll=get_scroll_mode("AUTO"), expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Entregar Tarea", bgcolor="#16A34A", color="white", on_click=_do_submit),
            ]
        )
        self.page.open(dlg)

    def _open_grade_dialog(self, assignment: dict):
        """Modal para calificar la tarea entregada."""
        is_mob = self.is_mobile()
        grade_input = ft.TextField(
            label="Calificación (0.0 a 5.0)",
            value=str(assignment.get("calificacion") or 5.0),
            border_radius=10,
            autofocus=True,
        )
        feedback_input = ft.TextField(
            label="Retroalimentación / Comentarios",
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
                ft.Icon(ft.Icons.STARS, color="#EAB308", size=22 if is_mob else 24),
                ft.Text("Calificar Tarea Entregada", size=16 if is_mob else 18, weight="bold")
            ]),
            content=ft.Container(
                width=340 if is_mob else 440,
                height=380 if is_mob else 360,
                content=ft.Column([
                    ft.Text(assignment.get("titulo", ""), size=13 if is_mob else 14, weight="bold", color="#0F172A"),
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
                ], spacing=0, scroll=get_scroll_mode("AUTO"), expand=True)
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
        is_mob = self.is_mobile()
        
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
            badge_text = "Pendiente ⏳"

        actions_list = []
        if self._is_profesor:
            if estado == "Entregado":
                actions_list.append(
                    ft.ElevatedButton(
                        "Calificar",
                        icon=ft.Icons.STARS,
                        bgcolor="#EAB308",
                        color="white",
                        height=36,
                        on_click=lambda e, a=asig: self._open_grade_dialog(a)
                    )
                )
            actions_list.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_400,
                    tooltip="Eliminar asignación",
                    on_click=lambda e, a=asig: self._delete_assignment(a)
                )
            )
        else:
            if estado == "Pendiente":
                actions_list.append(
                    ft.ElevatedButton(
                        "Entregar Tarea",
                        icon=ft.Icons.UPLOAD_FILE,
                        bgcolor="#7C3AED",
                        color="white",
                        height=36,
                        on_click=lambda e, a=asig: self._open_submit_dialog(a)
                    )
                )
            elif estado in ["Entregado", "Calificado"]:
                actions_list.append(
                    ft.OutlinedButton(
                        "Ver Entrega",
                        icon=ft.Icons.VISIBILITY,
                        height=36,
                        on_click=lambda e, a=asig: self._open_submit_dialog(a)
                    )
                )

        card_content = ft.Column([
            ft.Row([
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    bgcolor=badge_bg,
                    border_radius=12,
                    content=ft.Row([
                        ft.Icon(badge_icon, color=badge_color, size=14),
                        ft.Text(badge_text, color=badge_color, size=11, weight="bold"),
                    ], spacing=4, tight=True)
                ),
                ft.Text(asig.get("asignatura", "General"), size=12, weight="bold", color=self.primary_color),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=8),
            ft.Text(asig.get("titulo", "Sin título"), size=15 if is_mob else 16, weight="bold", color=colors["text"]),
            ft.Text(f"Profesor: {asig.get('profesor')} • Fecha límite: {asig.get('fecha_entrega')} {asig.get('hora_entrega', '')}", size=11, color=colors["text_muted"]),
            ft.Container(height=8),
            ft.Text(asig.get("instrucciones", ""), size=12, color=colors["text_secondary"], max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Container(height=12),
            ft.Row(actions_list, alignment=ft.MainAxisAlignment.END, spacing=8),
        ], spacing=0)

        return ft.Container(
            padding=ft.padding.all(14 if is_mob else 18),
            bgcolor=colors["surface"],
            border_radius=14,
            border=ft.border.all(1, colors["border"]),
            content=card_content
        )

    def _refresh_ui(self):
        filtered = self._get_filtered_assignments()
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()

        if not filtered:
            grid_content = ft.Container(
                padding=30,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.Icons.ASSIGNMENT_LATE, size=48, color=ft.Colors.GREY_400),
                    ft.Text("No hay asignaciones en esta categoría", size=14, color=ft.Colors.GREY_500)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        else:
            grid_content = ft.ResponsiveRow(
                controls=[
                    ft.Container(self._build_assignment_card(a, colors), col={"xs": 12, "sm": 6, "md": 6, "lg": 4})
                    for a in filtered
                ],
                spacing=12,
                run_spacing=12,
            )

        if self._assignments_grid_ref.current:
            self._assignments_grid_ref.current.content = grid_content
            try: self._assignments_grid_ref.current.update()
            except: pass

    def build(self) -> ft.Control:
        self._load_assignments()
        colors = self._get_theme_colors()
        navbar = self._build_navbar("Asignaciones y Tareas")
        is_mob = self.is_mobile()

        def _set_filter(f_name):
            self._filter_status = f_name
            self._refresh_ui()

        def _on_search(e):
            self._search_term = e.control.value
            self._refresh_ui()

        filter_buttons = [
            ft.TextButton("Todas", on_click=lambda e: _set_filter("Todas")),
            ft.TextButton("Pendientes", on_click=lambda e: _set_filter("Pendientes")),
            ft.TextButton("Entregadas", on_click=lambda e: _set_filter("Entregadas")),
            ft.TextButton("Calificadas", on_click=lambda e: _set_filter("Calificadas")),
        ]

        header_actions = []
        if self._is_profesor:
            header_actions.append(
                ft.ElevatedButton(
                    "+ Nueva Asignación",
                    bgcolor="#7C3AED",
                    color="white",
                    height=40,
                    on_click=self._open_create_assignment_dialog
                )
            )

        search_field = ft.TextField(
            ref=self._search_ref,
            hint_text="Buscar asignación...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            on_change=_on_search,
            expand=True,
        )

        filter_row = ft.Row(filter_buttons, scroll=get_scroll_mode("AUTO"))

        self._assignments_grid_ref.current = ft.Container(expand=True)
        self._refresh_ui()

        body = ft.Container(
            expand=True,
            padding=ft.padding.all(12 if is_mob else 24),
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Asignaciones & Tareas", size=20 if is_mob else 26, weight="bold", color=colors["text"]),
                        ft.Text("Consulta tus tareas pendientes, entregas y notas de clase.", size=12 if is_mob else 14, color=colors["text_muted"]),
                    ], expand=True),
                    ft.Row(header_actions) if header_actions else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=14),
                ft.Column([
                    search_field,
                    ft.Container(height=6),
                    filter_row,
                ]) if is_mob else ft.Row([
                    search_field,
                    filter_row,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=16),
                self._assignments_grid_ref.current,
            ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)
        )

        controls = [navbar, body]
        if is_mob:
            controls.append(self._build_bottom_nav("Asignaciones"))

        return ft.Column(controls, expand=True, spacing=0)
