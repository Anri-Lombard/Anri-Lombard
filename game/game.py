"""Hulk Smash: a bug-smashing game played through GitHub issues.

Usage: ISSUE_TITLE='smash|7' ISSUE_USER=octocat python game/game.py
Prints a one-line result for the issue comment.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "game" / "state.json"
README = ROOT / "README.md"
REPO = "Anri-Lombard/Anri-Lombard"
ROWS, COLS = 3, 8
CELLS = ROWS * COLS


def new_state():
    return {"round": 1, "smashed": [], "total": 0, "leaderboard": {}, "recent": []}


def smash(state, cell, user):
    """Apply a move. Returns a message; mutates state."""
    if not 0 <= cell < CELLS:
        return f"There is no bug #{cell}. Hulk is confused."
    if cell in state["smashed"]:
        return f"Bug #{cell} is already a puddle. Pick a live one!"
    state["smashed"].append(cell)
    state["total"] += 1
    state["leaderboard"][user] = state["leaderboard"].get(user, 0) + 1
    state["recent"] = [f"@{user} smashed bug #{cell}"] + state["recent"][:4]
    if len(state["smashed"]) == CELLS:
        state["recent"][0] = f"@{user} smashed the LAST bug and cleared round {state['round']}!"
        state["round"] += 1
        state["smashed"] = []
        return f"HULK SMASH! You cleared round {state['round'] - 1}. A fresh swarm has appeared."
    return f"HULK SMASH! Bug #{cell} is no more. {CELLS - len(state['smashed'])} to go."


def cell_html(i, smashed):
    if i in smashed:
        return '<img src="game/splat.svg" width="56" alt="smashed">'
    url = (f"https://github.com/{REPO}/issues/new?title=smash%7C{i}"
           "&body=Just+hit+%22Create%22.+Hulk+handles+the+rest+%F0%9F%92%9A")
    return f'<a href="{url}"><img src="game/bug.svg" width="56" alt="bug {i}"></a>'


def render(state):
    rows = "\n".join(
        "".join(cell_html(r * COLS + c, state["smashed"]) for c in range(COLS)) + "<br>"
        for r in range(ROWS)
    )
    top = sorted(state["leaderboard"].items(), key=lambda kv: -kv[1])[:5]
    board = "\n".join(f"| {n} | [@{u}](https://github.com/{u}) | {s} |" for n, (u, s) in enumerate(top, 1))
    recent = "\n".join(f"- {r}" for r in state["recent"]) or "- Nobody yet. Be the first!"
    return f"""<!-- GAME:START -->
### 💚 Hulk smash! Help me squash these bugs

Click a bug, hit **Create**, and in about a minute it's a puddle. Round **{state['round']}**, **{state['total']}** bugs smashed all-time.

<p align="center">
{rows}
</p>

<details>
<summary>🏆 Leaderboard and recent smashes</summary>

| # | Smasher | Bugs |
|---|---|---|
{board or "| - | nobody yet | 0 |"}

{recent}

</details>
<!-- GAME:END -->"""


def write_readme(state):
    text = README.read_text()
    text = re.sub(r"<!-- GAME:START -->.*<!-- GAME:END -->", lambda _: render(state), text, flags=re.S)
    README.write_text(text)


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else new_state()
    m = re.fullmatch(r"smash\|(\d{1,3})", os.environ.get("ISSUE_TITLE", "").strip())
    if not m:
        print("That's not a smash command. Use the links in the README!")
        sys.exit(0)
    user = os.environ["ISSUE_USER"]
    print(smash(state, int(m.group(1)), user))
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    write_readme(state)


if __name__ == "__main__":
    main()
