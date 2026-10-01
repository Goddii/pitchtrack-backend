import unittest
from datetime import datetime

from flask_jwt_extended import create_access_token

from __init__ import create_app
from config import Config
from extensions import db
from models import Match, Player, Team

TYPE_FIELDS = ("penalty_goals", "headed_goals", "right_foot_goals", "left_foot_goals")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_SEED = False


class GoalTypesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.home = Team(name="Alpha FC")
        self.away = Team(name="Bravo FC")
        db.session.add_all([self.home, self.away])
        db.session.commit()

        self.striker = self._player("Striker One", "Forward", self.home)
        self.keeper = self._player("Keeper One", "Goalkeeper", self.home)
        self.first = self._match(4, 0)
        self.second = self._match(3, 0)

        self.admin = {"Authorization": "Bearer " + create_access_token(identity="1", additional_claims={"role": "admin"})}
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _player(self, name, position, team):
        player = Player(name=name, position=position, team_id=team.id)
        db.session.add(player)
        db.session.commit()
        return player

    def _match(self, home_score, away_score):
        match = Match(
            home_team_id=self.home.id, away_team_id=self.away.id, match_date=datetime(2026, 7, 26, 15),
            status="completed", home_score=home_score, away_score=away_score,
        )
        db.session.add(match)
        db.session.commit()
        return match

    def _row(self, player, **overrides):
        row = {"player_id": player.id, "started": True, "minutes_played": 90, "goals": 0, "assists": 0, "yellow_cards": 0, "red_cards": 0}
        row.update(overrides)
        return row

    def _put(self, match, rows):
        return self.client.put(f"/api/matches/{match.id}/player-stats", json={"stats": rows}, headers=self.admin)

    def _totals(self, player):
        return self.client.get(f"/api/players/{player.id}/stats").get_json()

    def test_totals_start_at_zero_for_every_goal_type(self):
        totals = self._totals(self.striker)
        for field in TYPE_FIELDS:
            self.assertEqual(totals[field], 0, field)

    def test_goal_types_are_saved_and_summed_across_matches(self):
        self._put(self.first, [self._row(self.striker, goals=3, right_foot_goals=2, headed_goals=1)])
        self._put(self.second, [self._row(self.striker, goals=2, penalty_goals=1, left_foot_goals=1)])

        totals = self._totals(self.striker)
        self.assertEqual(totals["goals"], 5)
        self.assertEqual(totals["right_foot_goals"], 2)
        self.assertEqual(totals["headed_goals"], 1)
        self.assertEqual(totals["penalty_goals"], 1)
        self.assertEqual(totals["left_foot_goals"], 1)

    def test_goal_types_default_to_zero_when_left_out(self):
        self.assertEqual(self._put(self.first, [self._row(self.striker, goals=2)]).status_code, 200)
        totals = self._totals(self.striker)
        self.assertEqual(totals["goals"], 2)
        self.assertEqual(sum(totals[f] for f in TYPE_FIELDS), 0)

    def test_goal_types_can_be_fewer_than_goals(self):
        response = self._put(self.first, [self._row(self.striker, goals=3, right_foot_goals=1)])
        self.assertEqual(response.status_code, 200)

    def test_goal_types_cannot_add_up_to_more_than_the_goals(self):
        response = self._put(self.first, [self._row(self.striker, goals=2, right_foot_goals=2, headed_goals=1)])
        self.assertEqual(response.status_code, 400)
        self.assertIn("goal types", response.get_json()["error"])
        self.assertEqual(self._totals(self.striker)["goals"], 0)

    def test_goal_types_without_goals_are_rejected(self):
        self.assertEqual(self._put(self.first, [self._row(self.striker, goals=0, penalty_goals=1)]).status_code, 400)

    def test_invalid_goal_type_numbers_are_rejected(self):
        for bad in ({"penalty_goals": -1}, {"headed_goals": "one"}, {"left_foot_goals": 1.5}, {"right_foot_goals": True}):
            with self.subTest(bad=bad):
                response = self._put(self.first, [self._row(self.striker, goals=3, **bad)])
                self.assertEqual(response.status_code, 400)

    def test_match_rows_include_the_goal_types(self):
        self._put(self.first, [self._row(self.striker, goals=2, right_foot_goals=1, headed_goals=1)])
        row = self.client.get(f"/api/matches/{self.first.id}/player-stats").get_json()[0]
        self.assertEqual(row["right_foot_goals"], 1)
        self.assertEqual(row["headed_goals"], 1)
        self.assertEqual(row["penalty_goals"], 0)
        self.assertEqual(row["left_foot_goals"], 0)

    def test_club_totals_include_the_goal_types(self):
        self._put(self.first, [self._row(self.striker, goals=2, penalty_goals=1, left_foot_goals=1)])
        rows = self.client.get(f"/api/teams/{self.home.id}/player-stats").get_json()
        striker = next(r for r in rows if r["player"]["id"] == self.striker.id)
        self.assertEqual(striker["penalty_goals"], 1)
        self.assertEqual(striker["left_foot_goals"], 1)
        self.assertEqual(striker["headed_goals"], 0)


if __name__ == "__main__":
    unittest.main()
