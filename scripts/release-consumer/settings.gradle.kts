// Minimal customer app built by scripts/validate-consumer.sh. The SDK is resolved through its POM
// like a customer app: from the local Maven repository (--local) or from JitPack (x.y.z).
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

val sdkRepository = providers.gradleProperty("leeepSdkRepository").get()

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        when (sdkRepository) {
            // Only the SDK may come from the local repository; its dependencies resolve as for customers.
            "local" -> mavenLocal { content { includeGroup("com.github.REGALITECH") } }
            // Same declaration as the README asks customers to add.
            "jitpack" -> maven { url = uri("https://jitpack.io") }
            else -> error("Unknown SDK repository: $sdkRepository")
        }
    }
}

rootProject.name = "LeeepReleaseSmoke"
include(":app")
