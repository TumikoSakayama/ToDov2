import flet as ft
import requests

API_URL = "http://127.0.0.1:5000/api/notes"

def main(page: ft.Page):
    page.title = "My Advanced Todo App"
    page.theme_mode = "light" 
    page.window_width = 400
    page.window_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER

    tasks_view = ft.Column(spacing=10, scroll="adaptive")
    new_task_title = ft.TextField(label="Task Title", autofocus=True)

    def load_tasks():
        try:
            response = requests.get(API_URL, timeout=5)
            tasks_view.controls.clear()

            if response.status_code == 200:
                notes = response.json()

                if not notes:
                    tasks_view.controls.append(
                        ft.Container(
                            content=ft.Text("No tasks found. Tap + to start!", size=16, color="grey"),
                            padding=20,
                            alignment=ft.Alignment(0,0)
                        )
                    )
                else:
                    for note in notes:
                        current_id = note['id']
                        def delete_clicked(e, id=current_id):
                            try:
                                requests.delete(f"{API_URL}/{id}", timeout=5)
                                load_tasks()
                            except Exception as ex:
                                print(f"Delete Error: {ex}")

                        tasks_view.controls.append(
                            ft.Card(
                                content=ft.Container(
                                    content=ft.ListTile(
                                        title=ft.Text(note['title'], weight="bold"),
                                        subtitle=ft.Text(f"Priority: {note.get('priority', 0)}"),
                                        trailing=ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color="red",
                                            on_click=delete_clicked
                                        ),
                                    ),
                                    padding=5
                                )   
                            )
                        )
            page.update()
        except Exception as e:
            print(f"Connection / Logic Error: {e}")
            tasks_view.controls.append(ft.Text("Could not connect to server.", color="red"))
            page.update()

    def save_tasks(e):
        if not new_task_title.value:
            new_task_title.error_text= "Title can not be empty!"
            page.update()
            return
        try:
            requests.post(API_URL, json={'title': new_task_title.value}, timeout=5)
            new_task_title.value = ""
            add_task_dialog.open = False
            load_tasks()
            page.update()
        except Exception as ex:
            print(f"Save Error: {ex}")

    add_task_dialog= ft.AlertDialog(
        title=ft.Text("Add a New Task"),
        content=new_task_title,
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: (setattr(add_task_dialog, "open", False), page.update())),
            ft.TextButton("Save", on_click=save_tasks)
        ])

    page.overlay.append(add_task_dialog)
    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Container(
            content=ft.Text("+", size=22, weight="bold", color="white"),
            alignment=ft.Alignment(0,0),
        ),
        bgcolor="blue",
        on_click = lambda _: (setattr(add_task_dialog, "open", True), page.update())
    )
    
    page.add(
        ft.Container(
            content=ft.Text("My Tasks", size=28, weight="bold"),
            margin=ft.margin.only(top=20, bottom=10)
        ),
        ft.ElevatedButton("Refresh List", icon="refresh", on_click= lambda _: load_tasks()),
        ft.Divider(),
        tasks_view
    )
    load_tasks()

if __name__ == "__main__":
    ft.app(target=main)