from afco.report.generate import generate_report, render_markdown


def test_step9_report_is_reproducible_and_audited():
    report = generate_report(fuzz_trials=100, fleet_size=2)
    assert report.d3_safe
    assert report.d9_invariant_breaches == ()
    assert report.d13_rejected_events == 0
    assert report.fuzz_false_accepts == 0
    assert set(report.patent_claims) == {
        "claim_1_runtime_automata_gate",
        "claim_2_adaptive_safe_recovery",
        "claim_5_declarative_protocol_normalization",
    }
    markdown = render_markdown(report)
    assert "AFCO M9 Verification Report" in markdown
    assert "100" in markdown

