"""
views/pages/subjects_page.py
PointList v14.2
Nueva vista "Mis materias" con acceso a tareas, calificaciones y recursos por cada asignatura.
Diseño idéntico a Figma (Imagen 3).
"""

import flet as ft
import copy
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class SubjectsPage(BasePage):
    """Página de Mis materias (Figma Redesign)."""

    SUBJECT_DETAILS = [
        {
            "id": "mat_inf",
            "name": "Informática",
            "subtitle": "Programación, base de datos, sitios web",
            "tip": "Gestiona tus tarea, notas y recursos en un solo lugar",
            "color": "#DC2626",
            "bg_color": "#FEF2F2",
            "icon_bg": "#FEE2E2",
            "icon_type": "laptop",
        },
        {
            "id": "mat_mat",
            "name": "Matemática",
            "subtitle": "Álgebra, cálculo y resolución de problemas",
            "tip": "Practica, repasa y mejora tu rendimiento",
            "color": "#16A34A",
            "bg_color": "#F0FDF4",
            "icon_bg": "#DCFCE7",
            "icon_type": "calc",
        },
        {
            "id": "mat_ing",
            "name": "Inglés",
            "subtitle": "Gramática, vocabulario y comprensión lectora",
            "tip": "Accede a materiales y actividades para fortalecer tu aprendizaje",
            "color": "#7C3AED",
            "bg_color": "#F5F3FF",
            "icon_bg": "#F3E8FF",
            "icon_type": "en",
        },
        {
            "id": "mat_qui",
            "name": "Química",
            "subtitle": "Reacciones, soluciones y estequiometría",
            "tip": "Consulta apuntes, ejercicios y recursos de la materia",
            "color": "#EA580C",
            "bg_color": "#FFF7ED",
            "icon_bg": "#FFEDD5",
            "icon_type": "lab",
        },
        {
            "id": "mat_fis",
            "name": "Física",
            "subtitle": "Mecánica, ondas y electromagnetismo",
            "tip": "Formula modelos y analiza fenómenos científicos",
            "color": "#2563EB",
            "bg_color": "#EFF6FF",
            "icon_bg": "#DBEAFE",
            "icon_type": "physics",
        },
        {
            "id": "mat_val",
            "name": "Valores",
            "subtitle": "Ética, ciudadanía y compromiso social",
            "tip": "Desarrolla habilidades socioemocionales y proyectos éticos",
            "color": "#D97706",
            "bg_color": "#FFFBEB",
            "icon_bg": "#FEF3C7",
            "icon_type": "ethics",
        },
    ]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id") if self._user else None
        self._search_term = ""
        self._subjects_list_container = ft.Column(spacing=16)

    def _build_subject_icon(self, icon_type: str, color: str, icon_bg: str) -> ft.Control:
        """Construye el contenedor de icono distintivo por asignatura."""
        if icon_type == "en":
            content_ctrl = ft.Text("EN", size=22, weight=ft.FontWeight.BOLD, color=color)
        elif icon_type == "laptop":
            content_ctrl = ft.Icon(ft.Icons.COMPUTER, color=color, size=32)
        elif icon_type == "calc":
            content_ctrl = ft.Icon(ft.Icons.CALCULATE_OUTLINED, color=color, size=32)
        elif icon_type == "lab":
            content_ctrl = ft.Icon(ft.Icons.SCIENCE_OUTLINED, color=color, size=32)
        elif icon_type == "physics":
            content_ctrl = ft.Icon(ft.Icons.SPEED, color=color, size=32)
        else:
            content_ctrl = ft.Icon(ft.Icons.FAVORITE_OUTLINE, color=color, size=32)

        return ft.Container(
            width=80,
            height=72,
            bgcolor=icon_bg,
            border_radius=16,
            alignment=ft.alignment.center,
            content=content_ctrl
        )

    def _open_subject_modal(self, subject_name: str):
        """Abre un modal interactivo con todos los datos específicos de la asignatura."""
        from services.navigation_service import NavigationController
        
        # Obtener notas del usuario para esta asignatura
        notes = NavigationController.cache.get("notes", [])
        if not notes and self._uid:
            try: notes = self._db.obtener_notas(self._uid) or []
            except: notes = []

        subj_notes = [n for n in notes if n.get("asignatura", "").lower() == subject_name.lower()]
        grades = [float(n.get("calificacion", 0)) for n in subj_notes]
        avg = (sum(grades) / len(grades)) if grades else 0.0

        # Obtener asignaciones de esta asignatura
        assignments = NavigationController.cache.get("assignments", [])
        subj_assig = [a for a in assignments if a.get("asignatura", "").lower() == subject_name.lower()]

        # Contenido modal
        notes_rows = []
        if subj_notes:
            for n in subj_notes[:5]:
                notes_rows.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#F8FAFC",
                        border_radius=10,
                        border=ft.border.all(1, "#E2E8F0"),
                        content=ft.Row([
                            ft.Text(f"⭐ {n.get('calificacion', 0)}", weight="bold", color="#7C3AED", size=13),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(n.get("comentarios") or "Sin comentarios", size=11, color="#334155"),
                                ft.Text(str(n.get("fecha", "")), size=9, color="#94A3B8"),
                            ], expand=True)
                        ])
                    )
                )
        else:
            notes_rows.append(ft.Text("No hay calificaciones registradas para esta materia.", size=12, color="#94A3B8"))

        assig_rows = []
        if subj_assig:
            for a in subj_assig[:5]:
                st_col = "#16A34A" if a.get("estado") == "Entregado" else "#D97706"
                assig_rows.append(
                    ft.Container(
                        padding=10,
                        bgcolor="#F8FAFC",
                        border_radius=10,
                        border=ft.border.all(1, "#E2E8F0"),
                        content=ft.Row([
                            ft.Icon(ft.Icons.ASSIGNMENT, color=st_col, size=18),
                            ft.Container(width=10),
                            ft.Column([
                                ft.Text(a.get("titulo", ""), size=12, weight="bold", color="#0F172A"),
                                ft.Text(f"Entrega: {a.get('fecha_entrega', '')} - Estado: {a.get('estado', '')}", size=10, color="#64748B"),
                            ], expand=True)
                        ])
                    )
                )
        else:
            assig_rows.append(ft.Text("No hay asignaciones pendientes para esta materia.", size=12, color="#94A3B8"))

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.BOOKMARK_ROUNDED, color="#7C3AED", size=24),
                ft.Text(f"Materia: {subject_name}", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=520, height=450,
                content=ft.Column([
                    # Resumen KPI
                    ft.Container(
                        padding=14,
                        bgcolor="#F1F5F9",
                        border_radius=12,
                        content=ft.Row([
                            ft.Column([
                                ft.Text("Promedio de Materia", size=11, color="#64748B"),
                                ft.Text(f"{avg:.1f} / 5.0", size=22, weight="bold", color="#7C3AED")
                            ], expand=True),
                            ft.Column([
                                ft.Text("Calificaciones", size=11, color="#64748B"),
                                ft.Text(str(len(subj_notes)), size=22, weight="bold", color="#0F172A")
                            ], expand=True),
                            ft.Column([
                                ft.Text("Tareas", size=11, color="#64748B"),
                                ft.Text(str(len(subj_assig)), size=22, weight="bold", color="#0F172A")
                            ], expand=True),
                        ])
                    ),
                    ft.Container(height=10),
                    ft.Text("Últimas Calificaciones", size=13, weight="bold", color="#0F172A"),
                    ft.Column(notes_rows, spacing=6),
                    ft.Container(height=10),
                    ft.Text("Asignaciones de la Materia", size=13, weight="bold", color="#0F172A"),
                    ft.Column(assig_rows, spacing=6),
                ], spacing=0, scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton(
                    "Ver todas las Tareas",
                    bgcolor="#7C3AED", color="white",
                    on_click=lambda e: [self.page.close(dlg), NavigationController.update_view("Asignaciones")]
                ),
            ]
        )
        self.page.open(dlg)

    def _build_subject_card(self, subj_data: dict) -> ft.Control:
        """Construye una tarjeta horizontal estilo Figma (Imagen 3)."""
        colors = self._get_theme_colors()

        icon_ctrl = self._build_subject_icon(subj_data["icon_type"], subj_data["color"], subj_data["icon_bg"])

        return ft.Container(
            bgcolor=colors["card_bg"],
            border_radius=16,
            border=ft.border.all(1, "#E2E8F0"),
            padding=ft.padding.all(16),
            content=ft.Row([
                # Franja acentuada de color izquierda
                ft.Container(
                    width=6,
                    height=72,
                    border_radius=3,
                    bgcolor=subj_data["color"],
                ),
                ft.Container(width=10),
                # Icono
                icon_ctrl,
                ft.Container(width=16),
                # Columna Central: Nombre y Descripción corta
                ft.Column([
                    ft.Text(subj_data["name"], size=16, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(subj_data["subtitle"], size=11, color=colors["text_muted"]),
                ], spacing=4, expand=True),
                # Separador vertical fino
                ft.Container(width=1, height=48, bgcolor=colors["divider"]),
                ft.Container(width=16),
                # Columna Derecha: Consejo/Tip y Botón Ver Materia
                ft.Container(
                    width=280,
                    content=ft.Row([
                        ft.Container(
                            width=10, height=10, border_radius=5, bgcolor=subj_data["icon_bg"]
                        ),
                        ft.Container(width=6),
                        ft.Text(subj_data["tip"], size=10.5, color=colors["text_muted"], expand=True),
                    ])
                ),
                ft.Container(width=12),
                ft.TextButton(
                    content=ft.Row([
                        ft.Text("Ver materia", size=12, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=colors["text"])
                    ], spacing=4),
                    on_click=lambda e, name=subj_data["name"]: self._open_subject_modal(name)
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _render_subjects_list(self):
        """Renderiza la lista filtrada de asignaturas."""
        term = self._search_term.strip().lower()
        cards = []
        for subj in self.SUBJECT_DETAILS:
            if term in subj["name"].lower() or term in subj["subtitle"].lower():
                cards.append(self._build_subject_card(subj))

        if not cards:
            self._subjects_list_container.controls = [
                ft.Container(
                    padding=32,
                    alignment=ft.alignment.center,
                    content=ft.Text("No se encontraron materias con ese nombre.", color="#94A3B8", size=13)
                )
            ]
        else:
            self._subjects_list_container.controls = cards

    def _on_search_change(self, e):
        self._search_term = e.control.value
        self._render_subjects_list()
        try: self._subjects_list_container.update()
        except: pass

    def build(self) -> ft.Control:
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("sidebar_asignaturas"))

        # Campo de búsqueda y filtro (Figma Header Bar)
        search_field = ft.TextField(
            hint_text="Buscar materia...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            bgcolor=colors["surface"],
            border_color="#E2E8F0",
            content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
            on_change=self._on_search_change,
            expand=True,
        )

        filter_dropdown = ft.Container(
            padding=ft.padding.symmetric(horizontal=24, vertical=10),
            border_radius=10,
            border=ft.border.all(1, "#CBD5E1"),
            bgcolor=colors["surface"],
            content=ft.Text("Todos", size=12, weight="bold", color=colors["text"])
        )

        top_filter_bar = ft.Container(
            padding=16,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=16,
            content=ft.Row([
                search_field,
                ft.Container(width=16),
                filter_dropdown
            ])
        )

        self._render_subjects_list()

        main_content = ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor=colors["background"],
            content=ft.Column([
                # Cabecera
                ft.Column([
                    ft.Text("Mis materias", size=26, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text("Organiza y accede a todas tus asignaturas en un solo lugar", size=13, color=colors["text_secondary"]),
                ], spacing=2),
                ft.Container(height=16),
                top_filter_bar,
                ft.Container(height=16),
                self._subjects_list_container
            ], spacing=0, scroll=get_scroll_mode(self.page))
        )

        return ft.Column([
            navbar,
            main_content
        ], expand=True, spacing=0)
