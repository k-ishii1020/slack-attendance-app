# Slack Attendance Bot
Slack Attendance Botは、Slack上で出退勤や休憩の通知を任意のチャンネルへ投稿するアプリです。

![](/assets/1.png)

## 機能 
- 出勤、退勤、休憩の開始、終了をSlackの任意のチャンネルへ投稿。  
  会社やチームの文化によって２つの投稿タイプの選択が可能。
  - チャンネルへ直接投稿するタイプ（例:勤怠専用チャンネル）
  - 特定のスレッド内に投稿するタイプ（例:チームチャンネルの勤怠スレッド）
- Botとしてではなく、ユーザとして投稿するため、`from:@ユーザ名`で検索が可能。
- 出退勤時にプロフィールのステータス絵文字を変更（🏢🏠💤）
- 投稿する際のメッセージは個人ごとに変更可能。

## 必要な環境
- Docker Composeが使用できるサーバ（PythonとMySQLを使用します）
- ユーザトークンを取得するOAuth認証を行うために、アクセス可能なドメインを持っていること。
- Slackアプリを作成するための権限を持っていること。

## 本アプリ導入に必要な前提知識
- Slackのアプリの作成方法
- Slackのユーザトークン、アプリトークンの違いの理解
- Docker Composeの基本的な使い方

## 技術的な補足
- Slackとの通信はWebsocketを使用
- データベースはMySQLを使用し、ユーザトークンは暗号化して保存

## 制約事項
- 勤怠連絡を特定のスレッド内に投稿するタイプを使用する場合、パブリックチャンネルのみ対応しています。  
プライベートチャンネルやDMにはあえて対応していません。（詳細は後述）

## 初回セットアップ
```shell
# 本リポジトリのクローン
git clone https://github.com/k-ishii1020/slack-attendance-app.git
cd slack-attendance-app
cp .env.sample .env
# 任意のエディタで.envで空欄になっている箇所を修正（Slackアプリ周りの詳細は後述）
nano .env

# 必要に応じで、config.yamlの内容を修正
nano config.yaml
```

## Slackアプリの作成
1. https://api.slack.com/apps → From a Manifestを選択し、app_manifest.yamlの内容を参考にアプリを作成
1. Basic Information → App CredentialsのClient ID、Client Secret、Signing Secretを.envのSLACK_APP_CLIENT_ID、SLACK_APP_CLIENT_SECRET、SLACK_APP_SIGNING_SECRETに設定。
1. Basic Information → App-Level Tokensを作成し、.envのSLACK_APP_APP_TOKENに設定。Scopeは `connections:write`です。
1. OAuth & Permissions → OAuth TokensのInstall to {ワークスペース名} でトークンを生成。Bot User OAuth Tokenを.envのSLACK_APP_BOT_TOKENに設定。
1. Basic Information → Display Informationを適当に設定

### Docker関連の操作
```shell
### 起動
docker compose up -d
### 停止
docker compose stop
### コンテナ削除
docker compose down
### .envを修正したりGit最新化を行った場合
docker compose down && docker compose up -d --build
```

## Slackユーザトークンの取得の際の権限について
本Slackアプリでは、ユーザトークンに以下の権限が必要です。  
なお、データベースはSlackアプリ管理者が用意した環境に保存されるため、当然ながらSlackアプリ制作者にデータが送信されることは一切ありません。
- `chat:write` :ユーザとしてメッセージを投稿するため
- `users.profile:read` :ユーザのプロフィール情報を取得するため
- `users.profile:write` :ユーザのプロフィール情報を変更するため
- `channels:history`　: スレッド投稿タイプを使用する際に、該当のスレッドを検索するため
- `channels:read` : チャンネルの一覧情報を取得するため

※  なお、`groups:history, im:history, mpim:history`についてはあえて付与していません。  
ユーザトークンを入手したSlackアプリ管理者が、DMやプライベートチャンネルのメッセージを取得することを防ぐためです。

## 開発方針について
本アプリは以下の方針に基づいて開発しています。
- 機能追加の要望やバグ報告はIssueやPull Requestで受け付けています。
- Slackアプリを使用する企業であれば、どの組織でも汎用的に利用できることを目指しています。  
  そのため、特定の組織でしか使えない機能は実装しません。


## 注意事項・免責事項
- 本アプリを使用したことによるいかなる損害に対しても、制作者は一切の責任を負いません。
- 本アプリは、使用者（本リポジトリをクローンした人）がセットアップしたデータベース内にユーザトークンを暗号化して保存します。
  万が一ユーザトークンが漏洩した場合、Slackのメッセージなどを不正に利用される可能性がありますので十分に注意してください。
  また、各種トークンやシークレット情報の取り扱いには十分注意してください。
- 本アプリは、SlackのAPIを使用しています。そのため、SlackのAPIが変更された場合、本アプリの動作が保証されない可能性があります。
- 本アプリは、MITライセンスで公開されています。商用利用や改変、再配布が可能ですが、その際の責任は負いかねます。
- 寄付は大歓迎です！ぜひ[こちら](https://github.com/sponsors/k-ishii1020)からお願いします。