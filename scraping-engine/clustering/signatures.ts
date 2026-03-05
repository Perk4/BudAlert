/**
 * Provider Signatures
 * HTML/API patterns that identify each platform
 */

export interface ProviderSignature {
  provider: string;
  patterns: string[];
  urlPatterns?: RegExp[];
  weight: number; // How reliable this signature is (0-1)
}

export const PROVIDER_SIGNATURES: ProviderSignature[] = [
  {
    provider: 'dutchie',
    patterns: [
      'api.dutchie.com',
      'dutchie-',
      '__NEXT_DATA__',
      'dutchie.com/embedded-menu',
      'dutchie.com/dispensary',
    ],
    urlPatterns: [
      /dutchie\.com\/embedded-menu/,
      /dutchie\.com\/dispensary/,
    ],
    weight: 0.9,
  },
  {
    provider: 'jane',
    patterns: [
      'iheartjane.com',
      'jane-embed',
      'jane-menu',
      'iheartjane',
    ],
    urlPatterns: [
      /iheartjane\.com/,
    ],
    weight: 0.95,
  },
  {
    provider: 'blaze',
    patterns: [
      'blaze.me',
      'blaze-retail',
      'blazeInsights',
      'blz-',
    ],
    urlPatterns: [
      /blaze\.me/,
    ],
    weight: 0.9,
  },
  {
    provider: 'weedmaps',
    patterns: [
      'weedmaps.com',
      'wmcdn.com',
      'weedmaps-',
    ],
    urlPatterns: [
      /weedmaps\.com/,
    ],
    weight: 0.95,
  },
  {
    provider: 'wordpress',
    patterns: [
      'wp-content',
      'wp-json',
      'woocommerce',
      'wordpress',
    ],
    weight: 0.7, // Less reliable - many sites use WordPress
  },
  {
    provider: 'shopify',
    patterns: [
      'cdn.shopify.com',
      'Shopify.theme',
      'shopify-',
    ],
    urlPatterns: [
      /\.myshopify\.com/,
    ],
    weight: 0.85,
  },
];

/**
 * Menu URL patterns for different providers
 */
export const MENU_URL_PATTERNS: Record<string, RegExp[]> = {
  dutchie: [
    /\/embedded-menu/,
    /\/menu/,
  ],
  jane: [
    /iheartjane\.com/,
  ],
  blaze: [
    /\/menu\//,
  ],
  weedmaps: [
    /weedmaps\.com\/dispensaries/,
  ],
};
