import { mkdir, readFile, writeFile } from 'fs/promises';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

export function defaultSessionFile(moduleUrl, filename) {
  return resolve(dirname(fileURLToPath(moduleUrl)), filename);
}

export async function loadSessionFile(sessionFile) {
  try {
    const raw = await readFile(sessionFile, 'utf8');
    return JSON.parse(raw);
  } catch (error) {
    if (error.code === 'ENOENT') {
      return null;
    }
    throw error;
  }
}

export async function saveSessionFile(sessionFile, payload) {
  await mkdir(dirname(sessionFile), { recursive: true });
  await writeFile(sessionFile, JSON.stringify(payload, null, 2));
}

export function cookiesToHeader(cookies = []) {
  return cookies
    .filter(cookie => cookie && cookie.name && cookie.value)
    .map(cookie => `${cookie.name}=${cookie.value}`)
    .join('; ');
}
