# OPS+ Golf

A multiplayer baseball trivia game. Each round shows a **target OPS+**; every contestant
picks a real player and season, and your score is how far that season's OPS+ lands from
the target. Like golf, **low score wins**.

Created and programmed by Oliver Almeter.

## How it works

1. Enter the number of contestants and rounds.
2. Each round, the game sets a target OPS+ (random, or pick a custom target from 50-150).
3. Each contestant chooses a player and one of that player's seasons. The player field
   autocompletes as you type.
4. Points = `|season OPS+ - target OPS+|`. Lowest cumulative total after the final round wins.

A running scoreboard and a per-round leaderboard chart track everyone's progress.

## Data

`batting_data_6024.csv` - 4.2 MB of Baseball-Reference standard batting, **1954-2024**.
One row per player-season with the full counting line plus OPS+, rOBA and Rbat+.
It was scraped with the R notebook in the companion `OPS_plus_Shiny` project.

## Running from source

Requires Python 3 and:

```bash
pip install pandas matplotlib ttkthemes
```

Then:

```bash
python app.py
```

`tkinter` ships with most Python installs on Windows. The CSV must sit next to `app.py`.

## Building the Windows executable

```bash
pyinstaller app.spec
```

Output lands in `dist/`. Build artifacts are gitignored - the prebuilt Windows
build is attached to the releases page instead of being committed, since it is ~330 MB.

## Attribution

Batting data is derived from [Baseball-Reference](https://www.baseball-reference.com)
standard batting tables, scraped with the notebook in
[OPS_plus_Shiny](https://github.com/oliveralmeter/OPS_plus_Shiny). It is included here so
the game runs offline, and is redistributed for non-commercial personal use. Baseball-Reference
is a Sports Reference LLC site; please consult them directly for any other use of their data.

Built with `pandas`, `matplotlib`, `ttkthemes` and `tkinter`.
