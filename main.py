from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from insights import PLAYER_INSIGHTS, TEAM_INSIGHTS, VENUE_INSIGHTS, OVERALL_BOWLING_AVERAGES
import uvicorn

app = FastAPI(title="IPL Opposition Planning API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
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
        'Ishan Kishan', 'Suryakumar Yadav', 'Tilak Varma', 'Tim David',
        'Hardik Pandya', 'Rohit Sharma', 'Jasprit Bumrah', 
        'Rahul Chahar', 'Tymal Mills', 'Kieron Pollard'
    ],
    'Royal Challengers Bangalore': [
        'Virat Kohli', 'Faf du Plessis', 'Glenn Maxwell', 'Dinesh Karthik',
        'Rajat Patidar', 'AB de Villiers', 'Wanindu Hasaranga', 'Harshal Patel', 
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
        'Kane Williamson', 'Aiden Markram', 'Nicholas Pooran',
        'Abdul Samad', 'Abhishek Sharma', 'Washington Sundar', 'Bhuvneshwar Kumar', 
        'T Natarajan', 'Umran Malik', 'Marco Jansen', 'Travis Head'
    ],
    'Gujarat Titans': [
        'David Miller', 'Sai Sudharsan',
        'Rahul Tewatia', 'Wriddhiman Saha', 'Rashid Khan', 'Mohammed Shami', 
        'Lockie Ferguson', 'Alzarri Joseph', 'Yash Dayal'
    ],
    'Lucknow Super Giants': [
        'KL Rahul', 'Quinton de Kock', 'Marcus Stoinis', 'Deepak Hooda',
        'Ayush Badoni', 'Krunal Pandya', 'Jason Holder', 'Avesh Khan',
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

# Load data on startup
batting_data = None
team_data = None
batter_vs_bowler_data = None
team_vs_bowler_data = None
venue_data = None

@app.on_event("startup")
async def load_data():
    global batting_data, team_data, batter_vs_bowler_data, team_vs_bowler_data, venue_data
    try:
        batting_data = pd.read_csv(DATA_DIR / "IPL_21_24_Batting.csv")
        team_data = pd.read_csv(DATA_DIR / "IPL_Team_BattingData_21_24.csv")
        batter_vs_bowler_data = pd.read_csv(DATA_DIR / "Batters_StrikeRateVSBowlerType.csv")
        team_vs_bowler_data = pd.read_csv(DATA_DIR / "Team_vs_BowlingType.csv")
        venue_data = pd.read_csv(DATA_DIR / "IPL_Venue_details.csv")
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {e}")

@app.get("/")
async def root():
    return {"message": "IPL Opposition Planning API is running!"}

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
async def get_scatter_plot_data():
    """Get scatter plot data for players"""
    if batting_data is None:
        raise HTTPException(status_code=500, detail="Batting data not loaded")
    
    # Define the 15 key players for scatter plot
    key_players = [
        'Shubman Gill', 'Faf du Plessis', 'Ruturaj Gaikwad', 'Virat Kohli',
        'KL Rahul', 'Jos Buttler', 'Sanju Samson', 'Shikhar Dhawan',
        'Suryakumar Yadav', 'Yashasvi Jaiswal', 'Ishan Kishan', 'Rohit Sharma',
        'Shivam Dube', 'Venkatesh Iyer', 'David Warner'
    ]
    
    scatter_data = []
    for _, row in batting_data.iterrows():
        if row['Batter_Name'] in key_players:
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
                'second_innings_sr': float(second_sr) if second_sr else 0
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
