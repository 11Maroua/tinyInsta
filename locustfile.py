#!/usr/bin/env python3
"""
Locustfile pour TinyInsta - Teste des timelines différentes par utilisateur.
"""

from locust import HttpUser, task, between
import random


class TinyInstaUser(HttpUser):
    """Utilisateur virtuel testant une timeline unique."""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Assigne un user_id unique à chaque utilisateur Locust."""
        self.user_id = random.randint(1, 1000)
    
    @task
    def get_timeline(self):
        """Récupère la timeline de cet utilisateur."""
        with self.client.get(
            f"/api/timeline?user=user{self.user_id}&limit=20",
            catch_response=True,
            name="/api/timeline"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
