class ItemNotFound(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id


class BelowMinimumQuantity(Exception):
    def __init__(self, min_qty: int):
        self.min_qty = min_qty
