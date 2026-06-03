export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

export interface TocHeading {
  id: string;
  text: string;
  level: 2 | 3;
}

export function extractHeadings(content: string): TocHeading[] {
  const headings: TocHeading[] = [];
  for (const line of content.split("\n")) {
    if (line.startsWith("## ")) {
      const text = line.slice(3).trim();
      headings.push({ id: slugify(text), text, level: 2 });
    } else if (line.startsWith("### ")) {
      const text = line.slice(4).trim();
      headings.push({ id: slugify(text), text, level: 3 });
    }
  }
  return headings;
}

export function flatPagesFromManifest(
  sections: { title: string; pages: { slug: string; title: string }[] }[]
) {
  return sections.flatMap((s) => s.pages.map((p) => ({ ...p, section: s.title })));
}
