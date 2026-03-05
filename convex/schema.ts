import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

/**
 * NYS Dispensary Schema
 * Source: https://cannabis.ny.gov/dispensary-location-verification
 * 
 * Fields:
 * - entity_name: Business name
 * - address: Street address (nullable for delivery-only)
 * - city: City name
 * - zip_code: 5-digit ZIP code (nullable)
 * - website: Dispensary website URL (nullable)
 * - is_microbusiness: Whether marked as microbusiness with retail location (**)
 * - is_delivery_only: Whether marked as temporary delivery only (***)
 * - scraped_at: Timestamp of when record was scraped
 * 
 * Note: County, license_type, and license_number are NOT available from the source
 */

export default defineSchema({
  nysDispensaries: defineTable({
    entity_name: v.string(),
    address: v.optional(v.string()),
    city: v.string(),
    zip_code: v.optional(v.string()),
    website: v.optional(v.string()),
    is_microbusiness: v.boolean(),
    is_delivery_only: v.boolean(),
    scraped_at: v.number(), // Unix timestamp
  })
    // Indexes for common queries
    .index("by_city", ["city"])
    .index("by_zip", ["zip_code"])
    .index("by_scraped_at", ["scraped_at"])
    // Unique constraint on entity_name to prevent duplicates
    .index("by_entity_name", ["entity_name"]),
});
