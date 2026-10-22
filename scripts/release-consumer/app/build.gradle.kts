import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "jp.leeep.releasesmoke"
    compileSdk = 35

    defaultConfig {
        applicationId = "jp.leeep.releasesmoke"
        // Same as the SDK. Raising the SDK's minSdk breaks customer apps, so the manifest merge fails here.
        minSdk = 21
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            // R8 fails on classes the SDK needs but its POM does not bring in.
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

dependencies {
    implementation("com.github.REGALITECH:leeep-android-sdk:${providers.gradleProperty("leeepSdkVersion").get()}")
}
