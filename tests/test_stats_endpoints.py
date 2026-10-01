import unittest
from datetime import datetime

from __init__ import create_app
from config import Config
from extensions import db
from models import Match, Player, PlayerMatchStat, Team


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_SEED = False


class StatsEndpointsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.alpha = Team(name="Alpha FC")
        self.bravo = Team(name="Bravo FC")
        db.session.add_all([self.alpha, self.bravo])
        db.session.commit()

        self.striker = self._player("Striker One", "Forward", self.alpha, 9)
        self.keeper = self._player("Keeper One", "Goalkeeper", self.alpha, 1)
        self.bench = self._player("Bench One", "Defender", self.alpha, 4)
        self.rival = self._player("Rival One", "Forward", self.bravo, 10)

        # Alpha at home, then Alpha away, then one still to play
        self.first = self._match(self.alpha, self.bravo, datetime(2026, 7, 1, 15), "completed", 2, 1, venue="Gikomba")
        self.second = self._match(self.bravo, self.alpha, datetime(2026, 7, 15, 15), "completed", 0, 3)
        self.future = self._match(self.alpha, self.bravo, datetime(2026, 8, 1, 15), "scheduled")

        self._stat(self.striker, self.first, goals=2, assists=0)
        self._stat(self.striker, self.second, goals=1, assists=1, yellow_cards=1)
        self._stat(self.keeper, self.first, minutes_played=90)
        self._stat(self.rival, self.first, goals=1)

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _player(self, name, position, team, number):
        player = Player(name=name, position=position, team_id=team.id, jersey_number=number)
        db.session.add(player)
        db.session.commit()
        return player

    def _match(self, home, away, when, status, home_score=None, away_score=None, venue=None):
        match = Match(
            home_team_id=home.id, away_team_id=away.id, match_date=when,
            status=status, home_score=home_score, away_score=away_score, venue=venue,
        )
        db.session.add(match)
        db.session.commit()
        return match

    def _stat(self, player, match, **values):
        row = {"started": True, "minutes_played": 90, "goals": 0, "assists": 0, "yellow_cards": 0, "red_cards": 0}
        row.update(values)
        db.session.add(PlayerMatchStat(player_id=player.id, match_id=match.id, **row))
        db.session.commit()

    # ── a player's match log ──

    def test_match_log_for_unknown_player_is_404(self):
        self.assertEqual(self.client.get("/api/players/9999/matches").status_code, 404)

    def test_player_with_no_rows_has_an_empty_log(self):
        self.assertEqual(self.client.get(f"/api/players/{self.bench.id}/matches").get_json(), [])

    def test_match_log_lists_newest_first_with_opponent_and_side(self):
        rows = self.client.get(f"/api/players/{self.striker.id}/matches").get_json()
        self.assertEqual([r["match_id"] for r in rows], [self.second.id, self.first.id])

        away, home = rows
        self.assertFalse(away["was_home"])
        self.assertEqual(away["opponent"], {"id": self.bravo.id, "name": "Bravo FC"})
        self.assertTrue(home["was_home"])
        self.assertEqual(home["opponent"], {"id": self.bravo.id, "name": "Bravo FC"})

    def test_match_log_rows_carry_the_match_and_the_players_numbers(self):
        home = self.client.get(f"/api/players/{self.striker.id}/matches").get_json()[1]
        self.assertEqual(home["status"], "completed")
        self.assertEqual(home["venue"], "Gikomba")
        self.assertEqual((home["home_score"], home["away_score"]), (2, 1))
        self.assertEqual(home["home_team"]["name"], "Alpha FC")
        self.assertEqual(home["stats"], {
            "started": True, "minutes_played": 90, "goals": 2, "assists": 0, "yellow_cards": 0, "red_cards": 0,
        })

    def test_match_log_only_contains_matches_with_a_row_for_that_player(self):
        rows = self.client.get(f"/api/players/{self.keeper.id}/matches").get_json()
        self.assertEqual([r["match_id"] for r in rows], [self.first.id])

    # ── a club's player totals ──

    def test_club_totals_for_unknown_team_is_404(self):
        self.assertEqual(self.client.get("/api/teams/9999/player-stats").status_code, 404)

    def test_club_totals_include_every_player_even_with_no_stats(self):
        rows = self.client.get(f"/api/teams/{self.alpha.id}/player-stats").get_json()
        names = sorted(r["player"]["name"] for r in rows)
        self.assertEqual(names, ["Bench One", "Keeper One", "Striker One"])

        bench = next(r for r in rows if r["player"]["name"] == "Bench One")
        self.assertEqual((bench["appearances"], bench["goals"], bench["minutes"]), (0, 0, 0))

    def test_club_totals_sum_across_matches(self):
        rows = self.client.get(f"/api/teams/{self.alpha.id}/player-stats").get_json()
        striker = next(r for r in rows if r["player"]["id"] == self.striker.id)
        self.assertEqual(striker["appearances"], 2)
        self.assertEqual(striker["starts"], 2)
        self.assertEqual(striker["minutes"], 180)
        self.assertEqual(striker["goals"], 3)
        self.assertEqual(striker["assists"], 1)
        self.assertEqual(striker["yellow_cards"], 1)
        self.assertEqual(striker["red_cards"], 0)

    def test_club_totals_leave_out_other_clubs_players(self):
        rows = self.client.get(f"/api/teams/{self.alpha.id}/player-stats").get_json()
        self.assertNotIn(self.rival.id, [r["player"]["id"] for r in rows])

    def test_club_totals_describe_each_player(self):
        rows = self.client.get(f"/api/teams/{self.alpha.id}/player-stats").get_json()
        keeper = next(r for r in rows if r["player"]["id"] == self.keeper.id)
        self.assertEqual(keeper["player"], {
            "id": self.keeper.id, "name": "Keeper One", "position": "Goalkeeper", "jersey_number": 1, "photo_url": None,
        })

    def test_totals_agree_with_the_single_player_endpoint(self):
        rows = self.client.get(f"/api/teams/{self.alpha.id}/player-stats").get_json()
        striker = next(r for r in rows if r["player"]["id"] == self.striker.id)
        single = self.client.get(f"/api/players/{self.striker.id}/stats").get_json()
        for field in ("appearances", "starts", "minutes", "goals", "assists", "yellow_cards", "red_cards"):
            self.assertEqual(striker[field], single[field], field)


if __name__ == "__main__":
    unittest.main()
