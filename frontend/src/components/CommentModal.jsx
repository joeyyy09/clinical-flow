
import React, { useState, useEffect } from 'react';
import Modal from './Modal';
import { Send, User, Clock } from 'lucide-react';

/**
 * CommentModal Component
 * 
 * Allows users to view and post comments/notes for a specific site.
 * Used for inter-team collaboration (e.g., CRAs and Medical Monitors).
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Controls visibility.
 * @param {Function} props.onClose - Closure callback.
 * @param {string} props.siteNumber - The site ID for which comments are displayed.
 */
const CommentModal = ({ isOpen, onClose, siteNumber }) => {
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [tag, setTag] = useState('Info');
    const [loading, setLoading] = useState(false);
    const [showMentions, setShowMentions] = useState(false);
    const [mentionQuery, setMentionQuery] = useState('');

    // Mock Users for Mentions
    const USERS = [
        { id: 'cra', name: 'Sarah (Lead CRA)', handle: '@Sarah' },
        { id: 'mm', name: 'Dr. Chang (Medical)', handle: '@DrChang' },
        { id: 'dm', name: 'Data Management', handle: '@DM_Team' },
        { id: 'safety', name: 'Safety Lead', handle: '@Safety' }
    ];

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

    const handleInputChange = (e) => {
        const val = e.target.value;
        setNewComment(val);

        const lastWord = val.split(' ').pop();
        if (lastWord.startsWith('@') && lastWord.length > 0) {
            setShowMentions(true);
            setMentionQuery(lastWord.slice(1).toLowerCase());
        } else {
            setShowMentions(false);
        }
    };

    const insertMention = (handle) => {
        const words = newComment.split(' ');
        words.pop(); // Remove the partial mention
        setNewComment([...words, handle, ''].join(' '));
        setShowMentions(false);
    };

    const filteredUsers = USERS.filter(u =>
        u.handle.toLowerCase().includes(mentionQuery) ||
        u.name.toLowerCase().includes(mentionQuery)
    );

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
        <Modal isOpen={isOpen} onClose={onClose} title={`Site Action Log - Site ${siteNumber}`}>
            <div className="flex flex-col h-[400px]">
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                    {comments.length === 0 ? (
                        <p className="text-center text-slate-400 italic mt-10">No action history for this site.</p>
                    ) : (
                        comments.map((c, i) => (
                            <div key={i} className="bg-slate-50 dark:bg-slate-700/50 p-3 rounded-lg border border-slate-100 dark:border-slate-700">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="font-semibold text-xs text-blue-600 dark:text-blue-400 flex items-center gap-2">
                                        <div className="flex items-center gap-1"><User className="w-3 h-3" /> {c.author}</div>
                                        {c.tag && (
                                            <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${c.tag === 'Urgent' ? 'bg-rose-100 text-rose-600' :
                                                c.tag === 'Review' ? 'bg-amber-100 text-amber-600' :
                                                    c.tag === 'Resolved' ? 'bg-emerald-100 text-emerald-600' :
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
                                <p className="text-sm text-slate-700 dark:text-slate-300">
                                    {c.comment.split(' ').map((word, w_i) =>
                                        word.startsWith('@') ? <span key={w_i} className="font-bold text-blue-500 bg-blue-50 dark:bg-blue-900/30 px-1 rounded mx-0.5">{word}</span> : word + ' '
                                    )}
                                </p>
                            </div>
                        ))
                    )}
                </div>

                <form onSubmit={handleSubmit} className="border-t border-slate-100 dark:border-slate-700 pt-4 relative">
                    {showMentions && filteredUsers.length > 0 && (
                        <div className="absolute bottom-full left-0 mb-2 w-64 bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50">
                            {filteredUsers.map(u => (
                                <button
                                    key={u.id}
                                    type="button"
                                    onClick={() => insertMention(u.handle)}
                                    className="w-full text-left px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 flex flex-col"
                                >
                                    <span className="font-bold text-sm text-slate-800 dark:text-white">{u.handle}</span>
                                    <span className="text-xs text-slate-500">{u.name}</span>
                                </button>
                            ))}
                        </div>
                    )}

                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={newComment}
                            onChange={handleInputChange}
                            placeholder="Log action or status change..."
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
                            <option value="Resolved">Resolved</option>
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
