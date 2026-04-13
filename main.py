import random
import csv

# ==========================================
# 1. DYNAMIC BID COST
# ==========================================
def bid_cost(price, base_cost=1.0, alpha=5.0):
    # Calculates the entry fee for placing a bid.
    # We use an inversely proportional formula so that lower bids cost more.
    # The '+ 1' in the denominator ensures we never divide by zero if a player bids exactly 0.
    return base_cost + alpha / (price + 1)

# ==========================================
# 2. AI PLAYER STRATEGIES
# ==========================================
def strategy_random(player, max_price=20):
    # Baseline bot: picks a completely random number.
    return random.randint(0, max_price)

def strategy_low_bias(player, max_price=20):
    # Aggressive bot: rolls two random numbers and keeps the smallest one using min().
    # This statistical trick naturally pulls the average bid downwards over time.
    return min(random.randint(0, max_price), random.randint(0, max_price))

def strategy_avoid_zero(player, max_price=20):
    # Smart/Frugal bot: realizes that bidding 0 or 1 carries a huge entry fee.
    # It starts its random range at 2 to save money on participation costs.
    return random.randint(2, max_price)

# ==========================================
# 3. SINGLE ROUND ENGINE
# ==========================================
def run_round(bids, base_cost=1.0, alpha=5.0):
    # We use a custom Binary Search Tree (BST) to efficiently sort the bids.
    bst = BST()
    for player, price in bids:
        bst.insert(price, player)

    # inorder() gives us the sorted list, and lowest_unique() finds the winner.
    inorder = bst.inorder()
    winner_price, winner = bst.lowest_unique()

    # Calculate the financial cost for every player in this round.
    costs = {}
    for player, price in bids:
        c = bid_cost(price, base_cost, alpha)
        costs[player] = costs.get(player, 0) + c

    # The seller's revenue is the sum of all entry fees paid by the players.
    revenue = sum(costs.values())

    # Return a clean dictionary with all the round data for the frontend/GUI to use.
    return {
        "bst": bst,
        "inorder": inorder,
        "winner": winner,
        "winner_price": winner_price,
        "costs": costs,
        "revenue": revenue,
        "bids": bids,
    }

# ==========================================
# 4. MULTI-ROUND SIMULATION
# ==========================================
def run_multi_rounds(rounds_data, base_cost=1.0, alpha=5.0):
    # Variables to track long-term statistics across multiple rounds.
    player_stats = {}
    round_results = []
    revenues = []

    for round_id, bids in rounds_data.items():
        # Execute the round logic
        result = run_round(bids, base_cost, alpha)
        round_results.append((round_id, result))
        revenues.append(result["revenue"])

        winner = result["winner"]
        winner_price = result["winner_price"]

        # Update the lifetime stats for each participant
        for player, price in bids:
            # Initialize the player's profile if it doesn't exist yet
            if player not in player_stats:
                player_stats[player] = {"wins": 0, "total_cost": 0.0, "total_profit": 0.0}

            cost = result["costs"].get(player, 0)
            player_stats[player]["total_cost"] += cost

            # Calculate Net Profit:
            # If they win, they gain the item's value (price) minus their entry fee.
            # If they lose, they just lose their entry fee.
            if player == winner:
                player_stats[player]["wins"] += 1
                player_stats[player]["total_profit"] += (winner_price - cost)
            else:
                player_stats[player]["total_profit"] -= cost

    return player_stats, round_results, revenues

# ==========================================
# 5. CSV DATA LOADERS
# ==========================================
def load_single_round_csv(path):
    # Reads bid data from a CSV file for a single round.
    # Expected CSV format requires a 'joueur' column and a 'prix' column.
    bids = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bids.append((row["joueur"], int(row["prix"])))
    return bids

def load_multi_round_csv(path):
    # Reads a large CSV dataset containing multiple rounds.
    # Expected CSV format: 'manche', 'joueur', 'prix'.
    rounds = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = int(row["manche"])
            # Groups the bids into a dictionary using the round ID ('manche') as the key.
            # setdefault() is an optimized way to append to a list within a dict.
            rounds.setdefault(m, []).append((row["joueur"], int(row["prix"])))
    return rounds

# ─────────────────────────────────────────
# Player strategies
# ─────────────────────────────────────────

# Strategy 1: pick a completely random price between 0 and max_price
def strategy_random(player, max_price=20):
    return random.randint(0, max_price)

# Strategy 2: pick the lower of two random prices it favours small prices without always going to zero
def strategy_low_bias(player, max_price=20):
    return min(random.randint(0, max_price), random.randint(0, max_price))

# Strategy 3: never bid 0 or 1 to avoid the high risk premium on very low prices
def strategy_avoid_zero(player, max_price=20):
    return random.randint(2, max_price)

# Strategy 4: use the history of past rounds to make a smarter choice
def strategy_smart(player, max_price=20, history=None):

    # no history yet, just pick a small random price to start
    if history is None or len(history) == 0:
        return random.randint(1, max_price // 4)

    # count how many times each price was played in the last 10 rounds
    frequences = {}
    for ronde in history[-10:]:
        for _, p in ronde:
            if p not in frequences:
                frequences[p] = 0
            frequences[p] += 1

    # find the smallest price that appeared exactly once (was unique)
    # that price had a good chance of winning, so we try it again
    for prix in range(0, max_price + 1):
        if frequences.get(prix, 0) == 1:
            return prix

    # if no price was unique, find the smallest price nobody played
    # an unplayed price is very likely to be unique this round
    for prix in range(0, max_price + 1):
        if prix not in frequences:
            return prix

    # last resort: everything has been played, just pick a small random price
    return random.randint(0, max_price // 4)


# dictionary that maps strategy names to their functions
# used in gui.py to call a strategy by name
STRATEGIES = {
    "Random":    strategy_random,
    "LowBias":   strategy_low_bias,
    "AvoidZero": strategy_avoid_zero,
    "Smart":     strategy_smart,
}

