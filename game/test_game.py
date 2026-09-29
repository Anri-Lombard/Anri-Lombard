from game import CELLS, new_state, render, smash

s = new_state()
assert "no more" in smash(s, 3, "a")
assert "puddle" in smash(s, 3, "b") and s["total"] == 1
assert "no bug" in smash(s, CELLS, "a")
for i in range(CELLS):
    if i != 3:
        smash(s, i, "a")
assert s["round"] == 2 and s["smashed"] == [] and s["leaderboard"] == {"a": CELLS}
assert "cleared round 1" in s["recent"][0]
assert render(s).count("bug.svg") == CELLS
print("ok")
