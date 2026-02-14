#!/bin/bash

# release_apk.sh
# Automates the process of building a release APK for Android

KEYSTORE_PATH="android/app/upload-keystore.jks"
KEY_PROPS="android/key.properties"
ALIAS="upload"
PASS="password123"

echo "🚀 Starting Release Build Process..."

# 1. Check for Keytool
if ! command -v keytool &> /dev/null; then
    echo "⚠️ Warning: 'keytool' not found. If you already have a keystore, this is fine."
    # We continue, maybe the user has one or flutter can handle it? No, flutter needs it. 
    # But let's warn.
else
    echo "✅ Keytool found."
fi

# 2. Check for Flutter
if ! command -v flutter &> /dev/null; then
    echo "❌ Error: 'flutter' is not installed or not in PATH."
    exit 1
fi

# 3. Generate Keystore if missing
if [ ! -f "$KEYSTORE_PATH" ]; then
    if command -v keytool &> /dev/null; then
        echo "🔑 Generating new keystore at $KEYSTORE_PATH..."
        keytool -genkey -v -keystore $KEYSTORE_PATH \
            -keyalg RSA -keysize 2048 -validity 10000 \
            -alias $ALIAS \
            -storepass $PASS -keypass $PASS \
            -dname "CN=Talaba Hamkor, OU=IT, O=TalabaHamkor, L=Tashkent, S=Tashkent, C=UZ"
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to generate keystore."
            exit 1
        fi
        echo "✅ Keystore generated."
    else
        echo "❌ Keystore missing and 'keytool' not found. Cannot proceed."
        exit 1
    fi
else
    echo "✅ Keystore already exists."
fi

# 4. Create key.properties
echo "📄 Configuring $KEY_PROPS..."
cat > $KEY_PROPS <<EOL
storePassword=$PASS
keyPassword=$PASS
keyAlias=$ALIAS
storeFile=app/upload-keystore.jks
EOL
echo "✅ key.properties created."

# 5. GENERATE ASSETS (Icons & Splash)
echo "🎨 Generating App Icons & Splash Screen..."
echo "   Running: flutter pub get"
flutter pub get

echo "   Running: flutter_launcher_icons"
dart run flutter_launcher_icons

echo "   Running: flutter_native_splash"
dart run flutter_native_splash:create

# 6. Build APK
echo "🔨 Building Release APK..."
flutter build apk --release

if [ $? -eq 0 ]; then
    echo "✅ Build Successful!"
    echo "📂 APK Location: build/app/outputs/flutter-apk/app-release.apk"
else
    echo "❌ Build Failed."
    exit 1
fi
