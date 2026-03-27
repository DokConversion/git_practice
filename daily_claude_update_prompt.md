# Daily Claude Code Briefing – marc@winestreet-media.de

## Context
Performance Marketing Agency, VSL focus (Meta/YouTube/Google Ads, Direct Response).

## Steps
1. Search: "Claude Code" changelog/updates/skills (last 24h) – Anthropic blog, GitHub, X/Twitter
2. YouTube: search "Claude Code" – top 3 by views (last 7 days), transcribe key insights (Whisper)
3. Instagram: scrape hashtag #claudecode + #claudeai via Apify Instagram Hashtag Scraper – top 3 posts by likes/comments, transcribe Reels if video (Whisper)
4. Filter all sources for VSL/performance marketing relevance
5. Send email

## Email
**To:** marc@winestreet-media.de
**Subject:** Claude Code Update – [DATE]

```
### Updates (max 3 bullets)
### Neuer Skill/Befehl (falls vorhanden)
### VSL Use Case des Tages (1 konkretes Beispiel)
### Top Content (YouTube + Instagram – je 1 Satz Insight + Link)
### Quick Tip (1 Satz)
```

Keep each section max 2-3 sentences. No filler. German language.

## Tools needed
- Apify API key → env: APIFY_API_KEY (actor: apify/instagram-hashtag-scraper)
- YouTube Data API key → env: YOUTUBE_API_KEY
- OpenAI Whisper API key → env: OPENAI_API_KEY (for transcription)
- SMTP credentials → env: SMTP_HOST, SMTP_USER, SMTP_PASS
