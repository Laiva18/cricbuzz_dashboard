import streamlit as st
import pandas as pd
import mysql.connector
from PIL import Image
import re
import numpy as np
import requests
from datetime import datetime
import time

# -----------------------------
# 1. Page configuration
# -----------------------------

st.set_page_config(
    page_title="Cricbuzz Dashboard",
    page_icon="🏏",
    layout="wide"
)

# -----------------------------
# 2. Global CSS Styling for Cricket Theme
# -----------------------------
st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background-color: #E6F2E6;  /* light green */
        color: #000000;
    }

    /* Sidebar styling */
    .css-1d391kg {  /* sidebar container */
        background-color: #F0F8F0;  /* very light green */
    }
    .css-1d391kg h3 {
        color: #2E7D32;
    }

    /* Sidebar buttons */
    div.stButton > button {
        background-color: #A8D5BA;  /* light green */
        color: #000000;
        font-weight: bold;
        border-radius: 8px;
        padding: 6px 12px;
        margin: 5px 0;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #81C784;  /* slightly darker green on hover */
        color: #000000;
    }

    /* Expander headers */
    .streamlit-expanderHeader {
        background-color: #F9F9F4;
        color: #2E7D32;
        font-weight: bold;
        border-radius: 8px;
        padding: 5px;
    }

    /* Expander content */
    .streamlit-expanderContent {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 10px;
    }

    /* Table headers */
    th {
        background-color: #D7CCC8 !important;
        color: #000000 !important;
    }

    /* Highlight headings */
    h1, h2, h3, h4 {
        color: #2E7D32;
    }

    </style>
    """, unsafe_allow_html=True
)

# -----------------------------
#  Navigation setup using session_state
# -----------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

def set_page(page_name):
    st.session_state.page = page_name

# Sidebar with markdown "links"
st.sidebar.markdown("<h3 style='margin-bottom: 0;'>NAVIGATE:</h3>", unsafe_allow_html=True)

if st.sidebar.button("🏠 Home", key="home_btn"):
    set_page('Home')
if st.sidebar.button("📺 Live Matches", key="live_btn"):
    set_page('Live Matches')
if st.sidebar.button("📈 Player Statistics", key="player_btn"):
    set_page('Player Statistics')
if st.sidebar.button("🗄️ SQL Analytics", key="sql_btn"):
    set_page('SQL Analytics')
if st.sidebar.button("📝 CRUD Operations", key="crud_btn"):
    set_page('CRUD Operations')

# -----------------------------
# 3. Connect to MySQL

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Laiva@14997',  # use your actual password
        database='cricbuzz_db'
    )
# -----------------------------
# 4. Page content based on st.session_state.page
# -----------------------------
if st.session_state.page == "Home":
    image = Image.open("pic1.jpg")
    st.image(image, width=400)
    st.markdown("<h1 style='color: darkgreen;'>Welcome to the Cricbuzz Dashboard!</h1>", unsafe_allow_html=True)
    st.markdown("Stay updated with live cricket matches and stats.")

#==================================================
#==================================================
#LIVE MATCHES
#==================================================
#==================================================
elif st.session_state.page == "Live Matches":
    st.markdown("<h1 style='color: green; text-align: center;'>🏏 Live Cricket Matches</h1>", unsafe_allow_html=True)

    
    # ---------------------- API FUNCTIONS ----------------------
    @st.cache_data
    def get_live_matches():
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "x-rapidapi-key": "f8561bb487msh5b07b9b66b38fcfp180036jsn6d5a2bde83e4",
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers)
        return response.json()

    @st.cache_data
    def get_scorecard(match_id):
        url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"
        headers = {
            "x-rapidapi-key": "f8561bb487msh5b07b9b66b38fcfp180036jsn6d5a2bde83e4",
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers)
        return response.json()

    # ---------------------- SIDEBAR FILTERS ----------------------
    st.sidebar.header("Filter Matches")
    data = get_live_matches()
    matches_list = []

    for match_type in data.get("typeMatches", []):
        type_name = match_type.get("matchType")
        for series in match_type.get("seriesMatches", []):
            if "seriesAdWrapper" in series:
                for match in series["seriesAdWrapper"].get("matches", []):
                    match_info = match.get("matchInfo", {})
                    match_score = match.get("matchScore", {})
                    matches_list.append({
                        "MatchID": match_info.get("matchId"),
                        "MatchType": type_name,
                        "Format": match_info.get("matchFormat"),
                        "Series": match_info.get("seriesName"),
                        "Match": match_info.get("matchDesc"),
                        "Status": match_info.get("stateTitle"),
                        "Venue": match_info.get("venueInfo", {}).get("ground"),
                        "City": match_info.get("venueInfo", {}).get("city"),
                        "Team1": match_info.get("team1", {}).get("teamName"),
                        "Team2": match_info.get("team2", {}).get("teamName"),
                        "Team1Runs": match_score.get("team1Score", {}).get("inngs1", {}).get("runs"),
                        "Team1Wkts": match_score.get("team1Score", {}).get("inngs1", {}).get("wickets"),
                        "Team1Overs": match_score.get("team1Score", {}).get("inngs1", {}).get("overs"),
                        "Team2Runs": match_score.get("team2Score", {}).get("inngs1", {}).get("runs"),
                        "Team2Wkts": match_score.get("team2Score", {}).get("inngs1", {}).get("wickets"),
                        "Team2Overs": match_score.get("team2Score", {}).get("inngs1", {}).get("overs"),
                    })

    df_matches = pd.DataFrame(matches_list)

    match_types = ["All"] + df_matches["MatchType"].dropna().unique().tolist()
    selected_type = st.sidebar.selectbox("Match Type", match_types, index=0)

    formats = ["All"] + df_matches["Format"].dropna().unique().tolist()
    selected_format = st.sidebar.selectbox("Format", formats, index=0)

    filtered_df = df_matches.copy()
    if selected_type != "All":
        filtered_df = filtered_df[filtered_df["MatchType"] == selected_type]
    if selected_format != "All":
        filtered_df = filtered_df[filtered_df["Format"] == selected_format]

    st.markdown("---")

    # ---------------------- DISPLAY MATCH CARDS ----------------------
    for idx, row in filtered_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            
            # Team names with basic score
            col1.markdown(f"### {row['Team1']}")
            col1.metric(label="Score", value=f"{row['Team1Runs']}/{row['Team1Wkts']}", delta=f"Overs: {row['Team1Overs']}")
            
            col2.markdown(f"**🏏{row['Match']}**")
            col2.markdown(f"🏆Series: {row['Series']}")
            col2.markdown(f"📍Venue: {row['Venue']}, {row['City']}")
            col2.markdown(f"🟢Status: **{row['Status']}**")
            
            col3.markdown(f"### {row['Team2']}")
            col3.metric(label="Score", value=f"{row['Team2Runs']}/{row['Team2Wkts']}", delta=f"Overs: {row['Team2Overs']}")
            
            # Full Scorecard in tabs
            st.markdown("---")
            match_id = row["MatchID"]
            score_data_api = get_scorecard(match_id)
            if score_data_api:
                innings_list = score_data_api.get("scorecard", [])
                for inng in innings_list:
                    with st.expander(f"{inng.get('batteamname')} Innings"):
                        st.markdown(f"**Score:** {inng.get('score')}/{inng.get('wickets')} ({inng.get('overs')} ov)")
                        
                        batsmen = inng.get("batsman", [])
                        batsmen_played = [b for b in batsmen if int(b.get("balls",0))>0]
                        if batsmen_played:
                            bat_df = pd.DataFrame([{
                                "Batsman": b.get("name"),
                                "Runs": b.get("runs"),
                                "Balls": b.get("balls"),
                                "4s": b.get("fours"),
                                "6s": b.get("sixes"),
                                "SR": b.get("strkrate"),
                                "Dismissal": b.get("outdec")
                            } for b in batsmen_played])
                            st.markdown("**Batting**")
                            st.table(bat_df)

                        bowlers = inng.get("bowler", [])
                        bowlers_played = [b for b in bowlers if float(b.get("overs",0))>0]
                        if bowlers_played:
                            bowl_df = pd.DataFrame([{
                                "Bowler": b.get("name"),
                                "Overs": b.get("overs"),
                                "Maidens": b.get("maidens"),
                                "Runs": b.get("runs"),
                                "Wickets": b.get("wickets"),
                                "Economy": b.get("economy")
                            } for b in bowlers_played])
                            st.markdown("**Bowling**")
                            st.table(bowl_df)

                        extras = inng.get("extras", {})
                        st.markdown(f"**Extras:** {extras.get('total',0)} (b {extras.get('byes',0)}, lb {extras.get('legbyes',0)}, w {extras.get('wides',0)}, nb {extras.get('noballs',0)})")

            st.markdown("___")


#========================================================================
#===========================================================================
#PLAYER STATISTICS
#===========================================================================
#=============================================================================

elif st.session_state.page == "Player Statistics":
    st.markdown("<h1 style='color: green; text-align: center;'>👤 Players info and Stats</h1>", unsafe_allow_html=True)

    # --------------------------
    # 🔍 Player Search
    # --------------------------
    player_name = st.text_input("Enter Player Name:")
    players = []

    if player_name:
        search_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
        headers = {
            "x-rapidapi-key": "f8561bb487msh5b07b9b66b38fcfp180036jsn6d5a2bde83e4",
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        querystring = {"plrN": player_name}
        response = requests.get(search_url, headers=headers, params=querystring)

        if response.status_code == 200:
            data = response.json()
            players = data.get("player", [])

            if players:
                # Dropdown to select player
                player_options = {f"{p['name']} — {p['teamName']}": p for p in players}
                selected_player_name = st.selectbox("Select Player", list(player_options.keys()))
                player = player_options[selected_player_name]
                player_id = player.get("id")

                # --------------------------
                # Fetch Personal Info
                # --------------------------
                details_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}"
                details_response = requests.get(details_url, headers=headers)
                if details_response.status_code == 200:
                    details = details_response.json()
                    st.markdown("---")
                    st.markdown(f"### {details.get('name')} ({details.get('nickName', '')})")
                    
                    st.markdown(f"**🏅Role:** {details.get('role')}")
                    st.markdown(f"**🤝Team:** {details.get('intlTeam')}")
                    st.markdown(f"**🏏Batting Style:** {details.get('bat')}")
                    st.markdown(f"**🏐Bowling Style:** {details.get('bowl')}")
                    st.markdown(f"**🏠Birth Place:** {details.get('birthPlace')}")
                    st.markdown(f"**🎂Date of Birth:** {details.get('DoBFormat')}")
                    st.markdown(f"**🧍‍♂️Height:** {details.get('height')}")
                    st.markdown(f"**🏟Teams:** {details.get('teams')}")
                    st.markdown("---")

                    # --------------------------
                    # Select Format (appears after personal info)
                    # --------------------------
                    format_options = ["Test", "ODI", "T20", "IPL"]
                    selected_format = st.selectbox("Select Format", format_options)

                    # --------------------------
                    # Helper Functions to Fetch Stats
                    # --------------------------
                    def fetch_stats(player_id, stat_type):
                        """
                        stat_type: 'batting' or 'bowling'
                        """
                        url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/{stat_type}"
                        resp = requests.get(url, headers=headers)
                        if resp.status_code == 200:
                            return resp.json()
                        return {}

                    def parse_stats(data):
                        """
                        Convert API response to a pandas DataFrame
                        """
                        if "values" not in data:
                            return pd.DataFrame()
                        headers = data.get("headers", [])
                        rows = []
                        for item in data["values"]:
                            row_vals = item.get("values", [])
                            rows.append(row_vals)
                        df = pd.DataFrame(rows, columns=headers)
                        return df

                    # --------------------------
                    # Tabs for Batting and Bowling
                    # --------------------------
                    tab1, tab2 = st.tabs(["Batting Stats", "Bowling Stats"])

                    with tab1:
                        batting_data = fetch_stats(player_id, "batting")
                        batting_df = parse_stats(batting_data)
                        if not batting_df.empty:
                            batting_df_filtered = batting_df[["ROWHEADER", selected_format]]
                            st.markdown(f"### 🏏 Batting Stats - {selected_format}")
                            st.dataframe(batting_df_filtered)
                        else:
                            st.info("No batting stats available.")

                    with tab2:
                        bowling_data = fetch_stats(player_id, "bowling")
                        bowling_df = parse_stats(bowling_data)
                        if not bowling_df.empty:
                            bowling_df_filtered = bowling_df[["ROWHEADER", selected_format]]
                            st.markdown(f"### 🎯 Bowling Stats - {selected_format}")
                            st.dataframe(bowling_df_filtered)
                        else:
                            st.info("No bowling stats available.")

                    # --------------------------
                    # Profile link
                    # --------------------------
                    web_url = details.get("appIndex", {}).get("webURL")
                    if web_url:
                        st.markdown(f"[🔗 View Full Profile on Cricbuzz]({web_url})")

                else:
                    st.error("Failed to fetch player details.")
            else:
                st.info("No player found with this name.")
        else:
            st.error("Failed to search player. Try again later.")



#====================================================
#====================================================
#SQL Analytics- Questions
#====================================================
#====================================================

elif st.session_state.page == "SQL Analytics":
    st.markdown("<h1 style='color: green; text-align: center;'>📑 SQL Analytics</h1>", unsafe_allow_html=True)
    st.markdown("""
    This section contains SQL questions.
    """)

#------------------------------
#QUES 1
#----------------------------
    # Define function inside or outside the main code (better outside but works here too)
    def fetch_indian_players():
        conn = get_connection()
        query = """
        SELECT 
            name AS full_name,
            role AS playing_role,
            batting_style,
            bowling_style
        FROM 
            ques_1
        WHERE 
            country = 'India';
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    # Fetch and display Indian players data for Ques 1
    st.markdown("### Ques 1 Players who represent India")
    indian_players_df = fetch_indian_players()
    st.dataframe(indian_players_df)
#----------------------------------------------
    #QUES 2
#-------------------------------------------
    def ques_2():
        conn = get_connection()
        query = """
            SELECT 
            match_desc,
            team1,
            team2,
            venue,
            start_date AS match_datetime
        FROM 
            ques_2
        ORDER BY 
            start_date DESC
        LIMIT 7;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return(df)
    st.markdown("### Ques 2 Cricket matches that were played in the last Few days")
    ques2_df = ques_2()
    st.dataframe(ques2_df)
#-------------------------------------
#QUES 3
#----------------------------------
    def top_odi_scorer():
        conn = get_connection()
        query = """
        SELECT 
            r.name AS player_name,
            r.runs AS total_runs,
            r.average AS batting_average,
            b.`100s_ODI` AS centuries
        FROM 
            run_stats_by_format r
        LEFT JOIN 
            player_batting_stats b
        ON 
            r.player_id = b.player_id
        WHERE 
            r.format = 'ODI'
        ORDER BY 
            r.runs DESC
        LIMIT 6;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return (df)
    st.markdown("### Ques 3 Top 10 highest run scorers in ODI")
    ques3_df = top_odi_scorer()
    st.dataframe(ques3_df)
#--------------------------------------
#QUES 4
#--------------------------------------
    def get_large_venues():
        conn = get_connection()
        query = """
        SELECT
            ground,
            city,
            country,
            capacity
        FROM
            venues
        WHERE
            capacity > 25000
        ORDER BY
            capacity DESC;
    """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 4 Cricket venues")
    ques4_df = get_large_venues()
    st.dataframe(ques4_df)
#------------------------------------------------
#QUES 5
#----------------------------------------------
    # --------------------------------------
# QUES 5 — Team Wins from IPL Table
# --------------------------------------

    def fetch_team_wins_ipl():
        conn = get_connection()
        query = """
            SELECT 
                winnerTeam AS team_name,
                COUNT(*) AS total_wins
            FROM 
                ipl
            WHERE
                winnerTeam IS NOT NULL
                AND winnerTeam <> ''
                AND winnerTeam NOT LIKE '%no result%'
            GROUP BY 
                winnerTeam
            ORDER BY 
                total_wins DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    st.markdown("### Ques 5 Number of matches each team has won")
    ques5_df = fetch_team_wins_ipl()
    st.dataframe(ques5_df)

#----------------------------------
#QUES 6
#---------------------------------
    def fetch_player_role_counts():
        conn = get_connection()
        query = """
        SELECT
            role,
            COUNT(*) AS player_count
        FROM
            player_role
        GROUP BY
            role
        ORDER BY
            player_count DESC;
        """
    
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 6 Players & their playing role")
    ques6_df = fetch_player_role_counts()
    st.dataframe(ques6_df)
#---------------------------------------
#QUES 7
#---------------------------------------
    def fetch_highest_scores_with_player():
        conn = get_connection()
        query = """
        SELECT
            r.format AS format,
            r.name AS player_name,
            r.runs AS highest_score
        FROM
            run_stats_by_format r
        INNER JOIN (
            SELECT
                format,
                MAX(runs) AS max_runs
            FROM
                run_stats_by_format
            GROUP BY
                format
        ) AS max_scores
        ON r.format = max_scores.format AND r.runs = max_scores.max_runs
        ORDER BY
            r.format;
        """
    
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 7 Highest batting score in each cricket format")
    ques7_df = fetch_highest_scores_with_player()
    st.dataframe(ques7_df)
#---------------------------------------
#QUES 8
#--------------------------------------

    VENUE_COUNTRY_MAP = {
        "Perth Stadium": "Australia",
        "Kennington Oval": "England",
        "Edgbaston": "England",
        "Hagley Oval": "England",
        "Kensington Oval": "Barbados",
        "Mission Road Ground": "Mong Kok",
    }
    def fetch_2024_series():
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                series_id,
                series_name,
                match_format,
                venue,
                MIN(start_date) AS series_start_date,
                COUNT(match_id) AS total_matches
            FROM ques_8
            WHERE YEAR(start_date) = 2024
            GROUP BY series_id, series_name, match_format, venue;
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

    # Convert into DataFrame
        df = pd.DataFrame(rows)

    # Map venue → host country
        df["host_country"] = df["venue"].apply(
            lambda v: VENUE_COUNTRY_MAP.get(v, "Unknown")
        )
    # Reorder columns
        df = df[[
        "series_name",
        "host_country",
        "match_format",
        "series_start_date",
        "total_matches",
        "venue",
        "series_id"
        ]]
        return df
    st.markdown("### Ques 8 Series 2024")
    ques8_df = fetch_2024_series()
    st.dataframe(ques8_df)


#--------------------------------------
#QUES 9
#-------------------------------------
    def fetch_all_rounders():
        conn = get_connection()
        query = """
        SELECT
            r.name AS player_name,
            r.format AS format,
            r.runs AS total_runs,
            b.wickets AS total_wickets
        FROM
            run_stats_by_format r
        INNER JOIN
            bowling_stats b
                ON r.player_id = b.player_id
        WHERE
            r.runs > 1000
            AND b.wickets > 50
        ORDER BY
            r.runs DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 9 All rounder players")
    ques9_df = fetch_all_rounders()
    st.dataframe(ques9_df)
#------------------------------------
#QUES 10
#-----------------------------------

    def get_last_20_completed_matches():
        conn = get_connection()
        query = """
        SELECT
            match_desc,
            team1,
            team2,
            venue,
            status,
            SUBSTRING_INDEX(status, ' won', 1) AS winning_team,
            CASE
                WHEN status LIKE '%runs%' THEN 'Runs'
                WHEN status LIKE '%wkt%' OR status LIKE '%wickets%' THEN 'Wickets'
                ELSE 'Unknown'
            END AS victory_type,
            CASE
                WHEN status LIKE '%runs%' THEN
                    SUBSTRING_INDEX(
                        SUBSTRING_INDEX(status, ' runs', 1), ' ', -1
                    )
                WHEN status LIKE '%wickets%' THEN
                    SUBSTRING_INDEX(
                        SUBSTRING_INDEX(status, ' wickets', 1), ' ', -1
                    )
                WHEN status LIKE '%wkts%' THEN
                    SUBSTRING_INDEX(
                        SUBSTRING_INDEX(status, ' wkts', 1), ' ', -1
                    )
                ELSE NULL
            END AS victory_margin
        FROM matches
        WHERE status LIKE '%won%'
        ORDER BY match_id DESC
        LIMIT 20;
        """

        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 10 Details of 20 completed matches")
    ques10_df = get_last_20_completed_matches()
    st.dataframe(ques10_df)
#------------------------------------------
#QUES 11
#----------------------------------------
    def player_format_comparison():
        conn = get_connection()
        query = """
        SELECT
            player_id,
            name,
            SUM(CASE WHEN format = 'Test' THEN runs ELSE 0 END) AS test_runs,
            SUM(CASE WHEN format = 'ODI' THEN runs ELSE 0 END) AS odi_runs,
            SUM(CASE WHEN format = 'T20I' THEN runs ELSE 0 END) AS t20i_runs,
            ROUND(SUM(runs) / SUM(innings), 2) AS overall_average,
            COUNT(DISTINCT format) AS formats_played
        FROM run_stats_by_format
        GROUP BY player_id, name
        HAVING COUNT(DISTINCT format) >= 2
        ORDER BY SUM(runs) DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 11 Player's performance in different formats")
    ques11_df = player_format_comparison()
    st.dataframe(ques11_df)
#--------------------------------------
#QUES 12
#------------------------------------
    def fetch_matches():
        conn = get_connection()
        query = """
            SELECT winnerTeam, city
            FROM ipl
            WHERE winnerTeam IN (
            'CHENNAI SUPER KINGS', 'DELHI CAPITALS', 'KOLKATA KNIGHT RIDERS',
            'LUCKNOW SUPER GIANTS', 'MUMBAI INDIANS', 'PUNJAB KINGS',
            'RAJASTHAN ROYALS', 'SUNRISERS HYDERABAD'
        )
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df


    def calculate_home_away_wins(df):
        TEAM_CITY_MAP = {
            "MUMBAI INDIANS": "Mumbai",
            "SUNRISERS HYDERABAD": "Hyderabad",
            "DELHI CAPITALS": "Delhi",
            "CHENNAI SUPER KINGS": "Chennai",
            "LUCKNOW SUPER GIANTS": "Lucknow",
            "PUNJAB KINGS": "Mohali",
            "KOLKATA KNIGHT RIDERS": "Kolakata",
            "RAJASTHAN ROYALS": "Jaipur"
        }

        teams = list(TEAM_CITY_MAP.keys())

    # Determine home win: winner's city matches match city
        df['Home_Win'] = df.apply(lambda x: 1 if TEAM_CITY_MAP.get(x['winnerTeam'], "") == x['city'] else 0, axis=1)
        df['Away_Win'] = df['Home_Win'].apply(lambda x: 0 if x == 1 else 1)

    # Aggregate wins by team
        home_wins = df.groupby('winnerTeam')['Home_Win'].sum().reindex(teams, fill_value=0)
        away_wins = df.groupby('winnerTeam')['Away_Win'].sum().reindex(teams, fill_value=0)

    # Combine into a single DataFrame
        performance = pd.DataFrame({
            "Home_Wins": home_wins,
            "Away_Wins": away_wins
        })
        return performance
    if __name__ == "__main__":
        df_matches = fetch_matches()
    home_away_performance = calculate_home_away_wins(df_matches)
    print(home_away_performance)
    st.markdown("### Ques 12 Performance at home v/s away")
    st.dataframe(home_away_performance)

#----------------------------------------------------------------
#QUES 13
#-----------------------------------------------------------
    conn = get_connection()
    query = """
    SELECT 
        id AS batting_position,
        batter,
        runs
    FROM sl_1st_innings
    ORDER BY id;
    """

    df = pd.read_sql(query, conn)
    conn.close()

    print("\n=== RAW DATA ===")
    print(df)

# -----------------------------
# Compute Partnerships
# -----------------------------
    partnerships = []

    for i in range(len(df) - 1):
        p1 = df.iloc[i]
        p2 = df.iloc[i + 1]

        combined_runs = p1["runs"] + p2["runs"]

    # Check condition: partnership >= 100 runs
        if combined_runs >= 100:
            partnerships.append({
                "batter_1": p1["batter"],
                "batter_2": p2["batter"],
                "runs_1": p1["runs"],
                "runs_2": p2["runs"],
                "combined_runs": combined_runs,
                "partnership_between_positions": f"{p1['batting_position']} & {p2['batting_position']}",
                "innings": "1st Innings (SL)"
            })

# Convert to DataFrame
    df_partnerships = pd.DataFrame(partnerships)

    print("\n PARTNERSHIPS >= 100 RUNS")
    print(df_partnerships)
    st.markdown("### Ques 13 Batting partnerships")
    st.dataframe(df_partnerships)

#----------------------------------------------
#QUES 14
#-------------------------------------------
    conn = get_connection()
    query_bowling = "SELECT * FROM ques_14_n"
    df_bowling = pd.read_sql(query_bowling, conn)

    query_venue = "SELECT matchId, venue FROM ipl"
    df_venue = pd.read_sql(query_venue, conn)

# Convert overs column to float
    def overs_to_float(overs_str):
        if pd.isna(overs_str):
            return 0
        parts = str(overs_str).split('.')
        overs = int(parts[0])
        balls = int(parts[1]) if len(parts) > 1 else 0
        return overs + balls / 6

    df_bowling['overs'] = df_bowling['overs'].apply(overs_to_float)

# Convert numeric columns
    df_bowling['wickets'] = pd.to_numeric(df_bowling['wickets'], errors='coerce')
    df_bowling['runs'] = pd.to_numeric(df_bowling['runs'], errors='coerce')
    df_bowling['economy'] = pd.to_numeric(df_bowling['economy'], errors='coerce')

# Merge with venue info
    df = df_bowling.merge(df_venue, left_on='match_id', right_on='matchId', how='left')

# Filter for bowlers with >2 overs
    df = df[df['overs'] > 2]

# Group by bowler and venue
    bowling_stats_df = df.groupby(['bowler_id', 'name', 'venue']).agg(
        matches_played=('match_id','nunique'),
        total_wickets=('wickets','sum'),
        avg_economy=('economy','mean')
    ).reset_index()

# Keep only bowlers with >=2 matches at the venue
    bowling_stats_df = bowling_stats_df[bowling_stats_df['matches_played'] >= 2]

# Sort results
    bowling_stats_df = bowling_stats_df.sort_values(['venue', 'avg_economy'])

# Show results
    print(bowling_stats_df)
    conn.close()
    st.markdown("### Ques 14 Bowling performance at different venues")
    st.dataframe(bowling_stats_df)


#------------------------------------
#QUES 15
#------------------------------------
    def fetch_high_scorers():
        conn = get_connection()
        query = """
            SELECT 
                Player,
                MatchesPlayed,
                InningsPlayed,
                TotalRuns,
                AverageRuns,
                TotalBalls,
                StrikeRate,
                TeamWins
            FROM 
                ques_15
            WHERE 
                TotalRuns > 100
            ORDER BY 
                TotalRuns DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

# Display result for Ques 15
    st.markdown("### Ques 15 Exceptionally well in close matches")
    high_scorers_df = fetch_high_scorers()
    st.dataframe(high_scorers_df)

#-----------------------------------
#QUES 16
#------------------------------------
    conn = get_connection()
    query = """
    SELECT
        name AS player_name,
        year,
        AVG(runs) AS avg_runs,
        AVG(strkrate) AS avg_strike_rate
    FROM
        ques_16
    WHERE
        year >= '2020'
        AND name IN (
            SELECT name
            FROM ques_16
            WHERE year >= '2020'
            GROUP BY name
            HAVING COUNT(DISTINCT year) = 5
        )
    GROUP BY
        name, year
    ORDER BY
        player_name ASC,
        year ASC,
        avg_strike_rate ASC
    LIMIT 20;
    """

    ques16_df = pd.read_sql(query, conn)  # renamed DataFrame
    conn.close()
    
    print(ques16_df)
    st.markdown("### Ques 16 Batting performance over different years")
    st.dataframe(ques16_df)

#------------------------------------
#QUES 17
#----------------------------------
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM ques_17", conn)
    conn.close()

# 3️⃣ Create a column to indicate if toss winner also won the match
    df['toss_win_match'] = df['tossWinnerName'] == df['winningTeam']

# 4️⃣ Group by toss decision and calculate percentage of matches won by toss winners
    summary = df.groupby('decision').agg(
        total_matches=('matchId', 'count'),
        matches_won_by_toss_winner=('toss_win_match', 'sum')
    ).reset_index()

    summary['win_percentage'] = round(
        (summary['matches_won_by_toss_winner'] / summary['total_matches']) * 100, 2
    )
    print(summary)
    st.markdown("### Ques 17 Toss decision")
    st.dataframe(summary)

#-----------------------------------
#QUES 18
#----------------------------------
    def ques_18():
        query = """
        WITH
            eco AS (
                SELECT playerId, name,
                    CAST(ODI AS DECIMAL(5,2)) AS odi_eco,
                    CAST(T20 AS DECIMAL(5,2)) AS t20_eco
                FROM ques_18
                WHERE Stat = 'Eco'
            ),
            wickets AS (
                SELECT playerId,
                    CAST(ODI AS UNSIGNED) AS odi_wkts,
                    CAST(T20 AS UNSIGNED) AS t20_wkts
                FROM ques_18
                WHERE Stat = 'Wickets'
            )
        SELECT
            e.name AS player_name,
            ROUND((e.odi_eco + e.t20_eco) / 2, 2) AS overall_economy,
            (w.odi_wkts + w.t20_wkts) AS total_wickets
        FROM eco e
        JOIN wickets w ON e.playerId = w.playerId
        ORDER BY overall_economy ASC, total_wickets DESC
        LIMIT 10;
        """

# Execute query and load into DataFrame
        conn = get_connection()
        ques_18 = pd.read_sql(query, conn)
        conn.close()
        print(ques_18)
        st.markdown("### Ques 18 Most economical bowlers ")
        st.dataframe(ques_18)

#-------------------------------------
#QUES 19
#------------------------------------
    def ques_19():
        conn = get_connection()
        query = """
        SELECT
            name AS player_name,
            COUNT(*) AS innings_played,
            AVG(runs) AS avg_runs,
            STDDEV(runs) AS stddev_runs
        FROM
            ques_16
        WHERE
            year IN ('2022', '2023', '2024', '2025')
            AND balls >= 10
        GROUP BY
            name
        HAVING
            COUNT(*) >= 2
        ORDER BY
            stddev_runs DESC;
        """

        ques_19 = pd.read_sql(query, conn)
        print(ques_19)
        conn.close()
        st.markdown("### Ques 19 Batsmen consistency")
        st.dataframe(ques_19)

#----------------------------------------
#QUES 20
#----------------------------------------
    def ques_20():
        conn = get_connection()
        query = """
        SELECT
            pp.name,
            pbs.Matches_ODI,
            pbs.Matches_T20,
            pbs.Matches_IPL,
            pbs.Average_ODI,
            pbs.Average_T20,
            pbs.Average_IPL,
            (COALESCE(pbs.Matches_ODI,0) + COALESCE(pbs.Matches_T20,0) + COALESCE(pbs.Matches_IPL,0)) AS total_matches
        FROM
            player_batting_stats AS pbs
        JOIN
            player_profiles AS pp
        ON
            pbs.player_id = pp.player_id
        WHERE
            (COALESCE(pbs.Matches_ODI,0) + COALESCE(pbs.Matches_T20,0) + COALESCE(pbs.Matches_IPL,0)) >= 20
        ORDER BY
            total_matches DESC;
        """
# Load query into Pandas DataFrame
        ques_20 = pd.read_sql(query, conn)
        print(ques_20)
        conn.close()
        st.markdown("### Ques 20 Performance in different formats")
        st.dataframe(ques_20)

#------------------------------------
#QUES 21
#-----------------------------------
    def ques_21():
        conn = get_connection()
        query = """
        WITH pivoted AS (
            SELECT
                playerId,
                name,
                MAX(CASE WHEN Stat = 'Runs' THEN Test END) AS runs_test,
                MAX(CASE WHEN Stat = 'Avg' THEN Test END) AS avg_test,
                MAX(CASE WHEN Stat = 'SR' THEN Test END) AS sr_test,
                MAX(CASE WHEN Stat = 'Wickets' THEN Test END) AS wickets_test,
                MAX(CASE WHEN Stat = 'Eco' THEN Test END) AS eco_test,
                MAX(CASE WHEN Stat = 'Avg' THEN Test END) AS bowl_avg_test
            FROM ques_18
            GROUP BY playerId, name
        ),

        scores AS (
            SELECT
                playerId,
                name,
                (runs_test * 0.01) +
                (avg_test * 0.5) +
                (sr_test * 0.3) AS batting_points,
                (wickets_test * 2) +
                ((50 - bowl_avg_test) * 0.5) +
                ((6 - eco_test) * 2) AS bowling_points
            FROM pivoted
        )

        SELECT
            name,
            batting_points,
            bowling_points,
            (batting_points + bowling_points) AS total_score
        FROM scores
        ORDER BY total_score DESC;
        """

        ques_21 = pd.read_sql(query, conn)
        print(ques_21)
        conn.close()
        st.markdown("### Ques 21 Ranking system")
        st.dataframe(ques_21)

#------------------------------------
#QUES 22
#------------------------------------
    conn = get_connection()
    query = """
    SELECT matchId, team1Name, team2Name, winnerTeam, status
    FROM ipl
    WHERE 
        (team1Name = 'MUMBAI INDIANS' AND team2Name = 'DELHI CAPITALS') OR
        (team1Name = 'DELHI CAPITALS' AND team2Name = 'MUMBAI INDIANS') OR
        (team1Name = 'CHENNAI SUPER KINGS' AND team2Name = 'SUNRISERS HYDERABAD') OR
        (team1Name = 'SUNRISERS HYDERABAD' AND team2Name = 'CHENNAI SUPER KINGS') OR
        (team1Name = 'RAJASTHAN ROYALS' AND team2Name = 'KOLKATA KNIGHT RIDERS') OR
        (team1Name = 'KOLKATA KNIGHT RIDERS' AND team2Name = 'RAJASTHAN ROYALS') OR
        (team1Name = 'MUMBAI INDIANS' AND team2Name = 'RAJASHTAN ROYALS') OR
        (team1Name = 'RAJASHTAN ROYALS' AND team2Name = 'MUMBAI INDIANS') OR
        (team1Name = 'CHENNAI SUPER KINGS' AND team2Name = 'MUMBAI INDIANS') OR
        (team1Name = 'MUMBAI INDIANS' AND team2Name = 'CHENNAI SUPER KINGS') OR
        (team1Name = 'MUMBAI INDIANS' AND team2Name = 'GUJARAT TITANS') OR
        (team1Name = 'GUJARAT TITANS' AND team2Name = 'MUMBAI INDIANS');
    """
    df = pd.read_sql(query, conn)
    conn.close()

# -----------------------------
# 3. Normalize team names
# -----------------------------
    for col in ['team1Name','team2Name','winnerTeam']:
        df[col] = df[col].str.upper().str.strip()

# -----------------------------
# 4. Extract victory margin
# -----------------------------
    def extract_margin(status):
        if pd.isna(status):
            return None
        m = re.search(r'won by (\d+) (runs|wkt|wkts)', status.lower())
        if m:
            return int(m.group(1))
        return None

    df['victoryMargin'] = df['status'].apply(extract_margin)

# -----------------------------
# 5. Assign teamA and teamB alphabetically
# -----------------------------
    df['teamA'] = df[['team1Name','team2Name']].min(axis=1)
    df['teamB'] = df[['team1Name','team2Name']].max(axis=1)

# -----------------------------
# 6. Compute head-to-head stats
# -----------------------------
    grouped = df.groupby(['teamA','teamB'])

    result = grouped.apply(lambda x: pd.Series({
        'total_matches': len(x),
        'teamA_wins': (x['winnerTeam'] == x['teamA']).sum(),
        'teamB_wins': (x['winnerTeam'] == x['teamB']).sum(),
        'teamA_avg_margin': x.loc[x['winnerTeam'] == x['teamA'], 'victoryMargin'].mean(),
        'teamB_avg_margin': x.loc[x['winnerTeam'] == x['teamB'], 'victoryMargin'].mean(),
        'teamA_win_pct': (x['winnerTeam'] == x['teamA']).mean() * 100,
        'teamB_win_pct': (x['winnerTeam'] == x['teamB']).mean() * 100
    })).reset_index()

    print(result)
    st.markdown("### Ques 22 Head to head match analysis")
    st.dataframe(result)

#--------------------------------
#QUES 23
#--------------------------------
    MAX_MATCHES = 10  # last N matches to consider
    conn = get_connection()
    df = pd.read_sql(
        "SELECT match_id, id, name, balls, runs, strkrate, year FROM ques_16",
        conn
    )
    conn.close()

# --- Sort by player and by match (chronological) ---
    df = df.sort_values(by=["name", "match_id"]).reset_index(drop=True)

# --- Function to compute metrics for a player ---
    def compute_form_metrics(player_df, max_matches=MAX_MATCHES):
        recent = player_df.tail(max_matches)  # last N matches
        runs = recent["runs"].values
        sr = recent["strkrate"].values
    
        last_5_runs = recent["runs"].tail(5)
        avg_last_5 = last_5_runs.mean()
    
        avg_last_10 = runs.mean()
        std_runs = runs.std(ddof=0)
        fifty_plus = (runs >= 50).sum()
    
        return {
            "avg_last_5": avg_last_5,
            "avg_last_10": avg_last_10,
            "std_runs": std_runs,
            "fifty_plus_count": fifty_plus,
            "sr_last_5": sr[-5:].mean() if len(sr) >= 5 else sr.mean(),
            "sr_first_5": sr[:5].mean() if len(sr) >= 5 else sr.mean()
        }

# --- Compute metrics for all players ---
    records = []
    for name, g in df.groupby("name"):
        metrics = compute_form_metrics(g)
        rec = {
            "name": name,
            "avg_last_5": metrics["avg_last_5"],
            "avg_last_10": metrics["avg_last_10"],
            "std_runs": metrics["std_runs"],
            "fifty_plus_count": metrics["fifty_plus_count"],
            "sr_last_5": metrics["sr_last_5"],
            "sr_first_5": metrics["sr_first_5"]
        }
        records.append(rec)

    form_df = pd.DataFrame(records)

# --- Categorize form ---
    def categorize_form(row):
        if (row["avg_last_5"] >= row["avg_last_10"] * 0.9) and (row["std_runs"] < row["avg_last_10"] * 0.5) and (row["fifty_plus_count"] >= 2):
            return "Excellent Form"
        if (row["avg_last_5"] >= row["avg_last_10"] * 0.7) and (row["std_runs"] < row["avg_last_10"] * 0.7):
            return "Good Form"
        if (row["avg_last_5"] >= row["avg_last_10"] * 0.5):
            return "Average Form"
        return "Poor Form"

# --- Add the form category column ---
    form_df["form_category"] = form_df.apply(categorize_form, axis=1)

# --- Custom top selection ---
    good_form = form_df[form_df["form_category"] == "Good Form"].sort_values(by="avg_last_5", ascending=False).head(10)
    average_form = form_df[form_df["form_category"] == "Average Form"].sort_values(by="avg_last_5", ascending=False).head(5)
    poor_form = form_df[form_df["form_category"] == "Poor Form"].sort_values(by="avg_last_5", ascending=False).head(3)

    custom_top_players = pd.concat([good_form, average_form, poor_form]).reset_index(drop=True)

# --- Display results ---
    print(custom_top_players)
    st.markdown("### Ques 23 Player's form")
    st.dataframe(custom_top_players)

#----------------------------------------
#QUES 24
#----------------------------------------
    st.markdown("## Ques 24 Batting partnerships")

# -----------------------------
# 1. Connect to MySQL database
# -----------------------------
    conn = get_connection()
    query = """
    SELECT match_id, id AS player_id, name, runs
    FROM ques_16
    ORDER BY match_id, player_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

# -----------------------------
# 3. Ensure runs is numeric
# -----------------------------
    df['runs'] = pd.to_numeric(df['runs'], errors='coerce')

# -----------------------------
# 4. Prepare consecutive batsmen pairs
# -----------------------------
    df['next_player'] = df.groupby('match_id')['name'].shift(-1)
    df['next_player_id'] = df.groupby('match_id')['player_id'].shift(-1)
    df['next_runs'] = df.groupby('match_id')['runs'].shift(-1)

# Only keep valid rows
    partnerships = df.dropna(subset=['next_player', 'next_runs']).copy()

# Partnership runs
    partnerships['partnership_runs'] = partnerships['runs'] + partnerships['next_runs']

# -----------------------------
# 5. Standardize player pair order
# -----------------------------
    partnerships['playerA'] = partnerships[['name', 'next_player']].min(axis=1)
    partnerships['playerB'] = partnerships[['name', 'next_player']].max(axis=1)

# -----------------------------
# 6. Calculate partnership stats
# -----------------------------
    grouped = partnerships.groupby(['playerA', 'playerB'])

    partnership_stats = grouped.agg(
        total_partnerships=('partnership_runs', 'count'),
        avg_partnership_runs=('partnership_runs', 'mean'),
        partnerships_over_50=('partnership_runs', lambda x: (x >= 50).sum()),
        highest_partnership=('partnership_runs', 'max')
    ).reset_index()

# Success rate
    partnership_stats['success_rate'] = (
        partnership_stats['partnerships_over_50'] /
        partnership_stats['total_partnerships'] * 100
    )

# -----------------------------
# 7. Debug print (Top 20)
# -----------------------------
    st.dataframe(
        partnership_stats.sort_values('avg_partnership_runs', ascending=False).head(20)
    )

#-----------------------------------------
#QUES 25
#-----------------------------------------
    conn = get_connection()
    query = """
    SELECT match_id, id AS player_id, name, balls, runs, fours, sixes, strkrate, year
    FROM ques_16
    """
    df = pd.read_sql(query, conn)
    conn.close()

# -----------------------------
# 3. Ensure proper types
# -----------------------------
    df['runs'] = pd.to_numeric(df['runs'], errors='coerce')
    df['strkrate'] = pd.to_numeric(df['strkrate'], errors='coerce')
    df['year'] = pd.to_numeric(df['year'], errors='coerce')

# -----------------------------
# 4. Compute yearly averages per player
# -----------------------------
    yearly_stats = df.groupby(['player_id','name','year']).agg(
        avg_runs=('runs', 'mean'),
        avg_strkrate=('strkrate', 'mean')
    ).reset_index()

# -----------------------------
# 5. Compare each year to previous year
# -----------------------------
    yearly_stats = yearly_stats.sort_values(['player_id','year'])
    yearly_stats['runs_diff'] = yearly_stats.groupby('player_id')['avg_runs'].diff()
    yearly_stats['strkrate_diff'] = yearly_stats.groupby('player_id')['avg_strkrate'].diff()

# -----------------------------
# 6. Identify yearly trend
# -----------------------------
    def yearly_trend(row):
        if pd.isna(row['runs_diff']):
            return 'Stable'
        if row['runs_diff'] > 5 or row['strkrate_diff'] > 5:  # threshold can be adjusted
            return 'Improving'
        elif row['runs_diff'] < -5 or row['strkrate_diff'] < -5:
            return 'Declining'
        else:
            return 'Stable'

    yearly_stats['yearly_trend'] = yearly_stats.apply(yearly_trend, axis=1)

# -----------------------------
# 7. Determine overall career trajectory
# -----------------------------
    def career_phase(player_df):
        improving = (player_df['yearly_trend'] == 'Improving').sum()
        declining = (player_df['yearly_trend'] == 'Declining').sum()
        stable = (player_df['yearly_trend'] == 'Stable').sum()
    
        if improving > declining and improving >= stable:
            return 'Career Ascending'
        elif declining > improving and declining >= stable:
            return 'Career Declining'
        else:
            return 'Career Stable'

    career_trajectory = yearly_stats.groupby(['player_id','name']).apply(career_phase).reset_index()
    career_trajectory.columns = ['player_id','name','career_phase']

# -----------------------------
# 8. Merge trajectory with yearly stats
# -----------------------------
    final_df = yearly_stats.merge(career_trajectory, on=['player_id','name'])
    print(final_df.head(20))
    st.markdown("### Ques 25 Player performance evolution")
    st.dataframe(final_df.head(20))


#===========================================================
# =========================================================
#        CRUD PAGE
# =========================================================
#==========================================================

elif st.session_state.page == "CRUD Operations":
    st.markdown("<h1 style='color: green; text-align: center;'>🛠️ CRUD Operations</h1>", unsafe_allow_html=True)
    st.markdown("""
    Hello User! now you can CREATE, READ, UPDATE and DELETE.
    """)

    def crud_page():
    
    # ------------------------------
    # Table Selection
    # ------------------------------
        tables = {
        "🏏 Batsmen": "run_stats_by_format",
        "🎯 Bowlers": "bowling_stats_format",
        "👤 Players": "player_profiles",
    }
        table_display = st.selectbox("Select Table to Manage:", list(tables.keys()))
        table_name = tables[table_display]

    # Fetch columns
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        schema = cursor.fetchall()
        conn.close()
        cols = [c[0] for c in schema]
        pk = cols[0]  # assume first column is primary key

    # ------------------------------
    # READ Records
    # ------------------------------
        st.markdown("---")
        with st.expander("📖 View Table Data", expanded=False):
            conn = get_connection()
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            conn.close()
            if df.empty:
                st.info("No records available.")
            else:
                st.dataframe(df, use_container_width=True)

    # ------------------------------
    # CREATE Records
    # ------------------------------
        st.markdown("---")
        with st.expander("➕ Add New Record"):
            with st.form("create_form"):
                inputs = {}
                for col in cols:
                    inputs[col] = st.text_input(f"{col}")
                submitted = st.form_submit_button("Add Record")
                if submitted:
                    conn = get_connection()
                    cur = conn.cursor()
                    q_cols = ", ".join(cols)
                    placeholders = ", ".join(["%s"] * len(cols))
                    cur.execute(f"INSERT INTO {table_name} ({q_cols}) VALUES ({placeholders})", list(inputs.values()))
                    conn.commit()
                    conn.close()
                    st.success("🎉 Record added successfully!")

    # ------------------------------
    # UPDATE Records
    # ------------------------------
        st.markdown("---")
        with st.expander("✏️ Update Record"):
            conn = get_connection()
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            conn.close()
            if df.empty:
                st.info("No records available to update.")
            else:
                selected_id = st.selectbox("Select record to update:", df[pk].tolist(), key=f"update_{table_name}")
                row = df[df[pk] == selected_id].iloc[0]

                with st.form("update_form"):
                    updated_vals = {}
                    for col in cols:
                        updated_vals[col] = st.text_input(col, value=row[col])
                    submitted = st.form_submit_button("Update Record")
                    if submitted:
                        conn = get_connection()
                        cur = conn.cursor()
                        set_clause = ", ".join([f"{c}=%s" for c in cols])
                        cur.execute(f"UPDATE {table_name} SET {set_clause} WHERE {pk}=%s", list(updated_vals.values()) + [selected_id])
                        conn.commit()
                        conn.close()
                        st.success("🔄 Record updated successfully!")

    # ------------------------------
    # DELETE Records
    # ------------------------------
        st.markdown("---")

# Delete record expander
        with st.expander("🗑 Delete Record"):
    # Fetch table data
            conn = get_connection()
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            conn.close()

            if df.empty:
                st.info("No records available to delete.")
            else:
        # Select player by name
                delete_name = st.selectbox("Select player to delete:", df['name'].tolist(), key=f"delete_{table_name}")

        # Delete button
                if st.button("Delete Record", key=f"del_btn_{table_name}"):
            # Map name to primary key
                    delete_id = df.loc[df['name'] == delete_name, pk].iat[0]

                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(f"DELETE FROM {table_name} WHERE {pk}=%s", (delete_id,))
                    conn.commit()
                    conn.close()

                    st.success(f"✅ Record for '{delete_name}' deleted successfully!")
    crud_page()
#=========================================================
#END
#=======================================================

















