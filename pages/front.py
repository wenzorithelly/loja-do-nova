import flet as ft
import os
from supabase import create_client
from dotenv import load_dotenv
import math

load_dotenv()
supabaseUrl = "https://crswolnvchmpqdjqldop.supabase.co"
supabaseKey = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url=supabaseUrl, supabase_key=supabaseKey)


def display_error_banner(page, error):
    def close_banner(e):
        page.banner.open = False
        page.update()

    page.banner = ft.Banner(
        bgcolor=ft.colors.RED_500,
        leading=ft.Icon(name=ft.icons.WARNING_AMBER_ROUNDED),
        content=ft.Text(f"Error occurred: {error}"),
        actions=[ft.TextButton("Cancel", on_click=close_banner)]
    )
    page.banner.open = True
    page.update()


def fetch_data(page: ft.Page) -> list:
    try:
        result = supabase.table("products").select('*').execute()
        products = result.data

        name_list = [{'id': product['id'], 'name': product['name'], 'quantity': product['quantity'],
                      'price': product['price'], 'promotion_price': product['promotion_price'],
                      'category': product['category']} for product in products if product['name']]
        return name_list

    except Exception as a:
        display_error_banner(page, a)
        return []


class Products(ft.Container):
    def __init__(self, frontbox: 'FrontBox', products: dict) -> None:
        super().__init__(width=170, height=170, padding=10, border_radius=10, ink=True, margin=8,
                         gradient=ft.LinearGradient(
                             begin=ft.alignment.top_left,
                             end=ft.Alignment(0.8, 1),
                             colors=[
                                ft.colors.INDIGO_800,
                                ft.colors.GREY_900
                             ],
                             tile_mode=ft.GradientTileMode.MIRROR,
                             rotation=math.pi / 3,
                         ))
        self.frontbox = frontbox
        self.products = products

        product_price = self.replace_dot(str(products['price']))
        product_price = f"R${product_price}"
        self.product_title: ft.Text = ft.Text(products['name'], size=15, weight=ft.FontWeight.W_600)
        self.order_counter: ft.TextField = ft.TextField(value="0", text_align=ft.TextAlign.CENTER,
                                                        height=20, expand=False, width=50)
        self.product_price: ft.Text = ft.Text(product_price, size=12)
        button_row = ft.Row(controls=[
            ft.IconButton(ft.icons.REMOVE, on_click=self.minus_click),
            self.order_counter,
            ft.IconButton(ft.icons.ADD, on_click=self.plus_click),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)

        self.content: ft.Column = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[self.product_title]),
                ft.Row(controls=[self.product_price]),
                ft.Divider(height=4, color=ft.colors.TRANSPARENT),
                button_row
            ]
        )

    def minus_click(self, e):
        self.order_counter.value = str(int(self.order_counter.value) - 1)
        if int(self.order_counter.value) < 0:
            self.order_counter.value = 0
        self.frontbox.page.update()

    def plus_click(self, e):
        self.order_counter.value = str(int(self.order_counter.value) + 1)
        self.frontbox.page.update()

    @staticmethod
    def replace_dot(num):
        if "." in num:
            number = num.replace(".", ",")
        else:
            number = num
        return number


class FrontBox(ft.SafeArea):
    def __init__(self, page: ft.Page, visible):
        super().__init__(visible)
        self.page = page
        self.data = fetch_data(page=self.page)
        self.list_products: ft.ListView = ft.ListView(expand=True, spacing=5)
        self.end_order: ft.ElevatedButton = ft.ElevatedButton(
            text="Finalizar Pedido",
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            height=30,
            on_click=self.open_dlg
        )

        self.dlg_content: ft.Container = ft.Container(content=ft.Column([
            ft.Text("Resumão")
        ]))
        self.order_dlg: ft.AlertDialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Resumo do Pedido"),
            content=self.dlg_content,
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dlg),
                ft.TextButton("Salvar", on_click=self.send_order()),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.content: ft.Column = ft.Column(
            controls=[
                ft.Divider(height=3, color=ft.colors.TRANSPARENT),
                ft.Row(controls=[ft.Text("Caixa", size=20, weight=ft.FontWeight.W_800),
                                 self.end_order],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=5, color=ft.colors.TRANSPARENT),
                ft.Container(content=self.list_products, expand=False)
            ]
        )
        self.populate_products()

    def populate_products(self):
        products_per_row = 2
        for i in range(0, len(self.data), products_per_row):
            row_controls = []
            for product in self.data[i:i + products_per_row]:
                row_controls.append(Products(self, product))

            self.list_products.controls.append(ft.Row(controls=row_controls, spacing=10))

        self.page.update()

    def open_dlg(self, e):
        self.page.dialog = self.order_dlg
        self.order_dlg.open = True
        self.page.update()

    def close_dlg(self, e):
        self.order_dlg.open = False
        self.page.update()

    def send_order(self):
        pass
