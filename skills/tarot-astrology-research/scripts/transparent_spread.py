#!/usr/bin/env python3
"""Create a reproducible Tarot draw from a visible seed and a standard card list."""
from __future__ import annotations

import argparse
import hashlib
import json
import random

MAJOR = "The Fool|The Magician|The High Priestess|The Empress|The Emperor|The Hierophant|The Lovers|The Chariot|Strength|The Hermit|Wheel of Fortune|Justice|The Hanged Man|Death|Temperance|The Devil|The Tower|The Star|The Moon|The Sun|Judgement|The World".split("|")
SUITS = ("Wands", "Cups", "Swords", "Pentacles")
CARDS = MAJOR + [f"{rank} of {suit}" for suit in SUITS for rank in ("Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King")]


def draw(seed: str, count: int = 3) -> dict:
    if not 1 <= count <= 10:
        raise ValueError("count must be between 1 and 10")
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big"))
    deck = CARDS.copy()
    rng.shuffle(deck)
    cards = [{"position": i + 1, "card": deck[i], "reversed": bool(rng.getrandbits(1))} for i in range(count)]
    return {"seed": seed, "deck_size": len(CARDS), "cards": cards, "warning": "Symbolic reflection only; not a forecast."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, help="A user-visible seed, not a secret")
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(draw(args.seed, args.count), indent=2))
