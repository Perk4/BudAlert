import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { Doc, Id } from "./_generated/dataModel";

/**
 * Dispensary CRUD operations
 */

// Get all dispensaries
export const list = query({
  args: {
    limit: v.optional(v.number()),
    status: v.optional(v.string()),
    provider: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    let q = ctx.db.query("dispensaries");
    
    if (args.status) {
      q = q.withIndex("by_status", (q) => q.eq("status", args.status as any));
    } else if (args.provider) {
      q = q.withIndex("by_provider", (q) => q.eq("provider", args.provider as any));
    }
    
    if (args.limit) {
      return await q.take(args.limit);
    }
    
    return await q.collect();
  },
});

// Get dispensary by ID
export const get = query({
  args: { id: v.id("dispensaries") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Get dispensaries by provider and status
export const getByProviderStatus = query({
  args: {
    provider: v.string(),
    status: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let q = ctx.db
      .query("dispensaries")
      .withIndex("by_provider_status", (q) =>
        q.eq("provider", args.provider as any).eq("status", args.status as any)
      );
    
    if (args.limit) {
      return await q.take(args.limit);
    }
    
    return await q.collect();
  },
});

// Get pending dispensaries ordered by priority
export const getPendingByPriority = query({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const dispensaries = await ctx.db
      .query("dispensaries")
      .withIndex("by_status", (q) => q.eq("status", "pending"))
      .collect();
    
    // Sort by priority (descending)
    const sorted = dispensaries.sort((a, b) => b.priority - a.priority);
    
    if (args.limit) {
      return sorted.slice(0, args.limit);
    }
    
    return sorted;
  },
});

// Create dispensary
export const create = mutation({
  args: {
    name: v.string(),
    address: v.optional(v.string()),
    city: v.string(),
    zipCode: v.optional(v.string()),
    website: v.optional(v.string()),
    provider: v.optional(v.string()),
    priority: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    
    return await ctx.db.insert("dispensaries", {
      name: args.name,
      address: args.address,
      city: args.city,
      zipCode: args.zipCode,
      website: args.website,
      provider: (args.provider as any) || "unknown",
      providerConfidence: 0,
      status: "pending",
      priority: args.priority || 0,
      createdAt: now,
      updatedAt: now,
    });
  },
});

// Update dispensary
export const update = mutation({
  args: {
    id: v.id("dispensaries"),
    updates: v.object({
      provider: v.optional(v.string()),
      providerConfidence: v.optional(v.number()),
      providerDetectedAt: v.optional(v.number()),
      status: v.optional(v.string()),
      priority: v.optional(v.number()),
      workingMethodId: v.optional(v.id("methods")),
      workingMethodConfidence: v.optional(v.number()),
      lastSuccessfulScrape: v.optional(v.number()),
      menuUrl: v.optional(v.string()),
      hasAgeGate: v.optional(v.boolean()),
      hasCloudflare: v.optional(v.boolean()),
      requiresBrowser: v.optional(v.boolean()),
      inventoryMethod: v.optional(v.string()),
      inventoryConfidence: v.optional(v.number()),
    }),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      ...args.updates,
      updatedAt: Date.now(),
    } as any);
    
    return args.id;
  },
});

// Get statistics
export const getStats = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("dispensaries").collect();
    
    const stats = {
      total: all.length,
      byStatus: {} as Record<string, number>,
      byProvider: {} as Record<string, number>,
      solved: 0,
      pending: 0,
      blocked: 0,
      researching: 0,
    };
    
    for (const d of all) {
      stats.byStatus[d.status] = (stats.byStatus[d.status] || 0) + 1;
      stats.byProvider[d.provider] = (stats.byProvider[d.provider] || 0) + 1;
      
      if (d.status === "solved") stats.solved++;
      if (d.status === "pending") stats.pending++;
      if (d.status === "blocked") stats.blocked++;
      if (d.status === "researching") stats.researching++;
    }
    
    return stats;
  },
});
