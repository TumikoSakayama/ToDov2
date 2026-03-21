import flet as ft
import requests

API_URL = "http://127.0.0.1:5000/api/notes"

def main(page: ft.Page):
    page.title = "My Advanced Todo App"
    page.theme_mode = "light" # Using string instead of ft.ThemeMode
    page.window_width = 400
    page.window_height = 600

    tasks_view = ft.Column(spacing=10, scroll="adaptive")

    def load_tasks():
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                notes = response.json()
                tasks_view.controls.clear()
                for note in notes:
                    tasks_view.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.ListTile(
                                    title=ft.Text(note['title'], weight="bold"),
                                    subtitle=ft.Text(f"Priority: {note.get('priority', 0)}"),
                                    leading=ft.Checkbox(value=note.get('is_done', False)),
                                    # Using string "delete"
                                    trailing=ft.IconButton(icon="delete", icon_color="red"),
                                ),
                                padding=10
                            )
                        )
                    )
                page.update()
        except Exception as e:
            print(f"Connection Error: {e}")


    # Using strings for icon and color
    refresh_button = ft.ElevatedButton(
        "Refresh Tasks", 
        icon="refresh",
        color="white",
        bgcolor="blue",
        on_click=lambda _: load_tasks()
    )

    page.add(
        ft.Text("My Tasks", size=30, weight="bold"),
        refresh_button,
        tasks_view
    )

    load_tasks()

   
    page.floating_action_button = ft.FloatingActionButton(
        icon="add",
        bgcolor="blue",
        on_click=lambda _: print("Button Clicked!") # Simplified for testing
    )
    page.update()


if __name__ == "__main__":
    ft.run(main)