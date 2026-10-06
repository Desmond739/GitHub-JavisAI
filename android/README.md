# Naya Android

- Application ID: `cm.nexora.naya`
- Minimum Android: 8.0 (API 26)
- Target/compile SDK: 35
- Java: 17

Open this `android` folder in Android Studio. The first launch accepts either
the private pairing URL printed by `backend\Start_MoneroAI_Mobile.bat` or a
deployed HTTPS URL for phone-independent use.

Early-access LAN traffic is cleartext HTTP but every private API request requires
the random device token. Use it only on a trusted home network. Public release
must use HTTPS before Play Store submission. A signed app alone does not provide
cloud AI; deploy the backend and inference provider described in the root guide.

For release, generate an upload keystore in Android Studio, build an Android App
Bundle, then enroll in Google Play App Signing. Never add the keystore or its
password to this project.
