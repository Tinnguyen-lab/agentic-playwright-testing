"""The UI's subprocess browser bridge fails clearly when the target is offline."""
import socket

import pytest

from src.models.playwright_artifacts import ActionType, PlaywrightAction, PlaywrightPlan
from src.services.browser_tasks import BrowserTaskError, run_task


@pytest.mark.parametrize("task", ["snapshot", "ground"])
def test_unavailable_target_does_not_return_empty_success(task):
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
        url = f"http://127.0.0.1:{port}/login"
        payload = (
            {"url": url}
            if task == "snapshot"
            else {"plan": PlaywrightPlan(actions=[PlaywrightAction(type=ActionType.GOTO, arg=url)]).model_dump(mode="json")}
        )
        with pytest.raises(BrowserTaskError, match="ERR_CONNECTION_REFUSED"):
            run_task(task, payload, timeout=30)
