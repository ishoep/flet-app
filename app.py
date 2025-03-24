import flet as ft
import datetime
import time
from typing import Optional, Dict, List
import math
import random
import json
import logging
from enum import Enum

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='billiard_app.log'
)

class TableStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    WAITING = "waiting"

class Language(Enum):
    RUSSIAN = "ru"
    UZBEK = "uz"
    ENGLISH = "en"

class BilliardTable(ft.Container):
    def __init__(self, number: int, status: TableStatus = TableStatus.AVAILABLE, **kwargs):
        super().__init__(**kwargs)
        self.number = number
        self.status = status
        self.width = 160
        self.height = 80
        self.border_radius = 8
        self.drag_interval = 10
        self.rotate_angle = 0
        self.animate = ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        self.on_hover = self.hover_animation
        self.on_click = self.select_table
        self.client_name = ""
        self.start_time = None
        self.current_tariff = 8.50
        self.products = []
        self.selected = False
        
        self.status_colors = {
            TableStatus.AVAILABLE: "#4CAF50",
            TableStatus.OCCUPIED: "#FF9800",
            TableStatus.MAINTENANCE: "#F44336",
            TableStatus.RESERVED: "#2196F3",
            TableStatus.WAITING: "#9C27B0"
        }
        
        self.bgcolor = "#8B4513"  # Wooden color for table
        self.border = ft.border.all(2, "#5D4037")
        self.content = self._create_table_content()
    
    def _create_table_content(self):
        return ft.Stack(
            [
                # Table surface
                ft.Container(
                    width=140,
                    height=60,
                    bgcolor="#2E7D32",
                    border_radius=6,
                    top=10,
                    left=10,
                    border=ft.border.all(2, "#1B5E20")
                ),
                # Table pockets
                self._create_pocket(10, 10),
                self._create_pocket(130, 10),
                self._create_pocket(10, 50),
                self._create_pocket(130, 50),
                # Table number
                ft.Container(
                    content=ft.Text(
                        f"{self.number}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color="white"
                    ),
                    width=30,
                    height=30,
                    bgcolor=self.status_colors.get(self.status, "#4CAF50"),
                    border_radius=15,
                    alignment=ft.alignment.center,
                    left=65,
                    top=25
                )
            ]
        )
    
    def _create_pocket(self, left, top):
        return ft.Container(
            width=16,
            height=16,
            bgcolor="black",
            border_radius=8,
            left=left,
            top=top
        )
    
    def hover_animation(self, e):
        self.scale = 1.05 if e.data == "true" else 1
        self.border = ft.border.all(2, "#3498DB" if e.data == "true" else "#5D4037")
        self.update()
    
    def select_table(self, e):
        self.selected = not self.selected
        self.border = ft.border.all(3, "#3498DB" if self.selected else "#5D4037")
        self.update()
        e.page.table_details_panel.update_details(self)
        e.page.update()

class ProductItem(ft.Container):
    def __init__(self, name: str, price: float, stock: int, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.price = price
        self.stock = stock
        self.width = 180
        self.height = 120
        self.bgcolor=ft.colors.WHITE
        self.border_radius=12
        self.padding=12
        self.border=ft.border.all(1, "#E0E0E0")
        self.animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        self.on_hover=self.hover_animation
        
        self.content=ft.Column(
            controls=[
                ft.Container(
                    height=50,
                    width=50,
                    border_radius=8,
                    bgcolor="#F5F5F5",
                    content=ft.Icon(ft.icons.LOCAL_BAR, color="#757575", size=24),
                    alignment=ft.alignment.center
                ),
                ft.Text(self.name, weight=ft.FontWeight.BOLD, size=16),
                ft.Row(
                    controls=[
                        ft.Text(f"${self.price:.2f}", color="#388E3C", size=14),
                        ft.Text(f"{self.stock} in stock", size=12, color="#757575")
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    width=150
                ),
                ft.Container(height=5),
                ft.ElevatedButton(
                    "Add",
                    width=120,
                    height=32,
                    style=ft.ButtonStyle(
                        padding=ft.Padding(0, 0, 0, 0),
                        bgcolor={"": "#42A5F5", "hovered": "#1E88E5"},
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5
        )
    
    def hover_animation(self, e):
        self.scale = 1.02 if e.data == "true" else 1
        self.border = ft.border.all(1, "#42A5F5" if e.data == "true" else "#E0E0E0")
        self.bgcolor = "#FAFAFA" if e.data == "true" else ft.colors.WHITE
        self.update()

class TableDetailsPanel(ft.Container):
    def __init__(self):
        super().__init__()
        self.width = 400
        self.height = 280
        self.bgcolor=ft.colors.WHITE
        self.border_radius=12
        self.padding=15
        self.border=ft.border.all(1, "#E0E0E0")
        self.elevation=3
        self.visible = False
        self.current_table = None
        
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Table Details", size=20, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            icon_size=20,
                            on_click=self.close_panel,
                            style=ft.ButtonStyle(
                                shape=ft.CircleBorder(),
                                padding=5
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=1, color="#E0E0E0"),
                ft.Column(
                    spacing=10,
                    controls=[
                        self._create_detail_row("Status:", "-"),
                        self._create_detail_row("Client:", "-"),
                        self._create_detail_row("Start Time:", "-"),
                        self._create_detail_row("Duration:", "-"),
                        self._create_detail_row("Tariff:", "-"),
                        self._create_detail_row("Current Cost:", "-"),
                        ft.Text("Products:", weight=ft.FontWeight.BOLD),
                        ft.Column([], scroll="auto", height=80)
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Start Session",
                            color="white",
                            bgcolor="#42A5F5",
                            height=36,
                            on_click=self.start_session
                        ),
                        ft.ElevatedButton(
                            "Close Bill",
                            color="white",
                            bgcolor="#EF5350",
                            height=36,
                            on_click=self.close_bill
                        )
                    ],
                    spacing=10
                )
            ],
            spacing=10
        )
    
    def _create_detail_row(self, label: str, value: str):
        return ft.Row(
            controls=[
                ft.Text(label, size=14, width=120, color="#616161"),
                ft.Text(value, size=14, weight=ft.FontWeight.W_500),
            ],
            spacing=10
        )
    
    def update_details(self, table: Optional[BilliardTable] = None):
        self.current_table = table
        self.visible = table is not None
        
        if table:
            details = self.content.controls[2].controls
            details[0].controls[1].value = table.status.value.capitalize()
            details[1].controls[1].value = table.client_name if table.client_name else "-"
            details[2].controls[1].value = table.start_time.strftime("%H:%M:%S") if table.start_time else "-"
            details[3].controls[1].value = self._get_duration(table) if table.start_time else "-"
            details[4].controls[1].value = f"${table.current_tariff}/hour"
            details[5].controls[1].value = f"${self._get_estimated_cost(table):.2f}" if table.start_time else "-"
            
            # Update products list
            products_list = self.content.controls[2].controls[7]
            products_list.controls.clear()
            for product in table.products:
                products_list.controls.append(
                    ft.Text(f"• {product['name']} (${product['price']:.2f})", size=12)
                )
            
            # Update buttons
            buttons = self.content.controls[3].controls
            buttons[0].text = "End Session" if table.status == TableStatus.OCCUPIED else "Start Session"
            buttons[0].bgcolor = "#EF5350" if table.status == TableStatus.OCCUPIED else "#42A5F5"
        
        self.update()
    
    def _get_duration(self, table: BilliardTable) -> str:
        duration = datetime.datetime.now() - table.start_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes = math.floor(remainder / 60)
        return f"{int(hours)}h {minutes:02d}m"
    
    def _get_estimated_cost(self, table: BilliardTable) -> float:
        duration = (datetime.datetime.now() - table.start_time).total_seconds() / 3600
        product_costs = sum(p['price'] for p in table.products)
        return (duration * table.current_tariff) + product_costs
    
    def start_session(self, e):
        if self.current_table:
            if self.current_table.status == TableStatus.AVAILABLE:
                self.current_table.status = TableStatus.OCCUPIED
                self.current_table.start_time = datetime.datetime.now()
                self.current_table.client_name = "Guest"
                logging.info(f"Session started on Table {self.current_table.number}")
            else:
                self.current_table.status = TableStatus.AVAILABLE
                self.current_table.start_time = None
                self.current_table.client_name = ""
                self.current_table.products = []
                logging.info(f"Session ended on Table {self.current_table.number}")
            
            self.current_table.selected = False
            self.current_table.border = ft.border.all(2, "#5D4037")
            self.current_table.update()
            self.update_details(None)
            e.page.update()
    
    def close_bill(self, e):
        if self.current_table and self.current_table.status == TableStatus.OCCUPIED:
            total = self._get_estimated_cost(self.current_table)
            logging.info(f"Bill closed for Table {self.current_table.number}. Total: ${total:.2f}")
            self.start_session(e)  # This will end the session
    
    def close_panel(self, e):
        if self.current_table:
            self.current_table.selected = False
            self.current_table.border = ft.border.all(2, "#5D4037")
            self.current_table.update()
        self.update_details(None)
        e.page.update()

class BoardSettingsPanel(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.width = 300
        self.bgcolor=ft.colors.WHITE
        self.border_radius=12
        self.padding=15
        self.border=ft.border.all(1, "#E0E0E0")
        self.elevation=3
        self.visible = False
        
        self.board_colors = [
            {"name": "Green", "value": "#E8F5E9"},
            {"name": "Blue", "value": "#E3F2FD"},
            {"name": "Gray", "value": "#F5F5F5"},
            {"name": "Wood", "value": "#EFEBE9"},
        ]
        
        self.content = ft.Column(
            controls=[
                ft.Text("Board Settings", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1, color="#E0E0E0"),
                ft.Text("Board Color:", size=14, color="#616161"),
                ft.Row(
                    controls=[
                        ft.Container(
                            width=40,
                            height=40,
                            border_radius=20,
                            bgcolor=color["value"],
                            border=ft.border.all(2, "#BDBDBD"),
                            on_click=lambda e, c=color["value"]: self.change_board_color(c)
                        ) for color in self.board_colors
                    ],
                    spacing=10
                ),
                ft.Text("Table Layout:", size=14, color="#616161"),
                ft.ElevatedButton(
                    "Reset Layout",
                    icon=ft.icons.RESTORE,
                    on_click=self.reset_layout
                )
            ],
            spacing=15
        )
    
    def change_board_color(self, color):
        self.page.board_container.bgcolor = color
        self.page.update()
        logging.info(f"Board color changed to {color}")
    
    def reset_layout(self, e):
        for i, table in enumerate(self.page.tables):
            table.left = 50 + (i % 3) * 200
            table.top = 50 + (i // 3) * 150
            table.update()
        logging.info("Table layout reset to default")

class BilliardApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Billiard Hub Pro"
        self.page.window_width = 1366
        self.page.window_height = 768
        self.page.window_min_width = 1024
        self.page.window_min_height = 600
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.fonts = {
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
            "Montserrat": "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap"
        }
        self.page.theme = ft.Theme(
            font_family="Roboto",
            color_scheme=ft.ColorScheme(
                primary="#42A5F5",
                secondary="#66BB6A",
                surface=ft.colors.WHITE,
                background="#FAFAFA"
            )
        )
        
        self.current_view = "tables"
        self.language = Language.RUSSIAN
        self.tables = []
        self.products = [
            {"name": "Beer", "price": 5.00, "stock": 24},
            {"name": "Soda", "price": 2.50, "stock": 36},
            {"name": "Water", "price": 1.50, "stock": 48},
            {"name": "Snacks", "price": 3.00, "stock": 20},
            {"name": "Coffee", "price": 2.00, "stock": 30},
            {"name": "Tea", "price": 1.50, "stock": 40},
        ]
        
        self.setup_ui()
        self.update_clock()
    
    def setup_ui(self):
        # Navbar
        self.navbar = ft.Container(
            height=70,
            bgcolor=ft.colors.WHITE,
            padding=ft.padding.symmetric(horizontal=25),
            border=ft.border.only(bottom=ft.border.BorderSide(1, "#E0E0E0")),
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.SPORTS_BAR, color="#42A5F5", size=28),
                            ft.Text("Billiard Hub", size=24, weight=ft.FontWeight.BOLD, font_family="Montserrat"),
                        ],
                        spacing=10
                    ),
                    ft.Container(expand=True),
                    ft.PopupMenuButton(
                        icon=ft.icons.TRANSLATE,
                        items=[
                            ft.PopupMenuItem(text="Русский", on_click=lambda e: self.change_language(Language.RUSSIAN)),
                            ft.PopupMenuItem(text="O'zbek", on_click=lambda e: self.change_language(Language.UZBEK)),
                            ft.PopupMenuItem(text="English", on_click=lambda e: self.change_language(Language.ENGLISH)),
                        ]
                    ),
                    ft.IconButton(
                        icon=ft.icons.NOTIFICATIONS_OUTLINED,
                        icon_size=22,
                        style=ft.ButtonStyle(
                            shape=ft.CircleBorder(),
                            padding=8
                        )
                    ),
                    ft.IconButton(
                        icon=ft.icons.SETTINGS_OUTLINED,
                        icon_size=22,
                        style=ft.ButtonStyle(
                            shape=ft.CircleBorder(),
                            padding=8
                        )
                    ),
                    ft.Container(
                        width=180,
                        height=40,
                        bgcolor="#F5F5F5",
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=12),
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.ACCOUNT_CIRCLE_OUTLINED, size=20),
                                ft.Text("Administrator", size=14),
                            ],
                            spacing=10
                        )
                    ),
                    self.clock_display()
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            )
        )
        
        # Sidebar
        self.sidebar = ft.Container(
            width=240,
            bgcolor=ft.colors.WHITE,
            padding=ft.padding.only(top=20),
            border=ft.border.only(right=ft.border.BorderSide(1, "#E0E0E0")),
            content=ft.Column(
                controls=[
                    self._create_nav_item("Tables", ft.icons.TABLE_RESTAURANT_OUTLINED, "tables"),
                    self._create_nav_item("Service", ft.icons.LOCAL_BAR_OUTLINED, "service"),
                    self._create_nav_item("Reports", ft.icons.INSERT_CHART_OUTLINED, "reports"),
                    self._create_nav_item("Settings", ft.icons.SETTINGS_OUTLINED, "settings"),
                    ft.Container(expand=True),
                    ft.Divider(height=1, color="#E0E0E0"),
                    ft.Container(
                        padding=20,
                        content=ft.Column(
                            controls=[
                                ft.Text("SYSTEM STATUS", size=12, color="#757575", weight=ft.FontWeight.BOLD),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            width=10,
                                            height=10,
                                            border_radius=5,
                                            bgcolor="#4CAF50"
                                        ),
                                        ft.Text("All systems normal", size=12, color="#616161"),
                                    ],
                                    spacing=8
                                )
                            ],
                            spacing=5
                        )
                    )
                ],
                spacing=0
            )
        )
        
        # Table details panel
        self.table_details_panel = TableDetailsPanel()
        
        # Board settings panel
        self.board_settings_panel = BoardSettingsPanel(self.page)
        
        # Main content area
        self.board_container = ft.Container(
            expand=True,
            bgcolor="#E8F5E9",  # Default green board color
            padding=20,
            border_radius=12,
            border=ft.border.all(1, "#E0E0E0")
        )
        
        self.main_content = ft.Container(
            expand=True,
            bgcolor="#FAFAFA",
            padding=ft.padding.symmetric(horizontal=25, vertical=20),
            content=self.create_tables_view()
        )
        
        # Layout
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
    
    def change_language(self, language: Language):
        self.language = language
        # In a complete implementation, this would update all UI text
        logging.info(f"Language changed to {language.value}")
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Language set to {language.name}"),
            action="OK"
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _create_nav_item(self, title: str, icon: str, view_name: str):
        return ft.Container(
            width=240,
            height=50,
            padding=ft.padding.only(left=25),
            on_click=lambda e: self.switch_view(view_name),
            bgcolor="#E3F2FD" if self.current_view == view_name else "transparent",
            border_radius=ft.border_radius.only(top_right=6, bottom_right=6),
            content=ft.Row(
                controls=[
                    ft.Icon(icon, color="#42A5F5" if self.current_view == view_name else "#757575", size=20),
                    ft.Text(title, color="#424242" if self.current_view == view_name else "#616161", size=15),
                ],
                spacing=15
            )
        )
    
    def clock_display(self):
        self.clock = ft.Text(
            datetime.datetime.now().strftime("%H:%M:%S"),
            size=16,
            weight=ft.FontWeight.W_600,
        )
        self.date_display = ft.Text(
            datetime.datetime.now().strftime("%d %b, %Y"),
            size=14,
            color="#616161"
        )
        return ft.Container(
            content=ft.Column(
                controls=[self.clock, self.date_display],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.END
            ),
            padding=ft.padding.only(left=20)
        )
    
    def update_clock(self):
        while True:
            time.sleep(1)
            self.clock.value = datetime.datetime.now().strftime("%H:%M:%S")
            self.date_display.value = datetime.datetime.now().strftime("%d %b, %Y")
            self.clock.update()
            self.date_display.update()
    
    def switch_view(self, view_name):
        self.current_view = view_name
        self.sidebar.content.controls = [
            self._create_nav_item("Tables", ft.icons.TABLE_RESTAURANT_OUTLINED, "tables"),
            self._create_nav_item("Service", ft.icons.LOCAL_BAR_OUTLINED, "service"),
            self._create_nav_item("Reports", ft.icons.INSERT_CHART_OUTLINED, "reports"),
            self._create_nav_item("Settings", ft.icons.SETTINGS_OUTLINED, "settings"),
            ft.Container(expand=True),
            ft.Divider(height=1, color="#E0E0E0"),
            self.sidebar.content.controls[-1]
        ]
        
        if view_name == "tables":
            self.main_content.content = self.create_tables_view()
        elif view_name == "service":
            self.main_content.content = self.create_service_view()
        elif view_name == "reports":
            self.main_content.content = self.create_reports_view()
        elif view_name == "settings":
            self.main_content.content = self.create_settings_view()
        
        self.sidebar.update()
        self.main_content.update()
    
    def create_tables_view(self):
        # Statistics row
        stats = ft.Container(
            height=110,
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            padding=15,
            border=ft.border.all(1, "#E0E0E0"),
            content=ft.Row(
                controls=[
                    self._create_stat_card("Total Tables", "8", "#42A5F5", ft.icons.TABLE_RESTAURANT),
                    self._create_stat_card("Occupied", "3", "#EF5350", ft.icons.ACCESS_TIME),
                    self._create_stat_card("Available", "4", "#66BB6A", ft.icons.CHECK_CIRCLE),
                    self._create_stat_card("Reserved", "1", "#AB47BC", ft.icons.BOOKMARK),
                    self._create_stat_card("Today's Revenue", "$342.75", "#26A69A", ft.icons.ATTACH_MONEY),
                ],
                spacing=15
            )
        )
        
        # Board with tables
        self.tables_grid = ft.GestureDetector(
            content=ft.Stack(
                controls=self.create_tables(),
                width=self.page.width - 265,
                height=self.page.height - 350
            ),
            drag_interval=10,
            on_pan_update=self.drag_tables
        )
        
        self.board_container.content = self.tables_grid
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Tables Management", size=22, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.icons.PALETTE_OUTLINED,
                            tooltip="Board Settings",
                            on_click=lambda e: self.toggle_board_settings()
                        )
                    ]
                ),
                ft.Container(height=10),
                stats,
                ft.Container(height=15),
                ft.Row(
                    controls=[
                        self.board_container,
                        ft.Column(
                            controls=[
                                self.table_details_panel,
                                self.board_settings_panel
                            ],
                            spacing=15
                        )
                    ],
                    spacing=15,
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )
    
    def toggle_board_settings(self):
        self.board_settings_panel.visible = not self.board_settings_panel.visible
        self.board_settings_panel.update()
    
    def create_tables(self):
        if not self.tables:
            self.tables = [
                BilliardTable(number=1, status=TableStatus.AVAILABLE, left=50, top=50),
                BilliardTable(number=2, status=TableStatus.OCCUPIED, left=250, top=50),
                BilliardTable(number=3, status=TableStatus.AVAILABLE, left=450, top=50),
                BilliardTable(number=4, status=TableStatus.MAINTENANCE, left=50, top=180),
                BilliardTable(number=5, status=TableStatus.AVAILABLE, left=250, top=180),
                BilliardTable(number=6, status=TableStatus.RESERVED, left=450, top=180),
                BilliardTable(number=7, status=TableStatus.AVAILABLE, left=50, top=310),
                BilliardTable(number=8, status=TableStatus.WAITING, left=250, top=310),
            ]
        return self.tables
    
    def drag_tables(self, e: ft.DragUpdateEvent):
        for table in self.tables:
            if table.scale == 1.05:  # Only move the hovered table
                table.left = max(20, min(table.left + e.delta_x, self.page.width - table.width - 300))
                table.top = max(20, min(table.top + e.delta_y, self.page.height - table.height - 250))
                table.update()
    
    def _create_stat_card(self, title: str, value: str, color: str, icon):
        return ft.Container(
            width=180,
            height=80,
            bgcolor="#FAFAFA",
            border_radius=10,
            padding=12,
            border=ft.border.all(1, "#E0E0E0"),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=lambda e: self._animate_stat_card(e),
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=50,
                        height=50,
                        bgcolor=f"{color}20",
                        border_radius=25,
                        content=ft.Icon(icon, color=color, size=20),
                        alignment=ft.alignment.center
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=12, color="#616161"),
                            ft.Text(value, size=18, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=3
                    )
                ],
                spacing=15
            )
        )
    
    def _animate_stat_card(self, e):
        e.control.bgcolor = "#F5F5F5" if e.data == "true" else "#FAFAFA"
        e.control.update()
    
    def create_service_view(self):
        product_grid = ft.GridView(
            runs_count=4,
            max_extent=200,
            child_aspect_ratio=0.9,
            spacing=15,
            run_spacing=15,
        )
        
        for product in self.products:
            product_grid.controls.append(
                ProductItem(
                    name=product["name"],
                    price=product["price"],
                    stock=product["stock"],
                    on_click=lambda e, p=product: self.add_product_to_table(p)
                )
            )
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Service Menu", size=22, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.SearchBar(
                            width=300,
                            height=40,
                            bar_hint_text="Search products...",
                            bar_bgcolor=ft.colors.WHITE,
                            bar_overlay_color=ft.colors.WHITE,
                        )
                    ]
                ),
                ft.Container(height=15),
                ft.Text("Select a product to add to an occupied table", size=13, color="#757575"),
                ft.Container(height=15),
                ft.Container(
                    content=product_grid,
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )
    
    def add_product_to_table(self, product):
        occupied_tables = [t for t in self.tables if t.status == TableStatus.OCCUPIED]
        if occupied_tables:
            # In a real app, this would show a dialog to select a table
            table = random.choice(occupied_tables)
            table.products.append(product)
            logging.info(f"Added {product['name']} to Table {table.number}")
            
            if table.selected:
                self.table_details_panel.update_details(table)
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Added {product['name']} to Table {table.number}"),
                action="OK"
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def create_reports_view(self):
        return ft.Column(
            controls=[
                ft.Text("Analytics & Reports", size=22, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Revenue Report", size=18),
                            ft.Image(src="https://via.placeholder.com/800x400?text=Revenue+Chart"),
                            ft.Text("Table Utilization", size=18),
                            ft.Image(src="https://via.placeholder.com/800x400?text=Utilization+Chart"),
                        ],
                        spacing=20
                    ),
                    bgcolor=ft.colors.WHITE,
                    border_radius=12,
                    padding=20,
                    border=ft.border.all(1, "#E0E0E0"),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )
    
    def create_settings_view(self):
        return ft.Column(
            controls=[
                ft.Text("Settings", size=22, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                ft.Container(
                    content=ft.Tabs(
                        tabs=[
                            ft.Tab(
                                text="General",
                                content=ft.Column(
                                    controls=[
                                        ft.ListTile(
                                            title=ft.Text("Language"),
                                            subtitle=ft.Text("Change application language"),
                                            trailing=ft.PopupMenuButton(
                                                icon=ft.icons.ARROW_DROP_DOWN,
                                                items=[
                                                    ft.PopupMenuItem(text="Русский", on_click=lambda e: self.change_language(Language.RUSSIAN)),
                                                    ft.PopupMenuItem(text="O'zbek", on_click=lambda e: self.change_language(Language.UZBEK)),
                                                    ft.PopupMenuItem(text="English", on_click=lambda e: self.change_language(Language.ENGLISH)),
                                                ]
                                            )
                                        ),
                                        ft.Divider(),
                                        ft.ListTile(
                                            title=ft.Text("Theme"),
                                            subtitle=ft.Text("Light/Dark mode"),
                                            trailing=ft.Switch(
                                                value=True,
                                                on_change=lambda e: self.toggle_theme(e.control.value)
                                            )
                                        )
                                    ],
                                    spacing=0
                                )
                            ),
                            ft.Tab(
                                text="Tariffs",
                                content=ft.Column(
                                    controls=[
                                        ft.Text("Tariff settings will be here", size=16)
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            ),
                            ft.Tab(
                                text="Users",
                                content=ft.Column(
                                    controls=[
                                        ft.Text("User management will be here", size=16)
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                )
                            )
                        ]
                    ),
                    bgcolor=ft.colors.WHITE,
                    border_radius=12,
                    padding=20,
                    border=ft.border.all(1, "#E0E0E0"),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )
    
    def toggle_theme(self, is_light):
        self.page.theme_mode = ft.ThemeMode.LIGHT if is_light else ft.ThemeMode.DARK
        logging.info(f"Theme changed to {'light' if is_light else 'dark'} mode")
        self.page.update()

def main(page: ft.Page):
    app = BilliardApp(page)

ft.app(target=main)