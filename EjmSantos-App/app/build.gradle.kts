plugins {
    alias(libs.plugins.android.application)
}

val ejmApiBaseUrl = providers.gradleProperty("EJM_API_BASE_URL")
    .orElse("https://ejm-santos-site-1.onrender.com/")
    .get()
val ejmSupportWhatsApp = providers.gradleProperty("EJM_SUPPORT_WHATSAPP")
    .orElse("")
    .get()
val ejmSupportEmail = providers.gradleProperty("EJM_SUPPORT_EMAIL")
    .orElse("contato@ejmsantos.com")
    .get()

android {
    namespace = "com.example.ejmsantos"
    compileSdk {
        version = release(36)
    }

    defaultConfig {
        applicationId = "com.example.ejmsantos"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "API_BASE_URL", "\"$ejmApiBaseUrl\"")
        buildConfigField("String", "SUPPORT_WHATSAPP", "\"$ejmSupportWhatsApp\"")
        buildConfigField("String", "SUPPORT_EMAIL", "\"$ejmSupportEmail\"")
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.activity)
    implementation(libs.constraintlayout)
    implementation(libs.stripe.android)
    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
}
