import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

/**
 * BudAlert Full Schema
 * Using schemaless tables for evolved data structures
 * Indexes restored from production
 */

// Helper for flexible documents
const flexibleDoc = v.any();

export default defineSchema({
  // ============================================
  // NYS Dispensaries (new table - strict)
  // ============================================
  nysDispensaries: defineTable({
    entity_name: v.string(),
    address: v.optional(v.string()),
    city: v.string(),
    zip_code: v.optional(v.string()),
    website: v.optional(v.string()),
    is_microbusiness: v.boolean(),
    is_delivery_only: v.boolean(),
    scraped_at: v.number(),
  })
    .index("by_city", ["city"])
    .index("by_zip", ["zip_code"])
    .index("by_scraped_at", ["scraped_at"])
    .index("by_entity_name", ["entity_name"]),

  // ============================================
  // Core Data Tables (flexible for evolution)
  // ============================================
  retailers: defineTable(flexibleDoc)
    .index("by_slug", ["slug"])
    .index("by_region", ["region"])
    .index("by_license", ["licenseNumber"]),

  products: defineTable(flexibleDoc)
    .index("by_brand", ["brandId"])
    .index("by_category", ["category"])
    .index("by_brand_category", ["brandId", "category"])
    .index("by_normalized_name", ["normalizedName"]),

  brands: defineTable(flexibleDoc)
    .index("by_normalized_name", ["normalizedName"])
    .index("by_category", ["category"]),

  // ============================================
  // Inventory Tables (flexible)
  // ============================================
  currentInventory: defineTable(flexibleDoc)
    .index("by_retailer", ["retailerId"])
    .index("by_product", ["productId"])
    .index("by_brand", ["brandId"])
    .index("by_retailer_product", ["retailerId", "productId"])
    .index("by_retailer_brand", ["retailerId", "brandId"])
    .index("by_stock_status", ["inStock", "brandId"])
    .index("by_low_stock", ["inStock", "quantity"]),

  menuSnapshots: defineTable(flexibleDoc)
    .index("by_batch", ["batchId"])
    .index("by_retailer_time", ["retailerId", "scrapedAt"])
    .index("by_retailer_product", ["retailerId", "productId"])
    .index("by_product_time", ["productId", "scrapedAt"]),

  inventoryDeltas: defineTable(flexibleDoc)
    .index("by_batch", ["batchId"])
    .index("by_product_date", ["productId", "scrapeDate"])
    .index("by_retailer_date", ["retailerId", "scrapeDate"])
    .index("by_brand_date", ["brandId", "scrapeDate"])
    .index("by_product_retailer", ["productId", "retailerId", "scrapedAt"])
    .index("by_date_cycle", ["scrapeDate", "cycleLabel"])
    .index("by_velocity", ["scrapeDate", "velocityPerHour"]),

  inventoryEvents: defineTable(flexibleDoc)
    .index("by_batch", ["batchId"])
    .index("by_time", ["timestamp"])
    .index("by_type", ["eventType", "timestamp"])
    .index("by_retailer", ["retailerId", "timestamp"])
    .index("by_product", ["productId", "timestamp"])
    .index("by_notified", ["notified", "timestamp"])
    .index("by_type_notified", ["eventType", "notified"])
    .index("by_notification_state", ["notificationState", "timestamp"]),

  // ============================================
  // Scraping Infrastructure
  // ============================================
  scrapeBatches: defineTable(flexibleDoc)
    .index("by_batch", ["batchId"])
    .index("by_status", ["status"])
    .index("by_time", ["startedAt"]),

  scrapeBatchChunks: defineTable(flexibleDoc)
    .index("by_batch", ["batchId"])
    .index("by_tracking", ["trackingId"])
    .index("by_tracking_chunk", ["trackingId", "chunkIndex"]),

  scrapeJobs: defineTable(flexibleDoc)
    .index("by_status", ["status"])
    .index("by_batch", ["batchId"])
    .index("by_retailer_time", ["retailerId", "startedAt"]),

  scraperAlerts: defineTable(flexibleDoc)
    .index("by_time", ["createdAt"])
    .index("by_type", ["type", "createdAt"])
    .index("by_severity", ["severity", "createdAt"])
    .index("by_acknowledged", ["acknowledged", "createdAt"]),

  deadLetterQueue: defineTable(flexibleDoc)
    .index("by_platform", ["sourcePlatform"])
    .index("by_retailer", ["retailerId"])
    .index("by_error_type", ["errorType"])
    .index("by_time", ["lastAttemptAt"])
    .index("by_status", ["resolvedAt"]),

  // ============================================
  // User & Subscription Tables
  // ============================================
  users: defineTable(flexibleDoc)
    .index("by_email", ["email"])
    .index("by_plan", ["plan"])
    .index("by_external_auth", ["authProvider", "externalAuthId"]),

  subscriptions: defineTable(flexibleDoc)
    .index("by_email", ["email"])
    .index("by_tier", ["tier", "status"])
    .index("by_stripe_customer", ["stripeCustomerId"])
    .index("by_stripe_subscription", ["stripeSubscriptionId"]),

  watchlists: defineTable(flexibleDoc)
    .index("by_user", ["userId"])
    .index("by_user_type", ["userId", "type"]),

  productWatches: defineTable(flexibleDoc)
    .index("by_email", ["email"])
    .index("by_product", ["productId"])
    .index("by_email_product", ["email", "productId"])
    .index("by_active", ["isActive"]),

  alerts: defineTable(flexibleDoc)
    .index("by_user_time", ["userId", "createdAt"])
    .index("by_user_unread", ["userId", "isRead"])
    .index("by_watchlist", ["watchlistId"]),

  // ============================================
  // Notification Queue
  // ============================================
  notificationQueue: defineTable(flexibleDoc)
    .index("by_event", ["eventId"])
    .index("by_status", ["status", "nextRetryAt"])
    .index("by_webhook", ["webhookUrl", "status"])
    .index("by_dedupe_key", ["dedupeKey"]),

  // ============================================
  // B2B / Account Tables
  // ============================================
  retailerAccounts: defineTable(flexibleDoc)
    .index("by_retailer", ["retailerId"])
    .index("by_email", ["email"])
    .index("by_stripe_customer", ["stripeCustomerId"]),

  b2bAlerts: defineTable(flexibleDoc)
    .index("by_account_time", ["accountId", "createdAt"])
    .index("by_account_unread", ["accountId", "isRead"])
    .index("by_type", ["type", "createdAt"])
    .index("by_severity", ["severity", "createdAt"]),

  b2bPriceCache: defineTable(flexibleDoc)
    .index("by_account", ["accountId"])
    .index("by_account_product", ["accountId", "productId"]),

  competitorMonitors: defineTable(flexibleDoc)
    .index("by_account", ["accountId"])
    .index("by_competitor", ["competitorId"])
    .index("by_account_competitor", ["accountId", "competitorId"]),

  // ============================================
  // Analytics & Cache
  // ============================================
  brandAnalytics: defineTable(flexibleDoc)
    .index("by_brand_period", ["brandId", "period", "periodStart"])
    .index("by_brand_region", ["brandId", "region"])
    .index("by_region_period", ["region", "period", "periodStart"]),

  statsCache: defineTable(flexibleDoc)
    .index("by_key", ["key"]),

  // ============================================
  // Payments
  // ============================================
  paymentEvents: defineTable(flexibleDoc)
    .index("by_stripe_event", ["stripeEventId"])
    .index("by_type", ["eventType", "createdAt"])
    .index("by_email", ["email", "createdAt"]),
});
