"""B7 NHC stem 解析与中心汇总。"""

from pipeline.revision.b7.nhc_stem import CenterStatsCollector, anonymize_filename, parse_nhc_stem


def test_parse_nhc_stem():
    p = parse_nhc_stem("THYB_S_AN01_ND000091_202052842015")
    assert p["center_id"] == "THYB_S_AN01"
    assert p["patient_id"] == "ND000091"
    assert p["timestamp"] == "202052842015"


def test_parse_unknown_stem():
    p = parse_nhc_stem("short_name")
    assert p["center_id"] is None


def test_anonymize_preserves_timestamp_suffix():
    out = anonymize_filename("THYB_S_AN01_ND000091_202052842015", ".png")
    assert out.endswith("_202052842015.png")
    assert out.count("_") >= 2


def test_center_stats_collector():
    c = CenterStatsCollector()
    c.record("THYB_S_AN01", "ND000091")
    c.record("THYB_S_AN01", "ND000091")
    c.record("THYB_S_AN01", "ND000092")
    c.record("THYB_S_AH04", "ND000133")
    s = c.to_summary()
    assert s["n_centers"] == 2
    assert s["n_images"] == 4
    assert s["n_patients_total"] == 3
    assert s["centers"]["THYB_S_AN01"]["n_images"] == 3
    assert s["centers"]["THYB_S_AN01"]["n_patients"] == 2
