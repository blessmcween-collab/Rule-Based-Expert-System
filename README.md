# Rule-Based-Expert-System
# Rule-Based Expert System (Forward Chaining)

A small expert system in pure Python. You give it facts (symptoms), and it infers conclusions by chaining IF-THEN rules, logging every reasoning step and explaining *why* it reached each conclusion.

> Educational demo only. The medical rules are simplified and are not medical advice.

## Features
- **Rule engine** with rules stored in `rules.json` (change the domain without touching code)
- **Forward chaining** using the match → select → act cycle
- **Multi-step inference**: conclusions from one rule trigger other rules
- **Conflict resolution** by rule priority (urgent rules fire first)
- **Reasoning log** printed on screen and saved to `inference_log.txt`
- **"Why?" explanations** that trace any conclusion back to the user's facts
- **Unit tests** with `unittest`

## Run it
```bash
python expert_system.py                                    # interactive
python expert_system.py --facts fever,cough,body_aches,fatigue
python -m unittest -v                                      # tests
```

## Example
```
Step 1: R1: IF fever AND cough THEN respiratory_symptoms
Step 2: R4: IF respiratory_symptoms AND body_aches AND fatigue THEN possible_flu
Step 3: R9: IF possible_flu THEN advice_rest_and_fluids

why? > advice rest and fluids
- advice rest and fluids  <- rule R9: Flu: rest and keep hydrated
    - possible flu  <- rule R4: Respiratory symptoms plus aches and tiredness fit the flu
        - respiratory symptoms  <- rule R1: Fever with cough suggests a respiratory issue
            - fever  <- you told me this
            - cough  <- you told me this
        - body aches  <- you told me this
        - fatigue  <- you told me this
```

## Project structure
| File | Purpose |
|---|---|
| `expert_system.py` | Rule class, inference engine, logging, CLI |
| `rules.json` | Knowledge base (14 rules) |
| `test_expert_system.py` | Unit tests |

## Concepts demonstrated
Knowledge representation, forward chaining (data-driven reasoning), the recognise-act cycle, conflict resolution, explainable AI, separating data from logic, Python dataclasses, logging, argparse, unit testing.
