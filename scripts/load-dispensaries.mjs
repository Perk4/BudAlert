import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api.js";
import fs from "fs";

const CONVEX_URL = "https://quick-weasel-225.convex.cloud";
const client = new ConvexHttpClient(CONVEX_URL);

const rawData = JSON.parse(fs.readFileSync("/tmp/nys_dispensaries_prepared.json", "utf-8"));

// Convert null values to undefined (Convex optional fields)
const data = rawData.map(d => ({
  entity_name: d.entity_name,
  city: d.city,
  is_microbusiness: d.is_microbusiness,
  is_delivery_only: d.is_delivery_only,
  scraped_at: d.scraped_at,
  // Optional fields - convert null to undefined
  ...(d.address ? { address: d.address } : {}),
  ...(d.zip_code ? { zip_code: d.zip_code } : {}),
  ...(d.website ? { website: d.website } : {}),
}));

console.log(`Loading ${data.length} dispensaries...`);

const BATCH_SIZE = 50;
let inserted = 0;
let updated = 0;
let errors = 0;

for (let i = 0; i < data.length; i += BATCH_SIZE) {
  const batch = data.slice(i, i + BATCH_SIZE);
  try {
    const result = await client.mutation(api.nysDispensaries.batchUpsert, {
      dispensaries: batch
    });
    inserted += result.inserted;
    updated += result.updated;
    console.log(`Batch ${Math.floor(i/BATCH_SIZE) + 1}: +${result.inserted} inserted, ~${result.updated} updated`);
  } catch (err) {
    console.error(`Batch ${Math.floor(i/BATCH_SIZE) + 1} failed:`, err.message);
    errors += batch.length;
  }
}

console.log(`\nDone! Inserted: ${inserted}, Updated: ${updated}, Errors: ${errors}`);
