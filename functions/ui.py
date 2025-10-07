from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.metrics import dp, sp

import os
import time
import requests

# === Config ===
# Override with: PILLSYNC_SERVER="http://192.168.1.109:5000"
SERVER = os.environ.get("PILLSYNC_SERVER", "http://127.0.0.1:5000")

Window.size = (480, 320)
Window.clearcolor = (0, 0, 0, 1)

class RoundedButton(Button):
    def __init__(self, bg_color=(0, 0.48, 1, 1), **kwargs):
        super(RoundedButton, self).__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class RoundedBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(RoundedBoxLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class StatusIndicator(Widget):
    color = ListProperty([0, 1, 0, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color_instruction = Color(*self.color)
            self.circle = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self.update_circle, size=self.update_circle, color=self.update_color)

    def update_circle(self, *args):
        self.circle.pos = self.pos
        self.circle.size = self.size

    def update_color(self, *args):
        self.color_instruction.rgba = self.color

# Main application class for the pillsync
class DispenserApp(App):
    current_user = StringProperty("Loading...")
    clock_time = StringProperty("")
    next_dose_text = StringProperty("")
    alert_text = StringProperty("")
    alert_color = NumericProperty(1)
    connection_status = BooleanProperty(False)
    manual_clock_enabled = BooleanProperty(False)
    manual_offset = NumericProperty(0)
    dev_menu_event = None
    alert_active = BooleanProperty(False)
    _alert_check_paused = False

    all_users = ListProperty([])
    all_prescriptions = ListProperty([])
    current_user_index = NumericProperty(0)

    current_schedule = ListProperty([])
    full_schedule = ListProperty([])
    next_dose_index = NumericProperty(0)

    def build(self):
        self.root = self.create_main_ui()
        self._load_data_from_server()
        Clock.schedule_interval(self._load_data_from_server, 60)
        Clock.schedule_interval(self._check_server_for_alerts, 5)
        Clock.schedule_interval(self.update_clock, 1)
        return self.root

    def _load_data_from_server(self, *args):
        try:
            # Fetch all users
            user_url = f"{SERVER}/users?format=json"
            user_response = requests.get(user_url, timeout=5)

            if user_response.status_code == 200:
                self.all_users = user_response.json()
                self.connection_status = True

                # Fetch all prescriptions
                schedule_url = f"{SERVER}/prescriptions?format=json"
                schedule_response = requests.get(schedule_url, timeout=5)
                if schedule_response.status_code == 200:
                    self.all_prescriptions = schedule_response.json()

                    # Filter and display data for the currently selected user
                    self._filter_and_sort_prescriptions()
                    print("Data loaded and filtered for current user.")
                else:
                    print("Failed to load schedule from server.")
            else:
                self.current_user = "Server Error"
                self.connection_status = False

        except requests.exceptions.RequestException as e:
            if self.connection_status:
                print(f"Failed to connect to server: {e}")
            self.current_user = "Offline"
            self.connection_status = False
            self.all_users = []
            self.all_prescriptions = []
            self._filter_and_sort_prescriptions()

    def _check_server_for_alerts(self, *args):
        if not self.connection_status or self.alert_active or self._alert_check_paused:
            return
        try:
            alert_url = f"{SERVER}/check_alert"
            response = requests.get(alert_url, timeout=3)
            if response.status_code == 200:
                alert_data = response.json()
                if alert_data.get("alert"):
                    self.alert_active = True
                    # if server sends name/prescription_id, we can use them
                    self.alert_text = alert_data.get("message", "Time for medication!")
                    self.alert_color = 1
                    print(f"SERVER ALERT: {self.alert_text}")
        except requests.exceptions.RequestException as e:
            print(f"Could not check for server alert: {e}")

    def get_time(self):
        current_time = time.time() + self.manual_offset
        return time.strftime("%I:%M %p", time.localtime(current_time)).lstrip("0")

    def parse_time(self, time_str):
        try:
            time_obj = time.strptime(time_str, "%I:%M %p")
            return time_obj.tm_hour * 60 + time_obj.tm_min
        except ValueError:
            try:
                time_obj = time.strptime(time_str, "%H:%M")
                return time_obj.tm_hour * 60 + time_obj.tm_min
            except ValueError:
                return None

    def format_time_for_display(self, time_str):
        if not time_str or not isinstance(time_str, str):
            return ""
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            return time_str.lstrip("0")
        try:
            time_obj = time.strptime(time_str, "%H:%M")
            return time.strftime("%I:%M %p", time_obj).lstrip("0")
        except (ValueError, TypeError):
            return "Invalid Time"

    def update_clock(self, dt):
        self.clock_time = self.get_time()

    def create_main_ui(self):
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        top_row = BoxLayout(size_hint=(1, 0.15), spacing=dp(10), padding=[dp(10), 0, dp(10), 0])

        self.user_button = RoundedButton(text=self.current_user, font_size=sp(22), halign="left", bg_color=(0, 0, 0, 0), on_press=self.switch_user)
        self.user_button.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.bind(current_user=self.user_button.setter('text'))

        indicator_container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint_x=0.1)
        self.connection_indicator = StatusIndicator(size_hint=(None, None), size=(dp(20), dp(20)))
        indicator_container.add_widget(self.connection_indicator)
        self.bind(connection_status=self.update_connection_status)
        self.update_connection_status()

        self.next_label = Label(font_size=sp(22), color=(0, 1, 0, 1), halign="right")
        self.next_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.bind(next_dose_text=self.next_label.setter('text'))

        top_row.add_widget(self.user_button)
        top_row.add_widget(indicator_container)
        top_row.add_widget(self.next_label)

        self.clock_label = Label(font_size=sp(65), color=(1, 1, 1, 1), size_hint=(1, 0.7))
        self.bind(clock_time=self.clock_label.setter('text'))
        self.clock_label.text = self.get_time()

        bottom_row = BoxLayout(size_hint=(1, 0.15), spacing=dp(10))

        manual_btn = RoundedButton(text="DISPENSE", font_size=sp(22), on_press=self.manual_dispense)

        self.alert_label = Label(text=self.alert_text, font_size=sp(18), halign="center", valign="middle")
        self.alert_label.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        self.bind(alert_text=self.alert_label.setter('text'))
        self.bind(alert_color=self.update_alert_color)
        self.update_alert_color()

        details_btn = RoundedButton(text="DETAILS", font_size=sp(22))
        details_btn.bind(on_touch_down=self._details_touch_down)
        details_btn.bind(on_touch_up=self._details_touch_up)

        bottom_row.add_widget(manual_btn)
        bottom_row.add_widget(self.alert_label)
        bottom_row.add_widget(details_btn)

        layout.add_widget(top_row)
        layout.add_widget(self.clock_label)
        layout.add_widget(bottom_row)
        return layout

    def update_alert_color(self, *args):
        self.alert_label.color = [1, 0, 0, 1] if self.alert_color == 1 else [0, 1, 0, 1]

    def update_connection_status(self, *args):
        self.connection_indicator.color = (0, 1, 0, 1) if self.connection_status else (1, 0, 0, 1)

    def _update_next_dose_display(self):
        if not self.current_schedule:
            self.next_dose_text = "No Doses Scheduled"
            self.next_label.font_size = dp(18)
            return

        self.next_label.font_size = dp(22)

        if self.next_dose_index >= len(self.current_schedule):
            self.next_dose_index = 0

        next_dose = self.current_schedule[self.next_dose_index]
        formatted_time = self.format_time_for_display(next_dose['time_of_day'])
        self.next_dose_text = f"Next: {formatted_time}"

    def manual_dispense(self, instance):
        if not self.alert_active:
            self.alert_text = "No active dose"
            self.alert_color = 1
            Clock.schedule_once(self._clear_alert, 3)
            print("Dispense button pressed, but no alert is active.")
            return

        content = RoundedBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        prompt_label = Label(text='Simulate Fingerprint Scan', font_size=sp(22))
        button_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        success_btn = RoundedButton(text="Simulate Success", bg_color=(0, 0.5, 0, 1))
        failure_btn = RoundedButton(text="Simulate Failure", bg_color=(0.5, 0, 0, 1))
        button_layout.add_widget(success_btn)
        button_layout.add_widget(failure_btn)
        content.add_widget(prompt_label)
        content.add_widget(button_layout)
        popup = Popup(title='Verification Simulation', content=content, size_hint=(0.8, 0.6),
                      separator_color=(0, 0, 0, 0), background_color=(0, 0, 0, 0))
        success_btn.bind(on_press=lambda x: self._handle_dispense_success(popup))
        failure_btn.bind(on_press=lambda x: self._handle_dispense_failure(popup))
        popup.open()

    def _handle_dispense_success(self, popup):
        self.alert_text = "Dose Dispensed"
        self.alert_color = 2
        self.alert_active = False
        popup.dismiss()

        if not self.current_schedule:
            return

        dispensed_dose = self.current_schedule[self.next_dose_index]
        dispensed_id = dispensed_dose['prescription_id']

        self._sync_dispense_action(dispensed_id)
        self._load_data_from_server()

        print(f"Dispense Succeeded. Reported dispense for prescription_id: {dispensed_id}")
        Clock.schedule_once(self._clear_alert, 5)

        self._alert_check_paused = True
        Clock.schedule_once(self._resume_alert_checks, 30)

    def _resume_alert_checks(self, dt):
        self._alert_check_paused = False
        print("Alert checks resumed.")

    def _sync_dispense_action(self, prescription_id):
        if not self.connection_status:
            print("Offline, cannot sync dispense action.")
            return

        try:
            sync_url = f"{SERVER}/sync_actions"
            payload = {"actions": [{"action": "dispense", "success": True, "prescription_id": prescription_id}]}
            response = requests.post(sync_url, json=payload, timeout=5)
            if response.status_code == 200 and response.json().get("success"):
                print("Successfully synced dispense action with the server.")
            else:
                print("Failed to sync dispense action with the server.")
        except requests.exceptions.RequestException as e:
            print(f"Error syncing action: {e}")

    def _handle_dispense_failure(self, popup):
        self.alert_text = "Scan Failed"
        self.alert_color = 1
        self.alert_active = True
        Clock.schedule_once(self._clear_alert, 5)
        print("Dispense Failed.")
        popup.dismiss()

    def _clear_alert(self, dt):
        if self.alert_text not in ["Scan Finger to Dispense"]:
            self.alert_text = ""
        if self.alert_active:
            self.alert_text = "Scan Finger to Dispense"
            self.alert_color = 1

    def show_details(self, instance):
        content = RoundedBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        title_label = Label(text=f"{self.current_user}'s Schedule", font_size=sp(24), bold=True, size_hint_y=None, height=dp(40))

        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_content = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        scroll_content.bind(minimum_height=scroll_content.setter('height'))

        if not self.full_schedule:
            no_meds_label = Label(text="No prescriptions found for this user.", font_size=sp(20))
            scroll_content.add_widget(no_meds_label)
        else:
            for dose in self.full_schedule:
                formatted_time = self.format_time_for_display(dose['time_of_day'])
                status_text = f"({dose['status']})"
                dose_label = Label(
                    text=f"{dose['name']} - {dose['dosage']} - {formatted_time} {status_text}",
                    font_size=sp(16), size_hint_y=None, height=dp(30)
                )
                scroll_content.add_widget(dose_label)

        scroll_view.add_widget(scroll_content)

        close_button = RoundedButton(text="Close", size_hint_y=None, height=dp(50))
        content.add_widget(title_label)
        content.add_widget(scroll_view)
        content.add_widget(close_button)

        popup = Popup(title='Prescription Details', content=content, size_hint=(0.99, 0.99),
                      separator_color=(0, 0, 0, 0), background_color=(0, 0, 0, 0))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def _details_touch_down(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.dev_menu_event = Clock.schedule_once(self.show_dev_menu, 2)

    def _details_touch_up(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.dev_menu_event:
                self.dev_menu_event.cancel()
                self.dev_menu_event = None
                self.show_details(instance)

    def show_dev_menu(self, dt):
        self.dev_menu_event = None

        content = RoundedBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        title_label = Label(text="Developer Menu", font_size=sp(24), bold=True, size_hint_y=None, height=dp(40))

        time_layout = BoxLayout(size_hint_y=None, height=dp(50))
        hour_spinner = Spinner(text=self.get_time().split(":")[0], values=[str(i) for i in range(1, 13)])
        min_spinner = Spinner(text=self.get_time().split(":")[1].split()[0], values=[f"{i:02}" for i in range(60)])
        period_spinner = Spinner(text=self.get_time().split()[1], values=["AM", "PM"])
        time_layout.add_widget(hour_spinner)
        time_layout.add_widget(Label(text=":"))
        time_layout.add_widget(min_spinner)
        time_layout.add_widget(period_spinner)

        set_time_btn = RoundedButton(text="Set Time", size_hint_y=None, height=dp(50))
        reset_time_btn = RoundedButton(text="Reset to Real Time", size_hint_y=None, height=dp(50))
        close_btn = RoundedButton(text="Close", size_hint_y=None, height=dp(50))

        content.add_widget(title_label)
        content.add_widget(time_layout)
        content.add_widget(set_time_btn)
        content.add_widget(reset_time_btn)
        content.add_widget(close_btn)

        popup = Popup(title='Dev Menu', content=content, size_hint=(0.9, 0.9),
                      separator_color=(0, 0, 0, 0), background_color=(0, 0, 0, 0))

        set_time_btn.bind(on_press=lambda x: self._set_manual_time(
            popup, hour_spinner.text, min_spinner.text, period_spinner.text))
        reset_time_btn.bind(on_press=lambda x: self._reset_to_real_time(popup))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _set_manual_time(self, popup, hour, minute, period):
        try:
            target_time_str = f"{hour}:{minute} {period}"
            today_str = time.strftime("%Y-%m-%d")
            full_time_str = f"{today_str} {target_time_str}"
            target_timestamp = time.mktime(time.strptime(full_time_str, "%Y-%m-%d %I:%M %p"))
            self.manual_offset = target_timestamp - time.time()
            self.manual_clock_enabled = True
            print(f"Clock overridden. New time: {self.get_time()}")
            popup.dismiss()
        except Exception as e:
            print(f"Error setting manual time: {e}")

    def _reset_to_real_time(self, popup):
        self.manual_clock_enabled = False
        self.manual_offset = 0
        print("Clock reset to real time.")
        popup.dismiss()

    def switch_user(self, *args):
        if not self.all_users:
            return
        self.current_user_index = (self.current_user_index + 1) % len(self.all_users)
        self._filter_and_sort_prescriptions()
        print(f"Switched to user: {self.current_user}")

    def _filter_and_sort_prescriptions(self):
        if not self.all_users:
            self.current_user = "Offline"
            self.current_schedule = []
            self.full_schedule = []
            return

        # Get the current user based on the index
        current_user_data = self.all_users[self.current_user_index]
        self.current_user = current_user_data.get("name", "Unknown User")
        current_user_id = current_user_data.get("user_id")

        # Filter all prescriptions for the current user
        user_prescriptions = [p for p in self.all_prescriptions if p['user_id'] == current_user_id]

        # Sort active schedule for the main UI
        active_schedule = [p for p in user_prescriptions if p['status'] == 'Active']
        active_schedule.sort(key=lambda p: self.parse_time(self.format_time_for_display(p['time_of_day'])) or 0)
        self.current_schedule = active_schedule

        # Sort full schedule for the details view
        active_details = [p for p in user_prescriptions if p['status'] == 'Active']
        dispensed_details = [p for p in user_prescriptions if p['status'] == 'Dispensed']
        active_details.sort(key=lambda p: self.parse_time(self.format_time_for_display(p['time_of_day'])) or 0)
        dispensed_details.sort(key=lambda p: self.parse_time(self.format_time_for_display(p['time_of_day'])) or 0, reverse=True)
        self.full_schedule = active_details + dispensed_details

        self.next_dose_index = 0
        self._update_next_dose_display()

if __name__ == "__main__":
    DispenserApp().run()
