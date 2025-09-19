# AI Cruel - Twilio Notification System

## Overview

The AI Cruel deadline manager now includes a comprehensive notification system that can send SMS and WhatsApp messages via Twilio. This system provides deadline reminders, daily summaries, and overdue alerts to help users stay on top of their deadlines.

## Features Implemented

### Core Notification Service

-   **TwilioNotificationService**: Complete service for sending SMS and WhatsApp notifications
-   **Multiple notification types**:
    -   Deadline reminders with countdown and urgency indicators
    -   Daily summaries of upcoming deadlines
    -   Overdue alerts for missed deadlines
    -   Custom notifications

### Database Models

-   **Notification**: Tracks all sent notifications with delivery status
-   **NotificationPreference**: User preferences for notification timing and methods
-   **Integration**: Proper relationships with User and Deadline models

### API Endpoints

All endpoints are available under `/api/notifications/`:

#### Sending Notifications

-   `POST /send` - Send custom notification
-   `POST /send-deadline-reminder` - Send deadline reminder
-   `POST /send-daily-summary` - Send daily summary of deadlines

#### Notification Management

-   `GET /` - List user's notifications (paginated)
-   `GET /stats` - Notification statistics and delivery rates
-   `GET /status/{message_sid}` - Check delivery status

#### User Preferences

-   `POST /preferences` - Create notification preferences
-   `GET /preferences` - Get user preferences
-   `PUT /preferences` - Update preferences
-   `DELETE /preferences` - Delete preferences

### Smart Features

#### Message Formatting

-   **Deadline reminders**: Include countdown, urgency indicators, and direct links
-   **Daily summaries**: Grouped by urgency (overdue, today, upcoming)
-   **Overdue alerts**: Clear indication of how many days overdue
-   **Emoji indicators**: Visual urgency indicators (🚨, ⏰, 📅)

#### User Preferences

-   **Notification timing**: Customizable reminder hours (24h, 4h, 1h before deadline)
-   **Quiet hours**: Configurable quiet periods to avoid late-night notifications
-   **Weekend notifications**: Optional weekend notification control
-   **Method selection**: Choose between SMS or WhatsApp
-   **Daily summaries**: Customizable daily summary timing

#### Delivery Tracking

-   **Status monitoring**: Track pending, sent, delivered, failed status
-   **Retry logic**: Built-in retry counting for failed deliveries
-   **Error handling**: Comprehensive error tracking and reporting

## Configuration

### Environment Variables

```bash
# Required for basic functionality
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_SMS_FROM=+1234567890

# Optional for WhatsApp support
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890
```

### Setup Instructions

1. **Get Twilio credentials**: Sign up at https://console.twilio.com/
2. **Configure phone numbers**: Set up SMS and optionally WhatsApp numbers
3. **Set environment variables**: Add credentials to your environment
4. **Test the service**: Use `test_notification_service.py` to verify setup

## Usage Examples

### Basic SMS Notification

```python
from app.services.notification_service import get_notification_service, NotificationType

service = get_notification_service()
result = await service.send_notification(
    phone_number="+1234567890",
    message="Your deadline is approaching!",
    notification_type=NotificationType.SMS
)
```

### Deadline Reminder

```python
result = await service.send_deadline_reminder(
    phone_number="+1234567890",
    deadline_title="Complete project proposal",
    deadline_date=datetime(2024, 1, 15, 17, 0),
    deadline_url="https://github.com/project/issues/123",
    priority="high"
)
```

### Daily Summary

```python
deadlines = [
    {
        'title': 'Review pull requests',
        'due_date': '2024-01-15T17:00:00',
        'priority': 'medium',
        'url': 'https://github.com/project/pulls'
    }
]

result = await service.send_daily_summary(
    phone_number="+1234567890",
    deadlines=deadlines
)
```

## API Examples

### Send Custom Notification

```bash
curl -X POST "/api/notifications/send" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "message": "Custom reminder message",
    "notification_type": "sms"
  }'
```

### Get User's Notification Preferences

```bash
curl -X GET "/api/notifications/preferences" \
  -H "Authorization: Bearer your_jwt_token"
```

### Update Notification Preferences

```bash
curl -X PUT "/api/notifications/preferences" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "preferred_method": "whatsapp",
    "daily_summary_enabled": true,
    "daily_summary_time": "09:00",
    "reminder_hours_before": "24,4,1",
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
  }'
```

## Testing

### Manual Testing

Use the provided test script:

```bash
cd backend
python test_notification_service.py
```

### Integration Testing

The notification system integrates seamlessly with the existing deadline and portal systems. When deadlines are scraped from GitHub, Jira, or Trello, users can receive automatic notifications based on their preferences.

## Security & Privacy

-   **Authentication required**: All endpoints require valid JWT tokens
-   **User isolation**: Users can only manage their own notifications and preferences
-   **Phone number validation**: Robust validation of phone number formats
-   **Error handling**: Secure error messages that don't leak sensitive information
-   **Rate limiting**: Twilio naturally rate-limits to prevent abuse

## Next Steps

The notification system is now ready for integration with:

1. **Task Scheduler**: Automated deadline checking and notification sending
2. **Frontend Dashboard**: User interface for managing preferences and viewing notification history
3. **Webhook Integration**: Real-time notification status updates from Twilio

## Production Considerations

-   **Monitoring**: Track delivery rates and failed notifications
-   **Cost management**: Monitor Twilio usage to control costs
-   **Scaling**: Consider message queuing for high-volume notifications
-   **Compliance**: Ensure compliance with SMS/messaging regulations in your jurisdiction
-   **User consent**: Implement proper opt-in/opt-out mechanisms

The notification system provides a solid foundation for keeping users informed about their deadlines through their preferred communication channels.
