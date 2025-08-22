from pydantic import BaseModel

class VersionForm(BaseModel):
    latest_version: str
    min_required_version: str
    update_url: str