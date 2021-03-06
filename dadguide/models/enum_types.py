from enum import Enum


class Attribute(Enum):
    """Standard 5 PAD colors in enum form. Values correspond to DadGuide values."""
    Fire = 0
    Water = 1
    Wood = 2
    Light = 3
    Dark = 4
    Unknown = 5
    Nil = 6


class MonsterType(Enum):
    Evolve = 0
    Balance = 1
    Physical = 2
    Healer = 3
    Dragon = 4
    God = 5
    Attacker = 6
    Devil = 7
    Machine = 8
    Awoken = 12
    Enhance = 14
    Vendor = 15


class EvoType(Enum):
    """Evo types supported by DadGuide. Numbers correspond to their id values."""
    Base = 0  # Represents monsters who didn't require evo
    Evo = 1
    UvoAwoken = 2
    UuvoReincarnated = 3


class InternalEvoType(Enum):
    """Evo types unsupported by DadGuide."""
    Base = "Base"
    Normal = "Normal"
    Ultimate = "Ultimate"
    Reincarnated = "Reincarnated"
    Assist = "Assist"
    Pixel = "Pixel"
    SuperReincarnated = "Super Reincarnated"


class Server(Enum):
    JP = 0
    NA = 1
    KR = 2


class AwakeningRestrictedLatent(Enum):
    """Latent awakenings with availability gated by having an awakening"""
    UnmatchableClear = 606
    SpinnerClear = 607
    AbsorbPierce = 608


def enum_or_none(enum, value, default=None):
    if value is not None:
        return enum(value)
    else:
        return default
