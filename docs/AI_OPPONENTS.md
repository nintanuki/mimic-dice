# AI Opponents Guide

This document breaks down the behavior, logic, and difficulty levels of the AI bots available in Mimic Dice. 

## Simulation Results (100,000 Games)
To determine these tiers, I ran 100,000 games with all 11 bots competing simultaneously.

| Name | Wins | Ties | Win % | Tier |
| :--- | :--- | :--- | :--- | :--- |
| **Carl** | 14960 | 369 | 14.96% | Expert |
| **Negan** | 14940 | 383 | 14.94% | Expert |
| **Maggie** | 13911 | 390 | 13.91% | Hard |
| **Alice** | 13395 | 354 | 13.39% | Hard |
| **Daryl** | 13249 | 355 | 13.24% | Hard |
| **Rick** | 11230 | 382 | 11.23% | Medium |
| **Lizzie** | 10113 | 298 | 10.11% | Medium |
| **Shane** | 4705 | 188 | 4.70% | Easy |
| **Eugene** | 1447 | 87 | 1.44% | Very Easy |
| **Bob** | 635 | 47 | 0.63% | Very Easy |
| **Morgan** | 0 | 0 | 0.00% | Tutorial |

---

## Difficulty Tiers

### 💀 Expert Tier
*Top-tier bots that utilize aggressive "Calculated Greed."*

* **Carl:** The most efficient bot. He pushes for a massive 7-brain count but has a safety check: he will stop if he has at least 2 shotguns and 1 brain banked.
* **Negan:** Nearly identical to Carl, but slightly more conservative with a 6-brain threshold.

### ⚔️ Hard Tier
*Strong, consistent strategies that provide a solid challenge.*

* **Maggie:** The "Heavy Hitter" of the Hard tier. She plays similarly to the Experts (5-brain threshold) and consistently outperforms the standard bots.
* **Alice:** The "Baseline" bot. Her strategy is simple: stop exactly at 2 shotguns. No more, no less.
* **Daryl:** A balanced bot that stops at 5 brains if he has even a single shotgun, or immediately at 2 shotguns.

### ⚖️ Medium Tier
*Bots with specific logical flaws or predictable patterns.*

* **Rick:** Overly cautious. He stops at 5 brains or 2 shotguns. By stopping early on brains, he often fails to keep pace during high-scoring rounds.
* **Lizzie:** The "Gambler." She attempts to track the number of red dice remaining. While clever, this often lures her into taking "statistically safe" rolls that end in a bust.

### 🌱 Easy Tier
*Chaotic or rigid bots that are very easy for a human to outplay.*

* **Shane:** Rolls a random number of times (1-4) regardless of what the dice show.
* **Eugene:** Flips a coin (50/50 chance) to decide whether to continue after every roll.
* **Bob:** Stubborn. He refuses to stop until he has at least 2 brains, even if he is sitting on 2 shotguns.

### 🎓 Tutorial Tier
*The "Punching Bag" for new players.*

* **Morgan:** Has a logical error where he only stops if he has more shotguns than brains. Since he starts at 0/0, he effectively rolls until he busts every single turn. He is mathematically incapable of winning.