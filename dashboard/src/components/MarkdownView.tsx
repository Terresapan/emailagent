"use client";

import ReactMarkdown from "react-markdown";

export default function MarkdownView({ content }: { content: string }) {
    return (
        <ReactMarkdown>
            {content}
        </ReactMarkdown>
    );
}