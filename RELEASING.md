# リリース担当者向け手順

SDK 利用者向けの導入・更新方法は [README](README.md) を参照してください。

## 手順

1. 内部リポジトリで SDK を検証・ビルドし、既存の `make all` で AAR・依存 POM・ライセンス文書を公開リポジトリへ反映します。
2. 公開リポジトリに `releases/x.y.z.md` を作成します。先頭は `# x.y.z` とし、`## 変更内容` と `## 更新時の対応` に、そのバージョンの変更と必要な移行・確認事項を書きます。API の追加・非推奨・互換性への影響を含め、配布物と一緒に PR でレビューします。PR の `Release checks` が、ノートの形式と AAR へのライセンス文書の同梱をテストし、その PR の AAR を使った最小アプリのリリースビルド（R8 を含む）を確認します。成功してからマージします。
3. PR をマージ後、確認した公開コミットに `x.y.z` 形式のタグを付けて push します（`v` 接頭辞・プレリリース・先頭ゼロは使いません）。タグの push は配布開始と Release 公開を許可する操作です。タグは1つずつ push します。一度に4つ以上のタグを push すると GitHub がイベントを作らず、workflow が起動しません。
4. **Actions → Publish release** の成功と [Releases](https://github.com/REGALITECH/leeep-android-sdk/releases) の内容を確認します。この workflow が GitHub Release を公開し、購読者への通知の起点になります。

`Publish release` はタグの実在・変更履歴を確認し、JitPack の POM 取得によって必要ならビルドを開始します。最大 12 分間、ビルド成功と対象コミット、POM の座標・バージョンとタグにある依存定義との一致、AAR の完全一致と同梱ライセンス、Maven メタデータへのバージョン掲載を確認します。続けて、JitPack から取得したそのバージョンで最小アプリのリリースビルドを行います。いずれかが確認できなければ Release を公開しません。検証ジョブは読取権限で動き、公開ジョブだけが `contents: write` を使います。

以前から存在するタグ（workflow 導入前の 0.10.0 など）や検証失敗後の再試行は、**Actions → Publish release → Run workflow** で `main` を選び、`tag` にその既存タグを指定します。これは JitPack 配布確認と Release 公開を実行する操作です。workflow と変更履歴は実行時の `main` のコミットから取得し、AAR・文書はタグのコミットに固定して検証するので、旧タグを付け直す必要はありません。

既存のタグ・公開済み Release は変更しません。公開ジョブで Release 一覧を全ページ確認し、同じタグの draft があれば手動での確認を求めて停止します。同じタグの公開済み Release がある場合は、検証だけを行い、公開ジョブは `Release x.y.z is already published; leaving it unchanged.` を出して何も変更せずに成功します。公開ジョブは順番に実行し、初回または公開済みの正式版（`x.y.z` 形式）より新しい場合だけ Latest に設定します。旧版の告知補完では Latest を変更しません。タグの強制更新・削除や公開済み AAR の差し替えは行いません。

PR の `Release checks` は JitPack のビルドを開始せず、Release も公開しません。最小アプリのビルドは2回行います。1回目は、その PR の AAR を一時的なローカルの Maven リポジトリへ公開して取り込みます（JitPack と同じ `publishToMavenLocal`）。2回目は、JitPack でビルド済みの公開版（現時点では `0.10.0`）を取り込み、タグ push 後と同じ取得経路を確かめます。手元で同じ確認を行うには、JDK 17 と Android SDK（`ANDROID_HOME`）を用意して `scripts/validate-consumer.sh --local` または `scripts/validate-consumer.sh 0.10.0` を実行します。後者は JitPack でビルドに成功していない版を拒否します。

既に JitPack で配布済みの版を手元で確認する場合は `python3 scripts/release.py verify-jitpack 0.9.1` を使えます。このコマンドは未配布の版を指定すると JitPack ビルドを開始し得るため、公開承認のないバージョンには実行しないでください。

この workflow や `scripts/release.py`・`scripts/validate-consumer.sh` を変更して `main` にマージした後は、**Run workflow** から `main` と公開済みの最新タグを指定して実行します。公開ジョブが Summary に `Release x.y.z is already published; leaving it unchanged.` を出して成功すれば、次のリリース前に公開までの経路が動くことを確認できます。既存の Release は変更されません。

## JitPack の検証に失敗したとき

`Publish release` のログに出た原因で対応を分けます。いずれの場合もタグは付け直しません。

- **メタデータの反映待ち・JitPack の一時的な応答エラー**: 12 分待っても確認できなかった場合です。JitPack の状態を確認してから、同じタグで **Run workflow** を再実行します。
- **JitPack のビルド失敗**: `JitPack build failed` と表示され、待機せずに止まります。JitPack は失敗したビルド結果を保持するため、そのまま再実行しても再ビルドされません。表示された `build.log`（`https://jitpack.io/com/github/REGALITECH/leeep-android-sdk/<tag>/build.log`）で原因を確認します。
  - 依存の取得失敗など JitPack 側の一時的な問題であれば、[jitpack.io](https://jitpack.io) に GitHub アカウントで Sign In し、`REGALITECH/leeep-android-sdk` を Look up して該当バージョンの失敗したビルドを削除します。その後、同じタグで **Run workflow** を再実行すると JitPack が再ビルドします（[JitPack のドキュメント](https://docs.jitpack.io/building/)）。
  - 配布物やビルド設定そのものに誤りがある場合は、修正したうえで新しいバージョンを作成します。
