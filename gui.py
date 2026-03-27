import flet as ft
import requests
#from flet import icons, Colors

API_URL = "http://127.0.0.1:5000/api/notes"

def main(page: ft.Page):
    page.title = "My Advanced Todo App"
    page.theme_mode = "light" 
    page.window_width = 400
    page.window_height = 600

    fab = ft.FloatingActionButton(
        content=ft.Container(
            content=ft.Text("+", size=25, weight="bold", color="white"),
            alignment=ft.Alignment(0,0),
        ),
        bgcolor="blue",
        on_click= lambda _: (setattr(add_task_dialog, "open", True), page.update())
    )

    tasks_view = ft.Column(spacing=10, scroll="adaptive")
    new_task_title = ft.TextField(label="Task Title", autofocus=True)

    def load_tasks():
        tasks_view.controls.clear()
        tasks_view.controls.append(ft.Text("Loading tasks...", color="green"))
        page.update()

        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                notes = response.json()
                #tasks_view.controls.clear()

            for note in notes:
                current_id = note['id']

                def delete_task(e, task_id=current_id):
                    try:
                        res = requests.delete(f"{API_URL}/{task_id}", timeout=5)
                        if res.status_code == 200:
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
                                    content=ft.Text("X", color="red", weight="bold"),
                                    on_click=delete_task,
                                    tooltip="Delete Task"
                                ),
                            ),
                            padding=10
                        )   
                    )
                )

        except Exception as e:
            print(f"Connection Error: {e}")

    def save_tasks(e):
        if new_task_title.value:
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

    page.floating_action_button = fab
    
    page.add(
        ft.Text("My Tasks", size=30, weight="bold"),
        ft.ElevatedButton("Refresh", icon="refresh", on_click= lambda _: load_tasks()),
        tasks_view
    )

    load_tasks()
    page.update()


if __name__ == "__main__":
    ft.app(target=main)