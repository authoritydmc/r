import subprocess
import time
import requests
import os
import pytest

def test_docker_build_and_run():
    """Build the Docker image and check that the app runs and responds on the expected port."""
    image_tag = "redirector-test:latest"
    container_name = "redirector-test-container"
    # Build the Docker image
    build_cmd = ["docker", "build", "-t", image_tag, "."]
    subprocess.run(build_cmd, check=True)

    # Run the container
    run_cmd = [
        "docker", "run", "-d", "--rm",
        "-p", "8080:80",
        "--name", container_name,
        image_tag
    ]
    container_id = subprocess.check_output(run_cmd).decode().strip()
    try:
        # Wait for the app to start
        for _ in range(30):
            try:
                resp = requests.get("http://localhost:8080", timeout=1)
                if resp.status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            pytest.fail("App did not start in Docker container")
        # Check the dashboard page content
        assert "URL Shortener" in resp.text
    finally:
        subprocess.run(["docker", "stop", container_name])
