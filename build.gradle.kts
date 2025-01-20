plugins {
    id("maven-publish")
}

group = "com.github.REGALITECH"

dependencies {
    api(libs.kotlinx.serialization.json)
    api(libs.androidx.runtime.android)
    api(libs.androidx.ui.android)
}

publishing {
    publications {
        create<MavenPublication>("aarPublication") {
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

