import uuid
from pathlib import Path

from rseed.util.fs import dump_yaml, load_yaml


def get_random_string():
    return str(uuid.uuid4())[:8]


class PersistDictList:
    def __init__(self, yaml, key="id", n=100):
        self.key = key
        self.n = n
        self.yaml = yaml
        if Path(self.yaml).exists():
            self.values = load_yaml(self.yaml)
        else:
            self.values = []

    def get(self, n):
        return self.values[-n:]

    def get_i(self, new_value):
        for i, value in enumerate(self.values):
            if new_value.get(self.key) is not None:
                if value.get(self.key) == new_value.get(self.key):
                    return i
        return None

    def save(self):
        self.values = self.values[-self.n :]
        dump_yaml(self.values, self.yaml)

    def append(self, new_value):
        if self.key not in new_value:
            new_value[self.key] = get_random_string()
        i = self.get_i(new_value)
        if i is None:
            self.values.append(new_value)
        else:
            self.values[i] = new_value
        self.save()

    def delete(self, del_value):
        i = self.get_i(del_value)
        if i is not None:
            del self.values[i]
            self.save()


if __name__ == "__main__":
    p = PersistDictList("test.yaml")
