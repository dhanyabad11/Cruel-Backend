# 🔔 Notification Settings - User Guide

## Overview

The notification settings feature allows users to configure how they want to receive deadline reminders through multiple channels:

-   **Email** - Receive reminders via email
-   **SMS** - Receive text message reminders
-   **WhatsApp** - Receive WhatsApp message reminders
-   **Push** - Receive browser push notifications

## How to Access Settings

1. **Navigation Menu**: Click on "Settings" in the top navigation bar
2. **Direct URL**: Visit `/settings/notifications` in your browser

## Features

### Contact Information

-   **Email Address**: Configure your email for email notifications
-   **Phone Number (SMS)**: Set your phone number for SMS reminders
-   **WhatsApp Number**: Set your WhatsApp number for WhatsApp reminders

### Phone Number Format

-   Accepts Indian phone numbers: `+91XXXXXXXXXX` or `XXXXXXXXXX`
-   Automatically formats to international format (`+91XXXXXXXXXX`)
-   Validates that numbers are valid Indian mobile numbers

### Notification Channels

Toggle each notification type on/off:

-   ✅ **Email Notifications** - Default: ON
-   📱 **SMS Notifications** - Default: OFF
-   💬 **WhatsApp Notifications** - Default: OFF
-   🔔 **Push Notifications** - Default: ON

### Reminder Timing

Choose when to receive reminders before deadlines:

-   1 Hour Before
-   6 Hours Before
-   **1 Day Before** (Default)
-   3 Days Before
-   1 Week Before

## Backend API Endpoints

### GET `/api/settings/notifications`

-   **Purpose**: Get user's current notification settings
-   **Auth**: Required (JWT token)
-   **Response**: Complete notification settings object

### PUT `/api/settings/notifications`

-   **Purpose**: Update notification settings
-   **Auth**: Required (JWT token)
-   **Body**: Notification settings data
-   **Response**: Updated settings object

### POST `/api/settings/notifications`

-   **Purpose**: Create or update notification settings
-   **Auth**: Required (JWT token)
-   **Body**: Notification settings data
-   **Response**: Settings object

### DELETE `/api/settings/notifications`

-   **Purpose**: Reset settings to defaults
-   **Auth**: Required (JWT token)
-   **Response**: Success message

## Database Schema

The notification settings are stored in the `notification_settings` table with:

```sql
- id (Primary Key)
- user_id (UUID, references auth.users)
- email (TEXT)
- phone_number (TEXT)
- whatsapp_number (TEXT)
- email_enabled (BOOLEAN, default: true)
- sms_enabled (BOOLEAN, default: false)
- whatsapp_enabled (BOOLEAN, default: false)
- push_enabled (BOOLEAN, default: true)
- reminder_frequency (TEXT, default: '1_day')
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## Security Features

-   **Row Level Security (RLS)**: Users can only access their own settings
-   **Authentication Required**: All endpoints require valid JWT token
-   **Input Validation**: Phone numbers and frequencies are validated
-   **Auto-creation**: Default settings created automatically for new users

## Usage Flow

1. **User navigates to Settings** → Loads current preferences
2. **User updates preferences** → Saves to database via API
3. **User gets deadline reminders** → System uses these preferences
4. **Notification service** → Sends reminders through enabled channels

## Integration with Notifications

The notification system will use these settings to:

-   Determine which channels to send reminders through
-   Use the correct contact information (email, phone, WhatsApp)
-   Send reminders at the preferred timing (1 hour, 1 day, etc.)
-   Skip disabled notification types

## Next Steps

To complete the integration:

1. **Run the SQL script** in Supabase to create the database table
2. **Update notification service** to read user preferences
3. **Test the settings page** to ensure it saves/loads correctly
4. **Configure Twilio** for SMS/WhatsApp with Indian numbers
5. **Test end-to-end** notification flow with user preferences
