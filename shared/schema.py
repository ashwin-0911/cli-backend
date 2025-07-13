from pydantic import BaseModel
from typing import Literal
from typing import Optional

class JobPayload(BaseModel):
    org_id: str
    app_version_id: str
    test_path: str
    priority: int = 1
    target: Literal["emulator", "device", "browserstack"]
    job_id: Optional[str] = None 