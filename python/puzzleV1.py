import random
import datetime
import threading
import sys
import csv
import time
import math

sys.setrecursionlimit(1000000) #sets max recursion depth so program doesnt return recursionerror

GOAL_STATE = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0) #solved state of the puzzle
_heuristic_cache = {}                                                   #cache for heuristic values

def print_board(state):
    for r in range(4):
        row = ""
        for c in range(4):
            val = state[r * 4 + c]
            if val == 0:
                row += "  _"
            else:
                row += f"{val:3}"
        print(row)
    print()
#Prints the 15-puzzle board as a 4x4 grid, displaying _ for the blank tile (0) and right-aligned numbers for the rest

def get_neighbors(state):
    blank = state.index(0)       #find blank tile position
    r = blank // 4               #convert to row
    c = blank % 4                #convert to col
    neighbors = []

    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: #Up/down/left/right
        new_r = r + dr
        new_c = c + dc

        if new_r >= 0 and new_r < 4 and new_c >= 0 and new_c < 4:
            new_index = new_r * 4 + new_c
            lst = list(state)
            lst[blank], lst[new_index] = lst[new_index], lst[blank] #swaps blank tile
            neighbors.append(tuple(lst))
    return neighbors

def manhattan(state):
    total = 0
    for i in range(16):
        val = state[i]
        if val != 0:                          #skips blank tile
            goal_row = (val - 1) // 4        #target row
            goal_col = (val - 1) % 4         #target col
            curr_row = i // 4
            curr_col = i % 4
            total += abs(curr_row - goal_row) + abs(curr_col - goal_col) #sum of distances
    return total

def heuristic(state):
    if state in _heuristic_cache:             #return cached value if available
        return _heuristic_cache[state]

    conflict = 0

    for row in range(4):   # check rows
        tiles = []
        for col in range(4):
            val = state[row * 4 + col]
            if val != 0:
                goal_row = (val - 1) // 4
                goal_col = (val - 1) % 4
                if goal_row == row:           #tile belongs to row
                    tiles.append((val, col, goal_col))
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                if tiles[i][2] > tiles[j][2]:
                    conflict += 2             # +2 for every linear conflict

    for col in range(4): # check columns
        tiles = []
        for row in range(4):
            val = state[row * 4 + col]
            if val != 0:
                goal_row = (val - 1) // 4
                goal_col = (val - 1) % 4
                if goal_col == col:           #tile belongs in col
                    tiles.append((val, row, goal_row))
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                if tiles[i][2] > tiles[j][2]:
                    conflict += 2

    result = manhattan(state) + conflict      #manhattan and conflict penalty
    _heuristic_cache[state] = result          #cache result before returning
    return result

def solve(initial, timeout_seconds=180):
    if initial == GOAL_STATE:
        return [initial], 0, False

    data = {"explored": 0, "timed_out": False}
    stop_event = threading.Event()

    def timer():
        stop_event.wait(timeout_seconds)
        if not stop_event.is_set():
            data["timed_out"] = True          #signals timeout to search
    t = threading.Thread(target=timer, daemon=True)
    t.start()

    def search(path, g, threshold):
        if data["timed_out"]:
            return "TIMEOUT"
        state = path[-1]
        f = g + heuristic(state)
        if f > threshold:
            return f                          # Prune; return f as next threshold candidate
        data["explored"] += 1
        if state == GOAL_STATE:
            return "FOUND"
        minimum = float("inf")
        path_set = set(path)                  # Fast visited lookup
        for nb in get_neighbors(state):
            if nb not in path_set:
                path.append(nb)
                result = search(path, g + 1, threshold)
                if result in ("FOUND", "TIMEOUT"):
                    return result
                if result < minimum:
                    minimum = result
                path.pop()
        return minimum

    threshold = heuristic(initial)            # IDA* starting threshold
    path = [initial]
    while True:
        result = search(path, 0, threshold)
        if result == "FOUND":
            stop_event.set()
            return path, data["explored"], False
        if result == "TIMEOUT":
            stop_event.set()
            return None, data["explored"], True
        if result == float("inf"):            # No solution exists
            stop_event.set()
            return None, data["explored"], False
        threshold = result                    # Raise threshold and retry

def is_solvable(state):
    tiles = [t for t in state if t != 0]

    inversions = 0
    for i in range(len(tiles)):
        for j in range(i + 1, len(tiles)):
            if tiles[i] > tiles[j]:
                inversions += 1              # Count pairs out of order

    blank_row_from_bottom = 4 - (state.index(0) // 4)
    even_row = blank_row_from_bottom % 2 == 0
    odd_row  = blank_row_from_bottom % 2 != 0

    #blank on even row from bottom requires odd inversions, odd row requires even inversions
    return (even_row and inversions % 2 == 1) or (odd_row and inversions % 2 == 0)

def generate_random_board():
    tiles = list(range(16))
    random.shuffle(tiles)
    state = tuple(tiles)
    if not is_solvable(state):
        nz = [i for i in range(16) if tiles[i] != 0]
        tiles[nz[0]], tiles[nz[1]] = tiles[nz[1]], tiles[nz[0]]  # Swap 2 non-blank tiles to fix parity
        state = tuple(tiles)
    return state

def scramble_board(n_moves):
    # Generate a board of known difficulty by making n random moves from goal state
    state = GOAL_STATE
    prev = None
    for _ in range(n_moves):
        neighbors = [nb for nb in get_neighbors(state) if nb != prev]  # avoid immediate backtrack
        prev = state
        state = random.choice(neighbors)
    return state

def get_user_board():
    print("Enter 16 numbers (0-15, space-separated), where 0 = blank:")
    try:
        nums = list(map(int, input("> ").split()))
        if len(nums) != 16 or sorted(nums) != list(range(16)):   # Validate exact tile set
            print("Error: must use each of 0-15 exactly once.")
            return None
        if not all(isinstance(n, int) for n in nums):            # Safety check
            print("Error: non-integer value detected.")
            return None
        return tuple(nums)
    except ValueError:
        print("Error: integers only.")
        return None
    except Exception as e:
        print(f"Unexpected error reading board: {e}")
        return None

def print_solution(path):
    if len(path) == 1:
        print("This board is already solved!")
        print_board(path[0])
        return
    for i in range(len(path)):
        print("Initial Board:" if i == 0 else f"Move {i}:")
        print_board(path[i])
    print(f"Solved in {len(path) - 1} move(s)!")

def save_results(initial, path, stats):
    def board_str(s):
        result = ""
        for r in range(4):
            for c in range(4):
                val = s[r * 4 + c]
                result += "  _" if val == 0 else f"{val:3}"
            result += "\n"
        return result

    try:
        with open("results.txt", "a") as f:  # Append to results file
            f.write("=" * 40 + "\n")
            f.write(f"Timestamp      : {stats['timestamp']}\n")
            f.write(f"Moves to solve : {stats['moves']}\n")
            f.write(f"States explored: {stats['states_explored']}\n")
            f.write(f"Timed out      : {stats['timed_out']}\n")
            f.write(f"Initial Board:\n{board_str(initial)}\n")
            if not stats["timed_out"] and path is not None:
                for i in range(len(path)):
                    f.write("Initial:\n" if i == 0 else f"Move {i}:\n")
                    f.write(board_str(path[i]) + "\n")
                f.write("Board was already solved!\n" if stats["moves"] == 0 else f"Solved in {stats['moves']} move(s)!\n")
            else:
                f.write("No solution found within the time limit.\n")
            f.write("=" * 40 + "\n\n")
    except IOError as e:
        print(f"Error saving results: {e}")

def get_board_features(state):
    # Extract observable features from a board state for regression analysis
    return {
        "initial_manhattan" : manhattan(state),
        "initial_conflicts" : heuristic(state) - manhattan(state),
        "initial_heuristic" : heuristic(state),
        "blank_position"    : state.index(0),
        "tiles_in_place"    : sum(1 for i in range(16) if state[i] == i + 1)
    }

def run_benchmark(n=100, timeout_seconds=30, mode="random", scramble_depths=None):
    # mode="random" uses fully random boards
    # mode="controlled" uses scramble_board across specified depths
    print(f"Running benchmark on {n} boards...")
    print(f"Timeout per board: {timeout_seconds}s")
    print(f"Mode: {mode}\n")

    results = []

    if mode == "controlled" and scramble_depths is not None:
        boards = [(scramble_board(d), d) for d in scramble_depths]
    else:
        boards = [(generate_random_board(), -1) for _ in range(n)]

    for i, (board, depth) in enumerate(boards):
        features = get_board_features(board)

        start = time.time()
        path, explored, timed_out = solve(board, timeout_seconds=timeout_seconds)
        elapsed = round(time.time() - start, 4)

        results.append({
            "board_id"          : i + 1,
            "scramble_depth"    : depth,                           # known difficulty, -1 if random
            "solve_time"        : elapsed,
            "moves"             : len(path) - 1 if path else -1,
            "states_explored"   : explored,
            "log_states"        : round(math.log1p(explored), 6),  # log(1 + states) to handle 0
            "timed_out"         : timed_out,
            **features
        })

        status = "TIMEOUT" if timed_out else f"{len(path)-1} moves"
        print(f"Board {i+1}/{len(boards)} — depth {depth} — {status} — {elapsed}s")

    with open("benchmark.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"\nBenchmark complete. Results saved to benchmark.csv")
    return results

def main():
    print("=" * 40)
    print("     Welcome to the 15-Puzzle Solver")
    print("=" * 40)
    print()

    try:
        choice = input("Generate a (r)andom board or (e)nter your own? [r/e]: ").strip().lower()
        if not (choice == "r" or choice == "e"):
            print("Unrecognized choice -- defaulting to random board.")
            choice = "r"
    except EOFError:
        print("No input detected -- defaulting to random board.")
        choice = "r"

    initial = get_user_board() or generate_random_board() if choice == "e" else generate_random_board()

    print()
    print("Starting board:")
    print_board(initial)

    if not is_solvable(initial):
        print("Unsolvable board. Exiting.")
        return

    if initial == GOAL_STATE:
        print("This board is already solved! Nothing to do.")
        stats = {
            "timestamp"      : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "moves"          : 0,
            "states_explored": 0,
            "timed_out"      : False,
        }
        save_results(initial, [initial], stats)
        print("Results saved to results.txt")
        return

    print("Solving with IDA* + linear conflict...")
    print("(Time limit: 3 minutes)")
    print()

    try:
        path, explored, timed_out = solve(initial, timeout_seconds=180)
    except RecursionError:
        print("Recursion limit hit -- puzzle may be too deep to solve.")
        return

    stats = {
        "timestamp"      : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "moves"          : len(path) - 1 if path else 0,
        "states_explored": explored,
        "timed_out"      : timed_out,
    }

    if timed_out:
        print()
        print("WARNING: This board exceeded the 3 minute time limit.")
        print(f"  States explored before giving up: {explored:,}")
        print("  This board is too complex to solve in a reasonable amount of time.")
        print("  Try entering a different board or generating a new random one.")
        save_results(initial, None, stats)
        print("Partial results saved to results.txt")
        return

    if not path:
        print("No solution found.")
        return

    print_solution(path)
    save_results(initial, path, stats)
    print("Results saved to results.txt")
    print(f"States explored: {explored:,}")

def run_tests():
    assert manhattan(GOAL_STATE) == 0                                                                       # test 1: solved board = 0 distance
    assert manhattan((1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15)) == 1                                        # test 2: one tile off by one step
    assert is_solvable(GOAL_STATE)                                                                          # test 3: goal is solvable
    assert not is_solvable((2,1,3,4,5,6,7,8,9,10,11,12,13,14,15,0))                                       # test 4: known unsolvable
    assert len(get_neighbors((0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15))) == 2                                # test 5: corner blank = 2 neighbors
    path, explored, timed_out = solve(GOAL_STATE)
    assert path == [GOAL_STATE] and explored == 0 and not timed_out                                        # test 6: already solved
    path, _, timed_out = solve((1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15))
    assert path is not None and len(path) == 2 and not timed_out                                           # test 7: one move away
    assert scramble_board(10) != GOAL_STATE                                                                 # test 9: scrambled board is not goal
    assert is_solvable(scramble_board(20))                                                                  # test 10: scrambled board is always solvable
    try:
        save_results(GOAL_STATE, [GOAL_STATE], {"timestamp":"2026-01-01 00:00:00","moves":0,"states_explored":0,"timed_out":False})
        assert "2026-01-01 00:00:00" in open("results.txt").read()                                         # test 8: results.txt written
    except IOError:
        print("Warning: could not verify results.txt in tests.")
    print("All tests passed.")

if __name__ == "__main__":
    run_tests()
    print()
    mode = input("Run (b)enchmark or (s)olver? [b/s]: ").strip().lower()
    if mode == "b":
        n = int(input("How many boards?: "))
        t = int(input("Timeout per board in seconds? [30 recommended]: "))
        m = input("Mode — (r)andom or (c)ontrolled?: ").strip().lower()
        if m == "c":
            low   = int(input("Min scramble depth?: "))
            high  = int(input("Max scramble depth?: "))
            step  = int(input("Step size?: "))
            depths = list(range(low, high + 1, step)) * (n // ((high - low) // step + 1))
            run_benchmark(n, timeout_seconds=t, mode="controlled", scramble_depths=depths)
        else:
            run_benchmark(n, timeout_seconds=t, mode="random")
    else:
        main()
