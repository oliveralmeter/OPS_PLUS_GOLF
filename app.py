import pandas as pd
import random
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
from ttkthemes import ThemedTk
import os
import sys

def resource_path(relative_path):
    """
    Get absolute path to resource, works for development and when bundled with PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define Syracuse colors and basic palette
syracuse_orange = "#D44500"
syracuse_blue = "#0B3954"
white = "#FFFFFF"
grey = "#F0F0F0"

class MLBGameApp:
    def __init__(self, root, data_file):
        self.root = root
        self.root.title("OPS+ Golf")
        self.root.geometry("1000x700")
        self.root.configure(bg=white)
        
        # Set the app's icon using the PNG file
        self.icon_img = tk.PhotoImage(file=resource_path("myicon.gif"))
        self.root.iconphoto(False, self.icon_img)
        
        # Set a modern theme for ttk widgets (using Breeze) and configure styles
        self.style = ttk.Style(self.root)
        self.style.theme_use("breeze")
        self.style.configure("TButton", background=syracuse_orange, foreground=white)
        self.style.map("TButton", background=[("active", syracuse_orange)])
        
        self.df = self.load_data(resource_path(data_file))
        self.unique_players = sorted(self.df['Player'].unique().tolist())
        
        # Game parameters (set by user on start screen)
        self.num_players = 0
        self.total_rounds = 0
        self.current_round = 0
        self.target_ops = 0
        
        # Score tracking
        self.scoreboard = {}      # cumulative points for each contestant (lower is better)
        self.score_history = {}   # score progression per contestant (for each round)
        self.round_history = []   # text log for each round
        
        # UI Elements / Frames
        self.start_frame = None
        self.game_frame = None
        self.score_frame = None
        self.history_frame = None
        self.chart_frame = None
        # Each player entry: (name_var, player_var, year_var, year_dropdown)
        self.player_entries = []  
        
        # Matplotlib Figure & Canvas for leaderboard visualization
        self.fig = None
        self.ax = None
        self.canvas = None
        
        # Global variable to track an open suggestion box (if any)
        self.open_suggestion_box = None
        
        self.show_start_screen()
        self.root.bind("<Button-1>", self.close_suggestion_box)

    def load_data(self, file_path):
        try:
            df = pd.read_csv(file_path)
            required_cols = {'Player', 'Year', 'OPS_plus'}
            if not required_cols.issubset(df.columns):
                logging.error("CSV file is missing one or more required columns.")
                raise ValueError("CSV file missing required columns.")
            df['Player'] = df['Player'].str.strip()
            df['Year'] = df['Year'].astype(int)
            return df[['Player', 'Year', 'OPS_plus']].dropna()
        except Exception as e:
            logging.error(f"Error loading CSV: {e}")
            messagebox.showerror("File Error", f"Error loading CSV file: {e}")
            self.root.quit()

    def get_random_ops(self):
        # Generate a random target OPS+ between 50 and 150
        return random.randint(50, 150)

    def get_player_years(self, player):
        if not player:
            return []
        player_data = self.df[self.df['Player'].str.lower() == player.lower()]
        if not player_data.empty:
            return sorted(player_data['Year'].unique().tolist())
        return []

    def get_player_ops(self, player, year):
        match = self.df[(self.df['Player'].str.lower() == player.lower()) &
                        (self.df['Year'] == year)]
        if not match.empty:
            return match.iloc[0]['OPS_plus']
        return None

    def get_best_guess_season(self, player, target_ops):
        player_data = self.df[self.df['Player'].str.lower() == player.lower()]
        if not player_data.empty:
            player_data = player_data.copy()
            player_data['OPS_Diff'] = abs(player_data['OPS_plus'] - target_ops)
            best_season = player_data.loc[player_data['OPS_Diff'].idxmin()]
            return best_season['Year'], best_season['OPS_plus']
        return None, None

    def autocomplete(self, event, player_var, dropdown, idx):
        typed_text = player_var.get()
        suggestions = [p for p in self.unique_players if typed_text.lower() in p.lower()]
        if hasattr(dropdown, 'suggestion_box') and dropdown.suggestion_box:
            dropdown.suggestion_box.destroy()
            dropdown.suggestion_box = None
        if suggestions:
            lb = tk.Listbox(self.root, font=("Arial", 14))
            for item in suggestions:
                lb.insert(tk.END, item)
            lb.bind("<<ListboxSelect>>", lambda e, var=player_var, lb=lb, idx=idx: self.on_suggestion_select(var, lb, idx))
            lb.bind("<FocusOut>", lambda e: lb.destroy())
            x = dropdown.winfo_rootx() - self.root.winfo_rootx()
            y = dropdown.winfo_rooty() - self.root.winfo_rooty() + dropdown.winfo_height()
            lb.place(x=x, y=y, width=dropdown.winfo_width())
            dropdown.suggestion_box = lb
            self.open_suggestion_box = lb

    def on_suggestion_select(self, var, lb, idx):
        try:
            selection = lb.get(lb.curselection())
            var.set(selection)
        except tk.TclError:
            pass
        lb.destroy()
        self.open_suggestion_box = None
        self.update_year_dropdown(var, idx)

    def close_suggestion_box(self, event):
        if self.open_suggestion_box:
            self.open_suggestion_box.destroy()
            self.open_suggestion_box = None

    def show_start_screen(self):
        self.start_frame = tk.Frame(self.root, padx=20, pady=20, bg=white)
        self.start_frame.pack(fill="both", expand=True)
        
        title_label = tk.Label(self.start_frame, text="OPS+ Golf", font=("Arial", 28, "bold"), fg=syracuse_blue, bg=white)
        title_label.pack(pady=20)
        
        instructions = (
            "Welcome to OPS+ Golf!\n\n"
            "Enter the number of contestants and rounds to start.\n"
            "Before each round, choose your name and select a player and season.\n"
            "Try to match the target OPS+ as closely as possible.\n"
            "Your score is the absolute difference (lower is better)."
        )
        instr_label = tk.Label(self.start_frame, text=instructions, font=("Arial", 14), justify="center", bg=white)
        instr_label.pack(pady=10)
        
        param_frame = tk.Frame(self.start_frame, bg=white)
        param_frame.pack(pady=10)
        tk.Label(param_frame, text="Number of Contestants:", font=("Arial", 14), bg=white).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.num_players_entry = tk.Entry(param_frame, font=("Arial", 14))
        self.num_players_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(param_frame, text="Number of Rounds:", font=("Arial", 14), bg=white).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.num_rounds_entry = tk.Entry(param_frame, font=("Arial", 14))
        self.num_rounds_entry.grid(row=1, column=1, padx=5, pady=5)
        
        start_button = tk.Button(self.start_frame, text="Start Game", command=self.start_game, font=("Arial", 16))
        start_button.pack(pady=20)
        
        credit_label = tk.Label(self.start_frame, text="Created and programmed by Oliver Almeter", font=("Arial", 12), bg=white, fg=syracuse_blue)
        credit_label.pack(side="bottom", pady=10)

    def start_game(self):
        try:
            self.num_players = int(self.num_players_entry.get())
            self.total_rounds = int(self.num_rounds_entry.get())
            self.current_round = 1
            if self.num_players < 1 or self.total_rounds < 1:
                messagebox.showerror("Input Error", "Number of contestants and rounds must be at least 1.")
                return
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for contestants and rounds.")
            return
        
        self.scoreboard = {i: 0 for i in range(self.num_players)}
        self.score_history = {i: [0] for i in range(self.num_players)}
        
        self.start_frame.pack_forget()
        self.setup_game_screen()

    def setup_game_screen(self):
        self.game_frame = tk.Frame(self.root, padx=20, pady=20, bg=white)
        self.game_frame.pack(fill="both", expand=True)
        
        # Top section (white background with colored text)
        top_frame = tk.Frame(self.game_frame, bg=white, padx=10, pady=10)
        top_frame.pack(fill="x")
        self.round_label = tk.Label(top_frame, text=f"Round {self.current_round} of {self.total_rounds}", font=("Arial", 20), bg=white, fg=syracuse_blue)
        self.round_label.pack(side="left", padx=10)
        self.target_ops = self.get_random_ops()
        self.target_label = tk.Label(top_frame, text=f"Target OPS+: {self.target_ops}", font=("Arial", 20, "bold"), fg=syracuse_orange, bg=white)
        self.target_label.pack(side="left", padx=10)
        
        custom_target_frame = tk.Frame(top_frame, bg=white)
        custom_target_frame.pack(side="left", padx=10)
        self.custom_round_target_var = tk.BooleanVar()
        self.custom_round_target_check = tk.Checkbutton(custom_target_frame, text="Custom Round Target", variable=self.custom_round_target_var, font=("Arial", 14), bg=white, fg=syracuse_blue)
        self.custom_round_target_check.pack(side="left")
        self.custom_round_target_entry = tk.Entry(custom_target_frame, width=6, font=("Arial", 14))
        self.custom_round_target_entry.pack(side="left", padx=5)
        
        # Validate custom target if provided
        def validate_custom_target():
            if self.custom_round_target_var.get():
                try:
                    custom_val = int(self.custom_round_target_entry.get())
                    if not (50 <= custom_val <= 150):
                        messagebox.showerror("Input Error", "Custom target OPS+ must be between 50 and 150.")
                        return False
                except ValueError:
                    messagebox.showerror("Input Error", "Please enter a valid number for the custom target OPS+.")
                    return False
            return True
        
        # Contestant selections (white background)
        selection_frame = tk.Frame(self.game_frame, bg=white)
        selection_frame.pack(pady=10, fill="x")
        self.player_entries = []
        for i in range(self.num_players):
            row_frame = tk.Frame(selection_frame, bg=white)
            row_frame.pack(pady=5, fill="x")
            
            tk.Label(row_frame, text="Name:", font=("Arial", 14), bg=white).grid(row=0, column=0, padx=5, sticky="e")
            name_var = tk.StringVar()
            name_entry = tk.Entry(row_frame, textvariable=name_var, font=("Arial", 14), width=15)
            name_entry.grid(row=0, column=1, padx=5)
            name_var.set(f"Contestant {i+1}")
            
            tk.Label(row_frame, text="Player:", font=("Arial", 14), bg=white).grid(row=0, column=2, padx=5, sticky="e")
            player_var = tk.StringVar()
            player_dropdown = ttk.Combobox(row_frame, textvariable=player_var, state='normal', width=30, font=("Arial", 14))
            player_dropdown['values'] = self.unique_players
            player_dropdown.grid(row=0, column=3, padx=5)
            player_dropdown.bind("<KeyRelease>", lambda event, pv=player_var, d=player_dropdown, idx=i: self.autocomplete(event, pv, d, idx))
            player_dropdown.bind("<<ComboboxSelected>>", lambda e, pv=player_var, idx=i: self.update_year_dropdown(pv, idx))
            
            tk.Label(row_frame, text="Year:", font=("Arial", 14), bg=white).grid(row=0, column=4, padx=5, sticky="e")
            year_var = tk.StringVar()
            year_dropdown = ttk.Combobox(row_frame, textvariable=year_var, state='readonly', width=10, font=("Arial", 14))
            year_dropdown.grid(row=0, column=5, padx=5)
            
            self.player_entries.append((name_var, player_var, year_var, year_dropdown))
        
        # Buttons
        button_frame = tk.Frame(self.game_frame, bg=white)
        button_frame.pack(pady=10)
        self.submit_round_button = tk.Button(button_frame, text="Submit Round", command=lambda: self.play_round_wrapper(validate_custom_target), font=("Arial", 16))
        self.submit_round_button.pack(side="left", padx=10)
        self.next_round_button = tk.Button(button_frame, text="Next Round", command=self.next_round, font=("Arial", 16), state="disabled")
        self.next_round_button.pack(side="left", padx=10)
        
        # Scoreboard panel (white background, with headers in Syracuse Blue)
        self.score_frame = tk.Frame(self.game_frame, bd=2, relief="groove", padx=10, pady=10, bg=white)
        self.score_frame.pack(pady=10, fill="x")
        score_title = tk.Label(self.score_frame, text="Scoreboard (Cumulative Points)", font=("Arial", 18, "bold"), bg=white, fg=syracuse_blue)
        score_title.pack()
        self.score_labels = {}
        for i in range(self.num_players):
            name = self.player_entries[i][0].get() or f"Contestant {i+1}"
            label = tk.Label(self.score_frame, text=f"{name}: 0", font=("Arial", 16), bg=white)
            label.pack(anchor="w", padx=5, pady=2)
            self.score_labels[i] = label
        
        # History panel (white background, headers in Syracuse Blue)
        self.history_frame = tk.Frame(self.game_frame, bd=2, relief="groove", padx=10, pady=10, bg=white)
        self.history_frame.pack(pady=10, fill="both", expand=True)
        history_title = tk.Label(self.history_frame, text="Round History", font=("Arial", 18, "bold"), bg=white, fg=syracuse_blue)
        history_title.pack()
        self.history_text = tk.Text(self.history_frame, height=8, state="disabled", wrap="word", font=("Arial", 14), bg=white)
        self.history_text.pack(fill="both", expand=True)
        
        # Leaderboard panel (chart) with white background and headers in Syracuse Blue
        self.chart_frame = tk.Frame(self.game_frame, bd=2, relief="groove", padx=10, pady=10, bg=white)
        self.chart_frame.pack(pady=10, fill="both", expand=True)
        chart_title = tk.Label(self.chart_frame, text="Leaderboard", font=("Arial", 18, "bold"), bg=white, fg=syracuse_blue)
        chart_title.pack()
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Points (Lower is Better)", fontsize=12)
        self.ax.set_ylabel("Contestants", fontsize=12)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.update_leaderboard_chart()

    def play_round_wrapper(self, validate_func):
        if validate_func():
            self.play_round()

    def update_year_dropdown(self, player_var, idx):
        selected_player = player_var.get()
        available_years = self.get_player_years(selected_player)
        if idx < len(self.player_entries):
            _, _, _, year_dropdown = self.player_entries[idx]
            year_dropdown['values'] = available_years
            if available_years:
                year_dropdown.set(available_years[0])
            else:
                year_dropdown.set("")

    def play_round(self):
        if self.custom_round_target_var.get():
            try:
                custom_val = int(self.custom_round_target_entry.get())
                self.target_ops = custom_val
            except ValueError:
                messagebox.showerror("Input Error", "Please enter a valid number for the custom target OPS+.")
                return
        self.target_label.config(text=f"Target OPS+: {self.target_ops}")
        
        round_result = f"--- Round {self.current_round} Results ---\nTarget OPS+: {self.target_ops}\n"
        round_diffs = {}
        
        for i, entry in enumerate(self.player_entries):
            name_var, player_var, year_var, _ = entry
            contestant_name = name_var.get().strip() or f"Contestant {i+1}"
            player = player_var.get().strip()
            year_str = year_var.get().strip()
            if player and year_str:
                try:
                    year = int(year_str)
                except ValueError:
                    round_result += f"{contestant_name}: Invalid year input.\n"
                    continue
                ops = self.get_player_ops(player, year)
                if ops is not None:
                    diff = abs(self.target_ops - ops)
                    round_diffs[i] = diff
                    self.scoreboard[i] += diff
                    round_result += f"{contestant_name} ({player} in {year}): OPS+ {ops} | Diff: {diff}\n"
                    
                    best_year, best_ops = self.get_best_guess_season(player, self.target_ops)
                    if best_year is not None:
                        round_result += f"    Best guess season: {best_year} (OPS+ {best_ops})\n"
                else:
                    round_result += f"{contestant_name} ({player} in {year}): No data found.\n"
            else:
                round_result += f"{contestant_name}: Incomplete selection.\n"
        
        if round_diffs:
            winner_idx = min(round_diffs, key=round_diffs.get)
            winner_points = round_diffs[winner_idx]
            winner_name = self.player_entries[winner_idx][0].get().strip() or f"Contestant {winner_idx+1}"
            round_result += f"\nRound Winner: {winner_name} with {winner_points} points.\n"
        else:
            round_result += "\nNo valid entries this round.\n"
        
        self.round_history.append(round_result)
        self.update_history_text(round_result)
        
        for i in range(self.num_players):
            name = self.player_entries[i][0].get().strip() or f"Contestant {i+1}"
            self.score_labels[i].config(text=f"{name}: {self.scoreboard[i]}")
        
        self.update_leaderboard_chart()
        
        self.submit_round_button.config(state="disabled")
        if self.current_round < self.total_rounds:
            self.next_round_button.config(state="normal")
        else:
            self.end_game()

    def next_round(self):
        for entry in self.player_entries:
            name_var, player_var, year_var, _ = entry
            player_var.set("")
            year_var.set("")
        self.custom_round_target_var.set(False)
        self.custom_round_target_entry.delete(0, tk.END)
        
        self.current_round += 1
        self.target_ops = self.get_random_ops()
        self.round_label.config(text=f"Round {self.current_round} of {self.total_rounds}")
        self.target_label.config(text=f"Target OPS+: {self.target_ops}")
        self.submit_round_button.config(state="normal")
        self.next_round_button.config(state="disabled")

    def update_history_text(self, text):
        self.history_text.config(state="normal")
        self.history_text.insert("end", text + "\n")
        self.history_text.see("end")
        self.history_text.config(state="disabled")

    def update_leaderboard_chart(self):
        self.ax.clear()
        self.ax.set_xlabel("Points (Lower is Better)", fontsize=12)
        self.ax.set_title("Leaderboard", fontsize=16)
        
        contestants = []
        scores = []
        for i in range(self.num_players):
            name = self.player_entries[i][0].get().strip() or f"Contestant {i+1}"
            contestants.append(name)
            scores.append(self.scoreboard[i])
        
        bars = self.ax.barh(contestants, scores, color="skyblue")
        self.ax.invert_yaxis()
        
        for bar in bars:
            width = bar.get_width()
            self.ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f"{width:.1f}", va='center', fontsize=12)
        
        self.ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        self.canvas.draw()

    def end_game(self):
        final_result = "=== Game Over! ===\nFinal Cumulative Scores:\n"
        for i in range(self.num_players):
            name = self.player_entries[i][0].get().strip() or f"Contestant {i+1}"
            final_result += f"{name}: {self.scoreboard[i]} points\n"
        if self.scoreboard:
            overall_winner_idx = min(self.scoreboard, key=self.scoreboard.get)
            winner_name = self.player_entries[overall_winner_idx][0].get().strip() or f"Contestant {overall_winner_idx+1}"
            final_result += f"\nOverall Winner: {winner_name}!\n"
        else:
            final_result += "\nNo winners.\n"
        
        messagebox.showinfo("Game Over", final_result)
        restart = messagebox.askyesno("Restart", "Do you want to play again?")
        if restart:
            self.reset_game()
        else:
            self.root.quit()

    def reset_game(self):
        self.game_frame.destroy()
        self.scoreboard = {}
        self.score_history = {}
        self.round_history = []
        self.player_entries = []
        self.show_start_screen()

if __name__ == "__main__":
    root = ThemedTk(theme="breeze")
    app = MLBGameApp(root, 'batting_data_6024.csv')
    root.mainloop()
