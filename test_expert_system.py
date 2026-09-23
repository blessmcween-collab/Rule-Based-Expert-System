"""Run with:  python -m unittest -v"""
import unittest
from expert_system import ExpertSystem, Rule


def make_system():
    rules = [
        Rule("A", ["a", "b"], "c", "a and b give c"),
        Rule("B", ["c"], "d", "c gives d"),
        Rule("C", ["d", "e"], "f", "d and e give f"),
        Rule("URG", ["x"], "urgent_help", "x is urgent", priority=10),
    ]
    return ExpertSystem(rules)


class TestForwardChaining(unittest.TestCase):
    def test_single_step(self):
        es = make_system()
        es.add_facts(["a", "b"])
        es.run()
        self.assertIn("c", es.facts)

    def test_multi_step_chain(self):
        es = make_system()
        es.add_facts(["a", "b", "e"])
        es.run()
        # a,b -> c -> d, then d,e -> f : three steps, in that order
        self.assertEqual([s.new_fact for s in es.steps], ["c", "d", "f"])

    def test_nothing_fires_without_matching_facts(self):
        es = make_system()
        es.add_facts(["a"])
        es.run()
        self.assertEqual(es.steps, [])

    def test_each_rule_fires_once(self):
        es = make_system()
        es.add_facts(["a", "b"])
        es.run()
        es.run()  # running again must not duplicate anything
        self.assertEqual(len([s for s in es.steps if s.rule.id == "A"]), 1)

    def test_priority_fires_first(self):
        es = make_system()
        es.add_facts(["a", "b", "x"])
        es.run()
        self.assertEqual(es.steps[0].rule.id, "URG")

    def test_explanation_traces_back_to_user_facts(self):
        es = make_system()
        es.add_facts(["a", "b", "e"])
        es.run()
        text = "\n".join(es.explain("f"))
        self.assertIn("rule C", text)
        self.assertIn("rule A", text)
        self.assertIn("you told me this", text)

    def test_input_normalisation(self):
        es = make_system()
        es.add_facts(["  A ", "B"])
        es.run()
        self.assertIn("c", es.facts)


class TestRealRules(unittest.TestCase):
    def test_flu_chain_from_json(self):
        es = ExpertSystem.from_json("rules.json")
        es.add_facts(["fever", "cough", "body aches", "fatigue"])
        result = es.run()
        self.assertIn("possible_flu", result["possible"])
        self.assertIn("advice_rest_and_fluids", result["advice"])


if __name__ == "__main__":
    unittest.main()
