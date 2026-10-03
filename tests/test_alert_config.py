from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_three_symptom_alerts_are_fully_configured_and_have_runbooks():
    config = yaml.safe_load((ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8"))
    alerts = config["alerts"]
    assert len(alerts) == 3
    assert {alert["name"] for alert in alerts} == {
        "HighLatencyP95",
        "ElevatedRequestErrorRate",
        "LowRetrievalSuccess",
    }
    for alert in alerts:
        assert alert["type"] == "symptom-based"
        assert alert["severity"] in {"warning", "critical"}
        assert alert["duration"] in {"5m", "10m"}
        assert alert["channel"] == "#k4-l3b-alerts"
        assert alert["owner"]
        assert "TODO" not in str(alert.values())
        assert (ROOT / alert["runbook"].split("#", 1)[0]).exists()
