

# AEGIS — Research Scope



## Project

AEGIS: Explainable Security Gateway and Evaluation Lab for AI Agents



## Version

0.1 — Initial research scope



## Problem

AI agents may consume untrusted content containing instructions

that attempt to redirect the agent away from its legitimate task.

If the agent has access to tools, this can lead to unauthorized actions.



## Research Question

How does policy enforcement affect attack success, legitimate

task completion, false-positive rate, and execution overhead

in a controlled tool-using agent?



## Initial Hypothesis

A policy-enforcement gateway can reduce unauthorized tool actions

while preserving legitimate task completion. This must be verified

through controlled experiments.



## Planned Comparisons

1. Baseline agent without additional defenses.

2. Rules-based input filtering.

3. Policy enforcement at the tool-execution boundary.



## Initial Test Dimensions

- Benign versus adversarial scenarios

- Direct versus indirect instructions

- English, Hindi, Marathi, and code-mixed examples

- Read-only versus sensitive simulated tool actions

- Attack success versus legitimate task completion



## Safety Boundaries

- Use synthetic data and simulated tools.

- Do not connect real email, financial, or personal accounts.

- Do not execute commands supplied by untrusted webpages.

- Do not allow the agent to access arbitrary local files.

- Keep all attack testing inside the controlled environment.



## Evaluation Metrics

- Attack success rate

- Unauthorized tool-action rate

- Legitimate task completion rate

- False-positive rate

- Added execution latency



## Research Integrity

- Compare against existing work before claiming novelty.

- Record dataset sources, licenses, and scenario labels.

- Keep evaluation cases separate from any training data.

- Report negative results and limitations.

- Never invent performance numbers.



## Scope Constraints

- Solo developer

- Six-week target

- Python 3.12

- Laptop and free resources

- No paid API required for the initial benchmark



## Current Status

Research scope drafted; literature review and novelty validation

remain in progress.



