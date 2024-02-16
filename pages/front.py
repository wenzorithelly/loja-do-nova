import flet as ft
import os
import pg8000
from dotenv import load_dotenv

load_dotenv()
db_params: dict = {
    "config": "postgres",
    "user": "postgres.crswolnvchmpqdjqldop",
    "password": os.environ.get("DB_PASSWORD"),
    "host": "aws-0-sa-east-1.pooler.supabase.com",
    "port": "5432"
}


class FrontBox(ft.SafeArea):
    def __init__(self, page: ft.Page, visible):
        super().__init__(visible)
        self.page = page

