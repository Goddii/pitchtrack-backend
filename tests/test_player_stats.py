import unittest
from datetime import datetime

from flask_jwt_extended import create_access_token

from __init__ import create_app
from config import Config
from extensions import db
from models import Match, Player, Team


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_SEED = False


class PlayerStatsApiTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.home = Team(name="Alpha FC", city="Nairobi")
        self.away = Team(name="Bravo FC", city="Nairobi")
        db.session.add_all([self.home, self.away])
        db.session.commit()

        self.striker = self._player("Striker One", "Forward", self.home)
        self.keeper = self._player("Keeper One", "Goalkeeper", self.home)
        self.sub = self._player("Bench One", "Defender", self.home)
        self.rival = self._player("Rival One", "Forward", self.away)

        self.done = self._match("completed", home_score=2, away_score=1)
        self.future = self._match("scheduled")

        self.admin = {"Authorization": "Bearer " + create_access_token(identity="1", additional_claims={"role": "admin"})}
        self.fan = {"Authorization": "Bearer " + create_access_token(identity="2", additional_claims={"role": "user"})}
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

    def _match(self, status, home_score=None, away_score=None):
        match = Match(
            home_team_id=self.home.id,
            away_team_id=self.away.id,
            match_date=datetime(2026, 7, 26, 15, 0),
            status=status,
            home_score=home_score,
            away_score=away_score,
        )
        db.session.add(match)
        db.session.commit()
        return match

    def _row(self, player, **overrides):
        row = {"player_id": player.id, "started": True, "minutes_played": 90, "goals": 0, "assists": 0, "yellow_cards": 0, "red_cards": 0}
        row.update(overrides)
        return row

    def _put(self, match, rows, headers=None):
        return self.client.put(
            f"/api/matches/{match.id}/player-stats",
            json={"stats": rows},
            headers=self.admin if headers is None else headers,
        )

    def _totals(self, player):
        response = self.client.get(f"/api/players/{player.id}/stats")
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    # ── aggregates ──

    def test_player_with_no_stats_has_zero_totals(self):
        self.assertEqual(
            self._totals(self.striker),
            {
                "player_id": self.striker.id, "appearances": 0, "starts": 0, "minutes": 0, "goals": 0, "assists": 0,
                "yellow_cards": 0, "red_cards": 0,
                "penalty_goals": 0, "headed_goals": 0, "right_foot_goals": 0, "left_foot_goals": 0,
            },
        )

    def test_unknown_player_stats_returns_404(self):
        self.assertEqual(self.client.get("/api/players/9999/stats").status_code, 404)

    def test_totals_sum_across_matches(self):
        second = self._match("completed", home_score=1, away_score=0)
        self._put(self.done, [self._row(self.striker, goals=2, assists=0, yellow_cards=1)])
        self._put(second, [self._row(self.striker, started=False, minutes_played=30, goals=1, assists=0, red_cards=1)])

        totals = self._totals(self.striker)
        self.assertEqual(totals["appearances"], 2)
        self.assertEqual(totals["starts"], 1)
        self.assertEqual(totals["minutes"], 120)
        self.assertEqual(totals["goals"], 3)
        self.assertEqual(totals["yellow_cards"], 1)
        self.assertEqual(totals["red_cards"], 1)

    def test_unused_substitute_is_not_an_appearance(self):
        self._put(self.done, [self._row(self.sub, started=False, minutes_played=0)])
        totals = self._totals(self.sub)
        self.assertEqual(totals["appearances"], 0)
        self.assertEqual(totals["minutes"], 0)

    # ── entering stats ──

    def test_entering_stats_requires_an_admin(self):
        rows = [self._row(self.striker)]
        self.assertEqual(self._put(self.done, rows, headers={}).status_code, 401)
        self.assertEqual(self._put(self.done, rows, headers=self.fan).status_code, 403)

    def test_cannot_enter_stats_for_a_scheduled_match(self):
        response = self._put(self.future, [self._row(self.striker)])
        self.assertEqual(response.status_code, 400)
        self.assertIn("scheduled", response.get_json()["error"])

    def test_player_must_belong_to_one_of_the_teams(self):
        outsider_team = Team(name="Charlie FC")
        db.session.add(outsider_team)
        db.session.commit()
        outsider = self._player("Outsider", "Forward", outsider_team)
        self.assertEqual(self._put(self.done, [self._row(outsider)]).status_code, 400)

    def test_unknown_player_is_rejected(self):
        self.assertEqual(self._put(self.done, [{"player_id": 9999, "minutes_played": 90}]).status_code, 400)

    def test_invalid_numbers_are_rejected(self):
        for bad in ({"goals": -1}, {"minutes_played": 121}, {"assists": "two"}, {"yellow_cards": 1.5}, {"started": "yes"}):
            with self.subTest(bad=bad):
                self.assertEqual(self._put(self.done, [self._row(self.striker, **bad)]).status_code, 400)

    def test_goals_cannot_exceed_the_team_score(self):
        response = self._put(self.done, [self._row(self.striker, goals=2), self._row(self.keeper, goals=1)])
        self.assertEqual(response.status_code, 400)
        self.assertIn("score", response.get_json()["error"])

    def test_goals_are_checked_against_goals_already_recorded(self):
        self._put(self.done, [self._row(self.striker, goals=2)])
        self.assertEqual(self._put(self.done, [self._row(self.keeper, goals=1)]).status_code, 400)

    def test_saving_again_updates_instead_of_duplicating(self):
        self._put(self.done, [self._row(self.striker, goals=1)])
        self._put(self.done, [self._row(self.striker, goals=2)])
        self.assertEqual(self._totals(self.striker)["goals"], 2)
        rows = self.client.get(f"/api/matches/{self.done.id}/player-stats").get_json()
        self.assertEqual(len(rows), 1)

    def test_a_bad_row_saves_nothing(self):
        response = self._put(self.done, [self._row(self.striker, goals=1), self._row(self.keeper, goals=-3)])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._totals(self.striker)["goals"], 0)

    # ── reading a match's stats ──

    def test_match_stats_list_includes_player_details(self):
        self._put(self.done, [self._row(self.striker, goals=1), self._row(self.rival, goals=1)])
        rows = self.client.get(f"/api/matches/{self.done.id}/player-stats").get_json()
        self.assertEqual(len(rows), 2)
        first = next(r for r in rows if r["player"]["id"] == self.striker.id)
        self.assertEqual(first["player"]["name"], "Striker One")
        self.assertEqual(first["goals"], 1)
        self.assertEqual(first["match_id"], self.done.id)

    def test_removing_a_players_row(self):
        self._put(self.done, [self._row(self.striker)])
        url = f"/api/matches/{self.done.id}/player-stats/{self.striker.id}"
        self.assertEqual(self.client.delete(url, headers=self.fan).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=self.admin).status_code, 200)
        self.assertEqual(self._totals(self.striker)["appearances"], 0)
        self.assertEqual(self.client.delete(url, headers=self.admin).status_code, 404)

    # ── cleanup and the new height field ──

    def test_deleting_a_match_removes_its_stats(self):
        self._put(self.done, [self._row(self.striker, goals=1)])
        self.client.delete(f"/api/matches/{self.done.id}", headers=self.admin)
        self.assertEqual(self._totals(self.striker)["appearances"], 0)

    def test_deleting_a_player_removes_their_stats(self):
        self._put(self.done, [self._row(self.striker, goals=1)])
        self.client.delete(f"/api/players/{self.striker.id}", headers=self.admin)
        rows = self.client.get(f"/api/matches/{self.done.id}/player-stats").get_json()
        self.assertEqual(rows, [])

    def test_height_can_be_set_and_is_returned(self):
        created = self.client.post(
            "/api/players",
            json={"name": "Tall Man", "position": "Defender", "team_id": self.home.id, "height_cm": 191},
            headers=self.admin,
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.get_json()["height_cm"], 191)

        updated = self.client.put(f"/api/players/{created.get_json()['id']}", json={"height_cm": 193}, headers=self.admin)
        self.assertEqual(updated.get_json()["height_cm"], 193)

    def test_height_defaults_to_none(self):
        self.assertIsNone(self.client.get(f"/api/players/{self.striker.id}").get_json()["height_cm"])

    def test_invalid_height_is_rejected(self):
        response = self.client.put(f"/api/players/{self.striker.id}", json={"height_cm": 20}, headers=self.admin)
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
