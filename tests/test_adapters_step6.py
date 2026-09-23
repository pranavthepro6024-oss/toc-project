from pathlib import Path

import pytest

from afco.adapters import AdapterLoadError, load_adapter


ROOT = Path(__file__).parents[1] / "afco" / "adapters"


def test_dynamic_hot_load_translates_without_kernel_changes():
    machine = load_adapter(ROOT / "ocpp16.yaml")
    result = machine.transduce([
        "Authorize", "AuthorizationAccepted", "CablePlugged", "CableLocked", "EvReady",
        "PrechargeComplete", "StartTransaction", "StopTransaction",
        "PowerStopped", "ContactorsOpen", "Unplugged",
        "MeterFinal", "PaymentAccepted",
    ])
    assert result.success
    assert result.output_word[:3] == ["auth_req", "auth_ok", "plug_in"]
    assert result.output_word[-1] == "pay_ok"


@pytest.mark.parametrize("name", ["ocpp201.yaml", "chademo.yaml"])
def test_shipped_adapters_load(name):
    assert load_adapter(ROOT / name).states


def test_malformed_adapter_is_rejected_at_load_time():
    with pytest.raises(AdapterLoadError):
        load_adapter(ROOT / "malformed_test.yaml")
