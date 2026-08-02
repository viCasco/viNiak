import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
CHANNEL_HANDLE = "@viNiakOficial"
MAX_RESULTS = 12
OUTPUT_FILE = Path("data/youtube-videos.json")


def get_json(endpoint: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Realiza una petición GET a YouTube Data API y devuelve el JSON."""

    query = urllib.parse.urlencode(parameters)
    url = f"{YOUTUBE_API_BASE}/{endpoint}?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "viNiak-Website-Updater/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"YouTube API respondió con HTTP {error.code}: {body}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"No se pudo conectar con YouTube API: {error.reason}"
        ) from error


def choose_thumbnail(thumbnails: dict[str, Any]) -> str:
    """Selecciona la miniatura disponible de mayor calidad."""

    priorities = ("maxres", "standard", "high", "medium", "default")

    for quality in priorities:
        thumbnail = thumbnails.get(quality)

        if thumbnail and thumbnail.get("url"):
            return str(thumbnail["url"])

    return ""


def main() -> None:
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()

    if not api_key:
        print(
            "ERROR: no está definida la variable YOUTUBE_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 1. Localizar el canal mediante su handle.
    channel_response = get_json(
        "channels",
        {
            "part": "snippet,contentDetails",
            "forHandle": CHANNEL_HANDLE,
            "key": api_key,
        },
    )

    channels = channel_response.get("items", [])

    if not channels:
        print(
            f"ERROR: no se encontró el canal {CHANNEL_HANDLE}.",
            file=sys.stderr,
        )
        sys.exit(1)

    channel = channels[0]
    channel_id = channel["id"]
    channel_title = channel["snippet"]["title"]
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. Leer los últimos vídeos de la lista de subidas.
    videos_response = get_json(
        "playlistItems",
        {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": MAX_RESULTS,
            "key": api_key,
        },
    )

    videos: list[dict[str, Any]] = []

    for item in videos_response.get("items", []):
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        video_id = content_details.get("videoId")

        if not video_id:
            video_id = (
                snippet.get("resourceId", {})
                .get("videoId")
            )

        title = snippet.get("title", "").strip()

        # Ignorar elementos eliminados o privados.
        if (
            not video_id
            or title in {"Deleted video", "Private video"}
        ):
            continue

        thumbnails = snippet.get("thumbnails", {})

        videos.append(
            {
                "id": video_id,
                "title": title,
                "description": snippet.get("description", "").strip(),
                "publishedAt": content_details.get(
                    "videoPublishedAt",
                    snippet.get("publishedAt", ""),
                ),
                "thumbnail": choose_thumbnail(thumbnails),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "embedUrl": f"https://www.youtube-nocookie.com/embed/{video_id}",
            }
        )

    output = {
        "channel": {
            "id": channel_id,
            "handle": CHANNEL_HANDLE,
            "title": channel_title,
            "url": f"https://www.youtube.com/{CHANNEL_HANDLE}",
        },
        "total": len(videos),
        "videos": videos,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"Guardados {len(videos)} vídeos de "
        f"{channel_title} en {OUTPUT_FILE}."
    )


if __name__ == "__main__":
    main()