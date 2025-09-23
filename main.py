from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
import json
from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from insights import PLAYER_INSIGHTS, TEAM_INSIGHTS, VENUE_INSIGHTS, OVERALL_BOWLING_AVERAGES
from config import settings
import uvicorn

# Global variables for data
batting_data = None
team_data = None
batter_vs_bowler_data = None
team_vs_bowler_data = None
venue_data = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global batting_data, team_data, batter_vs_bowler_data, team_vs_bowler_data, venue_data
    try:
        print(f"Loading data from: {Path(__file__).parent / 'data'}")
        data_dir = Path(__file__).parent / "data"
        print(f"Data directory exists: {data_dir.exists()}")
        
        if data_dir.exists():
            try:
                batting_data = pd.read_csv(data_dir / "IPL_21_24_Batting.csv")
                print("Loaded batting data successfully")
            except Exception as e:
                print(f"Error loading batting data: {e}")
            
            try:
                team_data = pd.read_csv(data_dir / "IPL_Team_BattingData_21_24.csv")
                print("Loaded team data successfully")
            except Exception as e:
                print(f"Error loading team data: {e}")
            
            try:
                batter_vs_bowler_data = pd.read_csv(data_dir / "Batters_StrikeRateVSBowlerType.csv")
                print("Loaded batter vs bowler data successfully")
            except Exception as e:
                print(f"Error loading batter vs bowler data: {e}")
            
            try:
                team_vs_bowler_data = pd.read_csv(data_dir / "Team_vs_BowlingType.csv")
                print("Loaded team vs bowler data successfully")
            except Exception as e:
                print(f"Error loading team vs bowler data: {e}")
            
            try:
                venue_data = pd.read_csv(data_dir / "IPL_Venue_details.csv")
                print("Loaded venue data successfully")
            except Exception as e:
                print(f"Error loading venue data: {e}")
        else:
            print("Data directory not found, using hardcoded data only")
    except Exception as e:
        print(f"Error during startup: {e}")
        print("Continuing with hardcoded data only")
    
    yield
    # Shutdown
    print("Application shutting down")

app = FastAPI(title="IPL Opposition Planning API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Team players mapping
TEAM_PLAYERS = {
    'Chennai Super Kings': [
        'Ruturaj Gaikwad', 'Devon Conway', 'Ravindra Jadeja', 
        'Mahendra Singh Dhoni', 'Shivam Dube', 'Moeen Ali', 'Deepak Chahar', 
        'Dwayne Bravo', 'Tushar Deshpande'
    ],
    'Mumbai Indians': [
        'Ishan Kishan', 'Rohit Sharma', 'Suryakumar Yadav', 'Tilak Varma', 'Tim David',
        'Hardik Pandya',  'Jasprit Bumrah', 
        'Rahul Chahar', 'Tymal Mills', 'Kieron Pollard'
    ],
    'Royal Challengers Bangalore': [
        'Virat Kohli', 'Faf du Plessis', 'Glenn Maxwell', 'Dinesh Karthik',
        'Rajat Patidar', 'AB de Villiers',  'Harshal Patel', 'Yash Dayal',
        'Mohammed Siraj', 'Josh Hazlewood', 'Akash Deep'
    ],
    'Kolkata Knight Riders': [
        'Venkatesh Iyer', 'Shreyas Iyer', 'Nitish Rana',
        'Andre Russell', 'Rinku Singh', 'Phil Salt', 'Sunil Narine', 
        'Pat Cummins', 'Varun Chakravarthy'
    ],
    'Delhi Capitals': [
        'David Warner', 'Prithvi Shaw', 'Rishabh Pant', 'Axar Patel',
        'Lalit Yadav', 'Rovman Powell', 'Shardul Thakur', 'Kuldeep Yadav',
        'Anrich Nortje', 'Mustafizur Rahman', 'Khaleel Ahmed'
    ],
    'Punjab Kings': [
        'Mayank Agarwal', 'Shikhar Dhawan', 'Liam Livingstone',
        'Jonny Bairstow', 'Shahrukh Khan', 'Sam Curran', 'Kagiso Rabada', 
        'Arshdeep Singh', 'Rahul Chahar'
    ],
    'Rajasthan Royals': [
        'Jos Buttler', 'Yashasvi Jaiswal', 'Sanju Samson', 'Shimron Hetmyer',
        'Riyan Parag', 'Devdutt Padikkal', 'Ravichandran Ashwin', 'Trent Boult',
        'Prasidh Krishna', 'Yuzvendra Chahal', 'Obed McCoy'
    ],
    'Sunrisers Hyderabad': [
        'Kane Williamson', 'Abhishek Sharma','Travis Head' 'Aiden Markram', 'Nicholas Pooran',
        'Abdul Samad',  'Washington Sundar', 'Bhuvneshwar Kumar', 
        'T Natarajan', 'Umran Malik', 'Marco Jansen'
    ],
    'Gujarat Titans': [
        'David Miller', 'Sai Sudharsan',
        'Rahul Tewatia', 'Wriddhiman Saha', 'Rashid Khan', 'Mohammed Shami', 
        'Lockie Ferguson', 'Alzarri Joseph'
    ],
    'Lucknow Super Giants': [
        'KL Rahul', 'Quinton de Kock', 'Marcus Stoinis', 'Deepak Hooda',
        'Ayush Badoni', 'Jason Holder', 'Avesh Khan',
        'Dushmantha Chameera', 'Ravi Bishnoi', 'Mohsin Khan'
    ]
}

# Sample venues
VENUES = [
    "M. A. Chidambaram Stadium, Chennai",
    "Wankhede Stadium, Mumbai",
    "M. Chinnaswamy Stadium, Bangalore",
    "Eden Gardens, Kolkata",
    "Arun Jaitley Stadium, Delhi",
    "Punjab Cricket Association IS Bindra Stadium, Mohali",
    "Sawai Mansingh Stadium, Jaipur",
    "Rajiv Gandhi International Stadium, Hyderabad",
    "Narendra Modi Stadium, Ahmedabad",
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow"
]

# Data directory path
DATA_DIR = Path(__file__).parent / "data"

@app.get("/")
async def root():
    return {"message": "IPL Opposition Planning API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/debug")
async def debug_info():
    """Debug endpoint to check deployment status"""
    return {
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "host": settings.HOST,
        "port": settings.PORT,
        "data_loaded": {
            "batting_data": batting_data is not None,
            "team_data": team_data is not None,
            "batter_vs_bowler_data": batter_vs_bowler_data is not None,
            "team_vs_bowler_data": team_vs_bowler_data is not None,
            "venue_data": venue_data is not None
        },
        "data_dir_exists": DATA_DIR.exists(),
        "python_version": sys.version
    }

@app.get("/config")
async def get_config():
    """Get API configuration"""
    return {
        "api_url": settings.api_url,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/teams")
async def get_teams():
    """Get all IPL teams"""
    return {"teams": list(TEAM_PLAYERS.keys())}

@app.get("/teams/{team_name}/players")
async def get_team_players(team_name: str):
    """Get players for a specific team"""
    if team_name not in TEAM_PLAYERS:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"team": team_name, "players": TEAM_PLAYERS[team_name]}

@app.get("/venues")
async def get_venues():
    """Get all venues"""
    return {"venues": VENUES}

@app.get("/player/{player_name}/insights")
async def get_player_insights(player_name: str):
    """Get insights for a specific player"""
    if player_name in PLAYER_INSIGHTS:
        return {
            "player": player_name,
            "insights": PLAYER_INSIGHTS[player_name]
        }
    else:
        # Generate default insights for players not in hardcoded data
        return {
            "player": player_name,
            "insights": {
                "ai_insights": [
                    f"{player_name} shows consistent performance across different match situations",
                    "Demonstrates good adaptability to various bowling attacks",
                    "Maintains steady scoring rate throughout innings"
                ],
                "strengths": [
                    "Solid technique against both pace and spin bowling",
                    "Good strike rotation ability"
                ],
                "areas_for_improvement": [
                    "Can improve boundary hitting percentage",
                    "Needs to work on powerplay acceleration"
                ]
            }
        }

@app.get("/team/{team_name}/insights")
async def get_team_insights(team_name: str):
    """Get insights for a specific team"""
    if team_name in TEAM_INSIGHTS:
        return {
            "team": team_name,
            "insights": TEAM_INSIGHTS[team_name]
        }
    else:
        raise HTTPException(status_code=404, detail="Team insights not found")

@app.get("/venue/{venue_name}/insights")
async def get_venue_insights(venue_name: str):
    """Get insights for a specific venue"""
    if venue_name in VENUE_INSIGHTS:
        return {
            "venue": venue_name,
            "insights": VENUE_INSIGHTS[venue_name]
        }
    else:
        # Generate default venue insights
        return {
            "venue": venue_name,
            "insights": {
                "insights": [
                    f"{venue_name} provides balanced conditions for batting",
                    "Good scoring opportunities in all phases of the game",
                    "Suitable for both pace and spin bowling",
                    "Average scoring rate supports competitive matches",
                    "Boundary hitting opportunities available throughout innings"
                ]
            }
        }

@app.get("/scatter-plot-data")
async def get_scatter_plot_data(selected_players: str = ""):
    """Get scatter plot data for players"""
    if batting_data is None:
        # Return hardcoded data if CSV not loaded
        key_players_data = [
            {'name': 'Shubman Gill', 'first_innings_avg': 45.2, 'second_innings_avg': 38.5, 'first_innings_sr': 142.8, 'second_innings_sr': 135.2},
            {'name': 'Faf du Plessis', 'first_innings_avg': 42.1, 'second_innings_avg': 35.8, 'first_innings_sr': 138.5, 'second_innings_sr': 132.1},
            {'name': 'Ruturaj Gaikwad', 'first_innings_avg': 41.8, 'second_innings_avg': 34.2, 'first_innings_sr': 136.9, 'second_innings_sr': 129.8},
            {'name': 'Virat Kohli', 'first_innings_avg': 48.5, 'second_innings_avg': 42.1, 'first_innings_sr': 140.2, 'second_innings_sr': 134.8},
            {'name': 'KL Rahul', 'first_innings_avg': 44.3, 'second_innings_avg': 39.7, 'first_innings_sr': 139.1, 'second_innings_sr': 133.5},
            {'name': 'Jos Buttler', 'first_innings_avg': 41.5, 'second_innings_avg': 36.8, 'first_innings_sr': 143.6, 'second_innings_sr': 138.2},
            {'name': 'Sanju Samson', 'first_innings_avg': 38.9, 'second_innings_avg': 33.5, 'first_innings_sr': 141.2, 'second_innings_sr': 135.8},
            {'name': 'Shikhar Dhawan', 'first_innings_avg': 39.8, 'second_innings_avg': 35.2, 'first_innings_sr': 134.5, 'second_innings_sr': 128.9},
            {'name': 'Suryakumar Yadav', 'first_innings_avg': 40.2, 'second_innings_avg': 36.1, 'first_innings_sr': 145.8, 'second_innings_sr': 140.2},
            {'name': 'Yashasvi Jaiswal', 'first_innings_avg': 43.1, 'second_innings_avg': 37.8, 'first_innings_sr': 138.9, 'second_innings_sr': 132.5},
            {'name': 'Ishan Kishan', 'first_innings_avg': 37.5, 'second_innings_avg': 32.8, 'first_innings_sr': 142.1, 'second_innings_sr': 136.8},
            {'name': 'Rohit Sharma', 'first_innings_avg': 46.2, 'second_innings_avg': 40.5, 'first_innings_sr': 137.8, 'second_innings_sr': 131.2},
            {'name': 'Shivam Dube', 'first_innings_avg': 35.8, 'second_innings_avg': 31.2, 'first_innings_sr': 144.5, 'second_innings_sr': 138.9},
            {'name': 'Venkatesh Iyer', 'first_innings_avg': 36.9, 'second_innings_avg': 32.1, 'first_innings_sr': 139.8, 'second_innings_sr': 133.5},
            {'name': 'David Warner', 'first_innings_avg': 44.8, 'second_innings_avg': 39.2, 'first_innings_sr': 141.5, 'second_innings_sr': 135.8}
        ]
        
        # Add selected players if not in the list
        selected_player_list = selected_players.split(',') if selected_players else []
        for player in selected_player_list:
            player = player.strip()
            if player and not any(p['name'] == player for p in key_players_data):
                # Add default data for selected players not in the key list
                key_players_data.append({
                    'name': player,
                    'first_innings_avg': 35.0 + (len(player) % 10),  # Some variation based on name
                    'second_innings_avg': 30.0 + (len(player) % 8),
                    'first_innings_sr': 135.0 + (len(player) % 15),
                    'second_innings_sr': 130.0 + (len(player) % 12)
                })
        
        return {"scatter_data": key_players_data}
    
    # Define the 15 key players for scatter plot
    key_players = [
        'Shubman Gill', 'Faf du Plessis', 'Ruturaj Gaikwad', 'Virat Kohli',
        'KL Rahul', 'Jos Buttler', 'Sanju Samson', 'Shikhar Dhawan',
        'Suryakumar Yadav', 'Yashasvi Jaiswal', 'Ishan Kishan', 'Rohit Sharma',
        'Shivam Dube', 'Venkatesh Iyer', 'David Warner'
    ]
    
    # Parse selected players
    selected_player_list = selected_players.split(',') if selected_players else []
    selected_player_list = [p.strip() for p in selected_player_list if p.strip()]
    
    # Combine key players with selected players
    all_players_to_show = list(set(key_players + selected_player_list))
    
    scatter_data = []
    for _, row in batting_data.iterrows():
        if row['Batter_Name'] in all_players_to_show:
            # Convert strike rate strings to float values
            first_sr = row['strike_rate_1st_innings']
            second_sr = row['strike_rate_2nd_innings']
            
            # Remove % symbol and convert to float
            if isinstance(first_sr, str) and first_sr.endswith('%'):
                first_sr = float(first_sr.replace('%', ''))
            if isinstance(second_sr, str) and second_sr.endswith('%'):
                second_sr = float(second_sr.replace('%', ''))
                
            scatter_data.append({
                'name': row['Batter_Name'],
                'first_innings_avg': float(row['batting_average_1st_innings']) if row['batting_average_1st_innings'] else 0,
                'second_innings_avg': float(row['batting_average_2nd_innings']) if row['batting_average_2nd_innings'] else 0,
                'first_innings_sr': float(first_sr) if first_sr else 0,
                'second_innings_sr': float(second_sr) if second_sr else 0,
                'isSelected': row['Batter_Name'] in selected_player_list
            })
    
    # Add any selected players not found in the data with default values
    found_players = [p['name'] for p in scatter_data]
    for player in selected_player_list:
        if player not in found_players:
            scatter_data.append({
                'name': player,
                'first_innings_avg': 35.0 + (len(player) % 10),
                'second_innings_avg': 30.0 + (len(player) % 8),
                'first_innings_sr': 135.0 + (len(player) % 15),
                'second_innings_sr': 130.0 + (len(player) % 12),
                'isSelected': True
            })
    
    return {"scatter_data": scatter_data}

@app.get("/team-scatter-plot-data")
async def get_team_scatter_plot_data():
    """Get scatter plot data for teams"""
    # Hardcoded team data for scatter plot
    team_scatter_data = [
        {"name": "Chennai Super Kings", "first_innings_avg": 173.59, "second_innings_avg": 152.45, "first_innings_sr": 144.27, "second_innings_sr": 134.38},
        {"name": "Mumbai Indians", "first_innings_avg": 170.25, "second_innings_avg": 151.25, "first_innings_sr": 140.05, "second_innings_sr": 138.75},
        {"name": "Royal Challengers Bangalore", "first_innings_avg": 175.85, "second_innings_avg": 146.75, "first_innings_sr": 142.15, "second_innings_sr": 135.25},
        {"name": "Kolkata Knight Riders", "first_innings_avg": 169.44, "second_innings_avg": 149.25, "first_innings_sr": 141.33, "second_innings_sr": 134.38},
        {"name": "Delhi Capitals", "first_innings_avg": 166.58, "second_innings_avg": 151.18, "first_innings_sr": 137.81, "second_innings_sr": 135.23},
        {"name": "Punjab Kings", "first_innings_avg": 168.25, "second_innings_avg": 148.50, "first_innings_sr": 136.75, "second_innings_sr": 134.25},
        {"name": "Rajasthan Royals", "first_innings_avg": 165.25, "second_innings_avg": 159.75, "first_innings_sr": 139.85, "second_innings_sr": 137.25},
        {"name": "Sunrisers Hyderabad", "first_innings_avg": 167.50, "second_innings_avg": 154.25, "first_innings_sr": 139.25, "second_innings_sr": 136.75},
        {"name": "Gujarat Titans", "first_innings_avg": 164.75, "second_innings_avg": 157.75, "first_innings_sr": 138.50, "second_innings_sr": 135.60},
        {"name": "Lucknow Super Giants", "first_innings_avg": 170.17, "second_innings_avg": 150.81, "first_innings_sr": 135.25, "second_innings_sr": 133.75}
    ]
    
    return {"team_scatter_data": team_scatter_data}

@app.get("/player/{player_name}/bowling-stats")
async def get_player_bowling_stats(player_name: str):
    """Get player stats against different bowling types"""
    if batter_vs_bowler_data is None:
        # Return default stats if data not loaded
        return {
            "player": player_name,
            "bowling_stats": {
                "Left arm pace": 130.0,
                "Right arm pace": 125.0,
                "Off spin": 115.0,
                "Leg spin": 120.0,
                "Slow left arm orthodox": 110.0,
                "Left arm wrist spin": 118.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("batter", {
                "Left arm pace": 128.5,
                "Right arm pace": 127.2,
                "Off spin": 118.3,
                "Leg spin": 122.1,
                "Slow left arm orthodox": 112.8,
                "Left arm wrist spin": 120.4
            })
        }
    
    player_stats = batter_vs_bowler_data[batter_vs_bowler_data['Batter_Name'] == player_name]
    
    if player_stats.empty:
        # Return default stats if player not found
        return {
            "player": player_name,
            "bowling_stats": {
                "Left arm pace": 130.0,
                "Right arm pace": 125.0,
                "Off spin": 115.0,
                "Leg spin": 120.0,
                "Slow left arm orthodox": 110.0,
                "Left arm wrist spin": 118.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("batter", {
                "Left arm pace": 128.5,
                "Right arm pace": 127.2,
                "Off spin": 118.3,
                "Leg spin": 122.1,
                "Slow left arm orthodox": 112.8,
                "Left arm wrist spin": 120.4
            })
        }
    
    bowling_stats = {}
    for _, row in player_stats.iterrows():
        bowling_stats[row['bowler.type']] = row['StrikeRate']
    
    return {
        "player": player_name,
        "bowling_stats": bowling_stats,
        "overall_averages": OVERALL_BOWLING_AVERAGES.get("batter", {
            "Left arm pace": 128.5,
            "Right arm pace": 127.2,
            "Off spin": 118.3,
            "Leg spin": 122.1,
            "Slow left arm orthodox": 112.8,
            "Left arm wrist spin": 120.4
        })
    }

@app.get("/team/{team_name}/bowling-stats")
async def get_team_bowling_stats(team_name: str):
    """Get team stats against different bowling types"""
    if team_vs_bowler_data is None:
        # Return default stats if data not loaded
        return {
            "team": team_name,
            "bowling_stats": {
                "Left arm pace": 135.0,
                "Right arm pace": 132.0,
                "Off spin": 125.0,
                "Leg spin": 128.0,
                "Slow left arm orthodox": 120.0,
                "Left arm wrist spin": 126.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("team", {
                "Left arm pace": 133.2,
                "Right arm pace": 130.8,
                "Off spin": 123.5,
                "Leg spin": 126.7,
                "Slow left arm orthodox": 118.9,
                "Left arm wrist spin": 124.3
            })
        }
    
    team_stats = team_vs_bowler_data[team_vs_bowler_data['batting_team'] == team_name]
    
    if team_stats.empty:
        # Return default stats if team not found
        return {
            "team": team_name,
            "bowling_stats": {
                "Left arm pace": 135.0,
                "Right arm pace": 132.0,
                "Off spin": 125.0,
                "Leg spin": 128.0,
                "Slow left arm orthodox": 120.0,
                "Left arm wrist spin": 126.0
            },
            "overall_averages": OVERALL_BOWLING_AVERAGES.get("team", {
                "Left arm pace": 133.2,
                "Right arm pace": 130.8,
                "Off spin": 123.5,
                "Leg spin": 126.7,
                "Slow left arm orthodox": 118.9,
                "Left arm wrist spin": 124.3
            })
        }
    
    bowling_stats = {}
    for _, row in team_stats.iterrows():
        bowling_stats[row['bowling_type']] = row['strike_rate']
    
    return {
        "team": team_name,
        "bowling_stats": bowling_stats,
        "overall_averages": OVERALL_BOWLING_AVERAGES.get("team", {
            "Left arm pace": 133.2,
            "Right arm pace": 130.8,
            "Off spin": 123.5,
            "Leg spin": 126.7,
            "Slow left arm orthodox": 118.9,
            "Left arm wrist spin": 124.3
        })
    }

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
