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
        result = supabase.table("products").select('*').order("category").execute()
        products = result.data

        name_list = [{'id': product['id'], 'name': product['name'], 'quantity': product['quantity'],
                      'price': product['price'], 'promotion_price': product['promotion_price'],
                      'category': product['category']} for product in products if product['name']]
        return name_list

    except Exception as a:
        display_error_banner(page, a)
        return []


class Products(ft.Container):
    def __init__(self, frontbox: 'FrontBox', products: dict, quantity: int) -> None:
        super().__init__(width=180, height=130, padding=4, border_radius=10, margin=4, bgcolor=ft.colors.GREY_600)
        self.frontbox = frontbox
        self.products = products
        self.page = self.frontbox.page

        category_color_mapping = {
            'vestuário': ft.colors.BLUE_700,
        }

        category = products['category'].lower()
        self.bgcolor = category_color_mapping.get(category, ft.colors.GREY_600)

        self.product_id_ = products['id']
        self.product_price_ = products['price']
        self.product_price_str = self.replace_dot(str(self.product_price_))
        self.product_price_str = f"R${self.product_price_str}"
        self.promotion_price_ = str(products['promotion_price'])
        self.promotion_price_str = self.replace_dot(str(self.promotion_price_))
        self.promotion_price_str = f"R${self.promotion_price_str}"

        self.product_title: ft.Text = ft.Text(products['name'], size=14, weight=ft.FontWeight.W_600, color=ft.colors.WHITE)
        self.order_counter: ft.TextField = ft.TextField(value=str(quantity), text_align=ft.TextAlign.CENTER,
                                                        height=20, expand=False, width=50, color=ft.colors.WHITE)
        self.product_price: ft.Text = ft.Text(self.product_price_str, size=16, color=ft.colors.WHITE)
        self.promotion_price: ft.Text = ft.Text("", size=16, color=ft.colors.WHITE)
        button_row = ft.Row(controls=[
            ft.IconButton(ft.icons.REMOVE, on_click=self.minus_click, icon_color=ft.colors.WHITE),
            self.order_counter,
            ft.IconButton(ft.icons.ADD, on_click=self.plus_click, icon_color=ft.colors.WHITE),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)

        self.if_promotion_price()
        self.content: ft.Column = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[self.product_title]),
                ft.Row(controls=[self.promotion_price, self.product_price], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                # ft.Divider(height=1, color=ft.colors.TRANSPARENT),
                button_row
            ]
        )

    def minus_click(self, e):
        self.order_counter.value = str(int(self.order_counter.value) - 1)
        if int(self.order_counter.value) < 0:
            self.order_counter.value = 0
        self.frontbox.calculate_total_amount()
        self.frontbox.page.update()

    def plus_click(self, e):
        self.order_counter.value = str(int(self.order_counter.value) + 1)
        self.frontbox.calculate_total_amount()
        self.frontbox.page.update()

    def if_promotion_price(self):
        if float(self.promotion_price_) > 0:
            self.promotion_price.value = self.promotion_price_str
            self.product_price = ft.Text(spans=[ft.TextSpan(self.product_price_str, ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH))], size=13)
        self.frontbox.page.update()

    @staticmethod
    def replace_dot(num):
        if "." in num:
            number = num.replace(".", ",")
        else:
            number = num
        return number


toggle_style_sheet: dict = {"icon": ft.icons.REFRESH_ROUNDED, "icon_size": 20}
search_button_style_sheet: dict = {"icon": ft.icons.SEARCH_ROUNDED, "icon_size": 25}
search_style_sheet: dict = {"height": 35, "expand": True, "cursor_height": 15, "hint_text": "Pesquisar um produto...",
                            "content_padding": 7, "border_radius": 12}


class FrontBox(ft.SafeArea):
    def __init__(self, page: ft.Page, visible, app=None):
        super().__init__(visible)
        self.page = page
        self.data = fetch_data(page=self.page)
        self.title: ft.Text = ft.Text("Loja do Nova", size=20, weight=ft.FontWeight.W_800)
        self.app = app
        # self.menubar = self.app.menubar
        self.toggle: ft.IconButton = ft.IconButton(
            **toggle_style_sheet, on_click=lambda e: self.refresh(e)
        )
        self.search_field: ft.TextField = ft.TextField(**search_style_sheet, on_submit=lambda e: self.search_items())
        self.search_button: ft.IconButton = ft.IconButton(**search_button_style_sheet,
                                                          on_click=lambda e: self.search_items())
        self.list_products: ft.ListView = ft.ListView(expand=True, spacing=5)
        self.quantities = {}
        self.reset_order_button: ft.TextButton = ft.TextButton(
            text="Reset",
            on_click=self.reset_order
        )
        self.send_order_button: ft.ElevatedButton = ft.ElevatedButton(
            text="Finalizar",
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            height=35,
            on_click=lambda e: self.send_order(e)
        )

        self.user_name: ft.TextField = ft.TextField(label="Nome", height=35, border_radius=12, expand=True)
        self.user_age: ft.TextField = ft.TextField(label="Idade", height=35, border_radius=12, width=80)
        self.user_phone: ft.TextField = ft.TextField(label="Telefone", height=35, border_radius=12, expand=True)
        self.user_email: ft.TextField = ft.TextField(label="E-mail", height=35, border_radius=12, expand=True)
        self.payment_method: ft.Dropdown = ft.Dropdown(
            label="Pagamento",
            width=150, border_radius=12,
            options=[
                ft.dropdown.Option("Crédito"),
                ft.dropdown.Option("Débito"),
                ft.dropdown.Option("Dinheiro"),
                ft.dropdown.Option("Pix")
            ],
            focused_border_color=ft.colors.BLACK
        )
        self.total_amount: ft.Text = ft.Text("R$0,00", size=20)
        self.order_summary: ft.Container = ft.Container(content=ft.Column([
            ft.Row(controls=[self.user_name]),
            ft.Row(controls=[self.user_age, self.user_phone], spacing=10),
            ft.Row(controls=[self.user_email]),
            ft.Divider(height=2, color=ft.colors.TRANSPARENT),
            ft.Row(controls=[self.payment_method, self.total_amount], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ]))

        self.content: ft.Column = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[self.title,
                              ft.Row([self.toggle], alignment=ft.MainAxisAlignment.END)
                              ]
                ),
                ft.Divider(height=5),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                self.order_summary,
                ft.Row(controls=[self.reset_order_button, self.send_order_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=2, color=ft.colors.TRANSPARENT),
                ft.Divider(height=5),
                ft.Row(controls=[self.search_field, self.search_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(content=self.list_products, expand=True)
            ], scroll=ft.ScrollMode.ALWAYS
        )
        self.populate_products()

    def refresh_products(self):
        self.data = fetch_data(self.page)
        self.list_products.controls.clear()
        self.populate_products()

    def populate_products(self):
        products_per_row = 2
        for i in range(0, len(self.data), products_per_row):
            row_controls = []
            for product in self.data[i:i + products_per_row]:
                if product['id'] not in self.quantities:
                    self.quantities[product['id']] = 0
                row_controls.append(Products(self, product, self.quantities[product['id']]))

            self.list_products.controls.append(ft.Row(controls=row_controls, spacing=10))

        self.page.update()

    def search_items(self):
        query = self.search_field.value.lower()
        if query:
            filtered_data = [product for product in self.data if query in product["name"].lower()]
            self.data = filtered_data
        else:
            self.data = fetch_data(self.page)

        self.list_products.controls.clear()
        self.populate_products()

    def calculate_total_amount(self):
        def replace_dot(num):
            if "." in num:
                number = num.replace(".", ",")
            else:
                number = num
            return number

        total_amount = 0
        for row in self.list_products.controls:
            for product in row.controls:
                if isinstance(product, Products):
                    if float(product.promotion_price_) > 0:
                        product_price = float(product.promotion_price_)
                        quantity_ordered = int(product.order_counter.value)
                        total_amount += product_price * quantity_ordered
                        self.quantities[product.product_id_] = quantity_ordered
                    else:
                        product_price = float(product.product_price_)
                        quantity_ordered = int(product.order_counter.value)
                        total_amount += product_price * quantity_ordered
                        self.quantities[product.product_id_] = quantity_ordered

        total_amount_str = f"R${total_amount:.2f}"
        total_amount_str = replace_dot(total_amount_str)
        self.total_amount.value = total_amount_str

    def send_order(self, e):
        self.send_order_button.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.WHITE)
        self.send_order_button.icon = None
        self.page.update()
        try:
            user_data = {
                "name": self.user_name.value,
                "email": self.user_email.value if self.user_email.value else None,
                "phone": self.user_phone.value if self.user_phone.value else None,
                "age": self.user_age.value if self.user_age.value else None
            }
            user = supabase.table('users').insert(user_data).execute()
            user_id = user.data[0]['id']

            order_detail_data = []
            for row in self.list_products.controls:
                for product in row.controls:
                    if isinstance(product, Products):
                        if int(product.order_counter.value) > 0:
                            detail_data = {
                                "product_id": product.product_id_,
                                "quantity": int(product.order_counter.value)
                            }
                            order_detail_data.append(detail_data)

            detail = supabase.table('order_details').insert(order_detail_data).execute()
            detail_id = detail.data[0]['id']

            def extract_and_convert_to_float(input_string):
                cleaned_string = ''.join(char if char.isdigit() or char in {',', '.'} else ' ' for char in input_string)

                cleaned_string = cleaned_string.replace(',', '.')

                return float(cleaned_string)

            order = supabase.table('orders').insert({
                "user_id": user_id,
                "detail_id": detail_id,
                "payment_type": self.payment_method.value,
                "total": extract_and_convert_to_float(self.total_amount.value)
            }).execute()

            if not order.data:
                raise Exception

            self.refresh_order_summary()
        except Exception as a:
            display_error_banner(self.page, str(a))

    def reset_order(self, e):
        self.refresh_order_summary()

    def refresh_order_summary(self):
        self.send_order_button.content = None
        self.send_order_button.text = "Finalizar"
        self.user_name.value = ""
        self.user_email.value = ""
        self.user_age.value = ""
        self.user_phone.value = ""
        self.total_amount.value = "R$0,00"
        self.payment_method.value = None
        self.quantities = {}

        self.list_products.controls.clear()
        self.populate_products()

    def refresh(self, e):
        self.toggle.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.WHITE)
        self.toggle.icon = None
        self.page.update()

        self.refresh_products()

        self.toggle.icon = ft.icons.REFRESH_ROUNDED
        self.page.update()
