"""
Rule-Based Expert System using Forward Chaining
-----------------------------------------------
How it works, in one sentence:
    Start from the facts the user gives, repeatedly fire any rule whose
    IF-part is fully known, add its THEN-part as a new fact, and stop when
    no rule can add anything new.

Run it:
    python expert_system.py                       (interactive)
    python expert_system.py --facts fever,cough,body_aches,fatigue

Educational demo only - the medical rules are simplified, not real advice.
"""

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging: every inference step is written to the screen AND to a log file.
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).with_name("inference_log.txt")
logger = logging.getLogger("expert_system")


def setup_logging() -> None:
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))
    logger.addHandler(file_handler)


def normalise(text: str) -> str:
    """'Body Aches ' -> 'body_aches' so user input matches rule names."""
    return text.strip().lower().replace(" ", "_").replace("-", "_")


def pretty(fact: str) -> str:
    """'possible_common_cold' -> 'possible common cold' for display."""
    return fact.replace("_", " ")


# ---------------------------------------------------------------------------
# Data classes: a Rule, and a record of one inference step.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    id: str
    conditions: list          # the IF part  (all must be true)
    conclusion: str           # the THEN part (new fact to add)
    description: str = ""
    priority: int = 0         # higher fires first when several rules match

    def is_satisfied_by(self, facts: set) -> bool:
        return all(condition in facts for condition in self.conditions)

    def __str__(self) -> str:
        return f"{self.id}: IF {' AND '.join(self.conditions)} THEN {self.conclusion}"


@dataclass
class InferenceStep:
    number: int
    rule: Rule
    new_fact: str
    candidates: int           # how many rules were ready to fire this cycle


# ---------------------------------------------------------------------------
# The expert system itself.
# ---------------------------------------------------------------------------
class ExpertSystem:
    def __init__(self, rules: list):
        # sorted() is stable, so rules with equal priority keep their file order
        self.rules = sorted(rules, key=lambda r: -r.priority)
        self.reset()

    def reset(self) -> None:
        self.facts = set()            # working memory: everything known so far
        self.initial_facts = set()    # what the user told us
        self.derived_by = {}          # fact -> the rule that produced it
        self.fired = set()            # rule ids already used (each fires once)
        self.steps = []               # the reasoning path, in order

    @classmethod
    def from_json(cls, path) -> "ExpertSystem":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        rules = [
            Rule(
                id=r["id"],
                conditions=[normalise(c) for c in r["if"]],
                conclusion=normalise(r["then"]),
                description=r.get("description", ""),
                priority=r.get("priority", 0),
            )
            for r in data["rules"]
        ]
        return cls(rules)

    # ---- facts ----------------------------------------------------------
    def input_symptoms(self) -> list:
        """Facts a user can enter: conditions that no rule ever concludes."""
        conclusions = {r.conclusion for r in self.rules}
        symptoms = {c for r in self.rules for c in r.conditions if c not in conclusions}
        return sorted(symptoms)

    def add_facts(self, facts) -> list:
        """Add user facts. Returns any the knowledge base doesn't recognise."""
        known = set(self.input_symptoms())
        unknown = []
        for fact in facts:
            fact = normalise(fact)
            if not fact:
                continue
            if fact not in known:
                unknown.append(fact)
            self.facts.add(fact)
            self.initial_facts.add(fact)
            logger.info(f"FACT GIVEN   {fact}")
        return unknown

    # ---- forward chaining -----------------------------------------------
    def run(self, max_cycles: int = 1000) -> list:
        """
        The recognise-act cycle:
          1. MATCH   - find every rule whose conditions are all known facts
                       and whose conclusion is new (the 'conflict set').
          2. SELECT  - pick one (highest priority, then file order).
          3. ACT     - add its conclusion to the facts and log the step.
          Repeat until the conflict set is empty.
        Because new facts are added each cycle, a conclusion from one rule
        can satisfy another rule later - that is multi-step chaining.
        """
        logger.info("---- forward chaining started ----")
        for _ in range(max_cycles):
            conflict_set = [
                r for r in self.rules
                if r.id not in self.fired
                and r.is_satisfied_by(self.facts)
                and r.conclusion not in self.facts
            ]
            if not conflict_set:
                break

            rule = conflict_set[0]                     # SELECT
            self.fired.add(rule.id)                    # ACT
            self.facts.add(rule.conclusion)
            self.derived_by[rule.conclusion] = rule

            step = InferenceStep(len(self.steps) + 1, rule, rule.conclusion, len(conflict_set))
            self.steps.append(step)
            logger.info(f"STEP {step.number:<3}    {rule}   ({rule.description})")

        logger.info(f"---- finished: {len(self.steps)} new fact(s) inferred ----")
        return self.conclusions()

    def conclusions(self) -> dict:
        """Group derived facts by their prefix so the output is readable."""
        groups = {"urgent": [], "possible": [], "advice": [], "intermediate": []}
        for step in self.steps:
            fact = step.new_fact
            prefix = fact.split("_")[0]
            groups[prefix if prefix in groups else "intermediate"].append(fact)
        return groups

    # ---- explanation ----------------------------------------------------
    def explain(self, fact: str, depth: int = 0) -> list:
        """Answer 'WHY do you believe X?' by walking back down the chain."""
        fact = normalise(fact)
        pad = "    " * depth
        if fact in self.initial_facts:
            return [f"{pad}- {pretty(fact)}  <- you told me this"]
        if fact in self.derived_by:
            rule = self.derived_by[fact]
            lines = [f"{pad}- {pretty(fact)}  <- rule {rule.id}: {rule.description}"]
            for condition in rule.conditions:
                lines.extend(self.explain(condition, depth + 1))
            return lines
        return [f"{pad}- {pretty(fact)}  <- not known (it was never given or inferred)"]


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------
def print_report(es: ExpertSystem) -> None:
    print("\n=== REASONING PATH ===")
    if not es.steps:
        print("No rules could fire with those facts.")
    for s in es.steps:
        print(f"Step {s.number}: {s.rule}")
        print(f"         because: {s.rule.description}  [{s.candidates} rule(s) were ready]")

    groups = es.conclusions()
    labels = {"urgent": "!! URGENT", "possible": "Possible conditions",
              "advice": "Advice", "intermediate": "Intermediate findings"}
    print("\n=== CONCLUSIONS ===")
    for key, label in labels.items():
        if groups[key]:
            print(f"{label}: {', '.join(pretty(f) for f in groups[key])}")
    if not any(groups.values()):
        print("Nothing could be concluded.")
    print("\n(Educational demo only - not medical advice.)")
    print(f"Full log saved to {LOG_FILE.name}")


def ask_for_symptoms(es: ExpertSystem) -> list:
    options = es.input_symptoms()
    print("Known symptoms:")
    for i, name in enumerate(options, 1):
        print(f"  {i:>2}. {pretty(name)}")
    raw = input("\nEnter symptom numbers or names, separated by commas: ")
    chosen = []
    for item in raw.split(","):
        item = item.strip()
        if item.isdigit() and 1 <= int(item) <= len(options):
            chosen.append(options[int(item) - 1])
        elif item:
            chosen.append(item)
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description="Forward-chaining expert system")
    parser.add_argument("--facts", help="comma-separated symptoms, e.g. fever,cough")
    parser.add_argument("--rules", default=Path(__file__).with_name("rules.json"))
    args = parser.parse_args()

    setup_logging()
    es = ExpertSystem.from_json(args.rules)
    print(f"Loaded {len(es.rules)} rules.\n")

    symptoms = args.facts.split(",") if args.facts else ask_for_symptoms(es)
    unknown = es.add_facts(symptoms)
    if unknown:
        print(f"Note: no rules use {', '.join(unknown)} - they'll be ignored by the rules.")

    es.run()
    print_report(es)

    if args.facts:          # non-interactive mode: stop here
        return
    print("\nAsk 'why' about any fact (e.g. possible flu), or press Enter to quit.")
    while (question := input("why? > ").strip()):
        print("\n".join(es.explain(question)))


if __name__ == "__main__":
    main()
