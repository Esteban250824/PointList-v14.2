"""
pages/calendar_page.py
Página de calendario vFinal_Pro_v9: Auto-refresco instantáneo, caché agresivo, diseño Figma exacto.
"""

import flet as ft
import threading
import time
from datetime import datetime, date, timedelta
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode
from utils.helpers import MONTH_NAMES_ES


class CalendarPage(BasePage):
    """Página de calendario mensual con diseño premium, edición y auto-refresco."""

    EVENT_TYPES = ["General", "Examen", "Entrega", "Reunión", "Feriado", "Otro"]
    TYPE_COLORS = {
        "General":  "#4F46E5",  # Azul/Indigo
        "Examen":   "#EF4444",  # Rojo
        "Entrega":  "#F59E0B",  # Amarillo/Naranja
        "Reunión":  "#8B5CF6",  # Morado
        "Feriado":  "#10B981",  # Verde
        "Otro":     "#6B7280",  # Gris
    }

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db   = db
        self._user = NavigationController.get_current_user()
        self._uid  = self._user.get("id")

        today = date.today()
        self._current_year  = today.year
        self._current_month = today.month
        self._selected_date = today
        self._events: list  = []
        self._calendar_ref  = ft.Ref[ft.Column]()
        self._events_ref    = ft.Ref[ft.Column]()
        
        # Sincronización en background
        self._sync_thread = None
        self._stop_sync = False

    def _load_events(self):
        """Carga eventos desde caché primero, luego de BD."""
        from services.navigation_service import NavigationController
        cached_events = NavigationController.cache.get("events", [])
        if cached_events:
            self._events = cached_events
        else:
            self._events = self._db.obtener_eventos(self._uid) if self._uid else []
            NavigationController.cache["events"] = self._events

    def _sync_events_background(self):
        """Sincroniza eventos en background sin bloquear la UI."""
        time.sleep(3)
        while not self._stop_sync:
            try:
                from services.navigation_service import NavigationController
                new_events = self._db.obtener_eventos(self._uid) if self._uid else []
                if new_events != self._events:
                    self._events = new_events
                    NavigationController.cache["events"] = new_events
                    self._refresh_ui(reload_data=False)
            except: pass
            time.sleep(10)

    def _events_for_date(self, d: date) -> list:
        result = []
        for ev in self._events:
            try:
                fecha_val = ev.get("fecha_inicio", "")
                if not fecha_val:
                    continue
                
                if isinstance(fecha_val, str):
                    if "T" in fecha_val:
                        ev_date = datetime.fromisoformat(fecha_val).date()
                    else:
                        ev_date = date.fromisoformat(fecha_val)
                elif isinstance(fecha_val, (datetime, date)):
                    ev_date = fecha_val.date() if isinstance(fecha_val, datetime) else fecha_val
                else:
                    continue

                if ev_date == d:
                    result.append(ev)
            except Exception:
                continue
        return result

    def _prev_year(self, e):
        self._current_year -= 1
        self._refresh_ui()

    def _next_year(self, e):
        self._current_year += 1
        self._refresh_ui()

    def _prev_month(self, e):
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        self._refresh_ui()

    def _next_month(self, e):
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        self._refresh_ui()

    def _select_date(self, d: date):
        self._selected_date = d
        self._refresh_ui(reload_data=False)

    def _build_calendar(self) -> ft.Column:
        """Construye el calendario mensual según el diseño Figma exacto."""
        import calendar
        colors = self._get_theme_colors()

        year  = self._current_year
        month = self._current_month
        today = date.today()

        # Botón Año Anterior (Azul)
        prev_year_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHEVRON_LEFT, color="#1565C0", size=30),
                ft.Text(f"{year - 1}", color="#1565C0", size=30, weight=ft.FontWeight.BOLD),
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            border=ft.border.all(1, "#E5E7EB"),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=18, vertical=10),
            on_click=self._prev_year,
            bgcolor=colors["surface"]
        )

        # Pill central de Mes (Gris)
        month_pill = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=30, on_click=self._prev_month, icon_color=ft.Colors.BLACK),
                ft.Text(MONTH_NAMES_ES[month - 1], size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=26, on_click=self._next_month, icon_color=ft.Colors.BLACK),
            ], spacing=16, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor="#E0E0E0",
            border_radius=30,
            padding=ft.padding.symmetric(horizontal=24, vertical=10),
        )

        # Botón Año Siguiente (Verde)
        next_year_btn = ft.Container(
            content=ft.Row([
                ft.Text(f"{year + 1}", color="#10B981", size=30, weight=ft.FontWeight.BOLD),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#10B981", size=20),
            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
            border=ft.border.all(1, "#E5E7EB"),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=18, vertical=10),
            on_click=self._next_year,
            bgcolor=colors["surface"]
        )

        header = ft.Row([
            prev_year_btn,
            ft.Container(expand=True),
            month_pill,
            ft.Container(expand=True),
            next_year_btn,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        days_header = ft.Row(
            controls=[
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.BLACK,
                    border_radius=18,
                    padding=ft.padding.symmetric(vertical=16),
                    alignment=ft.alignment.center,
                    content=ft.Text(d, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
                )
                for d in day_names
            ],
            spacing=12,
        )

        cal = calendar.monthcalendar(year, month)
        rows = []
        for week in cal:
            cells = []
            for day_num in week:
                if day_num == 0:
                    cells.append(ft.Container(expand=True, height=90, bgcolor=colors["surface"]))
                    continue

                d = date(year, month, day_num)
                events_today = self._events_for_date(d)
                is_today     = (d == today)
                is_selected  = (d == self._selected_date)

                dots = []
                for ev in events_today[:3]:
                    dots.append(
                        ft.Container(
                            width=8, height=8, border_radius=4,
                            bgcolor=self.TYPE_COLORS.get(ev.get("tipo_evento", "General"), "#4F46E5")
                        )
                    )
                dots_row = ft.Row(controls=dots, spacing=6, alignment=ft.MainAxisAlignment.END)

                cell_bg = "#FFFFFF"
                if is_selected:
                    cell_bg = "#EEF2FF"

                cell_border = ft.border.all(1, "#E5E7EB")
                if is_selected:
                    cell_border = ft.border.all(2, self.primary_color)

                cell_content = ft.Stack([
                    ft.Container(
                        content=ft.Text(
                            str(day_num),
                            size=16,
                            # La celda siempre tiene fondo claro (blanco/#EEF2FF)
                            # → texto siempre oscuro para legibilidad en ambos temas
                            color=self.primary_color if is_today else "#1E293B",
                            weight=ft.FontWeight.BOLD if is_today or is_selected else ft.FontWeight.W_600
                        ),
                        left=16,
                        top=16
                    ),
                    ft.Container(
                        content=dots_row,
                        right=16,
                        top=16
                    )
                ], width=float('inf'), height=90)

                cell = ft.Container(
                    expand=True,
                    height=90,
                    border_radius=20,
                    bgcolor=cell_bg,
                    border=cell_border,
                    shadow=ft.BoxShadow(
                        blur_radius=14,
                        spread_radius=-7,
                        color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                        offset=ft.Offset(0, 8)
                    ),
                    on_click=lambda e, dd=d: self._select_date(dd),
                    content=cell_content,
                )
                cells.append(cell)
            rows.append(ft.Row(controls=cells, expand=True, spacing=16))

        return ft.Column(controls=[
            header,
            ft.Container(height=20),
            days_header,
            ft.Container(height=16)
        ] + rows, spacing=16)

    def _get_upcoming_two_weeks_events(self) -> list:
        """Obtiene los eventos de la semana actual y la entrante (14 días desde el lunes actual)."""
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_next_week = start_week + timedelta(days=13)

        upcoming = []
        for ev in (self._events or []):
            try:
                raw_val = ev.get("fecha_inicio") or ev.get("fecha")
                if not raw_val: continue

                if isinstance(raw_val, str):
                    clean_d = raw_val.split("T")[0].strip()
                    ev_date = date.fromisoformat(clean_d)
                elif isinstance(raw_val, datetime):
                    ev_date = raw_val.date()
                elif isinstance(raw_val, date):
                    ev_date = raw_val
                else:
                    continue

                if start_week <= ev_date <= end_next_week:
                    upcoming.append({**ev, "_parsed_date": ev_date})
            except Exception:
                continue

        upcoming.sort(key=lambda x: x["_parsed_date"])
        return upcoming

    def _build_events_list(self) -> ft.Container:
        """Construye la lista de observaciones del día seleccionado y los Próximos Eventos (semana actual y entrante)."""
        colors = self._get_theme_colors()
        events = self._events_for_date(self._selected_date)
        
        # Formato de la fecha en español
        meses = MONTH_NAMES_ES
        date_str = f"{self._selected_date.day} de {meses[self._selected_date.month - 1].lower()}, {self._selected_date.year}"

        # Cabecera de la sección de observaciones
        header = ft.Row([
            ft.Row([
                ft.Text(date_str, size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Container(
                    content=ft.Text(f"{len(events)}", color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
                    bgcolor=self.primary_color,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2)
                ),
                ft.Text("Observaciones", size=13, color=colors["text_secondary"], weight=ft.FontWeight.W_500),
            ], spacing=8, expand=True),
            ft.ElevatedButton(
                text="Nuevo Evento",
                icon=ft.Icons.ADD,
                bgcolor=self.primary_color,
                color=ft.Colors.WHITE,
                height=36,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6)
                ),
                on_click=self._open_add_dialog
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # Generar las tarjetas de eventos o mostrar vacío
        if not events:
            items = [
                ft.Container(
                    padding=ft.padding.all(20), 
                    content=ft.Column([
                        ft.Icon(ft.Icons.EVENT_AVAILABLE, size=36, color=colors["text_secondary"]),
                        ft.Text("No hay observaciones para este día", color=colors["text_secondary"], size=13)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                )
            ]
        else:
            items = []
            for ev in events:
                tipo = ev.get("tipo_evento", "General")
                color = self.TYPE_COLORS.get(tipo, "#6B7280")
                
                item = ft.Container(
                    padding=ft.padding.all(14), 
                    bgcolor=colors["surface"], 
                    border_radius=12,
                    border=ft.border.all(1, "#E5E7EB"),
                    content=ft.Row([
                        ft.Column([
                            ft.Text(ev.get("titulo", ""), size=15, weight=ft.FontWeight.BOLD, color=colors["text"]),
                            ft.Container(height=2),
                            ft.Text(ev.get("descripcion", ""), size=12, color=colors["text_secondary"]),
                        ], spacing=2, expand=True),
                        ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            icon_color=colors["text_secondary"],
                            items=[
                                ft.PopupMenuItem(text="Editar", icon=ft.Icons.EDIT, on_click=lambda e, curr_ev=ev: self._open_edit_dialog(curr_ev)),
                                ft.PopupMenuItem(text="Eliminar", icon=ft.Icons.DELETE_OUTLINE, on_click=lambda e, eid=ev.get("id"): self._delete_event_from_menu(eid)),
                            ]
                        )
                    ]),
                )
                items.append(item)

        # Sección: Próximos Eventos (Semana actual y entrante)
        upcoming_two_weeks = self._get_upcoming_two_weeks_events()
        upcoming_items = []
        if not upcoming_two_weeks:
            upcoming_items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=16, horizontal=12),
                    alignment=ft.alignment.center,
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=18, color="#10B981"),
                        ft.Text("bien, no tienes eventos por ahora", size=13, color=colors["text_secondary"], weight=ft.FontWeight.W_500),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER)
                )
            )
        else:
            for ev in upcoming_two_weeks[:5]:
                ev_d = ev["_parsed_date"]
                tipo = ev.get("tipo_evento", "General")
                badge_col = self.TYPE_COLORS.get(tipo, "#4F46E5")
                d_format = f"{ev_d.day} de {meses[ev_d.month - 1].lower()}"
                
                upcoming_items.append(
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=12, vertical=10),
                        bgcolor="#F8FAFC",
                        border_radius=10,
                        border=ft.border.all(1, "#E2E8F0"),
                        content=ft.Row([
                            ft.Container(width=4, height=32, border_radius=2, bgcolor=badge_col),
                            ft.Container(width=8),
                            ft.Column([
                                ft.Text(ev.get("titulo", "Evento"), size=13, weight=ft.FontWeight.BOLD, color=colors["text"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(d_format, size=11, color=colors["text_secondary"]),
                            ], spacing=1, expand=True),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                bgcolor=ft.Colors.with_opacity(0.12, badge_col),
                                border_radius=6,
                                content=ft.Text(tipo, size=10, weight="bold", color=badge_col)
                            )
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                )

        upcoming_box = ft.Column([
            ft.Divider(height=24, color="#E2E8F0"),
            ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, color=self.primary_color, size=18),
                ft.Text("Próximos eventos (Semana actual y entrante)", size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ], spacing=6),
            ft.Container(height=6),
            ft.Column(controls=upcoming_items, spacing=8)
        ], spacing=0)

        # Caja contenedora principal
        return ft.Container(
            padding=ft.padding.all(20),
            border=ft.border.all(1, "#E5E7EB"),
            border_radius=16,
            bgcolor=colors["surface"],
            content=ft.Column(controls=[header, ft.Container(height=10)] + items + [upcoming_box], spacing=8, scroll=get_scroll_mode(self.page))
        )

    def _delete_event_from_menu(self, eid):
        """Elimina un evento de forma optimista."""
        from services.navigation_service import NavigationController
        self._events = [e for e in self._events if e.get("id") != eid]
        NavigationController.cache["events"] = self._events
        self._refresh_ui(reload_data=False)
        self._show_success("Evento eliminado.")
        
        threading.Thread(
            target=lambda: self._db.eliminar_evento(eid, self._uid),
            daemon=True
        ).start()

    def _refresh_ui(self, reload_data=True):
        if reload_data:
            self._load_events()
        if self._calendar_ref.current:
            self._calendar_ref.current.content = self._build_calendar()
        if self._events_ref.current:
            self._events_ref.current.content = self._build_events_list()
        try: self.page.update()
        except: pass

    def _open_add_dialog(self, e):
        self._open_event_dialog()

    def _open_event_dialog(self, ev: dict = None):
        is_edit = ev is not None
        title_field = ft.TextField(label="Título", value=ev.get("titulo", "") if is_edit else "", expand=True, border_radius=10)
        desc_field = ft.TextField(label="Descripción", value=ev.get("descripcion", "") if is_edit else "", multiline=True, min_lines=2, expand=True, border_radius=10)
        tipo_dd = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option(t) for t in self.EVENT_TYPES], value=ev.get("tipo_evento", "General") if is_edit else "General", expand=True, border_radius=10)
        fecha_field = ft.TextField(label="Fecha (YYYY-MM-DD)", value=str(ev.get("fecha_inicio")) if is_edit else str(self._selected_date), expand=True, border_radius=10)
        error_text = ft.Text("", color=ft.Colors.RED_600, size=12)

        def _save(e):
            if not title_field.value:
                error_text.value = "El título es requerido."
                self.page.update()
                return
            
            if is_edit:
                from services.navigation_service import NavigationController
                self._events = [e for e in self._events if e.get("id") != ev["id"]]
                new_event = {
                    "id": ev["id"],
                    "titulo": title_field.value,
                    "descripcion": desc_field.value,
                    "tipo_evento": tipo_dd.value,
                    "fecha_inicio": fecha_field.value,
                    "fecha_fin": fecha_field.value,
                }
                self._events.append(new_event)
                NavigationController.cache["events"] = self._events
                
                threading.Thread(
                    target=lambda: (
                        self._db.eliminar_evento(ev["id"], self._uid),
                        self._db.guardar_evento(self._uid, title_field.value, desc_field.value, tipo_dd.value, fecha_field.value, fecha_field.value)
                    ),
                    daemon=True
                ).start()
            else:
                from services.navigation_service import NavigationController
                new_event = {
                    "id": int(time.time() * 1000),
                    "titulo": title_field.value,
                    "descripcion": desc_field.value,
                    "tipo_evento": tipo_dd.value,
                    "fecha_inicio": fecha_field.value,
                    "fecha_fin": fecha_field.value,
                }
                self._events.append(new_event)
                NavigationController.cache["events"] = self._events
                
                threading.Thread(
                    target=lambda: self._db.guardar_evento(self._uid, title_field.value, desc_field.value, tipo_dd.value, fecha_field.value, fecha_field.value),
                    daemon=True
                ).start()
            
            self._refresh_ui(reload_data=False)
            dlg.open = False
            self.page.update()
            self._show_success("Evento guardado.")

        dlg = ft.AlertDialog(
            title=ft.Text("Editar Evento" if is_edit else "Nuevo Evento", weight=ft.FontWeight.BOLD),
            content=ft.Container(width=400, content=ft.Column([title_field, desc_field, tipo_dd, fecha_field, error_text], spacing=15, tight=True)),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton("Guardar", bgcolor=self.primary_color, color=ft.Colors.WHITE, on_click=_save),
            ],
        )
        self.page.open(dlg)

    def build(self) -> ft.Control:
        from services.navigation_service import NavigationController

        self._load_events()
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("nav_calendar"))
        is_mobile = self.page.width < 800
        
        if not self._sync_thread or not self._sync_thread.is_alive():
            self._stop_sync = False
            self._sync_thread = threading.Thread(target=self._sync_events_background, daemon=True)
            self._sync_thread.start()
        
        quick_nav = ft.Row(
            [
                ft.ElevatedButton(
                    "Inicio",
                    on_click=lambda e: NavigationController.update_view("Inicio"),
                    bgcolor=self.primary_color,
                    color=ft.Colors.WHITE,
                ),
                ft.ElevatedButton(
                    "Notas",
                    on_click=lambda e: NavigationController.update_view("Notas"),
                    bgcolor=colors["surface"],
                    color=colors["text"],
                ),
                ft.ElevatedButton(
                    "Mensajería",
                    on_click=lambda e: NavigationController.update_view("Mensajeria"),
                    bgcolor=colors["surface"],
                    color=colors["text"],
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        )

        calendar_container = ft.Container(
            ref=self._calendar_ref,
            content=self._build_calendar(),
            padding=ft.padding.all(12),
            bgcolor=colors["surface"],
            border_radius=16,
            border=ft.border.all(1, colors["divider"]),
            expand=True,
        )

        events_container = ft.Container(
            ref=self._events_ref,
            content=self._build_events_list(),
            expand=True,
        )

        # Si es móvil se muestran uno sobre otro; en escritorio se ponen lado a lado en un Row para evitar scroll
        if is_mobile:
            calendar_layout = ft.Column([
                calendar_container,
                ft.Container(height=10),
                events_container
            ], scroll=None, expand=True)
        else:
            calendar_layout = ft.Row([
                ft.Container(content=calendar_container, expand=2),
                ft.Container(content=events_container, expand=1),
            ], spacing=20, expand=True)

        content = ft.Column([
            quick_nav,
            ft.Container(height=12),
            calendar_layout
        ], expand=True, spacing=0)

        return ft.Column(controls=[navbar, ft.Container(expand=True, padding=ft.padding.all(16 if is_mobile else 32), content=content)], expand=True, spacing=0)
