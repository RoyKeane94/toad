# Feedback Request Email System

## Overview
A complete email system to request feedback from Toad users, with a beautiful HTML email template and management command for sending.

## What's Included

### 1. **Email Template** 
`accounts/templates/accounts/email/beta_feedback_email.html`

A beautiful, mobile-responsive email that includes:
- Friendly request for feedback with link to feedback form
- Prominent "Share Your Feedback" button linking to `/crm/feedback/`
- Special section encouraging users to share Toad with the 3-month trial link
- Professional design matching Toad's branding

### 2. **Email Utility Function**
`accounts/email_utils.py` - `send_feedback_request_email(user)`

Handles:
- Checking if user is subscribed to emails
- Rendering both HTML and plain text versions
- Logging success/failures
- Subject line: "We'd love your thoughts on Toad 💭"

### 3. **Management Command**
`accounts/management/commands/send_feedback_request.py`

Easy-to-use command for sending emails in bulk or to specific users.

## Usage

### Send to All Subscribed Users
```bash
python manage.py send_feedback_request
```
This will:
- Find all active, verified, and subscribed users
- Ask for confirmation
- Send feedback request emails to all of them

### Send to Specific User(s)
```bash
# Single user
python manage.py send_feedback_request --email user@example.com

# Multiple users
python manage.py send_feedback_request --email user1@example.com --email user2@example.com
```

### Dry Run (Test Without Sending)
```bash
python manage.py send_feedback_request --dry-run
```
Shows exactly who would receive emails without actually sending them.

### Send to ALL Users (Including Unsubscribed)
```bash
python manage.py send_feedback_request --all-users
```
⚠️ **Warning**: This overrides email subscription preferences. Use with caution!

## From Python Code

You can also send feedback emails programmatically:

```python
from accounts.email_utils import send_feedback_request_email
from django.contrib.auth import get_user_model

User = get_user_model()

# Send to specific user
user = User.objects.get(email='user@example.com')
send_feedback_request_email(user)

# Send to multiple users
for user in User.objects.filter(email_subscribed=True):
    send_feedback_request_email(user)
```

## Email Content

### What Users See:
1. **Header**: "We'd Love Your Thoughts on Toad 💭"
2. **Personal greeting**: "Hi [First Name],"
3. **Request**: Brief explanation asking for 2-3 minutes of feedback
4. **CTA Button**: "Share Your Feedback" → Links to https://meettoad.co.uk/crm/feedback/
5. **Share Section**: Beautiful green box with the trial signup link
   - https://meettoad.co.uk/accounts/register/trial-3-month
   - Mentions 3-month free trial worth £6
6. **Closing**: Warm thank you from "The Toad Team"

### Plain Text Version
A clean, readable plain text version is automatically included for email clients that don't support HTML.

## Best Practices

### Timing
- Wait at least 1-2 weeks after user signup before requesting feedback
- Don't send more than once per quarter to the same user
- Consider sending after significant product updates

### Targeting
- Start with engaged users (those who've created multiple grids)
- Consider segmenting by user tier (free vs. paid)
- Always respect email subscription preferences

### Monitoring
All email sends are logged, check logs with:
```bash
# View email logs
tail -f logs/django.log | grep "feedback request"
```

## Troubleshooting

### No emails being sent?
1. Check `email_subscribed` status: `User.objects.filter(email_subscribed=True).count()`
2. Verify email settings in `settings.py`
3. Check email backend configuration

### Users not receiving emails?
1. Check spam folders
2. Verify email addresses are correct and verified
3. Check server email logs

### Need to test the email?
```bash
# Send to your own email first
python manage.py send_feedback_request --email your.email@example.com
```

## Links in the Email

### Feedback Form
- **URL**: https://meettoad.co.uk/crm/feedback/
- **Purpose**: Collect user feedback anonymously
- **Features**: Name optional, covers usage, organization methods, improvements, and sharing willingness

### Trial Signup Link  
- **URL**: https://meettoad.co.uk/accounts/register/trial-3-month
- **Purpose**: Allow users to share Toad with friends/colleagues
- **Offer**: 3-month free Personal account trial (£6 value)
- **Benefits**: Up to 10 active grids, custom templates, archives, priority support

## Future Enhancements

Consider adding:
- Scheduled sending (e.g., automatically 2 weeks after signup)
- A/B testing different email copy
- Tracking which users submitted feedback after receiving the email
- Personalized content based on user behavior
- Follow-up emails for non-responders

---

**Created**: October 2025  
**Author**: Toad Team  
**Questions?** Contact support@meettoad.co.uk

