import random
import uuid

import numpy as np


class Config:
    def __init__(self):
        self.seed = 42

    def get_uuid(self):
        return str(uuid.uuid4())

    def set_global_seed(self, seed: int | None = None):
        if seed is not None:
            self.seed = seed
        random.seed(self.seed)
        np.random.seed(self.seed)
