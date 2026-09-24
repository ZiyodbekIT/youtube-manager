import os

from dotenv import load_dotenv
from googleapiclient.discovery import build


load_dotenv()

YOUTUBE_API_KEY = os.getenv(
    "YOUTUBE_API_KEY"
)


# ==========================================
# YOUTUBE API
# ==========================================

def get_youtube():

    if not YOUTUBE_API_KEY:

        raise ValueError(
            "YOUTUBE_API_KEY topilmadi. "
            ".env faylini tekshiring."
        )

    return build(
        "youtube",
        "v3",
        developerKey=YOUTUBE_API_KEY
    )


# ==========================================
# CHANNEL INFO
# ==========================================

def get_channel_info(channel_id):

    channel_id = channel_id.strip()

    if not channel_id:
        return None


    youtube = get_youtube()


    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )


    response = request.execute()


    items = response.get(
        "items",
        []
    )


    if not items:
        return None


    channel = items[0]


    snippet = channel.get(
        "snippet",
        {}
    )


    statistics = channel.get(
        "statistics",
        {}
    )


    thumbnails = snippet.get(
        "thumbnails",
        {}
    )


    thumbnail = ""


    if "high" in thumbnails:

        thumbnail = (
            thumbnails["high"]
            .get("url", "")
        )

    elif "medium" in thumbnails:

        thumbnail = (
            thumbnails["medium"]
            .get("url", "")
        )

    elif "default" in thumbnails:

        thumbnail = (
            thumbnails["default"]
            .get("url", "")
        )


    return {

        "id":
            channel.get(
                "id",
                channel_id
            ),

        "title":
            snippet.get(
                "title",
                "Noma'lum kanal"
            ),

        "description":
            snippet.get(
                "description",
                ""
            ),

        "thumbnail":
            thumbnail,

        "custom_url":
            snippet.get(
                "customUrl",
                ""
            ),

        "country":
            snippet.get(
                "country",
                ""
            ),

        "published_at":
            snippet.get(
                "publishedAt",
                ""
            ),

        "subscribers":
            statistics.get(
                "subscriberCount",
                "Yashirilgan"
            ),

        "views":
            statistics.get(
                "viewCount",
                "0"
            ),

        "videos":
            statistics.get(
                "videoCount",
                "0"
            ),
    }


# ==========================================
# CHANNEL UPLOADS PLAYLIST
# ==========================================

def get_uploads_playlist_id(
    channel_id
):

    channel_id = channel_id.strip()


    if not channel_id:
        return None


    youtube = get_youtube()


    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )


    response = request.execute()


    items = response.get(
        "items",
        []
    )


    if not items:
        return None


    content_details = (
        items[0]
        .get(
            "contentDetails",
            {}
        )
    )


    related_playlists = (
        content_details
        .get(
            "relatedPlaylists",
            {}
        )
    )


    return related_playlists.get(
        "uploads"
    )


# ==========================================
# LATEST VIDEOS
# ==========================================

def get_latest_videos(
    channel_id,
    max_results=8
):

    """
    Kanalning eng so'nggi videolarini oladi.

    Har bir video uchun:

    - ID
    - nomi
    - thumbnail
    - ko'rishlar
    - layklar
    - izohlar
    - yuklangan vaqt

    qaytariladi.
    """


    if not channel_id:
        return []


    try:

        max_results = int(
            max_results
        )

    except (
        TypeError,
        ValueError
    ):

        max_results = 8


    # YouTube API bir so'rovda
    # maksimum 50 ta natija beradi.

    max_results = max(
        1,
        min(
            max_results,
            50
        )
    )


    youtube = get_youtube()


    # --------------------------------------
    # UPLOADS PLAYLIST ID
    # --------------------------------------

    uploads_playlist_id = (
        get_uploads_playlist_id(
            channel_id
        )
    )


    if not uploads_playlist_id:
        return []


    # --------------------------------------
    # SO'NGGI VIDEOLARNI OLISH
    # --------------------------------------

    playlist_request = (
        youtube
        .playlistItems()
        .list(
            part="snippet,contentDetails",
            playlistId=(
                uploads_playlist_id
            ),
            maxResults=max_results
        )
    )


    playlist_response = (
        playlist_request.execute()
    )


    playlist_items = (
        playlist_response.get(
            "items",
            []
        )
    )


    if not playlist_items:
        return []


    # --------------------------------------
    # VIDEO ID'LAR
    # --------------------------------------

    video_ids = []


    for item in playlist_items:

        content_details = (
            item.get(
                "contentDetails",
                {}
            )
        )


        video_id = (
            content_details.get(
                "videoId"
            )
        )


        if not video_id:

            snippet = item.get(
                "snippet",
                {}
            )


            resource_id = (
                snippet.get(
                    "resourceId",
                    {}
                )
            )


            video_id = (
                resource_id.get(
                    "videoId"
                )
            )


        if video_id:

            video_ids.append(
                video_id
            )


    if not video_ids:
        return []


    # --------------------------------------
    # VIDEO STATISTICS
    # --------------------------------------

    videos_request = (
        youtube
        .videos()
        .list(
            part="snippet,statistics",
            id=",".join(
                video_ids
            )
        )
    )


    videos_response = (
        videos_request.execute()
    )


    video_items = (
        videos_response.get(
            "items",
            []
        )
    )


    # --------------------------------------
    # VIDEO MA'LUMOTLARINI TAYYORLASH
    # --------------------------------------

    videos_by_id = {}


    for video in video_items:

        video_id = video.get(
            "id"
        )


        if not video_id:
            continue


        snippet = video.get(
            "snippet",
            {}
        )


        statistics = video.get(
            "statistics",
            {}
        )


        thumbnails = snippet.get(
            "thumbnails",
            {}
        )


        thumbnail = ""


        if "maxres" in thumbnails:

            thumbnail = (
                thumbnails["maxres"]
                .get(
                    "url",
                    ""
                )
            )

        elif "standard" in thumbnails:

            thumbnail = (
                thumbnails["standard"]
                .get(
                    "url",
                    ""
                )
            )

        elif "high" in thumbnails:

            thumbnail = (
                thumbnails["high"]
                .get(
                    "url",
                    ""
                )
            )

        elif "medium" in thumbnails:

            thumbnail = (
                thumbnails["medium"]
                .get(
                    "url",
                    ""
                )
            )

        elif "default" in thumbnails:

            thumbnail = (
                thumbnails["default"]
                .get(
                    "url",
                    ""
                )
            )


        videos_by_id[
            video_id
        ] = {

            "id":
                video_id,

            "title":
                snippet.get(
                    "title",
                    "Nomsiz video"
                ),

            "description":
                snippet.get(
                    "description",
                    ""
                ),

            "thumbnail":
                thumbnail,

            "published_at":
                snippet.get(
                    "publishedAt",
                    ""
                ),

            "views":
                statistics.get(
                    "viewCount",
                    "0"
                ),

            "likes":
                statistics.get(
                    "likeCount",
                    "0"
                ),

            "comments":
                statistics.get(
                    "commentCount",
                    "0"
                ),
        }


    # --------------------------------------
    # TARTIBNI SAQLASH
    # --------------------------------------

    videos = []


    for video_id in video_ids:

        video_data = (
            videos_by_id.get(
                video_id
            )
        )


        if video_data:

            videos.append(
                video_data
            )


    return videos