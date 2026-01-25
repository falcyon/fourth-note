"""Progress tracking for real-time UI updates."""
import asyncio
from typing import Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ProgressEvent:
    """A single progress event."""
    step: str
    message: str
    details: Optional[dict] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_sse(self) -> str:
        """Format as Server-Sent Event."""
        data = {
            "step": self.step,
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp,
        }
        return f"data: {json.dumps(data)}\n\n"


class ProgressTracker:
    """Tracks progress and notifies listeners."""

    def __init__(self):
        self.events: List[ProgressEvent] = []
        self._listeners: List[asyncio.Queue] = []
        self._current_step: str = ""

    def emit(self, step: str, message: str, details: Optional[dict] = None):
        """Emit a progress event."""
        event = ProgressEvent(step=step, message=message, details=details)
        self.events.append(event)
        self._current_step = step

        # Notify all listeners
        for queue in self._listeners:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to progress events."""
        queue = asyncio.Queue(maxsize=100)
        self._listeners.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from progress events."""
        if queue in self._listeners:
            self._listeners.remove(queue)

    def complete(self, message: str = "Processing complete", details: Optional[dict] = None):
        """Mark processing as complete."""
        self.emit("complete", message, details)

    def error(self, message: str, details: Optional[dict] = None):
        """Mark processing as failed."""
        self.emit("error", message, details)

    def clear(self):
        """Clear all events."""
        self.events = []
        self._current_step = ""


# Global progress tracker instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get or create the global progress tracker."""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker
