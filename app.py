import flet as ft
import datetime
import time
import random
import math
import logging
from typing import Optional
from enum import Enum

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='billiard_app.log'
)

class TableStatus(Enum):
    AVAILABLE = "Свободен"
    OCCUPIED = "Занят"
    MAINTENANCE = "Обслуживание"
    RESERVED = "Бронь"

class BilliardTable(ft.Container):
    def __init__(self, app, number: int, status: TableStatus = TableStatus.AVAILABLE, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.number = number
        self.status = status
        self.width = 180
        self.height = 180
        self.border_radius = 12
        self.drag_interval = 10
        self.animate = ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        self.on_hover = self.hover_animation
        self.on_click = self.select_table
        self.client_name = ""
        self.start_time = None
        self.current_tariff = 10  # 10 руб за минуту
        self.products = []
        self.selected = False
        
        self.status_colors = {
            TableStatus.AVAILABLE: ft.colors.with_opacity(0.8, "#4CAF50"),
            TableStatus.OCCUPIED: ft.colors.with_opacity(0.8, "#FF9800"),
            TableStatus.MAINTENANCE: ft.colors.with_opacity(0.8, "#F44336"),
            TableStatus.RESERVED: ft.colors.with_opacity(0.8, "#2196F3")
        }
        
        self.bgcolor = ft.colors.with_opacity(0.9, "#8B4513")
        self.border = ft.border.all(2, "#5D4037")
        self.gradient = ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.with_opacity(0.7, "#8B4513"), ft.colors.with_opacity(0.9, "#5D4037")]
        )
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.colors.with_opacity(0.3, "#000000"),
            offset=ft.Offset(0, 0),
            blur_style=ft.ShadowBlurStyle.NORMAL,
        )
        self.content = self._create_table_content()
    
    def _create_table_content(self):
        # Создаем элементы управления, которые будем обновлять
        self.status_text = ft.Text(
            self.status.value,
            size=14,
            color=self.status_colors[self.status],
            weight=ft.FontWeight.BOLD
        )
        
        self.time_text = ft.Text(
            "00:00:00",
            size=12,
            color="white"
        ) if self.status == TableStatus.OCCUPIED else ft.Container()
        
        return ft.Stack(
            [
                # Основная поверхность стола
                ft.Container(
                    width=160,
                    height=120,
                    bgcolor="#2E7D32",
                    border_radius=10,
                    border=ft.border.all(2, "#1B5E20"),
                    top=10,
                    left=10,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=["#2E7D32", "#1B5E20"]
                    ),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.2, "#000000"),
                    )
                ),
                # Лузы
                *[self._create_pocket(x, y) for x, y in [(10,10), (144,10), (10,110), (144,110)]],
                # Номер стола
                ft.Container(
                    width=40,
                    height=40,
                    bgcolor=self.status_colors[self.status],
                    border_radius=20,
                    alignment=ft.alignment.center,
                    left=70,
                    top=50,
                    content=ft.Text(
                        f"{self.number}",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="white"
                    ),
                    animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=10,
                        color=ft.colors.with_opacity(0.3, "#000000"),
                    )
                ),
                # Статус и время
                ft.Container(
                    content=ft.Column(
                        [
                            self.status_text,
                            self.time_text
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    left=40,
                    top=100,
                    width=100,
                    alignment=ft.alignment.center,
                    opacity=0.9
                )
            ],
            width=180,
            height=180
        )
    
    def _create_pocket(self, left, top):
        return ft.Container(
            width=16,
            height=16,
            bgcolor="black",
            border_radius=8,
            left=left,
            top=top,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=5,
                color=ft.colors.with_opacity(0.5, "#000000"),
            )
        )
    
    def hover_animation(self, e):
        self.scale = 1.03 if e.data == "true" else 1
        self.border = ft.border.all(2, "#3498DB" if e.data == "true" else "#5D4037")
        self.update()
    
    def select_table(self, e):
        for table in self.app.tables:
            table.selected = False
            table.border = ft.border.all(2, "#5D4037")
            table.update()
        
        self.selected = True
        self.border = ft.border.all(3, "#3498DB")
        self.update()
        self.app.update_table_info(self)
    
    def update_status_display(self):
        self.status_text.value = self.status.value
        self.status_text.color = self.status_colors[self.status]
        
        if self.status == TableStatus.OCCUPIED:
            if not isinstance(self.time_text, ft.Text):
                self.time_text = ft.Text("00:00:00", size=12, color="white")
        else:
            if isinstance(self.time_text, ft.Text):
                self.time_text = ft.Container()
        
        self.update()

class ProductItem(ft.Container):
    def __init__(self, app, name: str, price: float, stock: int, category: str, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category
        self.width = 200
        self.height = 140
        self.bgcolor=ft.colors.with_opacity(0.8, "#424242")
        self.border_radius=14
        self.padding=14
        self.border=ft.border.all(1, ft.colors.with_opacity(0.3, "#616161"))
        self.animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        self.on_hover=self.hover_animation
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.colors.with_opacity(0.2, "#000000"),
        )
        
        self.content=ft.Column(
            controls=[
                ft.Container(
                    height=60,
                    width=60,
                    border_radius=10,
                    bgcolor=ft.colors.with_opacity(0.2, "#616161"),
                    content=ft.Icon(ft.icons.LOCAL_BAR, color="white", size=28),
                    alignment=ft.alignment.center,
                    animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
                ),
                ft.Text(self.name, weight=ft.FontWeight.BOLD, size=16, color="white"),
                ft.Row(
                    controls=[
                        ft.Text(f"{self.price:.2f} ₽", color="#4CAF50", size=14),
                        ft.Text(f"{self.stock} шт.", size=12, color="#BDBDBD")
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    width=170
                ),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "Добавить",
                    width=140,
                    height=36,
                    on_click=self.add_to_table,
                    style=ft.ButtonStyle(
                        padding=ft.Padding(0, 0, 0, 0),
                        bgcolor={"": ft.colors.with_opacity(0.8, "#42A5F5"), "hovered": ft.colors.with_opacity(1, "#1E88E5")},
                        shape=ft.RoundedRectangleBorder(radius=10),
                        animation_duration=200,
                        overlay_color=ft.colors.with_opacity(0.1, "#FFFFFF")
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6
        )
    
    def hover_animation(self, e):
        self.scale = 1.02 if e.data == "true" else 1
        self.border = ft.border.all(1, ft.colors.with_opacity(0.8, "#42A5F5") if e.data == "true" else ft.colors.with_opacity(0.3, "#616161"))
        self.bgcolor = ft.colors.with_opacity(0.9, "#616161") if e.data == "true" else ft.colors.with_opacity(0.8, "#424242")
        self.content.controls[0].scale = 1.1 if e.data == "true" else 1
        self.update()
    
    def add_to_table(self, e):
        if not self.app.tables:
            self.app.show_snackbar("Нет доступных столов")
            return
            
        def on_table_selected(e):
            if not dd.value:
                self.app.show_snackbar("Выберите стол")
                return
                
            table_number = int(dd.value)
            table = next(t for t in self.app.tables if t.number == table_number)
            if table.status != TableStatus.OCCUPIED:
                self.app.show_snackbar(f"Стол {table_number} должен быть занят")
                return
                
            table.products.append({"name": self.name, "price": self.price})
            self.stock -= 1
            self.content.controls[2].controls[1].value = f"{self.stock} шт."
            self.update()
            self.app.update_table_info(table)
            self.app.show_snackbar(f"Добавлено {self.name} к столу {table_number}")
            self.app.close_dialog()
        
        dd = ft.Dropdown(
            options=[ft.dropdown.Option(t.number) for t in self.app.tables if t.status == TableStatus.OCCUPIED],
            width=220,
            height=48,
            hint_text="Выберите стол",
            color="white",
            bgcolor=ft.colors.with_opacity(0.8, "#424242"),
            border_color=ft.colors.with_opacity(0.5, "#42A5F5"),
            focused_border_color="#42A5F5",
            border_radius=10,
            text_size=14
        )
        
        self.app.page.dialog = ft.AlertDialog(
            title=ft.Text(f"Добавить {self.name} к столу", color="white", size=18),
            content=dd,
            bgcolor=ft.colors.with_opacity(0.9, "#2E2E2E"),
            actions=[
                ft.ElevatedButton(
                    "Добавить",
                    on_click=on_table_selected,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#42A5F5", "hovered": "#1E88E5"},
                        padding=ft.Padding(16, 8, 16, 8),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    )
                ),
                ft.OutlinedButton(
                    "Отмена",
                    on_click=lambda e: self.app.close_dialog(),
                    style=ft.ButtonStyle(
                        side=ft.BorderSide(1, "#616161"),
                        shape=ft.RoundedRectangleBorder(radius=10)
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=12)
        )
        self.app.page.dialog.open = True
        self.app.page.update()

class BilliardApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Billiard Club Pro"
        self.page.window_width = 1366
        self.page.window_height = 768
        self.page.window_min_width = 1024
        self.page.window_min_height = 600
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#121212"
        self.page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"
        }
        self.page.theme = ft.Theme(font_family="Roboto")
        
        self.selected_table = None
        self.current_view = "tables"
        self.tables = []
        self.products = [
            {"name": "Пиво", "price": 150.00, "stock": 24, "category": "Алкоголь"},
            {"name": "Кола", "price": 80.00, "stock": 36, "category": "Напитки"},
            {"name": "Вода", "price": 50.00, "stock": 48, "category": "Напитки"},
            {"name": "Чипсы", "price": 120.00, "stock": 20, "category": "Закуски"},
            {"name": "Кофе", "price": 90.00, "stock": 30, "category": "Напитки"},
            {"name": "Чай", "price": 60.00, "stock": 40, "category": "Напитки"},
            {"name": "Бургер", "price": 180.00, "stock": 15, "category": "Закуски"},
            {"name": "Вино", "price": 250.00, "stock": 12, "category": "Алкоголь"},
        ]
        self.current_category = "Все"
        
        self.setup_ui()
        self.initialize_tables()
        self.update_clock()
        self.start_cost_updater()
    
    def setup_ui(self):
        # Верхняя панель с эффектом стекла
        self.navbar = ft.Container(
            height=70,
            bgcolor=ft.colors.with_opacity(0.7, "#1E1E1E"),
            padding=ft.padding.symmetric(horizontal=30),
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.with_opacity(0.2, "#FFFFFF"))),
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.SPORTS_BAR, color="#42A5F5", size=30),
                            ft.Text("Billiard Club Pro", size=24, weight=ft.FontWeight.BOLD, color="white"),
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        width=200,
                        height=44,
                        bgcolor=ft.colors.with_opacity(0.4, "#424242"),
                        border_radius=22,
                        padding=ft.padding.symmetric(horizontal=16),
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.ACCOUNT_CIRCLE_OUTLINED, size=22, color="white"),
                                ft.Text("Администратор", size=14, color="white"),
                            ],
                            spacing=12,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        border=ft.border.all(1, ft.colors.with_opacity(0.1, "#FFFFFF")),
                        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                        on_hover=lambda e: self._navbar_hover(e)
                    ),
                    self.clock_display()
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.colors.with_opacity(0.3, "#000000"),
            )
        )
        
        # Боковое меню
        self.sidebar = ft.Container(
            width=240,
            bgcolor=ft.colors.with_opacity(0.8, "#1E1E1E"),
            padding=ft.padding.only(top=20, left=10, right=10),
            border=ft.border.only(right=ft.border.BorderSide(1, ft.colors.with_opacity(0.1, "#FFFFFF"))),
            content=ft.Column(
                controls=[
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.TABLE_RESTAURANT_OUTLINED, color="white"),
                        title=ft.Text("Столы", color="white"),
                        selected=self.current_view == "tables",
                        on_click=lambda e: self.switch_view("tables"),
                        hover_color=ft.colors.with_opacity(0.1, "#42A5F5"),
                        height=48,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.LOCAL_BAR_OUTLINED, color="white"),
                        title=ft.Text("Бар", color="white"),
                        selected=self.current_view == "service",
                        on_click=lambda e: self.switch_view("service"),
                        hover_color=ft.colors.with_opacity(0.1, "#42A5F5"),
                        height=48,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    ft.Container(expand=True),
                ],
                spacing=4
            )
        )
        
        # Панель информации о столе
        self.table_info_panel = ft.Container(
            padding=20,
            margin=ft.margin.only(bottom=20),
            border_radius=14,
            bgcolor=ft.colors.with_opacity(0.7, "#2E2E2E"),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, "#FFFFFF")),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Информация о столе", size=20, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Container(expand=True),
                            ft.PopupMenuButton(
                                icon=ft.icons.MORE_VERT,
                                icon_color="white",
                                items=self._create_table_menu_items(),
                                tooltip="Действия со столом"
                            )
                        ]
                    ),
                    ft.Divider(height=1, color=ft.colors.with_opacity(0.1, "#FFFFFF")),
                    ft.Column(
                        controls=[
                            self._create_info_row("Стол:", "-", True),
                            self._create_info_row("Статус:", "-"),
                            self._create_info_row("Время:", "-"),
                            self._create_info_row("Стоимость:", "-"),
                            ft.Container(
                                content=ft.ListView(height=120, spacing=6),
                                padding=ft.padding.only(top=10)
                            )  # Для продуктов
                        ],
                        spacing=8
                    )
                ],
                spacing=12
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.colors.with_opacity(0.2, "#000000"),
            )
        )
        
        # Доска с столами
        self.board_container = ft.Container(
            expand=True,
            padding=20,
            content=ft.GridView(
                runs_count=4,
                max_extent=200,
                child_aspect_ratio=0.9,
                spacing=20,
                run_spacing=20,
            )
        )
        
        # Фильтры для бара
        self.category_filter = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Все",
                    on_click=lambda e: self.filter_products("Все"),
                    bgcolor={"": "#42A5F5", "hovered": "#1E88E5"},
                    color="white",
                    height=36,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(20, 0, 20, 0),
                        animation_duration=200
                    )
                ),
                ft.ElevatedButton(
                    "Напитки",
                    on_click=lambda e: self.filter_products("Напитки"),
                    bgcolor={"": ft.colors.with_opacity(0.3, "#424242"), "hovered": ft.colors.with_opacity(0.5, "#424242")},
                    color="white",
                    height=36,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(20, 0, 20, 0),
                        animation_duration=200
                    )
                ),
                ft.ElevatedButton(
                    "Закуски",
                    on_click=lambda e: self.filter_products("Закуски"),
                    bgcolor={"": ft.colors.with_opacity(0.3, "#424242"), "hovered": ft.colors.with_opacity(0.5, "#424242")},
                    color="white",
                    height=36,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(20, 0, 20, 0),
                        animation_duration=200
                    )
                ),
                ft.ElevatedButton(
                    "Алкоголь",
                    on_click=lambda e: self.filter_products("Алкоголь"),
                    bgcolor={"": ft.colors.with_opacity(0.3, "#424242"), "hovered": ft.colors.with_opacity(0.5, "#424242")},
                    color="white",
                    height=36,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(20, 0, 20, 0),
                        animation_duration=200
                    )
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            wrap=True
        )
        
        # Меню бара
        self.service_view = ft.Column(
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=20),
                    content=self.category_filter
                ),
                ft.GridView(
                    runs_count=4,
                    max_extent=220,
                    child_aspect_ratio=0.85,
                    spacing=15,
                    run_spacing=15,
                    padding=20,
                    expand=True
                )
            ],
            expand=True,
            spacing=0
        )
        
        # Основная область контента
        self.main_content = ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=[
                    self.table_info_panel if self.current_view == "tables" else ft.Container(),
                    ft.Container(
                        content=self.board_container if self.current_view == "tables" else self.service_view,
                        expand=True
                    )
                ],
                expand=True
            )
        )
        
        self.page.add(
            ft.Column(
                controls=[self.navbar],
                spacing=0
            ),
            ft.Row(
                controls=[self.sidebar, self.main_content],
                expand=True,
                spacing=0
            )
        )
    
    def _navbar_hover(self, e):
        e.control.bgcolor = ft.colors.with_opacity(0.6, "#424242") if e.data == "true" else ft.colors.with_opacity(0.4, "#424242")
        e.control.update()
    
    def _create_table_menu_items(self):
        items = [
            ft.PopupMenuItem(
                content=ft.Text("Свободен", color="white"),
                on_click=lambda e: self.change_table_status(TableStatus.AVAILABLE),
            ),
            ft.PopupMenuItem(
                content=ft.Text("Занят", color="white"),
                on_click=lambda e: self.change_table_status(TableStatus.OCCUPIED),
            ),
            ft.PopupMenuItem(
                content=ft.Text("Обслуживание", color="white"),
                on_click=lambda e: self.change_table_status(TableStatus.MAINTENANCE),
            ),
            ft.PopupMenuItem(
                content=ft.Text("Бронь", color="white"),
                on_click=lambda e: self.change_table_status(TableStatus.RESERVED),
            ),
            ft.PopupMenuItem(),
        ]
        
        if self.selected_table and self.selected_table.status == TableStatus.OCCUPIED:
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text("Остановить аренду", color="white"),
                    on_click=self.stop_rental,
                    icon=ft.icons.STOP
                )
            )
            items.append(ft.PopupMenuItem())
            
        items.append(
            ft.PopupMenuItem(
                content=ft.Text("Удалить стол", color="white"),
                on_click=self.remove_table,
                icon=ft.icons.DELETE
            )
        )
        
        return items
    
    def _create_info_row(self, label: str, value: str, bold: bool = False):
        return ft.Row(
            controls=[
                ft.Text(label, size=16, width=120, color="#BDBDBD"),
                ft.Text(value, size=16, weight=ft.FontWeight.BOLD if bold else None, color="white")
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def initialize_tables(self):
        for i in range(1, 9):
            status = TableStatus.AVAILABLE
            if i % 3 == 0: status = TableStatus.OCCUPIED
            
            table = BilliardTable(
                app=self,
                number=i,
                status=status
            )
            if status == TableStatus.OCCUPIED:
                table.start_time = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(5, 120))
            
            self.tables.append(table)
        
        self.board_container.content.controls = self.tables
        self.board_container.update()
    
    def clock_display(self):
        self.clock = ft.Text(datetime.datetime.now().strftime("%H:%M:%S"), size=16, color="white")
        self.date_display = ft.Text(datetime.datetime.now().strftime("%d.%m.%Y"), size=14, color="#BDBDBD")
        return ft.Container(
            content=ft.Column(
                controls=[self.clock, self.date_display],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.END
            ),
            padding=ft.padding.only(right=10)
        )
    
    def update_clock(self):
        def update():
            while True:
                try:
                    time.sleep(1)
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    current_date = datetime.datetime.now().strftime("%d.%m.%Y")
                    
                    if hasattr(self, 'clock') and hasattr(self, 'date_display'):
                        self.clock.value = current_time
                        self.date_display.value = current_date
                        self.clock.update()
                        self.date_display.update()
                except Exception as e:
                    logging.error(f"Error updating clock: {e}")
                    time.sleep(5)
        
        import threading
        threading.Thread(target=update, daemon=True).start()
    
    def start_cost_updater(self):
        def update_cost():
            while True:
                try:
                    time.sleep(60)  # Обновляем каждую минуту
                    for table in self.tables:
                        if table.status == TableStatus.OCCUPIED and table.start_time:
                            duration = datetime.datetime.now() - table.start_time
                            hours = int(duration.total_seconds() // 3600)
                            minutes = int((duration.total_seconds() % 3600) // 60)
                            seconds = int(duration.total_seconds() % 60)
                            
                            if hasattr(table, 'time_text') and isinstance(table.time_text, ft.Text):
                                table.time_text.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                                table.update()
                            
                            if table == self.selected_table:
                                self.update_table_info(table)
                except Exception as e:
                    logging.error(f"Error updating costs: {e}")
                    time.sleep(5)
        
        import threading
        threading.Thread(target=update_cost, daemon=True).start()
    
    def switch_view(self, view_name):
        self.current_view = view_name
        self.main_content.content.controls[0].visible = view_name == "tables"
        self.main_content.content.controls[1].content = (
            self.board_container if view_name == "tables" else self.service_view
        )
        self.page.update()
    
    def filter_products(self, category: str):
        self.current_category = category
        grid_view = self.service_view.controls[1]
        grid_view.controls.clear()
        
        for product in self.products:
            if category == "Все" or product["category"] == category:
                grid_view.controls.append(
                    ProductItem(
                        app=self,
                        name=product["name"],
                        price=product["price"],
                        stock=product["stock"],
                        category=product["category"]
                    )
                )
        
        # Обновляем состояние кнопок фильтров
        for btn in self.category_filter.controls:
            btn.bgcolor = (
                {"": "#42A5F5", "hovered": "#1E88E5"} 
                if btn.text == category 
                else {"": ft.colors.with_opacity(0.3, "#424242"), "hovered": ft.colors.with_opacity(0.5, "#424242")}
            )
            btn.update()
        
        self.page.update()
    
    def update_table_info(self, table: Optional[BilliardTable] = None):
        self.selected_table = table
        info = self.table_info_panel.content.controls[2].controls
        
        if table:
            info[0].controls[1].value = f"{table.number}"
            info[1].controls[1].value = table.status.value
            info[1].controls[1].color = table.status_colors[table.status]
            
            if table.status == TableStatus.OCCUPIED and table.start_time:
                duration = datetime.datetime.now() - table.start_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                seconds = int(duration.total_seconds() % 60)
                info[2].controls[1].value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # 10 руб за каждую минуту
                cost = (duration.total_seconds() / 60) * table.current_tariff
                cost += sum(p['price'] for p in table.products)
                info[3].controls[1].value = f"{cost:.2f} ₽"
                
                products_list = info[4].content
                products_list.controls.clear()
                for product in table.products:
                    products_list.controls.append(
                        ft.Text(f"• {product['name']} - {product['price']:.2f} ₽", size=14, color="white")
                    )
                info[4].content.update()
            else:
                info[2].controls[1].value = "-"
                info[3].controls[1].value = "-"
                info[4].content.controls.clear()
                info[4].content.update()
        else:
            for row in info[:4]:
                row.controls[1].value = "-"
                row.controls[1].color = None
            info[4].content.controls.clear()
            info[4].content.update()
        
        # Обновляем меню
        self.table_info_panel.content.controls[0].controls[2].items = self._create_table_menu_items()
        self.table_info_panel.update()
        self.page.update()
    
    def change_table_status(self, status: TableStatus):
        if self.selected_table:
            self.selected_table.status = status
            
            if status == TableStatus.OCCUPIED:
                self.selected_table.start_time = datetime.datetime.now()
                self.selected_table.client_name = "Гость"
            else:
                self.selected_table.start_time = None
                self.selected_table.client_name = ""
                if status != TableStatus.RESERVED:
                    self.selected_table.products = []
            
            # Обновляем отображение стола
            self.selected_table.update_status_display()
            self.update_table_info(self.selected_table)
            self.show_snackbar(f"Статус стола {self.selected_table.number} изменен на {status.value}")
    
    def stop_rental(self, e):
        if not self.selected_table or self.selected_table.status != TableStatus.OCCUPIED:
            self.show_snackbar("Выберите занятый стол")
            return

        def close_dlg(e):
            dlg_modal.open = False
            self.page.update()
            # После закрытия диалога меняем статус стола
            self.change_table_status(TableStatus.AVAILABLE)

        duration = datetime.datetime.now() - self.selected_table.start_time
        total_seconds = duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        time_cost = (total_seconds / 60) * self.selected_table.current_tariff
        products_cost = sum(p['price'] for p in self.selected_table.products)
        total_cost = time_cost + products_cost
        
        receipt_content = ft.Column(
            controls=[
                ft.Text("Чек", size=24, weight=ft.FontWeight.BOLD, color="white"),
                ft.Divider(color=ft.colors.with_opacity(0.1, "#FFFFFF")),
                ft.Text(f"Стол: {self.selected_table.number}", size=18, color="white"),
                ft.Text(f"Время: {hours:02d}:{minutes:02d}:{seconds:02d}", size=16, color="white"),
                ft.Text(f"Тариф: {self.selected_table.current_tariff} руб/мин", size=16, color="white"),
                ft.Text(f"Стоимость времени: {time_cost:.2f} ₽", size=16, color="white"),
                ft.Text("Товары:", size=16, weight=ft.FontWeight.BOLD, color="white"),
                *[ft.Text(f"- {p['name']}: {p['price']:.2f} ₽", color="white") for p in self.selected_table.products],
                ft.Divider(color=ft.colors.with_opacity(0.1, "#FFFFFF")),
                ft.Text(f"Итого: {total_cost:.2f} ₽", size=20, weight=ft.FontWeight.BOLD, color="#4CAF50"),
            ],
            spacing=10
        )

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Оплата аренды"),
            content=ft.Container(
                content=receipt_content,
                padding=10
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def open_dlg_modal(e):
            self.page.dialog = dlg_modal
            dlg_modal.open = True
            self.page.update()

        open_dlg_modal(e)
    
    def remove_table(self, e):
        if not self.selected_table:
            self.show_snackbar("Выберите стол для удаления")
            return

        def confirm_delete(e):
            table_to_remove = self.selected_table
            self.tables.remove(table_to_remove)
            self.selected_table = None
            self.update_table_info(None)
            self.board_container.content.controls = self.tables
            self.board_container.update()
            self.show_snackbar(f"Удален стол {table_to_remove.number}")
            dlg_modal.open = False
            self.page.update()

        def close_dlg(e):
            dlg_modal.open = False
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Подтверждение удаления"),
            content=ft.Text(f"Вы уверены, что хотите удалить стол {self.selected_table.number}?"),
            actions=[
                ft.TextButton("Да", on_click=confirm_delete),
                ft.TextButton("Нет", on_click=close_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def open_dlg_modal(e):
            self.page.dialog = dlg_modal
            dlg_modal.open = True
            self.page.update()

        open_dlg_modal(e)
    
    def close_dialog(self):
        if hasattr(self.page, 'dialog'):
            self.page.dialog.open = False
            self.page.update()
    
    def show_snackbar(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor="#424242",
            behavior=ft.SnackBarBehavior.FLOATING,
            elevation=10,
            shape=ft.RoundedRectangleBorder(radius=10)
        )
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    app = BilliardApp(page)

ft.app(target=main)