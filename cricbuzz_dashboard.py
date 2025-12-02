import streamlit as st
import pandas as pd
import mysql.connector
from PIL import Image
import re
import numpy as np
import requests
from datetime import datetime

# -----------------------------
# 1. Page configuration
# -----------------------------
st.set_page_config(
    page_title="Cricbuzz Dashboard",
    page_icon="🏏",
    layout="wide"
)
# -----------------------------
# 2. Navigation setup using session_state
# -----------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

def set_page(page_name):
    st.session_state.page = page_name

# Sidebar with markdown "links"
st.sidebar.markdown("<h3 style='margin-bottom: 0;'>NAVIGATE:</h3>", unsafe_allow_html=True)

if st.sidebar.button("Home", key="home_btn"):
    set_page('Home')
if st.sidebar.button("Live Matches", key="live_btn"):
    set_page('Live Matches')
if st.sidebar.button("Player Statistics", key="player_btn"):
    set_page('Player Statistics')
if st.sidebar.button("CRUD Operations", key="crud_btn"):
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
    st.markdown("<h1 style='color: blue;'>Welcome to the Cricbuzz Dashboard!</h1>", unsafe_allow_html=True)
    st.markdown("Stay updated with live cricket matches and stats.")
#--------------------------------------------
#--------------------------------------
#LIVE MATCHES
#------------------------------------
elif st.session_state.page == "Live Matches":
    st.markdown("<h2 style='color: green;'>Live Matches</h2>", unsafe_allow_html=True)
#------------------------------------------

    @st.cache_data
    def get_live_matches():
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
            "x-rapidapi-key": "d44b114a12mshafcb27880288e49p19823ejsndcc964aece66", 
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers)
        return response.json()

# Manual refresh button

    if st.button("🔄 Refresh Live Matches"):
        st.cache_data.clear()
        st.experimental_rerun()

# Load matches

    data = get_live_matches()
    matches = []

    for match_type in data.get("typeMatches", []):
        type_name = match_type.get("matchType")
        for series in match_type.get("seriesMatches", []):
            if "seriesAdWrapper" in series:
                for match in series["seriesAdWrapper"].get("matches", []):
                    match_info = match.get("matchInfo", {})
                    match_score = match.get("matchScore", {})
                    team1 = match_info.get("team1", {})
                    team2 = match_info.get("team2", {})

                    team1_score = match_score.get("team1Score", {}).get("inngs1", {})
                    team2_score = match_score.get("team2Score", {}).get("inngs1", {})

                    matches.append({
                        "MatchType": type_name,
                        "Series": match_info.get("seriesName"),
                        "Match": match_info.get("matchDesc"),
                        "Format": match_info.get("matchFormat"),
                        "Status": match_info.get("stateTitle"),
                        "Team 1": team1.get("teamName"),
                        "Team 1 Runs": team1_score.get("runs"),
                        "Team 1 Wickets": team1_score.get("wickets"),
                        "Team 1 Overs": team1_score.get("overs"),
                        "Team 2": team2.get("teamName"),
                        "Team 2 Runs": team2_score.get("runs"),
                        "Team 2 Wickets": team2_score.get("wickets"),
                        "Team 2 Overs": team2_score.get("overs"),
                    })

# Convert to DataFrame

    df_matches = pd.DataFrame(matches)

# Filters

    if not df_matches.empty:
        match_types = ["All"] + df_matches["MatchType"].dropna().unique().tolist()
        selected_type = st.selectbox("Select Match Type", match_types, index=0, key="match_type_filter")

        filtered_df = df_matches.copy()
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["MatchType"] == selected_type]

        formats = ["All"] + filtered_df["Format"].dropna().unique().tolist()
        selected_format = st.selectbox("Select Format", formats, index=0, key="format_filter")

        if selected_format != "All":
            filtered_df = filtered_df[filtered_df["Format"] == selected_format]

    # Expandable Match Cards
    
        for idx, row in filtered_df.iterrows():
            with st.expander(f"{row['Match']} — {row['Team 1']} vs {row['Team 2']} [{row['Status']}]"):
                st.markdown(f"**Series:** {row['Series']}")
                st.markdown(f"**Format:** {row['Format']}")
                st.markdown(f"**Status:** {row['Status']}")
                st.markdown("---")
            # Scores table
                score_data = {
                    "Team": [row['Team 1'], row['Team 2']],
                    "Runs": [row['Team 1 Runs'], row['Team 2 Runs']],
                    "Wickets": [row['Team 1 Wickets'], row['Team 2 Wickets']],
                    "Overs": [row['Team 1 Overs'], row['Team 2 Overs']]
                }
                st.table(pd.DataFrame(score_data))
    else:
        st.info("No live matches at the moment.")


#---------------------------------------------------
#PLAYER STATISTICS
#----------------------------------------------------

elif st.session_state.page == "Player Statistics":
    st.markdown("<h2 style='color: green;'>Top Batsmen and Bowlers</h2>", unsafe_allow_html=True)

# ----------------------------
# BATSMEN - RANKINGS

    def load_top_batsmen(format_type, metric):
        conn = get_connection()

    # Map format → correct columns
        cols = {
            "Test": ("Runs_Test", "Average_Test", "SR_Test", "Matches_Test", "Innings_Test"),
            "ODI":  ("Runs_ODI", "Average_ODI", "SR_ODI", "Matches_ODI", "Innings_ODI"),
            "T20":  ("Runs_T20", "Average_T20", "SR_T20", "Matches_T20", "Innings_T20")
        }

        runs_col, avg_col, sr_col, matches_col, inns_col = cols[format_type]

    # Determine aggregation and order column based on metric
        if metric == "Runs":
            agg_col = f"SUM(p.{runs_col})"
            order_col = agg_col
        elif metric == "Average":
            agg_col = f"AVG(p.{avg_col})"
            order_col = agg_col
        else:  # StrikeRate
            agg_col = f"AVG(p.{sr_col})"
            order_col = agg_col

        query = f"""
            SELECT 
                p.player_id,
                c.name AS player_name,
                SUM(p.{runs_col}) AS Runs,
                AVG(p.{avg_col}) AS Average,
                AVG(p.{sr_col}) AS StrikeRate,
                SUM(p.{matches_col}) AS Matches,
                SUM(p.{inns_col}) AS Innings
            FROM player_batting_stats p
            JOIN cricket_stats c ON p.player_id = c.player_id
            GROUP BY p.player_id, c.name
            ORDER BY {order_col} DESC
            LIMIT 10;
        """

        df = pd.read_sql(query, conn)
        conn.close()

    # Add Rank column
        df.insert(0, "Rank", range(1, len(df) + 1))

        return df


# Format Selection
    format_choice = st.selectbox(
        "Select Format",
        ["Test", "ODI", "T20"]
    )

    st.write("Showing Top 10 based on Runs, Average, and Strike Rate.")

# Tabs for different metrics
    tab1, tab2, tab3 = st.tabs(["🏅 Top by Runs", "📈 Top by Average", "⚡ Top by Strike Rate"])

    with tab1:
        st.subheader(f"Top 10 {format_choice} Batsmen — by Runs")
        df_runs = load_top_batsmen(format_choice, "Runs")
        st.dataframe(df_runs, use_container_width=True)

    with tab2:
        st.subheader(f"Top 10 {format_choice} Batsmen — by Average")
        df_avg = load_top_batsmen(format_choice, "Average")
        st.dataframe(df_avg, use_container_width=True)

    with tab3:
        st.subheader(f"Top 10 {format_choice} Batsmen — by Strike Rate")
        df_sr = load_top_batsmen(format_choice, "StrikeRate")
        st.dataframe(df_sr, use_container_width=True)

#------------------------------------------
#BOWLER RANKINGS
    def load_top_bowlers(format_type, metric):
        conn = get_connection()
    # Map metrics to table column
        metric_col_map = {
            "Wickets": "Wickets",
            "Average": "Average",
            "Overs": "Overs"
        }
        order_col = metric_col_map[metric]

    # Ascending for Average, Descending for Wickets/Overs
        order_dir = "ASC" if metric == "Average" else "DESC"

        query = f"""
            SELECT PlayerID,
                Name AS Bowler,
                Matches,
                Overs,
                Wickets,
                Average,
                Format
            FROM bowling_stats_format
            WHERE Format = '{format_type.lower()}'
            ORDER BY {order_col} {order_dir}
            LIMIT 10
        """
        conn = get_connection()
        df = pd.read_sql(query, conn)
        conn.close()

    # Add ranking
        df.insert(0, "Rank", range(1, len(df) + 1))
        return df

#Format Selector
    format_choice = st.selectbox(
        "Select Format",
        ["Test", "ODI", "T20"],
        key="format_select" 
    )

    st.write("Showing Top 10 Bowlers based on Wickets, Average, and Overs.")

# Tabs for MetricS

    tab1, tab2, tab3 = st.tabs(["🏆 Top by Wickets", "🎯 Top by Average", "⏱️ Top by Overs"])

    with tab1:
        st.subheader(f"Top 10 {format_choice} Bowlers — by Wickets")
        df_wickets = load_top_bowlers(format_choice, "Wickets")
        st.dataframe(df_wickets, use_container_width=True)

    with tab2:
        st.subheader(f"Top 10 {format_choice} Bowlers — by Average")
        df_avg = load_top_bowlers(format_choice, "Average")
        st.dataframe(df_avg, use_container_width=True)

    with tab3:
        st.subheader(f"Top 10 {format_choice} Bowlers — by Overs")
        df_overs = load_top_bowlers(format_choice, "Overs")
        st.dataframe(df_overs, use_container_width=True)

#------------------------------------
#Playeer info

    def get_player_info(player_name):
        conn = get_connection()
        query = """
            SELECT name,
                format,
                debut,
                last_played,
                debut_match_id,
                last_match_id
            FROM player_stat
            WHERE name LIKE %s
        """
        conn = get_connection()
        df = pd.read_sql(query, conn, params=(f"%{player_name}%",))
        conn.close()
        return df


# Streamlit Page

    st.subheader("Player Information Lookup")

# Search Box

    player_input = st.text_input(
        "Search Player by Name",
        key="player_search"
    )


# Display Table

    if player_input:
        df_player = get_player_info(player_input)
        if df_player.empty:
            st.warning("No player found with that name.")
        else:
            st.dataframe(df_player, use_container_width=True)
    else:
        st.info("Type a player's name to see details.")





    
                 



#--------------------------------
#CRUD operations - SQL questions
#--------------------------------
elif st.session_state.page == "CRUD Operations":
    st.markdown("<h2 style='color: green;'>CRUD Operations</h2>", unsafe_allow_html=True)
    st.markdown("""
    This section contains SQL questions.
    """)

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
    st.markdown("### Ques 1")
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
    st.markdown("### Ques 2")
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
            r.match_type = 'ODI'
        ORDER BY 
            r.runs DESC
        LIMIT 6;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return (df)
    st.markdown("### Ques 3")
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
            capacity > 30000
        ORDER BY
            capacity DESC;
    """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 4")
    ques4_df = get_large_venues()
    st.dataframe(ques4_df)
#------------------------------------------------
#QUES 5
#----------------------------------------------
    def fetch_team_wins():
        conn = get_connection()
        query = """
        SELECT
            team_name,
            matches_won AS total_wins
        FROM 
            team_q5
        ORDER BY 
            total_wins DESC
        LIMIT 10;
        """
    
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 5")
    ques5_df = fetch_team_wins()
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
    st.markdown("### Ques 6")
    ques6_df = fetch_player_role_counts()
    st.dataframe(ques6_df)
#---------------------------------------
#QUES 7
#---------------------------------------
    def fetch_highest_scores_with_player():
        conn = get_connection()
        query = """
        SELECT
            r.match_type AS format,
            r.name AS player_name,
            r.runs AS highest_score
        FROM
            run_stats_by_format r
        INNER JOIN (
            SELECT
                match_type,
                MAX(runs) AS max_runs
            FROM
                run_stats_by_format
            GROUP BY
                match_type
        ) AS max_scores
        ON r.match_type = max_scores.match_type AND r.runs = max_scores.max_runs
        ORDER BY
            r.match_type;
        """
    
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 7")
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
    st.markdown("### Ques 8")
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
            r.match_type AS format,
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
    st.markdown("### Ques 9")
    ques9_df = fetch_all_rounders()
    st.dataframe(ques9_df)
#------------------------------------
#QUES 10
#-----------------------------------
#Ques-10
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
    st.markdown("### Ques 10")
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
            SUM(CASE WHEN match_type = 'Test' THEN runs ELSE 0 END) AS test_runs,
            SUM(CASE WHEN match_type = 'ODI' THEN runs ELSE 0 END) AS odi_runs,
            SUM(CASE WHEN match_type = 'T20I' THEN runs ELSE 0 END) AS t20i_runs,
            ROUND(SUM(runs) / SUM(innings), 2) AS overall_average,
            COUNT(DISTINCT match_type) AS formats_played
        FROM run_stats_by_format
        GROUP BY player_id, name
        HAVING COUNT(DISTINCT match_type) >= 2
        ORDER BY SUM(runs) DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    st.markdown("### Ques 11")
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
    st.markdown("### Ques 12")
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
    st.markdown("### Ques 13")
    st.dataframe(df_partnerships)

#----------------------------------------------
#QUES 14
#---------------------------------------------
    conn = get_connection()
    query_bowling = "SELECT * FROM ques_14_n"
    df_bowling = pd.read_sql(query_bowling, conn)

    query_venue = "SELECT matchId, venue FROM ipl"
    df_venue = pd.read_sql(query_venue, conn)

# -----------------------------
# 3. Convert overs column to float
# -----------------------------
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

# -----------------------------
# 4. Merge with venue info
# -----------------------------
    df = df_bowling.merge(df_venue, left_on='match_id', right_on='matchId', how='left')

# -----------------------------
# 5. Filter for bowlers with >2 overs
# -----------------------------
    df = df[df['overs'] > 2]

# -----------------------------
# 6. Group by bowler and venue
# -----------------------------
    bowling_stats = df.groupby(['bowler_id', 'name', 'venue']).agg(
        matches_played=('match_id','nunique'),
        total_wickets=('wickets','sum'),
        avg_economy=('economy','mean')
    ).reset_index()

# -----------------------------
# 7. Keep only bowlers with >=3 matches at the venue
# -----------------------------
    bowling_stats = bowling_stats[bowling_stats['matches_played'] >= 2]

# -----------------------------
# 8. Sort results
# -----------------------------
    bowling_stats = bowling_stats.sort_values(['venue', 'avg_economy'])

# -----------------------------
# 9. Show results
# -----------------------------
    print(bowling_stats)
    conn.close()
    st.markdown("### Ques 14")
    st.dataframe(bowling_stats)

#------------------------------------
#QUES 15
#------------------------------------


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

    df = pd.read_sql(query, conn)
    print(df)
    conn.close()
    st.markdown("### Ques 16")
    st.dataframe(df)

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
    st.markdown("### Ques 17")
    st.dataframe(summary)

#-----------------------------------
#QUES 18
#----------------------------------
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
    df = pd.read_sql(query, conn)
    conn.close()
    print(df)
    st.markdown("### Ques 18")
    st.dataframe(df)

#-------------------------------------
#QUES 19
#------------------------------------
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

    df = pd.read_sql(query, conn)
    print(df)
    conn.close()
    st.markdown("### Ques 19")
    st.dataframe(df)

#----------------------------------------
#QUES 20
#----------------------------------------
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
    df = pd.read_sql(query, conn)
    print(df)
    conn.close()
    st.markdown("### Ques 20")
    st.dataframe(df)

#------------------------------------
#QUES 21
#-----------------------------------
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

    df = pd.read_sql(query, conn)
    print(df)
    conn.close()
    st.markdown("### Ques 21")
    st.dataframe(df)

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
    st.markdown("### Ques 22")
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
    st.markdown("### Ques 23")
    st.dataframe(custom_top_players)

#----------------------------------------
#QUES 24
#----------------------------------------
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

# Only keep rows where both batsmen have runs
    partnerships = df.dropna(subset=['next_player','next_runs']).copy()

# Calculate partnership runs
    partnerships['partnership_runs'] = partnerships['runs'] + partnerships['next_runs']

# -----------------------------
# 5. Standardize player pair order
# -----------------------------
    partnerships['playerA'] = partnerships[['name','next_player']].min(axis=1)
    partnerships['playerB'] = partnerships[['name','next_player']].max(axis=1)

# -----------------------------
# 6. Calculate partnership stats
# -----------------------------
    grouped = partnerships.groupby(['playerA','playerB'])

    partnership_stats = grouped.agg(
        total_partnerships=('partnership_runs','count'),
        avg_partnership_runs=('partnership_runs','mean'),
        partnerships_over_50=('partnership_runs', lambda x: (x >= 50).sum()),
        highest_partnership=('partnership_runs','max')
    ).reset_index()

# Success rate: % of partnerships over 50
    partnership_stats['success_rate'] = (
        partnership_stats['partnerships_over_50'] / partnership_stats['total_partnerships'] * 100
    )

# -----------------------------
# 7. Debug: check top 20 before filtering
# -----------------------------
    print("Top 20 partnerships before filtering:")
    print(partnership_stats.sort_values('avg_partnership_runs', ascending=False).head(20))

# -----------------------------
# 8. Filter pairs with >=5 partnerships
# -----------------------------
    partnership_stats_filtered = partnership_stats[partnership_stats['total_partnerships'] >= 5]

# Display filtered results sorted by average partnership runs
    print("\nFiltered partnerships (>=5 partnerships):")
    print(partnership_stats_filtered.sort_values('avg_partnership_runs', ascending=False))

    st.markdown("### Ques 24")
    st.dataframe(partnership_stats_filtered.sort_values('avg_partnership_runs', ascending=False))

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
    st.markdown("### Ques 25")
    st.dataframe(final_df.head(20))












