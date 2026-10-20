from __future__ import annotations
from dataclasses import dataclass
SCOPES_CALENDAR_RO = ['https://www.googleapis.com/auth/calendar.readonly']
SCOPES_CALENDAR_RW = ['https://www.googleapis.com/auth/calendar.events']
SCOPES_GMAIL_RO = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES_TASKS = ['https://www.googleapis.com/auth/tasks']
class NeedsGoogleAuth(Exception):
    pass
@dataclass
class GoogleAuthState:
    configured: bool = False
    project: str = ''
    client_id_present: bool = False
    @property
    def ready_for_oauth(self) -> bool:
        return self.configured and self.client_id_present
def auth_state_from_settings(s) -> GoogleAuthState:
    cid = bool(getattr(s, 'google_oauth_client_id', ''))
    return GoogleAuthState(configured=False, project=getattr(s, 'google_cloud_project', ''), client_id_present=cid)
