import os
import pickle
import time
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_authenticated_service():
    credentials = None
    token_file = "token.pickle"

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            client_secret_json = os.getenv("CLIENT_SECRET")
            if client_secret_json is None:
                print("❌ CLIENT_SECRET tidak ditemukan di environment variables!")
                exit()

            client_secrets = json.loads(client_secret_json)

            flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)

            # Use run_local_server() for local and browser environments
            credentials = flow.run_local_server(port=0)

        with open(token_file, "wb") as token:
            pickle.dump(credentials, token)

    return build("youtube", "v3", credentials=credentials)

def get_channel_subscribers(youtube, channel_id):
    request = youtube.channels().list(
        part="statistics",
        id=channel_id
    )
    response = request.execute()
    if "items" in response:
        return int(response["items"][0]["statistics"]["subscriberCount"])
    return 0

def get_latest_video(youtube, mode):
    request = youtube.search().list(
        part="id,snippet",
        order="date",
        maxResults=10,
        type="video",
        regionCode="ID",
        relevanceLanguage="id"
    )
    response = request.execute()

    if "items" in response and len(response["items"]) > 0:
        for item in response["items"]:
            video_id = item["id"]["videoId"]
            channel_id = item["snippet"]["channelId"]
            channel_name = item["snippet"]["channelTitle"]
            video_title = item["snippet"]["title"]

            if mode == "1":
                subs = get_channel_subscribers(youtube, channel_id)
                if subs >= 100000:
                    print(f"🔍 Ditemukan video dari {channel_name} ({subs} subscribers): {video_title}")
                    return video_id

            elif mode == "2":
                print(f"🎬 Ditemukan SHORTS dari {channel_name}: {video_title}")
                return video_id

    return None

def comment_on_video(youtube, video_id, comment_text):
    request = youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
    )
    request.execute()
    print(f"✅ Berhasil berkomentar di: https://www.youtube.com/watch?v={video_id}")

if __name__ == "__main__":
    youtube = get_authenticated_service()
    print("\n🔹 PILIH MODE 🔹")
    print("1. Mode Biasa")
    print("2. Mode Shorts")
    mode = input("\nKetik 1 atau 2: ").strip()

    if mode not in ["1", "2"]:
        print("❌ Pilihan tidak valid, keluar...")
        exit()

    print("\n🚀 Bot mulai berjalan...\n")

    while True:
        latest_video_id = get_latest_video(youtube, mode)
        if latest_video_id:
            comment_text = "Sholat di Masjid pahalanya auto gacor 🤑📈"
            comment_on_video(youtube, latest_video_id, comment_text)
        else:
            print("❌ Tidak ada video yang memenuhi syarat.")

        print("\n⏳ Menunggu 5 menit sebelum mengecek lagi...\n")
        time.sleep(300)
