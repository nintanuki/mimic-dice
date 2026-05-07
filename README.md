# Mimic Dice

A treasure-and-mimics reskin of *Zombie Dice*, built in Python and Pygame for a custom arcade cabinet.

---

## About

Mimic Dice is a "press your luck" party dice game inspired by [Zombie Dice](https://en.wikipedia.org/wiki/Zombie_Dice) (Steve Jackson Games, 2010). The mechanics stay faithful to the original; the theme is reimagined as a dungeon crawl where adventurers crack open chests hoping for treasure and praying they don't wake a mimic.

| Zombie Dice | Mimic Dice |
| --- | --- |
| Brain | Treasure Chest |
| Runner | Empty Chest |
| Shotgun Blast | Mimic |

This project is part of a larger arcade cabinet build. The cabinet runs an in-house launcher; Mimic Dice is one of several games written for it.

## Status

**Phase 1 — Playable Prototype** (in progress).
The dice physics and tray rendering are working. Game loop, scoring, turn flow, and AI opponents are next. See [docs/TODO.md](docs/TODO.md) for the full roadmap.

## Rules

The player shakes a cup of 13 dice and randomly draws 3 without looking. Dice come in three colors with different face distributions:

- **6 green dice** — 3 brains, 1 shotgun, 2 runners (safe).
- **4 yellow dice** — 2 of each (medium).
- **3 red dice** — 1 brain, 3 shotguns, 2 runners (dangerous).

The goal is to collect **13 brains**. After each roll the player chooses to *bank* their brains and pass the turn, or *push their luck* and roll again. Runners stay on the table and are re-rolled with new dice drawn from the cup to bring the next roll back to 3 dice. **Three shotguns in a single turn busts the player and wipes their brains for that turn.** First to 13 brains wins, with all other players getting one final turn to tie or beat them.

> *Source: paraphrased from [Zombie Dice — Wikipedia](https://en.wikipedia.org/wiki/Zombie_Dice).*

## Requirements

- Python 3.10+
- [Pygame](https://www.pygame.org/) 2.5+

## Install & Run

```powershell
git clone <repo-url> mimic-dice
cd mimic-dice
pip install -r requirements.txt
python main.py
```

### Controls (current prototype)

| Action | Keyboard | Controller |
| --- | --- | --- |
| Roll dice | `Space` | — *(TBD)* |
| Toggle fullscreen | `F11` | `Back` |
| Quit | Close window | `Start + Back + L1 + R1` |

## Project Structure

```
mimic-dice/
├── main.py              # Entry point and GameManager (thin coordinator).
├── settings.py          # All tunable constants. No magic numbers elsewhere.
├── crt.py               # CRT scanline + flicker post-process overlay.
├── requirements.txt     # Python package dependencies.
├── systems/             # Gameplay systems (dice physics, tray, etc.).
├── ui/                  # UI widgets and screens.
├── core/                # Cross-cutting helpers shared by systems.
├── utils/               # Generic utilities (e.g. spritesheet slicer).
├── assets/              # Graphics, audio, and fonts.
├── legacy/              # Reference code, including the AI bots from
│                        # "Automate the Boring Stuff" used as Phase 2 AI.
└── docs/                # Project documentation (read these in order below).
```

## Documentation

Read these in order before contributing:

1. **[README.md](README.md)** — *(this file)* what the project is and how to run it.
2. **[docs/TODO.md](docs/TODO.md)** — phased roadmap and known challenges.
3. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — how the code actually works.
4. **[docs/CHANGELOG.md](docs/CHANGELOG.md)** — append-only history of every change.
5. **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — required reading for every editor, human or AI.

## Credits

- Original game design: *Zombie Dice* by Steve Jackson Games.
- AI bot reference: Al Sweigart, *[Automate the Boring Stuff with Python](https://automatetheboringstuff.com/)*. See [legacy/zombie-dice-bots/](legacy/zombie-dice-bots/).
- Sprite attributions: [assets/graphics/sprites/attributions.md](assets/graphics/sprites/attributions.md).