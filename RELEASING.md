# リリース担当者向け手順

SDK 利用者向けの導入・更新方法は [README](README.md) を参照してください。

## 手順

1. 内部リポジトリで SDK を検証・ビルドし、既存の `make all` で AAR・依存 POM・ライセンス文書を公開リポジトリへ反映します。
2. 公開リポジトリに `releases/x.y.z.md` を作成します。先頭は `# x.y.z` とし、`## 変更内容` と `## 更新時の対応` に、そのバージョンの変更と必要な移行・確認事項を書きます。API の追加・非推奨・互換性への影響を含め、配布物と一緒に PR でレビューします。
3. PR をマージ後、確認した公開コミットに `x.y.z` 形式のタグを付けて push します（`v` 接頭辞・プレリリース・先頭ゼロは使いません）。タグの push は配布開始と Release 公開を許可する操作です。
4. **Actions → Publish release** の成功と [Releases](https://github.com/REGALITECH/leeep-android-sdk/releases) の内容を確認します。この workflow が GitHub Release を公開し、購読者への通知の起点になります。

`Publish release` はタグの実在・変更履歴を確認し、JitPack の POM 取得によって必要ならビルドを開始します。最大 12 分間、ビルド成功と対象コミット、POM の座標・バージョンとタグにある依存定義との一致、AAR の完全一致と同梱ライセンス、Maven メタデータへのバージョン掲載を確認します。いずれかが確認できなければ Release を公開しません。検証ジョブは読取権限で動き、公開ジョブだけが `contents: write` を使います。

以前から存在するタグ（workflow 導入前の 0.10.0 など）や検証失敗後の再試行は、**Actions → Publish release → Run workflow** で `main` を選び、`tag` にその既存タグを指定します。これは JitPack 配布確認と Release 公開を実行する操作です。workflow と変更履歴は実行時の `main` のコミットから取得し、AAR・文書はタグのコミットに固定して検証するので、旧タグを付け直す必要はありません。

既存のタグ・公開済み Release は変更しません。公開ジョブで Release 一覧を全ページ確認し、同じタグの Release（draft を含む）があれば停止します。公開ジョブは順番に実行し、初回または公開済みの正式版（`x.y.z` 形式）より新しい場合だけ Latest に設定します。旧版の告知補完では Latest を変更しません。タグの強制更新・削除や公開済み AAR の差し替えは行いません。

PR の `Release checks` はネットワークや公開を伴わないリリースゲートのテストだけを実行します。既に JitPack で配布済みの版を手元で確認する場合は `python3 scripts/release.py verify-jitpack 0.9.1` を使えます。このコマンドも未配布の版を指定すると JitPack ビルドを開始し得るため、公開承認のないバージョンには実行しないでください。

## JitPack の検証に失敗したとき

`Publish release` のログに出た原因で対応を分けます。いずれの場合もタグは付け直しません。

- **メタデータの反映待ち・JitPack の一時的な応答エラー**: 12 分待っても確認できなかった場合です。JitPack の状態を確認してから、同じタグで **Run workflow** を再実行します。
- **JitPack のビルド失敗**: `JitPack build failed` と表示され、待機せずに止まります。JitPack は失敗したビルド結果を保持するため、そのまま再実行しても再ビルドされません。表示された `build.log`（`https://jitpack.io/com/github/REGALITECH/leeep-android-sdk/<tag>/build.log`）で原因を確認します。
  - 依存の取得失敗など JitPack 側の一時的な問題であれば、[jitpack.io](https://jitpack.io) に GitHub アカウントで Sign In し、`REGALITECH/leeep-android-sdk` を Look up して該当バージョンの失敗したビルドを削除します。その後、同じタグで **Run workflow** を再実行すると JitPack が再ビルドします（[JitPack のドキュメント](https://docs.jitpack.io/building/)）。
  - 配布物やビルド設定そのものに誤りがある場合は、修正したうえで新しいバージョンを作成します。
