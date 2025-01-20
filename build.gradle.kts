plugins {
    id("maven-publish")
}

group = "com.github.REGALITECH"

publishing {
    publications {
        create<MavenPublication>("aarPublication") {
            from(components["release"])
            artifactId = "leeep-android-sdk"
            artifact(file("LeeepAndroidSdk.aar"))
            pom {
                name.set("LeeepSDK")
                description.set("LEEEP SDK for Android")
                url.set("https://github.com/REGALITECH/leeep-android-sdk")
            }
        }
    }
}

