# Pong Game

Repo for pong game built with AI

## Overview

This is a classic **Pong** game built with Python and Pygame. It features a single-player mode where you compete against an AI opponent on an 800×600 arena. The game includes:

- Smooth paddle and ball physics with spin and speed scaling on each hit
- An AI opponent that tracks the ball with slight imperfection to keep games competitive
- Sound effects (paddle hits, wall bounces, scoring, and a win fanfare) generated in real time — no audio files required
- A dark, neon-styled visual theme (cyan player vs. magenta computer)
- Score display and a "first to 7 wins" victory condition

## Instructions

### Requirements

- Python 3.8 or higher
- [Pygame](https://www.pygame.org/) 2.0.0 or higher

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/dbacademy/pong-game.git
   cd pong-game
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Game

```bash
python pong.py
```

### Controls

| Key | Action |
|-----|--------|
| `W` or `↑` | Move paddle up |
| `S` or `↓` | Move paddle down |
| `R` | Restart after a game ends |
| `ESC` | Quit the game |

### How to Play

- You control the **left paddle** (cyan); the computer controls the **right paddle** (magenta).
- Use the controls above to move your paddle and deflect the ball past the opponent.
- The first player to reach **7 points** wins.
- After a winner is declared, press **R** to start a new game. 
