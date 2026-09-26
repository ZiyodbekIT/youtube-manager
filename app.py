import os
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    session,
    url_for,
    request,
    jsonify,
)

from database import db, User, Channel, ChannelSnapshot, Notification
from youtube import (
    get_channel_info,
    get_latest_videos,
    resolve_channel_id
)


load_dotenv()


app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "development-only-secret"
)

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///manager.db"
)

# Ba'zi hosting xizmatlari eski postgres:// formatini berishi mumkin.
# SQLAlchemy esa postgresql:// formatini kutadi.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False


db.init_app(app)


oauth = OAuth(app)

google = oauth.register(
    name="google",

    client_id=os.getenv(
        "GOOGLE_CLIENT_ID"
    ),

    client_secret=os.getenv(
        "GOOGLE_CLIENT_SECRET"
    ),

    server_metadata_url=(
        "https://accounts.google.com/"
        ".well-known/openid-configuration"
    ),

    client_kwargs={
        "scope": "openid email profile"
    }
)


with app.app_context():
    db.create_all()


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return db.session.get(
        User,
        user_id
    )


def format_number(value):
    try:
        number = int(value)
    except (ValueError, TypeError):
        return value

    if number >= 1_000_000_000:
        formatted = number / 1_000_000_000

        return (
            f"{formatted:.1f}"
            .rstrip("0")
            .rstrip(".")
            + "B"
        )

    if number >= 1_000_000:
        formatted = number / 1_000_000

        return (
            f"{formatted:.1f}"
            .rstrip("0")
            .rstrip(".")
            + "M"
        )

    if number >= 1_000:
        formatted = number / 1_000

        return (
            f"{formatted:.1f}"
            .rstrip("0")
            .rstrip(".")
            + "K"
        )

    return f"{number:,}"


app.jinja_env.filters[
    "compact_number"
] = format_number

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.context_processor
def inject_notification_count():
    user = get_current_user()

    if not user:
        return {"global_unread_count": 0}

    unread_count = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).count()

    return {
        "global_unread_count": unread_count
    }


@app.route("/")
def index():
    user = get_current_user()

    if not user:
        return render_template(
            "login.html"
        )

    channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    channel_data = []

    for saved_channel in channels:

        try:
            info = get_channel_info(
                saved_channel.youtube_channel_id
            )

            if info:
                channel_data.append(info)

        except Exception as error:
            print(
                "Kanal ma'lumotlarini "
                "olishda xato:",
                error
            )

            channel_data.append({
                "id": (
                    saved_channel
                    .youtube_channel_id
                ),
                "title": (
                    saved_channel.title
                ),
                "thumbnail": (
                    saved_channel.thumbnail
                ),
                "subscribers": "?",
                "views": "?",
                "videos": "?",
            })

    return render_template(
        "index.html",
        user=user,
        channels=channel_data
    )


@app.route(
    "/channel/<channel_id>"
)
def channel_dashboard(channel_id):
    user = get_current_user()

    if not user:
        return redirect(
            url_for("login")
        )

    saved_channel = (
        Channel.query.filter_by(
            user_id=user.id,
            youtube_channel_id=channel_id
        ).first()
    )

    if not saved_channel:
        flash(
            "Bu kanal sizning "
            "hisobingizga ulanmagan."
        )

        return redirect(
            url_for("index")
        )

    try:
        channel = get_channel_info(
            channel_id
        )

        if not channel:
            flash(
                "YouTube kanalini "
                "topib bo‘lmadi."
            )

            return redirect(
                url_for("index")
            )

        videos = get_latest_videos(
            channel_id,
            max_results=8
        )

    except Exception as error:
        print(
            "Kanal dashboard xatosi:",
            error
        )

        flash(
            "Kanal ma'lumotlarini "
            "yuklashda xatolik yuz berdi."
        )

        return redirect(
            url_for("index")
        )

    total_video_views = 0
    total_likes = 0
    total_comments = 0

    most_viewed_video = None

    for video in videos:

        try:
            video_views = int(
                video.get(
                    "views",
                    0
                )
            )
        except (ValueError, TypeError):
            video_views = 0

        try:
            video_likes = int(
                video.get(
                    "likes",
                    0
                )
            )
        except (ValueError, TypeError):
            video_likes = 0

        try:
            video_comments = int(
                video.get(
                    "comments",
                    0
                )
            )
        except (ValueError, TypeError):
            video_comments = 0

        total_video_views += video_views
        total_likes += video_likes
        total_comments += video_comments

        if most_viewed_video is None:
            most_viewed_video = video

        else:
            try:
                current_best = int(
                    most_viewed_video.get(
                        "views",
                        0
                    )
                )
            except (
                ValueError,
                TypeError
            ):
                current_best = 0

            if video_views > current_best:
                most_viewed_video = video

    video_chart_values = []

    for video in reversed(videos):
        try:
            views = int(
                video.get(
                    "views",
                    0
                )
            )
        except (
            ValueError,
            TypeError
        ):
            views = 0

        video_chart_values.append(
            views
        )

    return render_template(
        "channel.html",
        user=user,
        channel=channel,
        videos=videos,
        total_video_views=(
            total_video_views
        ),
        total_likes=total_likes,
        total_comments=(
            total_comments
        ),
        most_viewed_video=(
            most_viewed_video
        ),
        video_chart_values=(
            video_chart_values
        ),
    )


def ask_groq(prompt):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY topilmadi."
        )

    payload = json.dumps({
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.45
    }).encode("utf-8")

    groq_request = urllib.request.Request(
    "https://api.groq.com/openai/v1/chat/completions",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "YouTube-Manager/1.0"
    },
    method="POST",
)

    try:
        with urllib.request.urlopen(
            groq_request,
            timeout=120
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise RuntimeError(
            f"Groq API xatosi ({error.code}): "
            f"{error_body}"
        )

    except urllib.error.URLError:
        raise RuntimeError(
            "Groq API bilan ulanish bo‘lmadi."
        )

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(
            "Groq API noto‘g‘ri yoki bo‘sh javob qaytardi."
        )

    if not answer or not answer.strip():
        raise RuntimeError(
            "Groq API bo‘sh javob qaytardi."
        )

    return answer.strip()

def build_channel_analysis_prompt(channel, videos):
    video_lines = []

    for index, video in enumerate(videos, start=1):
        video_lines.append(
            f"{index}. {video.get('title', 'Nomsiz video')} | "
            f"ko‘rishlar: {video.get('views', 0)} | "
            f"layklar: {video.get('likes', 0)} | "
            f"izohlar: {video.get('comments', 0)}"
        )

    videos_text = "\n".join(video_lines)

    return f"""
Sen YouTube kanal tahlilchisisan. Quyidagi real kanal ma'lumotlarini tahlil qil.
Faqat berilgan ma'lumotlarga tayangan holda yoz; ko‘rsatilmagan narsalarni uydirma.
Javobni o‘zbek tilida, sodda va foydali qilib ber.

KANAL:
Nomi: {channel.get('title', '')}
Obunachilar: {channel.get('subscribers', '')}
Jami ko‘rishlar: {channel.get('views', '')}
Jami videolar: {channel.get('videos', '')}

SO‘NGGI VIDEOLAR:
{videos_text or 'Video ma’lumoti yo‘q.'}

Javobni aynan quyidagi bo‘limlarda yoz:
1. Qisqa xulosa
2. Eng yaxshi ishlayotgan videolar
3. Kuzatilgan tendensiyalar
4. Yaxshilash uchun 5 ta aniq tavsiya
5. Keyingi video uchun 3 ta g‘oya

Raqamlarni tushunarli izohla. Kanal egasiga amalda nima qilish kerakligini ayt.
""".strip()


@app.route(
    "/api/channel/<channel_id>/ai-analysis",
    methods=["POST"]
)
def ai_channel_analysis(channel_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Avval Google hisobingizga kiring."
        }), 401

    saved_channel = Channel.query.filter_by(
        user_id=user.id,
        youtube_channel_id=channel_id
    ).first()

    if not saved_channel:
        return jsonify({
            "ok": False,
            "error": "Bu kanal hisobingizga ulanmagan."
        }), 404

    try:
        channel = get_channel_info(channel_id)
        videos = get_latest_videos(
            channel_id,
            max_results=8
        )

        if not channel:
            return jsonify({
                "ok": False,
                "error": "YouTube kanalini topib bo‘lmadi."
            }), 404

        prompt = build_channel_analysis_prompt(
            channel,
            videos
        )
        analysis = ask_groq(prompt)

        return jsonify({
            "ok": True,
            "analysis": analysis,
            "model": "openai/gpt-oss-20b",
            "video_count": len(videos),
        })

    except Exception as error:
        print("AI kanal tahlili xatosi:", error)

        return jsonify({
            "ok": False,
            "error": str(error)
        }), 500


def build_video_helper_prompt(channel, videos, topic):
    recent_titles = "\n".join(
        f"- {video.get('title', 'Nomsiz video')}"
        for video in videos[:8]
    ) or "- So‘nggi video ma'lumoti yo‘q"

    return f"""
Sen YouTube video tayyorlash bo‘yicha AI yordamchisan.
Javobni o‘zbek tilida, lotin yozuvida yoz.
Foydalanuvchi bergan mavzu asosida tayyor, ishlatishga qulay natija yarat.
Ko‘rsatmalarni javobda takrorlama; faqat tayyor natijani chiqar.

KANAL:
Nomi: {channel.get('title', '')}
Obunachilar: {channel.get('subscribers', '')}
Jami videolar: {channel.get('videos', '')}

SO‘NGGI VIDEO NOMLARI:
{recent_titles}

YANGI VIDEO MAVZUSI:
{topic}

Faqat quyidagi bo‘limlarda javob ber:

🎯 TITLE
Bitta asosiy YouTube sarlavha yoz. Qiziqarli bo‘lsin, lekin yolg‘on clickbait bo‘lmasin.

📝 DESCRIPTION
Videoga tayyor tavsif yoz. 2-4 qisqa paragraf yetarli.

#️⃣ HASHTAGLAR
8-12 ta mavzuga mos hashtag yoz.

🏷️ TAGLAR
YouTube Studio uchun vergul bilan ajratilgan 12-20 ta tag yoz.

🖼️ THUMBNAIL G‘OYASI
Thumbnail kompozitsiyasi, asosiy obyektlar, katta matn va effektlarni qisqa tushuntir.

🎬 VIDEO REJASI
Kirish, asosiy qism va yakunni o‘z ichiga olgan 5-7 punktli reja yoz.

Muhim:
- Promptdagi topshiriqlarni qayta yozma.
- Faqat tayyor kontentni ber.
- Kanalning so‘nggi mavzulari mos kelsa ulardan kontekst sifatida foydalan.
- Ma'lumot yetarli bo‘lmasa uydirma statistika yozma.
""".strip()


@app.route(
    "/api/channel/<channel_id>/video-helper",
    methods=["POST"]
)
def ai_video_helper(channel_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Avval Google hisobingizga kiring."
        }), 401

    saved_channel = Channel.query.filter_by(
        user_id=user.id,
        youtube_channel_id=channel_id
    ).first()

    if not saved_channel:
        return jsonify({
            "ok": False,
            "error": "Bu kanal hisobingizga ulanmagan."
        }), 404

    body = request.get_json(silent=True) or {}
    topic = str(body.get("topic", "")).strip()

    if len(topic) < 3:
        return jsonify({
            "ok": False,
            "error": "Video mavzusini yozing."
        }), 400

    if len(topic) > 500:
        return jsonify({
            "ok": False,
            "error": "Mavzu juda uzun. 500 belgidan oshirmang."
        }), 400

    try:
        channel = get_channel_info(channel_id)
        videos = get_latest_videos(channel_id, max_results=8)

        if not channel:
            return jsonify({
                "ok": False,
                "error": "YouTube kanalini topib bo‘lmadi."
            }), 404

        prompt = build_video_helper_prompt(
            channel,
            videos,
            topic
        )
        content = ask_groq(prompt)

        return jsonify({
            "ok": True,
            "content": content,
            "model": "openai/gpt-oss-20b"
        })

    except Exception as error:
        print("AI video yordamchi xatosi:", error)
        return jsonify({
            "ok": False,
            "error": str(error)
        }), 500



# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

def redirect_to_first_channel(section=""):
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channel = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).first()

    if not saved_channel:
        flash("Avval YouTube kanalini ulang.")
        return redirect(url_for("index") + "#channels")

    target = url_for(
        "channel_dashboard",
        channel_id=saved_channel.youtube_channel_id
    )

    if section:
        target += f"#{section}"

    return redirect(target)


@app.route("/channels")
def channels_page():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    channels = []

    for saved_channel in saved_channels:
        try:
            info = get_channel_info(
                saved_channel.youtube_channel_id
            )

            if info:
                channels.append(info)
                continue

        except Exception as error:
            print(
                "Kanallar sahifasi xatosi:",
                error
            )

        channels.append({
            "id": saved_channel.youtube_channel_id,
            "title": saved_channel.title,
            "thumbnail": saved_channel.thumbnail,
            "subscribers": "?",
            "views": "?",
            "videos": "?",
        })

    return render_template(
        "channels.html",
        user=user,
        channels=channels
    )


@app.route("/analytics")
def analytics_page():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    channels = []

    for item in saved_channels:
        try:
            info = get_channel_info(item.youtube_channel_id)

            if info:
                videos = get_latest_videos(
                    item.youtube_channel_id,
                    max_results=8
                )

                recent_views = 0
                recent_likes = 0
                recent_comments = 0

                for video in videos:
                    try:
                        recent_views += int(video.get("views", 0))
                    except (ValueError, TypeError):
                        pass

                    try:
                        recent_likes += int(video.get("likes", 0))
                    except (ValueError, TypeError):
                        pass

                    try:
                        recent_comments += int(video.get("comments", 0))
                    except (ValueError, TypeError):
                        pass

                info["recent_views"] = recent_views
                info["recent_likes"] = recent_likes
                info["recent_comments"] = recent_comments
                info["recent_video_count"] = len(videos)
                channels.append(info)

        except Exception as error:
            print("Tahlil sahifasi xatosi:", error)

    return render_template(
        "analytics.html",
        user=user,
        channels=channels
    )


@app.route("/videos")
def videos_page():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    channels = []

    for item in saved_channels:
        try:
            info = get_channel_info(item.youtube_channel_id)

            if not info:
                continue

            videos = get_latest_videos(
                item.youtube_channel_id,
                max_results=12
            )

            channels.append({
                "channel": info,
                "videos": videos
            })

        except Exception as error:
            print("Videolar sahifasi xatosi:", error)

    return render_template(
        "videos.html",
        user=user,
        channels=channels
    )


@app.route("/ideas")
def ideas_page():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    channels = [
        {
            "id": item.youtube_channel_id,
            "title": item.title,
            "thumbnail": item.thumbnail,
        }
        for item in saved_channels
    ]

    return render_template(
        "ideas.html",
        user=user,
        channels=channels
    )


@app.route("/assistant")
def assistant_page():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    channels = [
        {
            "id": item.youtube_channel_id,
            "title": item.title,
            "thumbnail": item.thumbnail,
        }
        for item in saved_channels
    ]

    return render_template(
        "assistant.html",
        user=user,
        channels=channels
    )


@app.route("/settings")
def settings_page():
    user = get_current_user()

    if not user:
        return redirect(url_for("login"))

    saved_channels = Channel.query.filter_by(
        user_id=user.id
    ).order_by(
        Channel.id.desc()
    ).all()

    return render_template(
        "settings.html",
        user=user,
        channel_count=len(saved_channels),
        ai_model="openai/gpt-oss-20b"
    )

def build_ideas_prompt(channel, videos, topic):
    recent_titles = "\n".join(
        f"- {video.get('title', 'Nomsiz video')} "
        f"(ko‘rishlar: {video.get('views', 0)})"
        for video in videos[:8]
    ) or "- So‘nggi video ma'lumoti yo‘q"

    topic_text = topic if topic else "Maxsus mavzu berilmagan"

    return f"""
Sen YouTube uchun yangi video g‘oyalari yaratuvchi AI yordamchisan.
Javobni o‘zbek tilida, lotin yozuvida yoz.
Ko‘rsatmalarni takrorlama. Faqat tayyor g‘oyalarni chiqar.

KANAL:
Nomi: {channel.get('title', '')}
Obunachilar: {channel.get('subscribers', '')}
Jami ko‘rishlar: {channel.get('views', '')}
Jami videolar: {channel.get('videos', '')}

SO‘NGGI VIDEOLAR:
{recent_titles}

FOYDALANUVCHI BERGAN YO‘NALISH:
{topic_text}

8 ta yangi video g‘oyasi yarat.

Har bir g‘oya quyidagi shaklda bo‘lsin:

💡 G‘OYA 1
🎯 Nomi: ...
📝 Mazmuni: 1-2 jumla
🖼️ Thumbnail: qisqa vizual g‘oya
⚡ Hook: videoning boshida tomoshabinni qiziqtiradigan bitta gap

Muhim:
- 8 ta g‘oya bir-biridan farq qilsin.
- Kanalning so‘nggi videolarini kontekst sifatida ishlat.
- Mavjud video nomlarini aynan ko‘chirib qo‘yma.
- Uydirma statistika yozma.
- Yolg‘on clickbait ishlatma.
""".strip()


@app.route(
    "/api/channel/<channel_id>/ideas",
    methods=["POST"]
)
def ai_generate_ideas(channel_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Avval Google hisobingizga kiring."
        }), 401

    saved_channel = Channel.query.filter_by(
        user_id=user.id,
        youtube_channel_id=channel_id
    ).first()

    if not saved_channel:
        return jsonify({
            "ok": False,
            "error": "Bu kanal hisobingizga ulanmagan."
        }), 404

    body = request.get_json(silent=True) or {}
    topic = str(body.get("topic", "")).strip()

    if len(topic) > 300:
        return jsonify({
            "ok": False,
            "error": "Yo‘nalish 300 belgidan oshmasin."
        }), 400

    try:
        channel = get_channel_info(channel_id)
        videos = get_latest_videos(
            channel_id,
            max_results=8
        )

        if not channel:
            return jsonify({
                "ok": False,
                "error": "YouTube kanalini topib bo‘lmadi."
            }), 404

        prompt = build_ideas_prompt(
            channel,
            videos,
            topic
        )

        ideas = ask_groq(prompt)

        return jsonify({
            "ok": True,
            "ideas": ideas,
            "model": "openai/gpt-oss-20b"
        })

    except Exception as error:
        print("AI g‘oyalar xatosi:", error)

        return jsonify({
            "ok": False,
            "error": str(error)
        }), 500




def build_assistant_prompt(channel, videos, message):
    recent_videos = "\n".join(
        f"- {video.get('title', 'Nomsiz video')} | "
        f"ko‘rishlar: {video.get('views', 0)} | "
        f"layklar: {video.get('likes', 0)} | "
        f"izohlar: {video.get('comments', 0)}"
        for video in videos[:8]
    ) or "- So‘nggi video ma'lumoti yo‘q"

    return f"""
Sen YouTube Manager ichidagi AI yordamchisan.
Foydalanuvchiga o‘zbek tilida, lotin yozuvida, sodda va amaliy javob ber.
Kanalga oid savollarda faqat quyidagi real ma'lumotlardan foydalan.
Ma'lumot yetarli bo‘lmasa, buni ochiq ayt va statistika uydirma.
Foydalanuvchi oddiy YouTube savolini bersa, foydali maslahat berishing mumkin.
Ko‘rsatmalarni javobda takrorlama.

KANAL:
Nomi: {channel.get('title', '')}
Obunachilar: {channel.get('subscribers', '')}
Jami ko‘rishlar: {channel.get('views', '')}
Jami videolar: {channel.get('videos', '')}

SO‘NGGI VIDEOLAR:
{recent_videos}

FOYDALANUVCHI SAVOLI:
{message}

JAVOB:
""".strip()


@app.route(
    "/api/channel/<channel_id>/assistant",
    methods=["POST"]
)
def ai_assistant_chat(channel_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Avval Google hisobingizga kiring."
        }), 401

    saved_channel = Channel.query.filter_by(
        user_id=user.id,
        youtube_channel_id=channel_id
    ).first()

    if not saved_channel:
        return jsonify({
            "ok": False,
            "error": "Bu kanal hisobingizga ulanmagan."
        }), 404

    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()

    if len(message) < 2:
        return jsonify({
            "ok": False,
            "error": "AI yordamchiga savol yozing."
        }), 400

    if len(message) > 1000:
        return jsonify({
            "ok": False,
            "error": "Savol 1000 belgidan oshmasin."
        }), 400

    try:
        channel = get_channel_info(channel_id)
        videos = get_latest_videos(
            channel_id,
            max_results=8
        )

        if not channel:
            return jsonify({
                "ok": False,
                "error": "YouTube kanalini topib bo‘lmadi."
            }), 404

        prompt = build_assistant_prompt(
            channel,
            videos,
            message
        )

        answer = ask_groq(prompt)

        return jsonify({
            "ok": True,
            "answer": answer,
            "model": "openai/gpt-oss-20b"
        })

    except Exception as error:
        print("AI yordamchi xatosi:", error)

        return jsonify({
            "ok": False,
            "error": str(error)
        }), 500





def safe_int(value):
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0


def create_channel_notification(user, saved_channel, kind, title, message):
    db.session.add(Notification(
        user_id=user.id,
        channel_id=saved_channel.id,
        kind=kind,
        title=title,
        message=message
    ))


def refresh_channel_notifications(user):
    saved_channels = Channel.query.filter_by(user_id=user.id).all()
    created = 0

    for saved_channel in saved_channels:
        try:
            info = get_channel_info(saved_channel.youtube_channel_id)
            if not info:
                continue

            subscribers = safe_int(info.get("subscribers"))
            views = safe_int(info.get("views"))
            videos = safe_int(info.get("videos"))

            snapshot = ChannelSnapshot.query.filter_by(channel_id=saved_channel.id).first()

            if snapshot is None:
                snapshot = ChannelSnapshot(
                    channel_id=saved_channel.id,
                    subscribers=subscribers,
                    views=views,
                    videos=videos
                )
                db.session.add(snapshot)
                continue

            sub_diff = subscribers - snapshot.subscribers
            view_diff = views - snapshot.views
            video_diff = videos - snapshot.videos

            if sub_diff > 0:
                create_channel_notification(
                    user, saved_channel, "subscribers",
                    f"{saved_channel.title}: obunachilar oshdi",
                    f"Oxirgi tekshiruvdan beri +{sub_diff:,} ta obunachi. Hozir jami {subscribers:,} ta."
                )
                created += 1

            if view_diff > 0:
                create_channel_notification(
                    user, saved_channel, "views",
                    f"{saved_channel.title}: ko‘rishlar oshdi",
                    f"Oxirgi tekshiruvdan beri +{view_diff:,} ta ko‘rish. Hozir jami {views:,} ta."
                )
                created += 1

            if video_diff > 0:
                create_channel_notification(
                    user, saved_channel, "videos",
                    f"{saved_channel.title}: yangi video aniqlandi",
                    f"Kanalda {video_diff} ta yangi video paydo bo‘lgan. Hozir jami {videos:,} ta video."
                )
                created += 1

            snapshot.subscribers = subscribers
            snapshot.views = views
            snapshot.videos = videos
            snapshot.checked_at = datetime.now(timezone.utc)

        except Exception as error:
            print("Bildirishnoma tekshiruvi xatosi:", error)

    db.session.commit()
    return created


def notifications_need_refresh(user, minutes=10):
    snapshots = (
        ChannelSnapshot.query
        .join(Channel, ChannelSnapshot.channel_id == Channel.id)
        .filter(Channel.user_id == user.id)
        .all()
    )

    saved_channel_count = Channel.query.filter_by(
        user_id=user.id
    ).count()

    if saved_channel_count == 0:
        return False

    # If a newly-added channel has no baseline yet, check now.
    if len(snapshots) < saved_channel_count:
        return True

    if not snapshots:
        return True

    oldest_check = min(
        snapshot.checked_at
        for snapshot in snapshots
        if snapshot.checked_at is not None
    )

    if oldest_check is None:
        return True

    # SQLite may return a naive datetime even when we stored UTC.
    if oldest_check.tzinfo is None:
        oldest_check = oldest_check.replace(tzinfo=timezone.utc)

    return (
        datetime.now(timezone.utc) - oldest_check
        >= timedelta(minutes=minutes)
    )


@app.before_request
def automatic_channel_notification_check():
    # Skip assets, auth flow and the manual refresh route.
    if request.endpoint in {
        "static",
        "login",
        "login_callback",
        "logout",
        "refresh_notifications",
    }:
        return None

    user = get_current_user()

    if not user:
        return None

    try:
        if notifications_need_refresh(user, minutes=10):
            refresh_channel_notifications(user)
    except Exception as error:
        # Notification monitoring must never break the main site.
        print("Avtomatik bildirishnoma tekshiruvi xatosi:", error)

    return None


@app.route("/notifications")
def notifications_page():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.id.desc()).limit(100).all()
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    return render_template(
        "notifications.html",
        user=user,
        notifications=notifications,
        unread_count=unread_count
    )


@app.route("/notifications/refresh", methods=["POST"])
def refresh_notifications():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    created = refresh_channel_notifications(user)
    if created:
        flash(f"🔔 {created} ta yangi kanal bildirishnomasi topildi.")
    else:
        flash("Hozircha yangi o‘zgarish topilmadi.")
    return redirect(url_for("notifications_page"))


@app.route("/notifications/read-all", methods=["POST"])
def read_all_notifications():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(url_for("notifications_page"))

@app.route("/login")
def login():
    if get_current_user():
        return redirect(
            url_for("index")
        )

    redirect_uri = url_for(
        "login_callback",
        _external=True
    )

    return google.authorize_redirect(
        redirect_uri
    )


@app.route("/login/callback")
def login_callback():
    try:
        token = (
            google.authorize_access_token()
        )

        user_info = token.get(
            "userinfo"
        )

        if not user_info:
            user_info = (
                google.userinfo()
            )

        google_id = user_info.get(
            "sub"
        )

        email = user_info.get(
            "email"
        )

        name = user_info.get(
            "name",
            "Foydalanuvchi"
        )

        picture = user_info.get(
            "picture"
        )

        if not google_id or not email:
            flash(
                "Google hisob "
                "ma'lumotlarini olib "
                "bo‘lmadi."
            )

            return redirect(
                url_for("index")
            )

        user = User.query.filter_by(
            google_id=google_id
        ).first()

        if not user:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )

            db.session.add(user)
            db.session.commit()

        else:
            user.email = email
            user.name = name
            user.picture = picture

            db.session.commit()

        session.clear()

        session["user_id"] = user.id

        return redirect(
            url_for("index")
        )

    except Exception as error:
        print(
            "Google Login xatosi:",
            error
        )

        flash(
            "Google orqali kirishda "
            "xatolik yuz berdi."
        )

        return redirect(
            url_for("index")
        )


@app.route("/logout")
def logout():
    session.clear()

    return redirect(
        url_for("index")
    )


@app.route(
    "/add-channel",
    methods=["POST"]
)
def add_channel():
    user = get_current_user()

    if not user:
        return redirect(
            url_for("login")
        )

    channel_input = request.form.get(
        "channel_id",
        ""
    ).strip()

    if not channel_input:
        flash(
            "Kanal ID yoki linkini kiriting."
        )

        return redirect(
            url_for("index")
        )

    try:
        # Channel ID, /channel/ link yoki @handle
        # linkini haqiqiy Channel ID'ga aylantiramiz.
        channel_id = resolve_channel_id(
            channel_input
        )

        if not channel_id:
            flash(
                "YouTube kanali topilmadi. "
                "Kanal ID yoki linkini tekshiring."
            )

            return redirect(
                url_for("index")
            )

        # Muhim: duplicate tekshiruvi endi
        # foydalanuvchi kiritgan link bilan emas,
        # haqiqiy Channel ID bilan qilinadi.
        existing_channel = (
            Channel.query.filter_by(
                user_id=user.id,
                youtube_channel_id=channel_id
            ).first()
        )

        if existing_channel:
            flash(
                "Bu kanal hisobingizga "
                "allaqachon qo‘shilgan."
            )

            return redirect(
                url_for("index")
            )

        channel_info = get_channel_info(
            channel_id
        )

        if not channel_info:
            flash(
                "Bunday YouTube kanali "
                "topilmadi."
            )

            return redirect(
                url_for("index")
            )

        channel = Channel(
            youtube_channel_id=(
                channel_info["id"]
            ),
            title=(
                channel_info["title"]
            ),
            thumbnail=(
                channel_info["thumbnail"]
            ),
            user_id=user.id
        )

        db.session.add(channel)
        db.session.commit()

        flash(
            f"✅ "
            f"{channel_info['title']} "
            "muvaffaqiyatli qo‘shildi."
        )

    except Exception as error:
        print(
            "Kanal qo‘shishda xato:",
            error
        )

        flash(
            "Kanalni tekshirishda "
            "xatolik yuz berdi."
        )

    return redirect(
        url_for("index")
    )


@app.route(
    "/remove-channel/<channel_id>",
    methods=["POST"]
)
def remove_channel(channel_id):
    user = get_current_user()

    if not user:
        return redirect(
            url_for("login")
        )

    channel = (
        Channel.query.filter_by(
            user_id=user.id,
            youtube_channel_id=channel_id
        ).first()
    )

    if not channel:
        flash(
            "Kanal topilmadi."
        )

        return redirect(
            url_for("index")
        )

    title = channel.title

    # Kanalga bog'langan notificationlarni o'chirish
    Notification.query.filter_by(
        user_id=user.id,
        channel_id=channel.id
    ).delete(
        synchronize_session=False
    )

    # Kanalga bog'langan snapshotni o'chirish
    ChannelSnapshot.query.filter_by(
        channel_id=channel.id
    ).delete(
        synchronize_session=False
    )

    # Endi kanalni xavfsiz o'chirish mumkin
    db.session.delete(channel)
    db.session.commit()

    flash(
        f"{title} hisobingizdan "
        "olib tashlandi."
    )

    return redirect(
        url_for("index")
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )