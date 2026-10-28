import os
import sys
import pytest
from thermal_surrogate import sampling
from thermal_surrogate.sampling import draw_samples, load_config

CONFIG=load_config("config/campaign.json")



# check the same seed
def test_same_seed_gives_same_samples():
    assert draw_samples(CONFIG,20)== draw_samples(CONFIG, 20)
    
#no sample leaves the domain
def test_samples_stay_inside_bounds():
    for row in draw_samples(CONFIG, 50):
        for name in ["L","t","Bi"]:
            p=CONFIG["parameters"][name]
            assert p["min"]<= row[name] <=p["max"]


# no samples share an ID so each simulation can be identified
def test_sample_ids_are_unique():
    rows=draw_samples(CONFIG,50)
    assert len({row["sample_id"] for row in rows}) ==50


# Bi really uses the log scale
def test_bi_covers_both_decades():
    bis=[row["Bi"] for row in draw_samples(CONFIG,20)]
    assert any(b<0.1 for b in bis) and any(b>0.1 for b in bis)



@pytest.mark.parametrize("n", [0,-1])
def test_non_positive_n_is_rejected(n):
    with pytest.raises(ValueError):
        draw_samples(CONFIG, n)

        

def test_cli_output_without_directory(tmp_path, monkeypatch):
    config = os.path.abspath("config/campaign.json")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sampling", "--config", config, "--n", "3", "--output", "sample.csv"])
    sampling.main()
    assert (tmp_path / "sample.csv").exists()





