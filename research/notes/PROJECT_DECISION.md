

\# Project Decision — BhashaFence



\## Working title

BhashaFence: Cross-Lingual AI Agent Security Evaluation Lab



\## Repository location

E:\\AEGIS



\## Why the project direction changed

Existing work already covers pre-execution agent firewalls,

policy enforcement, taint tracking, audit trails, and multilingual

prompt-injection detection.



Relevant references:

\- AEGIS paper: https://arxiv.org/abs/2603.12621

\- Agent Policy Gateway:

&#x20; https://github.com/howardhsieh/agent-policy-gateway

\- AgentDojo:

&#x20; https://github.com/ethz-spylab/agentdojo

\- BrowseSafe++:

&#x20; https://github.com/perplexityai/browsesafe-plus-plus



\## Proposed product

A reproducible evaluation lab for studying how language variants

of controlled indirect prompt-injection scenarios affect tool

authorization, legitimate task completion, and policy outcomes.



\## Proposed comparisons

1\. Agent without additional defense.

2\. Rules-based content filtering.

3\. Deterministic tool-execution authorization.



\## Core measurements

\- Unauthorized tool actions

\- Legitimate task completion

\- False-positive blocks

\- Policy decisions and explanations

\- Execution overhead



\## Scope

\- Solo development

\- Four to six weeks

\- Python 3.12

\- Laptop and free resources

\- Synthetic tools and data for the initial implementation

\- No paid API required for the initial pilot



\## Research integrity

Do not claim novelty based on the project name, dashboard,

multilingual support, or policy enforcement alone.



Review existing implementations, datasets, and licenses.

Document the precise difference between this prototype and

existing work before claiming a research contribution.



\## Decision status

Revised direction proposed.

Final research-gap validation remains pending.

Implementation has not started.



