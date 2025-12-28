
import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import { Send, User, Clock } from 'lucide-react';

const CommentModal = ({ isOpen, onClose, siteNumber }) => {
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [tag, setTag] = useState('Info');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && siteNumber) {
            fetchComments();
        }
    }, [isOpen, siteNumber]);

    const fetchComments = async () => {
        try {
            const res = await fetch(`http://127.0.0.1:8000/sites/${siteNumber}/comments`);
            const data = await res.json();
            setComments(data);
        } catch (error) {
            console.error("Failed to fetch comments", error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        setLoading(true);
        try {
            const res = await fetch(`http://127.0.0.1:8000/sites/${siteNumber}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    comment: newComment,
                    comment: newComment,
                    author: "Dr. Smith", // Mocked currently logged in user
                    tag: tag
                })
            });
            
            if (res.ok) {
                setNewComment('');
                fetchComments();
            }
        } catch (error) {
            console.error("Failed to post comment", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Team Collaboration - Site ${siteNumber}`}>
            <div className="flex flex-col h-[400px]">
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                    {comments.length === 0 ? (
                        <p className="text-center text-slate-400 italic mt-10">No discussion yet using this collaboration tool.</p>
                    ) : (
                        comments.map((c, i) => (
                            <div key={i} className="bg-slate-50 dark:bg-slate-700/50 p-3 rounded-lg border border-slate-100 dark:border-slate-700">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="font-semibold text-xs text-blue-600 dark:text-blue-400 flex items-center gap-2">
                                        <div className="flex items-center gap-1"><User className="w-3 h-3" /> {c.author}</div>
                                        {c.tag && (
                                            <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                                                c.tag === 'Urgent' ? 'bg-rose-100 text-rose-600' :
                                                c.tag === 'Review' ? 'bg-amber-100 text-amber-600' :
                                                'bg-blue-100 text-blue-600'
                                            }`}>
                                                {c.tag}
                                            </span>
                                        )}
                                    </span>
                                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                                        <Clock className="w-3 h-3" /> {new Date(c.created_at).toLocaleString()}
                                    </span>
                                </div>
                                <p className="text-sm text-slate-700 dark:text-slate-300">{c.comment}</p>
                            </div>
                        ))
                    )}
                </div>
                
                <form onSubmit={handleSubmit} className="border-t border-slate-100 dark:border-slate-700 pt-4">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="Add a note or flag for CRAs..."
                            className="flex-1 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        />
                        <select
                            value={tag}
                            onChange={(e) => setTag(e.target.value)}
                            className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                        >
                            <option value="Info">Info</option>
                            <option value="Review">Review</option>
                            <option value="Urgent">Urgent</option>
                        </select>
                        <button 
                            type="submit" 
                            disabled={loading || !newComment.trim()}
                            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </form>
            </div>
        </Modal>
    );
};

export default CommentModal;
