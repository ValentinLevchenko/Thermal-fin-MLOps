from thermal_surrogate.split import cut, shuffle_ids

IDS = [f"s{i:04d}" for i in range(200)]
FRACTIONS = {"train":0.7,"validation":0.15, "test": 0.15}

def test_same_seed_gives_same_order():
    assert shuffle_ids(IDS, 2026) == shuffle_ids(IDS, 2026)

def test_sizes():
    train, validation, test = cut(shuffle_ids(IDS,2026), FRACTIONS)
    assert (len(train), len(validation), len(test)) == (140, 30, 30)
    

def test_every_sample_exactly_once():
    train, validation, test = cut(shuffle_ids(IDS,2026), FRACTIONS)
    all_ids = train + validation + test 
    assert sorted(all_ids) == IDS
    assert len(set(all_ids)) == 200
    
    


