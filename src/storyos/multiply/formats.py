from __future__ import annotations

VIDEO_FORMATS = ("reel", "shorts", "youtube")
TEXT_FORMATS = ("journal", "linkedin", "blog", "newsletter", "podcast")
ALL_FORMATS = VIDEO_FORMATS + TEXT_FORMATS

FORMAT_LABELS = {
    "reel": "Instagram Reel (30–45s vertical)",
    "shorts": "YouTube Shorts (45–60s vertical, 9:16)",
    "youtube": "YouTube (5–8 minutes)",
    "journal": "Private journal reflection",
    "linkedin": "LinkedIn post",
    "blog": "Blog article draft",
    "newsletter": "Newsletter snippet",
    "podcast": "Podcast outline",
}

PUBLIC_FORMATS = frozenset({"linkedin", "blog", "newsletter", "podcast", "reel", "shorts", "youtube"})

FORMAT_GUIDANCE = {
    "reel": "Write a 30–45 second Instagram Reel script in vertical format.",
    "shorts": "Write a 45–60 second YouTube Shorts script in 9:16 vertical format.",
    "youtube": "Write a 5–8 minute YouTube script with natural pacing and breathing room.",
    "journal": "Write a private, reflective journal entry in the creator's voice.",
    "linkedin": "Write a LinkedIn post: hook line, short story, insight, optional question.",
    "blog": "Write a blog article draft with title, sections, and natural pacing.",
    "newsletter": "Write a personal newsletter note with one clear insight.",
    "podcast": "Write a podcast outline with segments and talking points.",
}
