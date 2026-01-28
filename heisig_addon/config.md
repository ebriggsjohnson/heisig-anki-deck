### Heisig Mnemonic Generator Settings

- **llm_provider**: `"anthropic"` or `"openai"` — which LLM API to use for story generation.
- **api_key**: Your API key. Leave empty to disable LLM story generation.
- **model**: Model name (e.g. `"claude-sonnet-4-20250514"` for Anthropic, `"gpt-4o"` for OpenAI).
- **auto_generate_story**: If `true`, automatically call the LLM when the Character field loses focus. If `false`, only decomposition info is filled; use the 漢 button to generate a story manually.
- **character_field**: Name of the note field containing the character (default `"Character"`).
- **explanation_field**: Name of the note field to fill with the explanation (default `"Heisig Explanation"`).
