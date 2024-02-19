# TODO: Refresh page when product is detete
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
    def __init__(self, page: ft.Page, visible=False, frontbox=None):
        super().__init__(visible)
        self.page = page
        self.frontbox = frontbox
        self.search_field: ft.TextField = ft.TextField(**search_style_sheet, on_submit=lambda e: self.search_items())
        self.search_button: ft.IconButton = ft.IconButton(**search_button_style_sheet,
                                                          on_click=lambda e: self.search_items())
        self.data = fetch_data(page=self.page)
        self.text_fields = {}
        self.save_product_button = None
        self.delete_product_button = None
        self.expansion_panel_list = ft.ExpansionPanelList(expand=True)
        self.add_product: ft.IconButton = ft.IconButton(
            icon=ft.icons.ADD_ROUNDED,
            bgcolor=ft.colors.GREEN_600,
            icon_color=ft.colors.WHITE,
            on_click=self.open_dlg
        )

        # Dialog Content
        self.input_name: ft.TextField = ft.TextField(label="Nome do Produto", expand=True, border_radius=12)
        self.input_quantity: ft.TextField = ft.TextField(label="Quantidade", expand=True, border_radius=12)
        self.input_price: ft.TextField = ft.TextField(label="Preço", expand=True, border_radius=12)
        self.input_promotion: ft.TextField = ft.TextField(label="Preço Promocional", expand=True, border_radius=12)
        self.input_category: ft.TextField = ft.TextField(label="Categoria", expand=True, border_radius=12)
        self.dlg_content: ft.Container = ft.Container(content=ft.Column([
            self.input_name, self.input_quantity, self.input_price, self.input_promotion, self.input_category
        ], spacing=4))
        self.add_product_dlg: ft.AlertDialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Adicionar Produto"),
            content=self.dlg_content,
            actions=[
                ft.TextButton("Cancelar", on_click=self.close_dlg),
                ft.TextButton("Salvar", on_click=self.save_product),
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )

        # MAIN PAGE
        self.main: ft.Column = ft.Column(
            controls=[
                ft.Row(controls=[
                    ft.Text("       "),
                    ft.Row(controls=[
                        ft.Text("Lista de Produtos", size=20, weight=ft.FontWeight.W_800),
                    ], alignment=ft.MainAxisAlignment.CENTER, expand=True),
                    self.add_product,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=4),
                ft.Divider(height=10, color="transparent"),
                ft.Row(controls=[self.search_field, self.search_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.expansion_panel_list,
            ], scroll=ft.ScrollMode.ALWAYS
        )

        self.content = self.main
        self.populate_products()

    def populate_products(self):
        self.expansion_panel_list.controls.clear()
        for product in self.data:
            name_field = ft.TextField(value=str(product['name']), label="Nome")
            quantity_field = ft.TextField(value=str(product['quantity']), label="Quantidade")
            price_field = ft.TextField(value=str(product['price']), label="Preço")
            promotion_price_field = ft.TextField(value=str(product['promotion_price']), label="Preço Promoção")
            self.text_fields[product['id']] = {
                'name': name_field,
                'quantity': quantity_field,
                'price': price_field,
                'promotion_price': promotion_price_field
            }

            exp = ft.ExpansionPanel(
                header=ft.ListTile(title=ft.Text(product['name'])), can_tap_header=True, expand=True
            )
            self.save_product_button = ft.IconButton(icon=ft.icons.SAVE_ROUNDED, icon_color=ft.colors.BLUE_600,
                                                     on_click=lambda e, prod=product: self.handle_save(prod))
            self.delete_product_button = ft.IconButton(icon=ft.icons.DELETE_ROUNDED, icon_color=ft.colors.RED_700,
                                                       on_click=lambda e, prod=product: self.handle_delete(prod))
            exp.content = ft.Container(
                content=ft.Column([
                    ft.Divider(height=1, color=ft.colors.TRANSPARENT),
                    name_field,
                    quantity_field,
                    price_field,
                    promotion_price_field,
                    ft.Row(controls=[
                        self.save_product_button,
                        self.delete_product_button
                    ], alignment=ft.MainAxisAlignment.END)
                ])
            )

            self.expansion_panel_list.controls.append(exp)

        self.page.update()

    def handle_save(self, product):
        self.save_product_button.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.WHITE)
        self.save_product_button.icon = None
        self.page.update()

        product_id = product['id']
        fields = self.text_fields.get(product_id)

        def replace_comma(num):
            if "," in num:
                number = num.replace(",", ".")
            else:
                number = num
            return number

        price = replace_comma(fields['quantity'].value)
        promotion_price = replace_comma(fields['promotion_price'].value)

        if fields:  # Check if the fields exist for the product
            try:
                updated_product = {
                    'name': str(fields['name'].value),
                    'quantity': int(fields['quantity'].value),
                    'price': float(price),
                    'promotion_price': float(promotion_price),
                }
                result = supabase.table("products").update(updated_product).eq('id', product_id).execute()

                if not result.data:
                    raise Exception(result.error.message)

                self.refresh_product_list()

            except Exception as e:
                display_error_banner(self.page, str(e))

        self.save_product_button.icon = ft.icons.SAVE_ROUNDED
        self.page.update()

    def handle_delete(self, product):
        self.delete_product_button.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.WHITE)
        self.delete_product_button.icon = None
        self.page.update()

        product_id = product['id']
        try:
            data = supabase.table('products').delete().eq('id', product_id).execute()
            if not data.data:
                raise Exception(data.error.message)
            self.refresh_product_list()
        except Exception as e:
            display_error_banner(self.page, str(e))

        self.delete_product_button.icon = ft.icons.SAVE_ROUNDED
        self.page.update()

    def search_items(self):
        query = self.search_field.value.lower()
        if query:
            filtered_data = [product for product in self.data if query in product["name"].lower()]
            self.data = filtered_data
        else:
            self.data = fetch_data(self.page)

        self.populate_products()

    def open_dlg(self, e):
        self.page.dialog = self.add_product_dlg
        self.add_product_dlg.open = True
        self.page.update()

    def close_dlg(self, e):
        self.add_product_dlg.open = False
        self.page.update()

    def save_product(self, e):
        def replace_comma(num):
            if "," in num:
                number = num.replace(",", ".")
            else:
                number = num
            return number

        promotion_price = self.input_promotion.value if len(self.input_promotion.value) > 0 else "0"
        promotion_price = replace_comma(promotion_price)
        price = replace_comma(self.input_price.value)

        try:
            data = supabase.table('products').insert({"name": self.input_name.value, "price": price,
                                                      "quantity": self.input_quantity.value,
                                                      "promotion_price": promotion_price,
                                                      "category": self.input_category.value}).execute()
            if not data.data:
                raise Exception(data.error.message)
            else:
                self.close_dlg(e)
                self.refresh_product_list()
        except Exception as e:
            display_error_banner(self.page, str(e))

    def refresh_product_list(self):
        self.data = fetch_data(page=self.page)
        self.expansion_panel_list.controls.clear()
        self.populate_products()
        self.frontbox.refresh_products()
        self.page.update()
