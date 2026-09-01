import uuid


class ItemNotFound(Exception):
    def __init__(self, item_id: uuid.UUID):
        self.item_id = item_id


class BelowMinimumQuantity(Exception):
    def __init__(self, min_qty: int):
        self.min_qty = min_qty


class AgentTurnLimitExceeded(Exception):
    pass


class InvalidRefreshToken(Exception):
    pass
