import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

/**
 * Scraping Research Engine Schema
 * Tracks dispensaries, methods, test runs, and learnings
 */

export default defineSchema({
  // ============================================
  // Dispensaries
  // ============================================
  dispensaries: defineTable({
    // Basic info (from NYS data)
    name: v.string(),
    address: v.optional(v.string()),
    city: v.string(),
    zipCode: v.optional(v.string()),
    website: v.optional(v.string()),
    
    // Provider classification
    provider: v.union(
      v.literal("dutchie"),
      v.literal("jane"),
      v.literal("blaze"),
      v.literal("weedmaps"),
      v.literal("wordpress"),
      v.literal("shopify"),
      v.literal("custom"),
      v.literal("unknown")
    ),
    providerConfidence: v.number(),
    providerDetectedAt: v.optional(v.number()),
    
    // Research status
    status: v.union(
      v.literal("pending"),
      v.literal("researching"),
      v.literal("solved"),
      v.literal("blocked"),
      v.literal("degraded"),
      v.literal("manual")
    ),
    priority: v.number(),
    
    // Working method (once found)
    workingMethodId: v.optional(v.id("methods")),
    workingMethodConfidence: v.optional(v.number()),
    lastSuccessfulScrape: v.optional(v.number()),
    
    // Metadata
    menuUrl: v.optional(v.string()),
    hasAgeGate: v.optional(v.boolean()),
    hasCloudflare: v.optional(v.boolean()),
    requiresBrowser: v.optional(v.boolean()),
    
    // Inventory detection
    inventoryMethod: v.optional(v.union(
      v.literal("cart_probe"),
      v.literal("api"),
      v.literal("dropdown"),
      v.literal("badge"),
      v.literal("none")
    )),
    inventoryConfidence: v.optional(v.number()),
    
    // Timestamps
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_provider", ["provider"])
    .index("by_status", ["status"])
    .index("by_priority", ["priority"])
    .index("by_city", ["city"])
    .index("by_provider_status", ["provider", "status"]),

  // ============================================
  // Methods (Pluggable Registry)
  // ============================================
  methods: defineTable({
    name: v.string(),
    provider: v.string(),
    type: v.union(
      v.literal("http"),
      v.literal("browser"),
      v.literal("api"),
      v.literal("hybrid")
    ),
    
    // Implementation
    scriptPath: v.string(),
    configSchema: v.optional(v.any()),
    
    // Stats
    successCount: v.number(),
    failCount: v.number(),
    avgLatencyMs: v.optional(v.number()),
    
    // Compatibility
    requiresChromium: v.boolean(),
    requiresProxy: v.boolean(),
    bypassesCloudflare: v.boolean(),
    
    // Metadata
    description: v.optional(v.string()),
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_provider", ["provider"])
    .index("by_type", ["type"])
    .index("by_name", ["name"]),

  // ============================================
  // Test Runs
  // ============================================
  testRuns: defineTable({
    dispensaryId: v.id("dispensaries"),
    methodId: v.id("methods"),
    
    // Execution
    startedAt: v.number(),
    completedAt: v.optional(v.number()),
    status: v.union(
      v.literal("running"),
      v.literal("success"),
      v.literal("partial"),
      v.literal("failed"),
      v.literal("timeout")
    ),
    
    // Results
    productsFound: v.number(),
    fieldsExtracted: v.array(v.string()),
    fieldCompleteness: v.object({
      overall: v.number(),
      name: v.number(),
      price: v.number(),
      brand: v.number(),
      category: v.number(),
      thc: v.number(),
      inStock: v.number(),
    }),
    inventoryDetected: v.boolean(),
    
    // Failure analysis
    errorType: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
    llmAnalysis: v.optional(v.string()),
    suggestedFix: v.optional(v.string()),
    
    // Artifacts
    sampleOutput: v.optional(v.any()),
    screenshotUrl: v.optional(v.string()),
    htmlSnapshotUrl: v.optional(v.string()),
    
    // Metadata
    metadata: v.optional(v.any()),
  })
    .index("by_dispensary", ["dispensaryId"])
    .index("by_method", ["methodId"])
    .index("by_status", ["status"])
    .index("by_time", ["startedAt"])
    .index("by_dispensary_method", ["dispensaryId", "methodId"]),

  // ============================================
  // Learnings (Knowledge Base)
  // ============================================
  learnings: defineTable({
    provider: v.string(),
    type: v.union(
      v.literal("gotcha"),
      v.literal("patch"),
      v.literal("pattern"),
      v.literal("blocker")
    ),
    
    title: v.string(),
    description: v.string(),
    
    // Applicability
    affectsDispensaries: v.array(v.id("dispensaries")),
    affectsMethods: v.array(v.id("methods")),
    
    // Solution (if any)
    solution: v.optional(v.string()),
    solutionCode: v.optional(v.string()),
    
    // Confidence
    confirmedBy: v.number(),
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_provider", ["provider"])
    .index("by_type", ["type"])
    .index("by_confidence", ["confirmedBy"]),
});
