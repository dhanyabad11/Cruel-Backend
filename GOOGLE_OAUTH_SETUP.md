# Google OAuth Setup Guide

This guide explains how to enable Google authentication in your Cruel application.

## Prerequisites

-   Supabase project created
-   Google Cloud Console access

## Step 1: Configure Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen:
    - User Type: External
    - App name: Cruel
    - User support email: Your email
    - Developer contact: Your email
6. Create OAuth 2.0 Client ID:
    - Application type: **Web application**
    - Name: Cruel Web App
    - Authorized JavaScript origins:
        - `https://your-project-ref.supabase.co`
    - Authorized redirect URIs:
        - `https://your-project-ref.supabase.co/auth/v1/callback`
7. Save the **Client ID** and **Client Secret**

## Step 2: Configure Supabase

1. Go to your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **Authentication** → **Providers**
4. Find **Google** in the list of providers
5. Enable Google provider
6. Enter your Google **Client ID** and **Client Secret**
7. Set the **Redirect URL** (copy from Supabase):
    ```
    https://your-project-ref.supabase.co/auth/v1/callback
    ```
8. Click **Save**

## Step 3: Update Google Cloud Console Redirect URIs

1. Go back to Google Cloud Console
2. Update the OAuth 2.0 Client redirect URIs to match Supabase:
    ```
    https://your-project-ref.supabase.co/auth/v1/callback
    ```
3. Add your production domain redirects:
    ```
    https://cruel.vercel.app/auth/callback
    https://your-domain.com/auth/callback
    ```

## Step 4: Test the Integration

### Backend Endpoints

The backend now supports these Google OAuth endpoints:

1. **Get OAuth URL**

    ```bash
    POST http://198.211.106.97/api/auth/oauth/google
    Body: { "redirect_url": "http://localhost:3000/auth/callback" }
    ```

    Returns: `{ "url": "https://accounts.google.com/...", "provider": "google" }`

2. **Handle OAuth Callback**
    ```bash
    POST http://198.211.106.97/api/auth/oauth/callback
    Body: { "code": "authorization_code_from_google" }
    ```
    Returns user session with access token

### Frontend Usage

Users can now:

1. Click "Continue with Google" on login or register pages
2. Be redirected to Google sign-in
3. Grant permissions
4. Be redirected back to `/auth/callback`
5. Automatically logged in

## Step 5: Production Deployment

### Environment Variables

No additional environment variables needed - Google OAuth uses Supabase configuration.

### Vercel Deployment

The frontend is already configured with:

-   `/auth/callback` route for OAuth redirect
-   Google sign-in buttons on login and register pages
-   Automatic token handling

### Testing Flow

1. Visit your deployed app: `https://cruel.vercel.app/login`
2. Click "Continue with Google"
3. Sign in with Google
4. Should redirect to dashboard with user logged in

## Troubleshooting

### "redirect_uri_mismatch" Error

**Problem**: Google returns redirect URI mismatch error

**Solution**:

-   Ensure redirect URIs in Google Cloud Console exactly match Supabase callback URL
-   Include both Supabase domain and your production domain

### "Invalid OAuth State" Error

**Problem**: OAuth state parameter doesn't match

**Solution**:

-   Clear browser cookies and try again
-   Ensure your frontend and backend are using the same Supabase project

### User Not Created in Database

**Problem**: User signs in with Google but not in your users table

**Solution**:

-   Supabase automatically creates users in `auth.users`
-   Your app can access user data via JWT token
-   No manual user creation needed

### Full Name Not Showing

**Problem**: User's full name from Google not appearing

**Solution**:

-   Backend extracts `full_name` from `user_metadata`
-   Also checks `name` field as fallback
-   Ensure frontend extracts nested user object:
    ```typescript
    const user = response.data.user || response.data;
    ```

## API Endpoints Summary

### Backend (Digital Ocean)

```
POST http://198.211.106.97/api/auth/oauth/google
POST http://198.211.106.97/api/auth/oauth/callback
```

### Frontend (Vercel)

```
GET  https://cruel.vercel.app/login          # Google button
GET  https://cruel.vercel.app/register       # Google button
GET  https://cruel.vercel.app/auth/callback  # OAuth redirect
```

## User Data Structure

After Google OAuth sign-in, user object includes:

```typescript
{
  "id": "uuid",
  "email": "user@gmail.com",
  "email_confirmed": true,
  "full_name": "John Doe",  // From Google profile
  "avatar_url": "https://...",  // Google profile picture
  "created_at": "2025-10-22T...",
  "last_sign_in": "2025-10-22T...",
  "is_active": true
}
```

## Security Notes

1. **Client Secret**: Never expose in frontend code
2. **Redirect URIs**: Must be exact match (including https/http)
3. **Token Storage**: Access tokens stored in localStorage
4. **CORS**: API proxy handles HTTPS→HTTP for Digital Ocean backend

## Additional Providers

To add more OAuth providers (GitHub, Facebook, etc.):

1. Follow similar setup in Supabase dashboard
2. Backend already supports multiple providers
3. Update frontend to add provider-specific buttons
4. Use same callback handler (`/auth/callback`)

## Support

If you encounter issues:

1. Check Supabase logs: Dashboard → Logs
2. Check backend logs: `docker-compose logs -f`
3. Check browser console for frontend errors
4. Verify redirect URIs match exactly
