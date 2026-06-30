plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace   = "com.theserverlab.eppviewer"
    compileSdk  = 34

    defaultConfig {
        applicationId   = "com.theserverlab.eppviewer"
        minSdk          = 26          // Android 8.0 — ~95% of devices
        targetSdk       = 34
        versionCode     = 13
        versionName     = "1.3.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled  = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    // Core AndroidX
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")

    // Material Design (toolbar, progress bar, dialogs)
    implementation("com.google.android.material:material:1.11.0")

    // CoordinatorLayout (for AppBarLayout + scrolling behaviour)
    implementation("androidx.coordinatorlayout:coordinatorlayout:1.2.0")

    // Standard test deps (optional — safe to leave in)
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
