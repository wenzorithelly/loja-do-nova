import flet as ft
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
import pytz
import os

load_dotenv()
supabaseUrl = "https://crswolnvchmpqdjqldop.supabase.co"
supabaseKey = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url=supabaseUrl, supabase_key=supabaseKey)


class Charts:
    def __init__(self):
        orders_data, order_details_data, users_data, products_data = self.fetch_data()
        self.orders_df = pd.DataFrame(orders_data)
        self.order_details_df = pd.DataFrame(order_details_data)
        self.users_df = pd.DataFrame(users_data)
        self.products_df = pd.DataFrame(products_data)

        self.details_with_products = pd.merge(self.order_details_df, self.products_df, left_on='product_id', right_on='id',
                                              how='inner', suffixes=('_order_details', '_products'))
        self.orders_with_details = pd.merge(self.orders_df, self.details_with_products, left_on='detail_id', right_on='id_order_details',
                                            how='inner', suffixes=('_orders', '_details_products'))
        self.final_merged_df = pd.merge(self.orders_with_details, self.users_df, left_on='user_id', right_on='id',
                                        how='inner', suffixes=('_orders_details_products', '_users'))

    @staticmethod
    def fetch_data():
        orders_data = supabase.table('orders').select('*').execute().data
        order_details_data = supabase.table('order_details').select('*').execute().data
        users_data = supabase.table('users').select('id, age').execute().data
        products_data = supabase.table('products').select('*').execute().data

        return orders_data, order_details_data, users_data, products_data

    def total_sold_today(self):
        brazil_tz = pytz.timezone('America/Sao_Paulo')
        self.orders_df['created_at'] = pd.to_datetime(self.orders_df['created_at'], errors='coerce').dt.tz_convert(brazil_tz)
        self.orders_df['total'] = self.orders_df['total'].astype(float)
        today = datetime.now().date()
        data = self.orders_df.loc[self.orders_df['created_at'].dt.date == today]
        total_sum = data['total'].sum()
        total_sum = round(total_sum, 2)
        return total_sum

    def orders_total_today(self):
        self.orders_df['created_at'] = pd.to_datetime(self.orders_df['created_at'])
        today = datetime.now().date()
        data = self.orders_df.loc[self.orders_df['created_at'].dt.date == today]
        data = data.shape[0]
        return data

    def products_sold_today(self):
        self.order_details_df['created_at'] = pd.to_datetime(self.order_details_df['created_at'])
        self.order_details_df['quantity'] = self.order_details_df['quantity'].astype(int)
        today = datetime.now().date()

        data = self.orders_df.loc[self.order_details_df['created_at'].dt.date == today]
        total_sum = data['quantity'].sum()
        return total_sum

    def most_sold_products_per_age(self):
        data = self.final_merged_df.groupby(['age', 'name'])['quantity_order_details'].sum().reset_index()
        data = data.sort_values(['age', 'quantity_order_details'], ascending=[True, False])

        max_indices = data.groupby('age')['quantity_order_details'].idxmax()

        result_df = data.loc[max_indices]

        bins = [10, 15, 20, 25, 30, 35, 40, float('inf')]
        labels = ['10-15', '15-20', '20-25', '25-30', '30-35', '35-40']
        result_df['age_group'] = pd.cut(result_df['age'], bins=bins[:-1], labels=labels, right=False)

        result_df = result_df[['age_group', 'name', 'quantity_order_details']]
        result_df = result_df.groupby('age_group', observed=True).first().reset_index()
        return result_df

    def most_sold_products(self):
        data = self.details_with_products.groupby('name')['quantity_order_details'].sum().reset_index()
        data = data.sort_values('quantity_order_details', ascending=False).head(8)
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
            ) for i, (name, quantity) in enumerate(zip(data['name'], data['quantity_order_details']))
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
            max_y=data['quantity_order_details'].max() + 2,
            expand=True,
        )
        return chart


toggle_style_sheet: dict = {"icon": ft.icons.REFRESH_ROUNDED, "icon_size": 20}


class Dashboard(ft.SafeArea):
    def __init__(self, page: ft.Page, visible):
        super().__init__(visible)
        self.page = page
        self.charts = Charts()
        self.title: ft.Text = ft.Text("Dashboard", size=20, weight=ft.FontWeight.W_800)
        self.toggle: ft.IconButton = ft.IconButton(
            **toggle_style_sheet, on_click=lambda e: self.refresh(e)
        )

        self.all_charts = self.load_data()
        self.main: ft.Column = ft.Column([
            ft.Container(content=ft.Column([
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[self.title, self.toggle]
                ),
                ft.Divider(height=5),
                ft.Divider(height=10, color=ft.colors.TRANSPARENT),

                # CHARTS
                self.all_charts
                ]), expand=True)
        ],
            scroll=ft.ScrollMode.ALWAYS)

        self.content = self.main

    def datatable_ages_products(self):
        products_per_age = self.charts.most_sold_products_per_age()
        columns = [
            ft.DataColumn(ft.Text("Idade")),
            ft.DataColumn(ft.Text("Produto")),
            ft.DataColumn(ft.Text("Qtde. Vendida"), numeric=True),
        ]

        rows = []
        for index, row in products_per_age.iterrows():
            cells = [
                ft.DataCell(ft.Text(str(row['age_group']))),
                ft.DataCell(ft.Text(row['name'])),
                ft.DataCell(ft.Text(str(row['quantity_order_details'])))
            ]
            rows.append(ft.DataRow(cells=cells))

        return ft.DataTable(columns=columns, rows=rows)

    def load_data(self):
        datatable_per_age = self.datatable_ages_products()
        today_total_sum = self.charts.total_sold_today()
        todays_sales = self.charts.orders_total_today()
        today_products = self.charts.products_sold_today()
        most_sold_products = self.charts.most_sold_products()

        all_charts = ft.Column([
            ft.Column(controls=[
                ft.Row(controls=[
                    ft.Text("Hoje:", size=20, weight=ft.FontWeight.W_800, text_align=ft.TextAlign.CENTER),
                    ft.Column(controls=[
                        ft.Text("Vendas", size=18, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                        ft.Text(todays_sales, size=30, weight=ft.FontWeight.BOLD, italic=True,
                                text_align=ft.TextAlign.CENTER)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Column(controls=[
                        ft.Text("Produtos", size=18, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                        ft.Text(today_products, size=30, weight=ft.FontWeight.BOLD, italic=True,
                                text_align=ft.TextAlign.CENTER)
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Column(controls=[
                        ft.Text("Total Vendido", size=18, weight=ft.FontWeight.W_500),
                        ft.Text(f"R${today_total_sum}", size=30, weight=ft.FontWeight.BOLD, italic=True)
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=5),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),

            # MOST SOLD PRODUCTS
            ft.Divider(height=10),
            ft.Row(controls=[ft.Text("Produtos Mais Vendidos", size=18, weight=ft.FontWeight.W_500)],
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(content=most_sold_products, alignment=ft.alignment.center),
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),

            # MOST SOLD PRODUCTS PER AGE
            ft.Divider(height=10),
            ft.Row(controls=[ft.Text("Produtos Mais Vendidos por Idade", size=18, weight=ft.FontWeight.W_500)],
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(content=datatable_per_age, alignment=ft.alignment.center)
        ])

        return all_charts

    def refresh(self, e):
        self.toggle.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.colors.WHITE)
        self.toggle.icon = None
        self.page.update()

        self.charts.fetch_data()
        new_charts = self.load_data()
        self.all_charts.controls.clear()
        self.all_charts.controls.extend(new_charts.controls)

        self.toggle.icon = ft.icons.REFRESH_ROUNDED
        self.page.update()
