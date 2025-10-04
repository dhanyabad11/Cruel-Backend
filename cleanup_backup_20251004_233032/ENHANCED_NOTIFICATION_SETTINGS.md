# 🔔 Enhanced Notification Settings - Complete User Guide

## Overview

The enhanced notification settings system allows users to configure **multiple reminder schedules** with **platform-specific preferences** for deadline notifications. Users can set up different reminders (e.g., 1 week before, 1 day before, 1 hour before) and choose which platforms to use for each reminder.

## Key Features

### 🕒 **Multiple Reminder Times**

Set up multiple reminders for each deadline:

-   **1 Hour Before** - Last minute urgent reminder
-   **6 Hours Before** - Same-day preparation reminder
-   **1 Day Before** - Final preparation reminder
-   **3 Days Before** - Early preparation reminder
-   **1 Week Before** - Advance planning reminder

### 📱 **Platform-Specific Configuration**

For each reminder time, choose which platforms to use:

-   **📧 Email** - Professional email notifications
-   **📱 SMS** - Instant text message alerts
-   **💬 WhatsApp** - WhatsApp message notifications
-   **🔔 Push** - Browser push notifications

### ✨ **Smart Configuration Examples**

**Example 1: Graduate Student**

-   **1 Week Before**: Email + Push (planning reminder)
-   **1 Day Before**: Email + SMS + WhatsApp (urgent reminder)
-   **1 Hour Before**: SMS + Push (final alert)

**Example 2: Working Professional**

-   **3 Days Before**: Email (advance notice)
-   **1 Day Before**: Email + WhatsApp (final reminder)

**Example 3: Heavy Mobile User**

-   **1 Week Before**: Push (lightweight reminder)
-   **1 Day Before**: SMS + WhatsApp + Push (multi-channel alert)

## User Interface

### Settings Page (`/settings/notifications`)

#### **Contact Information Section**

-   **Email Address**: Primary email for notifications
-   **Phone Number (SMS)**: Indian mobile number for SMS (+91XXXXXXXXXX)
-   **WhatsApp Number**: Indian mobile number for WhatsApp (+91XXXXXXXXXX)

#### **Global Channel Settings**

Master toggles for each notification type:

-   Enable/disable Email notifications globally
-   Enable/disable SMS notifications globally
-   Enable/disable WhatsApp notifications globally
-   Enable/disable Push notifications globally

#### **Reminder Schedule Section**

-   **Add Reminder**: Create new reminder configurations
-   **Remove Reminder**: Delete unwanted reminder setups
-   **Configure Each Reminder**:
    -   Select reminder timing (1 hour to 1 week before)
    -   Choose platforms for this specific reminder
    -   Platform checkboxes are independent for each reminder

### Example UI Flow:

1. **Add Reminder** → Choose "1 Week Before"
2. **Select Platforms** → Check Email + Push
3. **Add Another Reminder** → Choose "1 Day Before"
4. **Select Platforms** → Check SMS + WhatsApp + Push
5. **Save Settings** → Both reminders are saved

## Backend API Endpoints

### Main Settings Endpoints

-   **GET `/api/settings/notifications`** - Get settings + all reminders
-   **PUT `/api/settings/notifications`** - Update contact information
-   **DELETE `/api/settings/notifications`** - Reset to defaults

### Reminder Management Endpoints

-   **GET `/api/settings/reminders`** - Get all reminder configurations
-   **POST `/api/settings/reminders`** - Create/update single reminder
-   **PUT `/api/settings/reminders/bulk`** - Update all reminders at once
-   **DELETE `/api/settings/reminders/{time}`** - Delete specific reminder

### API Response Example:

```json
{
    "settings": {
        "email": "user@example.com",
        "phone_number": "+91XXXXXXXXXX",
        "whatsapp_number": "+91XXXXXXXXXX",
        "email_enabled": true,
        "sms_enabled": true,
        "whatsapp_enabled": true,
        "push_enabled": true
    },
    "reminders": [
        {
            "reminder_time": "1_week",
            "email_enabled": true,
            "sms_enabled": false,
            "whatsapp_enabled": false,
            "push_enabled": true
        },
        {
            "reminder_time": "1_day",
            "email_enabled": true,
            "sms_enabled": true,
            "whatsapp_enabled": true,
            "push_enabled": true
        },
        {
            "reminder_time": "1_hour",
            "email_enabled": false,
            "sms_enabled": true,
            "whatsapp_enabled": false,
            "push_enabled": true
        }
    ]
}
```

## Database Schema

### Enhanced Tables

#### `notification_settings` (Contact Info)

```sql
- id (Primary Key)
- user_id (UUID)
- email (TEXT)
- phone_number (TEXT)
- whatsapp_number (TEXT)
- email_enabled (BOOLEAN)
- sms_enabled (BOOLEAN)
- whatsapp_enabled (BOOLEAN)
- push_enabled (BOOLEAN)
```

#### `notification_reminders` (Multiple Reminder Configs)

```sql
- id (Primary Key)
- user_id (UUID)
- reminder_time (TEXT) -- '1_hour', '6_hours', '1_day', '3_days', '1_week'
- email_enabled (BOOLEAN)
- sms_enabled (BOOLEAN)
- whatsapp_enabled (BOOLEAN)
- push_enabled (BOOLEAN)
- UNIQUE(user_id, reminder_time)
```

## Setup Instructions

### 1. Database Setup

Run both SQL scripts in your Supabase SQL Editor:

```bash
# First, run the basic notification settings setup
cat notification_settings_setup.sql

# Then, run the enhanced reminders setup
cat enhanced_notification_settings_setup.sql
```

### 2. Backend Setup

The enhanced routes are already integrated. Restart your backend server:

```bash
cd backend && python main.py
```

### 3. Frontend Testing

Visit `/settings/notifications` to test the enhanced interface:

-   Add multiple reminders
-   Configure platform preferences for each
-   Save and verify settings persist

## Integration with Notification Service

### How the System Uses Settings

1. **Deadline Processing**: When a deadline approaches, the system:

    - Checks all reminder configurations for the user
    - Finds reminders matching the time difference
    - Sends notifications via enabled platforms for that reminder

2. **Multi-Channel Flow**:

    ```
    Deadline: Assignment due tomorrow at 11:59 PM
    Current time: Today 11:59 PM (24 hours before)

    → Find reminder_time = "1_day"
    → Check platforms: email=true, sms=true, whatsapp=false, push=true
    → Send via: Email + SMS + Push (skip WhatsApp)
    ```

3. **Validation Logic**:
    - Master toggles can disable entire channels
    - Reminder-specific settings work within enabled channels
    - Phone number required for SMS/WhatsApp
    - Email required for email notifications

## Benefits

### **For Power Users**

-   **Granular Control**: Different platforms for different urgency levels
-   **Flexible Scheduling**: Multiple reminder points
-   **Context Awareness**: Work hours vs. personal time preferences

### **For Casual Users**

-   **Simple Default**: One reminder via email + push
-   **Easy Expansion**: Add more reminders as needed
-   **Platform Choice**: Use preferred communication channels

### **For Mobile-First Users**

-   **Instant Alerts**: SMS + WhatsApp for urgent reminders
-   **Battery Friendly**: Email for advance planning
-   **Always Connected**: Push notifications for real-time updates

## Next Steps

1. **Run SQL Scripts** to create enhanced database tables
2. **Test Frontend** at `/settings/notifications`
3. **Configure Multiple Reminders** with different platform combinations
4. **Verify API Endpoints** work for reminder management
5. **Integrate with Deadline Service** to use enhanced settings

The enhanced notification settings provide unprecedented flexibility for deadline reminder management! 🚀
