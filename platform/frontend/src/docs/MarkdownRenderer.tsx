import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Check, Copy } from "lucide-react";
import { slugify } from "./docsUtils";

function parseInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let partKey = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index));
    }
    const token = match[0];
    if (token.startsWith("**")) {
      nodes.push(
        <strong key={`${keyPrefix}-b-${partKey++}`}>{token.slice(2, -2)}</strong>
      );
    } else if (token.startsWith("`")) {
      nodes.push(
        <code key={`${keyPrefix}-c-${partKey++}`} className="docs-inline-code">
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("[")) {
      const linkMatch = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
      if (linkMatch) {
        const [, label, href] = linkMatch;
        if (/^https?:\/\//.test(href)) {
          nodes.push(
            <a key={`${keyPrefix}-a-${partKey++}`} href={href} target="_blank" rel="noreferrer">
              {label}
            </a>
          );
        } else {
          nodes.push(
            <Link key={`${keyPrefix}-l-${partKey++}`} to={`/docs/${href.replace(/^\//, "")}`}>
              {label}
            </Link>
          );
        }
      }
    }
    last = match.index + token.length;
  }

  if (last < text.length) {
    nodes.push(text.slice(last));
  }

  return nodes.length ? nodes : [text];
}

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="docs-code-block">
      <div className="docs-code-header">
        <span>{lang || "code"}</span>
        <button type="button" className="docs-code-copy" onClick={handleCopy}>
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const blocks: ReactNode[] = [];
  const lines = content.split("\n");
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      i += 1;
      blocks.push(<CodeBlock key={key++} lang={lang} code={codeLines.join("\n")} />);
      continue;
    }

    if (line.startsWith("# ")) {
      const text = line.slice(2);
      blocks.push(
        <h1 key={key++} id={slugify(text)} className="docs-h1">
          {parseInline(text, `h1-${key}`)}
        </h1>
      );
      i += 1;
      continue;
    }

    if (line.startsWith("## ")) {
      const text = line.slice(3);
      blocks.push(
        <h2 key={key++} id={slugify(text)} className="docs-h2">
          {parseInline(text, `h2-${key}`)}
        </h2>
      );
      i += 1;
      continue;
    }

    if (line.startsWith("### ")) {
      const text = line.slice(4);
      blocks.push(
        <h3 key={key++} id={slugify(text)} className="docs-h3">
          {parseInline(text, `h3-${key}`)}
        </h3>
      );
      i += 1;
      continue;
    }

    if (line.startsWith("> ")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("> ")) {
        quoteLines.push(lines[i].slice(2));
        i += 1;
      }
      blocks.push(
        <blockquote key={key++} className="docs-callout">
          {quoteLines.map((q, qi) => (
            <p key={qi}>{parseInline(q, `q-${key}-${qi}`)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    if (line.trim() === "---") {
      blocks.push(<hr key={key++} className="docs-hr" />);
      i += 1;
      continue;
    }

    if (line.startsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        tableLines.push(lines[i]);
        i += 1;
      }
      const rows = tableLines
        .filter((r) => !/^\|[\s\-:|]+\|$/.test(r.trim()))
        .map((r) =>
          r
            .split("|")
            .slice(1, -1)
            .map((c) => c.trim())
        );
      if (rows.length) {
        const [head, ...body] = rows;
        blocks.push(
          <div key={key++} className="docs-table-wrap">
            <table className="docs-table">
              <thead>
                <tr>
                  {head.map((c, ci) => (
                    <th key={ci}>{parseInline(c, `th-${key}-${ci}`)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.map((row, ri) => (
                  <tr key={ri}>
                    {row.map((c, ci) => (
                      <td key={ci}>{parseInline(c, `td-${key}-${ri}-${ci}`)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      continue;
    }

    if (/^[-*] /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(lines[i].replace(/^[-*] /, ""));
        i += 1;
      }
      blocks.push(
        <ul key={key++} className="docs-ul">
          {items.map((item, ii) => (
            <li key={ii}>{parseInline(item, `li-${key}-${ii}`)}</li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, ""));
        i += 1;
      }
      blocks.push(
        <ol key={key++} className="docs-ol">
          {items.map((item, ii) => (
            <li key={ii}>{parseInline(item, `oli-${key}-${ii}`)}</li>
          ))}
        </ol>
      );
      continue;
    }

    if (line.trim() === "") {
      i += 1;
      continue;
    }

    const para: string[] = [line];
    i += 1;
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].startsWith("#") &&
      !lines[i].startsWith("|") &&
      !lines[i].startsWith("```") &&
      !lines[i].startsWith("> ") &&
      lines[i].trim() !== "---" &&
      !/^[-*] /.test(lines[i]) &&
      !/^\d+\. /.test(lines[i])
    ) {
      para.push(lines[i]);
      i += 1;
    }
    blocks.push(
      <p key={key++} className="docs-p">
        {parseInline(para.join(" "), `p-${key}`)}
      </p>
    );
  }

  return <article className="docs-article">{blocks}</article>;
}
