import flet as ft
import requests

API_URL = "http://127.0.0.1:5000/api/notes"

def main(page: ft.Page):
    current_task_payload = {}

    page.title = "My Advanced Todo App"
    page.theme_mode = "light" 
    page.window_width = 400
    page.window_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER

    tasks_view = ft.Column(spacing=10, scroll="adaptive")
    
    main_title = ft.TextField(label="Task Title", autofocus=True)
    main_desc = ft.TextField(label="Task Description", multiline=True)
    main_cat = ft.Dropdown(label="Category", value="Personal", options=[
        ft.dropdown.Option("Personal"),
        ft.dropdown.Option("Work"),
        ft.dropdown.Option("Health"),
        ft.dropdown.Option("Shopping"),
        ft.dropdown.Option("Finance"),
        ft.dropdown.Option("Home"),
        ft.dropdown.Option("Other")
    ])
    main_priority = ft.Dropdown(label="Priority", value="Low", options=[
        ft.dropdown.Option("Low"),
        ft.dropdown.Option("Medium"),
        ft.dropdown.Option("High")
    ])

    sub_title = ft.TextField(label="Subtask Title")
    sub_desc = ft.TextField(label="Subtask Description", multiline=True)
    sub_priority = ft.Dropdown(label="Priority", value="Low", options=[
        ft.dropdown.Option("Low"),
        ft.dropdown.Option("Medium"),
        ft.dropdown.Option("High")
    ])

    def close_all_dialogs():
        add_task_dialog.open = False
        prompt_subtask_dialog.open = False
        subtask_form_dialog.open = False
        page.update()

    def finalize_and_send():
        try:
            res = requests.post(API_URL, json=current_task_payload, timeout=5)
            if res.status_code in [200, 201]:
                load_tasks()
                close_all_dialogs()
                current_task_payload.clear()
        except Exception as ex:
            print(f"Final Save Error: {ex}")

    def add_subtask(e):
        new_sub = {
            "title": sub_title.value,
            "description": sub_desc.value,
            "priority": sub_priority.value,
            "category": current_task_payload["category"]
        }
        current_task_payload["subtasks"].append(new_sub)

        sub_title.value = ""
        sub_desc.value = ""
        sub_priority.value = "Low"

        subtask_form_dialog.open = False
        prompt_subtask_dialog.open = True
        page.update()

    def start_sub_flow(e):
        if not main_title.value:
            main_title.error_text= "Title can not be empty!"
            page.update()
            return
        
        current_task_payload.update({
            "title": main_title.value,
            "description": main_desc.value,
            "category": main_cat.value,
            "priority": main_priority.value,
            "subtasks": []
        })

        main_title.value = ""
        main_desc.value = ""

        add_task_dialog.open = False
        prompt_subtask_dialog.open = True
        page.update()

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
                        is_task_done = note.get('is_done', False)
                        cb = ft.Checkbox(value=is_task_done)

                        def on_checkbox_change(e, tid=note['id'], title=note['title'], ref=cb):
                            if ref.value == True: # Fixed typo from 'rev' to 'ref'
                                confirm_completion(tid, title, ref)
                            else:
                                update_task(tid, False)

                        cb.on_change = on_checkbox_change
                        
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
                                        leading=cb,
                                        title=ft.Text(
                                            note['title'], 
                                            weight="bold", 
                                            spans=[ft.TextSpan(style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH))] if is_task_done else []
                                        ),
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
        title=ft.Text("Add Main Task"),
        content=ft.Column([main_title, main_desc, main_cat, main_priority]),
        actions=[
            ft.TextButton("Cancel", on_click=lambda _: close_all_dialogs()),
            ft.TextButton("Save", on_click=start_sub_flow)
        ])

    prompt_subtask_dialog = ft.AlertDialog(
        title=ft.Text("Subtasks"),
        content=ft.Text("Would you like to add a subtask to this task?"),
        actions=[
            ft.TextButton("No", "Finish", on_click=lambda _: finalize_and_send()),
            ft.Button("Yes", "Add One", on_click=lambda _: (
                setattr(prompt_subtask_dialog, "open", False),
                setattr(subtask_form_dialog, "open", True),
                page.update()
            ))
        ]
    )

    subtask_form_dialog = ft.AlertDialog(
        title=ft.Text("Add Subtask"),
        content=ft.Column([sub_title, sub_desc, sub_priority], tight=True),
        actions=[
            ft.TextButton("Discard & Finish", on_click=lambda _: finalize_and_send()),
            ft.Button("Add Another", on_click=add_subtask)
        ]
    )

    page.overlay.extend([add_task_dialog, prompt_subtask_dialog, subtask_form_dialog])

    #page.overlay.append(add_task_dialog)
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
            margin=ft.Margin.only(top=20, bottom=10)
        ),
        ft.Button("Refresh List", icon="refresh", on_click= lambda _: load_tasks()),
        ft.Divider(),
        tasks_view
    )
    load_tasks()

    def confirm_completion(task_id, task_title, checkbox_ref):
        complete_dialog = ft.AlertDialog()
        
        def undo(e):
            try:
                update_task(task_id, False)
                if page.snack_bar:
                    page.snack_bar.open = False
                    page.update()
            except Exception as ex:
                print(f"Undo Error: {ex}")

        def handle_yes(e):
            try:
                res = requests.put(f"{API_URL}/{task_id}", json={'is_done': True}, timeout=5)
                if res.status_code == 200:
                    complete_dialog.open = False
                    load_tasks()
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"'{task_title}' marked as completed."),
                        action='UNDO',
                        on_action=undo,
                        duration=5000       
                    )
                    page.snack_bar.open = True
                    page.update()
            except Exception as ex:
                print(f"Completion Error: {ex}")

        def handle_no(e):
            checkbox_ref.value = False
            complete_dialog.open = False
            page.update()

        complete_dialog.title = ft.Text("Confirm Completion")
        complete_dialog.content = ft.Text(f"Mark '{task_title}' as completed?")
        complete_dialog.actions = [
            ft.TextButton("No", on_click=handle_no),
            ft.Button("Yes", on_click=handle_yes, bgcolor="green", color="white")
        ]
        page.overlay.append(complete_dialog)
        complete_dialog.open = True
        page.update()

    def update_task(task_id, status):
        try:
            requests.put(f"{API_URL}/{task_id}", json={'is_done': status}, timeout=5)
            load_tasks()
            page.update()
        except Exception as ex:
            print(f"Update Error: {ex}")


if __name__ == "__main__":
    ft.run(main)