# 🛌 寝落ち防止Discord Bot

指定したボイスチャンネル（VC）に滞在している時間をユーザーごとに計測し、設定した時間を経過したメンバーを自動的にVCから切断（キック）するDiscord Botです。

---

## ✨ 主な機能

* **個別タイマー管理**: VC入室時間をユーザーごとに個別に計測・管理します。
* **サーバーごとの独立設定**: サーバーごとに異なる切断時間や対象VCを設定・保存できます。
* **簡単コマンド管理**: コードを変更することなく、Discord内コマンドで即座に設定を変更可能です。

---

## 🎮 コマンド一覧

> ⚠️ コマンド接頭辞は `!` です。  
> ※ `!set_time`, `!add_channel`, `!remove_channel` の実行には**管理者権限（Administrator）**が必要です。

| コマンド | 入力例 | 説明 | 権限 |
| :--- | :--- | :--- | :--- |
| **`!sleepy`** | `!sleepy` | コマンドヘルプ（使い方一覧）を埋め込みパネルで表示します。 | 全ユーザー |
| **`!status`**<br>*(alias: `!config`)* | `!status` | 現在の**自動切断待機時間**と**対象VC一覧**を確認します。 | 全ユーザー |
| **`!set_time <分数>`** | `!set_time 60` | 自動切断までの時間を「分」単位で設定します。 | **管理者のみ** |
| **`!add_channel <VC名>`** | `!add_channel 寝落ち部屋` | 自動切断の対象とするボイスチャンネルを追加します。 | **管理者のみ** |
| **`!remove_channel <VC名>`** | `!remove_channel 睡眠厨` | 自動切断の対象から指定したボイスチャンネルを削除します。 | **管理者のみ** |

---

## ⚙️ 必要なBot権限

* **Privileged Gateway Intents**:
  * `MESSAGE CONTENT INTENT`（メッセージ内容の取得）
  * `SERVER MEMBERS INTENT`（メンバー情報の取得）
* **Bot Discord Permissions**:
  * `Move Members`（メンバーを移動・切断する権限）
  * `Send Messages` / `Embed Links`（メッセージ送信および埋め込み表示権限）

---

## 🚀 デプロイ環境（Render）

* **環境変数（Environment Variables）**:
  * `DISCORD_TOKEN`: Discord Developer Portalで取得したBotトークン
  * `PORT`: `10000`（Flaskサーバー受信用）
