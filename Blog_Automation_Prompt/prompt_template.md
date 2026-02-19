# Blog Automation Prompt Template

Use this template to generate blog posts from structured input. Fill in the placeholders and provide the completed prompt to Claude.

---

## Prompt

```
Write a blog post with the following specifications:

**Title:** [Your blog post title]

**Topic:** [Main subject of the post]

**Target Audience:** [Who is this for? e.g., beginner developers, DevOps engineers, tech managers]

**Tone:** [conversational / technical / formal / tutorial-style]

**Length:** [short (~500 words) / medium (~1000 words) / long (~2000 words)]

**Key Points to Cover:**
1. [Point 1]
2. [Point 2]
3. [Point 3]

**Include:**
- [ ] Code examples
- [ ] Diagrams or visual descriptions
- [ ] Step-by-step instructions
- [ ] Comparison table
- [ ] Call to action

**SEO Keywords:** [keyword1, keyword2, keyword3]

**Format:** Markdown with proper headings, code blocks, and a conclusion section.
```

---

## Usage Notes

- Fill in every bracketed placeholder before submitting.
- Check or uncheck the "Include" items to control what the output contains.
- For series posts, add a **Series Context** section describing previous and upcoming posts.
- Combine with the `documentation-blog-generator` skill for advanced content pipelines.
