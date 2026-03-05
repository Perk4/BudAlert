import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

/**
 * Insert or update a single NYS dispensary
 * Uses entity_name as the unique identifier
 */
export const upsert = mutation({
  args: {
    entity_name: v.string(),
    address: v.optional(v.string()),
    city: v.string(),
    zip_code: v.optional(v.string()),
    website: v.optional(v.string()),
    is_microbusiness: v.boolean(),
    is_delivery_only: v.boolean(),
    scraped_at: v.number(),
  },
  handler: async (ctx, args) => {
    // Check if dispensary already exists by entity_name
    const existing = await ctx.db
      .query("nysDispensaries")
      .withIndex("by_entity_name", (q) => q.eq("entity_name", args.entity_name))
      .first();

    if (existing) {
      // Update existing record
      await ctx.db.patch(existing._id, args);
      return { id: existing._id, action: "updated" };
    } else {
      // Insert new record
      const id = await ctx.db.insert("nysDispensaries", args);
      return { id, action: "inserted" };
    }
  },
});

/**
 * Batch upsert multiple dispensaries
 * Returns summary of operations
 */
export const batchUpsert = mutation({
  args: {
    dispensaries: v.array(
      v.object({
        entity_name: v.string(),
        address: v.optional(v.string()),
        city: v.string(),
        zip_code: v.optional(v.string()),
        website: v.optional(v.string()),
        is_microbusiness: v.boolean(),
        is_delivery_only: v.boolean(),
        scraped_at: v.number(),
      })
    ),
  },
  handler: async (ctx, args) => {
    let inserted = 0;
    let updated = 0;
    const errors: string[] = [];

    for (const dispensary of args.dispensaries) {
      try {
        const result = await ctx.db
          .query("nysDispensaries")
          .withIndex("by_entity_name", (q) =>
            q.eq("entity_name", dispensary.entity_name)
          )
          .first();

        if (result) {
          await ctx.db.patch(result._id, dispensary);
          updated++;
        } else {
          await ctx.db.insert("nysDispensaries", dispensary);
          inserted++;
        }
      } catch (err) {
        errors.push(
          `Failed to upsert ${dispensary.entity_name}: ${err instanceof Error ? err.message : String(err)}`
        );
      }
    }

    return { inserted, updated, errors, total: args.dispensaries.length };
  },
});

/**
 * Get all dispensaries
 */
export const list = query({
  handler: async (ctx) => {
    return await ctx.db.query("nysDispensaries").collect();
  },
});

/**
 * Get dispensaries by city
 */
export const getByCity = query({
  args: { city: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("nysDispensaries")
      .withIndex("by_city", (q) => q.eq("city", args.city))
      .collect();
  },
});

/**
 * Get dispensaries by ZIP code
 */
export const getByZip = query({
  args: { zip_code: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("nysDispensaries")
      .withIndex("by_zip", (q) => q.eq("zip_code", args.zip_code))
      .collect();
  },
});

/**
 * Count all dispensaries
 */
export const count = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("nysDispensaries").collect();
    return all.length;
  },
});

/**
 * Get summary statistics
 */
export const getStats = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("nysDispensaries").collect();
    
    const total = all.length;
    const microbusiness = all.filter((d) => d.is_microbusiness).length;
    const deliveryOnly = all.filter((d) => d.is_delivery_only).length;
    const withWebsite = all.filter((d) => d.website).length;
    
    // Group by city
    const byCity = all.reduce((acc, d) => {
      acc[d.city] = (acc[d.city] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const topCities = Object.entries(byCity)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([city, count]) => ({ city, count }));

    return {
      total,
      microbusiness,
      deliveryOnly,
      withWebsite,
      topCities,
    };
  },
});
