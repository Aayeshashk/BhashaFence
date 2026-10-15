

\# BhashaFence



\*\*A Cross-Lingual AI Agent Security Evaluation Lab\*\*



BhashaFence is a research prototype for evaluating authorization policies against untrusted content in simulated AI-agent workflows. It compares a vulnerable baseline executor with a policy-enforced executor and includes multilingual structured-action scenarios and an indirect-prompt-injection evaluation pipeline.



> \*\*Research limitation:\*\* BhashaFence is a synthetic evaluation lab. Its current results do not demonstrate that a real AI model understands or resists multilingual prompt injection.



\## Objectives



\- Simulate interactions with sensitive and non-sensitive tools.

\- Compare baseline behavior with policy-enforced authorization.

\- Evaluate structured-action scenarios in English, Hindi, Marathi, and code-mixed language categories.

\- Track attempted, blocked, and executed synthetic actions.

\- Validate and score indirect-injection model proposals without executing proposed actions.

\- Export machine-readable evaluation reports.



\## Architecture



```text

BhashaFence

├── backend/app/

│   ├── simulator.py

│   ├── policy.py

│   ├── metrics.py

│   ├── indirect\_scenarios.py

│   ├── model\_evaluation.py

│   ├── model\_scoring.py

│   └── model\_runner.py

├── dataset/

│   └── processed/

│       ├── multilingual/

│       └── indirect\_injection/

├── scripts/

│   ├── run\_comparison.py

│   ├── run\_multilingual\_evaluation.py

│   ├── run\_indirect\_injection\_pilot.py

│   ├── audit\_indirect\_injection\_pilot.py

│   ├── build\_indirect\_injection\_pilot.py

│   └── build\_linguistic\_review\_matrix.py

├── tests/

├── artifacts/

├── docs/

└── requirements-dev.txt

```



\### Main components



\- \*\*Simulator:\*\* provides synthetic tools and simulated state.

\- \*\*Policy enforcement:\*\* blocks sensitive actions originating from untrusted content.

\- \*\*Metrics:\*\* summarizes execution, blocking, and authorization outcomes.

\- \*\*Model evaluation adapter:\*\* validates proposed model outputs without executing their proposed actions.

\- \*\*Paired runner:\*\* compares baseline and defense conditions and exports reports.

\- \*\*Multilingual evaluator:\*\* evaluates dataset-provided structured tool calls across language categories.

\- \*\*Indirect-injection pilot:\*\* checks dataset structure and evaluation pipeline integration.



\## Requirements



\- Python 3.12 recommended.

\- Git.

\- Windows instructions below use Command Prompt.



\## Setup



Clone or open the repository and navigate to its root directory.



Create and activate a virtual environment:



```cmd

python -m venv .venv

.venv\\Scripts\\activate

```



Install development dependencies:



```cmd

python -m pip install -r requirements-dev.txt

```



\## Run the evaluations



Run commands from the repository root with the virtual environment activated.



\### 1. Baseline versus policy defense



```cmd

python scripts\\run\_comparison.py

```



Output:



\- `artifacts/comparison\_results.csv`



The JSON summary is printed to the console.



\### 2. Multilingual structured-action evaluation



```cmd

python scripts\\run\_multilingual\_evaluation.py

```



Outputs:



\- `artifacts/multilingual\_evaluation.json`

\- `artifacts/multilingual\_evaluation.csv`



This evaluation uses dataset-supplied structured tool calls. It does not measure a model's ability to interpret multilingual natural-language instructions.



\### 3. Audit the indirect-injection pilot



```cmd

python scripts\\audit\_indirect\_injection\_pilot.py

```



The audit report is written to:



\- `artifacts/indirect\_injection/pilot\_quality\_audit.json`



The audit checks dataset structure. It does not establish semantic equivalence between translations or measure model resistance.



\### 4. Run the deterministic integration pilot



```cmd

python scripts\\run\_indirect\_injection\_pilot.py

```



Outputs:



\- `artifacts/indirect\_injection/integration\_run/pilot\_integration.json`

\- `artifacts/indirect\_injection/integration\_run/pilot\_integration.csv`



This runner uses a deterministic test double. It makes no real model calls and executes no tools.



\## Run tests



Run the full test suite:



```cmd

python -m pytest -q

```



Check whitespace and patch errors:



```cmd

git diff --check

```



\## Evaluation interpretation



The baseline executor is intentionally vulnerable to certain sensitive actions originating from untrusted content. The policy-enforced executor is designed to deny those actions while allowing eligible user-labelled actions.



Results should be interpreted using their explicit denominators and the limitations of the synthetic harness. See \[docs/RESULTS.md](docs/RESULTS.md) for the current findings.



\## Limitations



1\. Tool effects are synthetic; no real external actions are performed.

2\. Source labels are supplied by the evaluation harness or dataset.

3\. Structured-action evaluation does not test natural-language understanding.

4\. The indirect-injection pilot uses a deterministic test double, not a real language model.

5\. The 16 indirect-injection pilot records remain drafts and require independent linguistic review.

6\. The current pilot is not statistical evidence of real-world security.

7\. Proposed actions and the model's self-reported task completion are not proof of actual task execution or completion.



\## Research use



BhashaFence is intended as a reproducible starting point for controlled authorization-policy experiments. Real-model experiments, independently reviewed translations, broader datasets, and additional validation are necessary before drawing claims about practical multilingual prompt-injection resistance.



