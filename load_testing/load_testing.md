# Load Testing with Locust

## Introduction
This document outlines the load testing setup using **Locust**, a Python-based load testing tool. The goal is to simulate user behavior and assess application performance under stress.

## Setup
### **1. Install Dependencies**
```sh
pip install locust
```

### **2. Directory Structure**
```
/load_tests
    ├── locustfile.py          # Main entry point
```

## Locust Script
### **Main locustfile.py**
```python
from locust import HttpUser, between
from tasks.redirect_tasks import RedirectUpstreamTasks
from tasks.user_tasks import UserTasks

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    tasks = [RedirectUpstreamTasks, UserTasks]
```

### **Redirect Tasks (`redirect_tasks.py`)**
```python
from locust import TaskSet, task
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
```

## Running the Test
To start Locust with your defined tasks:
```sh
locust -f load_testing/locustfile.py --host=http://localhost:80
```
Then open `http://localhost:8089` in your browser to configure and start testing.

## Load Test Parameters
| Parameter    | Description                | Example Value |
|-------------|----------------------------|--------------|
| `Number of Users` | Simulated concurrent users | 100 |
| `Spawn Rate` | Rate of user ramp-up | 10 |
| `Request Timeout` | Max response wait time | 5 sec |
| `Max Failures` | Allowed failed requests | 50 |

## Monitoring & Analysis
### **View Results in Locust UI**
- Navigate to `http://localhost:8089` for real-time statistics.
- Check response times, failures, and throughput.

### **Export Data for Analysis**
```sh
locust --headless -f load_testing/locustfile.py --host=http://localhost:80 --csv=load_testing/load_test_results
```
