# LEEEP Android SDK

## ライセンス情報

SDK本体の利用条件は[LICENSE](LICENSE)、第三者ソフトウェアの情報は
[THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)を参照してください。
両文書はAARの`assets/leeep/licenses/`にも同梱しています。

アプリのライセンス情報画面には両文書を手動で掲載できます。
実行時には`context.assets.open("leeep/licenses/LICENSE")`および
`context.assets.open("leeep/licenses/THIRD_PARTY_NOTICES.txt")`で取得できます。

配布用POMにも商用ライセンスの名称・URLを記載します。
独自のライセンスを認識できない抽出ツールでは、上記文書を手動で取り込んでください。
第三者通知に記載する依存のバージョンはSDK単体で解決したものなので、
アプリ側の最終的な依存関係とも照合してください。

## 配布メタデータ

`sdk-dependencies.pom`はSDK本体のビルドから生成した依存定義です。
このファイルの依存関係だけを配布用POMへ取り込み、識別情報・ライセンス情報は
`build.gradle.kts`で設定します。SDK本体のリリース手順でAAR・文書と一緒に更新します。
