import flet as ft
from datetime import datetime
import threading
import time

# === Обновление времени и даты ===
def update_datetime(label: ft.Text):
    def run():
        while True:
            now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            label.value = now
            label.update()
            time.sleep(1)
    threading.Thread(target=run, daemon=True).start()

# === Карточка статистики ===
def stat_card(title, value, icon):
    return ft.Container(
        content=ft.Row([
            ft.Icon(name=icon, size=30, color=ft.Colors.PURPLE_700),
            ft.Column([
                ft.Text(value, size=22, weight="bold"),
                ft.Text(title, size=14, color=ft.Colors.GREY_600),
            ], spacing=2)
        ], alignment="start"),
        padding=10,
        width=200,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2))
    )

# === View "Столы" ===
def tables_view():
    return ft.Column([
        ft.Text("📊 Краткая статистика", size=18, weight="bold"),
        ft.Row([
            stat_card("Активные столы", "4", ft.Icons.TABLE_RESTAURANT),
            stat_card("Свободные столы", "2", ft.Icons.CHECK_CIRCLE),
            stat_card("Занятые столы", "2", ft.Icons.HOURGLASS_BOTTOM),
            stat_card("Сервисов добавлено", "8", ft.Icons.ADD_SHOPPING_CART),
        ], wrap=True, spacing=15),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        ft.Text("🎱 Доска со столами (будущий drag & rotate)", size=18, weight="bold"),
        ft.Container(
            content=ft.GridView(
                runs_count=3,
                controls=[
                    ft.Container(
                        content=ft.Text(f"Стол #{i+1}", weight="bold"),
                        alignment=ft.alignment.center,
                        bgcolor=ft.Colors.PURPLE_100,
                        border_radius=8,
                        padding=20,
                        on_click=lambda e: print(f"Выбран стол {e.control.content.value}")
                    ) for i in range(6)
                ],
                spacing=10,
                run_spacing=10,
                expand=True
            ),
            padding=10
        )
    ], scroll=ft.ScrollMode.AUTO)

# === View "Сервис" ===
def service_view():
    return ft.Column([
        ft.Text("🛒 Добавление сервисов к столам", size=18, weight="bold"),
        ft.Text("Выберите продукты для добавления к активным столам:", size=14),
        ft.Row([
            ft.ElevatedButton("Кофе ☕", icon=ft.Icons.COFFEE, on_click=lambda e: print("Добавлен Кофе")),
            ft.ElevatedButton("Пиво 🍺", icon=ft.Icons.LOCAL_BAR, on_click=lambda e: print("Добавлено Пиво")),
            ft.ElevatedButton("Снеки 🍿", icon=ft.Icons.FASTFOOD, on_click=lambda e: print("Добавлены Снеки")),
        ], spacing=10)
    ], scroll=ft.ScrollMode.AUTO)

# === Главная функция ===
def main(page: ft.Page):
    page.title = "Billiard Management"
    page.bgcolor = ft.Colors.GREY_100
    page.window_width = 1100
    page.window_height = 700

    # Текущая дата и время (вверху справа)
    clock_text = ft.Text("", size=14, weight="bold", color=ft.Colors.GREY_800)
    update_datetime(clock_text)

    # Навигационное меню слева
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=ft.Colors.WHITE,
        extended=True,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.TABLE_RESTAURANT, label="Столы"),
            ft.NavigationRailDestination(icon=ft.Icons.SHOPPING_CART, label="Сервис"),
        ],
    )

    # Контейнер, куда будет подгружаться контент
    content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    # Обработка переключения навигации
    def nav_click(e):
        selected_index = rail.selected_index
        content_area.controls.clear()
        if selected_index == 0:
            content_area.controls.append(tables_view())
        elif selected_index == 1:
            content_area.controls.append(service_view())
        page.update()

    rail.on_change = nav_click

    # Верхняя панель
    topbar = ft.Container(
        content=ft.Row([
            ft.Text("🎱 Billiard Management", size=20, weight="bold", color=ft.Colors.PURPLE_700),
            ft.Container(expand=True),
            clock_text
        ], alignment="center", vertical_alignment="center"),
        padding=10,
        bgcolor=ft.Colors.WHITE,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_300, offset=ft.Offset(0, 2)),
    )

    # Общий Layout
    layout = ft.Row([
        rail,
        ft.VerticalDivider(width=1),
        ft.Column([
            topbar,
            content_area
        ], expand=True)
    ], expand=True)

    page.add(layout)

    # Загрузка стартового контента
    nav_click(None)

ft.app(target=main)
