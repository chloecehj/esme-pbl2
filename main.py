import random
import csv
class Node:
    def __init__(self, price):
        self.price   = price  # the bid amount this node represents
        self.players = []     # all players who placed this exact bid amount
        self.left    = None   # left child = holds a lower price
        self.right   = None   # right child = holds a higher price

class BST:
    def __init__(self):
        self.root = None  # tree starts empty; first insert will set this

# ── insertion ──────────────────────────────────────────────────────────────

    def insert(self, price, player):
        if self.root is None:
            self.root = Node(price)        # first bid ever = becomes the root
            self.root.players.append(player)    # register the player at this price
        else:
            self._insert(self.root, price, player)    # tree exists = recurse into it
        
    def _insert(self, node, price, player):
        if price == node.price:
            node.players.append(player)    # price already exists = just add the player (bid is now non-unique)    
        elif price < node.price:
            if node.left is None:
                node.left = Node(price)      # empty left slot = create a new node here
                node.left.players.append(player)    # register the player
            else:
                self._insert(node.left, price, player)    # keep walking left
        else:
            if node.right is None:
                node.right = Node(price)           # empty right slot = create a new node here
                node.right.players.append(player)    # register the player
            else:
                self._insert(node.right, price, player)    # keep walking right

# ── traversal ──────────────────────────────────────────────────────────────

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result    # returns all (price, players) pairs sorted lowest = highest

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left,  result)                    # visit lower prices first
            result.append((node.price, node.players[:]))         # record this price + a copy of its players list
            self._inorder(node.right, result)                    # then visit higher prices

# ── auction logic ──────────────────────────────────────────────────────────

    def lowest_unique(self):
        for price, players in self.inorder():     # iterate from lowest price upward
            if len(players) == 1:            # only one player bid this price = it's unique
                return price, players[0]    # this player wins the auction
        return None, None    # no unique bid found (all prices tied, or tree is empty)

# ── navigation ─────────────────────────────────────────────────────────────

    def successor(self, price):
        result = [None]    # list so the recursive helper can write back to it
        self._successor(self.root, price, result)
        return result[0]    # smallest price strictly greater than the given price, or None

    def _successor(self, node, price, result):
        if node is None:
            return    # fell off the tree = stop
        if node.price > price:
            result[0] = node.price        # valid candidate = record it
            self._successor(node.left,  price, result)     # try to find something even closer (smaller but still > price)
        else:
            self._successor(node.right, price, result)    # too small or equal = go right

    def predecessor(self, price):
        result = [None]     # list so the recursive helper can write back to it
        self._predecessor(self.root, price, result)
        return result[0]     # largest price strictly less than the given price, or None

    def _predecessor(self, node, price, result):
        if node is None:
            return    # fell off the tree → stop
        if node.price < price:
            result[0] = node.price        # valid candidate = record it
            self._predecessor(node.right, price, result)    # try to find something even closer (larger but still < price)
        else:
            self._predecessor(node.left,  price, result)    # too large or equal = go left

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
    player_stats = {}
    round_results = []
    revenues = []

    for round_id, bids in rounds_data.items():
        # run the round and add the round id into the result dict
        result = run_round(bids, base_cost, alpha)
        result["round_id"] = round_id
        round_results.append(result)
        revenues.append(result["revenue"])

        winner = result["winner"]
        winner_price = result["winner_price"]

        for player, price in bids:
            if player not in player_stats:
                player_stats[player] = {"wins": 0, "total_cost": 0.0, "total_profit": 0.0}

            cost = result["costs"].get(player, 0)
            player_stats[player]["total_cost"] += cost

            if player == winner:
                player_stats[player]["wins"] += 1
                player_stats[player]["total_profit"] += (winner_price - cost)
            else:
                player_stats[player]["total_profit"] -= cost

    # build summary with win rate and average profit per round
    n_rounds = len(round_results)
    summary = {}
    for p, s in player_stats.items():
        summary[p] = {
            "wins":       s["wins"],
            "win_rate":   s["wins"] / n_rounds,
            "avg_cost":   s["total_cost"] / n_rounds,
            "avg_profit": s["total_profit"] / n_rounds,
        }

    return summary, round_results, revenues

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


# dictionary that maps strategy names to their functions
# used in gui.py to call a strategy by name
STRATEGIES = {
    "Random":    strategy_random,
    "LowBias":   strategy_low_bias,
    "AvoidZero": strategy_avoid_zero,
}

