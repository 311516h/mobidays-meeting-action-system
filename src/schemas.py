from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["high", "medium", "low"]
Status = Literal["todo", "in_progress", "done", "needs_review"]


class ActionItem(BaseModel):
    owner: str = Field(..., min_length=1)
    task: str = Field(..., min_length=1)
    due_date: str = Field(default="미정")
    priority: Priority = "medium"
    status: Status = "todo"
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_utterance: str = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=1)


class ActionItemRecord(ActionItem):
    action_item_id: str
    meeting_id: str
    chunk_id: str


class ActionItemList(BaseModel):
    items: list[ActionItem] = Field(default_factory=list)


class SlackPayload(BaseModel):
    channel: str
    text: str
    blocks: list[dict]
