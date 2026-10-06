plugins { id("com.android.application") }

android {
    namespace = "cm.nexora.naya"
    compileSdk = 35

    defaultConfig {
        applicationId = "cm.nexora.naya"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "3.0.0-beta1"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
