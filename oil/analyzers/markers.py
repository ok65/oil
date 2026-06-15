

class Marker:

    def __init__(self, parent, index: int):
        self.parent = parent
        self._index = index

    @property
    def index(self) -> int:
        return self._index