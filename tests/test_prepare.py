import hashlib
import json

import pytest

from thermal_surrogate.prepare import generate_case, read_measures


HEADER = (
    "Statistics_root_area_integrate,"
    "Statistics_root_temperature_integral_integrate\n"
)


def test_read_measures_valid(tmp_path):

    path = tmp_path / "values.csv"
    path.write_text(HEADER + "2.0, 6.0\n", encoding = "utf-8")

    result = read_measures(path)

    assert result == {
        "root_area": 2.0,
        "root_temperature_integral": 6.0,
        "root_temperature_mean": 3.0
    }


@pytest.mark.parametrize(
    "content", 
    [
        "",
        HEADER,
        "wrong_column, another_column\n 1,2\n",
        HEADER + "abc, 6.0\n",
        HEADER + "0, 6.0\n",
        HEADER + "-1, 6.0\n",
        HEADER + "2.0, inf\n",
        HEADER + "nan, 6.0\n",
        HEADER + "1e-300, 1e300\n"
    ]
)


def test_read_measures_invalid(tmp_path, content):

    path = tmp_path / "values.csv"
    path.write_text(content, encoding = "utf-8")

    with pytest.raises(ValueError):

        read_measures(path)


def test_generate_case_with_measures(tmp_path):

    output = tmp_path / "reference"
    measures = tmp_path / "values.csv"
    measures.write_text(HEADER + "1.0, 3.0\n", encoding = "utf-8")

    generate_case(
        N = 4, L = 2.5, d = 0.75, t = 0.25,
        output_dir = output,
        measures_path = measures
    )

    manifest = json.loads(
        (output / "manifest.json").read_text(encoding = "utf-8")
    )

    assert manifest["parameters"] == {
        "N": 4, "L": 2.5, "d": 0.75, "t": 0.25
    }

    assert manifest["results"]["root_temperature_mean"] == 3.0

    for filename, expected_hash in manifest["files"].items():

        actual_hash = hashlib.sha256(
            (output / filename).read_bytes()
        ).hexdigest()

        assert actual_hash == expected_hash

    assert set(manifest["templates"]) == {
        "fin.geo.liquid",
        "thermal_fin.json.liquid",
        "thermal-fin.cfg.liquid"
    }