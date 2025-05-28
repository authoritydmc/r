from locust import HttpUser, TaskSet, task, between
import uuid

class RedirectUpstreamTasks(TaskSet):
    @task
    def create_random_redirect(self):
        shortcut = f"shortcut-{uuid.uuid4().hex[:8]}"
        target = "https://example.com"
        self.client.post(f"/edit/{shortcut}", data={"type": "redirect", "target": target}, name="/edit/<shortcut>")
        self.client.get(f"/{shortcut}", name="/<shortcut>")

    @task
    def create_and_test_google_redirect(self):
        shortcut = "google"
        target = "https://google.com"
        self.client.post(f"/edit/{shortcut}", data={"type": "redirect", "target": target}, name="/edit/google")
        self.client.get(f"/{shortcut}", name="/google")

    @task
    def check_upstreams_ui(self):
        self.client.get(f"/check-upstreams-ui/test-pattern", name="/check-upstreams-ui/<pattern>")

    @task
    def access_random_unknown_shortcut(self):
        unknown_shortcut = f"unknown-{uuid.uuid4().hex[:6]}"
        self.client.get(f"/{unknown_shortcut}", name="/<unknown-shortcut>")

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    tasks = [RedirectUpstreamTasks]