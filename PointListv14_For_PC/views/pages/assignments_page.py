"""
pages/assignments_page.py - v20.5
Página de Asignaciones y Mis Tareas (Diseño Exacto Figma / Imagen 1):
- Tarjetas KPI (Tareas totales, Pendientes, Entregadas, Calificadas)
- Barra con buscador 'Buscar tarea por titulo o asignatura...' y filtros [Todas] [Pendientes] [Entregadas] [Calificadas]
- Tarjetas con franja lateral de color, insignia de estado (Entregado / Pendiente), etiqueta de asignatura y botones de acción
- Banner inferior '¡Vas al día! Sigue así'
"""

import flet as ft
import threading
import time
import os
import copy
from datetime import date, datetime, timedelta
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class AssignmentsPage(BasePage):
    """Página de Mis Tareas y Asignaciones v20.5."""

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
            "fecha_entrega": "2026-08-07",
            "hora_entrega": "23:59",
            "instrucciones": "Resolver los ejercicios de la página 45 a la 50 del libro de la guía. Presenta el procedimiento completo de forma clara.",
            "puntuacion_maxima": 5.0,
            "estado": "Entregado",
            "entrega_texto": "Taller resuelto enviado.",
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
            "fecha_entrega": "2026-08-11",
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
            "titulo": "Informe de laboratorio: Reacciones Químicas",
            "asignatura": "Química",
            "profesor": "Prof. Roberto Gómez",
            "estudiante_id": "todos",
            "estudiante_nombre": "Todos los estudiantes",
            "fecha_entrega": "2026-08-03",
            "hora_entrega": "12:00",
            "instrucciones": "Redacta el informe correspondiente a la práctica de laboratorio #4 incluyendo la tabla de observaciones y conclusiones.",
            "puntuacion_maxima": 5.0,
            "estado": "Entregado",
            "entrega_texto": "Informe adjunto.",
            "archivo_adjunto": "",
            "calificacion": 4.8,
            "retroalimentacion": "Excelente trabajo.",
        }
    ]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        self._rol = self._user.get("rol", "estudiante")
        self._is_profesor = self._rol == "profesor"
        self._assignments = NavigationController.cache.get("assignments", [])
        if not self._assignments:
            self._assignments = copy.deepcopy(self.DEFAULT_ASSIGNMENTS)
            NavigationController.cache["assignments"] = self._assignments
        self._filter_status = getattr(self, "_filter_status", "Todas")
        self._filter_subject = getattr(self, "_filter_subject", "Todas")
        self._search_term = getattr(self, "_search_term", "")
        self._main_column = ft.Column(spacing=14, scroll=get_scroll_mode("AUTO"), expand=True)

    def _refresh_ui(self):
        from services.navigation_service import NavigationController
        NavigationController.update_view("Asignaciones", force_rebuild=True)

    def _open_submit_dialog(self, assignment: dict):
        text_input = ft.TextField(
            label="Comentarios / Texto de Entrega",
            hint_text="Escribe aquí los detalles de tu solución...",
            multiline=True, min_lines=3, border_radius=10
        )
        def _do_submit(e):
            assignment["estado"] = "Entregado"
            assignment["entrega_texto"] = text_input.value.strip()
            from services.navigation_service import NavigationController
            NavigationController.cache["assignments"] = copy.deepcopy(self._assignments)
            self.page.close(dlg)
            self._show_success("¡Tarea entregada exitosamente!")
            self._refresh_ui()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Entregar: {assignment.get('titulo')}", size=16, weight="bold"),
            content=text_input,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Confirmar Entrega", bgcolor="#22C55E", color="white", on_click=_do_submit)
            ]
        )
        self.page.open(dlg)

    def _open_view_submission_dialog(self, assignment: dict):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Detalles de Entrega: {assignment.get('titulo')}", size=16, weight="bold"),
            content=ft.Column([
                ft.Text(f"Asignatura: {assignment.get('asignatura')}", weight="bold"),
                ft.Text(f"Profesor: {assignment.get('profesor')}"),
                ft.Text(f"Estado: {assignment.get('estado')}", color="#2563EB" if assignment.get('estado') == "Entregado" else "#16A34A"),
                ft.Divider(),
                ft.Text("Instrucciones:", weight="bold"),
                ft.Text(assignment.get("instrucciones", "")),
                ft.Divider(),
                ft.Text("Tu respuesta:", weight="bold"),
                ft.Text(assignment.get("entrega_texto") or "Sin texto adicional.")
            ], spacing=6, tight=True),
            actions=[
                ft.ElevatedButton("Cerrar", bgcolor="#0284C7", color="white", on_click=lambda e: self.page.close(dlg))
            ]
        )
        self.page.open(dlg)

    def build(self) -> ft.Control:
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("messaging_title") if False else "Mis Tareas")

        # ─── HEADER ──────────────────────────────────────────────────────────
        header = ft.Column([
            ft.Text("Mis Tareas", size=28, weight="bold", color=colors["text"]),
            ft.Text("Consulta y entrega las tareas asignadas por tu profesores.", size=13, color=colors["text_secondary"]),
        ], spacing=2)

        # ─── KPI CARDS (TOTAL, PENDIENTES, ENTREGADAS, CALIFICADAS) ───────────
        total_count = len(self._assignments)
        pending_count = sum(1 for a in self._assignments if a.get("estado") == "Pendiente")
        done_count = sum(1 for a in self._assignments if a.get("estado") == "Entregado")
        graded_count = sum(1 for a in self._assignments if a.get("estado") == "Calificado")

        def kpi_card(title, count, icon, bg_icon, icon_col):
            return ft.Container(
                bgcolor=colors["surface"],
                border_radius=16,
                padding=16,
                expand=True,
                border=ft.border.all(1, "#E2E8F0"),
                content=ft.Row([
                    ft.Container(
                        width=44, height=44, border_radius=12, bgcolor=bg_icon,
                        alignment=ft.alignment.center,
                        content=ft.Icon(icon, color=icon_col, size=22)
                    ),
                    ft.Column([
                        ft.Text(str(count), size=24, weight="bold", color=colors["text"]),
                        ft.Text(title, size=12, color=colors["text_secondary"])
                    ], spacing=0)
                ], spacing=12)
            )

        kpi_row = ft.Row([
            kpi_card("Tareas totales", total_count, ft.Icons.ASSIGNMENT_TURNED_IN_OUTLINED, "#EEF2FF", "#4F46E5"),
            kpi_card("Pendientes", pending_count, ft.Icons.ACCESS_TIME, "#FEF3C7", "#D97706"),
            kpi_card("Entregadas", done_count, ft.Icons.INBOX, "#DBEAFE", "#2563EB"),
            kpi_card("Calificadas", graded_count, ft.Icons.GRADE, "#DCFCE7", "#16A34A"),
        ], spacing=12)

        # ─── BARRA DE BÚSQUEDA, ASIGNATURAS Y FILTROS ─────────────────────────
        search_field = ft.TextField(
            hint_text="Buscar tarea por titulo o asignatura...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            bgcolor=colors["surface"],
            expand=True,
            height=40,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
            on_change=lambda e: setattr(self, "_search_term", e.control.value.lower().strip())
        )

        subject_options = [ft.dropdown.Option("Todas", text="📚 Todas las Materias")] + [
            ft.dropdown.Option(s, text=f"📘 {s}") for s in self.SUBJECTS
        ]

        def _on_subject_change(e):
            self._filter_subject = e.control.value
            self._refresh_ui()

        subject_dropdown = ft.Dropdown(
            options=subject_options,
            value=self._filter_subject,
            width=210,
            height=40,
            border_radius=10,
            bgcolor=colors["surface"],
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
            on_change=_on_subject_change
        )

        filter_buttons = []
        for status in ["Todas", "Pendientes", "Entregadas", "Calificadas"]:
            is_sel = (self._filter_status == status) or (status == "Todas" and self._filter_status == "Todas")
            
            def _filter_click(st=status):
                self._filter_status = st
                self._refresh_ui()

            filter_buttons.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor="#334155" if is_sel else colors["surface"],
                    border_radius=8,
                    border=ft.border.all(1, "#334155" if is_sel else "#CBD5E1"),
                    ink=True,
                    on_click=lambda e, st=status: _filter_click(st),
                    content=ft.Text(status, size=12, weight="bold" if is_sel else "normal", color="white" if is_sel else colors["text"])
                )
            )

        filter_row = ft.Row([
            search_field,
            subject_dropdown,
            ft.Row(filter_buttons, spacing=6)
        ], spacing=12)

        # ─── LISTA DE TARJETAS DE ASIGNACIÓN ─────────────────────────────────
        filtered = []
        for a in self._assignments:
            st = a.get("estado", "Pendiente")
            subj = a.get("asignatura", "")
            if self._filter_status == "Pendientes" and st != "Pendiente": continue
            if self._filter_status == "Entregadas" and st != "Entregado": continue
            if self._filter_status == "Calificadas" and st != "Calificado": continue
            if self._filter_subject != "Todas" and subj != self._filter_subject: continue
            if self._search_term and self._search_term not in a.get("titulo", "").lower() and self._search_term not in subj.lower():
                continue
            filtered.append(a)

        cards_col = ft.Column(spacing=12)

        for asig in filtered:
            st = asig.get("estado", "Pendiente")
            is_entregado = st in ("Entregado", "Calificado")
            
            stripe_color = "#3B82F6" if is_entregado else "#F97316"
            badge_bg = "#DBEAFE" if is_entregado else "#FEF3C7"
            badge_fg = "#2563EB" if is_entregado else "#D97706"
            badge_text = "✓ Entregado" if is_entregado else "⏰ Pendiente"

            btn_action = ft.OutlinedButton(
                "👁️ Ver entrega",
                style=ft.ButtonStyle(color="#0F172A", shape=ft.RoundedRectangleBorder(radius=8)),
                height=36,
                on_click=lambda e, curr=asig: self._open_view_submission_dialog(curr)
            ) if is_entregado else ft.ElevatedButton(
                "↑ Entregar tarea",
                bgcolor="#22C55E",
                color="white",
                height=36,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e, curr=asig: self._open_submit_dialog(curr)
            )

            card_item = ft.Container(
                bgcolor=colors["surface"],
                border_radius=14,
                border=ft.border.all(1, "#E2E8F0"),
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row([
                    # Franja lateral izquierda de color
                    ft.Container(width=6, bgcolor=stripe_color, expand=False),
                    ft.Container(
                        padding=16,
                        expand=True,
                        content=ft.Row([
                            # Badge de estado
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                bgcolor=badge_bg,
                                border_radius=10,
                                content=ft.Text(badge_text, size=12, weight="bold", color=badge_fg)
                            ),
                            # Título, descripción y detalles
                            ft.Column([
                                ft.Text(asig.get("titulo", ""), size=15, weight="bold", color=colors["text"]),
                                ft.Text(asig.get("instrucciones", ""), size=12, color=colors["text_secondary"], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Row([
                                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=13, color="#64748B"),
                                    ft.Text(f"Entrega: {asig.get('fecha_entrega')} ({asig.get('hora_entrega')})", size=11, color="#64748B"),
                                    ft.Text(" • ", color="#94A3B8"),
                                    ft.Icon(ft.Icons.PERSON_OUTLINE, size=13, color="#64748B"),
                                    ft.Text(f"Profesor: {asig.get('profesor')}", size=11, color="#64748B"),
                                ], spacing=4)
                            ], spacing=4, expand=True),
                            # Asignatura badge y botón de acción
                            ft.Column([
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                    bgcolor="#F1F5F9",
                                    border_radius=8,
                                    alignment=ft.alignment.center,
                                    content=ft.Text(asig.get("asignatura", ""), size=11, color="#475569", weight="bold")
                                ),
                                btn_action
                            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.END, spacing=8)
                        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ], spacing=0)
            )
            cards_col.controls.append(card_item)

        # ─── BANNER INFERIOR "¡VAS AL DÍA!" ─────────────────────────────────
        bottom_banner = ft.Container(
            padding=12,
            bgcolor=colors["surface"],
            border_radius=20,
            border=ft.border.all(1, "#E2E8F0"),
            alignment=ft.alignment.center,
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#22C55E", size=24),
                ft.Column([
                    ft.Text("¡Vas al día! Sigue así", size=13, weight="bold", color=colors["text"]),
                    ft.Text("No tienes tareas pendientes para hoy.", size=11, color=colors["text_secondary"])
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        )

        content = ft.Column([
            navbar,
            ft.Container(height=14),
            header,
            ft.Container(height=16),
            kpi_row,
            ft.Container(height=16),
            filter_row,
            ft.Container(height=16),
            cards_col,
            ft.Container(height=24),
            bottom_banner
        ], scroll=get_scroll_mode("AUTO"), expand=True, spacing=0)

        return ft.Container(padding=24, bgcolor=colors["background"], content=content, expand=True)
