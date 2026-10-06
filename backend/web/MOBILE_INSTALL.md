# Naya mobile client

This is the installable mobile web client for MoneroAI 2.0 RC1.

For development, serve this folder over HTTPS and configure it to call the
owner's authenticated Naya API. For an Android release, wrap the same client in
a signed Trusted Web Activity or Capacitor shell after HTTPS hosting and device
pairing are ready.

The current Windows API listens only on `127.0.0.1`. This is intentional: do not
change it to `0.0.0.0` merely to reach it from a phone, because that would expose
private memory and task controls to the local network without authentication.

Required before public Android distribution:

1. Deploy the API behind HTTPS with owner accounts and device pairing.
2. Supply an Android application ID and signing keystore.
3. Build and sign the APK/AAB using Android Studio or CI.
4. Test notification, microphone, and wake-word permissions on a physical device.
