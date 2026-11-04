# Text analysis

Turns a customer message into sentiment, topics, and a one-line summary using
Gemini. Configure root `.env` as described in the [setup guide](../../README.md),
start FastAPI, and try `POST /analyze` in http://127.0.0.1:8000/docs.

Request:

```json
{"text": "The onboarding call helped, but the dashboard is slow and confusing."}
```

Example response (wording can vary):

```json
{
  "sentiment": "mixed",
  "topics": ["onboarding", "dashboard performance", "usability"],
  "summary": "Helpful onboarding, but the dashboard is slow and confusing."
}
```

## Maintenance and debugging

- `service.py` contains the prompt/provider call; `schemas.py` defines the contract.
- Uses `GEMINI_API_KEY` and `GEMINI_MODEL`, Google's native SDK, JSON schema mode,
  and Pydantic validation. Sentiment: positive, neutral, negative, or mixed.
- Invalid requests return 422. Malformed/invalid model output gets one retry,
  then 502. Provider errors return 502, timeouts 504, and missing key,
  connection issues or rate limits 503. Each call has a 30-second timeout;
  SDK automatic retries are disabled.
- A configured model must support structured output and have available quota.
  `GEMINI_MODEL` does not change the RAG embedding model.

Offline checks: `python -m unittest src.llm.test_analysis`.
