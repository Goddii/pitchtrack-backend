"""
Seed the database with sample data matching the frontend mock data.

Usage:
    cd pitchtrack-backend
    PYTHONPATH=. pipenv run python seed.py

This will:
  - Create an admin user (admin@pitchtrack.com / admin123)
  - Create a regular user (user@example.com / password123)
  - Create 8 teams, 18 players, and 14 matches
"""

from datetime import datetime
from run import app
from extensions import db
from models import User, Team, Player, Match, Favorite

ADMIN_EMAIL = "admin@pitchtrack.com"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "user@example.com"
USER_PASSWORD = "password123"

TEAMS_DATA = [
    {"name": "Riverside FC",     "city": "Millbrook",   "founded_year": 1998, "coach": "Daniel Otieno"},
    {"name": "Kestrel City",     "city": "Dunmore",     "founded_year": 2004, "coach": "Grace Wanjiru"},
    {"name": "Iron Bridge SC",   "city": "Halden",      "founded_year": 1987, "coach": "Peter Kamau"},
    {"name": "Vale United",      "city": "Ashcombe",    "founded_year": 2011, "coach": None},
    {"name": "Coastal Rovers",   "city": "Seaford",     "founded_year": 2000, "coach": "Susan Achieng"},
    {"name": "Ashfield Town",    "city": "Ashfield",    "founded_year": 1993, "coach": None},
    {"name": "Oakfield",         "city": "Oak Valley",  "founded_year": 2015, "coach": "Michael Ouma"},
    {"name": "Priory Rangers",   "city": "Priory",      "founded_year": 1990, "coach": None},
]

PLAYERS_DATA = [
    # Riverside FC (team_id = 1 after insert)
    {"name": "James Mwangi",     "position": "Forward",    "jersey_number": 9,  "nationality": "Kenya",    "age": 24, "team_idx": 0,
     "bio": "A product of the Millbrook youth academy, James leads the line with pace and a clinical first touch inside the box.",
     "attributes": {"pace": 86, "shooting": 84, "passing": 63, "dribbling": 80, "defending": 32, "physical": 71}},
    {"name": "Brian Kiptoo",     "position": "Midfielder",  "jersey_number": 8,  "nationality": "Kenya",    "age": 27, "team_idx": 0,
     "bio": "Riverside's engine room, Brian dictates tempo from a deep-lying playmaker role.",
     "attributes": {"pace": 70, "shooting": 62, "passing": 85, "dribbling": 78, "defending": 60, "physical": 68}},
    {"name": "Felix Otieno",     "position": "Defender",    "jersey_number": 4,  "nationality": "Kenya",    "age": 29, "team_idx": 0,
     "bio": "A commanding centre-back and the club's longest-serving player, now into his sixth season.",
     "attributes": {"pace": 66, "shooting": 35, "passing": 68, "dribbling": 55, "defending": 87, "physical": 82}},
    {"name": "Samuel Njoroge",   "position": "Goalkeeper",  "jersey_number": 1,  "nationality": "Kenya",    "age": 25, "team_idx": 0,
     "bio": "Samuel's shot-stopping kept Riverside in three matches they had no business winning last season.",
     "attributes": {"diving": 82, "handling": 79, "kicking": 68, "reflexes": 85, "speed": 55, "positioning": 80}},

    # Kestrel City (team_idx = 1)
    {"name": "Collins Wafula",   "position": "Forward",    "jersey_number": 11, "nationality": "Kenya",    "age": 22, "team_idx": 1,
     "bio": "The league's fastest outlet ball, Collins thrives running in behind static back lines.",
     "attributes": {"pace": 88, "shooting": 80, "passing": 58, "dribbling": 84, "defending": 28, "physical": 65}},
    {"name": "Eric Mutiso",      "position": "Midfielder",  "jersey_number": 6,  "nationality": "Kenya",    "age": 26, "team_idx": 1,
     "bio": "A tireless box-to-box presence who covers every blade of grass at Dunmore.",
     "attributes": {"pace": 68, "shooting": 55, "passing": 82, "dribbling": 72, "defending": 66, "physical": 72}},
    {"name": "Tony Achieng",     "position": "Defender",    "jersey_number": 3,  "nationality": "Kenya",    "age": 23, "team_idx": 1,
     "bio": "An overlapping full-back whose crossing has produced six assists this season.",
     "attributes": {"pace": 75, "shooting": 32, "passing": 64, "dribbling": 58, "defending": 79, "physical": 74}},

    # Iron Bridge SC (team_idx = 2)
    {"name": "Vincent Odhiambo", "position": "Forward",    "jersey_number": 7,  "nationality": "Kenya",    "age": 30, "team_idx": 2,
     "bio": "Iron Bridge's all-time top scorer, still finding the net well into his thirties.",
     "attributes": {"pace": 78, "shooting": 88, "passing": 65, "dribbling": 76, "defending": 30, "physical": 75}},
    {"name": "Dennis Barasa",    "position": "Defender",    "jersey_number": 5,  "nationality": "Uganda",   "age": 28, "team_idx": 2,
     "bio": "A no-nonsense stopper signed from across the border two seasons ago.",
     "attributes": {"pace": 62, "shooting": 30, "passing": 60, "dribbling": 48, "defending": 84, "physical": 86}},

    # Vale United (team_idx = 3)
    {"name": "Kevin Omondi",     "position": "Midfielder",  "jersey_number": 10, "nationality": "Kenya",    "age": 25, "team_idx": 3,
     "bio": "Vale's creative spark, equally comfortable threading a pass or beating a man.",
     "attributes": {"pace": 74, "shooting": 70, "passing": 88, "dribbling": 85, "defending": 50, "physical": 62}},
    {"name": "Allan Kiprop",     "position": "Goalkeeper",  "jersey_number": 1,  "nationality": "Kenya",    "age": 31, "team_idx": 3,
     "bio": "A veteran shot-stopper marshalling one of the league's youngest back lines.",
     "attributes": {"diving": 80, "handling": 83, "kicking": 74, "reflexes": 81, "speed": 48, "positioning": 85}},

    # Coastal Rovers (team_idx = 4)
    {"name": "Hassan Juma",      "position": "Forward",    "jersey_number": 9,  "nationality": "Tanzania", "age": 24, "team_idx": 4,
     "bio": "Hassan's movement in the box has made him a nightmare for static defences.",
     "attributes": {"pace": 84, "shooting": 82, "passing": 60, "dribbling": 79, "defending": 26, "physical": 70}},
    {"name": "Moses Kiplagat",   "position": "Defender",    "jersey_number": 2,  "nationality": "Kenya",    "age": 27, "team_idx": 4,
     "bio": "A reliable right-back who rarely misses a fixture.",
     "attributes": {"pace": 71, "shooting": 34, "passing": 62, "dribbling": 52, "defending": 81, "physical": 78}},

    # Ashfield Town (team_idx = 5)
    {"name": "George Mbugua",    "position": "Midfielder",  "jersey_number": 8,  "nationality": "Kenya",    "age": 26, "team_idx": 5,
     "bio": "The heartbeat of Ashfield's midfield since their 2023 promotion push.",
     "attributes": {"pace": 66, "shooting": 58, "passing": 76, "dribbling": 70, "defending": 63, "physical": 69}},

    # Oakfield (team_idx = 6)
    {"name": "Patrick Simiyu",   "position": "Forward",    "jersey_number": 14, "nationality": "Kenya",    "age": 21, "team_idx": 6,
     "bio": "The league's breakout talent this season, still just 21 and already drawing scouts.",
     "attributes": {"pace": 89, "shooting": 75, "passing": 55, "dribbling": 81, "defending": 24, "physical": 60}},

    # Priory Rangers (team_idx = 7)
    {"name": "Elias Karanja",    "position": "Defender",    "jersey_number": 6,  "nationality": "Kenya",    "age": 29, "team_idx": 7,
     "bio": "Elias marshals a young Priory back line with quiet authority.",
     "attributes": {"pace": 64, "shooting": 30, "passing": 58, "dribbling": 46, "defending": 83, "physical": 80}},
]

MATCHES_DATA = [
    # team indices: 0=Riverside, 1=Kestrel, 2=Iron Bridge, 3=Vale, 4=Coastal, 5=Ashfield, 6=Oakfield, 7=Priory
    # (home_idx, away_idx, date_str, status, home_score, away_score, minute, venue)
    (0, 4, "2026-07-25T15:00:00", "scheduled",  None, None, None, "Millbrook Community Ground"),
    (1, 3, "2026-07-25T17:30:00", "scheduled",  None, None, None, "Dunmore Athletic Park"),
    (2, 6, "2026-07-26T14:00:00", "scheduled",  None, None, None, "Halden Recreation Field"),
    (5, 7, "2026-07-26T16:00:00", "scheduled",  None, None, None, "Ashfield Community Pitch"),

    (0, 1, "2026-07-18T15:00:00", "completed",  2, 1, None, "Millbrook Community Ground"),
    (3, 2, "2026-07-18T17:00:00", "completed",  0, 0, None, "Ashcombe Fields"),
    (4, 5, "2026-07-11T15:00:00", "completed",  3, 2, None, "Seaford Pitch"),
    (7, 0, "2026-07-11T14:00:00", "completed",  1, 3, None, "Priory Ground"),

    (6, 4, "2026-08-01T15:00:00", "scheduled",  None, None, None, "Oak Valley Ground"),
    (1, 5, "2026-08-01T17:00:00", "scheduled",  None, None, None, "Dunmore Athletic Park"),

    (0, 3, "2026-07-26T15:00:00", "live",  1, 0, 63, "Millbrook Community Ground"),
    (1, 6, "2026-07-26T15:00:00", "live",  0, 0, 27, "Dunmore Athletic Park"),
    (4, 7, "2026-07-26T15:30:00", "live",  2, 2, 78, "Seaford Pitch"),
    (5, 2, "2026-07-26T16:00:00", "live",  0, 0, 5,  "Ashfield Community Pitch"),
]


def seed():
    with app.app_context():
        print("Clearing existing data…")
        Match.query.delete()
        Player.query.delete()
        Favorite.query.delete()
        Team.query.delete()
        User.query.delete()
        db.session.commit()

        # ── Users ──
        print("Creating users…")
        admin = User(name="Admin", email=ADMIN_EMAIL, role="admin")
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)

        regular = User(name="Test User", email=USER_EMAIL, role="user")
        regular.set_password(USER_PASSWORD)
        db.session.add(regular)
        db.session.commit()
        print(f"  ✓ Admin:   {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"  ✓ Regular: {USER_EMAIL} / {USER_PASSWORD}")

        # ── Teams ──
        print("Creating teams…")
        team_records = []
        for t in TEAMS_DATA:
            team = Team(name=t["name"], city=t["city"],
                        founded_year=t["founded_year"], coach=t["coach"])
            db.session.add(team)
            team_records.append(team)
        db.session.commit()
        print(f"  ✓ {len(team_records)} teams created")

        # ── Players ──
        print("Creating players…")
        player_count = 0
        for p in PLAYERS_DATA:
            player = Player(
                name=p["name"],
                position=p["position"],
                jersey_number=p["jersey_number"],
                nationality=p["nationality"],
                age=p["age"],
                bio=p["bio"],
                attributes=p["attributes"],
                team_id=team_records[p["team_idx"]].id,
            )
            db.session.add(player)
            player_count += 1
        db.session.commit()
        print(f"  ✓ {player_count} players created")

        # ── Matches ──
        print("Creating matches…")
        match_count = 0
        for (h_idx, a_idx, date_str, status, h_score, a_score, minute, venue) in MATCHES_DATA:
            match = Match(
                home_team_id=team_records[h_idx].id,
                away_team_id=team_records[a_idx].id,
                match_date=datetime.fromisoformat(date_str),
                status=status,
                home_score=h_score,
                away_score=a_score,
                minute=minute,
                venue=venue,
            )
            db.session.add(match)
            match_count += 1
        db.session.commit()
        print(f"  ✓ {match_count} matches created")

        print("\n✅ Seed complete!")
        print(f"   ─────────────────────────────────────")
        print(f"   Admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"   User login:  {USER_EMAIL} / {USER_PASSWORD}")
        print(f"   ─────────────────────────────────────")


if __name__ == "__main__":
    seed()
