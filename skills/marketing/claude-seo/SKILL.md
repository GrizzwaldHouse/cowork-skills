---
name: claude-seo
description: "Search engine optimization skill for technical SEO audits, content optimization, schema markup, site architecture analysis, and keyword strategy. Use when the user mentions SEO, search rankings, organic traffic, keyword research, meta tags, site crawlability, page speed, schema markup, search console data, backlinks, or wants to improve their website's search engine visibility. Also trigger for content optimization, title tag writing, meta description creation, and competitive SEO analysis."
---

# Claude SEO Skill

Comprehensive search engine optimization covering technical SEO, content optimization, and strategic planning.

## Technical SEO Audit

### Site Crawlability Checklist
- [ ] robots.txt properly configured (not blocking important pages)
- [ ] XML sitemap exists, is valid, and submitted to Search Console
- [ ] No orphan pages (every page reachable via internal links)
- [ ] Canonical tags set correctly (no duplicate content issues)
- [ ] Hreflang tags for multi-language sites
- [ ] Clean URL structure (no parameters, descriptive slugs)
- [ ] Proper 301 redirects for moved/deleted pages
- [ ] No redirect chains or loops

### Page Speed & Core Web Vitals
- **LCP** (Largest Contentful Paint): Target < 2.5s
- **INP** (Interaction to Next Paint): Target < 200ms
- **CLS** (Cumulative Layout Shift): Target < 0.1

Common fixes:
- Optimize and lazy-load images (WebP/AVIF format, srcset for responsive)
- Minimize render-blocking CSS/JS
- Use font-display: swap for web fonts
- Preload critical resources
- Implement proper image dimensions to prevent CLS

### Mobile-First Optimization
- Responsive design (no horizontal scrolling)
- Touch-friendly tap targets (48px minimum)
- Readable font sizes without zooming (16px minimum body)
- No intrusive interstitials

## Content Optimization

### On-Page SEO Elements

```html
<!-- Title Tag: 50-60 characters, primary keyword near front -->
<title>Primary Keyword - Supporting Context | Brand</title>

<!-- Meta Description: 150-160 characters, compelling CTA -->
<meta name="description" content="Clear value proposition with primary keyword. Include a call-to-action that encourages clicks.">

<!-- Heading Hierarchy -->
<h1>One per page, contains primary keyword</h1>
<h2>Section headers with secondary keywords</h2>
<h3>Subsection headers with related terms</h3>
```

### Content Structure
- **Introduction**: Hook + primary keyword in first 100 words
- **Body**: Comprehensive coverage of topic with semantic keywords
- **Headings**: Clear hierarchy (H1 > H2 > H3), keyword-rich but natural
- **Internal links**: Link to related pages with descriptive anchor text
- **Media**: Images with descriptive alt text, relevant videos
- **Conclusion**: Summary + clear next action

### Keyword Strategy
1. **Primary keyword**: Main topic (1 per page)
2. **Secondary keywords**: Related topics (2-5 per page)
3. **Long-tail variants**: Specific queries users actually search
4. **Semantic keywords**: Related terms and synonyms (LSI)

### Content Quality Signals
- Comprehensive coverage (2000+ words for competitive topics)
- Original research, data, or insights
- Updated regularly (include "Last updated" dates)
- Expert authorship (author bio, credentials, E-E-A-T signals)
- User engagement (low bounce rate, high time on page)

## Schema Markup (Structured Data)

### Common Schema Types

```json
// Article Schema
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": {"@type": "Person", "name": "Author Name"},
  "datePublished": "2026-01-01",
  "dateModified": "2026-04-14",
  "image": "https://example.com/image.jpg",
  "description": "Article description"
}

// FAQ Schema
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "Question text?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Answer text."
    }
  }]
}

// Product Schema
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "offers": {
    "@type": "Offer",
    "price": "99.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}

// LocalBusiness Schema
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Business Name",
  "address": {"@type": "PostalAddress", ...},
  "telephone": "+1-555-555-5555",
  "openingHours": "Mo-Fr 09:00-17:00"
}
```

## Site Architecture

### URL Structure
```
example.com/
├── /category/                    # Category page
│   ├── /category/subcategory/    # Subcategory
│   │   └── /category/subcategory/page-slug/  # Content page
├── /blog/                        # Blog index
│   └── /blog/post-slug/          # Blog post
└── /tools/                       # Tool/resource pages
```

### Internal Linking Strategy
- **Hub-and-spoke**: Pillar pages link to cluster content and vice versa
- **Contextual links**: Link within body content (not just navigation)
- **Breadcrumbs**: Help users and search engines understand hierarchy
- **Related content**: Suggest relevant pages at end of content
- **Anchor text**: Descriptive, keyword-rich (avoid "click here")

## SEO Audit Report Template

```markdown
# SEO Audit Report: [Site Name]

## Executive Summary
[Key findings and priority recommendations]

## Technical Health
- Crawlability: [Score/Status]
- Core Web Vitals: [LCP/INP/CLS scores]
- Mobile Usability: [Status]
- Schema Markup: [Present/Missing]
- SSL/HTTPS: [Status]

## Content Analysis
- Keyword coverage: [Assessment]
- Content quality: [Assessment]
- Thin/duplicate content: [Count/pages]
- Missing meta tags: [Count/pages]

## Priority Recommendations
1. [Highest impact fix]
2. [Second priority]
3. [Third priority]

## Detailed Findings
[Section-by-section breakdown]
```

## Competitive SEO Analysis

1. **Identify competitors**: Who ranks for your target keywords?
2. **Gap analysis**: What keywords do competitors rank for that you don't?
3. **Content comparison**: How does content depth and quality compare?
4. **Backlink profile**: Where do competitors get their links?
5. **Technical comparison**: Site speed, mobile experience, schema usage
6. **Opportunity mapping**: Where can you realistically outperform competitors?
