plugins {
    id("maven-publish")
}

group = "com.github.REGALITECH"
version = "0.0.2"

publishing {
    publications {
        create<MavenPublication>("mavenJava") {
            from(components["release"])
            artifactId = "leeep-android-sdk"
            pom {
                name.set("LeeepSDK")
                description.set("LEEEP SDK for Android")
                url.set("https://github.com/REGALITECH/leeep-android-sdk")
            }
        }
    }
}

