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
以下は配布済みの 0.9.1 を使う例です。更新時は [Releases](https://github.com/REGALITECH/leeep-android-sdk/releases) の変更内容・移行手順を確認し、採用するバージョンへ変更してください。

```kotlin
dependencies {
    implementation("com.github.REGALITECH:leeep-android-sdk:0.9.1")
}
```

Gradle Sync 後、アプリのビルド・初期化・タグ表示・注文計測を確認してください。
[0.10.0 の変更内容と移行手順](releases/0.10.0.md)には新しい初期化 API と非推奨警告への対応を記載しています。リリースノートのファイルがあるだけでは配布確認・GitHub Release 公開済みを意味しません。

## 更新通知を受け取る

このリポジトリ右上の **Watch → Custom → Releases → Apply** を選択すると、GitHub Release の公開通知を購読できます。
メールで受け取る場合は、GitHub 個人設定の **Notifications** で Watching のメール通知と受信先を確認してください。
通知経路は各アカウントの設定に従います。タグの追加だけでは Release 通知にはなりません。

利用アプリで更新 PR を受け取りたい場合は、そのアプリのリポジトリに `.github/dependabot.yml` を設定します。次はルートに Gradle プロジェクトがある場合の例です。

```yaml
version: 2
updates:
  - package-ecosystem: gradle
    directory: "/"
    schedule:
      interval: weekly
    allow:
      - dependency-name: "com.github.REGALITECH:leeep-android-sdk"
```

`directory` は利用アプリの Gradle プロジェクトの場所に合わせてください。既存の Dependabot 設定があれば、その `updates` に統合し、同じ ecosystem/directory の設定を重複させないでください。既に他の依存も更新している場合、この `allow` で対象を SDK だけに絞らないよう既存の方針を維持してください。
SDK 配布元に設定するだけでは利用アプリに更新 PR は届きません。Gradle の JitPack 設定と、対象バージョンが JitPack の Maven メタデータに反映されていることが必要です。PR の作成時期はチェックのスケジュールや cooldown 設定にも従います。自動マージは設定せず、変更内容を確認してから更新してください。

参考: [GitHub の通知設定](https://docs.github.com/en/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/configuring-notifications)、[Dependabot 設定](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)、[JitPack の導入](https://docs.jitpack.io/intro/)。

## リリース担当者向け手順

1. 内部リポジトリで SDK を検証・ビルドし、既存の `make all` で AAR・依存 POM・ライセンス文書を公開リポジトリへ反映します。
2. 公開リポジトリに `releases/x.y.z.md` を作成します。先頭は `# x.y.z` とし、`## 変更内容` と `## 更新時の対応` に、そのバージョンの変更と必要な移行・確認事項を書きます。API の追加・非推奨・互換性への影響を含め、配布物と一緒に PR でレビューします。
3. PR をマージ後、確認した公開コミットに `x.y.z` 形式のタグを付けて push します（`v` 接頭辞・プレリリース・先頭ゼロは使いません）。タグの push は配布開始と Release 公開を許可する操作です。
4. **Actions → Publish release** の成功と [Releases](https://github.com/REGALITECH/leeep-android-sdk/releases) の内容を確認します。この workflow が GitHub Release を公開し、購読者への通知の起点になります。

`Publish release` はタグの実在・変更履歴を確認し、JitPack の POM 取得によって必要ならビルドを開始します。最大 12 分間、ビルド成功と対象コミット、POM の座標・バージョン、AAR の完全一致と同梱ライセンス、Maven メタデータへのバージョン掲載を確認します。いずれかが確認できなければ Release を公開しません。検証ジョブは読取権限で動き、公開ジョブだけが `contents: write` を使います。

以前から存在するタグ（workflow 導入前の 0.10.0 など）や検証失敗後の再試行は、**Actions → Publish release → Run workflow** で `main` を選び、`tag` にその既存タグを指定します。これは JitPack 配布確認と Release 公開を実行する操作です。workflow と変更履歴は実行時の `main` のコミットから取得し、AAR・文書はタグのコミットに固定して検証するので、旧タグを付け直す必要はありません。

既存のタグ・公開済み Release は変更しません。同じタグに Release（draft を含む）があれば停止します。JitPack 障害やメタデータ反映待ちは状況を確認してから同じタグで再実行し、配布物の修正が必要な場合は新しいバージョンを作成してください。タグの強制更新・削除や公開済み AAR の差し替えは行いません。

PR の `Release checks` はネットワークや公開を伴わないリリースゲートのテストだけを実行します。既に JitPack で配布済みの版を手元で確認する場合は `python3 scripts/release.py verify-jitpack 0.9.1` を使えます。このコマンドも未配布の版を指定すると JitPack ビルドを開始し得るため、公開承認のないバージョンには実行しないでください。

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
