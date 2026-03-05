/**
 * Data loader for NYS Dispensaries
 * 
 * Usage (after Convex is deployed):
 * 1. Ensure Convex is initialized: npx convex dev
 * 2. Run this as a Convex action or use the CLI import script below
 */

import { internalMutation } from "./_generated/server";
import { v } from "convex/values";

/**
 * Internal mutation to bulk load dispensaries
 * Can be called from actions or other mutations
 */
export const bulkLoad = internalMutation({
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
        const existing = await ctx.db
          .query("nysDispensaries")
          .withIndex("by_entity_name", (q) =>
            q.eq("entity_name", dispensary.entity_name)
          )
          .first();

        if (existing) {
          await ctx.db.patch(existing._id, dispensary);
          updated++;
        } else {
          await ctx.db.insert("nysDispensaries", dispensary);
          inserted++;
        }
      } catch (err) {
        errors.push(
          `${dispensary.entity_name}: ${err instanceof Error ? err.message : String(err)}`
        );
      }
    }

    return { inserted, updated, errors, total: args.dispensaries.length };
  },
});
