"""Tests for Mealy Machine Finite-State Transducer."""

from afco.automata.transducer import MealyTransducer


def test_mealy_transducer() -> None:
    """A Mealy transducer that translates vendor messages to canonical symbols.

    Vendor inputs: {'vendor_auth', 'vendor_plug', 'vendor_stop'}
    Canonical outputs: {'auth_req', 'plug_in', 'power_ramp_down'}
    """
    transducer = MealyTransducer(
        states=frozenset({"Available", "Preparing", "Charging"}),
        input_alphabet=frozenset({"vendor_auth", "vendor_plug", "vendor_stop"}),
        output_alphabet=frozenset({"auth_req", "plug_in", "power_ramp_down"}),
        transitions={
            ("Available", "vendor_auth"): "Preparing",
            ("Preparing", "vendor_plug"): "Charging",
            ("Charging", "vendor_stop"): "Available",
        },
        emissions={
            ("Available", "vendor_auth"): "auth_req",
            ("Preparing", "vendor_plug"): "plug_in",
            ("Charging", "vendor_stop"): "power_ramp_down",
        },
        start_state="Available",
    )

    # Valid sequence
    res = transducer.transduce(["vendor_auth", "vendor_plug", "vendor_stop"])
    assert res.success is True
    assert res.output_word == ["auth_req", "plug_in", "power_ramp_down"]
    assert res.state_path == ["Available", "Preparing", "Charging", "Available"]

    # Invalid sequence: unexpected vendor_stop at Available
    bad_res = transducer.transduce(["vendor_stop"])
    assert bad_res.success is False
    assert bad_res.failure_index == 0
    assert bad_res.rejected_input == "vendor_stop"
