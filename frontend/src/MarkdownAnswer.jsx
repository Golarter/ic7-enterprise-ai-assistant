import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './MarkdownAnswer.css';

export default function MarkdownAnswer({ text }) {
  return (
    <div className="ic7-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        components={{
          a: ({ node: _node, ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" />
          ),
        }}
      >
        {String(text ?? '')}
      </ReactMarkdown>
    </div>
  );
}
