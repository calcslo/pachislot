import discord
from discord.ext import commands
import os
def Discord_file_upload(image_files):
    # ボットの設定
    intents = discord.Intents.default()
    intents.message_content = True  # メッセージの内容を取得できるようにする
    bot = commands.Bot(command_prefix="!", intents=intents)

    # ボットが起動したときに呼ばれるイベント
    @bot.event
    async def on_ready():
        print(f"{bot.user} has connected to Discord!")

        # 画像を送信するチャンネルを取得
        channel = bot.get_channel(1346542762379575359)  # ここにチャンネルIDを入れる
        if channel is None:
            print("エラー: チャンネルが見つかりません！")
            return

        print("画像アップロード処理開始")
        for image_path in image_files:
            try:
                await channel.send(file=discord.File(image_path))
                print(f"画像アップロード成功: {image_path}")
            except Exception as e:
                print(f"エラー発生: {e}")
        # 画像アップロードが終わったらBotを終了
        await bot.close()
        print("Botを終了しました")

    # ボットのトークン（Discordの開発者ポータルで取得）
    TOKEN = "XXXXXXXXXXXXXXXXXXXXXXX"

    bot.run(TOKEN)
#image_path = r"C:\Users\mikih\PycharmProjects\pythonProject\kakudaiborder_diff_chart_2025-03-05_batch_1.png"
#Discord_file_upload([image_path])