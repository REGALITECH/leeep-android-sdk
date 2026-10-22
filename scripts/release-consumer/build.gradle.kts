// AGP and Kotlin come from the SDK's version catalog (gradle/libs.versions.toml), which
// scripts/validate-consumer.sh copies next to this project, so the app follows the SDK toolchain.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
}
