from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
import os
import sys
import sqlite3
import json
import datetime
import pandas as pd
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Add the src directory to the path so we can import bot modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

app = Flask(__name__)


def get_league_db():
    """Connect to the league database"""
    # Get the environment variables for database paths
    data_dir = os.environ.get("DATA_DIR", "../data/")
    db_name = os.environ.get("LEAGUE_DB_NAME", "league")

    # Try multiple possible paths to find the database
    possible_paths = [
        os.path.join(data_dir, f"{db_name}.sqlite"),  # Using DATA_DIR env var
        os.path.join("../data/", f"{db_name}.sqlite"),  # Relative to web directory
        os.path.join(
            os.path.dirname(__file__), "..", "data", f"{db_name}.sqlite"
        ),  # Absolute path
        os.path.abspath(os.path.join("data", f"{db_name}.sqlite")),  # Absolute from cwd
    ]

    for path in possible_paths:
        try:
            print(f"Trying to connect to database at: {path}")
            if os.path.exists(os.path.dirname(path)):
                return sqlite3.connect(path)
        except Exception as e:
            print(f"Failed to connect to {path}: {e}")
            continue

    # If all attempts fail, try one last attempt with a direct path
    return sqlite3.connect(
        os.path.join(os.path.dirname(__file__), "..", "data", f"{db_name}.sqlite")
    )


def get_config_db():
    """Connect to the config database"""
    # Get the environment variables for database paths
    data_dir = os.environ.get("DATA_DIR", "../data/")
    db_name = os.environ.get("CONFIG_DB_NAME", "config")

    # Try multiple possible paths to find the database
    possible_paths = [
        os.path.join(data_dir, f"{db_name}.sqlite"),  # Using DATA_DIR env var
        os.path.join("../data/", f"{db_name}.sqlite"),  # Relative to web directory
        os.path.join(
            os.path.dirname(__file__), "..", "data", f"{db_name}.sqlite"
        ),  # Absolute path
        os.path.abspath(os.path.join("data", f"{db_name}.sqlite")),  # Absolute from cwd
    ]

    for path in possible_paths:
        try:
            print(f"Trying to connect to config database at: {path}")
            if os.path.exists(os.path.dirname(path)):
                return sqlite3.connect(path)
        except Exception as e:
            print(f"Failed to connect to {path}: {e}")
            continue

    # If all attempts fail, try one last attempt with a direct path
    return sqlite3.connect(
        os.path.join(os.path.dirname(__file__), "..", "data", f"{db_name}.sqlite")
    )


def dict_factory(cursor, row):
    """Convert SQL row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@app.route("/")
def index():
    """Main page with links to different views and summary stats"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Get basic stats for the dashboard
        total_players = cursor.execute("SELECT COUNT(*) as count FROM player").fetchone()["count"]
        total_matches = cursor.execute("SELECT COUNT(*) as count FROM match").fetchone()["count"]
        avg_mmr = cursor.execute("SELECT AVG(mmr) as avg FROM player").fetchone()["avg"]
        
        conn.close()
        return render_template(
            "index.html", 
            total_players=total_players,
            total_matches=total_matches,
            avg_mmr=round(avg_mmr) if avg_mmr else 0
        )
    except Exception as e:
        # If we can't get stats, just render the page without them
        print(f"Error fetching dashboard stats: {str(e)}")
        return render_template("index.html")


@app.route("/players")
def players():
    """Display all players and their stats"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        players = cursor.execute("SELECT * FROM player ORDER BY mmr DESC").fetchall()

        # Calculate win rate for each player
        for player in players:
            total_games = player["wins"] + player["losses"]
            player["win_rate"] = round(
                (player["wins"] / total_games * 100) if total_games > 0 else 0, 1
            )

        conn.close()
        return render_template("players.html", players=players)
    except Exception as e:
        error_message = f"Error connecting to the database: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.route("/player/<int:player_id>")
def player_detail(player_id):
    """Display detailed information about a specific player"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        player = cursor.execute(
            "SELECT * FROM player WHERE discord_id = ?", (player_id,)
        ).fetchone()

        if not player:
            conn.close()
            abort(404)

        # Get MMR history
        mmr_history = cursor.execute(
            "SELECT mmr, timestamp FROM mmr_history WHERE discord_id = ? ORDER BY timestamp",
            (player_id,),
        ).fetchall()

        # Get match history
        matches = []
        all_matches = cursor.execute(
            "SELECT * FROM match ORDER BY timestamp DESC"
        ).fetchall()

        # Get all players at once for better performance
        all_players = cursor.execute("SELECT * FROM player").fetchall()
        player_map = {str(p["discord_id"]): p for p in all_players}

        for match in all_matches:
            team1_ids = [tid.strip() for tid in match["team1"].split() if tid.strip()]
            team2_ids = [tid.strip() for tid in match["team2"].split() if tid.strip()]

            if str(player_id) in team1_ids or str(player_id) in team2_ids:
                # Map player IDs to player data with fallbacks
                team1_players_names = []
                for tid in team1_ids:
                    if str(tid) in player_map:
                        team1_players_names.append(player_map[str(tid)]["discord_name"])
                    else:
                        team1_players_names.append(f"Unknown ({tid})")

                team2_players_names = []
                for tid in team2_ids:
                    if str(tid) in player_map:
                        team2_players_names.append(player_map[str(tid)]["discord_name"])
                    else:
                        team2_players_names.append(f"Unknown ({tid})")

                match["team1_players"] = team1_players_names
                match["team2_players"] = team2_players_names
                match["player_team"] = 1 if str(player_id) in team1_ids else 2
                match["player_won"] = match["winner"] == match["player_team"]

                matches.append(match)

        # Generate MMR graph data
        mmr_data = None
        mmr_by_game_data = None

        if mmr_history:
            # Graph by date (original)
            df = pd.DataFrame(mmr_history)
            fig = px.line(
                df,
                x="timestamp",
                y="mmr",
                title=f"MMR History for {player['discord_name']} (By Date)",
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="MMR")
            mmr_data = json.dumps(fig, cls=PlotlyJSONEncoder)

            # Graph by game number
            df_by_game = pd.DataFrame(mmr_history).reset_index()
            df_by_game = df_by_game.rename(columns={"index": "game_number"})
            df_by_game["game_number"] = (
                df_by_game["game_number"] + 1
            )  # Start from 1 instead of 0

            fig_by_game = px.line(
                df_by_game,
                x="game_number",
                y="mmr",
                title=f"MMR History for {player['discord_name']} (By Game)",
            )
            fig_by_game.update_layout(xaxis_title="Game Number", yaxis_title="MMR")
            mmr_by_game_data = json.dumps(fig_by_game, cls=PlotlyJSONEncoder)

        conn.close()

        # Calculate win rate
        total_games = player["wins"] + player["losses"]
        win_rate = round(
            (player["wins"] / total_games * 100) if total_games > 0 else 0, 1
        )

        # Get current view type from query param, default to date view
        view_type = request.args.get("view", "date")

        return render_template(
            "player_detail.html",
            player=player,
            matches=matches,
            win_rate=win_rate,
            mmr_data=mmr_data,
            mmr_by_game_data=mmr_by_game_data,
            view_type=view_type,
        )
    except Exception as e:
        error_message = f"Error retrieving player details: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.route("/matches")
def matches():
    """Display all matches"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        page = request.args.get("page", 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        matches = cursor.execute(
            "SELECT * FROM match ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        ).fetchall()

        total_matches = cursor.execute(
            "SELECT COUNT(*) as count FROM match"
        ).fetchone()["count"]
        total_pages = (total_matches + per_page - 1) // per_page

        # Get all players at once for better performance
        all_players = cursor.execute("SELECT * FROM player").fetchall()
        player_map = {str(p["discord_id"]): p for p in all_players}

        # Process each match to get player names
        for match in matches:
            # Better handling of team IDs - strip whitespace and filter empty strings
            team1_ids = [tid.strip() for tid in match["team1"].split() if tid.strip()]
            team2_ids = [tid.strip() for tid in match["team2"].split() if tid.strip()]

            # Map player IDs to player data with fallbacks
            team1_players_names = []
            for player_id in team1_ids:
                if str(player_id) in player_map:
                    team1_players_names.append(
                        player_map[str(player_id)]["discord_name"]
                    )
                else:
                    team1_players_names.append(f"Unknown ({player_id})")

            team2_players_names = []
            for player_id in team2_ids:
                if str(player_id) in player_map:
                    team2_players_names.append(
                        player_map[str(player_id)]["discord_name"]
                    )
                else:
                    team2_players_names.append(f"Unknown ({player_id})")

            match["team1_players"] = team1_players_names
            match["team2_players"] = team2_players_names

            # Format timestamp
            if match["timestamp"]:
                try:
                    match["formatted_date"] = datetime.datetime.fromisoformat(
                        match["timestamp"]
                    ).strftime("%Y-%m-%d %H:%M")
                except:
                    match["formatted_date"] = match["timestamp"]

        conn.close()

        return render_template(
            "matches.html", matches=matches, page=page, total_pages=total_pages
        )
    except Exception as e:
        error_message = f"Error retrieving matches: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.route("/match/<int:match_id>")
def match_detail(match_id):
    """Display detailed information about a specific match"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        match = cursor.execute(
            "SELECT * FROM match WHERE match_id = ?", (match_id,)
        ).fetchone()
        if not match:
            conn.close()
            abort(404)

        # Debug the team IDs from the match
        print(f"Team1 IDs: {match['team1']}")
        print(f"Team2 IDs: {match['team2']}")

        # Direct query to get all players - we'll filter afterward
        all_players = cursor.execute("SELECT * FROM player").fetchall()
        player_map = {str(p["discord_id"]): p for p in all_players}

        # Get team IDs - handle potential whitespace and empty strings
        team1_ids = [tid.strip() for tid in match["team1"].split() if tid.strip()]
        team2_ids = [tid.strip() for tid in match["team2"].split() if tid.strip()]

        # Map player IDs to player data
        team1_players = []
        for player_id in team1_ids:
            if str(player_id) in player_map:
                team1_players.append(player_map[str(player_id)])
            else:
                # Fallback for missing players
                team1_players.append(
                    {
                        "discord_id": player_id,
                        "discord_name": f"Unknown Player ({player_id})",
                        "mmr": 0,
                    }
                )

        team2_players = []
        for player_id in team2_ids:
            if str(player_id) in player_map:
                team2_players.append(player_map[str(player_id)])
            else:
                # Fallback for missing players
                team2_players.append(
                    {
                        "discord_id": player_id,
                        "discord_name": f"Unknown Player ({player_id})",
                        "mmr": 0,
                    }
                )

        # Calculate team MMR totals
        team1_mmr = sum(p.get("mmr", 0) for p in team1_players)
        team2_mmr = sum(p.get("mmr", 0) for p in team2_players)

        # Additional debug information
        print(
            f"Team 1 Players: {[p.get('discord_name', 'unknown') for p in team1_players]}"
        )
        print(
            f"Team 2 Players: {[p.get('discord_name', 'unknown') for p in team2_players]}"
        )

        conn.close()

        return render_template(
            "match_detail.html",
            match=match,
            team1_players=team1_players,
            team2_players=team2_players,
            team1_mmr=team1_mmr,
            team2_mmr=team2_mmr,
        )
    except Exception as e:
        error_message = f"Error retrieving match details: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.route("/config")
def config():
    """Display configuration settings"""
    try:
        conn = get_config_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Get tables from sqlite_master
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        config_data = {}
        for table in tables:
            table_name = table["name"]
            config_data[table_name] = cursor.execute(
                f"SELECT * FROM {table_name}"
            ).fetchall()
        conn.close()
        return render_template("config.html", config_data=config_data)
    except Exception as e:
        error_message = f"Error retrieving configuration: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.route("/stats")
def stats():
    """Display general statistics about the bot usage"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Total players
        total_players = cursor.execute(
            "SELECT COUNT(*) as count FROM player"
        ).fetchone()["count"]

        # Total matches
        total_matches = cursor.execute(
            "SELECT COUNT(*) as count FROM match"
        ).fetchone()["count"]

        # Average MMR
        avg_mmr = cursor.execute("SELECT AVG(mmr) as avg FROM player").fetchone()["avg"]

        # Latest matches
        latest_matches = cursor.execute(
            "SELECT * FROM match ORDER BY timestamp DESC LIMIT 5"
        ).fetchall()

        # MMR distribution
        mmr_data = cursor.execute("SELECT mmr FROM player").fetchall()

        # Monthly matches
        monthly_data = cursor.execute(
            """
            SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) as count 
            FROM match 
            GROUP BY month 
            ORDER BY month
        """
        ).fetchall()

        # Create MMR distribution chart
        mmr_values = [p["mmr"] for p in mmr_data]
        if mmr_values:
            df = pd.DataFrame({"mmr": mmr_values})
            fig = px.histogram(df, x="mmr", nbins=20, title="MMR Distribution")
            mmr_chart = json.dumps(fig, cls=PlotlyJSONEncoder)
        else:
            mmr_chart = None

        # Create monthly matches chart
        if monthly_data:
            df = pd.DataFrame(monthly_data)
            fig = px.bar(df, x="month", y="count", title="Matches per Month")
            monthly_chart = json.dumps(fig, cls=PlotlyJSONEncoder)
        else:
            monthly_chart = None

        conn.close()

        return render_template(
            "stats.html",
            total_players=total_players,
            total_matches=total_matches,
            avg_mmr=round(avg_mmr) if avg_mmr else 0,
            latest_matches=latest_matches,
            mmr_chart=mmr_chart,
            monthly_chart=monthly_chart,
        )
    except Exception as e:
        error_message = f"Error retrieving statistics: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.route("/fake-data")
def fake_data():
    """Display fake data from the database"""
    try:
        conn = get_league_db()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Fetch fake players from the database
        fake_players = cursor.execute("SELECT * FROM fake_player").fetchall()

        # Fetch fake matches from the database
        fake_matches = cursor.execute(
            "SELECT match_id, team1, team2, winner, mmr_diff, timestamp FROM fake_match"
        ).fetchall()

        conn.close()
        return render_template(
            "fake_data.html", fake_players=fake_players, fake_matches=fake_matches
        )
    except Exception as e:
        error_message = f"Error retrieving fake data: {str(e)}"
        print(error_message)
        return render_template("error.html", error_message=error_message)


@app.template_filter("datetime")
def format_datetime(value, format="%Y-%m-%d %H:%M"):
    """Format a datetime string"""
    if not value:
        return ""
    try:
        return datetime.datetime.fromisoformat(value).strftime(format)
    except:
        return value


@app.template_filter("mmr_tier")
def mmr_tier_filter(mmr):
    """Return CSS tier class based on MMR value"""
    if mmr < 700:
        return "🔧 Iron"
    elif mmr < 900:
        return "🥉 Bronze"
    elif mmr < 1300:
        return "🥈 Silver"
    elif mmr < 1700:
        return "🥇 Gold"
    elif mmr < 2100:
        return "💎 Platinum"
    elif mmr < 2500:
        return "💠 Diamond"
    elif mmr < 2900:
        return "👑 Master"
    else:
        return "⚜️ Grandmaster"


@app.template_filter("mmr_tier_name")
def mmr_tier_name_filter(mmr):
    """Return tier name with emoji based on MMR value"""
    if mmr < 700:
        return "🔧 Iron"
    elif mmr < 900:
        return "🥉 Bronze"
    elif mmr < 1300:
        return "🥈 Silver"
    elif mmr < 1700:
        return "🥇 Gold"
    elif mmr < 2100:
        return "💎 Platinum"
    elif mmr < 2500:
        return "💠 Diamond"
    elif mmr < 2900:
        return "👑 Master"
    else:
        return "⚜️ Grandmaster"


@app.cli.command("init-db-dirs")
def init_db_dirs():
    """Create necessary directories for database files if they don't exist"""
    data_dir = os.environ.get("DATA_DIR", "data/")
    # Try multiple possible paths
    paths = [
        data_dir,
        "../data/",
        os.path.join(os.path.dirname(__file__), "..", "data"),
        os.path.abspath("data"),
    ]

    for path in paths:
        try:
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"Created directory: {path}")
            else:
                print(f"Directory already exists: {path}")
        except Exception as e:
            print(f"Failed to create directory {path}: {e}")


def create_app():
    """Factory function to create and configure the app"""
    # Create the data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")

    return app


if __name__ == "__main__":
    create_app().run(debug=True, host="0.0.0.0", port=5000)
