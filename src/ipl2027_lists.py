"""IPL 2027 retention / release data as of 17 Nov 2026 (retention deadline day).

PROVENANCE - READ THIS
  * The lists below are the franchise-by-franchise lists supplied by the project owner (compiled from press: SportsTak,
    Wisden, Cricket Times) and cross-checked this session against the Cricket News / Yahoo Sports roundup of 17 Nov 2026
    (purses, open slots, overseas slots, trades, headline releases all agree).
  * An OFFICIAL iplt20.com / BCCI release could not be reached from this environment (Business Standard returned 403; no
    iplt20.com page surfaced in search). So "official" below means "franchise lists as published by press on the deadline
    day". Anything that conflicts between sources is flagged in NOTES.
  * Auction pool: registration closes 23 Nov 2026, final auction register due 3 Dec 2026, auction 16 Dec 2026 (Goa).
    NO official auction pool exists yet, so nobody can be status A. Released players are status B.
"""
AS_OF = "17 Nov 2026"
SRC_LISTS = "IPL 2027 retention lists 17 Nov 2026 (owner-supplied press compilation; matches Cricket News/Yahoo 17 Nov)"
SRC_YAHOO = "Cricket News/Yahoo Sports roundup 17 Nov 2026"
AUCTION = dict(date="16 Dec 2026", venue="Goa", registration_close="23 Nov 2026", final_register="3 Dec 2026")

# purse (Rs crore), open squad slots, overseas slots available (Yahoo/Cricket News table; purse matches owner list)
TEAMS = {
 "CSK": dict(purse=28.05, open_slots=6, overseas_free=2,
   retained="Sanju Samson|Ruturaj Gaikwad|Ayush Mhatre|Dewald Brevis|Urvil Patel|Kartik Sharma|Sarfaraz Khan|Anshul Kamboj|Gurjapneet Singh|Mukesh Choudhary|Noor Ahmad|Rahul Chahar|Jamie Overton|Ramakrishna Ghosh|Shivam Dube|Shreyas Gopal|Akeal Hosein",
   traded_in="Liam Livingstone|Jack Edwards",
   released="MS Dhoni|Prashant Veer|Matthew Short|Matt Henry|Zak Foulkes|Spencer Johnson|Dian Forrester|Aman Khan|Kuldip Yadav|Akash Madhwal|Macneil Noronha"),
 "MI": dict(purse=32.60, open_slots=9, overseas_free=2,
   retained="Rohit Sharma|Suryakumar Yadav|Tilak Varma|Ryan Rickelton|Quinton de Kock|Raj Bawa|Corbin Bosch|Mitchell Santner|Raghu Sharma|Shardul Thakur|Ashwani Kumar|Jasprit Bumrah|Sherfane Rutherford|Will Jacks|Naman Dhir",
   traded_in="Arshdeep Singh",
   released="Trent Boult|Deepak Chahar|Allah Ghazanfar|Keshav Maharaj|Atharva Ankolekar|Mohammed Izhar|Danish Malewar|Mayank Markande|Mayank Rawat"),
 "RCB": dict(purse=14.15, open_slots=5, overseas_free=1,
   retained="Virat Kohli|Rajat Patidar|Devdutt Padikkal|Phil Salt|Jitesh Sharma|Tim David|Jordan Cox|Venkatesh Iyer|Krunal Pandya|Romario Shepherd|Bhuvneshwar Kumar|Josh Hazlewood|Jacob Duffy|Nuwan Thushara|Yash Dayal|Rasikh Dar|Suyash Sharma|Vicky Ostwal|Abhinandan Singh|Kanishk Chouhan",
   traded_in="",
   released="Jacob Bethell|Richard Gleeson|Mangesh Yadav|Satwik Deswal|Vihaan Malhotra"),
 "KKR": dict(purse=41.65, open_slots=8, overseas_free=3,
   retained="Cameron Green|Rinku Singh|Sunil Narine|Varun Chakaravarthy|Harshit Rana|Ramandeep Singh|Angkrish Raghuvanshi|Finn Allen|Vaibhav Arora|Rovman Powell|Tim Seifert|Manish Pandey|Anukul Roy|Sarthak Ranjan|Prashant Solanki|Saurabh Dubey|Kartik Tyagi",
   traded_in="",
   released="Ajinkya Rahane|Matheesha Pathirana|Mustafizur Rahman|Rachin Ravindra|Rahul Tripathi|Akash Deep|Blessing Muzarabani|Navdeep Saini|Umran Malik|Tejasvi Singh|Luvnith Sisodia|Daksh Kamra"),
 "DC": dict(purse=39.50, open_slots=9, overseas_free=4,
   retained="KL Rahul|Axar Patel|Tristan Stubbs|David Miller|Sameer Rizvi|Ashutosh Sharma|Prithvi Shaw|Mukesh Kumar|Auqib Nabi|Madhav Tiwari|Vipraj Nigam|Tripurana Vijay|Lungi Ngidi|Kyle Jamieson",
   traded_in="Rishabh Pant|Zeeshan Ansari",
   released="Mitchell Starc|Nitish Rana|Abishek Porel|Pathum Nissanka|Ben Duckett|Karun Nair|Sahil Parakh|Dushmantha Chameera|Rehan Ahmed|Ajay Mandal"),
 "PBKS": dict(purse=18.60, open_slots=6, overseas_free=2,
   retained="Shreyas Iyer|Prabhsimran Singh|Priyansh Arya|Shashank Singh|Yuzvendra Chahal|Marco Jansen|Marcus Stoinis|Azmatullah Omarzai|Cooper Connolly|Ben Dwarshuis|Xavier Bartlett|Yash Thakur|Vyshak Vijaykumar|Harpreet Brar|Harnoor Singh Pannu|Vishnu Vinod|Musheer Khan|Suryansh Shedge",
   traded_in="Hardik Pandya",
   released="Lockie Ferguson|Mitch Owen|Nehal Wadhera|Pyla Avinash|Praveen Dubey|Vishal Nishad"),
 "SRH": dict(purse=40.15, open_slots=7, overseas_free=3,
   retained="Pat Cummins|Abhishek Sharma|Ishan Kishan|Heinrich Klaasen|Nitish Kumar Reddy|Brydon Carse|Salil Arora|Aniket Verma|Harsh Dubey|R Smaran|Praful Hinge|Sakib Hussain|Shivang Kumar|Krains Fuletra|Eshan Malinga",
   traded_in="Khaleel Ahmed|Nathan Ellis|T Natarajan",
   released="Travis Head|Kamindu Mendis|Jaydev Unadkat|Dilshan Madushanka|Shivam Mavi|Gerald Coetzee|David Payne|Onkar Tarmale|Amit Kumar"),
 "RR": dict(purse=27.05, open_slots=6, overseas_free=3,
   retained="Yashasvi Jaiswal|Riyan Parag|Ravindra Jadeja|Dhruv Jurel|Vaibhav Sooryavanshi|Jofra Archer|Sandeep Sharma|Ravi Bishnoi|Nandre Burger|Dasun Shanaka|Donovan Ferreira|Lhuan-dre Pretorius|Shubham Dubey|Aman Rao Parela|Brijesh Sharma|Sushant Mishra|Yash Raj Punja",
   traded_in="Mohammed Shami|M Siddharth",
   released="Shimron Hetmyer|Adam Milne|Kwena Maphaka|Tushar Deshpande|Kuldeep Sen|Yudhvir Singh|Vignesh Puthur|Ravi Singh"),
 "GT": dict(purse=8.75, open_slots=3, overseas_free=2,
   retained="Shubman Gill|Sai Sudharsan|Jos Buttler|Rashid Khan|Mohammed Siraj|Kagiso Rabada|Prasidh Krishna|Washington Sundar|R Sai Kishore|Gurnoor Brar|Jason Holder|Rahul Tewatia|Glenn Phillips|Tom Banton|Kumar Kushagra|Jayant Yadav|Arshad Khan|Nishant Sindhu|Manav Suthar|Anuj Rawat|Ashok Sharma",
   traded_in="Harshal Patel",
   released="Ishant Sharma|Luke Wood|Kulwant Khejroliya|Shahrukh Khan|Connor Esterhuizen"),
 "LSG": dict(purse=47.45, open_slots=7, overseas_free=3,
   retained="Nicholas Pooran|Mayank Yadav|Mitchell Marsh|Josh Inglis|Aiden Markram|Ayush Badoni|Abdul Samad|Mukul Choudhary|Mohsin Khan|Shahbaz Ahmed|Himmat Singh|Digvesh Rathi|Prince Yadav|Akash Singh|Akshat Raghuwanshi|Arjun Tendulkar",
   traded_in="Kuldeep Yadav|Sam Curran",
   released="Avesh Khan|Anrich Nortje|Wanindu Hasaranga|Matthew Breetzke|George Linde|Naman Tiwari|Arshin Kulkarni"),
}
for _t in TEAMS.values():
    for _k in ("retained", "traded_in", "released"):
        _t[_k] = [x for x in _t[_k].split("|") if x]

# completed trades (owner list; same set reported by Cricket News 17 Nov). value Rs crore where stated.
TRADES = [
 ("Hardik Pandya", "MI", "PBKS", 18), ("Arshdeep Singh", "PBKS", "MI", 18), ("Rishabh Pant", "LSG", "DC", 15),
 ("Kuldeep Yadav", "DC", "LSG", 13.5), ("Liam Livingstone", "SRH", "CSK", None), ("Jack Edwards", "SRH", "CSK", None),
 ("Khaleel Ahmed", "CSK", "SRH", None), ("Nathan Ellis", "CSK", "SRH", None), ("T Natarajan", "DC", "SRH", None),
 ("Zeeshan Ansari", "SRH", "DC", None), ("Mohammed Shami", "LSG", "RR", None), ("M Siddharth", "LSG", "RR", None),
 ("Sam Curran", "RR", "LSG", None), ("Harshal Patel", "SRH", "GT", 4)]

# name in the lists -> name used in the PRI model files
ALIAS = {"Tilak Varma": "Namboori Tilak Varma", "Will Jacks": "William Jacks", "Nitish Kumar Reddy": "Nitish Reddy",
         "Varun Chakaravarthy": "Varun Chakravarthy", "KL Rahul": "Lokesh Rahul", "T Natarajan": "T Natarajan",
         "MS Dhoni": "Mahendra Singh Dhoni", "Abishek Porel": "Abhishek Porel", "Aman Rao Parela": "Aman Rao"}

# last disclosed price / retention fee (Rs crore). NOT a forecast of 2027 prices: used only as a clear-exceeds check.
LAST_PRICE_CR = {"Matheesha Pathirana": 18.0, "Trent Boult": 12.5, "Deepak Chahar": 9.25, "Mitchell Starc": 11.75,
                 "Travis Head": 14.0, "Shimron Hetmyer": 11.0, "Tushar Deshpande": 6.5, "Avesh Khan": 9.75,
                 "Mustafizur Rahman": 9.2, "Prashant Veer": 14.2, "Jacob Bethell": 2.6, "Mangesh Yadav": 5.2,
                 "Shahrukh Khan": 4.0}

# Bangladesh players reported (BCB confirmation, 12-13 Nov; Outlook, SportsCafe, Daily Star) as registered for the auction
BD_REGISTERED = {"Mustafizur Rahman", "Nahid Rana", "Rishad Hossain", "Hasan Mahmud", "Towhid Hridoy", "Taskin Ahmed", "Shoriful Islam"}

# releases reported ONLY by the Cricket News/Yahoo roundup (not in the owner list): team, name
EXTRA_RELEASED = [("MI", "Mahipal Lomror"), ("MI", "Robin Minz"), ("RCB", "Swapnil Singh")]
# players where the two sources disagree (kept as the owner list says, flagged)
CONFLICTS = {"Himmat Singh": "owner list: retained by LSG; Cricket News/Yahoo: released - UNRESOLVED, treated as retained (C)"}

NOTES = [
 "Himmat Singh: owner list says retained by LSG, Cricket News/Yahoo says released - unresolved.",
 "Mahipal Lomror, Robin Minz (MI) and Swapnil Singh (RCB) appear as released only in the Cricket News/Yahoo roundup.",
 "Cricket News/Yahoo (17 Nov) calls Travis Head 'opted out of IPL 2027' and Mitchell Starc 'opted out'; owner list says Head 'skipping IPL 2027'. Head -> F; Starc is released and has opted out (confirmed 18 Nov), so Starc -> F; Jacob Bethell is released by RCB but injured for IPL 2027 -> F.",
 "Ravindra Jadeja: owner list shows him as retained by RR, Yahoo as traded in from CSK. Either way he is with RR (E).",
 "Sam Curran: both sources show RR -> LSG trade, so he is no longer with RR (C).",
 "DC section of the owner list notes Kyle Jamieson and Lungi Ngidi retention is reported by only some outlets (SportsTak, Cricket Times), not Wisden - treated as C with that caveat.",
 "RR overseas count from the owner list: Archer, Burger, Shanaka, Ferreira, Pretorius = 5, leaving 3 free of 8 - matches the Yahoo table (3).",
]
