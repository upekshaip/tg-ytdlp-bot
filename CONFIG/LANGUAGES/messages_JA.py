# Messages Configuration (Japanese Translation)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# Removed circular import

class Messages(object):
    #######################################################
    # Messages and errors
    #######################################################
    CREDITS_MSG = "<blockquote><i>管理:</i> @iilililiiillliiliililliilliliiil\n🇮🇹 @tgytdlp_it_bot\n🇦🇪 @tgytdlp_uae_bot\n🇬🇧 @tgytdlp_uk_bot\n🇫🇷 @tgytdlp_fr_bot</blockquote>\n<b>🌍 言語を変更: /lang</b>"
    TO_USE_MSG = "<i>このボットを使用するには、@tg_ytdlp Telegramチャンネルに登録する必要があります。</i>\nチャンネルに参加した後、<b>ビデオリンクを再送信すると、ボットがダウンロードします</b> ❤️\n\n<blockquote>追伸 🔞NSFWコンテンツと☁️クラウドストレージからのファイルのダウンロードは有料です！ 1⭐️ = $0.02</blockquote>\n<blockquote>追伸 ‼️ チャンネルを離れないでください - ボットの使用が禁止されます ⛔️</blockquote>"

    ERROR1 = "URLリンクが見つかりませんでした。<b>https://</b>または<b>http://</b>でURLを入力してください"

    PLAYLIST_HELP_MSG = """
<blockquote expandable>📋 <b>プレイリスト (yt-dlp)</b>

プレイリストをダウンロードするには、URLの末尾に<code>*start*end</code>の範囲を付けて送信します。例: <code>URL*1*5</code> (1から5までの最初の5つのビデオをダウンロードします)。<code>URL*-1*-5</code> (最後から1から5までの5つのビデオをダウンロードします)。\nまたは、<code>/vid FROM-TO URL</code>を使用することもできます。例: <code>/vid 3-7 URL</code> (最初から3番目から7番目までのビデオをダウンロードします)。<code>/vid -3-7 URL</code> (最後から3番目から7番目までのビデオをダウンロードします)。<code>/audio</code>コマンドでも機能します。

<b>例:</b>

🟥 <b>YouTubeプレイリストのビデオ範囲:</b> (🍪が必要)
<code>https://youtu.be/playlist?list=PL...*1*5</code>
(1から5までの最初の5つのビデオをダウンロードします)
🟥 <b>YouTubeプレイリストの単一ビデオ:</b> (🍪が必要)
<code>https://youtu.be/playlist?list=PL...*3*3</code>
(3番目のビデオのみをダウンロードします)

⬛️ <b>TikTokプロフィール:</b> (あなたの🍪が必要)
<code>https://www.tiktok.com/@USERNAME*1*10</code>
(ユーザープロフィールの最初の10個のビデオをダウンロードします)

🟪 <b>Instagramストーリー:</b> (あなたの🍪が必要)
<code>https://www.instagram.com/stories/USERNAME*1*3</code>
(最初の3つのストーリーをダウンロードします)
<code>https://www.instagram.com/stories/highlights/123...*1*10</code>
(アルバムから最初の10個のストーリーをダウンロードします)

🟦 <b>VKビデオ:</b>
<code>https://vkvideo.ru/@PAGE_NAME*1*3</code>
(ユーザー/グループプロフィールの最初の3つのビデオをダウンロードします)

⬛️<b>Rutubeチャンネル:</b>
<code>https://rutube.ru/channel/CHANNEL_ID/videos*2*4</code>
(チャンネルから2番目から4番目までのビデオをダウンロードします)

🟪 <b>Twitchクリップ:</b>
<code>https://www.twitch.tv/USERNAME/clips*1*3</code>
(チャンネルから最初の3つのクリップをダウンロードします)

🟦 <b>Vimeoグループ:</b>
<code>https://vimeo.com/groups/GROUP_NAME/videos*1*2</code>
(グループから最初の2つのビデオをダウンロードします)

🟧 <b>Pornhubモデル:</b>
<code>https://www.pornhub.org/model/MODEL_NAME*1*2</code>
(モデルプロフィールの最初の2つのビデオをダウンロードします)
<code>https://www.pornhub.com/video/search?search=YOUR+PROMPT*1*3</code>
(あなたのプロンプトによる検索結果から最初の3つのビデオをダウンロードします)

など...
<a href=\"https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/supportedsites.md\">サポートされているサイトのリスト</a>を参照してください
</blockquote>

<blockquote expandable>🖼 <b>画像 (gallery-dl)</b>

<code>/img URL</code>を使用して、多くのプラットフォームから画像/写真/アルバムをダウンロードします。

<b>例:</b>
<code>/img https://vk.com/wall-160916577_408508</code>
<code>/img https://2ch.hk/fd/res/1747651.html</code>
<code>/img https://x.com/username/status/1234567890123456789</code>
<code>/img https://imgur.com/a/abc123</code>

<b>範囲:</b>
<code>/img 11-20 https://example.com/album</code> — アイテム11..20
<code>/img 11- https://example.com/album</code> — 11番目から最後まで (またはボットの制限まで)

<i>サポートされているプラットフォームには、vk、2ch、35photo、4chan、500px、ArtStation、Boosty、Civitai、Cyberdrop、DeviantArt、Discord、Facebook、Fansly、Instagram、Pinterest、Reddit、TikTok、Tumblr、Twitter/X、JoyReactorなどが含まれます。完全なリスト:</i>
<a href=\"https://raw.githubusercontent.com/mikf/gallery-dl/refs/heads/master/docs/supportedsites.md\">gallery-dlがサポートするサイト</a>
</blockquote>
"""
    HELP_MSG = """
<blockquote>🎬 <b>ビデオダウンロードボット - ヘルプ</b>

📥 <b>基本的な使い方:</b>
• リンクを送信 → ボットがダウンロードします
  <i>ボットはyt-dlpを介してビデオを、gallery-dlを介して画像を自動的にダウンロードしようとします。</i>
• <code>/audio URL</code> → 音声を抽出
• <code>/link [quality] URL</code> → ダイレクトリンクを取得
• <code>/proxy</code> → すべてのダウンロードでプロキシを有効/無効にする
• テキスト付きでビデオに返信 → キャプションを変更

📋 <b>プレイリストと範囲:</b>
• <code>URL*1*5</code> → 最初の5つのビデオをダウンロード
• <code>URL*-1*-5</code> → 最後の5つのビデオをダウンロード
• <code>/vid 3-7 URL</code> → <code>URL*3*7</code>になります
• <code>/vid -3-7 URL</code> → <code>URL*-3*-7</code>になります

🍪 <b>Cookieとプライベート:</b>
• プライベートビデオ用に*.txt Cookieをアップロード
• <code>/cookie [service]</code> → Cookieをダウンロード (youtube/tiktok/x/custom)
• <code>/cookie youtube 1</code> → インデックスでソースを選択 (1–N)
• <code>/cookies_from_browser</code> → ブラウザから抽出
• <code>/check_cookie</code> → Cookieを検証
• <code>/save_as_cookie</code> → テキストをCookieとして保存

🧹 <b>クリーニング:</b>
• <code>/clean</code> → メディアファイルのみ
• <code>/clean all</code> → すべて
• <code>/clean cookies/logs/tags/format/split/mediainfo/sub/keyboard</code>

⚙️ <b>設定:</b>
• <code>/settings</code> → 設定メニュー
• <code>/format</code> → 品質とフォーマット
• <code>/split</code> → ビデオをパートに分割
• <code>/mediainfo on/off</code> → メディア情報
• <code>/nsfw on/off</code> → NSFWブラー
• <code>/tags</code> → 保存されたタグを表示
• <code>/sub on/off</code> → 字幕
• <code>/keyboard</code> → キーボード (OFF/1x3/2x3)

🏷️ <b>タグ:</b>
• URLの後に<code>#tag1#tag2</code>を追加
• タグはキャプションに表示されます
• <code>/tags</code> → すべてのタグを表示

🔗 <b>ダイレクトリンク:</b>
• <code>/link URL</code> → 最高品質
• <code>/link [144-4320]/720p/1080p/4k/8k URL</code> → 特定の品質

⚙️ <b>クイックコマンド:</b>
• <code>/format [144-4320]/720p/1080p/4k/8k/best/ask/id 134</code> → 品質を設定
• <code>/keyboard off/1x3/2x3/full</code> → キーボードレイアウト
• <code>/split 100mb-2000mb</code> → パートサイズを変更
• <code>/subs off/ru/en auto</code> → 字幕言語
• <code>/list URL</code> → 利用可能なフォーマットのリスト
• <code>/mediainfo on/off</code> → メディア情報のオン/オフ
• <code>/proxy on/off</code> → すべてのダウンロードでプロキシを有効/無効にする

📊 <b>情報:</b>
• <code>/usage</code> → ダウンロード履歴
• <code>/search</code> → @vidを介したインライン検索

🖼 <b>画像:</b>
• <code>URL</code> → 画像URLをダウンロード
• <code>/img URL</code> → URLから画像をダウンロード
• <code>/img 11-20 URL</code> → 特定の範囲をダウンロード
• <code>/img 11- URL</code> → 11番目から最後までダウンロード

👨‍💻 <i>開発者:</i> @upekshaip
🤝 <i>貢献者:</i> @IIlIlIlIIIlllIIlIIlIllIIllIlIIIl
</blockquote>
    "
    
    # Version 1.0.0 - Added SAVE_AS_COOKIE_HINT for hint on /save_as_cookie
    SAVE_AS_COOKIE_HINT = (
        "<b><u>cookie.txt</u></b>としてCookieを保存し、ドキュメントとしてボットに送信するだけです。\n\n"
        "<b><u>/save_as_cookie</u></b>コマンドでプレーンテキストとしてCookieを送信することもできます。\n"
        "<b><b><u>/save_as_cookie</u></b>の使用法:</b>\n\n"
        "<pre>"
        "/save_as_cookie\n"
        "# Netscape HTTP Cookie File\n"
        "# http://curl.haxx.se/rfc/cookie_spec.html\n"
        "# このファイルはCookie-Editorによって生成されました\n"
        ".youtube.com  TRUE  /  FALSE  111  ST-xxxxx  session_logininfo=AAA\n"
        ".youtube.com  TRUE  /  FALSE  222  ST-xxxxx  session_logininfo=BBB\n"
        ".youtube.com  TRUE  /  FALSE  33333  ST-xxxxx  session_logininfo=CCC\n"
        "</pre>\n"
        "<blockquote>""
        "<b><u>手順:</u></b>\n"
        "https://t.me/tg_ytdlp/203 \n"
        "https://t.me/tg_ytdlp/214 "
        "</blockquote>"
    )
    
    # Search command message (English)
    SEARCH_MSG = """
🔍 <b>ビデオ検索</b>

下のボタンを押して、@vid経由でインライン検索を有効にします。

<blockquote>PCでは、任意のチャットで<b>「@vid 検索クエリ」</b>と入力するだけです。</blockquote>
    """
    
    # 設定とヒント
    
    
    IMG_HELP_MSG = (
        "<b>🖼 画像ダウンロードコマンド</b>\n\n"
        "使用法: <code>/img URL</code>\n\n"
        "<b>例:</b>\n"
        "• <code>/img https://example.com/image.jpg</code>\n"
        "• <code>/img 11-20 https://example.com/album</code>\n"
        "• <code>/img 11- https://example.com/album</code>\n"
        "• <code>/img https://vk.com/wall-160916577_408508</code>\n"
        "• <code>/img https://2ch.hk/fd/res/1747651.html</code>\n"
        "• <code>/img https://imgur.com/abc123</code>\n\n"
        "<b>サポートされているプラットフォーム (例):</b>\n"
        "<blockquote>vk、2ch、35photo、4chan、500px、ArtStation、Boosty、Civitai、Cyberdrop、DeviantArt、Discord、Facebook、Fansly、Instagram、Patreon、Pinterest、Reddit、TikTok、Tumblr、Twitter/X、JoyReactorなど — <a href=\"https://github.com/mikf/gallery-dl/blob/master/docs/supportedsites.md\">完全なリスト</a></blockquote>"
        "こちらも参照: "
    )
    
    LINK_HINT_MSG = (
        "品質を選択してダイレクトビデオリンクを取得します。\n\n"
        "使用法: /link + URL \n\n"
        "(例: /link https://youtu.be/abc123)\n"
        "(例: /link 720 https://youtu.be/abc123)"
    )
    
    # Add bot to group command message
    ADD_BOT_TO_GROUP_MSG = """
🤖 <b>グループにボットを追加</b>

グループにボットを追加して、拡張機能とより高い制限を入手してください！
————————————
📊 <b>現在の無料制限 (ボットのDM内):</b>
<blockquote>•🗑 未整理のすべてのファイルからの散らかったジャンク 👎
• 最大1ファイルサイズ: <b>8 GB </b>
• 最大1ファイル品質: <b>無制限</b>
• 最大1ファイル期間: <b>無制限</b>
• 最大ダウンロード数: <b>無制限</b>
• 1回あたりの最大プレイリストアイテム数: <b>50</b>
• 1回あたりの最大TikTokビデオ数: <b>500</b>
• 1回あたりの最大画像数: <b>1000</b>
• 1ダウンロードの最大時間: <b>2時間</b>
• 🔞 NSFWコンテンツは有料です！ 1⭐️ = $0.02
• 🆓 他のすべてのメディアは完全に無料です
• 📝 再ダウンロード時に即時再投稿するためのすべてのコンテンツログとキャッシュをログチャンネルに</blockquote>

💬<b>字幕付きビデオの制限:</b>
<blockquote>• 最大ビデオ+字幕期間: <b>1.5時間</b>
• 最大ビデオ+字幕ファイルサイズ: <b>500 MB</b>
• 最大ビデオ+字幕品質: <b>720p</b></blockquote>
————————————
🚀 <b>有料グループの特典 (2️⃣x の制限):</b>
<blockquote>•  🗂 トピック別に整理されたきれいなメディアボールト 👍
•  📁 ボットはあなたが呼んだトピックで返信します
•  📌 ダウンロードの進行状況を含むステータスメッセージを自動的にピン留め
•  🖼 /imgコマンドはメディアを10アイテムのアルバムとしてダウンロードします
• 最大1ファイルサイズ: <b>16 GB</b> ⬆️
• 1回あたりの最大プレイリストアイテム数: <b>100</b> ⬆️
• 1回あたりの最大TikTokビデオ数: 1000 ⬆️
• 1回あたりの最大画像数: 2000 ⬆️
• 1ダウンロードの最大時間: <b>4時間</b> ⬆️
• 🔞 NSFWコンテンツ: 完全なメタデータ付きで無料 🆓
• 📢 グループのために私のチャンネルに登録する必要はありません
• 👥 すべてのグループメンバーが有料機能にアクセスできます！
• 🗒 ログチャンネルへのログ/キャッシュなし！ グループ設定でコピー/再投稿を拒否できます</blockquote>

💬 <b>字幕付きビデオの2️⃣倍の制限:</b>
<blockquote>• 最大ビデオ+字幕期間: <b>3時間</b> ⬆️
• 最大ビデオ+字幕ファイルサイズ: <b>1000 MB</b> ⬆️
• 最大ビデオ+字幕品質: <b>1080p</b> ⬆️</blockquote>
————————————
💰 <b>価格と設定:</b>
<blockquote>• 価格: グループ内のボット1台あたり<b>月額$5</b>
• 設定: @iilililiiillliiliililliilliliiilにお問い合わせください
• 支払い: 💎TONまたはその他の方法💲
• サポート: 完全な技術サポートが含まれています</blockquote>
————————————
私のボットをグループに追加して、無料の🔞<b>NSFW</b>のブロックを解除し、すべての制限を2倍（x2️⃣）にすることができます。
あなたのグループが私のボットを使用できるようにしたい場合は、@iilililiiillliiliililliilliliiilまでご連絡ください。
————————————
💡<b>ヒント:</b> <blockquote>友達（たとえば100人）と一緒にお金を出し合って、グループ全体で1回の購入を行うことができます - すべてのグループメンバーが、そのグループ内のすべてのボット機能に<b>わずか$0.05</b>で完全に無制限にアクセスできるようになります</blockquote>
    """
    
    # NSFW Command Messages
    NSFW_ON_MSG = """
🔞 <b>NSFWモード: オン✅</b>

• NSFWコンテンツはぼかしなしで表示されます。
• スポイラーはNSFWメディアには適用されません。
• コンテンツはすぐに表示されます

<i>ぼかしを有効にするには/nsfw offを使用してください</i>
    """
    
    NSFW_OFF_MSG = """
🔞 <b>NSFWモード: オフ</b>

⚠️ <b>ぼかしが有効</b>
• NSFWコンテンツはスポイラーの下に隠されます   
• 表示するには、メディアをクリックする必要があります
• スポイラーはNSFWメディアに適用されます。

<i>ぼかしを無効にするには/nsfw onを使用してください</i>
    """
    
    NSFW_INVALID_MSG = """
❌ <b>無効なパラメータ</b>

使用法:
• <code>/nsfw on</code> - ぼかしを無効にする
• <code>/nsfw off</code> - ぼかしを有効にする
    """
    
    # UI Messages - Status and Progress
    CHECKING_CACHE_MSG = "🔄 <b>キャッシュを確認しています...</b>\n\n<code>{url}</code>"
    PROCESSING_MSG = "🔄 処理中..."
    DOWNLOADING_MSG = "📥 <b>メディアをダウンロードしています...</b>\n\n"

    DOWNLOADING_IMAGE_MSG = "📥 <b>画像をダウンロードしています...</b>\n\n"

    DOWNLOAD_COMPLETE_MSG = "✅ <b>ダウンロード完了</b>\n\n"
    
    # Download status messages
    DOWNLOADED_STATUS_MSG = "ダウンロード済み:"
    SENT_STATUS_MSG = "送信済み:"
    PENDING_TO_SEND_STATUS_MSG = "送信保留中:"
    TITLE_LABEL_MSG = "タイトル:"
    MEDIA_COUNT_LABEL_MSG = "メディア数:"
    AUDIO_DOWNLOAD_FINISHED_PROCESSING_MSG = "ダウンロードが完了し、音声を処理しています..."
    VIDEO_PROCESSING_MSG = "📽 ビデオを処理しています..."
    WAITING_HOURGLASS_MSG = "⌛️"
    
    # Cache Messages
    SENT_FROM_CACHE_MSG = "✅ <b>キャッシュから送信</b>\n\n送信されたアルバム: <b>{count}</b>"
    VIDEO_SENT_FROM_CACHE_MSG = "✅ ビデオはキャッシュから正常に送信されました。"
    PLAYLIST_SENT_FROM_CACHE_MSG = "✅ プレイリストのビデオはキャッシュから送信されました ({cached}/{total} ファイル)。"
    CACHE_PARTIAL_MSG = "📥 {cached}/{total} のビデオがキャッシュから送信され、不足しているものをダウンロードしています..."
    CACHE_CONTINUING_DOWNLOAD_MSG = "✅ キャッシュから送信: {cached}\n🔄 ダウンロードを続行しています..."
    FALLBACK_ANALYZE_MEDIA_MSG = "🔄 メディアを分析できませんでした。最大許容範囲 (1-{fallback_limit}) で続行します..."
    FALLBACK_DETERMINE_COUNT_MSG = "🔄 メディア数を特定できませんでした。最大許容範囲 (1-{total_limit}) で続行します..."
    FALLBACK_SPECIFIED_RANGE_MSG = "🔄 合計メディア数を特定できませんでした。指定された範囲 {start}-{end} で続行します..."

    # Error Messages
    INVALID_URL_MSG = "❌ <b>無効なURL</b>\n\nhttp://またはhttps://で始まる有効なURLを提供してください"

    ERROR_OCCURRED_MSG = "❌ <b>エラーが発生しました</b>\n\n<code>{url}</code>\n\nエラー: {error}"

    ERROR_SENDING_VIDEO_MSG = "❌ ビデオの送信中にエラーが発生しました: {error}"
    ERROR_UNKNOWN_MSG = "❌ 不明なエラー: {error}"
    ERROR_NO_DISK_SPACE_MSG = "❌ ビデオをダウンロードするためのディスク容量が不足しています。"
    ERROR_FILE_SIZE_LIMIT_MSG = "❌ ファイルサイズが{limit} GBの制限を超えています。許可されたサイズ内の小さいファイルを選択してください。"

    ERROR_GETTING_LINK_MSG = "❌ <b>リンクの取得中にエラーが発生しました:</b>\n{error}"

    # Telegram Rate Limit Messages
    RATE_LIMIT_WITH_TIME_MSG = "⚠️ Telegramはメッセージの送信を制限しています。\n⏳ お待ちください: {time}\nタイマーを更新するには、URLをもう一度2回送信してください。"
    RATE_LIMIT_NO_TIME_MSG = "⚠️ Telegramはメッセージの送信を制限しています。\n⏳ お待ちください: \nタイマーを更新するには、URLをもう一度2回送信してください。"
    
    # Subtitles Messages
    SUBTITLES_FAILED_MSG = "⚠️ 字幕のダウンロードに失敗しました"

    # Video Processing Messages

    # Stream/Link Messages
    STREAM_LINKS_TITLE_MSG = "🔗 <b>ダイレクトストリームリンク</b>\n\n"
    STREAM_TITLE_MSG = "📹 <b>タイトル:</b> {title}\n"
    STREAM_DURATION_MSG = "⏱ <b>期間:</b> {duration} 秒\n"

    
    # Download Progress Messages

    # Quality Selection Messages

    # NSFW Paid Content Messages

    # Callback Error Messages
    ERROR_ORIGINAL_NOT_FOUND_MSG = "❌ エラー: 元のメッセージが見つかりません。"

    # Tags Error Messages
    TAG_FORBIDDEN_CHARS_MSG = "❌ タグ #{tag} には禁止文字が含まれています。文字、数字、_ のみ使用できます。\n使用してください: {example}"
    
    # Playlist Messages
    PLAYLIST_SENT_MSG = "✅ プレイリストの動画を送信しました: {sent}/{total} ファイル。"
    PLAYLIST_CACHE_SENT_MSG = "✅ キャッシュから送信: {cached}/{total} ファイル。"
    
    # Failed Stream Messages
    FAILED_STREAM_LINKS_MSG = "❌ ストリームリンクの取得に失敗しました"

    # new messages
    # Browser Cookie Messages
    SELECT_BROWSER_MSG = "クッキーをダウンロードするブラウザを選択してください:"
    SELECT_BROWSER_NO_BROWSERS_MSG = "このシステムにブラウザが見つかりません。リモートURLからクッキーをダウンロードするか、ブラウザのステータスを監視できます:"
    BROWSER_MONITOR_HINT_MSG = "🌐 <b>ブラウザを開く</b> - ミニアプリでブラウザのステータスを監視します"
    BROWSER_OPEN_BUTTON_MSG = "🌐 ブラウザを開く"
    DOWNLOAD_FROM_URL_BUTTON_MSG = "📥 リモートURLからダウンロード"
    COOKIE_YT_FALLBACK_SAVED_MSG = "✅ YouTubeクッキーファイルがフォールバック経由でダウンロードされ、cookie.txtとして保存されました"
    COOKIES_NO_BROWSERS_NO_URL_MSG = "❌ 対応しているブラウザが見つからず、COOKIE_URLも設定されていません。/cookieを使用するか、cookie.txtをアップロードしてください。"
    COOKIE_FALLBACK_URL_NOT_TXT_MSG = "❌ フォールバックCOOKIE_URLは.txtファイルを指している必要があります。"
    COOKIE_FALLBACK_TOO_LARGE_MSG = "❌ フォールバッククッキーファイルが大きすぎます(>100KB)。"
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "❌ フォールバッククッキーソースが利用できません(ステータス {status})。/cookieを試すか、cookie.txtをアップロードしてください。"
    COOKIE_FALLBACK_ERROR_MSG = "❌ フォールバッククッキーのダウンロード中にエラーが発生しました。/cookieを試すか、cookie.txtをアップロードしてください。"
    COOKIE_FALLBACK_UNEXPECTED_MSG = "❌ フォールバッククッキーのダウンロード中に予期しないエラーが発生しました。"
    BTN_CLOSE = "🔚閉じる"
    
    # Args command messages
    ARGS_INVALID_BOOL_MSG = "❌ 無効なブール値"
    ARGS_CLOSED_MSG = "閉鎖"
    ARGS_ALL_RESET_MSG = "✅ すべての引数がリセットされました"
    ARGS_RESET_ERROR_MSG = "❌ 引数のリセット中にエラーが発生しました"
    ARGS_INVALID_PARAM_MSG = "❌ 無効なパラメータ"
    ARGS_BOOL_SET_MSG = "{value}に設定"
    ARGS_BOOL_ALREADY_SET_MSG = "すでに{value}に設定されています"
    ARGS_INVALID_SELECT_MSG = "❌ 無効な選択値"
    ARGS_VALUE_SET_MSG = "{value}に設定"
    ARGS_VALUE_ALREADY_SET_MSG = "すでに{value}に設定されています"
    ARGS_PARAM_DESCRIPTION_MSG = "<b>📝 {description}</b>\n\n"
    ARGS_CURRENT_VALUE_MSG = "<b>現在の値:</b> <code>{current_value}</code>\n\n"
    ARGS_XFF_EXAMPLES_MSG = "<b>例:</b>\n• <code>default</code> - デフォルトのXFF戦略を使用\n• <code>never</code> - XFFヘッダーを使用しない\n• <code>US</code> - アメリカ合衆国の国コード\n• <code>GB</code> - イギリスの国コード\n• <code>DE</code> - ドイツの国コード\n• <code>FR</code> - フランスの国コード\n• <code>JP</code> - 日本の国コード\n• <code>192.168.1.0/24</code> - IPブロック (CIDR)\n• <code>10.0.0.0/8</code> - プライベートIP範囲\n• <code>203.0.113.0/24</code> - パブリックIPブロック\n\n"
    ARGS_XFF_NOTE_MSG = "<b>注意:</b> これは--geo-bypassオプションを置き換えます。任意の2文字の国コードまたはCIDR表記のIPブロックを使用してください。\n\n"
    ARGS_EXAMPLE_MSG = "<b>例:</b> <code>{placeholder}</code>\n\n"
    ARGS_SEND_VALUE_MSG = "新しい値を送信してください。"
    ARGS_NUMBER_PARAM_MSG = "<b>🔢 {description}</b>\n\n"
    ARGS_RANGE_MSG = "<b>範囲:</b> {min_val} - {max_val}\n\n"
    ARGS_SEND_NUMBER_MSG = "数値を送信してください。"
    ARGS_JSON_PARAM_MSG = "<b>🔧 {description}</b>\n\n"
    ARGS_HTTP_HEADERS_EXAMPLES_MSG = "<b>例:</b>\n<code>{placeholder}</code>\n<code>{{\"X-API-Key\": \"your-key\"}}</code>\n<code>{{\"Authorization\": \"Bearer token\"}}</code>\n<code>{{\"Accept\": \"application/json\"}}</code>\n<code>{{\"X-Custom-Header\": \"value\"}}</code>\n\n"
    ARGS_HTTP_HEADERS_NOTE_MSG = "<b>注意:</b> これらのヘッダーは、既存のRefererおよびUser-Agentヘッダーに追加されます。\n\n"
    ARGS_CURRENT_ARGS_MSG = "<b>📋 現在のyt-dlp引数:</b>\n\n"
    ARGS_MENU_DESCRIPTION_MSG = "• ✅/❌ <b>ブール値</b> - True/Falseスイッチ\n• 📋 <b>選択</b> - オプションから選択\n• 🔢 <b>数値</b> - 数値入力\n• 📝🔧 <b>テキスト</b> - テキスト/JSON入力</div>\n\nこれらの設定はすべてのダウンロードに適用されます。"
    
    # Localized parameter names for display
    ARGS_PARAM_NAMES = {
        "force_ipv6": "IPv6接続を強制",
        "force_ipv4": "IPv4接続を強制", 
        "no_live_from_start": "ライブストリームを最初からダウンロードしない",
        "live_from_start": "ライブストリームを最初からダウンロードする",
        "no_check_certificates": "HTTPS証明書の検証を抑制",
        "check_certificate": "SSL証明書を確認",
        "no_playlist": "プレイリストではなく単一のビデオのみをダウンロード",
        "embed_metadata": "ビデオファイルにメタデータを埋め込む",
        "embed_thumbnail": "ビデオファイルにサムネイルを埋め込む",
        "write_thumbnail": "サムネイルをファイルに書き込む",
        "ignore_errors": "ダウンロードエラーを無視して続行",
        "legacy_server_connect": "レガシーサーバー接続を許可",
        "concurrent_fragments": "同時にダウンロードするフラグメントの数",
        "xff": "X-Forwarded-Forヘッダー戦略",
        "user_agent": "User-Agentヘッダー",
        "impersonate": "ブラウザの偽装",
        "referer": "Refererヘッダー",
        "geo_bypass": "地理的制限をバイパス",
        "hls_use_mpegts": "HLSにMPEG-TSを使用",
        "no_part": ".partファイルを使用しない",
        "no_continue": "部分的なダウンロードを再開しない",
        "audio_format": "オーディオ形式",
        "video_format": "ビデオ形式",
        "merge_output_format": "出力形式をマージ",
        "send_as_file": "ファイルとして送信",
        "username": "ユーザー名",
        "password": "パスワード",
        "twofactor": "2要素認証コード",
        "min_filesize": "最小ファイルサイズ (MB)",
        "max_filesize": "最大ファイルサイズ (MB)",
        "playlist_items": "プレイリストアイテム",
        "date": "日付",
        "datebefore": "以前の日付",
        "dateafter": "以降の日付",
        "http_headers": "HTTPヘッダー",
        "sleep_interval": "スリープ間隔",
        "max_sleep_interval": "最大スリープ間隔",
        "retries": "再試行回数",
        "http_chunk_size": "HTTPチャンクサイズ",
        "sleep_subtitles": "字幕のスリープ"
    }
    ARGS_CONFIG_TITLE_MSG = "<b>⚙️ yt-dlp引数設定</b>\n\n<blockquote>📋 <b>グループ:</b>\n{groups_msg}"
    ARGS_MENU_TEXT = (
        "<b>⚙️ yt-dlp引数設定</b>\n\n"
        "<blockquote>📋 <b>グループ:</b>\n"
        "• ✅/❌ <b>ブール値</b> - True/Falseスイッチ\n"
        "• 📋 <b>選択</b> - オプションから選択\n"
        "• 🔢 <b>数値</b> - 数値入力\n"
        "• 📝🔧 <b>テキスト</b> - テキスト/JSON入力</blockquote>\n\n"
        "これらの設定はすべてのダウンロードに適用されます。"
    )
    
    # Additional missing messages
    PLEASE_WAIT_MSG = "⏳ しばらくお待ちください..."
    ERROR_OCCURRED_SHORT_MSG = "❌ エラーが発生しました"

    # Args command messages (continued)
    ARGS_INPUT_TIMEOUT_MSG = "⏰ 非アクティブのため、入力モードが自動的に閉じられました (5分)。"
    ARGS_INPUT_DANGEROUS_MSG = "❌ 入力に危険な可能性のあるコンテンツが含まれています: {pattern}"
    ARGS_INPUT_TOO_LONG_MSG = "❌ 入力が長すぎます (最大1000文字)"
    ARGS_INVALID_URL_MSG = "❌ 無効なURL形式です。http://またはhttps://で始まる必要があります"
    ARGS_INVALID_JSON_MSG = "❌ 無効なJSON形式です"
    ARGS_NUMBER_RANGE_MSG = "❌ 数値は{min_val}から{max_val}の間でなければなりません"
    ARGS_INVALID_NUMBER_MSG = "❌ 無効な数値形式です"
    ARGS_DATE_FORMAT_MSG = "❌ 日付はYYYYMMDD形式でなければなりません (例: 20230930)"
    ARGS_YEAR_RANGE_MSG = "❌年は1900年から2100年の間でなければなりません"
    ARGS_MONTH_RANGE_MSG = "❌月は01から12の間でなければなりません"
    ARGS_DAY_RANGE_MSG = "❌日は01から31の間でなければなりません"
    ARGS_INVALID_DATE_MSG = "❌ 無効な日付形式"
    ARGS_INVALID_XFF_MSG = "❌ XFFは'default'、'never'、国コード(例: US)、またはIPブロック(例: 192.168.1.0/24)でなければなりません"
    ARGS_NO_CUSTOM_MSG = "カスタム引数は設定されていません。すべてのパラメータはデフォルト値を使用します。"
    ARGS_RESET_SUCCESS_MSG = "✅ すべての引数がデフォルトにリセットされました。"
    ARGS_TEXT_TOO_LONG_MSG = "❌ テキストが長すぎます。最大500文字。"
    ARGS_ERROR_PROCESSING_MSG = "❌ 入力処理中にエラーが発生しました。もう一度お試しください。"
    ARGS_BOOL_INPUT_MSG = "❌ ファイルとして送信オプションには'True'または'False'を入力してください。"
    ARGS_INVALID_NUMBER_INPUT_MSG = "❌ 有効な数値を入力してください。"
    ARGS_BOOL_VALUE_REQUEST_MSG = "このオプションを有効/無効にするには、<code>True</code>または<code>False</code>を送信してください。"
    ARGS_JSON_VALUE_REQUEST_MSG = "有効なJSONを送信してください。"
    
    # Tags command messages
    TAGS_NO_TAGS_MSG = "まだタグがありません。"
    TAGS_MESSAGE_CLOSED_MSG = "タグメッセージを閉じました。"
    
    # Subtitles command messages
    SUBS_DISABLED_MSG = "✅ 字幕が無効になり、常時確認モードがオフになりました。"
    SUBS_ALWAYS_ASK_ENABLED_MSG = "✅ SUBS常時確認が有効になりました。"
    SUBS_LANGUAGE_SET_MSG = "✅ 字幕言語をに設定しました: {flag} {name}"
    SUBS_WARNING_MSG = (
        "<blockquote>❗️警告: CPUへの影響が大きいため、この機能は非常に遅く(ほぼリアルタイム)、以下に制限されています:\n"
        "- 720p 最大品質\n"
        "- 1.5時間 最大期間\n"
        "- 500MB 最大ビデオサイズ</blockquote>\n\n"
    )
    SUBS_QUICK_COMMANDS_MSG = (
        "<b>クイックコマンド:</b>\n"
        "• <code>/subs off</code> - 字幕を無効にする\n"
        "• <code>/subs on</code> - 常時確認モードを有効にする\n"
        "• <code>/subs ru</code> - 言語を設定\n"
        "• <code>/subs ru auto</code> - AUTO/TRANSで言語を設定"
    )
    SUBS_DISABLED_STATUS_MSG = "🚫 字幕は無効です"
    SUBS_SELECTED_LANGUAGE_MSG = "{flag} 選択した言語: {name}{auto_text}"
    SUBS_DOWNLOADING_MSG = "💬 字幕をダウンロードしています..."
    SUBS_DISABLED_ERROR_MSG = "❌ 字幕は無効です。/subsを使用して設定してください。"
    SUBS_YOUTUBE_ONLY_MSG = "❌ 字幕のダウンロードはYouTubeでのみサポートされています。"
    SUBS_CAPTION_MSG = (
        "<b>💬 字幕</b>\n\n"
        "<b>ビデオ:</b> {title}\n"
        "<b>言語:</b> {lang}\n"
        "<b>タイプ:</b> {type}\n\n"
        "{tags}"
    )
    SUBS_SENT_MSG = "💬 字幕SRTファイルがユーザーに送信されました。"
    SUBS_ERROR_PROCESSING_MSG = "❌ 字幕ファイルの処理中にエラーが発生しました。"
    SUBS_ERROR_DOWNLOAD_MSG = "❌ 字幕のダウンロードに失敗しました。"
    SUBS_ERROR_MSG = "❌ 字幕のダウンロード中にエラーが発生しました: {error}"
    
    # Split command messages
    SPLIT_SIZE_SET_MSG = "✅ 分割パートサイズをに設定しました: {size}"
    SPLIT_INVALID_SIZE_MSG = (
        "❌ **無効なサイズです！**\n\n"
        "**有効な範囲:** 100MBから2GB\n\n"
        "**有効な形式:**\n"
        "• `100mb`から`2000mb` (メガバイト)\n"
        "• `0.1gb`から`2gb` (ギガバイト)\n\n"
        "**例:**\n"
        "• `/split 100mb` - 100メガバイト\n"
        "• `/split 500mb` - 500メガバイト\n"
        "• `/split 1.5gb` - 1.5ギガバイト\n"
        "• `/split 2gb` - 2ギガバイト\n"
        "• `/split 2000mb` - 2000メガバイト (2GB)\n\n"
        "**プリセット:**\n"
        "• `/split 250mb`, `/split 500mb`, `/split 1gb`, `/split 1.5gb`, `/split 2gb`"
    )
    SPLIT_MENU_TITLE_MSG = (
        "🎬 **ビデオ分割の最大パートサイズを選択してください:**\n\n"
        "**範囲:** 100MBから2GB\n\n"
        "**クイックコマンド:**\n"
        "• `/split 100mb` - `/split 2000mb`\n"
        "• `/split 0.1gb` - `/split 2gb`\n\n"
        "**例:** `/split 300mb`, `/split 1.2gb`, `/split 1500mb`"
    )
    SPLIT_MENU_CLOSED_MSG = "メニューを閉じました。"
    
    # Settings command messages
    SETTINGS_TITLE_MSG = "<b>ボット設定</b>\n\nカテゴリを選択してください:"
    SETTINGS_MENU_CLOSED_MSG = "メニューを閉じました。"
    SETTINGS_CLEAN_TITLE_MSG = "<b>🧹 クリーンオプション</b>\n\n何をクリーンアップしますか:"
    SETTINGS_COOKIES_TITLE_MSG = "<b>🍪 クッキー</b>\n\nアクションを選択してください:"
    SETTINGS_MEDIA_TITLE_MSG = "<b>🎞 メディア</b>\n\nアクションを選択してください:"
    SETTINGS_LOGS_TITLE_MSG = "<b>📖 情報</b>\n\nアクションを選択してください:"
    SETTINGS_MORE_TITLE_MSG = "<b>⚙️ その他のコマンド</b>\n\nアクションを選択してください:"
    SETTINGS_COMMAND_EXECUTED_MSG = "コマンドが実行されました。"
    SETTINGS_FLOOD_LIMIT_MSG = "⏳ フラッド制限。後でもう一度お試しください。"
    SETTINGS_HINT_SENT_MSG = "ヒントを送信しました。"
    SETTINGS_SEARCH_HELPER_OPENED_MSG = "検索ヘルパーを開きました。"
    SETTINGS_UNKNOWN_COMMAND_MSG = "不明なコマンド。"
    SETTINGS_HINT_CLOSED_MSG = "ヒントを閉じました。"
    SETTINGS_HELP_SENT_MSG = "ヘルプテキストをユーザーに送信"
    SETTINGS_MENU_OPENED_MSG = "/settingsメニューを開きました"
    
    # Search command messages
    SEARCH_HELPER_CLOSED_MSG = "🔍 検索ヘルパーを閉じました"
    SEARCH_CLOSED_MSG = "閉鎖"
    
    # Proxy command messages
    PROXY_ENABLED_MSG = "✅ プロキシ {status}。"
    PROXY_ERROR_SAVING_MSG = "❌ プロキシ設定の保存中にエラーが発生しました。"
    PROXY_MENU_TEXT_MSG = "すべてのyt-dlp操作でプロキシサーバーを使用しますか?"
    PROXY_MENU_TEXT_MULTIPLE_MSG = "すべてのyt-dlp操作で({count}個の利用可能な)プロキシサーバーを使用しますか?\n\n有効にすると、プロキシは{method}メソッドを使用して選択されます。"
    PROXY_MENU_CLOSED_MSG = "メニューを閉じました。"
    PROXY_ENABLED_CONFIRM_MSG = "✅ プロキシが有効になりました。すべてのyt-dlp操作でプロキシが使用されます。"
    PROXY_ENABLED_MULTIPLE_MSG = "✅ プロキシが有効になりました。すべてのyt-dlp操作で{method}選択メソッドを使用して{count}個のプロキシサーバーが使用されます。"
    PROXY_DISABLED_MSG = "❌ プロキシが無効になりました。"
    PROXY_ERROR_SAVING_CALLBACK_MSG = "❌ プロキシ設定の保存中にエラーが発生しました。"
    PROXY_ENABLED_CALLBACK_MSG = "プロキシが有効になりました。"
    PROXY_DISABLED_CALLBACK_MSG = "プロキシが無効になりました。"
    
    # Other handlers messages
    AUDIO_WAIT_MSG = "⏰ 前のダウンロードが完了するまでお待ちください"
    AUDIO_HELP_MSG = (
        "<b>🎧 オーディオダウンロードコマンド</b>\n\n"
        "使用法: <code>/audio URL</code>\n\n"
        "<b>例:</b>\n"
        "• <code>/audio https://youtu.be/abc123</code>\n"
        "• <code>/audio https://www.youtube.com/watch?v=abc123</code>\n"
        "• <code>/audio https://www.youtube.com/playlist?list=PL123*1*10</code>\n"
        "• <code>/audio 1-10 https://www.youtube.com/playlist?list=PL123</code>\n\n"
        "こちらも参照: /vid, /img, /help, /playlist, /settings"
    )
    AUDIO_HELP_CLOSED_MSG = "オーディオヒントを閉じました。"
    PLAYLIST_HELP_CLOSED_MSG = "プレイリストヘルプを閉じました。"
    USERLOGS_CLOSED_MSG = "ログメッセージを閉じました。"
    HELP_CLOSED_MSG = "ヘルプを閉じました。"
    
    # NSFW command messages
    NSFW_BLUR_SETTINGS_TITLE_MSG = "🔞 <b>NSFWブラー設定</b>\n\nNSFWコンテンツは<b>{status}</b>です。\n\nNSFWコンテンツをぼかすかどうかを選択してください:"
    NSFW_MENU_CLOSED_MSG = "メニューを閉じました。"
    NSFW_BLUR_DISABLED_MSG = "NSFWブラーが無効になりました。"
    NSFW_BLUR_ENABLED_MSG = "NSFWブラーが有効になりました。"
    NSFW_BLUR_DISABLED_CALLBACK_MSG = "NSFWブラーが無効になりました。"
    NSFW_BLUR_ENABLED_CALLBACK_MSG = "NSFWブラーが有効になりました。"
    
    # MediaInfo command messages
    MEDIAINFO_ENABLED_MSG = "✅ MediaInfo {status}。"
    MEDIAINFO_MENU_TITLE_MSG = "ダウンロードしたファイルのMediaInfoを送信しますか?"
    MEDIAINFO_MENU_CLOSED_MSG = "メニューを閉じました。"
    MEDIAINFO_ENABLED_CONFIRM_MSG = "✅ MediaInfoが有効になりました。ダウンロード後、ファイル情報が送信されます。"
    MEDIAINFO_DISABLED_MSG = "❌ MediaInfoが無効になりました。"
    MEDIAINFO_ENABLED_CALLBACK_MSG = "MediaInfoが有効になりました。"
    MEDIAINFO_DISABLED_CALLBACK_MSG = "MediaInfoが無効になりました。"
    
    # List command messages
    LIST_HELP_MSG = (
        "<b>📃 利用可能なフォーマットを一覧表示</b>\n\n"
        "URLの利用可能なビデオ/オーディオフォーマットを取得します。\n\n"
        "<b>使用法:</b>\n"
        "<code>/list URL</code>\n\n"
        "<b>例:</b>\n"
        "• <code>/list https://youtube.com/watch?v=123abc</code>\n"
        "• <code>/list https://youtube.com/playlist?list=123abc</code>\n\n"
        "<b>💡 フォーマットIDの使用方法:</b>\n"
        "リストを取得した後、特定のフォーマットIDを使用します:\n"
        "• <code>/format id 401</code> - フォーマット401をダウンロード\n"
        "• <code>/format id401</code> - 上記と同じ\n"
        "• <code>/format id140 audio</code> - フォーマット140をMP3オーディオとしてダウンロード\n\n"
        "このコマンドは、ダウンロード可能なすべてのフォーマットを表示します。"
    )
    LIST_PROCESSING_MSG = "🔄 利用可能なフォーマットを取得しています..."
    LIST_INVALID_URL_MSG = "❌ http://またはhttps://で始まる有効なURLを入力してください"
    LIST_CAPTION_MSG = (
        "📃 利用可能なフォーマット:\n<code>{url}</code>\n\n"
        "💡 <b>フォーマットの設定方法:</b>\n"
        "• <code>/format id 134</code> - 特定のフォーマットIDをダウンロード\n"
        "• <code>/format 720p</code> - 品質でダウンロード\n"
        "• <code>/format best</code> - 最高品質をダウンロード\n"
        "• <code>/format ask</code> - 常に品質を尋ねる\n\n"
        "{audio_note}\n"
        "📋 上記のリストからフォーマットIDを使用してください"
    )
    LIST_AUDIO_FORMATS_MSG = (
        "🎵 <b>オーディオのみのフォーマット:</b> {formats}\n"
        "• <code>/format id 140 audio</code> - フォーマット140をMP3オーディオとしてダウンロード\n"
        "• <code>/format id140 audio</code> - 上記と同じ\n"
        "これらはMP3オーディオファイルとしてダウンロードされます。\n\n"
    )
    LIST_ERROR_SENDING_MSG = "❌ フォーマットファイルの送信中にエラーが発生しました: {error}"
    LIST_ERROR_GETTING_MSG = "❌ フォーマットの取得に失敗しました:\n<code>{error}</code>"
    LIST_ERROR_OCCURRED_MSG = "❌ コマンドの処理中にエラーが発生しました"
    LIST_ERROR_CALLBACK_MSG = "エラーが発生しました"
    LIST_HOW_TO_USE_FORMAT_IDS_TITLE = "💡 フォーマットIDの使用方法:\n"
    LIST_FORMAT_USAGE_INSTRUCTIONS = "リストを取得した後、特定のフォーマットIDを使用します:\n"
    LIST_FORMAT_EXAMPLE_401 = "• /format id 401 - フォーマット401をダウンロード\n"
    LIST_FORMAT_EXAMPLE_401_SHORT = "• /format id401 - 上記と同じ\n"
    LIST_FORMAT_EXAMPLE_140_AUDIO = "• /format id 140 audio - フォーマット140をMP3オーディオとしてダウンロード\n"
    LIST_FORMAT_EXAMPLE_140_AUDIO_SHORT = "• /format id140 audio - 上記と同じ\n"
    LIST_AUDIO_FORMATS_DETECTED = "🎵 オーディオのみのフォーマットが検出されました: {formats}\n"
    LIST_AUDIO_FORMATS_NOTE = "これらのフォーマットはMP3オーディオファイルとしてダウンロードされます。\n"
    LIST_VIDEO_ONLY_FORMATS_MSG = "🎬 <b>ビデオのみのフォーマット:</b> {formats}\n"
    LIST_USE_FORMAT_ID_MSG = "📋 上記のリストからフォーマットIDを使用してください"
    
    # Link command messages
    LINK_USAGE_MSG = (
        "🔗 <b>使用法:</b>\n"
        "<code>/link [quality] URL</code>\n\n"
        "<b>例:</b>\n"
        "<blockquote>"
        "• /link https://youtube.com/watch?v=... - 最高品質\n"
        "• /link 720 https://youtube.com/watch?v=... - 720p以下\n"
        "• /link 720p https://youtube.com/watch?v=... - 上記と同じ\n"
        "• /link 4k https://youtube.com/watch?v=... - 4K以下\n"
        "• /link 8k https://youtube.com/watch?v=... - 8K以下"
        "</blockquote>\n\n"
        "<b>品質:</b> 1から10000まで (例: 144, 240, 720, 1080)"
    )
    LINK_INVALID_URL_MSG = "❌ 有効なURLを入力してください"
    LINK_PROCESSING_MSG = "🔗 ダイレクトリンクを取得しています..."
    LINK_DURATION_MSG = "⏱ <b>期間:</b> {duration} 秒\n"
    LINK_VIDEO_STREAM_MSG = "🎬 <b>ビデオストリーム:</b>\n<blockquote expandable><a href=\"{url}\">{url}</a></blockquote>\n\n"
    LINK_AUDIO_STREAM_MSG = "🎵 <b>オーディオストリーム:</b>\n<blockquote expandable><a href=\"{url}\">{url}</a></blockquote>\n\n"
    
    # Keyboard command messages
    KEYBOARD_UPDATED_MSG = "🎹 **キーボード設定が更新されました！**\n\n新しい設定: **{setting}**"
    KEYBOARD_INVALID_ARG_MSG = (
        "❌ **無効な引数です！**\n\n"
        "有効なオプション: `off`, `1x3`, `2x3`, `full`\n\n"
        "例: `/keyboard off`"
    )
    KEYBOARD_SETTINGS_MSG = (
        "🎹 **キーボード設定**\n\n"
        "現在: **{current}**\n\n"
        "オプションを選択してください:\n\n"
        "または、`/keyboard off`, `/keyboard 1x3`, `/keyboard 2x3`, `/keyboard full`を使用してください"
    )
    KEYBOARD_ACTIVATED_MSG = "🎹 キーボードが有効になりました！"
    KEYBOARD_HIDDEN_MSG = "⌨️ キーボードが非表示になりました"
    KEYBOARD_1X3_ACTIVATED_MSG = "📱 1x3キーボードが有効になりました！"
    KEYBOARD_2X3_ACTIVATED_MSG = "📱 2x3キーボードが有効になりました！"
    KEYBOARD_EMOJI_ACTIVATED_MSG = "🔣 絵文字キーボードが有効になりました！"
    KEYBOARD_ERROR_APPLYING_MSG = "キーボード設定{setting}の適用中にエラーが発生しました: {error}"
    
    # Format command messages
    FORMAT_ALWAYS_ASK_SET_MSG = "✅ フォーマットが常時確認に設定されました。URLを送信するたびに品質を尋ねられます。"
    FORMAT_ALWAYS_ASK_CONFIRM_MSG = "✅ フォーマットが常時確認に設定されました。これからはURLを送信するたびに品質を尋ねられます。"
    FORMAT_BEST_UPDATED_MSG = "✅ フォーマットが最高品質(AVC+MP4優先)に更新されました:\n{format}"
    FORMAT_ID_UPDATED_MSG = "✅ フォーマットがID {id}に更新されました:\n{format}\n\n💡 <b>注意:</b> これがオーディオのみのフォーマットの場合、MP3オーディオファイルとしてダウンロードされます。"
    FORMAT_ID_AUDIO_UPDATED_MSG = "✅ フォーマットがID {id} (オーディオのみ)に更新されました:\n{format}\n\n💡 これはMP3オーディオファイルとしてダウンロードされます。"
    FORMAT_QUALITY_UPDATED_MSG = "✅ フォーマットが品質{quality}に更新されました:\n{format}"
    FORMAT_CUSTOM_UPDATED_MSG = "✅ フォーマットがに更新されました:\n{format}"
    FORMAT_MENU_MSG = (
        "フォーマットオプションを選択するか、以下を使用してカスタムオプションを送信してください:\n"
        "• <code>/format &lt;format_string&gt;</code> - カスタムフォーマット\n"
        "• <code>/format 720</code> - 720p品質\n"
        "• <code>/format 4k</code> - 4K品質\n"
        "• <code>/format 8k</code> - 8K品質\n"
        "• <code>/format id 401</code> - 特定のフォーマットID\n"
        "• <code>/format ask</code> - 常にメニューを表示\n"
        "• <code>/format best</code> - bv+ba/最高品質"
    )
    FORMAT_CUSTOM_HINT_MSG = (
        "カスタムフォーマットを使用するには、次の形式でコマンドを送信してください:\n\n"
        "<code>/format bestvideo+bestaudio/best</code>\n\n"
        "<code>bestvideo+bestaudio/best</code>を目的のフォーマット文字列に置き換えてください。"
    )
    FORMAT_RESOLUTION_MENU_MSG = "目的の解像度とコーデックを選択してください:"
    FORMAT_ALWAYS_ASK_CONFIRM_MSG = "✅ フォーマットが常時確認に設定されました。これからはURLを送信するたびに品質を尋ねられます。"
    FORMAT_UPDATED_MSG = "✅ フォーマットがに更新されました:\n{format}"
    FORMAT_SAVED_MSG = "✅ フォーマットが保存されました。"
    FORMAT_CHOICE_UPDATED_MSG = "✅ フォーマットの選択が更新されました。"
    FORMAT_CUSTOM_MENU_CLOSED_MSG = "カスタムフォーマットメニューを閉じました"
    FORMAT_CODEC_SET_MSG = "✅ コーデックを{codec}に設定"
    
    # Cookies command messages
    COOKIES_BROWSER_CHOICE_UPDATED_MSG = "✅ ブラウザの選択が更新されました。"
    
    # Clean command messages
    
    # Admin command messages
    ADMIN_ACCESS_DENIED_MSG = "❌ アクセスが拒否されました。管理者のみ。"
    ACCESS_DENIED_ADMIN = "❌ アクセスが拒否されました。管理者のみ。"
    WELCOME_MASTER = "ようこそマスター 🥷"
    DOWNLOAD_ERROR_GENERIC = "❌ 申し訳ありません...ダウンロード中にエラーが発生しました。"
    SIZE_LIMIT_EXCEEDED = "❌ ファイルサイズが{max_size_gb} GBの制限を超えています。許可されたサイズ内の小さいファイルを選択してください。"
    ADMIN_SCRIPT_NOT_FOUND_MSG = "❌ スクリプトが見つかりません: {script_path}"
    ADMIN_DOWNLOADING_MSG = "⏳ {script_path}を使用して新しいFirebaseダンプをダウンロードしています..."
    ADMIN_CACHE_RELOADED_MSG = "✅ Firebaseキャッシュが正常にリロードされました！"
    ADMIN_CACHE_FAILED_MSG = "❌ Firebaseキャッシュのリロードに失敗しました。{cache_file}が存在するか確認してください。"
    ADMIN_ERROR_RELOADING_MSG = "❌ キャッシュのリロード中にエラーが発生しました: {error}"
    ADMIN_ERROR_SCRIPT_MSG = "❌ {script_path}の実行中にエラーが発生しました:\n{stdout}\n{stderr}"
    ADMIN_PROMO_SENT_MSG = "<b>✅ プロモーションメッセージが他のすべてのユーザーに送信されました</b>"
    ADMIN_CANNOT_SEND_PROMO_MSG = "<b>❌ プロモーションメッセージを送信できません。メッセージに返信してみてください\nまたはエラーが発生しました</b>"
    ADMIN_USER_NO_DOWNLOADS_MSG = "<b>❌ ユーザーはまだコンテンツをダウンロードしていません...</b> ログに存在しません"
    ADMIN_INVALID_COMMAND_MSG = "❌ 無効なコマンド"
    ADMIN_NO_DATA_FOUND_MSG = f"❌ <code>{{path}}</code>のキャッシュにデータが見つかりません"
    CHANNEL_GUARD_PENDING_EMPTY_MSG = "🛡️ キューは空です — まだ誰もチャンネルを離れていません。"
    CHANNEL_GUARD_PENDING_HEADER_MSG = "🛡️ <b>禁止キュー</b>\n保留中の合計: {total}"
    CHANNEL_GUARD_PENDING_ROW_MSG = "• <code>{user_id}</code> — {name} @{username} (最終退出: {last_left})"
    CHANNEL_GUARD_PENDING_MORE_MSG = "… さらに{extra}人のユーザー。"
    CHANNEL_GUARD_PENDING_FOOTER_MSG = "/block_user show • all • auto • 10sを使用してください"
    CHANNEL_GUARD_BLOCKED_ALL_MSG = "✅ キューからユーザーをブロックしました: {count}"
    CHANNEL_GUARD_AUTO_ENABLED_MSG = "⚙️ 自動ブロックが有効になりました: 新しい離脱者はすぐに禁止されます。"
    CHANNEL_GUARD_AUTO_DISABLED_MSG = "⏸ 自動ブロックが無効になりました。"
    CHANNEL_GUARD_AUTO_INTERVAL_SET_MSG = "⏱ スケジュールされた自動ブロックウィンドウが{interval}ごとに設定されました。"
    CHANNEL_GUARD_ACTIVITY_FILE_CAPTION_MSG = "🗂 過去{hours}時間(2日間)のチャンネルアクティビティログ。"
    CHANNEL_GUARD_ACTIVITY_SUMMARY_MSG = "📝 過去{hours}時間(2日間): 参加{joined}、退出{left}。"
    CHANNEL_GUARD_ACTIVITY_EMPTY_MSG = "ℹ️ 過去{hours}時間(2日間)のアクティビティはありません。"
    CHANNEL_GUARD_ACTIVITY_TOTALS_LINE_MSG = "合計: 🟢 {joined} 参加、🔴 {left} 退出。"
    CHANNEL_GUARD_NO_ACCESS_MSG = "❌ チャンネルアクティビティログにアクセスできません。ボットは管理者ログを読み取ることができません。この機能を有効にするには、ユーザーセッションで構成にCHANNEL_GUARD_SESSION_STRINGを指定してください。"
    BAN_TIME_USAGE_MSG = "❌ 使用法: {command} <10s|6m|5h|4d|3w|2M|1y>"
    BAN_TIME_INTERVAL_INVALID_MSG = "❌ 10s、6m、5h、4d、3w、2M、1yなどの形式を使用してください。"
    BAN_TIME_SET_MSG = "🕒 チャンネルログのスキャン間隔が{interval}に設定されました。"
    BAN_TIME_REPORT_MSG = (
        "🛡️ チャンネルスキャンレポート\n"
        "実行時刻: {run_ts}\n"
        "間隔: {interval}\n"
        "新しい離脱者: {new_leavers}\n"
        "自動禁止: {auto_banned}\n"
        "保留中: {pending}\n"
        "最終イベントID: {last_event_id}"
    )
    ADMIN_BLOCK_USER_USAGE_MSG = "❌ 使用法: /block_user <user_id>"
    ADMIN_CANNOT_DELETE_ADMIN_MSG = "🚫 管理者は管理者を削除できません"
    ADMIN_USER_BLOCKED_MSG = "ユーザーがブロックされました 🔒❌\n \nID: <code>{user_id}</code>\nブロックされた日付: {date}"
    ADMIN_USER_ALREADY_BLOCKED_MSG = "<code>{user_id}</code>はすでにブロックされています ❌😐"
    ADMIN_NOT_ADMIN_MSG = "🚫 申し訳ありません！ あなたは管理者ではありません"
    ADMIN_UNBLOCK_USER_USAGE_MSG = "❌ 使用法: /unblock_user <user_id>"
    ADMIN_USER_UNBLOCKED_MSG = "ユーザーのブロックが解除されました 🔓✅\n \nID: <code>{user_id}</code>\nブロック解除日: {date}"
    ADMIN_USER_ALREADY_UNBLOCKED_MSG = "<code>{user_id}</code>はすでにブロック解除されています ✅😐"
    ADMIN_UNBLOCK_ALL_DONE_MSG = "✅ ブロック解除されたユーザー: {count}\n⏱ タイムスタンプ: {date}"
    ADMIN_BOT_RUNNING_TIME_MSG = "⏳ <i>ボットの実行時間 -</i> <b>{time}</b>"
    ADMIN_UNCACHE_USAGE_MSG = "❌ キャッシュをクリアするURLを入力してください。\n使用法: <code>/uncache &lt;URL&gt;</code>"
    ADMIN_UNCACHE_INVALID_URL_MSG = "❌ 有効なURLを入力してください。\n使用法: <code>/uncache &lt;URL&gt;</code>"
    ADMIN_CACHE_CLEARED_MSG = "✅ URLのキャッシュが正常にクリアされました:\n<code>{url}</code>"
    ADMIN_NO_CACHE_FOUND_MSG = "ℹ️ このリンクのキャッシュが見つかりません。"
    ADMIN_ERROR_CLEARING_CACHE_MSG = "❌ キャッシュのクリア中にエラーが発生しました: {error}"
    ADMIN_ACCESS_DENIED_MSG = "❌ アクセスが拒否されました。管理者のみ。"
    ADMIN_UPDATE_PORN_RUNNING_MSG = "⏳ ポルノリスト更新スクリプトを実行しています: {script_path}"
    ADMIN_SCRIPT_COMPLETED_MSG = "✅ スクリプトが正常に完了しました！"
    ADMIN_SCRIPT_COMPLETED_WITH_OUTPUT_MSG = "✅ スクリプトが正常に完了しました！\n\n出力:\n<code>{output}</code>"
    ADMIN_SCRIPT_FAILED_MSG = "❌ スクリプトがリターンコード{returncode}で失敗しました:\n<code>{error}</code>"
    ADMIN_ERROR_RUNNING_SCRIPT_MSG = "❌ スクリプトの実行中にエラーが発生しました: {error}"
    ADMIN_RELOADING_PORN_MSG = "⏳ ポルノおよびドメイン関連のキャッシュをリロードしています..."
    ADMIN_PORN_CACHES_RELOADED_MSG = (
        "✅ ポルノキャッシュが正常にリロードされました！\n\n"
        "📊 現在のキャッシュステータス:\n"
        "• ポルノドメイン: {porn_domains}\n"
        "• ポルノキーワード: {porn_keywords}\n"
        "• サポートされているサイト: {supported_sites}\n"
        "• ホワイトリスト: {whitelist}\n"
        "• グレーリスト: {greylist}\n"
        "• ブラックリスト: {black_list}\n"
        "• ホワイトキーワード: {white_keywords}\n"
        "• プロキシドメイン: {proxy_domains}\n"
        "• プロキシ2ドメイン: {proxy_2_domains}\n"
        "• クリーンクエリ: {clean_query}\n"
        "• 非クッキードメイン: {no_cookie_domains}"
    )
    ADMIN_ERROR_RELOADING_PORN_MSG = "❌ ポルノキャッシュのリロード中にエラーが発生しました: {error}"
    ADMIN_CHECK_PORN_USAGE_MSG = "❌ 確認するURLを入力してください。\n使用法: <code>/check_porn &lt;URL&gt;</code>"
    ADMIN_CHECK_PORN_INVALID_URL_MSG = "❌ 有効なURLを入力してください。\n使用法: <code>/check_porn &lt;URL&gt;</code>"
    ADMIN_CHECKING_URL_MSG = "🔍 NSFWコンテンツのURLを確認しています...\n<code>{url}</code>"
    ADMIN_PORN_CHECK_RESULT_MSG = (
        "{status_icon} <b>ポルノチェック結果</b>\n\n"
        "<b>URL:</b> <code>{url}</code>\n"
        "<b>ステータス:</b> <b>{status_text}</b>\n\n"
        "<b>説明:</b>\n{explanation}"
    )
    ADMIN_ERROR_CHECKING_URL_MSG = "❌ URLの確認中にエラーが発生しました: {error}"
    
    # Clean command messages
    CLEAN_COOKIES_CLEANED_MSG = "クッキーをクリーンアップしました。"
    CLEAN_LOGS_CLEANED_MSG = "ログをクリーンアップしました。"
    CLEAN_TAGS_CLEANED_MSG = "タグをクリーンアップしました。"
    CLEAN_FORMAT_CLEANED_MSG = "フォーマットをクリーンアップしました。"
    CLEAN_SPLIT_CLEANED_MSG = "分割をクリーンアップしました。"
    CLEAN_MEDIAINFO_CLEANED_MSG = "メディア情報をクリーンアップしました。"
    CLEAN_SUBS_CLEANED_MSG = "字幕設定をクリーンアップしました。"
    CLEAN_KEYBOARD_CLEANED_MSG = "キーボード設定をクリーンアップしました。"
    CLEAN_ARGS_CLEANED_MSG = "引数設定をクリーンアップしました。"
    CLEAN_NSFW_CLEANED_MSG = "NSFW設定をクリーンアップしました。"
    CLEAN_PROXY_CLEANED_MSG = "プロキシ設定をクリーンアップしました。"
    CLEAN_FLOOD_WAIT_CLEANED_MSG = "フラッド待機設定をクリーンアップしました。"
    CLEAN_ALL_CLEANED_MSG = "すべてのファイルをクリーンアップしました。"
    CLEAN_COOKIES_MENU_TITLE_MSG = "<b>🍪 クッキー</b>\n\nアクションを選択してください:"
    
    # Cookies command messages
    COOKIES_FILE_SAVED_MSG = "✅ クッキーファイルが保存されました"
    COOKIES_SKIPPED_VALIDATION_MSG = "✅ YouTube以外のクッキーの検証をスキップしました"
    COOKIES_INCORRECT_FORMAT_MSG = "⚠️ クッキーファイルは存在しますが、形式が正しくありません"
    COOKIES_FILE_NOT_FOUND_MSG = "❌ クッキーファイルが見つかりません。"
    COOKIES_YOUTUBE_TEST_START_MSG = "🔄 YouTubeクッキーのテストを開始しています...\n\nクッキーを確認して検証する間、しばらくお待ちください。"
    COOKIES_YOUTUBE_WORKING_MSG = "✅ 既存のYouTubeクッキーは正常に機能しています！\n\n新しいものをダウンロードする必要はありません。"
    COOKIES_YOUTUBE_EXPIRED_MSG = "❌ 既存のYouTubeクッキーは期限切れまたは無効です。\n\n🔄 新しいクッキーをダウンロードしています..."
    COOKIES_SOURCE_NOT_CONFIGURED_MSG = "❌ {service}クッキーソースが設定されていません！"
    COOKIES_SOURCE_MUST_BE_TXT_MSG = "❌ {service}クッキーソースは.txtファイルである必要があります！"
    
    # Image command messages
    IMG_RANGE_LIMIT_EXCEEDED_MSG = "❗️ 範囲制限を超えました: {range_count}ファイルがリクエストされました (最大{max_img_files})。\n\n利用可能な最大数のファイルをダウンロードするには、次のいずれかのコマンドを使用してください:\n\n<code>/img {start_range}-{end_range} {url}</code>\n\n<code>/img {suggested_command_url_format}</code>"
    COMMAND_IMAGE_HELP_CLOSE_BUTTON_MSG = "🔚閉じる"
    COMMAND_IMAGE_MEDIA_LIMIT_EXCEEDED_MSG = "❗️ メディア制限を超えました: {count}ファイルがリクエストされました (最大{max_count})。\n\n利用可能な最大数のファイルをダウンロードするには、次のいずれかのコマンドを使用してください:\n\n<code>/img {start_range}-{end_range} {url}</code>\n\n<code>/img {suggested_command_url_format}</code>"
    IMG_FOUND_MEDIA_ITEMS_MSG = "📊 リンクから<b>{count}</b>個のメディアアイテムが見つかりました"
    IMG_SELECT_DOWNLOAD_RANGE_MSG = "ダウンロード範囲を選択してください:"
    
    # Args command parameter descriptions
    ARGS_IMPERSONATE_DESC_MSG = "ブラウザの偽装"
    ARGS_REFERER_DESC_MSG = "Refererヘッダー"
    ARGS_USER_AGENT_DESC_MSG = "User-Agentヘッダー"
    ARGS_GEO_BYPASS_DESC_MSG = "地理的制限をバイパス"
    ARGS_CHECK_CERTIFICATE_DESC_MSG = "SSL証明書を確認"
    ARGS_LIVE_FROM_START_DESC_MSG = "ライブストリームを最初からダウンロードする"
    ARGS_NO_LIVE_FROM_START_DESC_MSG = "ライブストリームを最初からダウンロードしない"
    ARGS_HLS_USE_MPEGTS_DESC_MSG = "HLSビデオにMPEG-TSコンテナを使用する"
    ARGS_NO_PLAYLIST_DESC_MSG = "プレイリストではなく単一のビデオのみをダウンロード"
    ARGS_NO_PART_DESC_MSG = ".partファイルを使用しない"
    ARGS_NO_CONTINUE_DESC_MSG = "部分的なダウンロードを再開しない"
    ARGS_AUDIO_FORMAT_DESC_MSG = "抽出用のオーディオ形式"
    ARGS_EMBED_METADATA_DESC_MSG = "ビデオファイルにメタデータを埋め込む"
    ARGS_EMBED_THUMBNAIL_DESC_MSG = "ビデオファイルにサムネイルを埋め込む"
    ARGS_WRITE_THUMBNAIL_DESC_MSG = "サムネイルをファイルに書き込む"
    ARGS_CONCURRENT_FRAGMENTS_DESC_MSG = "同時にダウンロードするフラグメントの数"
    ARGS_FORCE_IPV4_DESC_MSG = "IPv4接続を強制"
    ARGS_FORCE_IPV6_DESC_MSG = "IPv6接続を強制"
    ARGS_XFF_DESC_MSG = "X-Forwarded-Forヘッダー戦略"
    ARGS_HTTP_CHUNK_SIZE_DESC_MSG = "HTTPチャンクサイズ (バイト)"
    ARGS_SLEEP_SUBTITLES_DESC_MSG = "字幕ダウンロード前のスリープ (秒)"
    ARGS_LEGACY_SERVER_CONNECT_DESC_MSG = "レガシーサーバー接続を許可"
    ARGS_NO_CHECK_CERTIFICATES_DESC_MSG = "HTTPS証明書の検証を抑制"
    ARGS_USERNAME_DESC_MSG = "アカウントのユーザー名"
    ARGS_PASSWORD_DESC_MSG = "アカウントのパスワード"
    ARGS_TWOFACTOR_DESC_MSG = "2要素認証コード"
    ARGS_IGNORE_ERRORS_DESC_MSG = "ダウンロードエラーを無視して続行"
    ARGS_MIN_FILESIZE_DESC_MSG = "最小ファイルサイズ (MB)"
    ARGS_MAX_FILESIZE_DESC_MSG = "最大ファイルサイズ (MB)"
    ARGS_PLAYLIST_ITEMS_DESC_MSG = "ダウンロードするプレイリストアイテム (例: 1,3,5または1-5)"
    ARGS_DATE_DESC_MSG = "この日にアップロードされたビデオをダウンロード (YYYYMMDD)"
    ARGS_DATEBEFORE_DESC_MSG = "この日より前にアップロードされたビデオをダウンロード (YYYYMMDD)"
    ARGS_DATEAFTER_DESC_MSG = "この日以降にアップロードされたビデオをダウンロード (YYYYMMDD)"
    ARGS_HTTP_HEADERS_DESC_MSG = "カスタムHTTPヘッダー (JSON)"
    ARGS_SLEEP_INTERVAL_DESC_MSG = "リクエスト間のスリープ間隔 (秒)"
    ARGS_MAX_SLEEP_INTERVAL_DESC_MSG = "最大スリープ間隔 (秒)"
    ARGS_RETRIES_DESC_MSG = "再試行回数"
    ARGS_VIDEO_FORMAT_DESC_MSG = "ビデオコンテナ形式"
    ARGS_MERGE_OUTPUT_FORMAT_DESC_MSG = "マージ用の出力コンテナ形式"
    ARGS_SEND_AS_FILE_DESC_MSG = "すべてのメディアをメディアではなくドキュメントとして送信する"
    
    # Args command short descriptions
    ARGS_IMPERSONATE_SHORT_MSG = "偽装"
    ARGS_REFERER_SHORT_MSG = "リファラー"
    ARGS_GEO_BYPASS_SHORT_MSG = "地理的バイパス"
    ARGS_CHECK_CERTIFICATE_SHORT_MSG = "証明書の確認"
    ARGS_LIVE_FROM_START_SHORT_MSG = "ライブ開始"
    ARGS_NO_LIVE_FROM_START_SHORT_MSG = "ライブ開始なし"
    ARGS_USER_AGENT_SHORT_MSG = "ユーザーエージェント"
    ARGS_HLS_USE_MPEGTS_SHORT_MSG = "HLS MPEG-TS"
    ARGS_NO_PLAYLIST_SHORT_MSG = "プレイリストなし"
    ARGS_NO_PART_SHORT_MSG = "パートなし"
    ARGS_NO_CONTINUE_SHORT_MSG = "続行なし"
    ARGS_AUDIO_FORMAT_SHORT_MSG = "オーディオ形式"
    ARGS_EMBED_METADATA_SHORT_MSG = "メタを埋め込む"
    ARGS_EMBED_THUMBNAIL_SHORT_MSG = "サムネイルを埋め込む"
    ARGS_WRITE_THUMBNAIL_SHORT_MSG = "サムネイルを書き込む"
    ARGS_CONCURRENT_FRAGMENTS_SHORT_MSG = "同時"
    ARGS_FORCE_IPV4_SHORT_MSG = "IPv4を強制"
    ARGS_FORCE_IPV6_SHORT_MSG = "IPv6を強制"
    ARGS_XFF_SHORT_MSG = "XFFヘッダー"
    ARGS_HTTP_CHUNK_SIZE_SHORT_MSG = "チャンクサイズ"
    ARGS_SLEEP_SUBTITLES_SHORT_MSG = "スリープサブ"
    ARGS_LEGACY_SERVER_CONNECT_SHORT_MSG = "レガシー接続"
    ARGS_NO_CHECK_CERTIFICATES_SHORT_MSG = "証明書を確認しない"
    ARGS_USERNAME_SHORT_MSG = "ユーザー名"
    ARGS_PASSWORD_SHORT_MSG = "パスワード"
    ARGS_TWOFACTOR_SHORT_MSG = "2FA"
    ARGS_IGNORE_ERRORS_SHORT_MSG = "エラーを無視"
    ARGS_MIN_FILESIZE_SHORT_MSG = "最小サイズ"
    ARGS_MAX_FILESIZE_SHORT_MSG = "最大サイズ"
    ARGS_PLAYLIST_ITEMS_SHORT_MSG = "プレイリストアイテム"
    ARGS_DATE_SHORT_MSG = "日付"
    ARGS_DATEBEFORE_SHORT_MSG = "以前の日付"
    ARGS_DATEAFTER_SHORT_MSG = "以降の日付"
    ARGS_HTTP_HEADERS_SHORT_MSG = "HTTPヘッダー"
    ARGS_SLEEP_INTERVAL_SHORT_MSG = "スリープ間隔"
    ARGS_MAX_SLEEP_INTERVAL_SHORT_MSG = "最大スリープ"
    ARGS_VIDEO_FORMAT_SHORT_MSG = "ビデオ形式"
    ARGS_MERGE_OUTPUT_FORMAT_SHORT_MSG = "マージ形式"
    ARGS_SEND_AS_FILE_SHORT_MSG = "ファイルとして送信"
    
    # Additional cookies command messages
    COOKIES_FILE_TOO_LARGE_MSG = "❌ ファイルが大きすぎます。最大サイズは100 KBです。"
    COOKIES_INVALID_FORMAT_MSG = "❌ .txt形式のファイルのみが許可されています。"
    COOKIES_INVALID_COOKIE_MSG = "❌ cookie.txtのようには見えません(「# Netscape HTTP Cookie File」という行がありません)。"
    COOKIES_ERROR_READING_MSG = "❌ ファイルの読み取り中にエラーが発生しました: {error}"
    COOKIES_FILE_EXISTS_MSG = "✅ クッキーファイルが存在し、正しい形式です"
    COOKIES_FILE_TOO_LARGE_DOWNLOAD_MSG = "❌ {service}クッキーファイルが大きすぎます！ 最大100KB、取得{size}KB。"
    COOKIES_FILE_DOWNLOADED_MSG = "<b>✅ {service}クッキーファイルがダウンロードされ、フォルダにcookie.txtとして保存されました。</b>"
    COOKIES_SOURCE_UNAVAILABLE_MSG = "❌ {service}クッキーソースが利用できません(ステータス {status})。後でもう一度お試しください。"
    COOKIES_ERROR_DOWNLOADING_MSG = "❌ {service}クッキーファイルのダウンロード中にエラーが発生しました。後でもう一度お試しください。"
    COOKIES_USER_PROVIDED_MSG = "<b>✅ ユーザーが新しいクッキーファイルを提供しました。</b>"
    COOKIES_SUCCESSFULLY_UPDATED_MSG = "<b>✅ クッキーが正常に更新されました:</b>\n<code>{final_cookie}</code>"
    COOKIES_NOT_VALID_MSG = "<b>❌ 有効なクッキーではありません。</b>"
    COOKIES_YOUTUBE_SOURCES_NOT_CONFIGURED_MSG = "❌ YouTubeクッキーソースが設定されていません！"
    COOKIES_DOWNLOADING_YOUTUBE_MSG = "🔄 YouTubeクッキーをダウンロードして確認しています...\n\n試行{attempt} / {total}"
    
    # Additional admin command messages
    ADMIN_ACCESS_DENIED_AUTO_DELETE_MSG = "❌ アクセスが拒否されました。管理者のみ。"
    ADMIN_USER_LOGS_TOTAL_MSG = "合計: <b>{total}</b>\n<b>{user_id}</b> - ログ (最新10件):\n\n{format_str}"
    
    # Additional keyboard command messages
    KEYBOARD_ACTIVATED_MSG = "🎹 キーボードが有効になりました！"
    
    # Additional subtitles command messages
    SUBS_LANGUAGE_SET_MSG = "✅ 字幕言語をに設定しました: {flag} {name}"
    SUBS_LANGUAGE_AUTO_SET_MSG = "✅ 字幕言語をAUTO/TRANSを有効にしてに設定しました: {flag} {name}"
    SUBS_LANGUAGE_MENU_CLOSED_MSG = "字幕言語メニューを閉じました。"
    SUBS_DOWNLOADING_MSG = "💬 字幕をダウンロードしています..."
    
    # Additional admin command messages
    ADMIN_RELOADING_CACHE_MSG = "🔄 Firebaseキャッシュをメモリにリロードしています..."
    
    # Additional cookies command messages
    COOKIES_NO_BROWSERS_NO_URL_MSG = "❌ COOKIE_URLが設定されていません。/cookieを使用するか、cookie.txtをアップロードしてください。"
    COOKIES_DOWNLOADING_FROM_URL_MSG = "📥 リモートURLからクッキーをダウンロードしています..."
    COOKIE_FALLBACK_URL_NOT_TXT_MSG = "❌ フォールバックCOOKIE_URLは.txtファイルを指している必要があります。"
    COOKIE_FALLBACK_TOO_LARGE_MSG = "❌ フォールバッククッキーファイルが大きすぎます(>100KB)。"
    COOKIE_YT_FALLBACK_SAVED_MSG = "✅ YouTubeクッキーファイルがフォールバック経由でダウンロードされ、cookie.txtとして保存されました"
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "❌ フォールバッククッキーソースが利用できません(ステータス {status})。/cookieを試すか、cookie.txtをアップロードしてください。"
    COOKIE_FALLBACK_ERROR_MSG = "❌ フォールバッククッキーのダウンロード中にエラーが発生しました。/cookieを試すか、cookie.txtをアップロードしてください。"
    COOKIE_FALLBACK_UNEXPECTED_MSG = "❌ フォールバッククッキーのダウンロード中に予期しないエラーが発生しました。"
    COOKIES_BROWSER_NOT_INSTALLED_MSG = "⚠️ {browser}ブラウザがインストールされていません。"
    COOKIES_SAVED_USING_BROWSER_MSG = "✅ ブラウザを使用してクッキーを保存しました: {browser}"
    COOKIES_FAILED_TO_SAVE_MSG = "❌ クッキーの保存に失敗しました: {error}"
    COOKIES_YOUTUBE_WORKING_PROPERLY_MSG = "✅ YouTubeクッキーは正常に機能しています"
    COOKIES_YOUTUBE_EXPIRED_INVALID_MSG = "❌ YouTubeクッキーは期限切れまたは無効です\n\n新しいクッキーを取得するには/cookieを使用してください"
    
    # Additional format command messages
    FORMAT_MENU_ADDITIONAL_MSG = "• <code>/format &lt;format_string&gt;</code> - カスタムフォーマット\n• <code>/format 720</code> - 720p品質\n• <code>/format 4k</code> - 4K品質"
    
    # Callback answer messages
    FORMAT_HINT_SENT_MSG = "ヒントを送信しました。"
    FORMAT_MKV_TOGGLE_MSG = "MKVは現在{status}です"
    COOKIES_NO_REMOTE_URL_MSG = "❌ リモートURLが設定されていません"
    COOKIES_INVALID_FILE_FORMAT_MSG = "❌ 無効なファイル形式"
    COOKIES_FILE_TOO_LARGE_CALLBACK_MSG = "❌ ファイルが大きすぎます"
    COOKIES_DOWNLOADED_SUCCESSFULLY_MSG = "✅ クッキーが正常にダウンロードされました"
    COOKIES_SERVER_ERROR_MSG = "❌ サーバーエラー{status}"
    COOKIES_DOWNLOAD_FAILED_MSG = "❌ ダウンロードに失敗しました"
    COOKIES_UNEXPECTED_ERROR_MSG = "❌ 予期しないエラー"
    COOKIES_BROWSER_NOT_INSTALLED_CALLBACK_MSG = "⚠️ ブラウザがインストールされていません。"
    COOKIES_MENU_CLOSED_MSG = "メニューを閉じました。"
    COOKIES_HINT_CLOSED_MSG = "クッキーヒントを閉じました。"
    IMG_HELP_CLOSED_MSG = "ヘルプを閉じました。"
    SUBS_LANGUAGE_UPDATED_MSG = "字幕言語設定が更新されました。"
    SUBS_MENU_CLOSED_MSG = "字幕言語メニューを閉じました。"
    KEYBOARD_SET_TO_MSG = "キーボードを{setting}に設定"
    KEYBOARD_ERROR_PROCESSING_MSG = "設定の処理中にエラーが発生しました"
    MEDIAINFO_ENABLED_CALLBACK_MSG = "MediaInfoが有効になりました。"
    MEDIAINFO_DISABLED_CALLBACK_MSG = "MediaInfoが無効になりました。"
    NSFW_BLUR_DISABLED_CALLBACK_MSG = "NSFWブラーが無効になりました。"
    NSFW_BLUR_ENABLED_CALLBACK_MSG = "NSFWブラーが有効になりました。"
    SETTINGS_MENU_CLOSED_MSG = "メニューを閉じました。"
    SETTINGS_FLOOD_WAIT_ACTIVE_MSG = "フラッド待機がアクティブです。後でもう一度お試しください。"
    OTHER_HELP_CLOSED_MSG = "ヘルプを閉じました。"
    OTHER_LOGS_MESSAGE_CLOSED_MSG = "ログメッセージを閉じました。"
    
    # Additional split command messages
    SPLIT_MENU_CLOSED_MSG = "メニューを閉じました。"
    SPLIT_INVALID_SIZE_CALLBACK_MSG = "無効なサイズです。"
    
    # Additional error messages  
    MEDIAINFO_ERROR_SENDING_MSG = "❌ MediaInfoの送信中にエラーが発生しました: {error}"
    LINK_ERROR_OCCURRED_MSG = "❌ エラーが発生しました: {error}"
    
    # Additional document caption messages
    MEDIAINFO_DOCUMENT_CAPTION_MSG = "<blockquote>📊 MediaInfo</blockquote>"
    ADMIN_USER_LOGS_CAPTION_MSG = "{user_id} - すべてのログ"
    ADMIN_BOT_DATA_CAPTION_MSG = "{bot_name} - すべての{path}"
    
    # Additional cookies command messages (missing ones)
    DOWNLOAD_FROM_URL_BUTTON_MSG = "📥 リモートURLからダウンロード"
    BROWSER_OPEN_BUTTON_MSG = "🌐 ブラウザを開く"
    SELECT_BROWSER_MSG = "クッキーをダウンロードするブラウザを選択してください:"
    SELECT_BROWSER_NO_BROWSERS_MSG = "このシステムにブラウザが見つかりません。リモートURLからクッキーをダウンロードするか、ブラウザのステータスを監視できます:"
    BROWSER_MONITOR_HINT_MSG = "🌐 <b>ブラウザを開く</b> - ミニアプリでブラウザのステータスを監視します"
    COOKIES_FAILED_RUN_CHECK_MSG = "❌ /check_cookieの実行に失敗しました"
    COOKIES_FLOOD_LIMIT_MSG = "⏳ フラッド制限。後でもう一度お試しください。"
    COOKIES_FAILED_OPEN_BROWSER_MSG = "❌ ブラウザクッキーメニューを開けませんでした"
    COOKIES_SAVE_AS_HINT_CLOSED_MSG = "クッキーとして保存ヒントを閉じました。"
    
    # Link command messages
    LINK_USAGE_MSG = "🔗 <b>使用法:</b>\n<code>/link [quality] URL</code>\n\n<b>例:</b>\n<blockquote>• /link https://youtube.com/watch?v=... - 最高品質\n• /link 720 https://youtube.com/watch?v=... - 720p以下\n• /link 720p https://youtube.com/watch?v=... - 上記と同じ\n• /link 4k https://youtube.com/watch?v=... - 4K以下\n• /link 8k https://youtube.com/watch?v=... - 8K以下</blockquote>\n\n<b>品質:</b> 1から10000まで (例: 144, 240, 720, 1080)"
    
    # Additional format command messages
    FORMAT_8K_QUALITY_MSG = "• <code>/format 8k</code> - 8K品質"
    
    # Additional link command messages
    LINK_DIRECT_LINK_OBTAINED_MSG = "🔗 <b>ダイレクトリンクを取得しました</b>\n\n"
    LINK_FORMAT_INFO_MSG = "🎛 <b>フォーマット:</b> <code>{format_spec}</code>\n\n"
    LINK_AUDIO_STREAM_MSG = "🎵 <b>オーディオストリーム:</b>\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
    LINK_FAILED_GET_STREAMS_MSG = "❌ ストリームリンクの取得に失敗しました"
    LINK_ERROR_GETTING_MSG = "❌ <b>リンクの取得中にエラーが発生しました:</b>\n{error_msg}"
    
    # Additional cookies command messages (more)
    COOKIES_INVALID_YOUTUBE_INDEX_MSG = "❌ 無効なYouTubeクッキーインデックス: {selected_index}。利用可能な範囲は1-{total_urls}です"
    COOKIES_DOWNLOADING_CHECKING_MSG = "🔄 YouTubeクッキーをダウンロードして確認しています...\n\n試行{attempt} / {total}"
    COOKIES_DOWNLOADING_TESTING_MSG = "🔄 YouTubeクッキーをダウンロードして確認しています...\n\n試行{attempt} / {total}\n🔍 クッキーをテストしています..."
    COOKIES_SUCCESS_VALIDATED_MSG = "✅ YouTubeクッキーが正常にダウンロードされ、検証されました！\n\n使用されたソース{source} / {total}"
    COOKIES_ALL_EXPIRED_MSG = "❌ すべてのYouTubeクッキーは期限切れまたは利用不能です！\n\nボット管理者に連絡して交換してもらってください。"
    COOKIES_YOUTUBE_RETRY_LIMIT_EXCEEDED_MSG = "⚠️ YouTubeクッキーの再試行制限を超えました！\n\n🔢 最大: 1時間あたり{limit}回\n⏰ 後でもう一度お試しください"
    
    # Additional other command messages
    OTHER_TAG_ERROR_MSG = "❌ タグ#{wrong}には禁止文字が含まれています。文字、数字、_のみが許可されています。\n使用してください: {example}"
    
    # Additional subtitles command messages
    SUBS_INVALID_ARGUMENT_MSG = "❌ **無効な引数です！**\n\n"
    SUBS_LANGUAGE_SET_STATUS_MSG = "✅ 字幕言語がに設定されました: {flag} {name}"
    
    # Additional subtitles command messages (more)
    SUBS_EXAMPLE_AUTO_MSG = "例: `/subs ja auto`"
    
    # Additional subtitles command messages (more more)
    SUBS_SELECTED_LANGUAGE_MSG = "{flag} 選択した言語: {name}{auto_text}"
    SUBS_ALWAYS_ASK_TOGGLE_MSG = "✅ 常時確認モード{status}"
    
    # Additional subtitles menu messages
    SUBS_DISABLED_STATUS_MSG = "🚫 字幕は無効です"
    SUBS_SETTINGS_MENU_MSG = "<b>💬 字幕設定</b>\n\n{status_text}\n\n字幕言語を選択してください:\n\n"
    SUBS_SETTINGS_ADDITIONAL_MSG = "• <code>/subs off</code> - 字幕を無効にする\n"
    SUBS_AUTO_MENU_MSG = "<b>💬 字幕設定</b>\n\n{status_text}\n\n字幕言語を選択してください:"
    
    # Additional link command messages (more)
    LINK_TITLE_MSG = "📹 <b>タイトル:</b> {title}\n"
    LINK_DURATION_MSG = "⏱ <b>期間:</b> {duration} 秒\n"
    LINK_VIDEO_STREAM_MSG = "🎬 <b>ビデオストリーム:</b>\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
    
    # Additional subtitles limitation messages
    SUBS_LIMITATIONS_MSG = "- 720p 最大品質\n- 1.5時間 最大期間\n- 500MB 最大ビデオサイズ</blockquote>\n\n"
    
    # Additional subtitles warning and command messages
    SUBS_WARNING_MSG = "<blockquote>❗️警告: CPUへの影響が大きいため、この機能は非常に遅く(ほぼリアルタイム)、以下に制限されています:\n"
    SUBS_QUICK_COMMANDS_MSG = "<b>クイックコマンド:</b>\n"
    
    # Additional subtitles command description messages
    SUBS_DISABLE_COMMAND_MSG = "• `/subs off` - 字幕を無効にする\n"
    SUBS_ENABLE_ASK_MODE_MSG = "• `/subs on` - 常時確認モードを有効にする\n"
    SUBS_SET_LANGUAGE_MSG = "• `/subs ja` - 言語を設定\n"
    SUBS_SET_LANGUAGE_AUTO_MSG = "• `/subs ja auto` - AUTO/TRANSで言語を設定\n\n"
    SUBS_SET_LANGUAGE_CODE_MSG = "• <code>/subs on</code> - 常時確認モードを有効にする\n"
    SUBS_AUTO_SUBS_TEXT = " (自動字幕)"
    SUBS_AUTO_MODE_TOGGLE_MSG = "✅ 自動字幕モード{status}"
    
    # Subtitles log messages
    SUBS_DISABLED_LOG_MSG = "コマンド経由で字幕を無効にしました: {arg}"
    SUBS_ALWAYS_ASK_ENABLED_LOG_MSG = "コマンド経由で常時確認を有効にしました: {arg}"
    SUBS_LANGUAGE_SET_LOG_MSG = "コマンド経由で字幕言語を設定しました: {arg}"
    SUBS_LANGUAGE_AUTO_SET_LOG_MSG = "コマンド経由で字幕言語+自動モードを設定しました: {arg} auto"
    SUBS_MENU_OPENED_LOG_MSG = "ユーザーが/subsメニューを開きました。"
    SUBS_LANGUAGE_SET_CALLBACK_LOG_MSG = "ユーザーが字幕言語をに設定しました: {lang_code}"
    SUBS_AUTO_MODE_TOGGLED_LOG_MSG = "ユーザーがAUTO/TRANSモードをに切り替えました: {new_auto}"
    SUBS_ALWAYS_ASK_TOGGLED_LOG_MSG = "ユーザーが常時確認モードをに切り替えました: {new_always_ask}"
    
    # Cookies log messages
    COOKIES_BROWSER_REQUESTED_LOG_MSG = "ユーザーがブラウザからクッキーをリクエストしました。"
    COOKIES_BROWSER_SELECTION_SENT_LOG_MSG = "インストールされているブラウザのみを含むブラウザ選択キーボードが送信されました。"
    COOKIES_BROWSER_SELECTION_CLOSED_LOG_MSG = "ブラウザの選択を閉じました。"
    COOKIES_FALLBACK_SUCCESS_LOG_MSG = "フォールバックCOOKIE_URLが正常に使用されました (ソースは非表示)"
    COOKIES_FALLBACK_FAILED_LOG_MSG = "フォールバックCOOKIE_URLが失敗しました: ステータス={status} (非表示)"
    COOKIES_FALLBACK_UNEXPECTED_ERROR_LOG_MSG = "フォールバックCOOKIE_URL予期しないエラー: {error_type}: {error}"
    COOKIES_BROWSER_NOT_INSTALLED_LOG_MSG = "ブラウザ{browser}がインストールされていません。"
    COOKIES_SAVED_BROWSER_LOG_MSG = "ブラウザを使用してクッキーを保存しました: {browser}"
    COOKIES_FILE_SAVED_USER_LOG_MSG = "ユーザー{user_id}のクッキーファイルが保存されました。"
    COOKIES_FILE_WORKING_LOG_MSG = "クッキーファイルが存在し、正しい形式であり、YouTubeクッキーが機能しています。"
    COOKIES_FILE_EXPIRED_LOG_MSG = "クッキーファイルが存在し、正しい形式ですが、YouTubeクッキーは期限切れです。"
    COOKIES_FILE_CORRECT_FORMAT_LOG_MSG = "クッキーファイルが存在し、正しい形式です。"
    COOKIES_FILE_INCORRECT_FORMAT_LOG_MSG = "クッキーファイルが存在しますが、形式が正しくありません。"
    COOKIES_FILE_NOT_FOUND_LOG_MSG = "クッキーファイルが見つかりません。"
    COOKIES_SERVICE_URL_EMPTY_LOG_MSG = "{service}クッキーURLがユーザー{user_id}に対して空です。"
    COOKIES_SERVICE_URL_NOT_TXT_LOG_MSG = "{service}クッキーURLは.txtではありません (非表示)"
    COOKIES_SERVICE_FILE_TOO_LARGE_LOG_MSG = "{service}クッキーファイルが大きすぎます: {size}バイト (ソースは非表示)"
    COOKIES_SERVICE_FILE_DOWNLOADED_LOG_MSG = "ユーザー{user_id}の{service}クッキーファイルがダウンロードされました (ソースは非表示)。"
    
    # Admin log messages
    ADMIN_SCRIPT_NOT_FOUND_LOG_MSG = "スクリプトが見つかりません: {script_path}"
    ADMIN_FAILED_SEND_STATUS_LOG_MSG = "初期ステータスメッセージの送信に失敗しました"
    ADMIN_ERROR_RUNNING_SCRIPT_LOG_MSG = "{script_path}の実行中にエラーが発生しました: {stdout}\n{stderr}"
    ADMIN_CACHE_RELOADED_AUTO_LOG_MSG = "自動タスクによってFirebaseキャッシュがリロードされました。"
    ADMIN_CACHE_RELOADED_ADMIN_LOG_MSG = "管理者によってFirebaseキャッシュがリロードされました。"
    ADMIN_ERROR_RELOADING_CACHE_LOG_MSG = "Firebaseキャッシュのリロード中にエラーが発生しました: {error}"
    ADMIN_BROADCAST_INITIATED_LOG_MSG = "ブロードキャストが開始されました。テキスト:\n{broadcast_text}"
    ADMIN_BROADCAST_SENT_LOG_MSG = "ブロードキャストメッセージがすべてのユーザーに送信されました。"
    ADMIN_BROADCAST_FAILED_LOG_MSG = "ブロードキャストメッセージの送信に失敗しました: {error}"
    ADMIN_CACHE_CLEARED_LOG_MSG = "管理者{user_id}がURLのキャッシュをクリアしました: {url}"
    ADMIN_PORN_UPDATE_STARTED_LOG_MSG = "管理者{user_id}がポルノリスト更新スクリプトを開始しました: {script_path}"
    ADMIN_PORN_UPDATE_COMPLETED_LOG_MSG = "ポルノリスト更新スクリプトが管理者{user_id}によって正常に完了しました"
    ADMIN_PORN_UPDATE_FAILED_LOG_MSG = "管理者{user_id}によるポルノリスト更新スクリプトが失敗しました: {error}"
    ADMIN_SCRIPT_NOT_FOUND_LOG_MSG = "管理者{user_id}が存在しないスクリプトを実行しようとしました: {script_path}"
    ADMIN_PORN_UPDATE_ERROR_LOG_MSG = "管理者{user_id}によるポルノ更新スクリプトの実行中にエラーが発生しました: {error}"
    ADMIN_PORN_CACHE_RELOAD_STARTED_LOG_MSG = "管理者{user_id}がポルノキャッシュのリロードを開始しました"
    ADMIN_PORN_CACHE_RELOAD_ERROR_LOG_MSG = "管理者{user_id}によるポルノキャッシュのリロード中にエラーが発生しました: {error}"
    ADMIN_PORN_CHECK_LOG_MSG = "管理者{user_id}がNSFWのURLを確認しました: {url} - 結果: {status}"
    
    # Format log messages
    FORMAT_CHANGE_REQUESTED_LOG_MSG = "ユーザーがフォーマットの変更をリクエストしました。"
    FORMAT_ALWAYS_ASK_SET_LOG_MSG = "フォーマットをALWAYS_ASKに設定します。"
    FORMAT_UPDATED_BEST_LOG_MSG = "フォーマットを最高に更新しました: {format}"
    FORMAT_UPDATED_ID_LOG_MSG = "フォーマットをID {format_id}に更新しました: {format}"
    FORMAT_UPDATED_ID_AUDIO_LOG_MSG = "フォーマットをID {format_id} (オーディオのみ)に更新しました: {format}"
    FORMAT_UPDATED_QUALITY_LOG_MSG = "フォーマットを品質{quality}に更新しました: {format}"
    FORMAT_UPDATED_CUSTOM_LOG_MSG = "フォーマットをに更新しました: {format}"
    FORMAT_MENU_SENT_LOG_MSG = "フォーマットメニューを送信しました。"
    FORMAT_SELECTION_CLOSED_LOG_MSG = "フォーマットの選択を閉じました。"
    FORMAT_CUSTOM_HINT_SENT_LOG_MSG = "カスタムフォーマットのヒントを送信しました。"
    FORMAT_RESOLUTION_MENU_SENT_LOG_MSG = "フォーマット解像度メニューを送信しました。"
    FORMAT_RETURNED_MAIN_MENU_LOG_MSG = "メインフォーマットメニューに戻りました。"
    FORMAT_UPDATED_CALLBACK_LOG_MSG = "フォーマットをに更新しました: {format}"
    FORMAT_ALWAYS_ASK_SET_CALLBACK_LOG_MSG = "フォーマットをALWAYS_ASKに設定します。"
    FORMAT_CODEC_SET_LOG_MSG = "コーデック設定をに設定しました {codec}"
    FORMAT_CUSTOM_MENU_CLOSED_MSG = "カスタムフォーマットメニューを閉じました"
    
    # Link log messages
    LINK_EXTRACTED_LOG_MSG = "ユーザー{user_id}のダイレクトリンクを{url}から抽出しました"
    LINK_EXTRACTION_FAILED_LOG_MSG = "ユーザー{user_id}のダイレクトリンクを{url}から抽出できませんでした: {error}"
    LINK_COMMAND_ERROR_LOG_MSG = "ユーザー{user_id}のリンクコマンドでエラーが発生しました: {error}"
    
    # Keyboard log messages
    KEYBOARD_SET_LOG_MSG = "ユーザー{user_id}がキーボードをに設定しました {setting}"
    KEYBOARD_SET_CALLBACK_LOG_MSG = "ユーザー{user_id}がキーボードをに設定しました {setting}"
    
    # MediaInfo log messages
    MEDIAINFO_SET_COMMAND_LOG_MSG = "コマンド経由でMediaInfoを設定しました: {arg}"
    MEDIAINFO_MENU_OPENED_LOG_MSG = "ユーザーが/mediainfoメニューを開きました。"
    MEDIAINFO_MENU_CLOSED_LOG_MSG = "MediaInfo: 閉じました。"
    MEDIAINFO_ENABLED_LOG_MSG = "MediaInfoが有効になりました。"
    MEDIAINFO_DISABLED_LOG_MSG = "MediaInfoが無効になりました。"
    
    # Split log messages
    SPLIT_SIZE_SET_ARGUMENT_LOG_MSG = "分割サイズを引数経由で{size}バイトに設定しました。"
    SPLIT_MENU_OPENED_LOG_MSG = "ユーザーが/splitメニューを開きました。"
    SPLIT_SELECTION_CLOSED_LOG_MSG = "分割の選択を閉じました。"
    SPLIT_SIZE_SET_CALLBACK_LOG_MSG = "分割サイズを{size}バイトに設定しました。"
    
    # Proxy log messages
    PROXY_SET_COMMAND_LOG_MSG = "コマンド経由でプロキシを設定しました: {arg}"
    PROXY_MENU_OPENED_LOG_MSG = "ユーザーが/proxyメニューを開きました。"
    PROXY_MENU_CLOSED_LOG_MSG = "プロキシ: 閉じました。"
    PROXY_ENABLED_LOG_MSG = "プロキシが有効になりました。"
    PROXY_DISABLED_LOG_MSG = "プロキシが無効になりました。"
    
    # Other handlers log messages
    HELP_MESSAGE_CLOSED_LOG_MSG = "ヘルプメッセージを閉じました。"
    AUDIO_HELP_SHOWN_LOG_MSG = "/audioヘルプを表示しました"
    PLAYLIST_HELP_REQUESTED_LOG_MSG = "ユーザーがプレイリストヘルプをリクエストしました。"
    PLAYLIST_HELP_CLOSED_LOG_MSG = "プレイリストヘルプを閉じました。"
    AUDIO_HINT_CLOSED_LOG_MSG = "オーディオヒントを閉じました。"
    
    # Down and Up log messages
    DIRECT_LINK_MENU_CREATED_LOG_MSG = "ユーザー{user_id}の{url}からLINKボタン経由でダイレクトリンクメニューが作成されました"
    DIRECT_LINK_EXTRACTION_FAILED_LOG_MSG = "ユーザー{user_id}の{url}からLINKボタン経由でダイレクトリンクを抽出できませんでした: {error}"
    LIST_COMMAND_EXECUTED_LOG_MSG = "ユーザー{user_id}のLISTコマンドが実行されました, url: {url}"
    QUICK_EMBED_LOG_MSG = "クイック埋め込み: {embed_url}"
    ALWAYS_ASK_MENU_SENT_LOG_MSG = "常時確認メニューが{url}に送信されました"
    CACHED_QUALITIES_MENU_CREATED_LOG_MSG = "エラー後、ユーザー{user_id}のキャッシュされた品質メニューが作成されました: {error}"
    ALWAYS_ASK_MENU_ERROR_LOG_MSG = "{url}の常時確認メニューエラー: {error}"
    ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG = "フォーマットは/args設定で固定されています"
    ALWAYS_ASK_AUDIO_TYPE_MSG = "オーディオ"
    ALWAYS_ASK_VIDEO_TYPE_MSG = "ビデオ"
    ALWAYS_ASK_VIDEO_TITLE_MSG = "ビデオ"
    ALWAYS_ASK_NEXT_BUTTON_MSG = "次へ ▶️"
    ALWAYS_ASK_PREV_BUTTON_MSG = "◀️ 前へ"
    SUBTITLES_NEXT_BUTTON_MSG = "次へ ➡️"
    PORN_ALL_TEXT_FIELDS_EMPTY_MSG = "ℹ️ すべてのテキストフィールドが空です"
    SENDER_VIDEO_DURATION_MSG = "ビデオ期間:"
    SENDER_UPLOADING_FILE_MSG = "📤 ファイルをアップロードしています..."
    SENDER_UPLOADING_VIDEO_MSG = "📤 ビデオをアップロードしています..."
    DOWN_UP_VIDEO_DURATION_MSG = "🎞 ビデオ期間:"
    DOWN_UP_ONE_FILE_UPLOADED_MSG = "1つのファイルがアップロードされました。"
    DOWN_UP_VIDEO_INFO_MSG = "📋 ビデオ情報"
    DOWN_UP_NUMBER_MSG = "番号"
    DOWN_UP_TITLE_MSG = "タイトル"
    DOWN_UP_ID_MSG = "ID"
    DOWN_UP_DOWNLOADED_VIDEO_MSG = "☑️ ビデオをダウンロードしました。"
    DOWN_UP_PROCESSING_UPLOAD_MSG = "📤 アップロードのために処理しています..."
    DOWN_UP_SPLITTED_PART_UPLOADED_MSG = "📤 分割されたパート{part}ファイルがアップロードされました"
    DOWN_UP_UPLOAD_COMPLETE_MSG = "✅ アップロード完了"
    DOWN_UP_FILES_UPLOADED_MSG = "ファイルがアップロードされました"
    
    # Always Ask Menu Button Messages
    ALWAYS_ASK_VLC_ANDROID_BUTTON_MSG = "🎬 VLC (Android)"
    ALWAYS_ASK_CLOSE_BUTTON_MSG = "🔚 閉じる"
    ALWAYS_ASK_CODEC_BUTTON_MSG = "📼コーデック"
    ALWAYS_ASK_DUBS_BUTTON_MSG = "🗣 ダブ"
    ALWAYS_ASK_SUBS_BUTTON_MSG = "💬 字幕"
    ALWAYS_ASK_BROWSER_BUTTON_MSG = "🌐 ブラウザ"
    ALWAYS_ASK_VLC_IOS_BUTTON_MSG = "🎬 VLC (iOS)"
    
    # Always Ask Menu Callback Messages
    ALWAYS_ASK_GETTING_DIRECT_LINK_MSG = "🔗 ダイレクトリンクを取得しています..."
    ALWAYS_ASK_GETTING_FORMATS_MSG = "📃 利用可能なフォーマットを取得しています..."
    ALWAYS_ASK_STARTING_GALLERY_DL_MSG = "🖼 gallery-dlを開始しています…"
    
    # Always Ask Menu F-String Messages
    ALWAYS_ASK_DURATION_MSG = "⏱ <b>期間:</b>"
    ALWAYS_ASK_FORMAT_MSG = "🎛 <b>フォーマット:</b>"
    ALWAYS_ASK_BROWSER_MSG = "🌐 <b>ブラウザ:</b> Webブラウザで開く"
    ALWAYS_ASK_AVAILABLE_FORMATS_FOR_MSG = "利用可能なフォーマット"
    ALWAYS_ASK_HOW_TO_USE_FORMAT_IDS_MSG = "💡 フォーマットIDの使用方法:"
    ALWAYS_ASK_AFTER_GETTING_LIST_MSG = "リストを取得した後、特定のフォーマットIDを使用します:"
    ALWAYS_ASK_FORMAT_ID_401_MSG = "• /format id 401 - フォーマット401をダウンロード"
    ALWAYS_ASK_FORMAT_ID401_MSG = "• /format id401 - 上記と同じ"
    ALWAYS_ASK_FORMAT_ID_140_AUDIO_MSG = "• /format id 140 audio - フォーマット140をMP3オーディオとしてダウンロード"
    ALWAYS_ASK_AUDIO_ONLY_FORMATS_DETECTED_MSG = "🎵 オーディオのみのフォーマットが検出されました"
    ALWAYS_ASK_THESE_FORMATS_MP3_MSG = "これらのフォーマットはMP3オーディオファイルとしてダウンロードされます。"
    ALWAYS_ASK_HOW_TO_SET_FORMAT_MSG = "💡 <b>フォーマットの設定方法:</b>"
    ALWAYS_ASK_FORMAT_ID_134_MSG = "• <code>/format id 134</code> - 特定のフォーマットIDをダウンロード"
    ALWAYS_ASK_FORMAT_720P_MSG = "• <code>/format 720p</code> - 品質でダウンロード"
    ALWAYS_ASK_FORMAT_BEST_MSG = "• <code>/format best</code> - 最高品質をダウンロード"
    ALWAYS_ASK_FORMAT_ASK_MSG = "• <code>/format ask</code> - 常に品質を尋ねる"
    ALWAYS_ASK_AUDIO_ONLY_FORMATS_MSG = "🎵 <b>オーディオのみのフォーマット:</b>"
    ALWAYS_ASK_FORMAT_ID_140_AUDIO_CAPTION_MSG = "• <code>/format id 140 audio</code> - フォーマット140をMP3オーディオとしてダウンロード"
    ALWAYS_ASK_THESE_WILL_BE_MP3_MSG = "これらはMP3オーディオファイルとしてダウンロードされます。"
    ALWAYS_ASK_USE_FORMAT_ID_MSG = "📋 上記のリストからフォーマットIDを使用してください"
    ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_MSG = "❌ エラー: 元のメッセージが見つかりません。"
    ALWAYS_ASK_FORMATS_PAGE_MSG = "フォーマットページ"
    ALWAYS_ASK_ERROR_SHOWING_FORMATS_MENU_MSG = "❌ フォーマットメニューの表示中にエラーが発生しました"
    ALWAYS_ASK_ERROR_GETTING_FORMATS_MSG = "❌ フォーマットの取得中にエラーが発生しました"
    ALWAYS_ASK_ERROR_GETTING_AVAILABLE_FORMATS_MSG = "❌ 利用可能なフォーマットの取得中にエラーが発生しました。"
    ALWAYS_ASK_PLEASE_TRY_AGAIN_LATER_MSG = "後でもう一度お試しください。"
    ALWAYS_ASK_YTDLP_CANNOT_PROCESS_MSG = "🔄 <b>yt-dlpはこのコンテンツを処理できません"
    ALWAYS_ASK_SYSTEM_RECOMMENDS_GALLERY_DL_MSG = "システムは代わりにgallery-dlを使用することをお勧めします。"
    ALWAYS_ASK_OPTIONS_MSG = "**オプション:**"
    ALWAYS_ASK_FOR_IMAGE_GALLERIES_MSG = "• 画像ギャラリーの場合: <code>/img 1-10</code>"
    ALWAYS_ASK_FOR_SINGLE_IMAGES_MSG = "• 単一画像の場合: <code>/img</code>"
    ALWAYS_ASK_GALLERY_DL_WORKS_BETTER_MSG = "gallery-dlは、Instagram、Twitter、その他のソーシャルメディアコンテンツでよりうまく機能することがよくあります。"
    ALWAYS_ASK_TRY_GALLERY_DL_BUTTON_MSG = "🖼 gallery-dlを試す"
    ALWAYS_ASK_FORMAT_FIXED_VIA_ARGS_MSG = "🔒 /args経由でフォーマットが固定されました"
    ALWAYS_ASK_SUBTITLES_MSG = "🔤 字幕"
    ALWAYS_ASK_DUBBED_AUDIO_MSG = "🎧 ダビングされたオーディオ"
    ALWAYS_ASK_SUBTITLES_ARE_AVAILABLE_MSG = "💬 — 字幕が利用可能です"
    ALWAYS_ASK_CHOOSE_SUBTITLE_LANGUAGE_MSG = "💬 — 字幕言語を選択してください"
    ALWAYS_ASK_SUBS_NOT_FOUND_MSG = "⚠️ 字幕が見つからず、埋め込みません"
    ALWAYS_ASK_INSTANT_REPOST_MSG = "🚀 — キャッシュからの即時再投稿"
    ALWAYS_ASK_CHOOSE_AUDIO_LANGUAGE_MSG = "🗣 — オーディオ言語を選択してください"
    ALWAYS_ASK_NSFW_IS_PAID_MSG = "⭐️ — 🔞NSFWは有料です (⭐️$0.02)"
    ALWAYS_ASK_CHOOSE_DOWNLOAD_QUALITY_MSG = "📹 — ダウンロード品質を選択してください"
    ALWAYS_ASK_DOWNLOAD_IMAGE_MSG = "🖼 — 画像をダウンロード (gallery-dl)"
    ALWAYS_ASK_WATCH_VIDEO_MSG = "👁 — poketubeでビデオを視聴"
    ALWAYS_ASK_GET_DIRECT_LINK_MSG = "🔗 — ビデオへのダイレクトリンクを取得"
    ALWAYS_ASK_SHOW_AVAILABLE_FORMATS_MSG = "📃 — 利用可能なフォーマットリストを表示"
    ALWAYS_ASK_CHANGE_VIDEO_EXT_MSG = "📼 — ビデオの拡張子/コーデックを変更"
    ALWAYS_ASK_EMBED_BUTTON_MSG = "🚀埋め込み"
    ALWAYS_ASK_EXTRACT_AUDIO_MSG = "🎧 — オーディオのみを抽出"
    ALWAYS_ASK_NSFW_PAID_MSG = "⭐️ — 🔞NSFWは有料です (⭐️$0.02)"
    ALWAYS_ASK_INSTANT_REPOST_MSG = "🚀 — キャッシュからの即時再投稿"
    ALWAYS_ASK_WATCH_VIDEO_MSG = "👁 — poketubeでビデオを視聴"
    ALWAYS_ASK_CHOOSE_AUDIO_LANGUAGE_MSG = "🗣 — オーディオ言語を選択してください"
    ALWAYS_ASK_BEST_BUTTON_MSG = "最高"
    ALWAYS_ASK_OTHER_LABEL_MSG = "🎛その他"
    ALWAYS_ASK_SUB_ONLY_BUTTON_MSG = "📝字幕のみ"
    ALWAYS_ASK_SMART_GROUPING_MSG = "スマートグルーピング"
    ALWAYS_ASK_ADDED_ACTION_BUTTON_ROW_3_MSG = "アクションボタン行を追加しました (3)"
    ALWAYS_ASK_ADDED_ACTION_BUTTON_ROWS_2_2_MSG = "アクションボタン行を追加しました (2+2)"
    ALWAYS_ASK_ADDED_BOTTOM_BUTTONS_TO_EXISTING_ROW_MSG = "既存の行に下部ボタンを追加しました"
    ALWAYS_ASK_CREATED_NEW_BOTTOM_ROW_MSG = "新しい下部行を作成しました"
    ALWAYS_ASK_NO_VIDEOS_FOUND_IN_PLAYLIST_MSG = "プレイリストにビデオが見つかりません"
    ALWAYS_ASK_UNSUPPORTED_URL_MSG = "サポートされていないURL"
    ALWAYS_ASK_NO_VIDEO_COULD_BE_FOUND_MSG = "ビデオが見つかりませんでした"
    ALWAYS_ASK_NO_VIDEO_FOUND_MSG = "ビデオが見つかりません"
    ALWAYS_ASK_NO_MEDIA_FOUND_MSG = "メディアが見つかりません"
    ALWAYS_ASK_THIS_TWEET_DOES_NOT_CONTAIN_MSG = "このツイートには含まれていません"
    ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_MSG = "❌ <b>ビデオ情報の取得中にエラーが発生しました:</b>"
    ALWAYS_ASK_ERROR_RETRIEVING_VIDEO_INFO_SHORT_MSG = "ビデオ情報の取得中にエラーが発生しました"
    ALWAYS_ASK_TRY_CLEAN_COMMAND_MSG = "<code>/clean</code>コマンドを試してから、もう一度お試しください。エラーが続く場合は、YouTubeで認証が必要です。<code>/cookie</code>または<code>/cookies_from_browser</code>経由でcookies.txtを更新してから、もう一度お試しください。"
    ALWAYS_ASK_MENU_CLOSED_MSG = "メニューを閉じました。"
    ALWAYS_ASK_MANUAL_QUALITY_SELECTION_MSG = "🎛 手動品質選択"
    ALWAYS_ASK_CHOOSE_QUALITY_MANUALLY_MSG = "自動検出に失敗したため、品質を手動で選択してください:"
    ALWAYS_ASK_ALL_AVAILABLE_FORMATS_MSG = "🎛 利用可能なすべてのフォーマット"
    ALWAYS_ASK_AVAILABLE_QUALITIES_FROM_CACHE_MSG = "📹 利用可能な品質 (キャッシュから)"
    ALWAYS_ASK_USING_CACHED_QUALITIES_MSG = "⚠️ キャッシュされた品質を使用しています - 新しいフォーマットは利用できない場合があります"
    ALWAYS_ASK_DOWNLOADING_FORMAT_MSG = "📥 フォーマットをダウンロードしています"
    ALWAYS_ASK_DOWNLOADING_QUALITY_MSG = "📥 ダウンロード中"
    ALWAYS_ASK_DOWNLOADING_HLS_MSG = "📥 進行状況の追跡付きでダウンロードしています..."
    ALWAYS_ASK_DOWNLOADING_FORMAT_USING_MSG = "📥 フォーマットを使用してダウンロードしています:"
    ALWAYS_ASK_DOWNLOADING_AUDIO_FORMAT_USING_MSG = "📥 フォーマットを使用してオーディオをダウンロードしています:"
    ALWAYS_ASK_DOWNLOADING_BEST_QUALITY_MSG = "📥 最高品質をダウンロードしています..."
    ALWAYS_ASK_DOWNLOADING_DATABASE_MSG = "📥 データベースダンプをダウンロードしています..."
    ALWAYS_ASK_DOWNLOADING_IMAGES_MSG = "📥 ダウンロード中"
    ALWAYS_ASK_FORMATS_PAGE_FROM_CACHE_MSG = "フォーマットページ"
    ALWAYS_ASK_FROM_CACHE_MSG = "(キャッシュから)"
    ALWAYS_ASK_ERROR_ORIGINAL_MESSAGE_NOT_FOUND_DETAILED_MSG = "❌ エラー: 元のメッセージが見つかりません。削除された可能性があります。もう一度リンクを送信してください。"
    ALWAYS_ASK_ERROR_ORIGINAL_URL_NOT_FOUND_MSG = "❌ エラー: 元のURLが見つかりません。もう一度リンクを送信してください。"
    ALWAYS_ASK_DIRECT_LINK_OBTAINED_MSG = "🔗 <b>ダイレクトリンクを取得しました</b>"
    ALWAYS_ASK_TITLE_MSG = "📹 <b>タイトル:</b>"
    ALWAYS_ASK_DURATION_SEC_MSG = "⏱ <b>期間:</b>"
    ALWAYS_ASK_FORMAT_CODE_MSG = "🎛 <b>フォーマット:</b>"
    ALWAYS_ASK_VIDEO_STREAM_MSG = "🎬 <b>ビデオストリーム:</b>"
    ALWAYS_ASK_AUDIO_STREAM_MSG = "🎵 <b>オーディオストリーム:</b>"
    ALWAYS_ASK_FAILED_TO_GET_STREAM_LINKS_MSG = "❌ ストリームリンクの取得に失敗しました"
    DIRECT_LINK_EXTRACTED_ALWAYS_ASK_LOG_MSG = "ユーザー{user_id}の{url}から常時確認メニュー経由でダイレクトリンクを抽出しました"
    DIRECT_LINK_FAILED_ALWAYS_ASK_LOG_MSG = "ユーザー{user_id}の{url}から常時確認メニュー経由でダイレクトリンクを抽出できませんでした: {error}"
    DIRECT_LINK_EXTRACTED_DOWN_UP_LOG_MSG = "ユーザー{user_id}の{url}からdown_and_up_with_format経由でダイレクトリンクを抽出しました"
    DIRECT_LINK_FAILED_DOWN_UP_LOG_MSG = "ユーザー{user_id}の{url}からdown_and_up_with_format経由でダイレクトリンクを抽出できませんでした: {error}"
    DIRECT_LINK_EXTRACTED_DOWN_AUDIO_LOG_MSG = "ユーザー{user_id}の{url}からdown_and_audio経由でダイレクトリンクを抽出しました"
    DIRECT_LINK_FAILED_DOWN_AUDIO_LOG_MSG = "ユーザー{user_id}の{url}からdown_and_audio経由でダイレクトリンクを抽出できませんでした: {error}"
    
    # Audio processing messages
    AUDIO_SENT_FROM_CACHE_MSG = "✅ キャッシュからオーディオを送信しました。"
    AUDIO_PROCESSING_MSG = "🎙️ オーディオを処理しています..."
    AUDIO_DOWNLOADING_PROGRESS_MSG = "{process}\n📥 オーディオをダウンロードしています:\n{bar}   {percent:.1f}%"
    AUDIO_DOWNLOAD_ERROR_MSG = "オーディオのダウンロード中にエラーが発生しました。"
    AUDIO_DOWNLOAD_COMPLETE_MSG = "{process}\n{bar}   100.0%"
    AUDIO_EXTRACTION_FAILED_MSG = "❌ オーディオ情報の抽出に失敗しました"
    AUDIO_UNSUPPORTED_FILE_TYPE_MSG = "インデックス{index}のプレイリストでサポートされていないファイルタイプをスキップしています"
    AUDIO_FILE_NOT_FOUND_MSG = "ダウンロード後にオーディオファイルが見つかりません。"
    AUDIO_UPLOADING_MSG = "{process}\n📤 オーディオファイルをアップロードしています...\n{bar}   100.0%"
    AUDIO_SEND_FAILED_MSG = "❌ オーディオの送信に失敗しました: {error}"
    PLAYLIST_AUDIO_SENT_LOG_MSG = "プレイリストのオーディオを送信しました: {sent}/{total}ファイル (品質={quality}) ユーザー{user_id}"
    AUDIO_DOWNLOAD_FAILED_MSG = "❌ オーディオのダウンロードに失敗しました: {error}"
    DOWNLOAD_TIMEOUT_MSG = "⏰ タイムアウトのためダウンロードがキャンセルされました (2時間)"
    VIDEO_DOWNLOAD_COMPLETE_MSG = "{process}\n{bar}   100.0%"
    
    # FFmpeg messages
    VIDEO_FILE_NOT_FOUND_MSG = "❌ ビデオファイルが見つかりません: {filename}"
    VIDEO_PROCESSING_ERROR_MSG = "❌ ビデオの処理中にエラーが発生しました: {error}"
    
    # Sender messages
    ERROR_SENDING_DESCRIPTION_FILE_MSG = "❌ 説明ファイルの送信中にエラーが発生しました: {error}"
    CHANGE_CAPTION_HINT_MSG = "<blockquote>📝 ビデオのキャプションを変更したい場合は、新しいテキストでビデオに返信してください</blockquote>"
    
    # Always Ask Menu Messages
    NO_SUBTITLES_DETECTED_MSG = "字幕は検出されませんでした"
    VIDEO_PROGRESS_MSG = "<b>ビデオ:</b> {current} / {total}"
    AUDIO_PROGRESS_MSG = "<b>オーディオ:</b> {current} / {total}"
    
    # Error messages
    ERROR_CHECK_SUPPORTED_SITES_MSG = "あなたのサイトがサポートされているか<a href=\"https://github.com/chelaxian/tg-ytdlp-bot/wiki/YT_DLP#supported-sites\">こちら</a>で確認してください"
    ERROR_COOKIE_NEEDED_MSG = "このビデオをダウンロードするには<code>cookie</code>が必要な場合があります。まず、<b>/clean</b>コマンドでワークスペースをクリーンアップしてください"
    ERROR_COOKIE_INSTRUCTIONS_MSG = "Youtubeの場合 - <b>/cookie</b>コマンドで<code>cookie</code>を取得します。その他のサポートされているサイトの場合 - 独自のクッキー(<a href=\"https://t.me/tg_ytdlp/203\">ガイド1</a>)(<a href=\"https://t.me/tg_ytdlp/214\">ガイド2</a>)を送信し、その後ビデオリンクをもう一度送信してください。"
    CHOOSE_SUBTITLE_LANGUAGE_MSG = "字幕言語を選択してください"
    NO_ALTERNATIVE_AUDIO_LANGUAGES_MSG = "代替オーディオ言語はありません"
    CHOOSE_AUDIO_LANGUAGE_MSG = "オーディオ言語を選択してください"
    PAGE_NUMBER_MSG = "ページ{page}"
    TOTAL_PROGRESS_MSG = "合計進行状況"
    SUBTITLE_MENU_CLOSED_MSG = "字幕メニューを閉じました。"
    SUBTITLE_LANGUAGE_SET_MSG = "字幕言語がに設定されました: {value}"
    AUDIO_SET_MSG = "オーディオがに設定されました: {value}"
    FILTERS_UPDATED_MSG = "フィルターが更新されました"
    
    # Always Ask Menu Buttons
    BACK_BUTTON_TEXT = "🔙戻る"
    CLOSE_BUTTON_TEXT = "🔚閉じる"
    LIST_BUTTON_TEXT = "📃リスト"
    IMAGE_BUTTON_TEXT = "🖼画像"
    
    # Always Ask Menu Notes
    QUALITIES_NOT_AUTO_DETECTED_NOTE = "<blockquote>⚠️ 品質が自動検出されませんでした\n'その他'ボタンを使用して、利用可能なすべてのフォーマットを表示してください。</blockquote>"
    
    # Live Stream Messages
    LIVE_STREAM_DETECTED_MSG = "🚫 **ライブストリームが検出されました**\n\n進行中または無限のライブストリームのダウンロードは許可されていません。\n\nストリームが終了するのを待ってから、もう一度ダウンロードを試みてください:\n• ストリームの期間がわかっている\n• ストリームが終了した\n"
    AV1_NOT_AVAILABLE_FORMAT_SELECT_MSG = "`/format`コマンドを使用して別のフォーマットを選択してください。"
    
    # Direct Link Messages
    DIRECT_LINK_OBTAINED_MSG = "🔗 <b>ダイレクトリンクを取得しました</b>\n\n"
    TITLE_FIELD_MSG = "📹 <b>タイトル:</b> {title}\n"
    DURATION_FIELD_MSG = "⏱ <b>期間:</b> {duration} 秒\n"
    FORMAT_FIELD_MSG = "🎛 <b>フォーマット:</b> <code>{format_spec}</code>\n\n"
    VIDEO_STREAM_FIELD_MSG = "🎬 <b>ビデオストリーム:</b>\n<blockquote expandable><a href=\"{video_url}\">{video_url}</a></blockquote>\n\n"
    AUDIO_STREAM_FIELD_MSG = "🎵 <b>オーディオストリーム:</b>\n<blockquote expandable><a href=\"{audio_url}\">{audio_url}</a></blockquote>\n\n"
    
    # Processing Error Messages
    FILE_PROCESSING_ERROR_INVALID_CHARS_MSG = "❌ **ファイル処理エラー**\n\nビデオはダウンロードされましたが、ファイル名に無効な文字が含まれているため処理できませんでした。\n\n"
    FILE_PROCESSING_ERROR_INVALID_ARG_MSG = "❌ **ファイル処理エラー**\n\nビデオはダウンロードされましたが、無効な引数エラーのため処理できませんでした。\n\n"
    FORMAT_NOT_AVAILABLE_MSG = "❌ **フォーマットが利用できません**\n\nこのビデオで要求されたビデオフォーマットは利用できません。\n\n"
    FORMAT_ID_NOT_FOUND_MSG = "❌ フォーマットID {format_id}がこのビデオに見つかりません。\n\n利用可能なフォーマットID: {available_ids}\n"
    AV1_FORMAT_NOT_AVAILABLE_MSG = "❌ **このビデオではAV1フォーマットは利用できません。**\n\n**利用可能なフォーマット:**\n{formats_text}\n\n"
    
    # Additional Error Messages  
    AUDIO_FILE_PROCESSING_ERROR_INVALID_CHARS_MSG = "❌ **ファイル処理エラー**\n\nオーディオはダウンロードされましたが、ファイル名に無効な文字が含まれているため処理できませんでした。\n\n"
    AUDIO_FILE_PROCESSING_ERROR_INVALID_ARG_MSG = "❌ **ファイル処理エラー**\n\nオーディオはダウンロードされましたが、無効な引数エラーのため処理できませんでした。\n\n"
    
    # Keyboard Buttons
    CLEAN_EMOJI = "🧹"
    COOKIE_EMOJI = "🍪" 
    SETTINGS_EMOJI = "⚙️"
    PROXY_EMOJI = "🌐"
    IMAGE_EMOJI = "🖼"
    SEARCH_EMOJI = "🔍"
    VIDEO_EMOJI = "📼"
    USAGE_EMOJI = "📊"
    SPLIT_EMOJI = "✂️"
    AUDIO_EMOJI = "🎧"
    SUBTITLE_EMOJI = "💬"
    LANGUAGE_EMOJI = "🌎"
    TAG_EMOJI = "#️⃣"
    HELP_EMOJI = "🆘"
    LIST_EMOJI = "📃"
    PLAY_EMOJI = "⏯️"
    KEYBOARD_EMOJI = "🎹"
    LINK_EMOJI = "🔗"
    ARGS_EMOJI = "🧰"
    NSFW_EMOJI = "🔞"
    LIST_EMOJI = "📃"
    
    # NSFW Content Messages
    PORN_CONTENT_CANNOT_DOWNLOAD_MSG = "ユーザーがポルノコンテンツを入力しました。ダウンロードできません。"
    
    # Additional Log Messages
    NSFW_BLUR_SET_COMMAND_LOG_MSG = "コマンド経由でNSFWブラーを設定しました: {arg}"
    NSFW_MENU_OPENED_LOG_MSG = "ユーザーが/nsfwメニューを開きました。"
    NSFW_MENU_CLOSED_LOG_MSG = "NSFW: 閉じました。"
    COOKIES_DOWNLOAD_FAILED_LOG_MSG = "{service} のクッキーをダウンロードできませんでした: status={status} (URL 非表示)"
    COOKIES_DOWNLOAD_ERROR_LOG_MSG = "{service} のクッキーダウンロード中にエラーが発生しました: {error} (URL 非表示)"
    COOKIES_DOWNLOAD_UNEXPECTED_ERROR_LOG_MSG = "{service} のクッキーをダウンロード中に予期しないエラーが発生しました (URL 非表示): {error_type}: {error}"
    COOKIES_FILE_UPDATED_LOG_MSG = "ユーザー{user_id}のクッキーファイルが更新されました。"
    COOKIES_INVALID_CONTENT_LOG_MSG = "ユーザー{user_id}によって提供された無効なクッキーコンテンツ。"
    COOKIES_YOUTUBE_URLS_EMPTY_LOG_MSG = "ユーザー{user_id}のYouTubeクッキーURLは空です。"
    COOKIES_YOUTUBE_DOWNLOADED_VALIDATED_LOG_MSG = "YouTubeクッキーがダウンロードされ、ユーザー{user_id}のソース{source}から検証されました。"
    COOKIES_YOUTUBE_ALL_FAILED_LOG_MSG = "ユーザー{user_id}のすべてのYouTubeクッキーソースが失敗しました。"
    ADMIN_CHECK_PORN_ERROR_LOG_MSG = "管理者{admin_id}によるcheck_pornコマンドのエラー: {error}"
    SPLIT_SIZE_SET_CALLBACK_LOG_MSG = "分割パートサイズを{size}バイトに設定しました。"
    VIDEO_UPLOAD_COMPLETED_SPLITTING_LOG_MSG = "ファイル分割によるビデオのアップロードが完了しました。"
    PLAYLIST_VIDEOS_SENT_LOG_MSG = "プレイリストビデオを送信しました: {sent}/{total}ファイル (品質={quality}) ユーザー{user_id}"
    UNKNOWN_ERROR_MSG = "❌ 不明なエラー: {error}"
    SKIPPING_UNSUPPORTED_FILE_TYPE_MSG = "インデックス{index}のプレイリストでサポートされていないファイルタイプをスキップしています"
    FFMPEG_NOT_FOUND_MSG = "❌ FFmpegが見つかりません。FFmpegをインストールしてください。"
    CONVERSION_TO_MP4_FAILED_MSG = "❌ MP4への変換に失敗しました: {error}"
    EMBEDDING_SUBTITLES_WARNING_MSG = "⚠️ 字幕の埋め込みには時間がかかる場合があります (ビデオ1分あたり最大1分)！\n🔥 字幕の書き込みを開始しています..."
    SUBTITLES_CANNOT_EMBED_LIMITS_MSG = "ℹ️ 制限(品質/期間/サイズ)のため、字幕を埋め込むことはできません"
    SUBTITLES_NOT_AVAILABLE_LANGUAGE_MSG = "ℹ️ 選択した言語の字幕は利用できません"
    ERROR_SENDING_VIDEO_MSG = "❌ ビデオの送信中にエラーが発生しました: {error}"
    PLAYLIST_VIDEOS_SENT_MSG = "✅ プレイリストの動画を送信しました: {sent}/{total} ファイル。"
    DOWNLOAD_CANCELLED_TIMEOUT_MSG = "⏰ タイムアウトのためダウンロードがキャンセルされました (2時間)"
    FAILED_DOWNLOAD_VIDEO_MSG = "❌ ビデオのダウンロードに失敗しました: {error}"
    ERROR_SUBTITLES_NOT_FOUND_MSG = "❌ エラー: {error}"
    
    # Args command error messages
    ARGS_JSON_MUST_BE_OBJECT_MSG = "❌ JSONはオブジェクト(辞書)でなければなりません。"
    ARGS_INVALID_JSON_FORMAT_MSG = "❌ 無効なJSON形式です。有効なJSONを入力してください。"
    ARGS_VALUE_MUST_BE_BETWEEN_MSG = "❌ 値は{min_val}から{max_val}の間でなければなりません。"
    ARGS_PARAM_SET_TO_MSG = "✅ {description}をに設定しました: <code>{value}</code>"
    
    # Args command button texts
    ARGS_TRUE_BUTTON_MSG = "✅ True"
    ARGS_FALSE_BUTTON_MSG = "❌ False"
    ARGS_BACK_BUTTON_MSG = "🔙 戻る"
    ARGS_CLOSE_BUTTON_MSG = "🔚 閉じる"
    
    # Args command status texts
    ARGS_STATUS_TRUE_MSG = "✅"
    ARGS_STATUS_FALSE_MSG = "❌"
    ARGS_STATUS_TRUE_DISPLAY_MSG = "✅ True"
    ARGS_STATUS_FALSE_DISPLAY_MSG = "❌ False"
    ARGS_NOT_SET_MSG = "設定されていません"
    
    # Boolean values for import/export (all possible variations)
    ARGS_BOOLEAN_TRUE_VALUES = ["True", "true", "1", "yes", "on", "✅"]
    ARGS_BOOLEAN_FALSE_VALUES = ["False", "false", "0", "no", "off", "❌"]
    
    # Args command status indicators
    ARGS_STATUS_SELECTED_MSG = "✅"
    ARGS_STATUS_UNSELECTED_MSG = "⚪"
    
    # Down and Up error messages
    DOWN_UP_AV1_NOT_AVAILABLE_MSG = "❌ このビデオではAV1フォーマットは利用できません。\n\n利用可能なフォーマット:\n{formats_text}"
    DOWN_UP_ERROR_DOWNLOADING_MSG = "❌ ダウンロード中にエラーが発生しました: {error_message}"
    DOWN_UP_NO_VIDEOS_PLAYLIST_MSG = "❌ インデックス{index}のプレイリストにビデオが見つかりません。"
    DOWN_UP_VIDEO_CONVERSION_FAILED_INVALID_MSG = "❌ **ビデオ変換に失敗しました**\n\n無効な引数エラーのため、ビデオをMP4に変換できませんでした。\n\n"
    DOWN_UP_VIDEO_CONVERSION_FAILED_MSG = "❌ **ビデオ変換に失敗しました**\n\nビデオをMP4に変換できませんでした。\n\n"
    DOWN_UP_FAILED_STREAM_LINKS_MSG = "❌ ストリームリンクの取得に失敗しました"
    DOWN_UP_ERROR_GETTING_LINK_MSG = "❌ <b>リンクの取得中にエラーが発生しました:</b>\n{error_msg}"
    DOWN_UP_NO_CONTENT_FOUND_MSG = "❌ インデックス{index}にコンテンツが見つかりません"

    # Always Ask Menu error messages
    AA_ERROR_ORIGINAL_NOT_FOUND_MSG = "❌ エラー: 元のメッセージが見つかりません。"
    AA_ERROR_URL_NOT_FOUND_MSG = "❌ エラー: URLが見つかりません。"
    AA_ERROR_URL_NOT_EMBEDDABLE_MSG = "❌ このURLは埋め込むことができません。"
    AA_ERROR_CODEC_NOT_AVAILABLE_MSG = "❌ {codec}コーデックはこのビデオでは利用できません"
    AA_ERROR_FORMAT_NOT_AVAILABLE_MSG = "❌ {format}フォーマットはこのビデオでは利用できません"
    
    # Always Ask Menu button texts
    AA_AVC_BUTTON_MSG = "✅ AVC"
    AA_AVC_BUTTON_INACTIVE_MSG = "☑️ AVC"
    AA_AVC_BUTTON_UNAVAILABLE_MSG = "❌ AVC"
    AA_AV1_BUTTON_MSG = "✅ AV1"
    AA_AV1_BUTTON_INACTIVE_MSG = "☑️ AV1"
    AA_AV1_BUTTON_UNAVAILABLE_MSG = "❌ AV1"
    AA_VP9_BUTTON_MSG = "✅ VP9"
    AA_VP9_BUTTON_INACTIVE_MSG = "☑️ VP9"
    AA_VP9_BUTTON_UNAVAILABLE_MSG = "❌ VP9"
    AA_MP4_BUTTON_MSG = "✅ MP4"
    AA_MP4_BUTTON_INACTIVE_MSG = "☑️ MP4"
    AA_MP4_BUTTON_UNAVAILABLE_MSG = "❌ MP4"
    AA_MKV_BUTTON_MSG = "✅ MKV"
    AA_MKV_BUTTON_INACTIVE_MSG = "☑️ MKV"
    AA_MKV_BUTTON_UNAVAILABLE_MSG = "❌ MKV"

    # Flood limit messages
    FLOOD_LIMIT_TRY_LATER_MSG = "⏳ フラッド制限。後でもう一度お試しください。"
    
    # Cookies command button texts
    COOKIES_BROWSER_BUTTON_MSG = "✅ {browser_name}"
    COOKIES_CHECK_COOKIE_BUTTON_MSG = "✅ クッキーを確認"
    
    # Proxy command button texts
    PROXY_ON_BUTTON_MSG = "✅ オン"
    PROXY_OFF_BUTTON_MSG = "❌ オフ"
    PROXY_CLOSE_BUTTON_MSG = "🔚閉じる"
    
    # MediaInfo command button texts
    MEDIAINFO_ON_BUTTON_MSG = "✅ オン"
    MEDIAINFO_OFF_BUTTON_MSG = "❌ オフ"
    MEDIAINFO_CLOSE_BUTTON_MSG = "🔚閉じる"
    
    # Format command button texts
    FORMAT_AVC1_BUTTON_MSG = "✅ avc1 (H.264)"
    FORMAT_AVC1_BUTTON_INACTIVE_MSG = "☑️ avc1 (H.264)"
    FORMAT_AV01_BUTTON_MSG = "✅ av01 (AV1)"
    FORMAT_AV01_BUTTON_INACTIVE_MSG = "☑️ av01 (AV1)"
    FORMAT_VP9_BUTTON_MSG = "✅ vp09 (VP9)"
    FORMAT_VP9_BUTTON_INACTIVE_MSG = "☑️ vp09 (VP9)"
    FORMAT_MKV_ON_BUTTON_MSG = "✅ MKV: オン"
    FORMAT_MKV_OFF_BUTTON_MSG = "☑️ MKV: オフ"
    
    # Subtitles command button texts
    SUBS_LANGUAGE_CHECKMARK_MSG = "✅ "
    SUBS_AUTO_EMOJI_MSG = "✅"
    SUBS_AUTO_EMOJI_INACTIVE_MSG = "☑️"
    SUBS_ALWAYS_ASK_EMOJI_MSG = "✅"
    SUBS_ALWAYS_ASK_EMOJI_INACTIVE_MSG = "☑️"
    
    # NSFW command button texts
    NSFW_ON_NO_BLUR_MSG = "✅ オン (ぼかしなし)"
    NSFW_ON_NO_BLUR_INACTIVE_MSG = "☑️ オン (ぼかしなし)"
    NSFW_OFF_BLUR_MSG = "✅ オフ (ぼかし)"
    NSFW_OFF_BLUR_INACTIVE_MSG = "☑️ オフ (ぼかし)"
    
    # Admin command status texts
    ADMIN_STATUS_NSFW_MSG = "🔞"
    ADMIN_STATUS_CLEAN_MSG = "✅"
    ADMIN_STATUS_NSFW_TEXT_MSG = "NSFW"
    ADMIN_STATUS_CLEAN_TEXT_MSG = "クリーン"
    
    # Admin command additional messages
    ADMIN_ERROR_PROCESSING_REPLY_MSG = "ユーザー{user}の返信メッセージの処理中にエラーが発生しました: {error}"
    ADMIN_ERROR_SENDING_BROADCAST_MSG = "ユーザー{user}へのブロードキャストの送信中にエラーが発生しました: {error}"
    ADMIN_LOGS_FORMAT_MSG = "{bot_name}のログ\nユーザー: {user_id}\n合計ログ: {total}\n現在時刻: {now}\n\n{logs}"
    ADMIN_BOT_DATA_FORMAT_MSG = "{bot_name} {path}\n合計{path}: {count}\n現在時刻: {now}\n\n{data}"
    ADMIN_TOTAL_USERS_MSG = "<i>合計ユーザー数: {count}</i>\n最新20件の{path}:\n\n{display_list}"
    ADMIN_PORN_CACHE_RELOADED_MSG = "管理者{admin_id}によってポルノキャッシュがリロードされました。ドメイン: {domains}、キーワード: {keywords}、サイト: {sites}、ホワイトリスト: {whitelist}、グレーリスト: {greylist}、ブラックリスト: {black_list}、ホワイトキーワード: {white_keywords}、プロキシドメイン: {proxy_domains}、プロキシ2ドメイン: {proxy_2_domains}、クリーンクエリ: {clean_query}、非クッキードメイン: {no_cookie_domains}"
    
    # Args command additional messages
    ARGS_ERROR_SENDING_TIMEOUT_MSG = "タイムアウトメッセージの送信中にエラーが発生しました: {error}"
    
    # Language selection messages
    LANG_SELECTION_MSG = "🌍 <b>言語を選択してください</b>\n\n🇺🇸 English\n🇷🇺 Русский\n🇸🇦 العربية\n🇮🇳 हिन्दी\n🇨🇳 中文\n🇯🇵 日本語"
    LANG_CHANGED_MSG = "✅ 言語を{lang_name}に変更しました"
    LANG_ERROR_MSG = "❌ 言語の変更中にエラーが発生しました"
    LANG_CLOSED_MSG = "言語選択を閉じました"
    # Clean command additional messages
    
    # Cookies command additional messages
    COOKIES_BROWSER_CALLBACK_MSG = "[ブラウザ]コールバック: {callback_data}"
    COOKIES_ADDING_BROWSER_MONITORING_MSG = "URL付きのブラウザ監視ボタンを追加しています: {miniapp_url}"
    COOKIES_BROWSER_MONITORING_URL_NOT_CONFIGURED_MSG = "ブラウザ監視URLが設定されていません: {miniapp_url}"
    
    # Format command additional messages
    
    # Keyboard command additional messages
    KEYBOARD_SETTING_UPDATED_MSG = "🎹 **キーボード設定が更新されました！**\n\n新しい設定: **{setting}**"
    KEYBOARD_FAILED_HIDE_MSG = "キーボードの非表示に失敗しました: {error}"
    
    # Link command additional messages
    LINK_USING_WORKING_YOUTUBE_COOKIES_MSG = "ユーザー{user_id}のリンク抽出に有効なYouTubeクッキーを使用しています"
    LINK_NO_WORKING_YOUTUBE_COOKIES_MSG = "ユーザー{user_id}のリンク抽出に利用できる有効なYouTubeクッキーがありません"
    LINK_USING_EXISTING_YOUTUBE_COOKIES_MSG = "ユーザー{user_id}のリンク抽出に既存のYouTubeクッキーを使用しています"
    LINK_NO_YOUTUBE_COOKIES_FOUND_MSG = "ユーザー{user_id}のリンク抽出にYouTubeクッキーが見つかりません"
    LINK_COPIED_GLOBAL_COOKIE_FILE_MSG = "グローバルクッキーファイルをユーザー{user_id}のフォルダにコピーしてリンクを抽出しました"
    
    # MediaInfo command additional messages
    MEDIAINFO_USER_REQUESTED_MSG = "[MEDIAINFO] ユーザー{user_id}がmediainfoコマンドをリクエストしました"
    MEDIAINFO_USER_IS_ADMIN_MSG = "[MEDIAINFO] ユーザー{user_id}は管理者です: {is_admin}"
    MEDIAINFO_USER_IS_IN_CHANNEL_MSG = "[MEDIAINFO] ユーザー{user_id}はチャンネルに参加しています: {is_in_channel}"
    MEDIAINFO_ACCESS_DENIED_MSG = "[MEDIAINFO] ユーザー{user_id}のアクセスが拒否されました - 管理者ではなく、チャンネルにも参加していません"
    MEDIAINFO_ACCESS_GRANTED_MSG = "[MEDIAINFO] ユーザー{user_id}のアクセスが許可されました"
    MEDIAINFO_CALLBACK_MSG = "[MEDIAINFO]コールバック: {callback_data}"
    
    # URL Parser error messages
    URL_PARSER_ADMIN_ONLY_MSG = "❌ このコマンドは管理者のみが利用できます。"
    
    # Helper messages
    HELPER_DOWNLOAD_FINISHED_PO_MSG = "✅ POトークンサポートでダウンロードが完了しました"
    HELPER_FLOOD_LIMIT_TRY_LATER_MSG = "⏳ フラッド制限。後でもう一度お試しください。"
    
    # Database error messages
    DB_REST_TOKEN_REFRESH_ERROR_MSG = "❌ RESTトークンのリフレッシュエラー: {error}"
    DB_ERROR_CLOSING_SESSION_MSG = "❌ Firebaseセッションのクローズ中にエラーが発生しました: {error}"
    DB_ERROR_INITIALIZING_BASE_MSG = "❌ 基本データベース構造の初期化中にエラーが発生しました: {error}"

    DB_NOT_ALL_PARAMETERS_SET_MSG = "❌ config.pyにすべてのパラメータが設定されていません (FIREBASE_CONF, FIREBASE_USER, FIREBASE_PASSWORD)"
    DB_DATABASE_URL_NOT_SET_MSG = "❌ FIREBASE_CONF.databaseURLが設定されていません"
    DB_API_KEY_NOT_SET_MSG = "❌ idTokenを取得するためのFIREBASE_CONF.apiKeyが設定されていません"
    DB_ERROR_DOWNLOADING_DUMP_MSG = "❌ Firebaseダンプのダウンロード中にエラーが発生しました: {error}"
    DB_FAILED_DOWNLOAD_DUMP_REST_MSG = "❌ REST経由でのFirebaseダンプのダウンロードに失敗しました"
    DB_ERROR_DOWNLOAD_RELOAD_CACHE_MSG = "❌ _download_and_reload_cacheでエラーが発生しました: {error}"
    DB_ERROR_RUNNING_AUTO_RELOAD_MSG = "❌ 自動reload_cacheの実行中にエラーが発生しました (試行{attempt}/{max_retries}): {error}"
    DB_ALL_RETRY_ATTEMPTS_FAILED_MSG = "❌ すべての再試行に失敗しました"
    DB_STARTING_FIREBASE_DUMP_MSG = "🔄 {datetime}にFirebaseダンプのダウンロードを開始しています"
    DB_DEPENDENCY_NOT_AVAILABLE_MSG = "⚠️ 依存関係が利用できません: requestsまたはSession"
    DB_DATABASE_EMPTY_MSG = "⚠️ データベースは空です"
    
    # Magic.py error messages
    MAGIC_ERROR_CLOSING_LOGGER_MSG = "❌ ロガーのクローズ中にエラーが発生しました: {error}"
    MAGIC_ERROR_DURING_CLEANUP_MSG = "❌ クリーンアップ中にエラーが発生しました: {error}"
    
    # Update from repo error messages
    UPDATE_CLONE_ERROR_MSG = "❌ クローンエラー: {error}"
    UPDATE_CLONE_TIMEOUT_MSG = "❌ クローンタイムアウト"
    UPDATE_CLONE_EXCEPTION_MSG = "❌ クローン例外: {error}"
    UPDATE_CANCELED_BY_USER_MSG = "❌ ユーザーによって更新がキャンセルされました"

    # Update from repo success messages
    UPDATE_REPOSITORY_CLONED_SUCCESS_MSG = "✅ リポジトリが正常にクローンされました"
    UPDATE_BACKUPS_MOVED_MSG = "✅ バックアップが_backup/に移動されました"
    
    # Magic.py success messages
    MAGIC_ALL_MODULES_LOADED_MSG = "✅ すべてのモジュールがロードされました"
    MAGIC_CLEANUP_COMPLETED_MSG = "✅ 終了時にクリーンアップが完了しました"
    MAGIC_SIGNAL_RECEIVED_MSG = "\n🛑 シグナル{signal}を受信しました。正常にシャットダウンしています..."
    
    # Removed duplicate logger messages - these are user messages, not logger messages
    
    # Download status messages
    DOWNLOAD_STATUS_PLEASE_WAIT_MSG = "お待ちください..."
    DOWNLOAD_STATUS_HOURGLASS_EMOJIS = ["⏳", "⌛"]
    DOWNLOAD_STATUS_DOWNLOADING_HLS_MSG = "📥 HLSストリームをダウンロードしています:"
    DOWNLOAD_STATUS_WAITING_FRAGMENTS_MSG = "フラグメントを待っています"
    
    # Restore from backup messages
    RESTORE_BACKUP_NOT_FOUND_MSG = "❌ バックアップ{ts}が_backup/に見つかりません"
    RESTORE_FAILED_RESTORE_MSG = "❌ {src} -> {dest_path}の復元に失敗しました: {e}"
    RESTORE_SUCCESS_RESTORED_MSG = "✅ 復元済み: {dest_path}"
    
    # Image command messages
    IMG_INSTAGRAM_AUTH_ERROR_MSG = "❌ <b>{error_type}</b>\n\n<b>URL:</b> <code>{url}</code>\n\n<b>詳細:</b> {error_details}\n\n重大なエラーのためダウンロードが停止しました。\n\n💡 <b>ヒント:</b> 401 Unauthorizedエラーが発生した場合は、<code>/cookie instagram</code>コマンドを使用するか、独自のクッキーを送信してInstagramで認証してみてください。"
    
    # Porn filter messages
    PORN_DOMAIN_BLACKLIST_MSG = "❌ ポルノブラックリスト内のドメイン: {domain_parts}"
    PORN_KEYWORDS_FOUND_MSG = "❌ ポルノキーワードが見つかりました: {keywords}"
    PORN_DOMAIN_WHITELIST_MSG = "✅ ホワイトリスト内のドメイン: {domain}"
    PORN_WHITELIST_KEYWORDS_MSG = "✅ ホワイトリストキーワードが見つかりました: {keywords}"
    PORN_NO_KEYWORDS_FOUND_MSG = "✅ ポルノキーワードは見つかりませんでした"
    
    # Audio download messages
    AUDIO_TIKTOK_API_ERROR_SKIP_MSG = "⚠️ インデックス{index}でTikTok APIエラーが発生しました。次のオーディオにスキップします..."
    
    # Video download messages  
    VIDEO_TIKTOK_API_ERROR_SKIP_MSG = "⚠️ インデックス{index}でTikTok APIエラーが発生しました。次のビデオにスキップします..."
    
    # URL Parser messages
    URL_PARSER_USER_ENTERED_URL_LOG_MSG = "ユーザーが<b>url</b>を入力しました\n <b>ユーザー名:</b> {user_name}\nURL: {url}"
    URL_PARSER_USER_ENTERED_INVALID_MSG = "<b>ユーザーはこのように入力しました:</b> {input}\n{error_msg}"
    
    # Channel subscription messages
    CHANNEL_JOIN_BUTTON_MSG = "チャンネルに参加"
    
    # Handler registry messages
    HANDLER_REGISTERING_MSG = "🔍 ハンドラを登録しています: {handler_type} - {func_name}"
    
    # Clean command button messages
    CLEAN_COOKIE_DOWNLOAD_BUTTON_MSG = "📥 /cookie - 5つのクッキーをダウンロード"
    CLEAN_COOKIES_FROM_BROWSER_BUTTON_MSG = "🌐 /cookies_from_browser - ブラウザのYTクッキーを取得"
    CLEAN_CHECK_COOKIE_BUTTON_MSG = "🔎 /check_cookie - クッキーファイルを検証"
    CLEAN_SAVE_AS_COOKIE_BUTTON_MSG = "🔖 /save_as_cookie - カスタムクッキーをアップロード"
    
    # List command messages
    LIST_CLOSE_BUTTON_MSG = "🔚 閉じる"
    LIST_AVAILABLE_FORMATS_HEADER_MSG = "{url}で利用可能なフォーマット"
    LIST_FORMATS_FILE_NAME_MSG = "formats_{user_id}.txt"
    
    # Other handlers button messages
    OTHER_AUDIO_HINT_CLOSE_BUTTON_MSG = "🔚閉じる"
    OTHER_PLAYLIST_HELP_CLOSE_BUTTON_MSG = "🔚閉じる"
    
    # Search command button messages
    SEARCH_CLOSE_BUTTON_MSG = "🔚閉じる"
    
    # Tag command button messages
    TAG_CLOSE_BUTTON_MSG = "🔚閉じる"
    
    # Magic.py callback messages
    MAGIC_HELP_CLOSED_MSG = "ヘルプを閉じました。"
    
    # URL extractor callback messages
    URL_EXTRACTOR_CLOSED_MSG = "閉鎖"
    URL_EXTRACTOR_ERROR_OCCURRED_MSG = "エラーが発生しました"
    
    # FFmpeg messages
    FFMPEG_NOT_FOUND_MSG = "ffmpegがPATHまたはプロジェクトディレクトリに見つかりません。FFmpegをインストールしてください。"
    YTDLP_NOT_FOUND_MSG = "yt-dlpバイナリがPATHまたはプロジェクトディレクトリに見つかりません。yt-dlpをインストールしてください。"
    FFMPEG_VIDEO_SPLIT_EXCESSIVE_MSG = "ビデオは{rounds}個のパートに分割されますが、これは過剰な可能性があります"
    FFMPEG_SPLITTING_VIDEO_PART_MSG = "ビデオパート{current}/{total}を分割しています: {start_time:.2f}秒から{end_time:.2f}秒"
    FFMPEG_FAILED_CREATE_SPLIT_PART_MSG = "分割パート{part}の作成に失敗しました: {target_name}"
    FFMPEG_SUCCESSFULLY_CREATED_SPLIT_PART_MSG = "分割パート{part}を正常に作成しました: {target_name} ({size}バイト)"
    FFMPEG_ERROR_SPLITTING_VIDEO_PART_MSG = "ビデオパート{part}の分割中にエラーが発生しました: {error}"
    FFMPEG_VIDEO_SPLIT_SUCCESS_MSG = "ビデオが{count}個のパートに正常に分割されました"
    FFMPEG_ERROR_VIDEO_SPLITTING_PROCESS_MSG = "ビデオ分割プロセスでエラーが発生しました: {error}"
    FFMPEG_FFPROBE_BYPASS_ERROR_MSG = "[FFPROBE BYPASS] ビデオ{video_path}の処理中にエラーが発生しました: {error}"
    FFMPEG_VIDEO_FILE_NOT_EXISTS_MSG = "ビデオファイルが存在しません: {video_path}"
    FFMPEG_ERROR_PARSING_DIMENSIONS_MSG = "次元'{size_result}'の解析中にエラーが発生しました: {error}"
    FFMPEG_COULD_NOT_DETERMINE_DIMENSIONS_MSG = "'{size_result}'からビデオの次元を特定できませんでした。デフォルトを使用します: {width}x{height}"
    FFMPEG_ERROR_CREATING_THUMBNAIL_MSG = "サムネイルの作成中にエラーが発生しました: {stderr}"
    FFMPEG_ERROR_PARSING_DURATION_MSG = "ビデオの期間の解析中にエラーが発生しました: {error}、結果は: {result}"
    FFMPEG_THUMBNAIL_NOT_CREATED_MSG = "サムネイルが{thumb_dir}に作成されませんでした。デフォルトを使用します"
    FFMPEG_COMMAND_EXECUTION_ERROR_MSG = "コマンドの実行エラー: {error}"
    FFMPEG_ERROR_CREATING_THUMBNAIL_WITH_FFMPEG_MSG = "FFmpegでサムネイルの作成中にエラーが発生しました: {error}"
    
    # Gallery-dl messages
    GALLERY_DL_SKIPPING_NON_DICT_CONFIG_MSG = "非辞書設定セクションをスキップしています: {section}={opts}"
    GALLERY_DL_SETTING_CONFIG_MSG = "{section}.{key} = {value}を設定しています"
    GALLERY_DL_USING_USER_COOKIES_MSG = "[gallery-dl] ユーザーのクッキーを使用しています: {cookie_path}"
    GALLERY_DL_USING_YOUTUBE_COOKIES_MSG = "ユーザー{user_id}のYouTubeクッキーを使用しています"
    GALLERY_DL_COPIED_GLOBAL_COOKIE_MSG = "グローバルクッキーファイルをユーザー{user_id}のフォルダにコピーしました"
    GALLERY_DL_USING_COPIED_GLOBAL_COOKIES_MSG = "[gallery-dl] コピーされたグローバルクッキーをユーザーのクッキーとして使用しています: {cookie_path}"
    GALLERY_DL_FAILED_COPY_GLOBAL_COOKIE_MSG = "ユーザー{user_id}のグローバルクッキーファイルのコピーに失敗しました: {error}"
    GALLERY_DL_USING_NO_COOKIES_MSG = "ドメインに--no-cookiesを使用しています: {url}"
    GALLERY_DL_PROXY_REQUESTED_FAILED_MSG = "プロキシがリクエストされましたが、設定のインポート/取得に失敗しました: {error}"
    GALLERY_DL_FORCE_USING_PROXY_MSG = "gallery-dlにプロキシを強制的に使用しています: {proxy_url}"
    GALLERY_DL_PROXY_CONFIG_INCOMPLETE_MSG = "プロキシがリクエストされましたが、プロキシ設定が不完全です"
    GALLERY_DL_PROXY_HELPER_FAILED_MSG = "プロキシヘルパーが失敗しました: {error}"
    GALLERY_DL_PARSING_EXTRACTOR_ITEMS_MSG = "エクストラクタアイテムを解析しています..."
    GALLERY_DL_ITEM_COUNT_MSG = "アイテム{count}: {item}"
    GALLERY_DL_FOUND_METADATA_TAG2_MSG = "メタデータが見つかりました (タグ2): {info}"
    GALLERY_DL_FOUND_URL_TAG3_MSG = "URLが見つかりました (タグ3): {url}, メタデータ: {metadata}"
    GALLERY_DL_FOUND_METADATA_LEGACY_MSG = "メタデータが見つかりました (レガシー): {info}"
    GALLERY_DL_FOUND_URL_LEGACY_MSG = "URLが見つかりました (レガシー): {url}"
    GALLERY_DL_FOUND_FILENAME_MSG = "ファイル名が見つかりました: {filename}"
    GALLERY_DL_FOUND_DIRECTORY_MSG = "ディレクトリが見つかりました: {directory}"
    GALLERY_DL_FOUND_EXTENSION_MSG = "拡張子が見つかりました: {extension}"
    GALLERY_DL_PARSED_ITEMS_MSG = "{count}個のアイテムを解析しました、情報: {info}, フォールバック: {fallback}"
    GALLERY_DL_SETTING_CONFIG_MSG2 = "gallery-dl設定を設定しています: {config}"
    GALLERY_DL_TRYING_STRATEGY_A_MSG = "戦略Aを試しています: extractor.find + items()"
    GALLERY_DL_EXTRACTOR_MODULE_NOT_FOUND_MSG = "gallery_dl.extractorモジュールが見つかりません"
    GALLERY_DL_EXTRACTOR_FIND_NOT_AVAILABLE_MSG = "gallery_dl.extractor.find()がこのビルドでは利用できません"
    GALLERY_DL_CALLING_EXTRACTOR_FIND_MSG = "extractor.find({url})を呼び出しています"
    GALLERY_DL_NO_EXTRACTOR_MATCHED_MSG = "URLに一致するエクストラクタがありません"
    GALLERY_DL_SETTING_COOKIES_ON_EXTRACTOR_MSG = "エクストラクタにクッキーを設定しています: {cookie_path}"
    GALLERY_DL_FAILED_SET_COOKIES_ON_EXTRACTOR_MSG = "エクストラクタへのクッキーの設定に失敗しました: {error}"
    GALLERY_DL_EXTRACTOR_FOUND_CALLING_ITEMS_MSG = "エクストラクタが見つかりました、items()を呼び出しています"
    GALLERY_DL_STRATEGY_A_SUCCEEDED_MSG = "戦略Aが成功しました、情報を取得しました: {info}"
    GALLERY_DL_STRATEGY_A_NO_VALID_INFO_MSG = "戦略A: extractor.items()は有効な情報を返しませんでした"
    GALLERY_DL_STRATEGY_A_FAILED_MSG = "戦略A (extractor.find)が失敗しました: {error}"
    GALLERY_DL_FALLBACK_METADATA_MSG = "--get-urlsからのフォールバックメタデータ: 合計={total}"
    GALLERY_DL_ALL_STRATEGIES_FAILED_MSG = "すべての戦略がメタデータの取得に失敗しました"
    GALLERY_DL_FAILED_EXTRACT_IMAGE_INFO_MSG = "画像情報の抽出に失敗しました: {error}"
    GALLERY_DL_JOB_MODULE_NOT_FOUND_MSG = "gallery_dl.jobモジュールが見つかりません (インストールが壊れている可能性があります)"
    GALLERY_DL_DOWNLOAD_JOB_NOT_AVAILABLE_MSG = "gallery_dl.job.DownloadJobがこのビルドでは利用できません"
    GALLERY_DL_SEARCHING_DOWNLOADED_FILES_MSG = "gallery-dlディレクトリでダウンロードされたファイルを検索しています"
    GALLERY_DL_TRYING_FIND_FILES_BY_NAMES_MSG = "エクストラクタからファイル名でファイルを検索しようとしています"
    
    # Sender messages
    SENDER_ERROR_READING_USER_ARGS_MSG = "ユーザー{user_id}のユーザー引数の読み取り中にエラーが発生しました: {error}"
    SENDER_FFPROBE_BYPASS_ERROR_MSG = "[FFPROBE BYPASS] ビデオ{video_path}の処理中にエラーが発生しました: {error}"
    SENDER_USER_SEND_AS_FILE_ENABLED_MSG = "ユーザー{user_id}がsend_as_fileを有効にしているため、ドキュメントとして送信しています"
    SENDER_SEND_VIDEO_TIMED_OUT_MSG = "send_videoが繰り返しタイムアウトしました。send_documentにフォールバックします"
    SENDER_CAPTION_TOO_LONG_MSG = "キャプションが長すぎます。最小限のキャプションで試行しています"
    SENDER_SEND_VIDEO_MINIMAL_CAPTION_TIMED_OUT_MSG = "send_video (最小限のキャプション)がタイムアウトしました。send_documentにフォールバックします"
    SENDER_ERROR_SENDING_VIDEO_MINIMAL_CAPTION_MSG = "最小限のキャプションでビデオの送信中にエラーが発生しました: {error}"
    SENDER_ERROR_SENDING_FULL_DESCRIPTION_FILE_MSG = "完全な説明ファイルの送信中にエラーが発生しました: {error}"
    SENDER_ERROR_REMOVING_TEMP_DESCRIPTION_FILE_MSG = "一時的な説明ファイルの削除中にエラーが発生しました: {error}"
    
    # YT-DLP hook messages
    YTDLP_SKIPPING_MATCH_FILTER_MSG = "NO_FILTER_DOMAINSのドメインのmatch_filterをスキップしています: {url}"
    YTDLP_CHECKING_EXISTING_YOUTUBE_COOKIES_MSG = "ユーザー{user_id}のフォーマット検出のために、ユーザーのURLで既存のYouTubeクッキーを確認しています"
    YTDLP_EXISTING_YOUTUBE_COOKIES_WORK_MSG = "ユーザー{user_id}のフォーマット検出のために、既存のYouTubeクッキーがユーザーのURLで機能しています - それらを使用しています"
    YTDLP_EXISTING_YOUTUBE_COOKIES_FAILED_MSG = "既存のYouTubeクッキーがユーザーのURLで失敗しました。ユーザー{user_id}のフォーマット検出のために新しいものを取得しようとしています"
    YTDLP_TRYING_YOUTUBE_COOKIE_SOURCE_MSG = "ユーザー{user_id}のフォーマット検出のためにYouTubeクッキーソース{i}を試しています"
    YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_WORK_MSG = "ソース{i}のYouTubeクッキーがユーザー{user_id}のフォーマット検出のためにユーザーのURLで機能しています - ユーザーフォルダに保存されました"
    YTDLP_YOUTUBE_COOKIES_FROM_SOURCE_DONT_WORK_MSG = "ソース{i}のYouTubeクッキーがユーザー{user_id}のフォーマット検出のためにユーザーのURLで機能しません"
    YTDLP_FAILED_DOWNLOAD_YOUTUBE_COOKIES_MSG = "ユーザー{user_id}のフォーマット検出のためにソース{i}からYouTubeクッキーをダウンロードできませんでした"
    YTDLP_ALL_YOUTUBE_COOKIE_SOURCES_FAILED_MSG = "ユーザー{user_id}のフォーマット検出のためにすべてのYouTubeクッキーソースが失敗しました。クッキーなしで試します"
    YTDLP_NO_YOUTUBE_COOKIE_SOURCES_CONFIGURED_MSG = "ユーザー{user_id}のフォーマット検出のためにYouTubeクッキーソースが設定されていません。クッキーなしで試します"
    YTDLP_NO_YOUTUBE_COOKIES_FOUND_MSG = "ユーザー{user_id}のフォーマット検出にYouTubeクッキーが見つかりません。新しいものを取得しようとしています"
    YTDLP_USING_YOUTUBE_COOKIES_ALREADY_VALIDATED_MSG = "ユーザー{user_id}のフォーマット検出にYouTubeクッキーを使用しています (常時確認メニューで既に検証済み)"
    YTDLP_NO_YOUTUBE_COOKIES_FOUND_ATTEMPTING_RESTORE_MSG = "ユーザー{user_id}のフォーマット検出にYouTubeクッキーが見つかりません。復元を試みています..."
    YTDLP_COPIED_GLOBAL_COOKIE_FILE_MSG = "グローバルクッキーファイルをユーザー{user_id}のフォルダにコピーしてフォーマットを検出しました"
    YTDLP_FAILED_COPY_GLOBAL_COOKIE_FILE_MSG = "ユーザー{user_id}のグローバルクッキーファイルのコピーに失敗しました: {error}"
    YTDLP_USING_NO_COOKIES_FOR_DOMAIN_MSG = "get_video_formatsのドメインに--no-cookiesを使用しています: {url}"
    
    # App instance messages
    APP_INSTANCE_NOT_INITIALIZED_MSG = "アプリはまだ初期化されていません。{name}にアクセスできません"
    
    # Caption messages
    CAPTION_INFO_OF_VIDEO_MSG = "\n<b>キャプション:</b> <code>{caption}</code>\n<b>ユーザーID:</b> <code>{user_id}</code>\n<b>ユーザー名:</b> <code>{users_name}</code>\n<b>ビデオファイルID:</b> <code>{video_file_id}</code>"
    CAPTION_ERROR_IN_CAPTION_EDITOR_MSG = "caption_editorでエラーが発生しました: {error}"
    CAPTION_UNEXPECTED_ERROR_IN_CAPTION_EDITOR_MSG = "caption_editorで予期しないエラーが発生しました: {error}"
    CAPTION_VIDEO_URL_LINK_MSG = "<a href=\"{url}\">🔗 ビデオURL</a>{bot_mention}"
    
    # Database messages
    DB_DATABASE_URL_MISSING_MSG = "FIREBASE_CONF.databaseURLが設定にありません"
    DB_FIREBASE_ADMIN_INITIALIZED_MSG = "✅ firebase_adminが初期化されました"
    DB_REST_ID_TOKEN_REFRESHED_MSG = "🔁 REST idTokenが更新されました"
    DB_LOG_FOR_USER_ADDED_MSG = "ユーザーのログが追加されました"
    DB_DATABASE_CREATED_MSG = "dbが作成されました"
    DB_BOT_STARTED_MSG = "ボットが起動しました"
    DB_RELOAD_CACHE_EVERY_PERSISTED_MSG = "RELOAD_CACHE_EVERYがconfig.pyに永続化されました: {hours}時間"
    DB_PLAYLIST_PART_ALREADY_CACHED_MSG = "プレイリストパートは既にキャッシュされています: {path_parts}, スキップします"
    DB_GET_CACHED_PLAYLIST_VIDEOS_NO_CACHE_MSG = "get_cached_playlist_videos: URL/品質バリアントのキャッシュが見つかりません。空の辞書を返します"
    DB_GET_CACHED_PLAYLIST_COUNT_FAST_COUNT_MSG = "get_cached_playlist_count: 大規模な範囲の高速カウント: {cached_count}個のキャッシュされたビデオ"
    DB_GET_CACHED_MESSAGE_IDS_NO_CACHE_MSG = "get_cached_message_ids: ハッシュ{url_hash}、品質{quality_key}のキャッシュが見つかりません"
    DB_GET_CACHED_MESSAGE_IDS_NO_CACHE_ANY_VARIANT_MSG = "get_cached_message_ids: URLバリアントのキャッシュが見つかりません。Noneを返します"
    
    # Database cache auto-reload messages
    DB_AUTO_CACHE_ACCESS_DENIED_MSG = "❌ アクセスが拒否されました。管理者のみ。"
    DB_AUTO_CACHE_RELOADING_UPDATED_MSG = "🔄 自動Firebaseキャッシュリロードが更新されました！\n\n📊 ステータス: {status}\n⏰ スケジュール: 00:00から{interval}時間ごと\n🕒 次回のリロード: {next_exec} ({delta_min}分後)"
    DB_AUTO_CACHE_RELOADING_STOPPED_MSG = "🛑 自動Firebaseキャッシュリロードが停止しました！\n\n📊 ステータス: ❌ 無効\n💡 再有効化するには/auto_cache onを使用してください"
    DB_AUTO_CACHE_INVALID_ARGUMENT_MSG = "❌ 無効な引数です。/auto_cache on | off | N (1..168)を使用してください"
    DB_AUTO_CACHE_INTERVAL_RANGE_MSG = "❌ 間隔は1〜168時間でなければなりません"
    DB_AUTO_CACHE_FAILED_SET_INTERVAL_MSG = "❌ 間隔の設定に失敗しました"
    DB_AUTO_CACHE_INTERVAL_UPDATED_MSG = "⏱️ 自動Firebaseキャッシュ間隔が更新されました！\n\n📊 ステータス: ✅ 有効\n⏰ スケジュール: 00:00から{interval}時間ごと\n🕒 次回のリロード: {next_exec} ({delta_min}分後)"
    DB_AUTO_CACHE_RELOADING_STARTED_MSG = "🔄 自動Firebaseキャッシュリロードが開始されました！\n\n📊 ステータス: ✅ 有効\n⏰ スケジュール: 00:00から{interval}時間ごと\n🕒 次回のリロード: {next_exec} ({delta_min}分後)"
    DB_AUTO_CACHE_RELOADING_STOPPED_BY_ADMIN_MSG = "🛑 自動Firebaseキャッシュリロードが停止しました！\n\n📊 ステータス: ❌ 無効\n💡 再有効化するには/auto_cache onを使用してください"
    DB_AUTO_CACHE_RELOAD_ENABLED_LOG_MSG = "自動リロードが有効になりました。次回は{next_exec}"
    DB_AUTO_CACHE_RELOAD_DISABLED_LOG_MSG = "管理者が自動リロードを無効にしました。"
    DB_AUTO_CACHE_INTERVAL_SET_LOG_MSG = "自動リロード間隔が{interval}時間に設定されました。次回は{next_exec}"
    DB_AUTO_CACHE_RELOAD_STARTED_LOG_MSG = "自動リロードが開始されました。次回は{next_exec}"
    DB_AUTO_CACHE_RELOAD_STOPPED_LOG_MSG = "管理者が自動リロードを停止しました。"
    
    # Database cache messages (console output)
    DB_FIREBASE_CACHE_LOADED_MSG = "✅ Firebaseキャッシュがロードされました: {count}個のルートノード"
    DB_FIREBASE_CACHE_NOT_FOUND_MSG = "⚠️ Firebaseキャッシュファイルが見つかりません。空のキャッシュで開始します: {cache_file}"
    DB_FAILED_LOAD_FIREBASE_CACHE_MSG = "❌ Firebaseキャッシュのロードに失敗しました: {error}"
    DB_FIREBASE_CACHE_RELOADED_MSG = "✅ Firebaseキャッシュがリロードされました: {count}個のルートノード"
    DB_FIREBASE_CACHE_FILE_NOT_FOUND_MSG = "⚠️ Firebaseキャッシュファイルが見つかりません: {cache_file}"
    DB_FAILED_RELOAD_FIREBASE_CACHE_MSG = "❌ Firebaseキャッシュのリロードに失敗しました: {error}"
    
    # Database user ban messages
    DB_USER_BANNED_MSG = "🚫 あなたはボットから禁止されています！"
    
    # Always Ask Menu messages
    AA_NO_VIDEO_FORMATS_FOUND_MSG = "❔ ビデオフォーマットが見つかりません。画像ダウンローダーを試しています…"
    AA_FLOOD_WAIT_MSG = "⚠️ Telegramはメッセージの送信を制限しています。\n⏳ お待ちください: {time_str}\nタイマーを更新するには、URLをもう一度2回送信してください。"
    AA_VLC_IOS_MSG = "🎬 <b><a href=\"https://itunes.apple.com/app/apple-store/id650377962\">VLC Player (iOS)</a></b>\n\n<i>ボタンをクリックしてストリームURLをコピーし、VLCアプリに貼り付けてください</i>"
    AA_VLC_ANDROID_MSG = "🎬 <b><a href=\"https://play.google.com/store/apps/details?id=org.videolan.vlc\">VLC Player (Android)</a></b>\n\n<i>ボタンをクリックしてストリームURLをコピーし、VLCアプリに貼り付けてください</i>"
    AA_ERROR_GETTING_LINK_MSG = "❌ <b>リンクの取得中にエラーが発生しました:</b>\n{error_msg}"
    AA_ERROR_SENDING_FORMATS_MSG = "❌ フォーマットファイルの送信中にエラーが発生しました: {error}"
    AA_FAILED_GET_FORMATS_MSG = "❌ フォーマットの取得に失敗しました:\n<code>{output}</code>"
    AA_PROCESSING_WAIT_MSG = "🔎 分析中... (6秒待機)"
    AA_PROCESSING_MSG = "🔎 分析中..."
    AA_TAG_FORBIDDEN_CHARS_MSG = "❌ タグ#{wrong}には禁止文字が含まれています。文字、数字、_のみが許可されています。\n使用してください: {example}"
    
    # Helper limitter messages
    HELPER_ADMIN_RIGHTS_REQUIRED_MSG = "❗️ グループで作業するには、ボットに管理者権限が必要です。このグループの管理者にボットを作成してください。"
    
    # URL extractor messages
    URL_EXTRACTOR_WELCOME_MSG = "こんにちは、{first_name}さん\n \n<i>このボット🤖は、どんなビデオでも電報に直接ダウンロードできます。😊 詳細については、<b>/help</b></i> 👈を押してください\n\n<blockquote>追伸 🔞NSFWコンテンツと☁️クラウドストレージからのファイルのダウンロードは有料です！ 1⭐️ = $0.02</blockquote>\n<blockquote>追伸 ‼️ チャンネルを離れないでください - ボットの使用が禁止されます ⛔️</blockquote>\n \n {credits}"
    URL_EXTRACTOR_NO_FILES_TO_REMOVE_MSG = "🗑 削除するファイルがありません。"
    URL_EXTRACTOR_ALL_FILES_REMOVED_MSG = "🗑 すべてのファイルが正常に削除されました！\n\n削除されたファイル:\n{files_list}"
    
    # Video extractor messages
    VIDEO_EXTRACTOR_WAIT_DOWNLOAD_MSG = "⏰ 前のダウンロードが完了するまでお待ちください"
    
    # Helper messages
    HELPER_APP_INSTANCE_NONE_MSG = "check_userのアプリインスタンスはNoneです"
    HELPER_CHECK_FILE_SIZE_LIMIT_INFO_DICT_NONE_MSG = "check_file_size_limit: info_dictはNoneです。ダウンロードを許可します"
    HELPER_CHECK_SUBS_LIMITS_INFO_DICT_NONE_MSG = "check_subs_limits: info_dictはNoneです。字幕の埋め込みを許可します"
    HELPER_CHECK_SUBS_LIMITS_CHECKING_LIMITS_MSG = "check_subs_limits: 制限を確認しています - max_quality={max_quality}p, max_duration={max_duration}s, max_size={max_size}MB"
    HELPER_CHECK_SUBS_LIMITS_INFO_DICT_KEYS_MSG = "check_subs_limits: info_dictキー: {keys}"
    HELPER_SUBTITLE_EMBEDDING_SKIPPED_DURATION_MSG = "字幕の埋め込みがスキップされました: 期間{duration}sが制限{max_duration}sを超えています"
    HELPER_SUBTITLE_EMBEDDING_SKIPPED_SIZE_MSG = "字幕の埋め込みがスキップされました: サイズ{size_mb:.2f}MBが制限{max_size}MBを超えています"
    HELPER_SUBTITLE_EMBEDDING_SKIPPED_QUALITY_MSG = "字幕の埋め込みがスキップされました: 品質{width}x{height} (最小辺{min_side}p)が制限{max_quality}pを超えています"
    HELPER_COMMAND_TYPE_TIKTOK_MSG = "TikTok"
    HELPER_COMMAND_TYPE_INSTAGRAM_MSG = "Instagram"
    HELPER_COMMAND_TYPE_PLAYLIST_MSG = "プレイリスト"
    HELPER_RANGE_LIMIT_EXCEEDED_MSG = "❗️ {service}の範囲制限を超えました: {count} (最大{max_count})。\n\n利用可能な最大数のファイルをダウンロードするには、次のいずれかのコマンドを使用してください:\n\n<code>{suggested_command_url_format}</code>\n\n"
    HELPER_RANGE_LIMIT_EXCEEDED_LOG_MSG = "❗️ {service}の範囲制限を超えました: {count} (最大{max_count})\nユーザーID: {user_id}"
    
    # Handler registry messages
    
    # Download status messages
    
    # POT helper messages
    HELPER_POT_PROVIDER_DISABLED_MSG = "設定でPOトークンプロバイダーが無効になっています"
    HELPER_POT_URL_NOT_YOUTUBE_MSG = "URL {url}はYouTubeドメインではないため、POトークンをスキップします"
    HELPER_POT_PROVIDER_NOT_AVAILABLE_MSG = "POトークンプロバイダーが{base_url}で利用できません。標準のYouTube抽出にフォールバックします"
    HELPER_POT_PROVIDER_CACHE_CLEARED_MSG = "POトークンプロバイダーのキャッシュがクリアされました。次のリクエストで可用性を確認します"
    HELPER_POT_GENERIC_ARGS_MSG = "generic:impersonate=chrome,youtubetab:skip=authcheck"
    
    # Safe messenger messages
    HELPER_APP_INSTANCE_NOT_AVAILABLE_MSG = "アプリインスタンスはまだ利用できません"
    HELPER_USER_NAME_MSG = "ユーザー"
    HELPER_FLOOD_WAIT_DETECTED_SLEEPING_MSG = "フラッド待機が検出されました。{wait_seconds}秒間スリープします"
    HELPER_FLOOD_WAIT_DETECTED_COULDNT_EXTRACT_MSG = "フラッド待機が検出されましたが、時間を抽出できませんでした。{retry_delay}秒間スリープします"
    HELPER_MSG_SEQNO_ERROR_DETECTED_MSG = "msg_seqnoエラーが検出されました。{retry_delay}秒間スリープします"
    HELPER_MESSAGE_ID_INVALID_MSG = "MESSAGE_ID_INVALID"
    HELPER_MESSAGE_DELETE_FORBIDDEN_MSG = "MESSAGE_DELETE_FORBIDDEN"
    
    # Proxy helper messages
    HELPER_PROXY_CONFIG_INCOMPLETE_MSG = "プロキシ設定が不完全なため、直接接続を使用します"
    HELPER_PROXY_COOKIE_PATH_MSG = "users/{user_id}/cookie.txt"
    
    # URL extractor messages
    URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG = "🔚閉じる"
    URL_EXTRACTOR_ADD_GROUP_CLOSE_BUTTON_MSG = "🔚閉じる"
    URL_EXTRACTOR_COOKIE_ARGS_YOUTUBE_MSG = "youtube"
    URL_EXTRACTOR_COOKIE_ARGS_TIKTOK_MSG = "tiktok"
    URL_EXTRACTOR_COOKIE_ARGS_INSTAGRAM_MSG = "instagram"
    URL_EXTRACTOR_COOKIE_ARGS_TWITTER_MSG = "twitter"
    URL_EXTRACTOR_COOKIE_ARGS_CUSTOM_MSG = "custom"
    URL_EXTRACTOR_SAVE_AS_COOKIE_HINT_CLOSE_BUTTON_MSG = "🔚閉じる"
    URL_EXTRACTOR_CLEAN_LOGS_FILE_REMOVED_MSG = "🗑 ログファイルを削除しました。"
    URL_EXTRACTOR_CLEAN_TAGS_FILE_REMOVED_MSG = "🗑 タグファイルを削除しました。"
    URL_EXTRACTOR_CLEAN_FORMAT_FILE_REMOVED_MSG = "🗑 フォーマットファイルを削除しました。"
    URL_EXTRACTOR_CLEAN_SPLIT_FILE_REMOVED_MSG = "🗑 分割ファイルを削除しました。"
    URL_EXTRACTOR_CLEAN_MEDIAINFO_FILE_REMOVED_MSG = "🗑 メディア情報ファイルを削除しました。"
    URL_EXTRACTOR_CLEAN_SUBS_SETTINGS_REMOVED_MSG = "🗑 字幕設定を削除しました。"
    URL_EXTRACTOR_CLEAN_KEYBOARD_SETTINGS_REMOVED_MSG = "🗑 キーボード設定を削除しました。"
    URL_EXTRACTOR_CLEAN_ARGS_SETTINGS_REMOVED_MSG = "🗑 引数設定を削除しました。"
    URL_EXTRACTOR_CLEAN_NSFW_SETTINGS_REMOVED_MSG = "🗑 NSFW設定を削除しました。"
    URL_EXTRACTOR_CLEAN_PROXY_SETTINGS_REMOVED_MSG = "🗑 プロキシ設定を削除しました。"
    URL_EXTRACTOR_CLEAN_FLOOD_WAIT_SETTINGS_REMOVED_MSG = "🗑 フラッド待機設定を削除しました。"
    URL_EXTRACTOR_VID_HELP_CLOSE_BUTTON_MSG = "🔚閉じる"
    URL_EXTRACTOR_VID_HELP_TITLE_MSG = "🎬 ビデオダウンロードコマンド"
    URL_EXTRACTOR_VID_HELP_USAGE_MSG = "使用法: <code>/vid URL</code>"
    URL_EXTRACTOR_VID_HELP_EXAMPLES_MSG = "例:"
    URL_EXTRACTOR_VID_HELP_EXAMPLE_1_MSG = "• <code>/vid 3-7 https://youtube.com/playlist?list=123abc</code> (直接順)\n• <code>/vid -3-7 https://youtube.com/playlist?list=123abc</code> (逆順)"