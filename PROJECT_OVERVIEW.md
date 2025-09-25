# 🏗️ BTI Bot - Project Overview

## 📋 Current Status
- **Status**: ✅ Working and deployed
- **Cloud Run Service**: `btibot` in `europe-west1`
- **URL**: https://btibot-637190449180.europe-west1.run.app
- **GitHub**: https://github.com/Sergalmazfas/Bti-bot
- **Stable Tag**: `stable-working-20250925`

## 🏛️ Architecture

### Core Components
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Cloud Run      │    │   Database      │
│   Bot API       │◄──►│   (btibot)       │◄──►│   SQLite3       │
│                 │    │   europe-west1   │    │   zamerprobti.db│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   External APIs │
                       │   - Registry API │
                       │   - SERP API     │
                       │   - OpenAI API   │
                       └──────────────────┘
```

### File Structure
```
bti-bot-clean/
├── main.py              # Core bot logic (974 lines)
├── app.py               # Flask webhook entry point
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── zamerprobti.db      # SQLite database
└── docs/
    ├── JUNIOR_CHECKLIST_BTI_BOT.md
    ├── DEPLOYMENT_CHECKLIST.md
    ├── TESTING_PLAN.md
    └── SERP_ARCHITECTURE.md
```

## 🔧 Technical Stack

### Backend
- **Language**: Python 3.12
- **Framework**: Flask (webhook), python-telegram-bot
- **Database**: SQLite3 (local file)
- **Server**: Gunicorn (WSGI)

### Cloud Infrastructure
- **Platform**: Google Cloud Run
- **Container Registry**: gcr.io/talkhint/btibot
- **Secrets**: Google Secret Manager
- **Logging**: Google Cloud Logging

### External APIs
- **Telegram Bot API**: User interactions
- **Registry API**: Cadastral data lookup
- **SERP API**: Market pricing data
- **OpenAI API**: AI processing (optional)

## 🚀 Deployment Process

### Single Command Deploy
```bash
docker buildx build --platform linux/amd64 -t gcr.io/talkhint/btibot:latest . && \
docker push gcr.io/talkhint/btibot:latest && \
gcloud run deploy btibot \
  --image gcr.io/talkhint/btibot:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest"
```

### Webhook Configuration
```bash
# Set webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=https://btibot-637190449180.europe-west1.run.app/"

# Verify webhook
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

## 📊 Current Features

### ✅ Working Features
1. **Telegram Bot Interface**
   - `/start` command
   - Message handling
   - Callback query processing
   - Error handling

2. **Database Operations**
   - SQLite3 integration
   - Coefficient management
   - Competitor data storage
   - Pricing strategies

3. **Cloud Run Integration**
   - Health check endpoint
   - Webhook processing
   - Async message handling
   - Structured logging

### 🔄 In Development
1. **Registry Integration**
   - Cadastral number lookup
   - Property data extraction
   - Address validation

2. **SERP API Integration**
   - Market price analysis
   - Competitor comparison
   - Median calculations

3. **Pricing Engine**
   - Multi-factor pricing
   - Coefficient application
   - Market adjustment

## 🎯 Next Steps for Junior Developer

### Phase 1: Registry Integration
```python
# registry_client.py
def get_registry_data(cadastral_number: str) -> dict:
    """
    Fetch property data from registry API
    Returns: area_m2, address, object_type, cadastral_value, lat, lon
    """
    pass
```

### Phase 2: SERP Integration
```python
# serp_client.py
def get_market_data(lat: float, lon: float) -> dict:
    """
    Fetch market pricing from SERP API
    Returns: average_price, median_price, sample_size
    """
    pass
```

### Phase 3: Pricing Engine
```python
# pricing_engine.py
def calculate_prices(registry_data: dict, market_data: dict) -> dict:
    """
    Calculate three pricing models:
    - Technical passport (official)
    - Measurements (adjusted)
    - Specification (market-based)
    """
    pass
```

## 🔍 Monitoring & Debugging

### Health Checks
```bash
# Service health
curl -s https://btibot-637190449180.europe-west1.run.app/health

# Webhook status
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

### Logging
```bash
# Recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot" --limit=20

# Error logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot AND severity>=ERROR" --limit=10
```

### Testing
```bash
# Valid Telegram payload test
curl -X POST "https://btibot-637190449180.europe-west1.run.app/" \
  -H "Content-Type: application/json" \
  -d '{"update_id":100000001,"message":{"message_id":1,"date":1727240000,"chat":{"id":123456789,"type":"private"},"from":{"id":123456789,"is_bot":false,"first_name":"Test"},"text":"/start"}}'
```

## 📚 Documentation

### For Junior Developer
- `JUNIOR_CHECKLIST_BTI_BOT.md` - Step-by-step restoration guide
- `DEPLOYMENT_CHECKLIST.md` - Quick deployment reference
- `TESTING_PLAN.md` - Comprehensive testing strategy
- `SERP_ARCHITECTURE.md` - SERP integration architecture

### Key Commands
```bash
# Deploy
docker buildx build --platform linux/amd64 -t gcr.io/talkhint/btibot:latest . && docker push gcr.io/talkhint/btibot:latest && gcloud run deploy btibot --image gcr.io/talkhint/btibot:latest --region europe-west1 --platform managed --allow-unauthenticated --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest"

# Webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=https://btibot-637190449180.europe-west1.run.app/"

# Health
curl -s https://btibot-637190449180.europe-west1.run.app/health

# Logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=btibot" --limit=20
```

## 🎯 Success Criteria

### Current Status ✅
- [x] Bot responds to `/start` command
- [x] Health check returns `{"status":"ok"}`
- [x] Webhook properly configured
- [x] No critical errors in logs
- [x] Deployed to Cloud Run
- [x] Code committed to GitHub

### Next Milestones
- [ ] Registry API integration
- [ ] SERP API integration  
- [ ] Pricing calculations
- [ ] End-to-end testing
- [ ] Production monitoring

## 🚨 Troubleshooting

### Common Issues
1. **'date' error**: Use valid Telegram payload format
2. **Webhook errors**: Check URL and token
3. **Deployment failures**: Verify secrets in Secret Manager
4. **Database errors**: Check SQLite file permissions

### Quick Fixes
```bash
# Reset webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook"
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=https://btibot-637190449180.europe-west1.run.app/"

# Redeploy
docker buildx build --no-cache --platform linux/amd64 -t gcr.io/talkhint/btibot:latest . && docker push gcr.io/talkhint/btibot:latest && gcloud run deploy btibot --image gcr.io/talkhint/btibot:latest --region europe-west1 --platform managed --allow-unauthenticated --set-secrets="BOT_TOKEN=BOT_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,REESTR_API_TOKEN=REESTR_API_TOKEN:latest,SERPRIVER_API_KEY=SERPRIVER_API_KEY:latest"
```

---
**Last Updated**: 2025-09-25  
**Version**: stable-working-20250925  
**Status**: ✅ Production Ready
