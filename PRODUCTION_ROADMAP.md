# BudAlert Production Roadmap

**Version**: 1.0  
**Created**: 2026-03-05  
**Status**: Ready for Implementation  
**Timeline**: 4-8 weeks to full production

---

## Executive Summary

This roadmap translates completed research into a production-ready dispensary scraping system. All three target dispensaries (Gotham NYC, Housing Works, Conbud LES) have documented, tested scraping methods ready for deployment.

**Current State**: ✅ Research complete, methods validated, code written  
**Next State**: 🚀 Production system running, monitored, and scaling

**Key Milestones**:
- Week 1: First scraper in production (Gotham)
- Week 2: All 3 scrapers operational
- Week 3: API optimization complete
- Week 4: Monitoring and alerting live

---

## Table of Contents

1. [Week-by-Week Plan](#week-by-week-plan)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Cost Breakdown](#cost-breakdown)
4. [Success Criteria](#success-criteria)
5. [Risk Mitigation](#risk-mitigation)
6. [Deployment Options](#deployment-options)
7. [Scaling Strategy](#scaling-strategy)

---

## Week-by-Week Plan

### Week 1: Foundation & Quick Win

**Goal**: Deploy Gotham scraper to production and establish baseline infrastructure

#### Day 1-2: Environment Setup & Gotham Deployment

**Tasks**:
- [ ] Set up VPS or cloud account (AWS/GCP/DigitalOcean)
- [ ] Configure domain and DNS (optional but recommended)
- [ ] Install Docker on production server
- [ ] Deploy Gotham scraper (easiest path to production)
- [ ] Set up cron job for 6-hour intervals
- [ ] Verify first production scrape

**Deliverables**:
- Gotham scraper running automatically every 6 hours
- 150-300 products collected per run
- JSON output stored in organized directory structure
- Basic logging in place

**Technical Details**:
```bash
# Production setup commands
ssh user@production-server

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone repository
git clone https://github.com/your-org/budalert
cd budalert/research/phase5-gotham

# Build and test
docker-compose build
docker-compose up  # Test run

# Set up cron
crontab -e
# Add: 0 */6 * * * cd /home/user/budalert/research/phase5-gotham && docker-compose up
```

**Success Metrics**:
- ✅ Scraper runs without errors
- ✅ Data validates (all products have name + price)
- ✅ Output files saved to persistent storage
- ✅ <2% failure rate

**Time Investment**: 8-12 hours  
**Risk Level**: Low ⭐

---

#### Day 3-4: Data Storage & Housing Works Setup

**Tasks**:
- [ ] Set up PostgreSQL database (or Convex)
- [ ] Create product schema and tables
- [ ] Write Gotham data import script
- [ ] Deploy Housing Works Python scraper
- [ ] Test Housing Works on production server
- [ ] Schedule Housing Works scraper (daily)

**Deliverables**:
- Database schema created and tested
- Gotham data flowing into database
- Housing Works scraper deployed
- 200-400 products per Housing Works run

**Database Schema**:
```sql
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  dispensary VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  brand VARCHAR(100),
  category VARCHAR(50),
  price DECIMAL(10, 2),
  thc_value DECIMAL(5, 2),
  cbd_value DECIMAL(5, 2),
  quantity INTEGER,
  in_stock BOOLEAN,
  image_url TEXT,
  product_url TEXT,
  scraped_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(dispensary, name, scraped_at)
);

CREATE INDEX idx_dispensary ON products(dispensary);
CREATE INDEX idx_scraped_at ON products(scraped_at);
CREATE INDEX idx_category ON products(category);
```

**Alternative: Convex Setup**:
```bash
# Install Convex
npm install convex

# Initialize project
npx convex dev

# Deploy schema
npx convex deploy
```

**Success Metrics**:
- ✅ Database accessible and performant
- ✅ Gotham data importing successfully
- ✅ Housing Works scraper operational
- ✅ Data persists across scraper runs

**Time Investment**: 8-12 hours  
**Risk Level**: Low-Medium ⭐⭐

---

#### Day 5: Conbud Initial Deployment

**Tasks**:
- [ ] Deploy Conbud network intercept scraper
- [ ] Run scraper to capture GraphQL queries
- [ ] Handle CAPTCHA if present (manual first time)
- [ ] Extract and document GraphQL queries
- [ ] Verify Conbud data quality
- [ ] Schedule Conbud scraper (daily initially)

**Deliverables**:
- Conbud scraper deployed
- GraphQL queries captured and documented
- 100-300 products per Conbud run
- All 3 dispensaries operational

**CAPTCHA Handling**:
```javascript
// Run with manual intervention for CAPTCHA
const browser = await playwright.chromium.launch({
  headless: false,  // See browser window
  slowMo: 100       // Slow down for debugging
});

// Wait for manual CAPTCHA solving
await page.waitForTimeout(30000);  // 30 seconds
```

**Success Metrics**:
- ✅ Conbud scraper completes successfully
- ✅ GraphQL queries extracted
- ✅ Data includes variants and potency info
- ✅ CAPTCHA handling strategy documented

**Time Investment**: 6-10 hours  
**Risk Level**: Medium-High ⭐⭐⭐⭐

---

**Week 1 Summary**:
- ✅ 3 dispensaries in production
- ✅ 500-1000 products in database
- ✅ Automated scheduling configured
- ✅ Basic data pipeline operational

**Total Time**: 22-34 hours  
**Cost**: $0-50 (VPS + database)

---

### Week 2: Optimization & Reliability

**Goal**: Move from browser automation to direct API calls for 10x speed improvement

#### Day 6-7: API Discovery Phase

**Tasks**:
- [ ] Run Housing Works scraper with network logging
- [ ] Extract Blaze API endpoints from logs
- [ ] Run Conbud scraper with detailed request capture
- [ ] Document all discovered API endpoints
- [ ] Create API documentation file

**Deliverables**:
- Complete API endpoint catalog
- Request/response examples for each API
- Authentication requirements documented
- Rate limiting behavior observed

**API Discovery Process**:
```bash
# Run with network logging
cd phase4-housing-works
docker-compose up > housing-works-network.log 2>&1

# Extract API calls
cat output/housing-works-api-requests-*.json | jq '.[] | .url' | sort | uniq

# Document findings
cat > API_ENDPOINTS.md << 'EOF'
# Housing Works (Blaze)
- Products API: https://api.blaze.me/stores/housing-works/products
- Categories: https://api.blaze.me/menu/categories
- Inventory: https://api.blaze.me/inventory/check

# Conbud (Dutchie)
- GraphQL: https://api.dutchie.com/graphql
- Query: FilteredProducts
- Variables: { dispensaryId: "6430f42042cf3c004e37f0f8" }
EOF
```

**Success Metrics**:
- ✅ All API endpoints identified
- ✅ Authentication method documented
- ✅ Rate limits understood
- ✅ API documentation complete

**Time Investment**: 6-8 hours  
**Risk Level**: Low ⭐

---

#### Day 8-9: Direct API Implementation

**Tasks**:
- [ ] Implement Housing Works direct API scraper
- [ ] Implement Conbud direct GraphQL scraper
- [ ] A/B test: browser vs API methods
- [ ] Measure performance improvements
- [ ] Validate data quality matches browser method

**Deliverables**:
- Direct API scrapers for Housing Works and Conbud
- Performance comparison report
- Data validation showing 100% match
- Updated scrapers in production

**Performance Testing**:
```bash
# Browser method
time docker-compose run housing-works node scraper-playwright.js
# Expected: 30-60 seconds, 500-800 MB RAM

# API method
time docker-compose run housing-works node scraper-api-direct.js
# Expected: 2-5 seconds, 50-100 MB RAM

# Performance improvement: 10x faster, 8x less memory
```

**Success Metrics**:
- ✅ API scrapers 10x faster than browser
- ✅ Memory usage reduced 80%+
- ✅ Data quality maintained
- ✅ All tests passing

**Time Investment**: 10-14 hours  
**Risk Level**: Medium ⭐⭐⭐

---

#### Day 10: Error Handling & Fallbacks

**Tasks**:
- [ ] Implement retry logic with exponential backoff
- [ ] Create fallback: API → Browser → Alert
- [ ] Add error logging and categorization
- [ ] Set up basic alerting (email or Slack)
- [ ] Test failure scenarios

**Deliverables**:
- Robust error handling in all scrapers
- Fallback mechanisms tested
- Alert notifications configured
- Error documentation created

**Error Handling Implementation**:
```javascript
async function scrapeWithFallback(dispensary) {
  const methods = [
    { name: 'API', fn: scrapeViaAPI },
    { name: 'Browser', fn: scrapeViaBrowser },
  ];

  for (let i = 0; i < methods.length; i++) {
    const method = methods[i];
    
    for (let retry = 0; retry < 3; retry++) {
      try {
        console.log(`Attempting ${method.name} (retry ${retry + 1}/3)...`);
        const result = await method.fn(dispensary);
        
        if (result.products.length > 0) {
          return result;
        }
      } catch (error) {
        console.error(`${method.name} failed:`, error.message);
        
        if (retry < 2) {
          await sleep(Math.pow(2, retry) * 1000);
        }
      }
    }
  }

  // All methods failed
  await sendAlert(`All scraping methods failed for ${dispensary}`);
  throw new Error('Scraping failed');
}
```

**Success Metrics**:
- ✅ Scrapers retry on transient failures
- ✅ Browser fallback works when API fails
- ✅ Alerts sent on critical failures
- ✅ No data loss from temporary issues

**Time Investment**: 6-8 hours  
**Risk Level**: Low ⭐

---

**Week 2 Summary**:
- ✅ API optimization complete (10x faster)
- ✅ Robust error handling in place
- ✅ Fallback mechanisms tested
- ✅ Production system more reliable

**Total Time**: 22-30 hours  
**Cost**: $50-100 (VPS + database + monitoring)

---

### Week 3: Monitoring & Data Quality

**Goal**: Full observability and data enrichment

#### Day 11-12: Monitoring Dashboard

**Tasks**:
- [ ] Set up monitoring service (Grafana/Datadog/CloudWatch)
- [ ] Create metrics for each scraper
- [ ] Build monitoring dashboard
- [ ] Configure alerts for anomalies
- [ ] Set up log aggregation

**Deliverables**:
- Real-time monitoring dashboard
- Metrics tracked: product count, duration, errors
- Alerts for: count drops, failures, duration spikes
- Centralized logging

**Metrics to Track**:
```javascript
// Example metrics
const metrics = {
  // Per dispensary
  'products.gotham.count': 250,
  'products.housing_works.count': 380,
  'products.conbud.count': 180,
  
  // Performance
  'scrape.duration.gotham': 3.2,      // seconds
  'scrape.duration.housing_works': 5.8,
  'scrape.duration.conbud': 7.1,
  
  // Quality
  'scrape.success.gotham': 1,         // boolean
  'scrape.errors.housing_works': 0,
  
  // Data completeness
  'data.completeness.gotham': 0.75,   // percentage
  'data.with_thc.conbud': 0.90,
};

// Alert rules
const alerts = [
  {
    metric: 'products.*.count',
    condition: 'drops_by',
    threshold: 0.20,  // 20% drop
    action: 'slack_alert',
  },
  {
    metric: 'scrape.errors.*',
    condition: 'exceeds',
    threshold: 3,  // 3 consecutive failures
    action: 'email_alert',
  },
];
```

**Dashboard Layout**:
```
┌─────────────────────────────────────────────────┐
│  BudAlert Scraper Monitoring                    │
├─────────────────────────────────────────────────┤
│  Product Counts (Last 24h)                      │
│  📊 Gotham: 250 (↑ 5%)                          │
│  📊 Housing Works: 380 (→ 0%)                   │
│  📊 Conbud: 180 (↓ 2%)                          │
├─────────────────────────────────────────────────┤
│  Scraper Performance                             │
│  ⏱️  Avg Duration: 5.4s                          │
│  ✅ Success Rate: 98.5%                          │
│  ❌ Failures (24h): 2                            │
├─────────────────────────────────────────────────┤
│  Data Quality                                    │
│  📈 Completeness: 85%                            │
│  💰 Price Coverage: 100%                         │
│  🌿 THC Data: 75%                                │
└─────────────────────────────────────────────────┘
```

**Success Metrics**:
- ✅ Dashboard shows real-time data
- ✅ Alerts trigger correctly
- ✅ Logs searchable and organized
- ✅ Team has visibility into system health

**Time Investment**: 10-12 hours  
**Risk Level**: Low ⭐

---

#### Day 13-14: Data Enrichment

**Tasks**:
- [ ] Implement brand normalization
- [ ] Standardize category taxonomy
- [ ] Enhance potency extraction
- [ ] Add data validation pipeline
- [ ] Create data quality reports

**Deliverables**:
- Normalized brand names across dispensaries
- Consistent category structure
- Improved THC/CBD parsing
- Data quality score per product

**Data Normalization**:
```javascript
// Brand normalization
const brandMap = {
  'Select Elite': 'Select',
  'SELECT': 'Select',
  'select': 'Select',
  'Stiiizy': 'STIIIZY',
  'stiiizy': 'STIIIZY',
  // ... more mappings
};

function normalizeBrand(brand) {
  return brandMap[brand] || brand;
}

// Category standardization
const categoryMap = {
  'Pre-Roll': 'Pre-Rolls',
  'PreRoll': 'Pre-Rolls',
  'pre-roll': 'Pre-Rolls',
  'Edible': 'Edibles',
  'edible': 'Edibles',
  'Concentrate': 'Concentrates',
  // ... more mappings
};

function standardizeCategory(category) {
  return categoryMap[category] || category;
}

// Potency extraction
function extractPotency(description) {
  const thcMatch = description.match(/(\d+(?:\.\d+)?)\s*%?\s*THC/i);
  const cbdMatch = description.match(/(\d+(?:\.\d+)?)\s*%?\s*CBD/i);
  
  return {
    thc: thcMatch ? parseFloat(thcMatch[1]) : null,
    cbd: cbdMatch ? parseFloat(cbdMatch[1]) : null,
  };
}

// Data enrichment pipeline
function enrichProduct(rawProduct) {
  return {
    ...rawProduct,
    brand: normalizeBrand(rawProduct.brand),
    category: standardizeCategory(rawProduct.category),
    potency: extractPotency(rawProduct.description || ''),
    quality_score: calculateQualityScore(rawProduct),
  };
}

function calculateQualityScore(product) {
  let score = 0;
  if (product.name) score += 20;
  if (product.price) score += 20;
  if (product.brand) score += 15;
  if (product.category) score += 15;
  if (product.thc) score += 15;
  if (product.image) score += 10;
  if (product.description) score += 5;
  return score;  // Out of 100
}
```

**Success Metrics**:
- ✅ Brand names consistent (90%+ match rate)
- ✅ Categories standardized
- ✅ Potency data extracted (75%+ coverage)
- ✅ Data quality score calculated for all products

**Time Investment**: 8-10 hours  
**Risk Level**: Low ⭐

---

#### Day 15: Testing & Documentation

**Tasks**:
- [ ] Write integration tests for all scrapers
- [ ] Create API documentation
- [ ] Document deployment process
- [ ] Write operational runbook
- [ ] Conduct end-to-end testing

**Deliverables**:
- Test suite with >80% coverage
- Complete API documentation
- Deployment guide
- Operational runbook for on-call

**Test Suite**:
```javascript
// tests/scrapers.test.js
describe('Gotham Scraper', () => {
  it('should extract products from Gotham', async () => {
    const products = await scrapeGotham();
    expect(products.length).toBeGreaterThan(100);
    expect(products[0]).toHaveProperty('name');
    expect(products[0]).toHaveProperty('price');
  });

  it('should handle age gate', async () => {
    const products = await scrapeGotham({ ageGate: true });
    expect(products.length).toBeGreaterThan(0);
  });
});

describe('Data Quality', () => {
  it('should normalize brands', () => {
    expect(normalizeBrand('Select Elite')).toBe('Select');
    expect(normalizeBrand('stiiizy')).toBe('STIIIZY');
  });

  it('should calculate quality scores', () => {
    const product = { name: 'Test', price: 50, thc: 25 };
    const score = calculateQualityScore(product);
    expect(score).toBeGreaterThanOrEqual(55);
  });
});
```

**Operational Runbook**:
```markdown
# BudAlert Operations Runbook

## Daily Checks
- [ ] Verify all scrapers ran in last 24h
- [ ] Check product counts (should be stable ±10%)
- [ ] Review error logs for anomalies

## Common Issues

### Scraper fails with CAPTCHA
1. Check if Turnstile/reCAPTCHA appeared
2. Run with headless=false to solve manually
3. Consider CAPTCHA solving service for automation

### Product count drops >20%
1. Check if site is down: curl -I https://gotham.nyc/menu
2. Review HTML structure changes
3. Check if API endpoints changed
4. Fall back to browser method if API fails

### Database connection errors
1. Verify PostgreSQL is running: systemctl status postgresql
2. Check connection string: echo $DATABASE_URL
3. Restart database if needed: systemctl restart postgresql
```

**Success Metrics**:
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Runbook tested by team
- ✅ End-to-end flow verified

**Time Investment**: 8-10 hours  
**Risk Level**: Low ⭐

---

**Week 3 Summary**:
- ✅ Full monitoring in place
- ✅ Data quality improved
- ✅ Testing and documentation complete
- ✅ System ready for scale

**Total Time**: 26-32 hours  
**Cost**: $100-150 (monitoring + database + VPS)

---

### Week 4: Production Hardening & Scale

**Goal**: Prepare for long-term operation and expansion

#### Day 16-17: Infrastructure Optimization

**Tasks**:
- [ ] Migrate to managed database (RDS/Cloud SQL)
- [ ] Set up CDN for static assets (optional)
- [ ] Implement caching layer (Redis)
- [ ] Configure automated backups
- [ ] Optimize Docker images

**Deliverables**:
- Managed database with automatic backups
- Redis cache for API responses
- Optimized Docker images (50% smaller)
- Infrastructure-as-code (Terraform/CloudFormation)

**Infrastructure as Code**:
```hcl
# terraform/main.tf
resource "aws_db_instance" "budalert" {
  identifier     = "budalert-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  
  db_name  = "budalert"
  username = var.db_username
  password = var.db_password
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  
  tags = {
    Project = "BudAlert"
    Environment = "Production"
  }
}

resource "aws_elasticache_cluster" "budalert" {
  cluster_id      = "budalert-cache"
  engine          = "redis"
  node_type       = "cache.t3.micro"
  num_cache_nodes = 1
  port            = 6379
}
```

**Success Metrics**:
- ✅ Database backups running daily
- ✅ Cache hit rate >50%
- ✅ Infrastructure reproducible
- ✅ Disaster recovery plan tested

**Time Investment**: 10-12 hours  
**Risk Level**: Medium ⭐⭐⭐

---

#### Day 18-19: CI/CD Pipeline

**Tasks**:
- [ ] Set up GitHub Actions workflow
- [ ] Implement automated testing
- [ ] Configure deployment pipeline
- [ ] Add rollback mechanism
- [ ] Set up staging environment

**Deliverables**:
- Automated testing on every commit
- One-click deployment to production
- Staging environment for testing
- Rollback capability

**GitHub Actions Workflow**:
```yaml
# .github/workflows/deploy.yml
name: Deploy BudAlert Scrapers

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'  # Run every 6 hours
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 20
      - run: npm install
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker build -t budalert/gotham:${{ github.sha }} research/phase5-gotham
          docker build -t budalert/housing-works:${{ github.sha }} research/phase4-housing-works
          docker build -t budalert/conbud:${{ github.sha }} research/phase3-conbud
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push budalert/gotham:${{ github.sha }}
          docker push budalert/housing-works:${{ github.sha }}
          docker push budalert/conbud:${{ github.sha }}
      
      - name: Deploy to production
        run: |
          ssh ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }} << 'EOF'
            cd /opt/budalert
            docker-compose pull
            docker-compose up -d
            docker-compose ps
          EOF

  scrape:
    runs-on: ubuntu-latest
    if: github.event.schedule
    steps:
      - uses: actions/checkout@v3
      - name: Run scrapers
        run: docker-compose -f docker-compose-all.yml up
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: scraper-results
          path: output/**/*.json
```

**Success Metrics**:
- ✅ Tests run on every commit
- ✅ Deployments automated
- ✅ Staging environment mirrors production
- ✅ Rollback tested and works

**Time Investment**: 8-10 hours  
**Risk Level**: Medium ⭐⭐⭐

---

#### Day 20: Expansion Planning

**Tasks**:
- [ ] Research 5-10 additional dispensaries
- [ ] Identify platform types (Dutchie, Blaze, etc.)
- [ ] Create expansion roadmap
- [ ] Estimate scaling costs
- [ ] Document replication process

**Deliverables**:
- List of 10 target dispensaries
- Platform categorization
- Replication guide for new dispensaries
- Scaling cost projection

**Expansion Target List**:
```markdown
# Expansion Targets (NYC)

## Priority 1 (Same Platforms)
1. Cure Dispensary (Dutchie) - Reuse Conbud code
2. The Travel Agency (Blaze) - Reuse Housing Works code
3. Smacked (WordPress) - Reuse Gotham code

## Priority 2 (New Platforms)
4. Union Square Travel Agency (Unknown)
5. Forbidden Fruit (Unknown)
6. Have a Heart (Unknown)

## Priority 3 (Multi-State)
7. California dispensaries
8. Colorado dispensaries
9. Illinois dispensaries
```

**Platform Replication Guide**:
```markdown
# Adding a New Dutchie Dispensary

1. Copy phase3-conbud directory
2. Update dispensary URL in scraper-network-intercept.js
3. Run scraper to extract dispensaryId
4. Update scraper-graphql-direct.js with new dispensaryId
5. Test both scrapers
6. Add to docker-compose-all.yml
7. Deploy

Estimated time: 2-4 hours per dispensary
```

**Success Metrics**:
- ✅ 10 target dispensaries identified
- ✅ Platform types categorized
- ✅ Replication process documented
- ✅ Scaling costs estimated

**Time Investment**: 6-8 hours  
**Risk Level**: Low ⭐

---

**Week 4 Summary**:
- ✅ Infrastructure optimized and managed
- ✅ CI/CD pipeline operational
- ✅ Expansion roadmap created
- ✅ System production-hardened

**Total Time**: 24-30 hours  
**Cost**: $150-200/month (managed services)

---

## Infrastructure Setup

### Recommended Stack

```
┌─────────────────────────────────────────────┐
│  Application Layer                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Gotham  │  │ Housing │  │ Conbud  │    │
│  │ Scraper │  │  Works  │  │ Scraper │    │
│  │ (Node)  │  │ (Python)│  │ (Node)  │    │
│  └────┬────┘  └────┬────┘  └────┬────┘    │
└───────┼───────────┼─────────────┼──────────┘
        │           │             │
        ▼           ▼             ▼
┌─────────────────────────────────────────────┐
│  Data Layer                                 │
│  ┌─────────────────┐  ┌─────────────────┐  │
│  │   PostgreSQL    │  │     Redis       │  │
│  │  (Product Data) │  │    (Cache)      │  │
│  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────────────────────────────────┐
│  Infrastructure Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Monitoring    │  │    Alerting     │  │
│  │ (Grafana/DD)    │  │ (Slack/Email)   │  │
│  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────┘
```

### Option 1: Self-Hosted VPS (Budget-Friendly)

**Provider**: DigitalOcean, Linode, Vultr  
**Configuration**:
- 2 vCPU
- 4 GB RAM
- 80 GB SSD
- Ubuntu 22.04

**Setup**:
```bash
# Initial setup
apt update && apt upgrade -y
apt install docker.io docker-compose postgresql redis-server -y

# Configure PostgreSQL
sudo -u postgres createdb budalert
sudo -u postgres createuser budalert_user

# Clone repository
git clone https://github.com/your-org/budalert /opt/budalert
cd /opt/budalert

# Deploy
docker-compose -f docker-compose-all.yml up -d
```

**Pros**:
- ✅ Low cost ($20-40/month)
- ✅ Full control
- ✅ Simple deployment

**Cons**:
- ⚠️ Manual scaling
- ⚠️ Manual backups
- ⚠️ Single point of failure

**Best For**: MVP, small scale (3-10 dispensaries)

---

### Option 2: AWS Serverless (Scalable)

**Services**:
- Lambda (scraper execution)
- RDS PostgreSQL (database)
- ElastiCache Redis (cache)
- CloudWatch (monitoring)
- EventBridge (scheduling)

**Setup**:
```bash
# Package Lambda functions
cd research/phase5-gotham
zip -r gotham-lambda.zip . -x "node_modules/*"

# Deploy with SAM/CloudFormation
aws cloudformation create-stack \
  --stack-name budalert \
  --template-body file://cloudformation.yml \
  --parameters file://parameters.json
```

**Pros**:
- ✅ Auto-scaling
- ✅ Managed services
- ✅ High availability

**Cons**:
- ⚠️ More complex setup
- ⚠️ Vendor lock-in
- ⚠️ Higher cost at scale

**Best For**: Production scale (10-100 dispensaries)

---

### Option 3: Convex Backend (Fastest MVP)

**Services**:
- Convex (database + real-time sync)
- Vercel/Netlify (scraper hosting)
- GitHub Actions (scheduling)

**Setup**:
```bash
# Initialize Convex
npm install convex
npx convex dev

# Deploy schema
npx convex deploy

# Deploy scrapers to Vercel
vercel deploy
```

**Pros**:
- ✅ Fastest setup (1 day)
- ✅ Real-time data sync
- ✅ Built-in auth and functions
- ✅ Generous free tier

**Cons**:
- ⚠️ Less control
- ⚠️ Platform-specific

**Best For**: Rapid prototyping, demo

---

## Cost Breakdown

### Development Phase (One-Time)

| Item | Hours | Rate | Cost |
|------|-------|------|------|
| Week 1 Implementation | 30 | $100/hr | $3,000 |
| Week 2 Optimization | 26 | $100/hr | $2,600 |
| Week 3 Monitoring | 28 | $100/hr | $2,800 |
| Week 4 Hardening | 26 | $100/hr | $2,600 |
| **Total Development** | **110** | - | **$11,000** |

*Or 110 hours of your own time if DIY*

---

### Monthly Operating Costs

#### Budget Option (VPS)

| Service | Provider | Specs | Monthly Cost |
|---------|----------|-------|--------------|
| VPS | DigitalOcean | 2 vCPU, 4GB RAM | $24 |
| Database | Included | PostgreSQL on VPS | $0 |
| Cache | Included | Redis on VPS | $0 |
| Monitoring | Self-hosted | Grafana | $0 |
| Backups | DigitalOcean | 20GB snapshots | $4 |
| **Total** | - | - | **$28/month** |

**3 Dispensaries**: $28/month ($0.31/dispensary/day)  
**10 Dispensaries**: $48/month ($0.16/dispensary/day)

---

#### Production Option (AWS)

| Service | Specs | Monthly Cost |
|---------|-------|--------------|
| RDS PostgreSQL | db.t3.micro | $15 |
| ElastiCache Redis | cache.t3.micro | $12 |
| Lambda | 10K invocations/day | $5 |
| S3 Storage | 100GB | $2.30 |
| CloudWatch | Logs + metrics | $10 |
| Data Transfer | 100GB out | $9 |
| **Total** | - | **$53.30/month** |

**3 Dispensaries**: $53/month ($0.59/dispensary/day)  
**10 Dispensaries**: $85/month ($0.28/dispensary/day)  
**50 Dispensaries**: $180/month ($0.12/dispensary/day)

---

#### Premium Option (Convex)

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Convex | Starter | $25 |
| Vercel | Pro | $20 |
| GitHub Actions | Team | $4 |
| **Total** | - | **$49/month** |

**Scales automatically up to 100 dispensaries**

---

### Cost at Scale (100 Dispensaries)

| Infrastructure | Monthly | Annual | Cost/Dispensary/Day |
|----------------|---------|--------|---------------------|
| VPS (multiple) | $120 | $1,440 | $0.04 |
| AWS Managed | $350 | $4,200 | $0.12 |
| Convex | $99 | $1,188 | $0.03 |

---

## Success Criteria

### Week 1 Milestones

- [ ] **Infrastructure**: VPS or cloud account set up
- [ ] **Deployment**: Gotham scraper in production
- [ ] **Automation**: Cron job running every 6 hours
- [ ] **Data**: 150-300 products per Gotham run
- [ ] **Database**: Schema created, data importing
- [ ] **Housing Works**: Deployed and operational
- [ ] **Conbud**: Initial deployment complete
- [ ] **Product Count**: 500-1000 total products

**Success Definition**: All 3 scrapers running automatically with >95% success rate

---

### Week 2 Milestones

- [ ] **API Discovery**: All endpoints documented
- [ ] **Performance**: 10x speed improvement (API vs browser)
- [ ] **Reliability**: Error handling and fallbacks implemented
- [ ] **Alerts**: Basic alerting configured
- [ ] **Memory**: 80% reduction in resource usage
- [ ] **Data Quality**: 95%+ match between API and browser methods

**Success Definition**: System runs efficiently with minimal resource usage

---

### Week 3 Milestones

- [ ] **Monitoring**: Dashboard showing real-time metrics
- [ ] **Data Quality**: Normalization and enrichment complete
- [ ] **Testing**: >80% code coverage
- [ ] **Documentation**: Complete API docs and runbook
- [ ] **Alerts**: Configured for all critical scenarios
- [ ] **Quality Score**: 85%+ average data completeness

**Success Definition**: Full observability and high data quality

---

### Week 4 Milestones

- [ ] **Infrastructure**: Managed database with backups
- [ ] **CI/CD**: Automated deployment pipeline
- [ ] **Caching**: Redis cache with >50% hit rate
- [ ] **Scaling**: Expansion plan for 10+ dispensaries
- [ ] **Disaster Recovery**: Tested and documented
- [ ] **Cost Optimization**: Infrastructure costs under $60/month

**Success Definition**: Production-hardened system ready to scale

---

## Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **CAPTCHA blocks scraper** | Medium | High | Manual solving + CAPTCHA service + fallback to browser |
| **API changes break scraper** | Medium | High | Health checks + alerts + fallback to browser + version monitoring |
| **Site redesign** | Low | High | Multiple scraping methods + UI change detection + quick response team |
| **Rate limiting** | Low | Medium | Respect robots.txt + delays + rotate IPs if needed |
| **Database failure** | Low | Critical | Automated backups + managed service + multi-region if needed |
| **Server downtime** | Low | Medium | Uptime monitoring + redundancy + quick failover |

---

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Legal challenges** | Low | Critical | Respect ToS + public data only + legal review + clear purpose |
| **Dispensary blocks scraper** | Medium | Medium | Polite scraping + contact dispensaries + offer value exchange |
| **Data quality issues** | Medium | Medium | Validation pipeline + human review + user feedback |
| **Cost overruns** | Low | Low | Budget monitoring + cost alerts + optimize early |
| **Competition** | Low | Low | Focus on quality + unique features + fast iteration |

---

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Key person dependency** | Medium | High | Documentation + cross-training + modular architecture |
| **Burnout** | Medium | Medium | Realistic timelines + automation + team support |
| **Technical debt** | High | Medium | Regular refactoring + code reviews + testing |
| **Scope creep** | Medium | Low | Clear milestones + prioritization + MVP focus |

---

## Deployment Options Comparison

### Quick Start (Day 1)

**Method**: Local cron + Docker  
**Time**: 2-4 hours  
**Cost**: $0  
**Best For**: Testing, validation

```bash
# Run locally with cron
crontab -e
# Add: 0 */6 * * * cd ~/budalert && docker-compose up
```

---

### MVP Deploy (Week 1)

**Method**: Single VPS + Docker Compose  
**Time**: 1-2 days  
**Cost**: $20-40/month  
**Best For**: 3-10 dispensaries

```bash
# Deploy to DigitalOcean
ssh root@your-vps
git clone https://github.com/your-org/budalert
cd budalert
docker-compose -f docker-compose-all.yml up -d
```

---

### Production Deploy (Week 4)

**Method**: AWS/GCP managed services  
**Time**: 1 week  
**Cost**: $50-100/month  
**Best For**: 10-100 dispensaries

```bash
# Deploy with Terraform
cd terraform
terraform init
terraform apply
```

---

### Serverless Deploy (Fastest)

**Method**: GitHub Actions + Convex  
**Time**: 1 day  
**Cost**: $25-50/month  
**Best For**: Rapid MVP, demo

```bash
# Deploy to Convex
npx convex deploy

# Schedule with GitHub Actions
# (see .github/workflows/scrape.yml)
```

---

## Scaling Strategy

### Phase 1: Foundation (Weeks 1-4)
- 3 dispensaries operational
- Single VPS deployment
- Manual monitoring
- Basic alerting

**Target**: 500-1000 products, <5% error rate

---

### Phase 2: Optimization (Weeks 5-8)
- API optimization complete
- 10 dispensaries added
- Automated monitoring
- Managed database

**Target**: 3000-5000 products, <2% error rate

---

### Phase 3: Scale (Months 3-6)
- 25-50 dispensaries
- Multi-region deployment
- Advanced caching
- Team expansion

**Target**: 10,000-20,000 products, <1% error rate

---

### Phase 4: Enterprise (Months 6-12)
- 100+ dispensaries
- Multi-state coverage
- Machine learning for data quality
- Mobile app integration

**Target**: 50,000+ products, 99.5% uptime

---

## Next Steps

### Immediate Actions (This Week)

1. **Choose infrastructure option** (VPS recommended for MVP)
2. **Set up cloud account** (DigitalOcean/AWS/GCP)
3. **Deploy Gotham scraper** (easiest, fastest win)
4. **Verify data quality** (manual check of JSON output)
5. **Schedule next scraper** (Housing Works)

### Week 1 Goals

1. All 3 scrapers in production
2. Data flowing into database
3. Cron jobs scheduled
4. Basic monitoring in place

### Month 1 Goals

1. API optimization complete
2. Monitoring dashboard live
3. 10 dispensaries total
4. Data quality >85%

---

## Appendix

### Tools & Resources

**Development**:
- Docker Desktop: https://www.docker.com/products/docker-desktop
- Node.js 20+: https://nodejs.org
- PostgreSQL: https://www.postgresql.org
- Playwright: https://playwright.dev

**Infrastructure**:
- DigitalOcean: https://www.digitalocean.com
- AWS: https://aws.amazon.com
- Convex: https://www.convex.dev

**Monitoring**:
- Grafana: https://grafana.com
- Datadog: https://www.datadoghq.com
- CloudWatch: https://aws.amazon.com/cloudwatch

**Testing**:
- Jest: https://jestjs.io
- Playwright Test: https://playwright.dev

---

### Contact & Support

**Questions?** See QUICK_START.md for immediate help  
**Issues?** See operational runbook in Week 3 deliverables  
**Updates?** This roadmap is a living document - update as you learn

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-05  
**Next Review**: After Week 1 completion

---

✅ **Research Complete**  
✅ **Roadmap Documented**  
🚀 **Ready to Deploy**

Let's ship it! 🎯
