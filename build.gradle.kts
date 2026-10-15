import groovy.util.Node
import groovy.xml.XmlParser

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
                licenses {
                    license {
                        name.set("LEEEP SDK 商用ライセンス")
                        val licenseRef = project.version.toString().takeUnless { it == "unspecified" } ?: "main"
                        url.set("https://raw.githubusercontent.com/REGALITECH/leeep-android-sdk/$licenseRef/LICENSE")
                        distribution.set("repo")
                    }
                }
                developers {
                    developer {
                        name.set("株式会社REGALI")
                        organization.set("株式会社REGALI")
                        organizationUrl.set("https://regali.co.jp")
                    }
                }
                withXml {
                    // SDK本体から生成した依存定義を再利用する。
                    val sourcePom = XmlParser().parse(file("sdk-dependencies.pom"))
                    val dependencies = sourcePom.children().filterIsInstance<Node>().single {
                        it.name().toString().endsWith("dependencies")
                    }
                    asNode().append(dependencies)
                }
            }
        }
    }
}

