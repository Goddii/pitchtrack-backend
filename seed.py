"""
Seed the database with sample data — a fictional Kenyan Sunday-league setup.

Usage:
    cd pitchtrack-backend
    PYTHONPATH=. pipenv run python seed.py
"""

import random
from datetime import datetime
from extensions import db
from models import User, Team, Player, Match, Favorite, PlayerMatchStat
from seed_stats import make_height, seed_player_stats

ADMIN_EMAIL = "admin@pitchtrack.com"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "user@example.com"
USER_PASSWORD = "password123"

TEAMS_DATA = [
    {"name": "Sokoni Strikers FC",       "city": "Gikomba, Nairobi",     "founded_year": 2012, "coach": "Wilson 'Professor' Mbugua"},
    {"name": "Boda Boda Bullets FC",      "city": "Kayole, Nairobi",      "founded_year": 2015, "coach": "Ali Hassan"},
    {"name": "Mama Mboga United",         "city": "Kawangware, Nairobi",  "founded_year": 2009, "coach": "Grace Wanjiru"},
    {"name": "Chips Funga FC",            "city": "Eastleigh, Nairobi",   "founded_year": 2018, "coach": None},
    {"name": "Sukuma Wiki Warriors",      "city": "Dagoretti, Nairobi",   "founded_year": 2001, "coach": "Peter Kamau"},
    {"name": "Nyama Choma All Stars",     "city": "Ngong Road, Kajiado",  "founded_year": 1999, "coach": "Daniel Sankale"},
    {"name": "Late Kickoff FC",           "city": "Thika, Kiambu",        "founded_year": 2020, "coach": None},
    {"name": "Songa Mbele Rangers",       "city": "Kibera, Nairobi",      "founded_year": 2005, "coach": "Susan Achieng"},
]

ROSTERS = {
    0: [
        ("Erick Wanyonyi",   "Goalkeeper", 1,  "Kenya",  26),
        ("Bramwel Otieno",   "Defender",   2,  "Kenya",  28),
        ("Newton Kariuki",   "Defender",   3,  "Kenya",  24),
        ("Zablon Mutiso",    "Defender",   4,  "Kenya",  30),
        ("Douglas Wekesa",   "Defender",   5,  "Kenya",  22),
        ("Justus Njenga",    "Midfielder", 6,  "Kenya",  25),
        ("Kelly Ochieng",    "Midfielder", 7,  "Uganda", 27),
        ("Amos Kilonzo",     "Midfielder", 8,  "Kenya",  23),
        ("Victor Muriuki",   "Forward",    9,  "Kenya",  21),
        ("Titus Barasa",     "Forward",    10, "Kenya",  29),
        ("Cyrus Ngugi",      "Forward",    11, "Kenya",  19),
    ],
    1: [
        ("Boniface Mwendwa", "Goalkeeper", 1,  "Kenya",    27),
        ("Fredrick Kioko",   "Defender",   2,  "Kenya",    29),
        ("Robert Chege",     "Defender",   3,  "Kenya",    24),
        ("Simon Rotich",     "Defender",   4,  "Kenya",    31),
        ("Edwin Sang",       "Defender",   5,  "Kenya",    23),
        ("Enock Musyoka",    "Midfielder", 6,  "Kenya",    26),
        ("Nixon Korir",      "Midfielder", 7,  "Kenya",    28),
        ("Wesley Owino",     "Midfielder", 8,  "Tanzania", 25),
        ("Alex Waweru",      "Forward",    9,  "Kenya",    22),
        ("Duncan Maina",     "Forward",    10, "Kenya",    24),
        ("Ian Gitau",        "Forward",    11, "Kenya",    18),
    ],
    2: [
        ("Stephen Onyango",  "Goalkeeper", 1,  "Kenya", 30),
        ("Charles Wambua",   "Defender",   2,  "Kenya", 27),
        ("Francis Gitonga",  "Defender",   3,  "Kenya", 25),
        ("Anthony Njuguna",  "Defender",   4,  "Kenya", 29),
        ("David Muturi",     "Defender",   5,  "Kenya", 22),
        ("Paul Mutua",       "Midfielder", 6,  "Kenya", 26),
        ("Michael Ndungu",   "Midfielder", 7,  "Kenya", 24),
        ("John Kones",       "Midfielder", 8,  "Kenya", 28),
        ("Peter Njoroge",    "Forward",    9,  "Kenya", 23),
        ("Daniel Ouma",      "Forward",    10, "Kenya", 21),
        ("Joseph Langat",    "Forward",    11, "Kenya", 25),
    ],
    3: [
        ("Hassan Abdi",      "Goalkeeper", 1,  "Kenya", 24),
        ("Ibrahim Noor",     "Defender",   2,  "Kenya", 27),
        ("Yusuf Ali",        "Defender",   3,  "Kenya", 25),
        ("Mohamed Hassan",   "Defender",   4,  "Kenya", 29),
        ("Adan Roble",       "Defender",   5,  "Kenya", 22),
        ("Abdi Warsame",     "Midfielder", 6,  "Kenya", 26),
        ("Salim Juma",       "Midfielder", 7,  "Kenya", 28),
        ("Omar Sheikh",      "Midfielder", 8,  "Kenya", 24),
        ("Ahmed Noor",       "Forward",    9,  "Kenya", 21),
        ("Bashir Aden",      "Forward",    10, "Kenya", 23),
        ("Khalid Diriye",    "Forward",    11, "Kenya", 20),
    ],
    4: [
        ("Geoffrey Muriithi","Goalkeeper", 1,  "Kenya", 28),
        ("Nicholas Thiongo", "Defender",   2,  "Kenya", 26),
        ("Patrick Ndegwa",   "Defender",   3,  "Kenya", 24),
        ("Elias Wanjohi",    "Defender",   4,  "Kenya", 30),
        ("Martin Kamande",   "Defender",   5,  "Kenya", 22),
        ("Samuel Gachanja",  "Midfielder", 6,  "Kenya", 25),
        ("Peter Mburu",      "Midfielder", 7,  "Kenya", 27),
        ("John Kagwe",       "Midfielder", 8,  "Kenya", 23),
        ("James Nyaga",      "Forward",    9,  "Kenya", 21),
        ("Vincent Karioki",  "Forward",    10, "Kenya", 29),
        ("Dennis Mwaura",    "Forward",    11, "Kenya", 20),
    ],
    5: [
        ("Joseph Sironka",   "Goalkeeper", 1,  "Kenya", 27),
        ("Daniel Saitoti",   "Defender",   2,  "Kenya", 26),
        ("Moses Ntutu",      "Defender",   3,  "Kenya", 28),
        ("Peter Lekishon",   "Defender",   4,  "Kenya", 24),
        ("Samuel Mpaayei",   "Defender",   5,  "Kenya", 30),
        ("John Sankale",     "Midfielder", 6,  "Kenya", 25),
        ("Elijah Toroitich", "Midfielder", 7,  "Kenya", 27),
        ("Kevin Kones",      "Midfielder", 8,  "Kenya", 23),
        ("Brian Sialo",      "Forward",    9,  "Kenya", 22),
        ("George Nkoitoi",   "Forward",    10, "Kenya", 21),
        ("Francis Ole Kina", "Forward",    11, "Kenya", 26),
    ],
    6: [
        ("Kennedy Muchiri",  "Goalkeeper", 1,  "Kenya", 29),
        ("Peter Gathogo",    "Defender",   2,  "Kenya", 27),
        ("James Kariba",     "Defender",   3,  "Kenya", 25),
        ("Michael Ndirangu", "Defender",   4,  "Kenya", 31),
        ("Anthony Wachira",  "Defender",   5,  "Kenya", 23),
        ("David Kabue",      "Midfielder", 6,  "Kenya", 26),
        ("Stephen Githinji", "Midfielder", 7,  "Kenya", 24),
        ("Felix Mwaniki",    "Midfielder", 8,  "Kenya", 28),
        ("Collins Karanja",  "Forward",    9,  "Kenya", 22),
        ("Brian Mutugi",     "Forward",    10, "Kenya", 20),
        ("Erick Njihia",     "Forward",    11, "Kenya", 21),
    ],
    7: [
        ("Victor Omollo",    "Goalkeeper", 1,  "Kenya", 28),
        ("Kevin Onyango",    "Defender",   2,  "Kenya", 26),
        ("Brian Adero",      "Defender",   3,  "Kenya", 24),
        ("Felix Oduor",      "Defender",   4,  "Kenya", 29),
        ("Tony Owuor",       "Defender",   5,  "Kenya", 22),
        ("Eric Otieno",      "Midfielder", 6,  "Kenya", 27),
        ("Dennis Okello",    "Midfielder", 7,  "Kenya", 25),
        ("George Opiyo",     "Midfielder", 8,  "Kenya", 23),
        ("James Ochola",     "Forward",    9,  "Kenya", 21),
        ("Patrick Owino",    "Forward",    10, "Kenya", 20),
        ("Vincent Oyoo",     "Forward",    11, "Kenya", 18),
    ],
}

SKILL_BLURBS = {
    "Goalkeeper": [
        "{name} commands the box like it owes him rent, and shot-stopping is where {team} trusts him most.",
        "A reflex save specialist — {name} has kept {team} in matches they had no business surviving.",
        "{name} marshals the {team} back line with a voice that carries over any matatu horn nearby.",
        "Known for punching clear anything within reach, {name} rarely lets a cross past him unchallenged.",
    ],
    "Defender": [
        "A no-nonsense stopper, {name} treats every through-ball as a personal insult to {team}.",
        "{name} reads the game a beat ahead of most Sunday-league forwards, rarely caught out of position.",
        "The last line before the goalkeeper, {name} has made blocking crosses an art form for {team}.",
        "{name} tackles like the ball owes him money — hard, fast, and with a clean conscience.",
    ],
    "Midfielder": [
        "The engine room of {team}, {name} covers every blade of grass and still has energy to celebrate.",
        "{name} dictates tempo from deep, spraying passes around like he's got a subscription to assists.",
        "A tireless box-to-box presence, {name} is first to press and last to stop running for {team}.",
        "{name}'s vision splits defences open — teammates say he sees passes before they even happen.",
    ],
    "Forward": [
        "{name} leads the line for {team} with a nose for goal sharpened over years of estate-pitch football.",
        "Give {name} half a yard in the box and {team}'s opponents already know how this ends.",
        "{name}'s pace on the counter has turned into {team}'s go-to plan whenever the scoreline needs fixing.",
        "A poacher through and through, {name} scores the ugly ones just as happily as the wonder strikes.",
    ],
}

OCCUPATION_JOKES = [
    "rides a boda boda on weekdays and insists the throttle hand is the same as the shooting foot",
    "sells mitumba at the local market and negotiates transfer gossip harder than clothing prices",
    "is a matatu tout on Route 46 and treats the touchline like the roof of a moving vehicle",
    "runs a small cyber café and updates the team WhatsApp group more than the league table",
    "works as a mechanic in the estate's jua kali yard and fixes teammates' boots for a small fee",
    "is a mama mboga's firstborn and still gets sent to buy sukuma wiki before Sunday kickoff",
    "does hair at a barbershop famous for its line-ups, on and off the pitch",
    "is a form-four leaver still waiting for KCSE results and blaming the wait on match fatigue",
    "hawks roasted maize near the pitch during halftime and somehow never misses his own kickoff",
    "studies at a local TVET college and swears the coursework is tougher than pre-season training",
    "works part-time at a hardware shop and can quote screw sizes faster than his own stats",
    "drives for a delivery app between matches and treats every sprint like a bonus-time bonus",
    "is training to be an electrician and jokes that his tackles come with a shock included",
    "sells phone accessories at a stage stall and upsells screen protectors to anyone who'll listen",
    "is a church choir member on Saturdays and brings the same enthusiasm to Sunday celebrations",
    "works security at a supermarket and says standing all week is the best pre-match conditioning",
    "is apprenticing as a tailor and stitched half the team's original kit himself",
    "runs errands for a boda boda stage sacco and has never once been late for a shift, unlike this team",
]


def make_bio(name, position, team_name, idx):
    first_name = name.split()[0]
    skill = SKILL_BLURBS[position][idx % len(SKILL_BLURBS[position])].format(name=first_name, team=team_name)
    job = OCCUPATION_JOKES[idx % len(OCCUPATION_JOKES)]
    return f"{skill} Off the pitch, {first_name} {job}."


def make_attributes(position, seed_key):
    rng = random.Random(seed_key)
    if position == "Goalkeeper":
        return {
            "diving": rng.randint(70, 90),
            "handling": rng.randint(70, 88),
            "kicking": rng.randint(55, 80),
            "reflexes": rng.randint(72, 90),
            "speed": rng.randint(40, 60),
            "positioning": rng.randint(70, 88),
        }
    if position == "Defender":
        return {
            "pace": rng.randint(55, 78),
            "shooting": rng.randint(25, 40),
            "passing": rng.randint(50, 72),
            "dribbling": rng.randint(40, 60),
            "defending": rng.randint(75, 90),
            "physical": rng.randint(70, 88),
        }
    if position == "Midfielder":
        return {
            "pace": rng.randint(60, 80),
            "shooting": rng.randint(50, 72),
            "passing": rng.randint(70, 90),
            "dribbling": rng.randint(65, 85),
            "defending": rng.randint(50, 72),
            "physical": rng.randint(60, 78),
        }
    return {
        "pace": rng.randint(75, 92),
        "shooting": rng.randint(70, 90),
        "passing": rng.randint(50, 75),
        "dribbling": rng.randint(70, 88),
        "defending": rng.randint(20, 40),
        "physical": rng.randint(60, 80),
    }


PLAYERS_DATA = []
_global_idx = 0
for _team_idx, _roster in ROSTERS.items():
    _team_name = TEAMS_DATA[_team_idx]["name"]
    for (_name, _position, _jersey, _nationality, _age) in _roster:
        PLAYERS_DATA.append({
            "name": _name,
            "position": _position,
            "jersey_number": _jersey,
            "nationality": _nationality,
            "age": _age,
            "team_idx": _team_idx,
            "bio": make_bio(_name, _position, _team_name, _global_idx),
            "attributes": make_attributes(_position, _name),
        })
        _global_idx += 1

MATCHES_DATA = [
    (0, 4, "2026-08-02T15:00:00", "scheduled", None, None, None, "Gikomba Grounds"),
    (1, 3, "2026-08-02T17:30:00", "scheduled", None, None, None, "Kayole Social Hall Grounds"),
    (2, 6, "2026-08-03T14:00:00", "scheduled", None, None, None, "Kawangware Open Grounds"),
    (5, 7, "2026-08-03T16:00:00", "scheduled", None, None, None, "Ngong Road Recreation Ground"),
    (0, 1, "2026-07-26T15:00:00", "completed", 2, 1, None, "Gikomba Grounds"),
    (3, 2, "2026-07-26T17:00:00", "completed", 0, 0, None, "Eastleigh Airbase Grounds"),
    (4, 5, "2026-07-19T15:00:00", "completed", 3, 2, None, "Dagoretti Corner Grounds"),
    (7, 0, "2026-07-19T14:00:00", "completed", 1, 3, None, "Kibera Undugu Grounds"),
    (6, 4, "2026-08-09T15:00:00", "scheduled", None, None, None, "Thika Stadium Grounds"),
    (1, 5, "2026-08-09T17:00:00", "scheduled", None, None, None, "Kayole Social Hall Grounds"),
    (0, 3, "2026-07-31T15:00:00", "live", 1, 0, 63, "Gikomba Grounds"),
    (1, 6, "2026-07-31T15:00:00", "live", 0, 0, 27, "Kayole Social Hall Grounds"),
    (4, 7, "2026-07-31T15:30:00", "live", 2, 2, 78, "Dagoretti Corner Grounds"),
    (5, 2, "2026-07-31T16:00:00", "live", 0, 0, 5,  "Ngong Road Recreation Ground"),
]


def seed_database(app):
    """Seed the database using the provided Flask app instance."""
    with app.app_context():
        print("Clearing existing data…")
        PlayerMatchStat.query.delete()
        Match.query.delete()
        Player.query.delete()
        Favorite.query.delete()
        Team.query.delete()
        User.query.delete()
        db.session.commit()

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

        print("Creating teams…")
        team_records = []
        for t in TEAMS_DATA:
            team = Team(name=t["name"], city=t["city"],
                        founded_year=t["founded_year"], coach=t["coach"])
            db.session.add(team)
            team_records.append(team)
        db.session.commit()
        print(f"  ✓ {len(team_records)} teams created")

        print("Creating players…")
        player_count = 0
        for p in PLAYERS_DATA:
            player = Player(
                name=p["name"],
                position=p["position"],
                jersey_number=p["jersey_number"],
                nationality=p["nationality"],
                age=p["age"],
                height_cm=make_height(p["position"], p["name"]),
                bio=p["bio"],
                attributes=p["attributes"],
                team_id=team_records[p["team_idx"]].id,
            )
            db.session.add(player)
            player_count += 1
        db.session.commit()
        print(f"  ✓ {player_count} players created")

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

        print("Creating player stats…")
        seed_player_stats(app)

        print("\n✅ Seed complete!")
        print(f"   ─────────────────────────────────────")
        print(f"   Admin login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"   User login:  {USER_EMAIL} / {USER_PASSWORD}")
        print(f"   ─────────────────────────────────────")


# Backward compatibility for local CLI usage
def seed():
    from run import app
    seed_database(app)


if __name__ == "__main__":
    import sys

    if "--stats" in sys.argv:
        # Safe for a database with real rows: only adds missing heights and stats
        from run import app
        seed_player_stats(app)
    else:
        seed()