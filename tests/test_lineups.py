import unittest
from datetime import datetime

from flask_jwt_extended import create_access_token

from __init__ import create_app
from config import Config
from extensions import db
from models import Match, Player, Team
from utils.formations import parse_formation


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_SEED = False


class ParseFormationTest(unittest.TestCase):
    def test_accepts_common_formations(self):
        for text in ("4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "4-1-4-1", "3-4-1-2"):
            self.assertEqual(parse_formation(text), (text, None), text)

    def test_trims_whitespace(self):
        self.assertEqual(parse_formation("  4-4-2 "), ("4-4-2", None))

    def test_blank_or_missing_clears_the_formation(self):
        for empty in (None, "", "   "):
            self.assertEqual(parse_formation(empty), (None, None))

    def test_outfield_players_must_add_up_to_ten(self):
        for text in ("4-4-3", "4-3-2", "3-3-3"):
            clean, error = parse_formation(text)
            self.assertIsNone(clean, text)
            self.assertIn("10", error)

    def test_rejects_malformed_text(self):
        for text in ("433", "4-3-", "a-b-c", "4/3/3", "4-0-6", "10", "5-5", "4-3-1-1-1", 433, ["4-3-3"]):
            clean, error = parse_formation(text)
            self.assertIsNone(clean, repr(text))
            self.assertTrue(error, repr(text))


class LineupApiTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.home = Team(name="Alpha FC")
        self.away = Team(name="Bravo FC")
        db.session.add_all([self.home, self.away])
        db.session.commit()

        self.squad = [self._player(f"Alpha {n}", "Midfielder", self.home, n) for n in range(1, 14)]
        self.rival = self._player("Rival One", "Forward", self.away, 10)

        self.future = self._match("scheduled")
        self.done = self._match("completed", 1, 0)

        self.admin = {"Authorization": "Bearer " + create_access_token(identity="1", additional_claims={"role": "admin"})}
        self.fan = {"Authorization": "Bearer " + create_access_token(identity="2", additional_claims={"role": "user"})}
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

    def _match(self, status, home_score=None, away_score=None):
        match = Match(
            home_team_id=self.home.id, away_team_id=self.away.id, match_date=datetime(2026, 8, 2, 15, 0),
            status=status, home_score=home_score, away_score=away_score,
        )
        db.session.add(match)
        db.session.commit()
        return match

    def _lineup_row(self, player, **overrides):
        row = {"player_id": player.id, "started": True, "minutes_played": 0}
        row.update(overrides)
        return row

    def _played_row(self, player, **overrides):
        row = {"player_id": player.id, "started": True, "minutes_played": 90}
        row.update(overrides)
        return row

    def _put_stats(self, match, rows, headers=None):
        return self.client.put(
            f"/api/matches/{match.id}/player-stats",
            json={"stats": rows},
            headers=self.admin if headers is None else headers,
        )

    def _put_match(self, match, body, headers=None):
        return self.client.put(
            f"/api/matches/{match.id}", json=body, headers=self.admin if headers is None else headers
        )

    # ── formations on the match ──

    def test_a_match_has_no_formations_until_set(self):
        body = self.client.get(f"/api/matches/{self.future.id}").get_json()
        self.assertIsNone(body["home_formation"])
        self.assertIsNone(body["away_formation"])

    def test_an_admin_can_set_both_formations(self):
        response = self._put_match(self.future, {"home_formation": "4-3-3", "away_formation": "4-2-3-1"})

        self.assertEqual(response.status_code, 200)
        body = self.client.get(f"/api/matches/{self.future.id}").get_json()
        self.assertEqual((body["home_formation"], body["away_formation"]), ("4-3-3", "4-2-3-1"))

    def test_formations_appear_in_the_match_list(self):
        self._put_match(self.future, {"home_formation": "4-4-2"})

        listed = next(m for m in self.client.get("/api/matches").get_json() if m["id"] == self.future.id)

        self.assertEqual(listed["home_formation"], "4-4-2")

    def test_setting_one_formation_leaves_the_other_alone(self):
        self._put_match(self.future, {"home_formation": "4-4-2", "away_formation": "3-5-2"})
        self._put_match(self.future, {"home_formation": "4-3-3"})

        body = self.client.get(f"/api/matches/{self.future.id}").get_json()
        self.assertEqual((body["home_formation"], body["away_formation"]), ("4-3-3", "3-5-2"))

    def test_null_clears_a_formation(self):
        self._put_match(self.future, {"home_formation": "4-4-2"})
        self._put_match(self.future, {"home_formation": None})

        self.assertIsNone(self.client.get(f"/api/matches/{self.future.id}").get_json()["home_formation"])

    def test_a_bad_formation_is_rejected_and_nothing_else_changes(self):
        response = self._put_match(self.future, {"home_formation": "4-4-3", "venue": "Changed"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("10", response.get_json()["error"])
        body = self.client.get(f"/api/matches/{self.future.id}").get_json()
        self.assertIsNone(body["home_formation"])
        self.assertIsNone(body["venue"])

    def test_setting_a_formation_requires_an_admin(self):
        self.assertEqual(self._put_match(self.future, {"home_formation": "4-4-2"}, headers={}).status_code, 401)
        self.assertEqual(self._put_match(self.future, {"home_formation": "4-4-2"}, headers=self.fan).status_code, 403)

    # ── lineups before kickoff ──

    def test_a_lineup_can_be_saved_for_a_scheduled_match(self):
        rows = [self._lineup_row(p) for p in self.squad[:11]]

        response = self._put_stats(self.future, rows)

        self.assertEqual(response.status_code, 200)
        saved = self.client.get(f"/api/matches/{self.future.id}/player-stats").get_json()
        self.assertEqual(len(saved), 11)
        self.assertTrue(all(r["started"] and r["minutes_played"] == 0 for r in saved))

    def test_a_scheduled_match_accepts_nothing_but_the_lineup(self):
        for overrides in ({"minutes_played": 90}, {"goals": 1}, {"assists": 1}, {"yellow_cards": 1}, {"red_cards": 1}):
            response = self._put_stats(self.future, [self._lineup_row(self.squad[0], **overrides)])
            self.assertEqual(response.status_code, 400, overrides)
            self.assertIn("scheduled", response.get_json()["error"])

    def test_a_scheduled_match_still_checks_the_player_plays_for_a_side(self):
        other_team = Team(name="Charlie FC")
        db.session.add(other_team)
        db.session.commit()
        stranger = self._player("Stranger", "Forward", other_team, 9)

        response = self._put_stats(self.future, [self._lineup_row(stranger)])

        self.assertEqual(response.status_code, 400)
        self.assertIn("does not play for either team", response.get_json()["error"])

    def test_a_lineup_does_not_count_as_a_start_or_an_appearance(self):
        player = self.squad[0]
        self._put_stats(self.future, [self._lineup_row(player)])

        totals = self.client.get(f"/api/players/{player.id}/stats").get_json()

        self.assertEqual((totals["appearances"], totals["starts"], totals["minutes"]), (0, 0, 0))

    def test_a_played_start_still_counts(self):
        player = self.squad[0]
        self._put_stats(self.done, [self._played_row(player)])

        totals = self.client.get(f"/api/players/{player.id}/stats").get_json()

        self.assertEqual((totals["appearances"], totals["starts"], totals["minutes"]), (1, 1, 90))

    # ── no more than eleven starters ──

    def test_a_team_cannot_start_twelve_players(self):
        rows = [self._lineup_row(p) for p in self.squad[:12]]

        response = self._put_stats(self.future, rows)

        self.assertEqual(response.status_code, 400)
        self.assertIn("11", response.get_json()["error"])
        self.assertEqual(self.client.get(f"/api/matches/{self.future.id}/player-stats").get_json(), [])

    def test_the_starter_limit_counts_rows_already_saved(self):
        self._put_stats(self.future, [self._lineup_row(p) for p in self.squad[:11]])

        response = self._put_stats(self.future, [self._lineup_row(self.squad[11])])

        self.assertEqual(response.status_code, 400)

    def test_resaving_an_existing_starter_is_not_a_new_starter(self):
        self._put_stats(self.future, [self._lineup_row(p) for p in self.squad[:11]])

        response = self._put_stats(self.future, [self._lineup_row(self.squad[0])])

        self.assertEqual(response.status_code, 200)

    def test_taking_a_player_out_of_the_lineup_makes_room(self):
        self._put_stats(self.future, [self._lineup_row(p) for p in self.squad[:11]])

        self._put_stats(self.future, [self._lineup_row(self.squad[0], started=False)])
        response = self._put_stats(self.future, [self._lineup_row(self.squad[11])])

        self.assertEqual(response.status_code, 200)

    def test_the_limit_applies_after_kickoff_too(self):
        rows = [self._played_row(p) for p in self.squad[:12]]

        response = self._put_stats(self.done, rows)

        self.assertEqual(response.status_code, 400)
        self.assertIn("11", response.get_json()["error"])

    def test_each_team_has_its_own_limit_of_eleven(self):
        rows = [self._lineup_row(p) for p in self.squad[:11]] + [self._lineup_row(self.rival)]

        self.assertEqual(self._put_stats(self.future, rows).status_code, 200)


if __name__ == "__main__":
    unittest.main()
