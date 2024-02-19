# TODO: check scroll page
import flet as ft
import os
from supabase import create_client
from dotenv import load_dotenv
import time
import requests

load_dotenv()
supabaseUrl = "https://crswolnvchmpqdjqldop.supabase.co"
supabaseKey = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url=supabaseUrl, supabase_key=supabaseKey)

toggle_style_sheet: dict = {"icon": ft.icons.DARK_MODE_ROUNDED, "icon_size": 18}
_dark: str = ft.colors.with_opacity(0.5, "white")
_light: str = ft.colors.with_opacity(0.5, "black")


class Settings(ft.SafeArea):
    def __init__(self, page: ft.page, visible):
        super().__init__(visible)
        self.page = page
        self.title: ft.Text = ft.Text("Configurações", size=20, weight=ft.FontWeight.W_800)
        self.toggle: ft.IconButton = ft.IconButton(
            **toggle_style_sheet, on_click=lambda e: self.switch(e)
        )

        self.bio = ft.Text("App desenvolvido por Wenzo Rithelly, caso aconteça algum erro, clique no botão abaixo", size=12)
        self.call_me: ft.ElevatedButton = ft.ElevatedButton(
            text="Call Support",
            icon=ft.icons.SEND_ROUNDED,
            bgcolor=ft.colors.with_opacity(0.5, "white"),
            color=ft.colors.GREY_900,
            height=50,
            on_click=self.send_message

        )
        self.main: ft.Column = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[self.title, self.toggle]
                ),
                ft.Divider(height=5),
                ft.Divider(height=10, color="transparent"),
                ft.Row(controls=[self.bio], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=10, color="transparent"),
                ft.Row(controls=[self.call_me], alignment=ft.MainAxisAlignment.CENTER)
            ], scroll=ft.ScrollMode.HIDDEN
        )

        self.content = self.main

    def switch(self, e) -> None:
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.toggle.icon = ft.icons.LIGHT_MODE_ROUNDED
            self.page.navigation_bar.bgcolor = ft.colors.GREY_400
            self.page.navigation_bar.active_color = ft.colors.GREY_800
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.toggle.icon = ft.icons.DARK_MODE_ROUNDED
            self.page.navigation_bar.bgcolor = ft.colors.GREY_900
            self.page.navigation_bar.active_color = ft.colors.WHITE70

        self.page.update()

    def send_message(self, e):
        self.call_me.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.WHITE)
        self.call_me.icon = None
        self.page.update()

        time.sleep(0.1)

        headers = {
            "Authorization": "Bearer " + os.environ.get("WAAPI_TOKEN"),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "chatId": f"556296163339@c.us",
            "message": f"Suporte necessário: Loja do Nova"
        }
        endpoint = 'https://waapi.app/api/v1/instances/5384/client/action/send-message'
        response = requests.post(endpoint, json=payload, headers=headers)

        self.call_me.text = "Call Support"
        self.call_me.icon = ft.icons.SEND_ROUNDED
        self.page.update()
