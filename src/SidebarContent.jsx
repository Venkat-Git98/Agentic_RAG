import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SidebarContent = ({ node }) => {
    const [explanation, setExplanation] = useState('');

    useEffect(() => {
        if (!node) {
            fetch('/model_explanation.txt')
                .then(response => response.text())
                .then(text => setExplanation(text))
                .catch(error => console.error('Error fetching model explanation:', error));
        }
    }, [node]);

    if (!node) {
        return (
            <div className="p-4 text-gray-300">
                <div className="prose prose-sm prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {explanation}
                    </ReactMarkdown>
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 text-gray-300">
            <h3 className="text-xl font-bold text-cyan-400 mb-3">{node.data.label}</h3>
            <div className="prose prose-sm prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {node.data.description}
                </ReactMarkdown>
            </div>
        </div>
    );
};

export default SidebarContent; 