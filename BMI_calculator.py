import flet as ft
import datetime
import xml.etree.ElementTree as ET
import os
import sys
import argparse

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main(page: ft.Page):
    page.title = "Rozszerzony Kalkulator BMI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    if not page.web:
        page.window.resizable = False
        page.window.width = 400
        page.window.height = 600

    def load_history():
        if os.path.exists("bmi_history.xml"):
            tree = ET.parse("bmi_history.xml")
            root = tree.getroot()
            history = []
            for entry in root.findall('entry'):
                history.append({
                    'date': entry.find('date').text,
                    'bmi': float(entry.find('bmi').text),
                    'category': entry.find('category').text,
                    'weight': float(entry.find('weight').text),
                    'height': float(entry.find('height').text),
                    'age': int(entry.find('age').text),
                    'gender': entry.find('gender').text
                })
            return history
        return []

    def save_history(history_data):
        root = ET.Element("history")
        for entry in history_data[-10:]:
            entry_elem = ET.SubElement(root, "entry")
            for key, value in entry.items():
                elem = ET.SubElement(entry_elem, key)
                elem.text = str(value)
        tree = ET.ElementTree(root)
        tree.write("bmi_history.xml")

    history_data = load_history()

    def calculate_bmi(e):
        nonlocal history_data
        try:
            weight = float(weight_input.value)
            height = float(height_input.value) / 100  # konwersja cm na m
            age = int(age_input.value)
            gender = gender_dropdown.value

            bmi = weight / (height ** 2)
            
            if bmi < 18.5:
                category = "Niedowaga"
            elif 18.5 <= bmi < 25:
                category = "Prawidłowa waga"
            elif 25 <= bmi < 30:
                category = "Nadwaga"
            else:
                category = "Otyłość"
            
            # Obliczenie idealnej wagi
            if gender == "Mężczyzna":
                ideal_weight = 50 + 2.3 * ((height * 100 / 2.54) - 60)
            else:
                ideal_weight = 45.5 + 2.3 * ((height * 100 / 2.54) - 60)
            
            # Obliczenie podstawowej przemiany materii (BMR)
            if gender == "Mężczyzna":
                bmr = 88.362 + (13.397 * weight) + (4.799 * height * 100) - (5.677 * age)
            else:
                bmr = 447.593 + (9.247 * weight) + (3.098 * height * 100) - (4.330 * age)
            
            # Dodaj wynik do historii
            history_entry = {
                "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "bmi": round(bmi, 2),
                "category": category,
                "weight": weight,
                "height": height * 100,
                "age": age,
                "gender": gender
            }
            history_data.append(history_entry)
            save_history(history_data)

            # Przekaż wyniki do nowego widoku
            page.go(f"/results?bmi={bmi:.2f}&category={category}&ideal_weight={ideal_weight:.2f}&bmr={bmr:.2f}")

        except ValueError:
            error_dialog.open = True
            page.update()

    def clear_history(e):
        nonlocal history_data
        history_data.clear()
        save_history(history_data)
        update_history_view()
        page.update()

    def update_history_view():
        history_view.controls.clear()
        for entry in reversed(history_data):
            history_view.controls.append(
                ft.Text(f"{entry['date']} - BMI: {entry['bmi']} - {entry['category']}")
            )

    def close_dialog(e):
        error_dialog.open = False
        page.update()

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        theme_icon.name = "dark_mode" if page.theme_mode == ft.ThemeMode.LIGHT else "light_mode"
        page.update()

    def route_change(route):
        nonlocal history_data
        page.views.clear()
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.AppBar(title=ft.Text("Kalkulator BMI"), center_title=True, actions=[theme_icon]),
                        ft.Column([
                            weight_input,
                            height_input,
                            age_input,
                            gender_dropdown,
                            calculate_button,
                            ft.ElevatedButton("Pokaż historię", on_click=lambda _: page.go("/history")),
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        error_dialog,
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        elif page.route == "/history":
            update_history_view()
            page.views.append(
                ft.View(
                    "/history",
                    [
                        ft.AppBar(title=ft.Text("Historia BMI"), center_title=True, actions=[theme_icon]),
                        ft.Column([
                            history_view,
                            ft.ElevatedButton("Wyczyść historię", on_click=clear_history),
                            ft.ElevatedButton("Powrót", on_click=lambda _: page.go("/")),
                        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        elif page.route.startswith("/results"):
            params = page.route.split("?")[1].split("&")
            results = {param.split("=")[0]: param.split("=")[1] for param in params}
            results_content = [
                ft.Text(f"Twoje BMI: {results['bmi']}", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(f"Kategoria: {results['category']}", size=16),
                ft.Text(f"Idealna waga: {results['ideal_weight']} kg", size=16),
                ft.Text(f"BMR: {results['bmr']} kcal/dzień", size=16)
            ]
            if results['category'] == "Niedowaga":
                results_content.append(
                    ft.Row(
                        [
                            ft.Image(
                                src=resource_path("slim.png"),
                                width=200,
                                height=200,
                                fit=ft.ImageFit.CONTAIN
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                )
            elif results['category'] == "Prawidłowa waga":
                results_content.append(
                    ft.Row(
                        [
                            ft.Image(
                                src=resource_path("normal.png"),
                                width=200,
                                height=200,
                                fit=ft.ImageFit.CONTAIN
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                )
            elif results['category'] in ["Nadwaga", "Otyłość"]:
                results_content.append(
                    ft.Row(
                        [
                            ft.Image(
                                src=resource_path("pig.png"),
                                width=200,
                                height=200,
                                fit=ft.ImageFit.CONTAIN
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                )
            page.views.append(
                ft.View(
                    "/results",
                    [
                        ft.AppBar(title=ft.Text("Wyniki BMI"), center_title=True, actions=[theme_icon]),
                        ft.Column(results_content, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.ElevatedButton("Powrót", on_click=lambda _: page.go("/")),
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    weight_input = ft.TextField(label="Waga (kg)", width=300)
    height_input = ft.TextField(label="Wzrost (cm)", width=300)
    age_input = ft.TextField(label="Wiek", width=300)
    gender_dropdown = ft.Dropdown(
        label="Płeć",
        width=300,
        options=[
            ft.dropdown.Option("Mężczyzna"),
            ft.dropdown.Option("Kobieta"),
        ],
    )
    calculate_button = ft.ElevatedButton(text="Oblicz BMI", on_click=calculate_bmi, width=300)

    history_view = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=10)

    error_dialog = ft.AlertDialog(
        title=ft.Text("Błąd"),
        content=ft.Text("Wprowadź poprawne wartości."),
        actions=[
            ft.TextButton("OK", on_click=close_dialog),
        ],
    )

    theme_icon = ft.IconButton(
        icon="light_mode",
        on_click=toggle_theme,
        tooltip="Zmień motyw",
    )

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BMI Calculator")
    parser.add_argument("--web", action="store_true", help="Run in web mode")
    args = parser.parse_args()

    if args.web:
        ft.app(target=main, view=ft.WEB_BROWSER)
    else:
        ft.app(target=main)