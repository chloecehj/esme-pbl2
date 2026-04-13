# **📦 LowBid**

**MVP Status:** \[e.g., v1.0-Production]

**Group Members:** Allaire Chloé, Avenas Sarah, Jaber Nour, Merdji Camy, Bisiaux Clara


## **🎯 Project Overview**

Provide a concise (2-3 sentence) description of what your application does and the specific problem it solves. Why did you build this?
Our application allows users to play and simulate a bid system where the lowest unique bid wins. You can play against AI players or upload data files to analyze strategies, determine the winner, and view detailed statistics. It uses a Binary Search Tree (BST) to sort bids and efficiently find the winning bid.


## **🚀 Quick Start (Architect Level: < 60s Setup)**

Instructions on how to get this project running on a fresh machine.

1. **Clone the repo:**\
   copy-paste the code in VScode

2. **Setup Virtual Environment:**\
   python libraries

3. **Install Dependencies:**\
   make sure the CSV files are in the same folder as the two python codes

4. **Run Application:**\
   python interface.py


## **🛠️ Technical Architecture**

Explain how your code is organized. An "Architect-level" README should describe the separation of concerns.

- **main.py**: The core logic of the application. It contains the BST implementation

- **interface.py**: The graphical interface built with Tkinter.

- The CSV files that have to be stored in the same folder as the code


## **🧪 Testing & Validation**

How can a user verify the code works?

- If we run the code, we should have no errors and in the demo part (for example) we should have:
30 bids are loaded displayed
The BST in-order traversal showing all prices sorted from lowest to highest
At least one price marked Unique
A winner displayed with their price, successor and predecessor in the BST
Seller revenue and per-player costs


## **📦 Dependencies**

List the main third-party libraries used and _why_ they were chosen:

- tkinter: build the entire graphical interface
- csv: read the CSV files
- threading: run the 500-round simulation in the background so the interface does not freeze.
- random: generate bids
- os: build file paths and locate CSV files


## **🔮 Future Roadmap (v2.0)**

What features would you add if you had more time or a larger budget?

- Add a matplotlib graph showing win rate evolution across rounds
- Implement adaptive strategies that learn from previous rounds
- Allow multiple human players to connect and bid simultaneously in real time
  
