plugins {
    id("maven-publish")
}

group = "com.github.REGALITECH"

publishing {
    publications {
        create<MavenPublication>("aarPublication") {
            artifactId = "leeep-android-sdk"
            artifact(file("LeeepAndroidSdk.aar"))
            pom {
                name.set("LeeepSDK")
                description.set("LEEEP SDK for Android")
                url.set("https://github.com/REGALITECH/leeep-android-sdk")
                withXml {
                    // AARを手書きPOMで配布しているため、利用側へ推移的に渡す依存はここが唯一の宣言箇所。
                    // 宣言漏れがあると、利用側は該当機能を呼んだ時点でNoClassDefFoundErrorになる。
                    // バージョンはSDK本体がFirebase BoM 34.16.0で解決している値と揃えること。
                    asNode().appendNode("dependencies").apply {
                        fun dependency(groupId: String, artifactId: String, version: String) {
                            appendNode("dependency").apply {
                                appendNode("groupId", groupId)
                                appendNode("artifactId", artifactId)
                                appendNode("version", version)
                                appendNode("scope", "compile")
                            }
                        }

                        dependency("org.jetbrains.kotlinx", "kotlinx-serialization-json", "1.7.3")
                        dependency("com.google.firebase", "firebase-messaging", "25.1.1")
                        dependency("com.google.firebase", "firebase-installations", "19.1.2")
                    }
                }
            }
        }
    }
}
