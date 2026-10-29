"""
Unit tests for the Synthetic Grid Generator.
Verifies reproducibility, unit conformance, and simulated data labeling.
"""

from app.data_processing.synthetic_generator import SyntheticGridGenerator


def test_generator_deterministic_reproducibility():
    """Verify that identical seeds produce mathematically identical results."""
    gen1 = SyntheticGridGenerator(seed=101)
    gen2 = SyntheticGridGenerator(seed=101)

    res1 = gen1.generate_scenario_a_normal(hours=12)
    res2 = gen2.generate_scenario_a_normal(hours=12)

    assert len(res1["boundary_readings"]) == len(res2["boundary_readings"])
    assert len(res1["consumption_readings"]) == len(res2["consumption_readings"])

    # Verify first 5 boundary readings match exactly to the floating point bit
    for b1, b2 in zip(res1["boundary_readings"][:5], res2["boundary_readings"][:5]):
        assert b1["energy_kwh"] == b2["energy_kwh"]
        assert b1["voltage_v"] == b2["voltage_v"]
        assert b1["frequency_hz"] == b2["frequency_hz"]

    # Verify consumption readings match
    for c1, c2 in zip(res1["consumption_readings"][:5], res2["consumption_readings"][:5]):
        assert c1["energy_kwh"] == c2["energy_kwh"]

    # Different seed must produce distinct numbers
    gen3 = SyntheticGridGenerator(seed=999)
    res3 = gen3.generate_scenario_a_normal(hours=12)
    assert res1["consumption_readings"][0]["energy_kwh"] != res3["consumption_readings"][0]["energy_kwh"]


def test_generator_labels_and_units():
    """Verify all generated records are labeled as simulated and use approved units."""
    gen = SyntheticGridGenerator(seed=42)
    scenario_a = gen.generate_scenario_a_normal(hours=6)

    # 1. Boundary readings check
    for br in scenario_a["boundary_readings"]:
        assert br["is_simulated"] is True
        assert br["unit"] == "KWH"
        assert 45.0 <= br["frequency_hz"] <= 55.0
        assert br["voltage_v"] > 0

    # 2. Consumption readings check
    for cr in scenario_a["consumption_readings"]:
        assert cr["is_simulated"] is True
        assert cr["unit"] == "KWH"
        assert cr["energy_kwh"] >= 0
        assert cr["interval_minutes"] == 60


def test_generator_topology_tree():
    """Verify network assets and parent-child tree hierarchy."""
    gen = SyntheticGridGenerator(seed=42)
    topo = gen.generate_topology_entities()

    asset_codes = {a["asset_code"] for a in topo["assets"]}
    assert "SUB-132KV-NORTH" in asset_codes
    assert "FDR-11KV-F2" in asset_codes
    assert "DT-11KV-415V-101" in asset_codes

    # Verify relationships
    parent_child = [(r[0], r[1]) for r in topo["relationships"]]
    assert ("SUB-132KV-NORTH", "FDR-11KV-F2") in parent_child
    assert ("FDR-11KV-F2", "DT-11KV-415V-101") in parent_child

