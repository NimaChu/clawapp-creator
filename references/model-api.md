# Platform Model API

Use this only when the app genuinely needs AI.

## Endpoint

```text
POST /api/llm/chat
```

## Request shape

```json
{
  "appId": "your-app-id",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello" }
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

## Response shape

Read:

```text
choices[0].message.content
```

## Usage rules

- Match `appId` to the app `id` or `slug` in `manifest.json`.
- Choose the right `modelCategory` at upload time.
- Do not store model API keys in client code.
- If the app does not need AI, keep `modelCategory` as `none` and do not call this endpoint.
