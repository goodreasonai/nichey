import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from './MarkdownViewer.module.css'

export default function MarkdownViewer({ children }) {
    // Custom transform function for internal links
    const transformWikiLinks = (text) => {
        if (!text) return "";
        return text.replace(/\[\[([^\]|]+)\|?([^\]]*)\]\]/g, (match, pageName, displayText) => {
            const slug = pageName.trim().replace(/\s+/g, '-').toLowerCase(); // Convert title to URL slug
            const linkText = displayText.trim() || pageName.trim(); // Use displayText if provided
            return `[${linkText}](/article?e=${slug})`; // Convert to Markdown link
        });
    };

    return (
        <div className={styles.article}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {transformWikiLinks(children)}
            </ReactMarkdown>
        </div>
    );
}
