from django.db import models


class InventoryCategory(models.TextChoices):
    FABRIC = "FABRIC", "Fabric"
    BUTTON = "BUTTON", "Button"
    ZIP = "ZIP", "Zip"
    THREAD = "THREAD", "Thread"
    HOOK = "HOOK", "Hook"
    INTERLINING = "INTERLINING", "Interlining"
    OTHER = "OTHER", "Other"


class StockUnit(models.TextChoices):
    METRE = "METRE", "Metre"
    YARD = "YARD", "Yard"
    PIECE = "PIECE", "Piece"
    ROLL = "ROLL", "Roll"


class StockMovementType(models.TextChoices):
    OPENING = "OPENING", "Opening stock"
    STOCK_IN = "STOCK_IN", "Stock in"
    RESERVE = "RESERVE", "Reserve"
    RELEASE = "RELEASE", "Release"
    CONSUME = "CONSUME", "Consume"
    RETURN = "RETURN", "Return"
    ADJUSTMENT_IN = "ADJUSTMENT_IN", "Adjustment in"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Adjustment out"
