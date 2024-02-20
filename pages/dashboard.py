import flet as ft
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

load_dotenv()
supabaseUrl = "https://crswolnvchmpqdjqldop.supabase.co"
supabaseKey = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url=supabaseUrl, supabase_key=supabaseKey)


class Charts:
    def __init__(self):
        orders_data = supabase.table('orders').select('*').execute().data
        order_details_data = supabase.table('order_details').select('*').execute().data
        users_data = supabase.table('users').select('*').execute().data
        products_data = supabase.table('products').select('*').execute().data
        self.orders_df = pd.DataFrame(orders_data)
        self.order_details_df = pd.DataFrame(order_details_data)
        self.users_df = pd.DataFrame(users_data)
        self.products_df = pd.DataFrame(products_data)

        self.details_with_products = pd.merge(self.order_details_df, self.products_df, left_on='product_id', right_on='id',
                                              how='inner')
        self.orders_with_details = pd.merge(self.orders_df, self.order_details_df, left_on='detail_id', right_on='id',
                                            how='inner')
        self.final_merged_df = pd.merge(self.orders_with_details, self.users_df, left_on='user_id', right_on='id',
                                        how='inner')

    def total_sold_today(self):
        self.orders_df['created_at'] = pd.to_datetime(self.orders_df['created_at'])
        self.orders_df['total'] = self.orders_df['total'].astype(float)
        today = datetime.now().date()
        data = self.orders_df[self.orders_df['created_at'].dt.date >= today]
        total_sum = data['total'].sum()
        return total_sum

    def orders_total(self):
        self.orders_df['created_at'] = pd.to_datetime(self.orders_df['created_at'])
        today = datetime.now().date()
        data = self.orders_df[self.orders_df['created_at'].dt.date >= today]
        data = data.shape[0]
        return data

    def products_total(self):
        data = self.order_details_df.shape[0]
        return data

    def most_sold_products(self):
        data = self.details_with_products.groupby('name')['quantity_x'].sum().reset_index()
        data = data.sort_values('quantity_x', ascending=False).head(8)
        bar_groups = [
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=quantity,
                        width=40,
                        color=ft.colors.BLUE,
                        border_radius=0,
                    ),
                ],
            ) for i, (name, quantity) in enumerate(zip(data['name'], data['quantity_x']))
        ]

        chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(1, ft.colors.GREY_400),
            left_axis=ft.ChartAxis(
                labels_size=40, title_size=40, labels_interval=1
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=i, label=ft.Container(ft.Text(name), padding=10))
                    for i, name in enumerate(data['name'])
                ],
                labels_size=40,
            ),
            max_y=data['quantity_x'].max() + 2,
            expand=True,
        )
        return chart


class Dashboard(ft.SafeArea):
    def __init__(self, page: ft.Page, visible):
        super().__init__(visible)
        self.page = page
        self.charts = Charts()

        self.today_total_sum = self.charts.total_sold_today()
        self.todays_sales = self.charts.orders_total()
        self.most_sold_products = self.charts.most_sold_products()
        self.main: ft.Column = ft.Column([
            ft.Divider(height=0.8, color=ft.colors.TRANSPARENT),
            ft.Row(controls=[ft.Text("Dashboard", size=20, weight=ft.FontWeight.W_800)],
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=0.2, color="transparent"),
            ft.Divider(height=4),
            ft.Divider(height=10, color="transparent"),

            # CHARTS
            ft.Column(controls=[
                ft.Row(controls=[
                    ft.Text("Hoje", size=20, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                    ft.Column(controls=[
                        ft.Text("Qtde. de Vendas", size=18, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.todays_sales, size=30, weight=ft.FontWeight.BOLD, italic=True, text_align=ft.TextAlign.CENTER)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Column(controls=[
                        ft.Text("Total Vendido", size=18, weight=ft.FontWeight.W_500),
                        ft.Text(f"R${self.today_total_sum}", size=30, weight=ft.FontWeight.BOLD, italic=True)
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=5),
                # Additional Rows or Columns if needed
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            ft.Row(controls=[ft.Text("Produtos Mais Vendidos", size=18, weight=ft.FontWeight.W_500)],
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(content=self.most_sold_products, alignment=ft.alignment.center),
        ], scroll=ft.ScrollMode.ALWAYS, expand=True)
        self.content = self.main
