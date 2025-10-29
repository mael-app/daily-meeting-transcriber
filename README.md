# 🎤 Daily Meeting Transcriber

Automatically transcribe and summarize your daily meetings using OpenAI's Whisper and GPT-4o mini.

## Features

- 🎧 Audio transcription with Whisper (supports mp3, m4a, wav, etc.)
- 🤖 AI-powered structured summary generation
- 📊 Token usage tracking
- 🇫🇷 Optimized for French meetings
- 📝 Clean Markdown output

## Prerequisites

- Python 3.7+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

## Installation

```bash
git clone https://github.com/your-username/daily-meeting-transcriber.git
cd daily-meeting-transcriber
```

No dependencies needed! Uses Python's standard library only.

## Usage

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

2. Run the script:
```bash
python daily_transcriber.py path/to/your/meeting.m4a
```

3. (Optional) Use a custom prompt file:
```bash
python daily_transcriber.py path/to/your/meeting.m4a custom_prompt.json
```

4. Get your summary:
```
Daily-29-10-25-HexaTeam.md
```

## Output Format

The generated Markdown includes:

- **Travail d'hier** - Previous day's accomplishments
- **Organisation de la journée** - Today's plans and priorities
- **Revues de code** - PRs to review
- **Points techniques discutés** - Technical discussions
- **Action Items** - Follow-up tasks

## Configuration

### Filename Pattern

Edit the filename pattern at the top of the script:

```python
OUTPUT_FILENAME_PATTERN = "Daily-{day}-{month}-{year}-HexaTeam.md"
```

### Custom Prompts

Create a `prompt.json` file to customize the AI behavior:

```json
{
  "system_prompt": "Tu es un assistant chargé de générer un résumé structuré en Markdown d'un compte rendu de daily meeting de développeurs.",
  "user_prompt": "Analyse le texte fourni...\n\nTranscript du daily meeting :\n---\n{transcript}\n---",
  "language": "fr"
}
```

**Configuration options:**
- `system_prompt`: Instructions for the AI (optional)
- `user_prompt`: Template for processing the transcript (optional, must include `{transcript}` placeholder)
- `language`: Whisper transcription language using [ISO-639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (optional, default: `fr`)

**Supported languages:** `en` (English), `es` (Spanish), `de` (German), `it` (Italian), `pt` (Portuguese), `nl` (Dutch), `ja` (Japanese), `zh` (Chinese), and [many more](https://platform.openai.com/docs/guides/speech-to-text).

The script looks for `prompt.json` by default, or you can specify a custom path:

```bash
python daily_transcriber.py meeting.m4a my_prompts.json
```

## Cost Estimation

- Whisper: ~$0.006 per minute
- GPT-4o mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

A typical 15-minute daily costs ~$0.10-0.15.

## License

MIT
