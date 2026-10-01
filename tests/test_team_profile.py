import unittest

from flask_jwt_extended import create_access_token

from __init__ import create_app
from config import Config
from extensions import db
from models import Player, Team


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_SEED = False


class TeamProfileApiTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.team = Team(name="Alpha FC")
        self.other = Team(name="Bravo FC")
        db.session.add_all([self.team, self.other])
        db.session.commit()
        self.mine = self._player("Alpha One", self.team)
        self.theirs = self._player("Bravo One", self.other)

        self.admin = {"Authorization": "Bearer " + create_access_token(identity="1", additional_claims={"role": "admin"})}
        self.fan = {"Authorization": "Bearer " + create_access_token(identity="2", additional_claims={"role": "user"})}
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _player(self, name, team):
        player = Player(name=name, position="Midfielder", team_id=team.id)
        db.session.add(player)
        db.session.commit()
        return player

    def _put(self, payload, headers=None):
        return self.client.put(f"/api/teams/{self.team.id}", json=payload, headers=headers or self.admin)

    def test_profile_fields_default_to_null_in_the_payload(self):
        body = self.client.get(f"/api/teams/{self.team.id}").get_json()

        for field in ("nickname", "stadium", "capacity", "captain_id"):
            self.assertIn(field, body)
            self.assertIsNone(body[field])

    def test_admin_can_set_the_profile_fields(self):
        res = self._put({"nickname": " The Strikers ", "stadium": "Gikomba Grounds", "capacity": 4500, "captain_id": self.mine.id})

        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertEqual(body["nickname"], "The Strikers")
        self.assertEqual(body["stadium"], "Gikomba Grounds")
        self.assertEqual(body["capacity"], 4500)
        self.assertEqual(body["captain_id"], self.mine.id)

    def test_blank_text_and_null_clear_the_fields(self):
        self._put({"nickname": "X", "capacity": 10, "captain_id": self.mine.id})

        body = self._put({"nickname": "  ", "capacity": None, "captain_id": None}).get_json()

        self.assertIsNone(body["nickname"])
        self.assertIsNone(body["capacity"])
        self.assertIsNone(body["captain_id"])

    def test_captain_must_play_for_the_team(self):
        res = self._put({"captain_id": self.theirs.id})

        self.assertEqual(res.status_code, 400)
        self.assertIn("captain", res.get_json()["error"].lower())

    def test_unknown_captain_is_rejected(self):
        self.assertEqual(self._put({"captain_id": 9999}).status_code, 400)

    def test_capacity_must_be_a_positive_whole_number(self):
        for bad in (0, -5, "lots", 12.5, True):
            self.assertEqual(self._put({"capacity": bad}).status_code, 400, repr(bad))

    def test_text_fields_are_length_limited(self):
        self.assertEqual(self._put({"nickname": "x" * 121}).status_code, 400)
        self.assertEqual(self._put({"stadium": "x" * 121}).status_code, 400)

    def test_non_admins_cannot_edit_the_profile(self):
        self.assertEqual(self._put({"nickname": "Nope"}, headers=self.fan).status_code, 403)

    def test_rejected_update_changes_nothing(self):
        self._put({"nickname": "Keep", "capacity": 0})

        self.assertIsNone(self.client.get(f"/api/teams/{self.team.id}").get_json()["nickname"])

    def test_create_accepts_the_profile_fields_except_captain(self):
        res = self.client.post(
            "/api/teams", headers=self.admin, json={"name": "Charlie FC", "nickname": "Cs", "stadium": "Hill", "capacity": 900}
        )

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["capacity"], 900)
        self.assertIsNone(res.get_json()["captain_id"])

    def test_deleting_the_captain_clears_captain_id(self):
        self._put({"captain_id": self.mine.id})

        res = self.client.delete(f"/api/players/{self.mine.id}", headers=self.admin)

        self.assertEqual(res.status_code, 200)
        self.assertIsNone(self.client.get(f"/api/teams/{self.team.id}").get_json()["captain_id"])


if __name__ == "__main__":
    unittest.main()
