# Foundry Learn Chat

A small Python chat app based on the Microsoft Learn module
[Develop a generative AI chat app with Microsoft Foundry](https://learn.microsoft.com/en-us/training/modules/foundry-sdk/).

This is a follow-on exercise to my **Microsoft Certified: Azure AI Fundamentals (AI-901)** certification. The focus is the practical connection between a Foundry project, a deployed model, authentication, instructions, and a conversation in Python.

**Carlos Falconi · Learning project · October 2026**

## The example

The assistant answers questions about a fictional maintenance company, HarborWorks.
Its entire knowledge source is a short [operations FAQ](data/operations_faq.md).
For example:

- Who can approve a maintenance window?
- Which role did you just mention?
- What is the price of an urgent maintenance service?

The second question needs the previous conversation. The third asks for something
the FAQ does not contain, so the assistant should say that the information is
missing.

This is a model-backed chat app with context supplied in the prompt. There is no
search index, vector database, retrieval pipeline, or deployed agent in this exercise.

## How it works

```text
Question + FAQ instructions
          │
          ▼
Python app → AIProjectClient → get_openai_client()
                                 │
                                 ▼
                  Foundry Responses API
                  model = deployment name
                                 │
                                 ▼
                  Answer + token usage
                  + previous response ID
```

- **Microsoft Foundry** organizes the project and model deployment.
- **Azure Identity** uses Microsoft Entra ID through `DefaultAzureCredential`.
- **Azure AI Projects SDK** creates the project client.
- **OpenAI-compatible Responses API** submits messages to the deployed model.
- **Python** manages the chat loop, response IDs, and small checks.

The module covers both project clients and direct model endpoints. Its linked
exercise currently uses the Azure OpenAI endpoint directly. This adaptation uses
the **Foundry project endpoint** and `AIProjectClient.get_openai_client()` to make
that distinction explicit.

## Start with the notebook

[Open the walkthrough](notebooks/01_foundry_chat.ipynb) to follow the exercise in
short blocks. The notebook shows the SDK calls directly; `chat.py` packages the
same flow into a reusable command-line application.

The notebook makes **three real model requests** when its cloud cells run.
The standalone smoke test makes another three. Both consume the configured
Azure model's quota and may incur charges; they do not provision resources.

## Setup

Use Python 3.10 or newer and a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

For the command-line app alone, `requirements.txt` is enough.

In Azure:

1. Create or select a Microsoft Foundry project.
2. Deploy a text model that supports the Responses API. Choose an available
   small model and pay-per-token deployment for this exercise; check pricing and
   quota in the selected region.
3. Give the signed-in identity permission to invoke the model through the project.
   The project must be accessible to the identity used by the local Azure CLI.
4. Copy the **project endpoint** and the **exact deployment name** into `.env`.
5. Sign in with `az login`. If necessary, select the subscription containing
   the project with `az account set --subscription <subscription-id>`.

```dotenv
AZURE_AI_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
AZURE_AI_MODEL_DEPLOYMENT_NAME=your-model-deployment
MAX_OUTPUT_TOKENS=1200
MAX_CHAT_TURNS=10
REASONING_EFFORT=low
```

A model catalog name, an agent name, and a deployment name are not interchangeable.
The project endpoint is also different from an Azure OpenAI resource endpoint.

The example configuration is suitable for a reasoning model such as
`gpt-5-mini`: the output-token limit includes reasoning tokens, and
`REASONING_EFFORT=low` keeps the exercise small. Leave this setting empty for
models that do not support reasoning effort. Availability depends on the
subscription and region.

## Run it

Validate the local settings first; this does not contact Azure:

```bash
python chat.py --check-config
```

Ask one question:

```bash
python chat.py --question "Who can approve a maintenance window?"
```

Or start the chat:

```bash
python chat.py
```

Use `/reset` to drop the conversation reference, or `/quit` to leave. Resetting
the conversation does not reset the request count. A session allows at most
10 requests, with 1,000 characters per question and a configured output-token
limit. SDK retries are disabled so a failed request does not silently start more
requests.

The app sends the instructions on every call. It uses `previous_response_id`
to let the service connect the follow-up to the earlier exchange. History can
increase the number of input tokens billed on later requests.

## Check the behavior

```bash
python -m pytest -q
python smoke_test.py
```

The first command runs offline tests with a fake client and consumes no Azure
quota. The second calls the real deployment three times:

| Check | Expected behavior |
| --- | --- |
| Known policy | Identify the operations coordinator |
| Follow-up | Recall the role named in the previous answer |
| Missing information | State that the FAQ does not specify a price |

These are small deterministic text checks around nondeterministic model outputs,
not a comprehensive evaluation. A failed check should be reviewed, not relabeled
as a pass.

The smoke test writes [execution evidence](artifacts/README.md): answers, token
usage, latency, model identifier, SDK versions, and check results. It excludes
credentials, subscription IDs, authenticated endpoints, and arbitrary chat
history. Successful live execution is only claimed when an actual result has
been saved.

### Recorded Azure execution

On **12 October 2026**, the revised smoke test completed against an actual
**gpt-5-mini** deployment with Microsoft Entra authentication: **3/3 checks
passed, 1,420 total tokens**, and observed request latencies of 3.15–3.50 seconds.
The [JSON report](artifacts/cloud-smoke.json) contains the real answers and usage.

The first run passed two checks and abstained on a broadly worded follow-up.
That [initial failed check](artifacts/cloud-smoke-initial.json) is preserved;
the follow-up and instructions were clarified before the next run. Three
checks are only a small integration exercise, not a reliability benchmark.

The notebook was also executed end to end in a separate run: **three completed
requests and 1,174 total tokens**. Its saved outputs show the real answers, and
[notebook-execution.json](artifacts/notebook-execution.json) records the usage.

## Files

```text
chat.py                         # Configuration, SDK client, request, chat loop
smoke_test.py                   # Three real requests and a JSON evidence report
data/operations_faq.md          # Small fictional context
notebooks/01_foundry_chat.ipynb  # Step-by-step learning walkthrough
tests/test_chat.py              # Offline request and failure-handling tests
artifacts/                      # Sanitized execution evidence
.env.example                    # Configuration template; no credentials
```

## Scope and next steps

The FAQ is deliberately small. Sending it in every prompt makes the data flow
easy to inspect. A larger document collection would need a separate retrieval
design and evaluation.

The instructions ask the model to use only the FAQ, but this is not a security
boundary. The project does not establish robust prompt-injection protection,
production reliability, or business impact. It also does not train or fine-tune
a model.

Responses are stored by the service to support response-ID chaining. Use only
the fictional examples for this exercise. `/reset` clears the local reference;
it does not delete records from Azure. Review the service's retention settings
and remove only the dedicated exercise resources when finished.

A useful next step would be a larger evaluation set, then a comparison between
prompt-provided context and a real retrieval pipeline.

## Sources and attribution

- [Microsoft Learn module](https://learn.microsoft.com/en-us/training/modules/foundry-sdk/)
- [Official hands-on exercise](https://microsoftlearning.github.io/mslearn-ai-studio/Instructions/Exercises/03-foundry-sdk.html)
- [AIProjectClient reference](https://learn.microsoft.com/en-us/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient?view=azure-python)
- [Responses API in the learning module](https://learn.microsoft.com/en-us/training/modules/foundry-sdk/04-responses-api)

The exercise structure and SDK patterns are based on Microsoft Learn. The
HarborWorks scenario, app organization, notebook explanation, and checks are
adaptations for this repository. This is a personal learning project, not an
official Microsoft sample or an endorsement. Original repository code is
available under the [MIT License](LICENSE).
