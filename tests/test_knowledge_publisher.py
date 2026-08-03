"""Tests for C2G Knowledge Publisher (ADR-0296 Phase C)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from c2g.knowledge_publisher import publish_outcome_card, publish_predictive_card
from c2g.outcome_tracker import OutcomeTracker
from c2g.predictive_report import build_report


def test_publish_outcome_card_degraded_offline():
    outcome_data = {
        "success_score": 0.85,
        "generated_tasks": ["task-1", "task-2"],
        "completed_tasks": ["task-1"],
        "failed_tasks": [],
        "lessons_learned": ["Always specify upstream"],
        "status": "completed",
    }
    # Using invalid endpoint to force offline fallback
    res = publish_outcome_card(
        "pitch-demo",
        outcome_data,
        agora_endpoint="http://127.0.0.1:9 | INVALID",
        cockpit_knowledge_url="http://127.0.0.1:9 | INVALID",
    )
    assert res["status"] == "degraded_offline"
    assert res["slug"] == "c2g-outcome-pitch-demo"
    assert "pitch-pitch-demo" in res["payload"]["tags"]
    assert "c2g" in res["payload"]["tags"]
    assert "# C2G Strategic Pitch Outcome: `pitch-demo`" in res["payload"]["content"]
    assert "85.00%" in res["payload"]["content"]


def test_publish_predictive_card_degraded_offline():
    report_data = {
        "backtest": {
            "pitch_count": 5,
            "mean_success_score": 0.72,
            "completed_tasks": 10,
            "failed_tasks": 2,
        },
        "forecast": {"next_score": 0.75},
        "heatmap_markdown": "| Risk | Score |\n| --- | --- |\n| High | 0.9 |",
    }
    res = publish_predictive_card(
        report_data,
        agora_endpoint="http://127.0.0.1:9 | INVALID",
        cockpit_knowledge_url="http://127.0.0.1:9 | INVALID",
    )
    assert res["status"] == "degraded_offline"
    assert res["slug"] == "c2g-predictive-risk-heatmap"
    assert "predictive" in res["payload"]["tags"]
    assert "72.00%" in res["payload"]["content"]
    assert "| Risk | Score |" in res["payload"]["content"]


@patch("c2g.knowledge_publisher.httpx.Client")
def test_publish_outcome_card_mock_agora(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "event_id": "evt-123"}
    mock_client.post.return_value = mock_resp

    res = publish_outcome_card("pitch-alpha", {"success_score": 1.0})
    assert res["status"] == "ok"
    assert res["channel"] == "agora_mcp"
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args[1]["json"]
    assert call_args["tool"] == "publish_event"
    assert call_args["arguments"]["event_type"] == "bos://brain/events/card_updated"
    assert call_args["arguments"]["payload"]["slug"] == "c2g-outcome-pitch-alpha"


@patch("c2g.knowledge_publisher.httpx.Client")
def test_publish_predictive_card_mock_cockpit_fallback(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_resp_http = MagicMock()
    mock_resp_http.status_code = 201
    mock_resp_http.json.return_value = {"card_id": "card-999"}

    mock_client.post.side_effect = [ConnectionError("Agora down"), mock_resp_http]

    res = publish_predictive_card({"backtest": {"mean_success_score": 0.5}})
    assert res["status"] == "ok"
    assert res["channel"] == "http_put"
    assert mock_client.post.call_count == 2


def test_outcome_tracker_publish_integration(tmp_path):
    tracker = OutcomeTracker(tmp_path)
    tracker.track_pitch_creation("pitch-int-1", "path/to/pitch.md")
    tracker.add_lessons_learned("pitch-int-1", "Ensure good testing")

    res = tracker.publish_outcome_to_knowledge(
        "pitch-int-1", agora_endpoint="http://127.0.0.1:9 | INVALID"
    )
    assert res is not None
    assert res["status"] == "degraded_offline"
    assert "pitch-int-1" in res["payload"]["content"]


def test_predictive_report_publish_flag(tmp_path):
    report = build_report(tmp_path, horizon=2, publish_knowledge=True)
    assert "knowledge_publish" in report
    assert report["knowledge_publish"]["status"] in ("ok", "degraded_offline")
