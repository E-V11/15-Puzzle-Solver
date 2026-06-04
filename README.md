# 15-Puzzle Solver

An optimal solver for the 15-puzzle implemented in Python, using Iterative Deepening A* (IDA*) search with a Manhattan distance and linear conflict heuristic. Solves any solvable configuration optimally, meaning the solution returned is always the shortest possible sequence of moves.

## What is the 15-Puzzle?

The 15-puzzle is a 4x4 sliding tile puzzle containing tiles numbered 1-15 and one blank space. The objective is to reach the canonical ordering by sliding tiles into the blank one at a time. Despite its simple appearance the state space contains approximately 10^13 reachable configurations, making brute force search completely infeasible.

---

## How it Works

### IDA* Search

IDA* (Iterative Deepening A*) performs a series of depth-first searches each bounded by a cost threshold. The threshold begins at the heuristic value of the initial state and is raised each iteration to the minimum f-value that exceeded the previous bound:

    f(n) = g(n) + h(n)

where g(n) is the path cost from the root and h(n) is the heuristic estimate of the remaining cost. This gives IDA* the optimality guarantees of A* at a fraction of the memory cost — O(d) rather than O(b^d) where d is solution depth and b is the branching factor.

### Heuristic

The heuristic combines two admissible components:

**Manhattan Distance** — for each tile, the sum of horizontal and vertical distances from its current position to its goal position. Never overestimates, satisfying admissibility.

**Linear Conflict** — two tiles are in linear conflict if both belong in the same row or column but are in the wrong order relative to each other. Each conflict requires at least 2 additional moves to resolve. Adding this penalty on top of Manhattan distance produces a strictly tighter lower bound, substantially reducing nodes expanded.

    h(s) = manhattan(s) + 2 * (row_conflicts(s) + col_conflicts(s))

### Solvability

Not all 15-puzzle configurations are reachable. The program checks solvability by counting inversions and checking the blank tile's row from the bottom. A configuration is solvable if and only if:

    (blank on even row from bottom AND odd inversions)
    OR
    (blank on odd row from bottom AND even inversions)

## Performance

Benchmarked across 60 boards of controlled difficulty (scramble depth 10-120), the solver handles the majority of configurations well. Solve time grows non-linearly with board complexity — easy boards solve in milliseconds while harder configurations can take tens of seconds. Boards requiring more than roughly 52 optimal moves begin to approach the 3-minute timeout.

| Scramble Depth | Avg Solve Time | Avg Moves |
|---|---|---|
| 10-30 | < 0.01s | 10-26 |
| 40-60 | 0.1-5s | 28-44 |
| 70-90 | 0.5-6s | 36-48 |
| 100-120 | 1-26s | 38-58 |

## Features

- Optimal IDA* solver with Manhattan distance and linear conflict
- Heuristic caching for repeated state lookups
- Solvability validation before search
- Random board generation with guaranteed solvability
- User-defined board input with full validation
- Configurable timeout with clean early exit via background thread
- Step-by-step solution output
- Full run logging to results.txt
- Benchmark mode generating CSV data across controlled difficulty levels
- 10 automated unit tests covering all core functions

## Usage

Requires Python 3.8+. No external dependencies.

Run the program with:

    python puzzle.py

On launch the program runs all tests, then prompts:

    Run (b)enchmark or (s)olver? [b/s]:

**Solver mode** — generate a random board or enter your own 16 space-separated integers (0-15, where 0 is the blank):

    > 1 2 3 4 5 6 7 8 9 10 11 12 13 14 0 15

**Benchmark mode** — solve N boards and save results to benchmark.csv:

    How many boards?: 60
    Timeout per board in seconds? [30 recommended]: 30
    Mode — (r)andom or (c)ontrolled?: c
    Min scramble depth?: 10
    Max scramble depth?: 60
    Step size?: 10

## Project Structure

    15-Puzzle-Solver/
    ├── python/
    │   └── puzzle.py
    ├── docs/
    │   ├── paper.tex
    │   └── paper.pdf
    ├── .gitignore
    └── README.md
  
