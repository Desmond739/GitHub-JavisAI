# Naya 2.1 RC2 early-access setup

## Preserve Google credentials

Copy your existing `credentials.json` into:

`backend\data\personal_data\google\credentials.json`

Run from the backend folder:

`authorize_google_read_only.py --authorize-read-only`

The browser will request separate read-only consent for Calendar, Gmail metadata
and Drive metadata. OAuth token files remain on the Windows computer.

## Temporary MTN MoMo

Run `backend\Configure_Early_Access.bat` and enter the payment number and account
name. Customers receive manual payment instructions. They must submit a transaction
reference, and an administrator must verify the payment before a plan activates.
This does not claim to be an MTN Collections merchant integration.

## Cloudflare R2

Create a private R2 bucket named `naya-private`, create an object read/write API
token restricted to that bucket, then run `backend\Configure_Early_Access.bat`.
Naya encrypts every object locally with AES-256-GCM before upload. The generated
encryption key stays in `backend\.env`; losing it makes cloud objects unreadable.

## Android early access

1. Install Android Studio with Android SDK 35 and JDK 17.
2. Open the `android` folder and allow Gradle synchronization.
3. Run `backend\Start_MoneroAI_Mobile.bat` on a trusted private network.
4. Allow Windows Firewall private-network access if prompted.
5. Build and install the Android debug app.
6. Enter the private pairing URL displayed on the PC.

Never share the pairing URL, `.env`, OAuth tokens, R2 keys or Android keystore.
