

# AEGIS — Competitor and Literature Audit



## Audit date

2026-10-15



## Objective

Identify existing agent-security benchmarks, enforcement

systems, and red-team tools before making novelty claims.



## 1. AgentDojo

Repository:

https://github.com/ethz-spylab/agentdojo



Contribution:

- Evaluates prompt-injection attacks against LLM agents.

- Provides agent tasks, attack strategies, and defense comparisons.

- Uses task outcomes to evaluate attack and defense performance.



Implication for AEGIS:

Use established evaluation principles and compare against a

simple baseline. Do not present a generic agent benchmark as novel.



## 2. Agent Policy Gateway

Repository:

https://github.com/howardhsieh/agent-policy-gateway



Contribution to investigate:

- Policy enforcement at the tool-call boundary.

- Information-flow and taint tracking.

- Audit logging and benchmark comparisons.



Implication for AEGIS:

A gateway, policy file, or audit log is not sufficient evidence

of novelty. Inspect implementation, documentation, tests, and license.



## 3. Microsoft PyRIT

Repository:

https://github.com/microsoft/PyRIT



Contribution:

- Framework for automated red teaming of generative AI systems.

- Supports attack orchestration and evaluation workflows.



Implication for AEGIS:

Keep the MVP focused on agent action enforcement and controlled

evaluation rather than recreating a general red-team framework.



## 4. BrowseSafe++

Paper:

https://arxiv.org/abs/2610.17457



Contribution to investigate:

- Paired clean and attacked webpages.

- Multiple webpage representations and browser views.

- Text and screenshot prompt-injection detection.

- Multilingual and adaptive attack evaluation.



Implication for AEGIS:

Inspect language coverage, data construction, metrics, and

artifacts before proposing a multilingual benchmark contribution.



## 5. OWASP GenAI Security

Reference:

https://genai.owasp.org/llm-top-10/



Relevant risks:

- Prompt injection.

- Excessive agency.

- Sensitive information disclosure.

- Insecure tool and plugin behavior.



Implication for AEGIS:

Use a documented threat model and enforce least privilege.



## Preliminary research hypothesis

A policy-enforcement gateway may reduce unauthorized tool actions

while preserving legitimate task completion across controlled

indirect prompt-injection scenarios.



This is a hypothesis, not an established result.



## Questions requiring verification

1. What exact tasks, attack types, and defenses does each project cover?

2. Which languages are included, and how are examples labeled?

3. Are there paired benign controls for each adversarial scenario?

4. How are attack success and legitimate task completion defined?

5. Are the datasets and implementations reusable under their licenses?

6. Does an existing project already evaluate the proposed combination?

7. What specific research contribution remains after this comparison?



## Preliminary decision

Continue with AEGIS as a policy-enforcement and evaluation

prototype. Do not claim a novel defense or first-of-its-kind

multilingual benchmark until the questions above are investigated.



## Audit status

Initial source inventory completed.

Detailed implementation and dataset comparison pending.



