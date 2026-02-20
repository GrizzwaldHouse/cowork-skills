# Frontend UI Helper

**Version:** 1.1.0

## Name

Frontend UI Helper

## Description

A skill that assists with building and refining front-end user interfaces. It generates component code, suggests layout patterns, and helps debug styling issues across popular frameworks like React, Vue, and Svelte.

## Prerequisites

- A front-end project initialized with a supported framework (React, Vue, Svelte, or vanilla HTML/CSS/JS)
- Node.js and a package manager (npm, yarn, or pnpm) installed
- Basic familiarity with HTML, CSS, and JavaScript

## Usage

1. Open your front-end project in your editor.
2. Describe the UI component or layout you need to Claude.
3. Provide any existing code, design references, or constraints.
4. Review the generated code and integrate it into your project.

### Prompt Pattern

```
I need a [component type] for [purpose].
Framework: [React/Vue/Svelte/HTML]
Design requirements: [description or link to mockup]
Constraints: [accessibility, responsive, dark mode, etc.]
```

## Examples

### Example 1: Responsive Card Grid

**Input:**
```
I need a responsive card grid for displaying product listings.
Framework: React
Design requirements: 3 columns on desktop, 1 on mobile, with image and title per card.
Constraints: Must be accessible and use CSS Grid.
```

**Output:**
```jsx
function ProductGrid({ products }) {
  return (
    <div className="product-grid">
      {products.map((product) => (
        <article key={product.id} className="product-card">
          <img src={product.image} alt={product.name} />
          <h3>{product.name}</h3>
        </article>
      ))}
    </div>
  );
}
```

## Configuration

| Parameter       | Default   | Description                                  |
|-----------------|-----------|----------------------------------------------|
| framework       | react     | Target front-end framework                   |
| styling_method  | css       | CSS, Tailwind, CSS Modules, or styled-components |
| accessibility   | true      | Include ARIA attributes and semantic HTML    |

## Notes

- Generated components follow the conventions of the chosen framework.
- For Tailwind projects, specify `styling_method: tailwind` to get utility-class-based output.
- See `resources/` for reusable prompt snippets and reference patterns.
