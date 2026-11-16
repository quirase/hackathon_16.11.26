
"""
yt_transcript_parser.py

Turns a YouTube URL into a dictionary with two lists of the same length:
    {"word":      ["hello", "there", ...],
     "time_code": [0.0, 0.52, ...]}
    word       - every word of the transcript, in order
    time_code  - the time (in seconds) when the word at the same position is spoken

How it works:
    1. Try the youtube-transcript-api library first.
    2. If that fails (for example YouTube blocks our IP), use SerpApi instead.
       We have several SerpApi keys and take turns using them (key rotation).

Setup:
    pip install youtube-transcript-api serpapi
    (install "serpapi", NOT "google-search-results" - the two clash)

    Put the SerpApi keys in an environment variable, separated by commas:
        Mac/Linux:  export SERPAPI_KEYS="key1,key2,key3,key4,key5"
        Windows:    set SERPAPI_KEYS=key1,key2,key3,key4,key5
"""

import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

import serpapi
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


# ---------------------------------------------------------------------------
# Settings and key rotation
# ---------------------------------------------------------------------------

SERPAPI_KEYS = []
load_dotenv()

for key in os.environ.get("SERPAPI_KEYS", "").split(","):
    if key.strip() != "":
        SERPAPI_KEYS.append(key.strip())


# If a key stops working (no searches left, rate limit...) we skip it for 1 hour.
COOLDOWN = timedelta(hours=1)

# key -> the time when we are allowed to use it again
blocked_until = {}

# Which key we try next. It goes up by 1 every time, so the keys take turns.
next_key_index = 0


def get_next_key():
    """Return the next SerpApi key that is not on cooldown."""
    global next_key_index

    for _ in range(len(SERPAPI_KEYS)):
        key = SERPAPI_KEYS[next_key_index % len(SERPAPI_KEYS)]
        next_key_index += 1

        # Use the key if it was never blocked, or if its cooldown is over
        if key not in blocked_until or datetime.now() >= blocked_until[key]:
            return key

    raise RuntimeError("All SerpApi keys are used up or on cooldown.")


def block_key(key):
    """Put a key on cooldown so we stop using it for a while."""
    blocked_until[key] = datetime.now() + COOLDOWN


# ---------------------------------------------------------------------------
# Step 1: URL -> video id
# ---------------------------------------------------------------------------

def get_video_id(url):
    """
    Get the 11-character video id out of a YouTube link.
    Works for: youtube.com/watch?v=ID, youtu.be/ID, /shorts/ID, /embed/ID,
    /live/ID, or just the bare ID.
    """
    url = url.strip()

    # A video id is 11 letters, digits, "-" or "_" right after one of these
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)

    # Maybe the user gave us only the id
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    raise ValueError("Could not find a video id in: " + url)


# ---------------------------------------------------------------------------
# Step 2: get the transcript
# Both sources give us the same thing: a list of segments. A segment is a
# dictionary like {"text": "hello there", "start": 1.5, "end": 3.0}
# ---------------------------------------------------------------------------

def get_segments_from_youtube(video_id, language):
    """Get the transcript using youtube-transcript-api."""
    api = YouTubeTranscriptApi()
    fetched = None

    try:
        fetched = api.fetch(video_id, languages=[language])
    except NoTranscriptFound:
        # The language we wanted does not exist, so take the first one available
        for transcript in api.list(video_id):
            fetched = transcript.fetch()
            break
        if fetched is None:
            raise  # there is no transcript at all

    segments = []
    for piece in fetched:
        segments.append({
            "text": piece.text,
            "start": piece.start,
            "end": piece.start + piece.duration,
        })
    return segments


def get_segments_from_serpapi(video_id, language):
    """Get the transcript using SerpApi, rotating through our keys."""
    if len(SERPAPI_KEYS) == 0:
        raise RuntimeError("No SerpApi keys found. Set the SERPAPI_KEYS variable.")

    # Try each key at most once
    for _ in range(len(SERPAPI_KEYS)):
        key = get_next_key()
        client = serpapi.Client(api_key=key)

        try:
            results = client.search({
                "engine": "youtube_video_transcript",
                "v": video_id,
                "language_code": language,
            })
        except serpapi.HTTPError as error:
            # 401 = bad key, 403 = not allowed, 429 = out of searches / too many requests
            if error.status_code in (401, 403, 429):
                print("SerpApi key ending in " + key[-4:] + " failed, trying the next key...")
                block_key(key)
                continue  # go back to the top of the loop with a new key
            raise RuntimeError("SerpApi error: " + str(error.error))

        if "error" in results:
            raise RuntimeError("SerpApi error: " + str(results["error"]))

        # SerpApi gives times in milliseconds, so divide by 1000 to get seconds
        segments = []
        for item in results.get("transcript", []):
            segments.append({
                "text": item.get("snippet", ""),
                "start": item["start_ms"] / 1000,
                "end": item["end_ms"] / 1000,
            })

        if len(segments) == 0:
            raise RuntimeError("SerpApi returned an empty transcript.")
        return segments

    raise RuntimeError("All SerpApi keys failed.")


# ---------------------------------------------------------------------------
# Step 3: split into words and interpolate the time codes
# ---------------------------------------------------------------------------

def clean_text(text):
    """Remove [Music], >> and music notes, and fix symbols like &#39; and curly quotes"""
    text = re.sub(r"\[[^\]]*\]", " ", text)  # [Music], [Applause], ...
    text = text.replace(">>", " ")
    text = re.sub("[♪♫♬♩]", " ", text)  # music notes

    # Curly quotes and "…" -> normal ones, so "We’re" stays the English word "We're"
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("…", "...")
    text = text.replace("&#39;", "'")
    text = text.replace("&quot;", '"')
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")  # always last
    return text


def is_english_word(word):
    """
    True only if the word has at least one English letter (a-z) and contains
    nothing except English letters, digits and basic punctuation.
    So "We're" and "love," pass, but "♪", "—", "привіт" and "café" do not.
    """
    has_letter = re.search(r"[A-Za-z]", word) is not None
    only_allowed = re.fullmatch(r"[A-Za-z0-9'\".,!?;:()-]+", word) is not None
    return has_letter and only_allowed


def make_word_dict(segments):
    """
    Give every word its own time code using interpolation.

    Example: a segment starts at 10s and ends at 14s and has the words
    "I love python" (1 + 4 + 6 = 11 letters).
        "I"      starts at 10 + 4 * 0/11  = 10.00
        "love"   starts at 10 + 4 * 1/11  = 10.36
        "python" starts at 10 + 4 * 5/11  = 11.82
    Longer words take longer to say, so we split the time by number of letters.
    """
    all_words = []
    all_time_codes = []

    for i in range(len(segments)):
        segment = segments[i]
        words = clean_text(segment["text"]).split()
        if len(words) == 0:
            continue  # nothing to do for an empty segment

        start = segment["start"]
        end = segment["end"]

        # YouTube segments sometimes overlap. If this segment runs past the
        # start of the next one, cut it off there.
        if i + 1 < len(segments):
            next_start = segments[i + 1]["start"]
            if start < next_start < end:
                end = next_start

        duration = max(end - start, 0)
        total_letters = sum(len(word) for word in words)

        letters_so_far = 0
        for word in words:
            time_code = start + duration * letters_so_far / total_letters
            if is_english_word(word):
                all_words.append(word)
                all_time_codes.append(round(time_code, 3))
            letters_so_far += len(word)  # skipped words still take up time

    return {"word": all_words, "time_code": all_time_codes}


# ---------------------------------------------------------------------------
# The main function - this is the one you call from your site
# ---------------------------------------------------------------------------

def get_transcript(url, language="en"):
    """
    Input : YouTube URL (string) and an optional language code like "en"
    Output: (word_dict, full_text)
        word_dict = {'word': [...all words...], 'time_code': [...matching time codes...]}
        full_text = the complete cleaned transcript as one string
    """
    video_id = get_video_id(url)

    try:
        segments = get_segments_from_youtube(video_id, language)
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound) as error:
        # The video has no transcript, so SerpApi can't help either
        raise RuntimeError("No transcript for this video: " + type(error).__name__)
    except Exception as error:
        # Probably YouTube blocked us, so use SerpApi instead
        print("youtube-transcript-api failed (" + type(error).__name__ + "), using SerpApi...")
        segments = get_segments_from_serpapi(video_id, language)

    result = make_word_dict(segments)
    if len(result["word"]) == 0:
        raise RuntimeError("The transcript had no words.")

    # Keep the complete cleaned transcript as one string as well.
    full_text_parts = []
    for segment in segments:
        text = " ".join(clean_text(segment["text"]).split())
        if text:
            if text[-1] not in ".!?:;":
                text += "."
            full_text_parts.append(text)
    full_text = " ".join(full_text_parts)

    return result, full_text


# Runs only when you start this file directly (python yt_transcript_parser.py)
if __name__ == "__main__":
    link = input("YouTube URL: ")
    result, full_text = get_transcript(link)
    print(result["word"][:20])
    print(result["time_code"][:20])
    print("Total words:", len(result["word"]))
    print("Full text preview:", full_text[:100])