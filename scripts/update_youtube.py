import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

PLAYLIST_ID = "PLjIP8G7ecrCuZ4p-fSNJBt8i9HLUetOzG"
PLAYLIST_URL = (
    "https://www.youtube.com/playlist"
    f"?list={PLAYLIST_ID}"
)

OUTPUT_FILE = Path("data/youtube-videos.json")

# YouTube permite hasta 50 resultados por petición.
MAX_RESULTS_PER_REQUEST = 50


def get_json(
    endpoint: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """
    Realiza una petición GET a YouTube Data API
    y devuelve la respuesta como diccionario.
    """

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
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except urllib.error.HTTPError as error:
        body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"YouTube API respondió con HTTP "
            f"{error.code}: {body}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "No se pudo conectar con YouTube API: "
            f"{error.reason}"
        ) from error


def choose_thumbnail(
    thumbnails: dict[str, Any],
) -> str:
    """
    Selecciona la miniatura disponible de mayor calidad.
    """

    priorities = (
        "maxres",
        "standard",
        "high",
        "medium",
        "default",
    )

    for quality in priorities:
        thumbnail = thumbnails.get(quality)

        if thumbnail and thumbnail.get("url"):
            return str(thumbnail["url"])

    return ""


def get_playlist_information(
    api_key: str,
) -> dict[str, Any]:
    """
    Recupera el título, descripción y canal propietario
    de la playlist.
    """

    response = get_json(
        "playlists",
        {
            "part": "snippet,contentDetails",
            "id": PLAYLIST_ID,
            "key": api_key,
        },
    )

    items = response.get("items", [])

    if not items:
        raise RuntimeError(
            "No se encontró la playlist o no es pública: "
            f"{PLAYLIST_ID}"
        )

    item = items[0]
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})

    return {
        "id": PLAYLIST_ID,
        "title": snippet.get("title", ""),
        "description": snippet.get(
            "description",
            "",
        ),
        "channelId": snippet.get(
            "channelId",
            "",
        ),
        "channelTitle": snippet.get(
            "channelTitle",
            "",
        ),
        "thumbnail": choose_thumbnail(
            snippet.get("thumbnails", {}),
        ),
        "itemCount": content_details.get(
            "itemCount",
            0,
        ),
        "url": PLAYLIST_URL,
    }


def get_playlist_videos(
    api_key: str,
) -> list[dict[str, Any]]:
    """
    Recupera todos los vídeos de la playlist,
    respetando su orden.
    """

    videos: list[dict[str, Any]] = []
    next_page_token = ""

    while True:
        parameters: dict[str, Any] = {
            "part": "snippet,contentDetails,status",
            "playlistId": PLAYLIST_ID,
            "maxResults": MAX_RESULTS_PER_REQUEST,
            "key": api_key,
        }

        if next_page_token:
            parameters["pageToken"] = next_page_token

        response = get_json(
            "playlistItems",
            parameters,
        )

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            content_details = item.get(
                "contentDetails",
                {},
            )
            status = item.get("status", {})

            title = str(
                snippet.get("title", "")
            ).strip()

            video_id = content_details.get(
                "videoId"
            )

            if not video_id:
                video_id = (
                    snippet
                    .get("resourceId", {})
                    .get("videoId")
                )

            privacy_status = status.get(
                "privacyStatus",
                "",
            )

            # Ignorar vídeos eliminados, privados
            # o elementos que no tengan ID válido.
            if (
                not video_id
                or title in {
                    "Deleted video",
                    "Private video",
                }
                or privacy_status
                in {"private", "privacyStatusUnspecified"}
            ):
                continue

            position = snippet.get(
                "position",
                len(videos),
            )

            videos.append(
                {
                    "id": video_id,
                    "position": position,
                    "title": title,
                    "description": str(
                        snippet.get(
                            "description",
                            "",
                        )
                    ).strip(),
                    "publishedAt": (
                        content_details.get(
                            "videoPublishedAt"
                        )
                        or snippet.get(
                            "publishedAt",
                            "",
                        )
                    ),
                    "thumbnail": choose_thumbnail(
                        snippet.get(
                            "thumbnails",
                            {},
                        )
                    ),
                    "url": (
                        "https://www.youtube.com/"
                        f"watch?v={video_id}"
                        f"&list={PLAYLIST_ID}"
                    ),
                    "directUrl": (
                        "https://www.youtube.com/"
                        f"watch?v={video_id}"
                    ),
                    "embedUrl": (
                        "https://www.youtube-nocookie.com/"
                        f"embed/{video_id}"
                    ),
                }
            )

        next_page_token = response.get(
            "nextPageToken",
            "",
        )

        if not next_page_token:
            break

    videos.sort(
        key=lambda video: video["position"]
    )

    return videos


def main() -> None:
    api_key = os.environ.get(
        "YOUTUBE_API_KEY",
        "",
    ).strip()

    if not api_key:
        print(
            "ERROR: no está definida la variable "
            "YOUTUBE_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        playlist = get_playlist_information(
            api_key
        )

        videos = get_playlist_videos(
            api_key
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    output = {
        "updatedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "playlist": playlist,
        "total": len(videos),
        "videos": videos,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        f"Guardados {len(videos)} vídeos "
        f"de la playlist «{playlist['title']}» "
        f"en {OUTPUT_FILE}."
    )


if __name__ == "__main__":
    main()