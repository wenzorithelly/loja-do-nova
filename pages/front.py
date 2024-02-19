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
        super().__init__(width=170, height=170, padding=10, border_radius=10, margin=8,
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

        self.product_id_ = products['id']
        self.product_price_ = products['price']
        self.product_price_str = self.replace_dot(str(self.product_price_))
        self.product_price_str = f"R${self.product_price_str}"
        self.promotion_price_ = str(products['promotion_price'])
        self.promotion_price_str = self.replace_dot(str(self.promotion_price_))
        self.promotion_price_str = f"R${self.promotion_price_str}"

        self.product_title: ft.Text = ft.Text(products['name'], size=15, weight=ft.FontWeight.W_600)
        self.order_counter: ft.TextField = ft.TextField(value="0", text_align=ft.TextAlign.CENTER,
                                                        height=20, expand=False, width=50)
        self.product_price: ft.Text = ft.Text(self.product_price_str, size=14)
        self.promotion_price: ft.Text = ft.Text(self.promotion_price_str, size=16, visible=False)
        button_row = ft.Row(controls=[
            ft.IconButton(ft.icons.REMOVE, on_click=self.minus_click),
            self.order_counter,
            ft.IconButton(ft.icons.ADD, on_click=self.plus_click),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)

        self.if_promotion_price()
        self.content: ft.Column = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[self.product_title]),
                ft.Row(controls=[self.product_price, self.promotion_price], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=4, color=ft.colors.TRANSPARENT),
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
            self.promotion_price.visible = True
            self.product_price = ft.Text(spans=[ft.TextSpan(self.product_price_str, ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH))], size=12)
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
        self.send_order_button: ft.ElevatedButton = ft.ElevatedButton(
            text="Finalizar",
            bgcolor=ft.colors.GREEN_600,
            color=ft.colors.WHITE,
            height=30,
            on_click=lambda e: self.send_order(e)
        )

        self.user_name: ft.TextField = ft.TextField(label="Nome", height=35, border_radius=12, expand=True)
        self.user_age: ft.TextField = ft.TextField(label="Idade", height=35, border_radius=12, width=80)
        self.user_phone: ft.TextField = ft.TextField(label="Telefone", height=35, border_radius=12, expand=True)
        self.user_email: ft.TextField = ft.TextField(label="E-mail", height=35, border_radius=12, expand=True)
        self.payment_method: ft.Dropdown = ft.Dropdown(
            label="Pagamento",
            width=150, height=40, border_radius=12,
            options=[
                ft.dropdown.Option("Crédito"),
                ft.dropdown.Option("Débito"),
                ft.dropdown.Option("Dinheiro"),
                ft.dropdown.Option("Pix")
            ]
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
                ft.Divider(height=3, color=ft.colors.TRANSPARENT),
                ft.Row(controls=[ft.Text("Loja do Nova", size=20, weight=ft.FontWeight.W_800)],
                       alignment=ft.MainAxisAlignment.CENTER),
                self.order_summary,
                ft.Row(controls=[self.send_order_button], alignment=ft.MainAxisAlignment.END),
                ft.Divider(height=2, color=ft.colors.TRANSPARENT),
                ft.Divider(height=5),
                ft.Container(content=self.list_products, expand=False)
            ], scroll=ft.ScrollMode.HIDDEN
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
                    else:
                        product_price = float(product.product_price_)
                        quantity_ordered = int(product.order_counter.value)
                        total_amount += product_price * quantity_ordered

        total_amount_str = f"R${total_amount:.2f}"
        total_amount_str = replace_dot(total_amount_str)
        self.total_amount.value = total_amount_str

    def send_order(self, e):
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
            else:
                self.refresh_order_summary()
        except Exception as a:
            display_error_banner(self.page, str(a))

    def refresh_order_summary(self):
        self.user_name.value = ""
        self.user_email.value = ""
        self.user_age.value = ""
        self.user_phone.value = ""
        self.total_amount.value = ""
        self.payment_method.value = ""

        self.list_products.controls.clear()
        self.populate_products()
