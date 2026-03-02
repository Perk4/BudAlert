# Store Reconnaissance Findings

## Phase 6B: Medium Custom Sites

### Store Intelligence Summary

| Store | URL | Framework | Location | Key Tech | Age Gate | API Detected |
|-------|-----|-----------|----------|----------|----------|--------------|
| Travel Agency | thetravelagency.co | Remix/React | Union Square | SSR, Dutchie images | No | No |
| Gotham | gotham.nyc | WordPress/Dovetail | Multiple NYC | Plugin-based | Potential | AJAX |
| Dazed | dazed.fun | WordPress | Union Sq + Holyoke MA | Custom theme | Yes | Unknown |
| Green Apple | greenapple.nyc | WordPress Custom | Brooklyn | JS-heavy | Yes | Unknown |
| Chelsea Cannabis | chelseacannabis.co | Ruby on Rails | Chelsea | CSRF tokens | No | Potential REST |
| Verilife | verilife.com/ny | Magento | Multiple NY | Enterprise | No | GraphQL/REST |

### Detailed Intelligence

#### The Travel Agency
- **Architecture**: Modern React/Remix stack with server-side rendering
- **Data Source**: Embedded JSON in `window.__remixContext`
- **Product Display**: Server-rendered product cards with full metadata
- **Images**: Dutchie CDN integration (`images.dutchie.com`)
- **Inventory**: RYTHM brand focus, flower/vapes/edibles
- **Security**: Minimal - no age gate or bot protection detected
- **API Potential**: No external API calls observed, data embedded in page

#### Gotham NYC
- **Architecture**: WordPress with Dovetail ecommerce plugin
- **Data Source**: WordPress database via plugin AJAX calls
- **Product Display**: Plugin-generated product grids
- **Images**: Dutchie CDN + local WordPress uploads
- **Inventory**: Multi-brand dispensary
- **Security**: Standard WordPress, potential soft age verification
- **API Potential**: High - WordPress REST API + Dovetail endpoints

#### Dazed Cannabis
- **Architecture**: WordPress with custom cannabis theme
- **Data Source**: WordPress + WooCommerce potential
- **Product Display**: Theme-integrated product listings
- **Images**: Local + CDN hosting
- **Inventory**: Multi-location inventory (MA + NY)
- **Security**: Strong age verification popup system
- **API Potential**: WordPress REST API if accessible

#### Green Apple
- **Architecture**: Custom WordPress theme with heavy JavaScript
- **Data Source**: AJAX-loaded product data
- **Product Display**: JavaScript-rendered product grid
- **Images**: Local WordPress media library
- **Inventory**: Brooklyn-focused curated selection
- **Security**: Custom age verification system + JS dependency
- **API Potential**: WordPress REST API + custom endpoints

#### Chelsea Cannabis Co.
- **Architecture**: Ruby on Rails web application
- **Data Source**: Rails database via ActiveRecord models
- **Product Display**: ERB templates with Rails conventions
- **Images**: Rails asset pipeline + cloud storage
- **Inventory**: Chelsea-specific product selection
- **Security**: Rails CSRF protection, potential shop subdomain
- **API Potential**: Very high - Rails API conventions

#### Verilife NY
- **Architecture**: Magento enterprise e-commerce platform
- **Data Source**: Magento product catalog API
- **Product Display**: Magento themes with product grids
- **Images**: Magento media system + CDN
- **Inventory**: Multi-state operator (MSO) product catalog
- **Security**: Enterprise-grade Magento security
- **API Potential**: Extremely high - Magento REST API + GraphQL

### Framework Distribution

```
WordPress (3/6): Gotham, Dazed, Green Apple
- Standard WP structure with cannabis-specific plugins/themes
- REST API availability varies by configuration
- Age verification commonly implemented

Modern JS (1/6): Travel Agency  
- React/Remix with excellent SSR data access
- Minimal security barriers
- High-quality structured data

Enterprise (1/6): Verilife
- Magento enterprise platform
- Complex but well-documented API structure
- Professional-grade implementation

Custom Framework (1/6): Chelsea Cannabis
- Rails application with standard patterns
- CSRF protection requires session handling
- RESTful API potential
```

### Access Difficulty Rankings

1. **Easy (1/6)**: Travel Agency - Direct HTML scraping
2. **Medium (2/6)**: Gotham, Chelsea Cannabis - Framework complexity
3. **Hard (3/6)**: Dazed, Green Apple, Verilife - Age gates + JS dependency