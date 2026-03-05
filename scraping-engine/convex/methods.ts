import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

/**
 * Methods registry CRUD operations
 */

// List all methods
export const list = query({
  args: {
    provider: v.optional(v.string()),
    type: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    let q = ctx.db.query("methods");
    
    if (args.provider) {
      q = q.withIndex("by_provider", (q) => q.eq("provider", args.provider));
    } else if (args.type) {
      q = q.withIndex("by_type", (q) => q.eq("type", args.type as any));
    }
    
    return await q.collect();
  },
});

// Get method by ID
export const get = query({
  args: { id: v.id("methods") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Get methods for a specific provider
export const getByProvider = query({
  args: { provider: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("methods")
      .withIndex("by_provider", (q) => q.eq("provider", args.provider))
      .collect();
  },
});

// Register a new method
export const register = mutation({
  args: {
    name: v.string(),
    provider: v.string(),
    type: v.string(),
    scriptPath: v.string(),
    requiresChromium: v.boolean(),
    requiresProxy: v.optional(v.boolean()),
    bypassesCloudflare: v.optional(v.boolean()),
    description: v.optional(v.string()),
    configSchema: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    
    return await ctx.db.insert("methods", {
      name: args.name,
      provider: args.provider,
      type: args.type as any,
      scriptPath: args.scriptPath,
      requiresChromium: args.requiresChromium,
      requiresProxy: args.requiresProxy || false,
      bypassesCloudflare: args.bypassesCloudflare || false,
      description: args.description,
      configSchema: args.configSchema,
      successCount: 0,
      failCount: 0,
      createdAt: now,
      updatedAt: now,
    });
  },
});

// Update method stats
export const updateStats = mutation({
  args: {
    id: v.id("methods"),
    success: v.boolean(),
    latencyMs: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const method = await ctx.db.get(args.id);
    if (!method) throw new Error("Method not found");
    
    const updates: any = {
      updatedAt: Date.now(),
    };
    
    if (args.success) {
      updates.successCount = method.successCount + 1;
    } else {
      updates.failCount = method.failCount + 1;
    }
    
    // Update average latency
    if (args.latencyMs !== undefined) {
      const totalRuns = method.successCount + method.failCount + 1;
      const currentAvg = method.avgLatencyMs || 0;
      updates.avgLatencyMs = ((currentAvg * (totalRuns - 1)) + args.latencyMs) / totalRuns;
    }
    
    await ctx.db.patch(args.id, updates);
    return args.id;
  },
});

// Get method statistics
export const getStats = query({
  handler: async (ctx) => {
    const methods = await ctx.db.query("methods").collect();
    
    return methods.map(m => ({
      id: m._id,
      name: m.name,
      provider: m.provider,
      type: m.type,
      successRate: m.successCount + m.failCount > 0
        ? (m.successCount / (m.successCount + m.failCount) * 100).toFixed(1)
        : "0.0",
      totalRuns: m.successCount + m.failCount,
      avgLatencyMs: m.avgLatencyMs ? Math.round(m.avgLatencyMs) : null,
    }));
  },
});
