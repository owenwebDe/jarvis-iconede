"""Text processing helpers extracted from server.py."""
import re


def process_agent_response(response):
    """Helper to extract clean text from agent response."""
    text = ""
    if isinstance(response, str):
        text = response
    elif hasattr(response, 'output'):
        text = str(response.output)
    else:
        text = str(response)
    
    # Remove tool_outputs blocks
    text = re.sub(r"```tool_outputs.*?```", "", text, flags=re.DOTALL)
    # Remove <think>...</think> and <thinking>...</thinking> blocks (LLM reasoning traces)
    text = re.sub(r"<think(?:ing)?>.*?</think(?:ing)?>", "", text, flags=re.DOTALL)
    text = text.strip()
    return text


def clean_text_for_tts(text: str) -> str:
    """Strip URLs, links, and markdown formatting so TTS doesn't read the
    syntax aloud. Agents may freely emit markdown (headings, bullets, code
    fences, mermaid blocks) for the dashboard renderer; this function is
    the single point that flattens it for the audio pipeline.
    """
    if not text: return ""
    # Code blocks (triple backtick)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Links [text](url)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # URLs
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    # Headings # ## ### etc.
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold **text**
    text = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", text)
    # Italic *text*
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"\1", text)
    # Italic _text_
    text = re.sub(r"(?<![_\w])_([^_\n]+)_(?!_)", r"\1", text)
    # Strikethrough ~~text~~
    text = re.sub(r"~~([^~\n]+)~~", r"\1", text)
    # Underline __text__
    text = re.sub(r"__([^_\n]+)__", r"\1", text)
    # Highlight ==text==
    text = re.sub(r"==([^=\n]+)==", r"\1", text)
    # Superscript ^text^
    text = re.sub(r"\^([^\^\n]+)\^", r"\1", text)
    # Bullet lists
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Numbered lists
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    # Horizontal rules --- or ***
    text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Tables | col | col |
    text = re.sub(r"\|[^\|]+\|", "", text)
    # Emoji shortcodes :emoji:
    text = re.sub(r":\w+:", "", text)
    # HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Mermaid blocks
    text = re.sub(r"```mermaid[\s\S]*?```", "", text)
    # Excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove leading/trailing punctuation artifacts
    text = re.sub(r"^[,;:\-\s]+", "", text)
    text = re.sub(r"[,;:\-\s]+$", "", text)
    return text
