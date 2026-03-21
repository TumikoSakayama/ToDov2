import flet as ft
import requests

API_URL = "http://localhost:5000/api/notes"

def main(page: ft.Page):
    page.title = "My To-Do App version 2.0"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400
    page.window.height = 600

    tasks_view = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE)

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
                                content=ft.Column([
                                    ft.ListTile(
                                        title=ft.Text(note['title'], weight="bold"),
                                        subtitle=ft.Text(f"Priority: {note['priority']}"),
                                        trailing=ft.Checkbox(value=note.get('is_done', False))
                                    ),
                                ], spacing=5),
                                padding=10
                            )
                        )        
                    )
                page.update()
        except Exception as e:
            print(f"Error connecting to backend: {e}")

    refresh_button = ft.ElevatedButton("Refresh Tasks", on_click=lambda _: load_tasks())

    page.add(
        ft.Text("My To-Do List", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
        refresh_button,
        tasks_view
    )

    load_tasks()

if __name__ == "__main__":
    ft.app(target=main)