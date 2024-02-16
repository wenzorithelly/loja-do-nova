import flet as ft
import os
from supabase import create_client
from dotenv import load_dotenv

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


search_button_style_sheet: dict = {"icon": ft.icons.SEARCH_ROUNDED, "icon_size": 25}
search_style_sheet: dict = {"height": 35, "expand": True, "cursor_height": 15, "hint_text": "Pesquisar um produto...",
                            "content_padding": 7, "border_radius": 12}


class Products(ft.SafeArea):
    def __init__(self, page: ft.Page, visible):
        super().__init__(visible)
        self.page = page
        self.search_field: ft.TextField = ft.TextField(**search_style_sheet, on_submit=lambda e: self.search_items())
        self.search_button: ft.IconButton = ft.IconButton(**search_button_style_sheet, on_click=lambda e: self.search_items())
        self.data = fetch_data(page=self.page)
        self.text_fields = {}
        self.expansion_panel_list = ft.ExpansionPanelList()

        self.main: ft.Column = ft.Column(
            controls=[
                ft.Row(controls=[ft.Text("Lista de Produtos", size=18, weight=ft.FontWeight.W_600)],
                       alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(controls=[self.search_field, self.search_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.expansion_panel_list,
                ft.Divider(height=10)
            ]
        )

        self.content = self.main
        self.populate_products()

    def populate_products(self):
        self.expansion_panel_list.controls.clear()
        for product in self.data:
            quantity_field = ft.TextField(value=str(product['quantity']), label="Quantidade")
            price_field = ft.TextField(value=str(product['price']), label="Preço")
            promotion_price_field = ft.TextField(value=str(product['promotion_price']), label="Preço Promoção")
            self.text_fields[product['id']] = {
                'quantity': quantity_field,
                'price': price_field,
                'promotion_price': promotion_price_field
            }

            exp = ft.ExpansionPanel(
                header=ft.ListTile(title=ft.Text(product['name'])), can_tap_header=True
            )

            exp.content = ft.Container(
                content=ft.Column([
                    quantity_field,
                    price_field,
                    promotion_price_field,
                    ft.Row(controls=[
                        ft.IconButton(icon=ft.icons.SAVE_ROUNDED, on_click=lambda e, prod=product: self.handle_save(prod)),
                        ft.IconButton(icon=ft.icons.DELETE_ROUNDED, on_click=lambda e, prod=product: self.handle_delete(prod))
                    ], alignment=ft.MainAxisAlignment.END)
                ])
            )

            self.expansion_panel_list.controls.append(exp)

        self.page.update()

    def handle_save(self, product):
        product_id = product['id']
        fields = self.text_fields.get(product_id)

        if fields:  # Check if the fields exist for the product
            try:
                updated_product = {
                    'quantity': int(fields['quantity'].value),
                    'price': float(fields['price'].value),
                    'promotion_price': float(fields['promotion_price'].value),
                }
                result = supabase.table("products").update(updated_product).eq('id', product_id).execute()

                if not result.data:
                    raise Exception(result.error.message)

                self.data = fetch_data(self.page)
                self.populate_products()

            except Exception as e:
                display_error_banner(self.page, str(e))

    def handle_delete(self, product):
        product_id = product['id']
        try:
            data = supabase.table('products').delete().eq('id', product_id).execute()
            if not data.data:
                raise Exception(data.error.message)
        except Exception as e:
            display_error_banner(self.page, str(e))

    def search_items(self):
        query = self.search_field.value.lower()
        if query:
            filtered_data = [product for product in self.data if query in product["name"].lower()]
            self.data = filtered_data
        self.populate_products()
