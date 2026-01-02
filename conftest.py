"""Pytest configuration for static site tests."""

import pytest
import subprocess
import time
from pathlib import Path


@pytest.fixture(scope='session')
def http_server():
    """Start HTTP server for static site."""
    static_dir = Path(__file__).parent / 'static_site'
    port = 8765  # Use a different port to avoid conflicts

    # Start server
    server = subprocess.Popen(
        ['python3', '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
        cwd=static_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for server to start
    time.sleep(2)

    yield f'http://127.0.0.1:{port}'

    # Cleanup
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()


@pytest.fixture
def site_url(http_server):
    """Provide base URL to tests."""
    return http_server
