import flet as ft
import os
from supabase import create_client
from dotenv import load_dotenv
import math

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
        self.main: ft.Column = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[self.title, self.toggle]
                ),
                ft.Divider(height=10),
                ft.Divider(height=10, color="transparent")
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
