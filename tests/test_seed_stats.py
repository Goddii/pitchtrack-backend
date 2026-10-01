import unittest
from types import SimpleNamespace

from seed_stats import build_match_stats, make_height, split_goal_types

POSITION_MIX = ["Goalkeeper"] + ["Defender"] * 4 + ["Midfielder"] * 3 + ["Forward"] * 3


def squad(first_id):
    return [SimpleNamespace(id=first_id + i, position=position) for i, position in enumerate(POSITION_MIX)]


HOME = squad(1)
AWAY = squad(101)
HOME_IDS = {p.id for p in HOME}
AWAY_IDS = {p.id for p in AWAY}


def build(match_id=7, status="completed", minute=None, home_score=3, away_score=2):
    return build_match_stats(match_id, status, minute, home_score, away_score, HOME, AWAY)


def total(rows, ids, field):
    return sum(r[field] for r in rows if r["player_id"] in ids)


class BuildMatchStatsTest(unittest.TestCase):
    def test_every_player_gets_a_row(self):
        rows = build()
        self.assertEqual({r["player_id"] for r in rows}, HOME_IDS | AWAY_IDS)
        self.assertEqual(len(rows), 22)

    def test_goals_add_up_to_each_teams_score(self):
        rows = build(home_score=3, away_score=2)
        self.assertEqual(total(rows, HOME_IDS, "goals"), 3)
        self.assertEqual(total(rows, AWAY_IDS, "goals"), 2)

    def test_goalless_match_has_no_goals_or_assists(self):
        rows = build(home_score=0, away_score=0)
        self.assertEqual(total(rows, HOME_IDS | AWAY_IDS, "goals"), 0)
        self.assertEqual(total(rows, HOME_IDS | AWAY_IDS, "assists"), 0)

    def test_assists_never_exceed_goals(self):
        for match_id in range(1, 40):
            rows = build(match_id=match_id, home_score=4, away_score=3)
            self.assertLessEqual(total(rows, HOME_IDS, "assists"), 4)
            self.assertLessEqual(total(rows, AWAY_IDS, "assists"), 3)

    def test_goalkeepers_do_not_score_or_assist(self):
        goalkeepers = {HOME[0].id, AWAY[0].id}
        for match_id in range(1, 40):
            rows = build(match_id=match_id, home_score=5, away_score=5)
            self.assertEqual(total(rows, goalkeepers, "goals"), 0)
            self.assertEqual(total(rows, goalkeepers, "assists"), 0)

    def test_completed_match_players_play_the_full_game_unless_sent_off(self):
        for match_id in range(1, 60):
            for row in build(match_id=match_id):
                self.assertTrue(row["started"])
                if row["red_cards"] == 0:
                    self.assertEqual(row["minutes_played"], 90)
                else:
                    self.assertTrue(1 <= row["minutes_played"] <= 90)

    def test_live_match_uses_the_current_minute_and_score(self):
        rows = build(status="live", minute=63, home_score=1, away_score=0)
        self.assertEqual(total(rows, HOME_IDS, "goals"), 1)
        self.assertEqual(total(rows, AWAY_IDS, "goals"), 0)
        for row in rows:
            if row["red_cards"] == 0:
                self.assertEqual(row["minutes_played"], 63)
            else:
                self.assertLessEqual(row["minutes_played"], 63)

    def test_cards_stay_within_sensible_limits(self):
        for match_id in range(1, 60):
            for row in build(match_id=match_id):
                self.assertIn(row["yellow_cards"], (0, 1))
                self.assertIn(row["red_cards"], (0, 1))

    def test_same_match_always_gives_the_same_rows(self):
        self.assertEqual(build(match_id=12), build(match_id=12))

    def test_missing_scores_count_as_zero(self):
        rows = build(home_score=None, away_score=None)
        self.assertEqual(total(rows, HOME_IDS | AWAY_IDS, "goals"), 0)


class MakeHeightTest(unittest.TestCase):
    def test_heights_fit_the_position(self):
        for name in ("A", "B", "C", "D", "E"):
            self.assertTrue(183 <= make_height("Goalkeeper", name) <= 196)
            self.assertTrue(175 <= make_height("Defender", name) <= 190)
            self.assertTrue(168 <= make_height("Midfielder", name) <= 184)
            self.assertTrue(170 <= make_height("Forward", name) <= 188)

    def test_height_is_stable_for_a_player(self):
        self.assertEqual(make_height("Forward", "Abdi Warsame"), make_height("Forward", "Abdi Warsame"))


TYPE_FIELDS = ("penalty_goals", "headed_goals", "right_foot_goals", "left_foot_goals")


class GoalTypesSeedTest(unittest.TestCase):
    def test_every_generated_goal_gets_a_type(self):
        for match_id in range(1, 30):
            for row in build(match_id=match_id, home_score=3, away_score=2):
                self.assertEqual(sum(row[f] for f in TYPE_FIELDS), row["goals"])

    def test_split_adds_up_and_is_stable(self):
        first = split_goal_types(4, "7:3")
        self.assertEqual(first, split_goal_types(4, "7:3"))
        self.assertEqual(sum(first.values()), 4)
        self.assertEqual(set(first), set(TYPE_FIELDS))

    def test_no_goals_means_no_types(self):
        self.assertEqual(sum(split_goal_types(0, "x").values()), 0)

    def test_a_long_run_of_goals_uses_every_type(self):
        self.assertTrue(all(count > 0 for count in split_goal_types(300, "mix").values()))

    def test_right_foot_is_the_most_common_finish(self):
        totals = split_goal_types(500, "common")
        self.assertEqual(max(totals, key=totals.get), "right_foot_goals")


if __name__ == "__main__":
    unittest.main()
