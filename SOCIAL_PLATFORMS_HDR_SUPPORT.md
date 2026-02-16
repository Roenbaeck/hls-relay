# Social Platforms: HDR Support, API Availability, and Content Retention

This document provides an overview of major social and streaming platforms, focusing on:
- HDR (High Dynamic Range) content support for live streaming
- API availability for live streaming integration
- Content retention policies (how long videos are kept)

*Last updated: February 2026*

## Platform Comparison Summary

| Platform | HDR Support | Live Streaming API | Content Retention (Live) | Notes |
|----------|-------------|-------------------|-------------------------|--------|
| **YouTube** | ✅ Full Support | ✅ Yes | Indefinite | Best mainstream option for HDR streaming |
| **Twitch** | ⚠️ Partial | ✅ Yes | 14-60 days | HDR available for select high-end creators |
| **Facebook Live** | ⚠️ Limited | ✅ Yes | 30 days | Auto-deletes after 30 days (as of Feb 2025) |
| **Instagram Live** | ❌ No | ❌ No Public API | Indefinite (if saved) | Must save as Video/Reels to keep |
| **TikTok Live** | ❌ No | ⚠️ Limited | Indefinite | API focused on content, not live streaming |
| **LinkedIn Live** | ❌ No | ✅ Yes | Varies | Professional/business focus |
| **X (Twitter)** | ❌ No | ⚠️ Limited | Varies | No dedicated live API |
| **Reddit Live** | ❌ No | ❌ No | N/A | No public live streaming API |

---

## Detailed Platform Information

### YouTube Live

**HDR Support:** ✅ **Full Support**
- Supports HDR10 and HLG formats for live streaming
- Best mainstream platform for HDR content as of 2026
- Requires HDR-capable encoding setup and viewer devices

**API:** ✅ **Yes - YouTube Live Streaming API**
- [Official Documentation](https://developers.google.com/youtube/v3/live/docs)
- Features: Create, update, manage broadcasts, handle live chat, transition stream states
- Authentication: OAuth 2.0
- Supports both HLS and RTMP ingestion

**Content Retention:**
- **Live Videos:** Indefinite (unless manually deleted)
- **After Account Deletion:** 180 days before permanent removal

**Best For:** High-quality HDR streaming, long-term content preservation, gaming, and professional broadcasting

---

### Twitch

**HDR Support:** ⚠️ **Partial Support**
- HDR available for select regions and high-end creators
- Primarily focused on gaming and eSports where visual quality matters
- Implementation depends on streamer setup and viewer device compatibility

**API:** ✅ **Yes - Twitch API**
- [Official Documentation](https://dev.twitch.tv/api/)
- Features: Stream management, clips, chat moderation, EventSub webhooks, scheduling
- Authentication: OAuth 2.0
- RTMP ingestion for live streams

**Content Retention:**
- **Standard Users:** 14 days for past broadcasts
- **Partners/Prime/Turbo:** 60 days for past broadcasts
- **After Account Deletion:** 90 days

**Best For:** Gaming streams, interactive community engagement, real-time chat integration

---

### Facebook Live

**HDR Support:** ⚠️ **Limited**
- Supports 1080p live streams with high color accuracy
- Native HDR support for consumers is limited or experimental
- Focus on broad device compatibility over HDR

**API:** ✅ **Yes - Facebook Live Video API**
- [Official Documentation](https://developers.facebook.com/docs/videos/live-video-api)
- Features: Start/end broadcasts, get stream URLs, crosspost to Pages, manage comments
- Authentication: OAuth 2.0
- Requires Facebook Developer account

**Content Retention:**
- **Live Videos:** 30 days auto-deletion (policy updated February 19, 2025)
- Users receive notifications before deletion
- Can convert to Reels (permanent) or download/transfer to cloud storage
- Can postpone deletion up to 6 months
- **After Account Deletion:** 180 days (Meta retention policy)

**Best For:** Social engagement, community building, business/brand presence

---

### Instagram Live

**HDR Support:** ❌ **Not Supported**
- No HDR support for live streaming
- Standard dynamic range only

**API:** ❌ **No Public Live Streaming API**
- Instagram API focuses on content management and analytics
- Live streaming only available through mobile app
- Some third-party services attempt workarounds but may violate ToS

**Content Retention:**
- **Live Videos:** Can be saved to profile as Video posts or Reels (indefinite)
- **Stories:** 24 hours (can save as Highlights)
- **After Account Deletion:** 180 days (Meta retention policy)

**Best For:** Mobile-first content, Stories integration, visual storytelling

---

### TikTok Live

**HDR Support:** ❌ **Not Supported**
- No mainstream support for HDR live streaming
- Focus on accessibility and broad device support
- Standard 720p/1080p quality

**API:** ⚠️ **Limited - TikTok for Developers**
- [Official Documentation](https://developers.tiktok.com/doc/tiktok-api-v2-introduction/)
- Primarily for content management and user data
- OAuth 2.0 authentication
- Live streaming features not widely exposed through API

**Content Retention:**
- **Regular Videos:** Indefinite (user-managed)
- **Maximum Video Length:** Up to 1 hour for uploads (10 minutes for in-app recordings)
- **After Account Deletion:** 30 days before permanent removal

**Best For:** Short-form content, viral trends, younger demographics

---

### LinkedIn Live

**HDR Support:** ❌ **Not Supported**
- No explicit HDR support in developer documentation
- RTMP ingest with standard dynamic range
- Focus on event management over advanced video features

**API:** ✅ **Yes - LinkedIn Live Events API**
- [Official Documentation](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/live-video/)
- Features: Register, manage, ingest, and end live events
- Authentication: OAuth 2.0
- Supports member and company page streams
- Recommends professional broadcasting tools (StreamYard, Restream, OBS)

**Content Retention:**
- Varies by user settings
- Videos can be kept on profile indefinitely if saved

**Best For:** Professional networking, B2B content, corporate events, webinars

---

### X (formerly Twitter)

**HDR Support:** ❌ **Not Supported**
- No developer documentation or evidence of HDR streaming support
- Focus on stable, low-latency SDR streams
- Mobile and browser-based streaming priority

**API:** ⚠️ **Limited**
- No dedicated live streaming API like other platforms
- X Media Studio and legacy Periscope Producer RTMP ingest available
- Standard video upload APIs for recorded content

**Content Retention:**
- Varies by content type and user settings
- Live replays available if saved by user

**Best For:** Real-time news, quick updates, text-first engagement with video supplement

---

### Reddit Live (RPAN)

**HDR Support:** ❌ **Not Supported**
- No HDR support for live video streams
- Mobile-first UGC video platform processes streams in SDR

**API:** ❌ **No Public Live Streaming API**
- No official API for direct live streaming ingestion
- Live video facilitated by platform itself
- No external RTMP or API integrations documented

**Content Retention:**
- Depends on subreddit and user actions
- No standardized retention policy for live streams

**Best For:** Community-driven content, niche interests, AMAs (Ask Me Anything)

---

## Enterprise & White-Label Solutions

For production environments requiring guaranteed HDR support, consider professional streaming platforms:

- **Vimeo Livestream**: Enterprise-grade with 4K and HDR support
- **Wowza**: Custom streaming server with full control over formats
- **AWS IVS (Interactive Video Service)**: Scalable with HDR capability
- **Mux**: Modern video infrastructure with HDR support
- **Brightcove**: Enterprise video platform with advanced features
- **VPlayed**: White-label streaming solution with HDR options

These platforms offer:
- Full control over video encoding and formats
- HDR support end-to-end (ingest, transcode, delivery)
- Custom branding and integration
- Better suited for professional broadcasting needs

---

## HDR Streaming Requirements

To successfully stream in HDR, you need:

1. **Camera/Source**: HDR-capable recording device
2. **Encoder**: Software/hardware that supports HDR encoding (e.g., OBS with HDR settings, specialized hardware encoders)
3. **Platform**: Service with HDR support (currently YouTube is the best mainstream option)
4. **Viewer Device**: HDR-compatible display for playback

**Note**: Even on HDR-supported platforms, viewers without HDR displays will see SDR (tone-mapped) versions.

---

## Recommendations by Use Case

### For HDR Content Creators
- **Primary Choice**: YouTube Live (full HDR support, indefinite storage)
- **Gaming**: YouTube or Twitch (if eligible for HDR program)
- **Professional/Enterprise**: Dedicated platforms like Vimeo, Mux, or AWS IVS

### For Multi-Platform Streaming
- Use tools like Restream, StreamYard, or custom RTMP relays
- Note: Most multi-streaming tools will downgrade HDR to SDR for compatibility

### For Social Engagement
- Facebook Live or Instagram for Meta ecosystem
- TikTok for viral/trending content
- LinkedIn for B2B and professional content

### For Long-Term Archival
- YouTube (indefinite storage)
- Download and store locally or in cloud storage
- Avoid Twitch (14-60 day limit) unless you export regularly

---

## Important Notes

1. **HDR Support is Rare**: As of 2026, YouTube is the only major social platform with robust HDR live streaming support.

2. **Content Retention Varies Widely**: 
   - Twitch: 14-60 days (shortest)
   - Facebook Live: 30 days for live content
   - YouTube: Indefinite (longest)

3. **API Availability**: Most platforms have APIs, but Instagram and Reddit notably lack public live streaming APIs.

4. **Account Deletion Grace Periods**: Most platforms retain data for 30-180 days after account deletion.

5. **Platform Policies Change**: Always verify current policies with official documentation before building integrations.

6. **OBS HDR Note**: When using OBS to pull HLS streams (passive mode), HDR10 base layer is preserved but Dolby Vision dynamic metadata is dropped.

---

## Additional Resources

- [YouTube Live Streaming API](https://developers.google.com/youtube/v3/live/docs)
- [Twitch API Documentation](https://dev.twitch.tv/api/)
- [Facebook Live Video API](https://developers.facebook.com/docs/videos/live-video-api)
- [LinkedIn Live Events API](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/live-video/)
- [TikTok for Developers](https://developers.tiktok.com/)

---

*This document is intended as a starting point for finding new streaming targets. Platform capabilities and policies may change over time. Always consult official documentation for the most current information.*
