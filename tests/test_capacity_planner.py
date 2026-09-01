from process_copilot.capacity_planner import ProductionLine, simulate


def test_within_cap_returns_single_full_request_option() -> None:
    lines = [
        ProductionLine("map_dap", "磷肥支路", requested_p2o5_tpd=100.0),
        ProductionLine("ppa", "净化磷酸支路", requested_p2o5_tpd=50.0),
    ]
    result = simulate(lines, gypsum_cap_tpd=1000.0)

    assert result.request_within_cap is True
    assert len(result.options) == 1
    assert result.options[0].within_cap is True
    assert result.options[0].total_allocated_p2o5_tpd == 150.0


def test_over_cap_generates_three_mitigation_options() -> None:
    lines = [
        ProductionLine("map_dap", "磷肥支路", requested_p2o5_tpd=100.0, priority=1),
        ProductionLine("ppa", "净化磷酸支路", requested_p2o5_tpd=100.0, priority=5),
    ]
    # requested_high = 200 * 5 = 1000, cap = 400 -> exceeds cap.
    result = simulate(lines, gypsum_cap_tpd=400.0)

    assert result.request_within_cap is False
    assert [option.strategy for option in result.options] == [
        "proportional",
        "proportional",
        "priority_first",
        "equal_share",
    ]
    for option in result.options[1:]:
        assert option.within_cap is True


def test_gypsum_output_depends_only_on_total_p2o5_not_line_split() -> None:
    """磷石膏产出只取决于全园区磷酸总处理量，与支路怎么分配磷酸无关（报告 2.1 节）。"""
    same_total_split_a = [
        ProductionLine("a", "A", requested_p2o5_tpd=80.0),
        ProductionLine("b", "B", requested_p2o5_tpd=20.0),
    ]
    same_total_split_b = [
        ProductionLine("a", "A", requested_p2o5_tpd=50.0),
        ProductionLine("b", "B", requested_p2o5_tpd=50.0),
    ]
    result_a = simulate(same_total_split_a, gypsum_cap_tpd=1000.0)
    result_b = simulate(same_total_split_b, gypsum_cap_tpd=1000.0)

    assert result_a.requested_gypsum_output_high_tpd == result_b.requested_gypsum_output_high_tpd


def test_priority_first_fully_serves_higher_priority_before_lower() -> None:
    lines = [
        ProductionLine("low", "低优先级", requested_p2o5_tpd=100.0, priority=1),
        ProductionLine("high", "高优先级", requested_p2o5_tpd=100.0, priority=9),
    ]
    result = simulate(lines, gypsum_cap_tpd=400.0)  # budget = 400/5 = 80 tpd P2O5

    priority_option = next(o for o in result.options if o.strategy == "priority_first")
    allocations = {line.id: line for line in priority_option.lines}
    assert allocations["high"].allocated_p2o5_tpd == 80.0
    assert allocations["low"].allocated_p2o5_tpd == 0.0


def test_equal_share_splits_budget_evenly_regardless_of_request_size() -> None:
    lines = [
        ProductionLine("small", "小需求", requested_p2o5_tpd=10.0),
        ProductionLine("large", "大需求", requested_p2o5_tpd=200.0),
    ]
    result = simulate(lines, gypsum_cap_tpd=400.0)  # budget = 80 tpd P2O5, split 40/40

    equal_option = next(o for o in result.options if o.strategy == "equal_share")
    allocations = {line.id: line for line in equal_option.lines}
    assert allocations["small"].allocated_p2o5_tpd == 10.0  # capped at its own request
    assert allocations["large"].allocated_p2o5_tpd == 40.0


def test_disclosure_is_always_present() -> None:
    result = simulate([ProductionLine("a", "A", requested_p2o5_tpd=10.0)], gypsum_cap_tpd=1000.0)
    assert "调用方传入" in result.disclosure
