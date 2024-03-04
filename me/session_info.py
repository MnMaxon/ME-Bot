import dataclasses
from uuid import uuid4


@dataclasses.dataclass
class SessionInfo:
    session_id: str
    token_dict: dict[str, str] or None = None
    def is_logged_in(self):
        return self.token_dict is not None

def get_session_info():
    return SessionInfo(str(uuid4()))
