"""
services/notification_service.py
PointList v0.14.27
Servicio centralizado de notificaciones locales e in-app para alertas de tareas,
nuevas calificaciones asignadas por profesores y mensajes de chat.
"""

import flet as ft
from datetime import datetime

class NotificationService:
    """Manejador de notificaciones locales e in-app."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance.notifications_history = []
        return cls._instance

    def notify_in_app(self, page: ft.Page, title: str, message: str, icon=ft.Icons.NOTIFICATIONS, color="#10B981"):
        """Muestra una notificación flotante (SnackBar/Toast) dentro de la aplicación."""
        if not page:
            return

        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(icon, color="white", size=20),
                ft.Column([
                    ft.Text(title, weight="bold", color="white", size=13),
                    ft.Text(message, color="white", size=11),
                ], spacing=0, expand=True)
            ], spacing=10),
            bgcolor=color,
            duration=4000,
            show_close_icon=True,
        )
        page.open(snack)

        self.notifications_history.append({
            "title": title,
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

notification_service = NotificationService()
