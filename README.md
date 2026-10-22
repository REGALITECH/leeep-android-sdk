# LEEEP Android SDK

## 導入と更新

JitPack で `com.github.REGALITECH:leeep-android-sdk` を配布しています。
`settings.gradle.kts` の既存のリポジトリ設定に JitPack を追加してください。

```kotlin
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
}
```

利用するモジュールの `build.gradle.kts` に、固定したバージョンを指定します。
`x.y.z` には [Releases の Latest](https://github.com/REGALITECH/leeep-android-sdk/releases/latest) のバージョンを指定してください。

```kotlin
dependencies {
    implementation("com.github.REGALITECH:leeep-android-sdk:x.y.z")
}
```

Gradle Sync 後、アプリのビルド・初期化・タグ表示・注文計測を確認してください。
更新時は [Releases](https://github.com/REGALITECH/leeep-android-sdk/releases) で、現在のバージョンから採用するバージョンまでの各版の変更内容・更新時の対応を確認してください。リポジトリの `releases/` にあるファイルは公開前の原稿を含むため、ファイルがあるだけでは配布確認・GitHub Release 公開済みを意味しません。

## 更新通知を受け取る

### Release の通知メール

次の設定をすると、GitHub Release が公開されたときに、変更内容と更新時の対応がメールで届きます。

1. このリポジトリ右上の **Watch → Custom → Releases → Apply** を選択します。
2. GitHub の[通知設定](https://github.com/settings/notifications)の **Watching** で、通知先（Notify me）に **Email** が含まれていることを確認します。
   **On GitHub** だけの場合は GitHub 上の通知だけになり、メールは届きません。
3. 同じ画面の **Default notifications email** が、受け取りたいメールアドレスになっていることを確認します。
   組織ごとに送信先を変えている場合は、**Custom routing** の設定も確認してください。

通知の届き方は各アカウントの設定に従います。タグの追加だけでは Release の通知にはなりません。

### Dependabot の更新 PR

利用アプリで更新 PR を受け取りたい場合は、そのアプリのリポジトリのデフォルトブランチに `.github/dependabot.yml` を設定します。次はルートに Gradle プロジェクトがある場合の例です。

```yaml
version: 2
updates:
  - package-ecosystem: gradle
    directory: "/"
    schedule:
      interval: daily
    allow:
      - dependency-name: "com.github.REGALITECH:leeep-android-sdk"
    cooldown:
      default-days: 3
      exclude:
        - "com.github.REGALITECH:leeep-android-sdk"
```

`directory` は利用アプリの Gradle プロジェクトの場所に合わせてください。既存の Dependabot 設定があれば、その `updates` に統合し、同じ ecosystem/directory の設定を重複させないでください。既に他の依存も更新している場合、この `allow` で対象を SDK だけに絞らないよう既存の方針を維持してください。
この公開 SDK の取得に、専用の PAT や Dependabot 用の認証情報は不要です。
JitPack の版には公開日時がなく、Dependabot の標準の 3 日間の cooldown では更新候補から除外される場合があります。上の例は `cooldown.exclude` でこの SDK だけを待機対象から外します。既存設定へ統合するときは、他の依存向けの日数や例外を維持し、SDK の除外だけを追加してください。[cooldown の公式仕様](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#cooldown)も参照してください。
SDK 配布元に設定するだけでは利用アプリに更新 PR は届きません。利用アプリの Gradle に JitPack を設定してください。Dependabot は Maven メタデータ以外のバージョン一覧も調べるため、メタデータ未反映・GitHub Release 未公開のタグが候補になる場合があります。PR の作成時期はチェックのスケジュールにも従います。自動マージは設定せず、Release の変更内容を読み、対象版が配布済みであることを確認してから更新してください。

参考: [GitHub の通知設定](https://docs.github.com/en/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/configuring-notifications)、[Dependabot 設定](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)、[JitPack の導入](https://docs.jitpack.io/intro/)。

## リリース担当者向け手順

SDK の配布と GitHub Release の公開手順は [RELEASING.md](RELEASING.md) にまとめています。

## ライセンス情報

SDK本体の利用条件は[LICENSE](LICENSE)、第三者ソフトウェアの情報は
[THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)を参照してください。
両文書はAARの`assets/leeep/licenses/`にも同梱しています。

アプリのライセンス情報画面には両文書を手動で掲載できます。
実行時には`context.assets.open("leeep/licenses/LICENSE")`および
`context.assets.open("leeep/licenses/THIRD_PARTY_NOTICES.txt")`で取得できます。

配布用POMにも商用ライセンスの名称・URLを記載します。
JitPackではビルド対象コミットのLICENSEを参照するため、公開後に本文が変わっても
過去の成果物が参照する文面は変わりません。ローカルビルドで`GIT_COMMIT`が未指定の場合は`main`を参照します。
独自のライセンスを認識できない抽出ツールでは、上記文書を手動で取り込んでください。
第三者通知に記載する依存のバージョンはSDK単体で解決したものなので、
アプリ側の最終的な依存関係とも照合してください。

## 配布メタデータ

`sdk-dependencies.pom`はSDK本体のビルドから生成した依存定義です。
このファイルの依存関係だけを配布用POMへ取り込み、識別情報・ライセンス情報は
`build.gradle.kts`で設定します。SDK本体のリリース手順でAAR・文書と一緒に更新します。
