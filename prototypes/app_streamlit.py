import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Define Syracuse colors and palette
syracuse_orange = "#D44500"
syracuse_blue = "#0B3954"
white = "#FFFFFF"
grey = "#F0F0F0"

# --- Data Loading ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        required_cols = {'Player', 'Year', 'OPS_plus'}
        if not required_cols.issubset(df.columns):
            raise ValueError("CSV file missing required columns.")
        df['Player'] = df['Player'].str.strip()
        df['Year'] = df['Year'].astype(int)
        return df[['Player', 'Year', 'OPS_plus']].dropna()
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        st.stop()

df = load_data("batting_data_6024.csv")
unique_players = sorted(df['Player'].unique().tolist())

# --- Helper Functions ---
def get_random_ops():
    return random.randint(50, 150)

def get_player_years(player):
    if not player:
        return []
    player_data = df[df['Player'].str.lower() == player.lower()]
    if not player_data.empty:
        return sorted(player_data['Year'].unique().tolist())
    return []

def get_player_ops(player, year):
    match = df[(df['Player'].str.lower() == player.lower()) & (df['Year'] == year)]
    if not match.empty:
        return match.iloc[0]['OPS_plus']
    return None

def get_best_guess_season(player, target_ops):
    player_data = df[df['Player'].str.lower() == player.lower()]
    if not player_data.empty:
        player_data = player_data.copy()
        player_data['OPS_Diff'] = abs(player_data['OPS_plus'] - target_ops)
        best_season = player_data.loc[player_data['OPS_Diff'].idxmin()]
        return best_season['Year'], best_season['OPS_plus']
    return None, None

# --- Initialize Session State ---
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'num_players' not in st.session_state:
    st.session_state.num_players = 0
if 'total_rounds' not in st.session_state:
    st.session_state.total_rounds = 0
if 'current_round' not in st.session_state:
    st.session_state.current_round = 0
if 'target_ops' not in st.session_state:
    st.session_state.target_ops = 0
if 'scoreboard' not in st.session_state:
    st.session_state.scoreboard = {}
if 'round_history' not in st.session_state:
    st.session_state.round_history = []

# --- Start Screen ---
if not st.session_state.game_started:
    st.title("OPS+ Golf")
    st.markdown(f"""
    **Welcome to OPS+ Golf!**

    Enter the number of contestants and rounds to start.

    Before each round, choose your name and select a player and season.

    Try to match the target OPS+ as closely as possible.

    Your score is the absolute difference (lower is better).
    """)
    num_players = st.number_input("Number of Contestants", min_value=1, value=2, step=1)
    total_rounds = st.number_input("Number of Rounds", min_value=1, value=3, step=1)
    if st.button("Start Game"):
        st.session_state.num_players = num_players
        st.session_state.total_rounds = total_rounds
        st.session_state.current_round = 1
        st.session_state.target_ops = get_random_ops()
        st.session_state.scoreboard = {i: 0 for i in range(num_players)}
        st.session_state.round_history = []
        st.session_state.game_started = True
        st.experimental_rerun()

# --- Game Screen ---
if st.session_state.game_started:
    st.header(f"Round {st.session_state.current_round} of {st.session_state.total_rounds}")
    custom = st.checkbox("Custom Round Target")
    if custom:
        custom_target = st.number_input("Custom Target OPS+", min_value=50, max_value=150, value=st.session_state.target_ops, step=1)
        st.session_state.target_ops = custom_target
    st.subheader(f"Target OPS+: {st.session_state.target_ops}")
    
    st.markdown("---")
    st.write("### Contestant Details")
    
    # Create a list to hold contestant details
    contestants = []
    for i in range(st.session_state.num_players):
        st.write(f"**Contestant {i+1}**")
        col1, col2, col3 = st.columns([2, 4, 3])
        with col1:
            name = st.text_input("Name", value=f"Contestant {i+1}", key=f"name_{i}")
        with col2:
            player = st.selectbox("Select Player", options=unique_players, key=f"player_{i}")
        with col3:
            years = get_player_years(player)
            if years:
                year = st.selectbox("Select Season", options=years, key=f"year_{i}")
            else:
                year = None
        contestants.append((name, player, year))
    
    if st.button("Submit Round"):
        round_result = f"--- Round {st.session_state.current_round} Results ---\nTarget OPS+: {st.session_state.target_ops}\n"
        round_diffs = {}
        for i, (name, player, year) in enumerate(contestants):
            if player and year:
                try:
                    year_int = int(year)
                except ValueError:
                    round_result += f"{name}: Invalid year input.\n"
                    continue
                ops = get_player_ops(player, year_int)
                if ops is not None:
                    diff = abs(st.session_state.target_ops - ops)
                    round_diffs[i] = diff
                    st.session_state.scoreboard[i] += diff
                    round_result += f"{name} ({player} in {year_int}): OPS+ {ops} | Diff: {diff}\n"
                    best_year, best_ops = get_best_guess_season(player, st.session_state.target_ops)
                    if best_year is not None:
                        round_result += f"    Best guess season: {best_year} (OPS+ {best_ops})\n"
                else:
                    round_result += f"{name} ({player} in {year_int}): No data found.\n"
            else:
                round_result += f"{name}: Incomplete selection.\n"
        if round_diffs:
            winner_idx = min(round_diffs, key=round_diffs.get)
            winner_points = round_diffs[winner_idx]
            winner_name = contestants[winner_idx][0]
            round_result += f"\nRound Winner: {winner_name} with {winner_points} points.\n"
        else:
            round_result += "\nNo valid entries this round.\n"
        st.session_state.round_history.append(round_result)
        st.success(round_result)
        
        if st.session_state.current_round < st.session_state.total_rounds:
            st.session_state.current_round += 1
            st.session_state.target_ops = get_random_ops()
            st.experimental_rerun()
        else:
            st.session_state.game_started = False
            st.experimental_rerun()
    
    st.markdown("---")
    st.subheader("Scoreboard (Cumulative Points)")
    for i in range(st.session_state.num_players):
        st.write(f"{contestants[i][0]}: {st.session_state.scoreboard[i]} points")
    
    st.markdown("---")
    st.subheader("Round History")
    for history in st.session_state.round_history:
        st.text(history)
    
    st.markdown("---")
    st.subheader("Leaderboard")
    fig, ax = plt.subplots()
    contestants_names = [contestants[i][0] for i in range(st.session_state.num_players)]
    scores = [st.session_state.scoreboard[i] for i in range(st.session_state.num_players)]
    bars = ax.barh(contestants_names, scores, color="skyblue")
    ax.invert_yaxis()
    ax.set_xlabel("Points (Lower is Better)")
    ax.set_title("Leaderboard")
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f"{width:.1f}", va='center')
    st.pyplot(fig)
    
    if st.session_state.current_round > st.session_state.total_rounds:
        st.success("Game Over!")
        overall_winner_idx = min(st.session_state.scoreboard, key=st.session_state.scoreboard.get)
        overall_winner = contestants[overall_winner_idx][0]
        st.info(f"Overall Winner: {overall_winner}")
        if st.button("Restart Game"):
            # Clear session state keys
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()
