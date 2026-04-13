import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os, threading

from main import (load_single_round_csv, load_multi_round_csv, run_round, run_multi_rounds, bid_cost, strategy_random, strategy_low_bias, strategy_avoid_zero)



HERE = os.path.dirname(os.path.abspath(__file__))
def csv_path(name):  #find CSV file
    return os.path.join(HERE, name)

def log(widget, text):  #display text
    widget.config(state="normal")
    widget.insert(tk.END, text + "\n")
    widget.see(tk.END)
    widget.config(state="disabled")

def clear(widget):#delete inserted text
    widget.config(state="normal")
    widget.delete("1.0", tk.END)
    widget.config(state="disabled")

DARK   = "#1e1e2e"
PANEL  = "#181825"
TEXT   = "#cdd6f4"
MUTED  = "#a6adc8"
BLUE   = "#89b4fa"
GREEN  = "#a6e3a1"
RED    = "#f38ba8"
YELLOW = "#f9e2af"



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LowBid — Lowest Unique Bid Wins")
        self.configure(bg=DARK)
        self.resizable(True, True)
    
        self.base_cost  = tk.DoubleVar(value=1.0)
        self.alpha      = tk.DoubleVar(value=5.0)
        self.human_bid  = tk.IntVar(value=5)
    
        #create tabs
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self._tab_demo(nb)
        self._tab_multi(nb)
        self._tab_human(nb)

    def _param_row(self, parent, label, var):
        tk.Label(parent, text=label, bg=DARK, fg=MUTED, font=("Helvetica", 10)).pack(side="left", padx=(8, 2)) #create label
        tk.Entry(parent, textvariable=var, width=6, bg="#313244", fg=TEXT, insertbackground="white", relief="flat", font=("Helvetica", 10)).pack(side="left", padx=(0, 8))  #create input

    def _log_widget(self, parent, height=22): #create scolling part
        w = scrolledtext.ScrolledText(parent, state="disabled", bg=PANEL, fg=TEXT, font=("Courier", 10), height=height)
        w.pack(fill="both", expand=True, padx=10, pady=6)
        return w

  #TAB1 : Demo Round

    def _tab_demo(self, nb):
        f = tk.Frame(nb, bg=DARK)
        nb.add(f, text="  Demo round  ")
        pf = tk.Frame(f, bg=DARK); pf.pack(fill="x", padx=10, pady=6)
        self._param_row(pf, "base_cost", self.base_cost)
        self._param_row(pf, "alpha", self.alpha)
    
        ff = tk.Frame(f, bg=DARK); ff.pack(fill="x", padx=10)
        tk.Label(ff, text="CSV file :", bg=DARK, fg=MUTED, font=("Helvetica", 10)).pack(side="left")
        self.demo_path = tk.StringVar(value=csv_path("lowbid_manche_demo.csv"))
        #show path
        tk.Entry(ff, textvariable=self.demo_path, width=52, bg="#313244", fg=TEXT, insertbackground="white", relief="flat", font=("Helvetica", 9)).pack(side="left", padx=4)
        #choose file
        tk.Button(ff, text="…", command=self._browse_demo, bg="#313244", fg=TEXT, relief="flat").pack(side="left")
        #run demo
        bf = tk.Frame(f, bg=DARK); bf.pack(pady=6)
        tk.Button(bf, text="▶  Charge and analyse", command=self._run_demo, bg=BLUE, fg=DARK, font=("Helvetica", 11, "bold"), relief="flat", padx=12, pady=5).pack(side="left", padx=6)
    
        #show results
        self.log_demo = self._log_widget(f)

    def _browse_demo(self):  #choose a file
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if p:
            self.demo_path.set(p)

    def _run_demo(self):
    #use the selected file
        clear(self.log_demo)
        w = self.log_demo
        bc, al = self.base_cost.get(), self.alpha.get()
        path = self.demo_path.get()

        try:
          bids = load_single_round_csv(path)
        except Exception as e:
          log(w, f"Loading error : {e}"); return
      #run game
        result = run_round(bids, bc, al)

        log(w, f"File : {os.path.basename(path)}")  #show path
        log(w, f"Numer of bids : {len(bids)}  |  base_cost={bc}  α={al}\n")  #show stats
        for player, price in bids:
          log(w, f"  {player:<10} → price {price:<5}  cost: {bid_cost(price,bc,al):.2f}")  #show cost

        log(w, "\n ~ BST IN-ORDER (sorted prices)")
        for price, players in result["inorder"]:
          tag = "Unique" if len(players) == 1 else f"  {len(players)} players"
          log(w, f"  price{price:<6} players={players}  {tag}")  #show BST

        #show results
        log(w, "\n ~ RESULT ~")
        if result["winner"]:
          wp = result["winner_price"]
          log(w, f"  🏆 Winner : {result['winner']}  with price {wp}")
          succ = result["bst"].successor(wp)
          pred = result["bst"].predecessor(wp)
          log(w, f"     Successor  of {wp} in the BST : {succ}")
          log(w, f"     Predecessor of {wp} in the BST : {pred}")
        else:
          log(w, "  No unique price → round cancelled, no winner.")

        log(w, f"\n  Seller revenue : {result['revenue']:.2f}")

        #who paid what
        log(w, "\n ~ COST BY PLAYER ~")
        for p, c in sorted(result["costs"].items(), key=lambda x: -x[1]):
          log(w, f"  {p:<10} paid {c:.2f}")

        #show stats
        total_bids   = len(bids)
        unique_prices = sum(1 for _, pl in result["inorder"] if len(pl) == 1)
        log(w, f"\n ~ STATISTICS ~")
        log(w, f"  Total bids : {total_bids}")
        log(w, f"  Unique prices : {unique_prices}")
        log(w, f"  Non-unique prices : {len(result['inorder']) - unique_prices}")
        avg_cost = result["revenue"] / total_bids if total_bids else 0
        log(w, f"  Average cost/bid : {avg_cost:.2f}")


#TAB2 : Multi-Round (500 rounds CSV) 

    def _tab_multi(self, nb): 
        f = tk.Frame(nb, bg=DARK) # create a frame in the notebook + background color
        nb.add(f, text="  Multi-manches (500×40)  ") # add this frame as a new tab + name 
        pf = tk.Frame(f, bg=DARK); pf.pack(fill="x", padx=10, pady=6) # creates + displays frame to input parameters

        self._param_row(pf, "base_cost", self.base_cost) # create input fields for base cost and alpha 
        self._param_row(pf, "alpha (α)", self.alpha) 

        ff = tk.Frame(f, bg=DARK); ff.pack(fill="x", padx=10) # create + display frame for file selection

        tk.Label(ff, text="CSV file :", bg=DARK, fg=MUTED, 
                 font=("Helvetica", 10)).pack(side="left") # text + color + places it on the left

        self.multi_path = tk.StringVar(value=csv_path("lowbid_multi_manches_500x40.csv")) # variable storing the path of the csv file

        tk.Entry(ff, textvariable=self.multi_path, width=52, 
                 bg="#313244", fg=TEXT, insertbackground="white", 
                 relief="flat", font=("Helvetica", 9)).pack(side="left", padx=4) # entry fiel displaying file path

        tk.Button(ff, text="…", command=self._browse_multi, 
                  bg="#313244", fg=TEXT, relief="flat").pack(side="left") # button to open file explorer

        bf = tk.Frame(f, bg=DARK); bf.pack(pady=6) # frame for the button

        tk.Button(bf, text="Run simulation", command=self._run_multi, # button that lauches simulation
                  bg=RED, fg=DARK, font=("Helvetica", 11, "bold"), 
                  relief="flat", padx=12, pady=5).pack(side="left", padx=6) 

        self.multi_status = tk.Label(bf, text="", bg=DARK, fg=YELLOW, 
                                      font=("Helvetica", 10)) # show status
        self.multi_status.pack(side="left") 
        self.log_multi = self._log_widget(f) # log scrollable text

    def _browse_multi(self): 
        p = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")]) # allows only csv files

        if p: 
            self.multi_path.set(p) # if user selcts file updates the path variable 

    def _run_multi(self): 
        clear(self.log_multi) # clear log output
        self.multi_status.config(text="Loading...") # loading status
        self.update() # to display the status immediately 

        bc, al = self.base_cost.get(), self.alpha.get() # get parameter from input above
        path   = self.multi_path.get() # get csv file selected
        w      = self.log_multi # shortcut for log widget

        def work(): 
            try: # load all rounds form csv file
                rounds_data = load_multi_round_csv(path) 

            except Exception as e: 
                self.after(0, lambda: log(w, f"Erreur : {e}")) # if error displays it in log
                return 

            summary, round_results, revenues = run_multi_rounds(rounds_data, bc, al) # run simulation on all rounds

            self.after( # sends result to main thread
                0, 
                lambda: self._display_multi(
                    w, summary, round_results, revenues, path, bc, al
                )
            ) 

        threading.Thread(target=work, daemon=True).start() # starts thread

    def _display_multi(self, w, summary, round_results, revenues, path, bc, al): 
        self.multi_status.config(text="Done") # update status

        n = len(round_results) # nb of rounds

        log(w, f"File : {os.path.basename(path)}") 
        log(w, f"Round : {n}  |  base_cost={bc}  α={al}\n") # displays file infos
 
#count winners
        win_counts = {} # dictionnary player:wins
        no_winner = 0 # for rounds without winners

        for r in round_results: 
            if r["winner"]: # +1 wins for the player
                win_counts[r["winner"]] = win_counts.get(r["winner"], 0) + 1 

            else: # if no winner for the round
                no_winner += 1 

# DISPLAY STATS
        log(w, f"No winner rounds : {no_winner} / {n}") 
        log(w, f"Average seller revenue : {sum(revenues)/n:.2f}") 
        log(w, f"Total seller revenue : {sum(revenues):.2f}\n") 

        log(w, "PLAYER RANKING (top 15)") 
        log(w, f"{'Players':<12} {'Wins':>10} {'Win rate':>9} {'Average cost':>12} {'Average revenue':>14}") # header row
        log(w, "─" * 62) # separating lines

        top = sorted(summary.items(), key=lambda x: -x[1]["wins"])[:15] # sorts player by number of wins

        for p, s in top: # shows player stat
            log(w, 
                f"{p:<12} {s['wins']:>10}"
                f"{s['win_rate']*100:>7.1f}%" 
                f"  {s['avg_cost']:>10.2f}"  
                f"{s['avg_profit']:>13.2f}"
            ) 

    # Show 5 sample rounds 

        log(w, "\nSAMPLE (first 5 rounds)") 

        for r in round_results[:5]: # 5 first rounds
            wp = r["winner_price"] 
            winner = r["winner"] or "—" 
            log(w, 
                f"Round {r['round_id']:>3} |"
                f"Winner: {winner:<10} |"
                f"Price = {wp} |" 
                f"Revenue: {r['revenue']:.2f}") 

# TAB 3 — Play vs AI

    def _tab_human(self, nb):    # create the tab frame and add it to the notebook
        f = tk.Frame(nb, bg=DARK)
        nb.add(f, text="  Play vs AI  ")

        pf = tk.Frame(f, bg=DARK); pf.pack(fill="x", padx=10, pady=6)
        self._param_row(pf, "base_cost", self.base_cost)    # parameter row: base_cost and alpha
        self._param_row(pf, "alpha (α)", self.alpha)

        # row with the bid input spinbox and submit button
        bf = tk.Frame(f, bg=DARK); bf.pack(pady=4)
        tk.Label(bf, text="Your bid:", bg=DARK, fg=TEXT,
                 font=("Helvetica", 11)).pack(side="left", padx=4)
        # spinbox lets the player pick any integer between 0 and 200
        tk.Spinbox(bf, from_=0, to=200, textvariable=self.human_bid, width=6,
                   font=("Helvetica", 11)).pack(side="left")
        # clicking Submit calls _run_human
        tk.Button(bf, text="▶  Submit", command=self._run_human,
                  bg=GREEN, fg=DARK, font=("Helvetica", 11, "bold"),
                  relief="flat", padx=10, pady=4).pack(side="left", padx=8)

        # label that shows the win counter, updated after each round
        self.score_label = tk.Label(f, text="Wins: 0 / 0",
                                     bg=DARK, fg=YELLOW, font=("Helvetica", 11, "bold"))
        self.score_label.pack()

        # scrollable text area where round results are displayed
        self.log_human = self._log_widget(f, height=18)

        # counters to track the player's score across rounds
        self.human_wins = 0
        self.human_rounds = 0

    def _run_human(self):
        # called every time the player clicks Submit
        clear(self.log_human)
        w = self.log_human
        bc, al = self.base_cost.get(), self.alpha.get()
        hp = self.human_bid.get()

        # each bot is assigned a strategy function from engine.py
        bots = {
            "Alice (Rnd)":    strategy_random,
            "Bob (Low)":      strategy_low_bias,
            "Carol (NoZero)": strategy_avoid_zero,
        }

        # build the full list of bids: human first, then each bot calls its strategy 
        # fn(p, 50) calls the strategy function with the bot name and max_price=50
        bids = [("You", hp)] + [(p, fn(p, 50)) for p, fn in bots.items()]  

        result = run_round(bids, bc, al)
        self.human_rounds += 1       # run the auction: builds the BST and finds the lowest unique price

        log(w, "=== BIDS ===") # display each bid with its cost (base_cost + alpha / (price+1))
        for player, price in bids:
            log(w, f"  {player:<14} → {price:<5}  cost: {bid_cost(price,bc,al):.2f}")

        log(w, "\n=== BST IN-ORDER ===")
        for price, players in result["inorder"]:        # display the BST in-order traversal: prices sorted from lowest to highest
            tag = "★" if len(players) == 1 else " "    # ★ means only one player bid that price (unique)
            log(w, f"  {tag} price={price:<5} → {players}")

        log(w, "\n=== RESULT ===")
        if result["winner"] == "You":
            self.human_wins += 1
            log(w, f"  🎉 YOU WIN at price {result['winner_price']}!")        # show the winner of this round
        elif result["winner"]:
            log(w, f"  {result['winner']} wins at price {result['winner_price']}.")
        else:
            log(w, "  No unique bid → no winner this round.")

        log(w, f"\n  Your cost this round : {result['costs'].get('You', 0):.2f}")
        log(w, f"  Seller revenue       : {result['revenue']:.2f}")
        log(w, "\n  Tip: pick a price others are likely to avoid.")
        log(w, "  Very low prices cost more because of the risk premium α/(price+1)!")

        self.score_label.config(
            text=f"Wins: {self.human_wins} / {self.human_rounds}")    # refresh the win counter label at the top of the tab


# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
