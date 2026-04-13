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
      tag = "★ UNIQUE" if len(players) == 1 else f"  {len(players)} players"
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
    log(w, f"  Total bids     : {total_bids}")
    log(w, f"  Unique prices       : {unique_prices}")
    log(w, f"  Non-unique prices   : {len(result['inorder']) - unique_prices}")
    avg_cost = result["revenue"] / total_bids if total_bids else 0
    log(w, f"  Average cost/bid : {avg_cost:.2f}")


#TAB2 : 
