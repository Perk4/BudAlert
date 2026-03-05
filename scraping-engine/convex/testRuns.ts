import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { Id } from "./_generated/dataModel";

/**
 * Test run tracking
 */

// Create test run
export const create = mutation({
  args: {
    dispensaryId: v.id("dispensaries"),
    methodId: v.id("methods"),
    status: v.string(),
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
    errorType: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
    llmAnalysis: v.optional(v.string()),
    suggestedFix: v.optional(v.string()),
    sampleOutput: v.optional(v.any()),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    
    return await ctx.db.insert("testRuns", {
      dispensaryId: args.dispensaryId,
      methodId: args.methodId,
      startedAt: now,
      completedAt: now,
      status: args.status as any,
      productsFound: args.productsFound,
      fieldsExtracted: args.fieldsExtracted,
      fieldCompleteness: args.fieldCompleteness,
      inventoryDetected: args.inventoryDetected,
      errorType: args.errorType,
      errorMessage: args.errorMessage,
      llmAnalysis: args.llmAnalysis,
      suggestedFix: args.suggestedFix,
      sampleOutput: args.sampleOutput,
      metadata: args.metadata,
    });
  },
});

// Get test runs for a dispensary
export const getByDispensary = query({
  args: {
    dispensaryId: v.id("dispensaries"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let q = ctx.db
      .query("testRuns")
      .withIndex("by_dispensary", (q) => q.eq("dispensaryId", args.dispensaryId));
    
    if (args.limit) {
      return await q.take(args.limit);
    }
    
    return await q.collect();
  },
});

// Get test runs for a method
export const getByMethod = query({
  args: {
    methodId: v.id("methods"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let q = ctx.db
      .query("testRuns")
      .withIndex("by_method", (q) => q.eq("methodId", args.methodId));
    
    if (args.limit) {
      return await q.take(args.limit);
    }
    
    return await q.collect();
  },
});

// Get recent failures for analysis
export const getRecentFailures = query({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const runs = await ctx.db
      .query("testRuns")
      .withIndex("by_status", (q) => q.eq("status", "failed"))
      .order("desc")
      .take(args.limit || 10);
    
    return runs;
  },
});

// Check if method has been tried on dispensary
export const hasBeenTried = query({
  args: {
    dispensaryId: v.id("dispensaries"),
    methodId: v.id("methods"),
  },
  handler: async (ctx, args) => {
    const run = await ctx.db
      .query("testRuns")
      .withIndex("by_dispensary_method", (q) =>
        q.eq("dispensaryId", args.dispensaryId).eq("methodId", args.methodId)
      )
      .first();
    
    return run !== null;
  },
});

// Get all methods tried on a dispensary
export const getTriedMethods = query({
  args: {
    dispensaryId: v.id("dispensaries"),
  },
  handler: async (ctx, args) => {
    const runs = await ctx.db
      .query("testRuns")
      .withIndex("by_dispensary", (q) => q.eq("dispensaryId", args.dispensaryId))
      .collect();
    
    const methodIds = new Set(runs.map(r => r.methodId));
    return Array.from(methodIds);
  },
});
