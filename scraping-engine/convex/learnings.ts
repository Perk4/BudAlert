import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

/**
 * Knowledge base operations
 */

// List learnings
export const list = query({
  args: {
    provider: v.optional(v.string()),
    type: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let q = ctx.db.query("learnings");
    
    if (args.provider) {
      q = q.withIndex("by_provider", (q) => q.eq("provider", args.provider));
    } else if (args.type) {
      q = q.withIndex("by_type", (q) => q.eq("type", args.type as any));
    }
    
    if (args.limit) {
      return await q.take(args.limit);
    }
    
    return await q.collect();
  },
});

// Get learning by ID
export const get = query({
  args: { id: v.id("learnings") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Create or update learning
export const upsert = mutation({
  args: {
    provider: v.string(),
    type: v.string(),
    title: v.string(),
    description: v.string(),
    dispensaryId: v.id("dispensaries"),
    methodId: v.optional(v.id("methods")),
    solution: v.optional(v.string()),
    solutionCode: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Check if learning already exists
    const existing = await ctx.db
      .query("learnings")
      .withIndex("by_provider", (q) => q.eq("provider", args.provider))
      .filter((q) => q.eq(q.field("title"), args.title))
      .first();
    
    if (existing) {
      // Update: increment confirmation count and add dispensary
      const affectsDispensaries = existing.affectsDispensaries.includes(args.dispensaryId)
        ? existing.affectsDispensaries
        : [...existing.affectsDispensaries, args.dispensaryId];
      
      const affectsMethods = args.methodId && !existing.affectsMethods.includes(args.methodId)
        ? [...existing.affectsMethods, args.methodId]
        : existing.affectsMethods;
      
      await ctx.db.patch(existing._id, {
        confirmedBy: existing.confirmedBy + 1,
        affectsDispensaries,
        affectsMethods,
        updatedAt: Date.now(),
      });
      
      return existing._id;
    } else {
      // Create new learning
      const now = Date.now();
      
      return await ctx.db.insert("learnings", {
        provider: args.provider,
        type: args.type as any,
        title: args.title,
        description: args.description,
        affectsDispensaries: [args.dispensaryId],
        affectsMethods: args.methodId ? [args.methodId] : [],
        solution: args.solution,
        solutionCode: args.solutionCode,
        confirmedBy: 1,
        createdAt: now,
        updatedAt: now,
      });
    }
  },
});

// Get learnings for a provider
export const getByProvider = query({
  args: {
    provider: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("learnings")
      .withIndex("by_provider", (q) => q.eq("provider", args.provider))
      .collect();
  },
});

// Get high-confidence learnings
export const getHighConfidence = query({
  args: {
    minConfirmedBy: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const threshold = args.minConfirmedBy || 3;
    
    const learnings = await ctx.db
      .query("learnings")
      .withIndex("by_confidence")
      .order("desc")
      .collect();
    
    return learnings.filter(l => l.confirmedBy >= threshold);
  },
});
