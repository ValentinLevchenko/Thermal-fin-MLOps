import csv
import json
import random



def read_ids(path):
    ids = []
    with open(path) as f :
        for row in csv.DictReader(f):
            ids.append(row["sample_id"])
    return ids


# shuffle a copy of the IDs so the original seed doesn't change
def shuffle_ids(ids, seed):
    shuffled = sorted(ids)
    random.Random(seed).shuffle(shuffled)
    return shuffled
    

# cut the shuffled IDs into train, validation and test
def cut(shuffled, fractions):
    n = len(shuffled)
    n_train = round(fractions["train"]*n)
    n_val = round(fractions["validation"]*n)
    train = shuffled[:n_train]
    validation = shuffled[n_train:n_train + n_val]
    test = shuffled[n_train + n_val:]
    return train, validation, test


# write one line per sample and its set
def write_splits(path, train, validation, test):
    rows = []
    for sample_id in train:
        rows.append((sample_id, "train"))
    for sample_id in validation:
        rows.append((sample_id, "validation"))
    for sample_id in test:
        rows.append((sample_id, "test")) 
    rows.sort()
    
    with open(path, "w",newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "split"])
        writer.writerows(rows)




if __name__ == "__main__":
    with open("config/campaign.json") as f:
        config = json.load(f)
    seed = config["split"]["seed"]
        
    ids = read_ids("data/samples.csv")
    shuffled = shuffle_ids(ids, seed)
    train, validation, test = cut(shuffled, config["split"])
    write_splits("data/splits.csv", train, validation, test)
    print("train:", len(train), "validation:", len(validation), "test:", len(test))
    print("wrote data/splits.csv")


