

\# AEGIS — Research Gap Matrix



\## Research decision

Build a reproducible evaluation prototype for comparing

AI-agent security defenses on matched multilingual scenarios.



\## Existing work



| Project | Existing contribution | AEGIS differentiation to test |

| --- | --- | --- |

| AgentDojo | Agent tasks, attacks, defense evaluation | Matched language variants and tool-action outcomes |

| Agent Policy Gateway | Tool policies, taint tracking, audit logs | Controlled multilingual policy evaluation |

| PyRIT | General-purpose AI red teaming | Small reproducible action-level benchmark |

| BrowseSafe++ | Multilingual browser injection detection | Comparison of downstream enforcement outcomes |



\## Research question

Do semantically matched indirect prompt-injection scenarios

produce different unauthorized tool-action outcomes when

expressed in English, Hindi, Marathi, and code-mixed text?



\## Proposed configurations

A. No additional defense

B. Rules-based content filtering

C. Deterministic tool-execution policy enforcement



\## Experimental design

\- Use synthetic tools and synthetic data.

\- Create paired benign and adversarial scenarios.

\- Keep the intended user task constant across language variants.

\- Keep the malicious objective constant across variants.

\- Evaluate every configuration using the same scenario IDs.

\- Separate detection outcomes from actual action execution.

\- Record attempted and executed tool actions.

\- Report legitimate-task failures and false-positive blocks.

\- Record any translation ambiguity or semantic mismatch.



\## Minimum viable experiment

\- 5 distinct base attack scenarios

\- 4 language variants per scenario

\- 5 paired benign controls

\- 3 defense configurations

\- At least 75 scenario-configuration evaluations



The minimum is a pilot, not evidence of broad generalization.



\## Metrics

1\. Attack success rate

2\. Unauthorized tool-action rate

3\. Legitimate task completion rate

4\. False-positive block rate

5\. Execution overhead



\## Research limitations

\- The gateway itself is not novel.

\- Multilingual prompt-injection testing is not novel by itself.

\- A deterministic simulator does not establish LLM vulnerability.

\- An LLM-backed experiment is required to make claims about

&#x20; real model behavior.

\- A small dataset cannot establish broad multilingual robustness.

\- No improvement or publication outcome is guaranteed.



\## Phase 0 decision

Proceed with the controlled pilot design.



Before reporting research findings, validate scenario labels,

language equivalence, and evaluation scoring.



\## Status

MVP research design provisionally approved.

Implementation and experimental validation pending.



