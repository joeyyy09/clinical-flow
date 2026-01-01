
import React, { useState } from 'react';
import { LayoutDashboard, AlertTriangle, FileText, Database, Settings, Bell, Search, Activity, Bot, ChevronDown, User, LogOut, X } from 'lucide-react';
import ChatInterface from './ChatInterface';
import { motion, AnimatePresence } from 'framer-motion';

import Modal from './Modal';

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <div
        onClick={onClick}
        className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all duration-200 border-l-4 ${active
<<<<<<< HEAD
                ? 'bg-gradient-to-r from-blue-900/50 to-transparent border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
=======
            ? 'bg-gradient-to-r from-blue-900/50 to-transparent border-blue-500 text-blue-400'
            : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
>>>>>>> ed5a650 (Updated LLM in chatbot)
            }`}
    >
        <Icon className={`w-5 h-5 ${active ? 'text-blue-400' : ''}`} />
        <span className="font-medium text-sm tracking-wide">{label}</span>
    </div>
);

const AppLayout = ({ children, activeTab, setActiveTab, searchQuery, setSearchQuery, onLogout, darkMode, setDarkMode }) => {
    const [notificationsOpen, setNotificationsOpen] = useState(false);
    const [isSidebarOpen, setSidebarOpen] = useState(true);
    const [profileOpen, setProfileOpen] = useState(false);
    const [helpOpen, setHelpOpen] = useState(false);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [unreadCount, setUnreadCount] = useState(2);

    const handleLogout = () => {
        setProfileOpen(false);
        onLogout();
    };

    const markAllRead = () => {
        setUnreadCount(0);
        setNotificationsOpen(false);
    };

    return (
        <div className="flex h-screen bg-slate-50 dark:bg-slate-900 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
            {/* Premium Dark Sidebar */}
            <motion.div
                animate={{ width: isSidebarOpen ? 280 : 80 }}
                className="bg-slate-900 flex flex-col border-r border-slate-800 shadow-xl z-20"
            >
                <div className="h-16 flex items-center px-6 border-b border-slate-800">
                    <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                        <Activity className="text-white w-5 h-5" />
                    </div>
                    {isSidebarOpen && (
                        <motion.h1
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="ml-3 text-white font-bold text-xl tracking-tight"
                        >
                            Clinical<span className="text-blue-500">Flow</span>
                        </motion.h1>
                    )}
                </div>

                <div className="flex-1 py-6 overflow-y-auto">
                    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest px-6 mb-4">Analytics</div>
                    <SidebarItem icon={LayoutDashboard} label={isSidebarOpen ? "Overview" : ""} active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
                    <SidebarItem icon={AlertTriangle} label={isSidebarOpen ? "Risk Monitor" : ""} active={activeTab === 'risk'} onClick={() => setActiveTab('risk')} />

                    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest px-6 mb-4 mt-8">Data Ops</div>
                    <SidebarItem icon={Database} label={isSidebarOpen ? "Data Ingestion" : ""} active={activeTab === 'data'} onClick={() => setActiveTab('data')} />
                    <SidebarItem icon={FileText} label={isSidebarOpen ? "Reports" : ""} active={activeTab === 'reports'} onClick={() => setActiveTab('reports')} />

                    <div className="text-xs font-bold text-slate-500 uppercase tracking-widest px-6 mb-4 mt-8">Intelligence</div>
                    <SidebarItem icon={Bot} label={isSidebarOpen ? "Agent Copilot" : ""} active={activeTab === 'agent'} onClick={() => setActiveTab('agent')} />
                </div>

                <div className="p-4 border-t border-slate-800">
                    <div
                        onClick={() => setProfileOpen(true)}
                        className="flex items-center gap-3 p-2 rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer group"
                    >
                        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-emerald-400 to-cyan-500 flex items-center justify-center text-white font-bold text-sm">DS</div>
                        {isSidebarOpen && (
                            <div className="flex-1 min-w-0">
                                <p className="text-white text-sm font-medium truncate">Dr. Smith</p>
                                <p className="text-slate-400 text-xs truncate">Administrator</p>
                            </div>
                        )}
                        {isSidebarOpen && (
                            <button
                                onClick={(e) => { e.stopPropagation(); setSettingsOpen(true); }}
                                className="p-1 text-slate-500 hover:text-slate-300 rounded-full transition-colors"
                            >
                                <Settings className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>
            </motion.div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
                {/* Modern Glassy Header */}
                <header className="h-16 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-8 z-10 sticky top-0 transition-colors duration-200">
                    {/* Search */}
                    <div className="relative group w-96">
                        <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search studies, sites, or patients..."
                            className="w-full bg-slate-100/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-full pl-10 pr-10 py-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:bg-white dark:focus:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-sm"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        )}
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="relative">
                            <button
                                onClick={() => setNotificationsOpen(!notificationsOpen)}
                                className="relative p-2 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                            >
                                <Bell className="w-5 h-5" />
                                {unreadCount > 0 && (
                                    <span className="absolute top-1 right-2 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white dark:ring-slate-900 animate-pulse"></span>
                                )}
                            </button>

                            {/* Notification Dropdown */}
                            <AnimatePresence>
                                {notificationsOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                        className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-100 dark:border-slate-700 py-2 z-50"
                                    >
                                        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-700 font-semibold text-sm text-slate-700 dark:text-slate-200 flex justify-between items-center">
                                            <span>Operational Alerts</span>
                                            {unreadCount > 0 && (
                                                <button onClick={markAllRead} className="text-xs text-blue-600 dark:text-blue-400 hover:underline">Mark all read</button>
                                            )}
                                        </div>
                                        <div className="max-h-64 overflow-y-auto">
                                            <div className="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 border-b border-slate-100 dark:border-slate-700 cursor-pointer transition-colors">
                                                <p className="text-xs font-bold text-rose-600 dark:text-rose-400 mb-1 flex items-center justify-between">
                                                    High Risk Detected {unreadCount > 0 && <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>}
                                                </p>
                                                <p className="text-sm text-slate-600 dark:text-slate-300">Site 14 has exceeded missing pages threshold.</p>
                                                <p className="text-xs text-slate-400 mt-1">2 mins ago</p>
                                            </div>
                                            <div className="px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer transition-colors">
                                                <p className="text-xs font-bold text-blue-600 dark:text-blue-400 mb-1 flex items-center justify-between">
                                                    Ingestion Complete {unreadCount > 0 && <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>}
                                                </p>
                                                <p className="text-sm text-slate-600 dark:text-slate-300">Study 14 dataset processed successfully.</p>
                                                <p className="text-xs text-slate-400 mt-1">1 hour ago</p>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        <div className="h-8 w-px bg-slate-200 dark:bg-slate-700"></div>
                        <button
                            onClick={() => setHelpOpen(true)}
                            className="text-sm font-medium text-slate-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400 transition-colors"
                        >
                            Help Center
                        </button>
                    </div>
                </header>

                {/* Dynamic Page Content */}
                <main className={`flex-1 relative transition-colors duration-200 ${activeTab === 'agent' ? 'overflow-hidden p-6' : 'overflow-y-auto p-8 scroll-smooth bg-slate-50 dark:bg-slate-900'}`}>
                    {children}
                </main>
            </div>

            {/* Floating Chat Agent if not on Agent tab */}
            {activeTab !== 'agent' && (
                <div className="absolute bottom-8 right-8 z-50">
                    <ChatInterface minimized={true} />
                </div>
            )}

            {/* Modals */}
            <Modal isOpen={profileOpen} onClose={() => setProfileOpen(false)} title="User Profile">
                <div className="flex items-center gap-4 mb-6">
                    <div className="w-16 h-16 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-300 font-bold text-xl">DS</div>
                    <div>
                        <h4 className="font-bold text-lg text-slate-800 dark:text-white">Dr. Smith</h4>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Global Administrator</p>
                    </div>
                </div>
                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Email Address</label>
                        <input type="text" value="dr.smith@clinicalflow.com" disabled className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-3 py-2 text-sm text-slate-600 dark:text-slate-300" />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Role</label>
                        <input type="text" value="Super Admin" disabled className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-3 py-2 text-sm text-slate-600 dark:text-slate-300" />
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center gap-2 mt-4 py-2 border border-rose-200 dark:border-rose-900/50 text-rose-600 dark:text-rose-400 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20 text-sm font-medium transition-colors"
                    >
                        <LogOut className="w-4 h-4" /> Sign Out
                    </button>
                </div>
            </Modal>

            <Modal isOpen={helpOpen} onClose={() => setHelpOpen(false)} title="Help Center">
                <div className="prose prose-sm prose-slate dark:prose-invert">
                    <p>Welcome to the ClinicalFlow Help Center. Here are some quick guides:</p>
                    <ul className="space-y-2 list-disc pl-5">
                        <li><strong>Risk Monitor:</strong> Detailed overview of site risk profiles. High risk sites are flagged automatically.</li>
                        <li><strong>Data Ingestion:</strong> Drag and drop your Excel exports to update the dataset.</li>
                        <li><strong>Agent Copilot:</strong> Use the AI chat to ask questions like "Which sites have the most SAEs?"</li>
                    </ul>
                    <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
                        <p className="text-blue-800 dark:text-blue-300 font-medium">Need Support?</p>
                        <p className="text-blue-600 dark:text-blue-400 text-xs mt-1">Contact support@clinicalflow.com for technical assistance.</p>
                    </div>
                </div>
            </Modal>

            <Modal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} title="App Settings">
                <div className="space-y-6">
                    <div>
                        <h4 className="text-sm font-semibold text-slate-800 dark:text-white mb-2">Notifications</h4>
                        <div className="flex items-center justify-between py-2 border-b border-slate-50 dark:border-slate-800">
                            <span className="text-sm text-slate-600 dark:text-slate-300">Email Alerts</span>
                            <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                                <input type="checkbox" name="toggle" id="toggle1" className="toggle-checkbox absolute block w-5 h-5 rounded-full bg-white border-4 appearance-none cursor-pointer border-slate-300 checked:right-0 checked:border-blue-600" defaultChecked />
                                <label htmlFor="toggle1" className="toggle-label block overflow-hidden h-5 rounded-full bg-slate-300 cursor-pointer checked:bg-blue-600"></label>
                            </div>
                        </div>
                        <div className="flex items-center justify-between py-2">
                            <span className="text-sm text-slate-600 dark:text-slate-300">Browser Push</span>
                            <button className="text-xs text-blue-600 dark:text-blue-400 font-medium hover:underline">Enable</button>
                        </div>
                    </div>

                    <div>
                        <h4 className="text-sm font-semibold text-slate-800 dark:text-white mb-2">Appearance</h4>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setDarkMode(false)}
                                className={`flex-1 py-2 text-xs font-medium border rounded-lg transition-colors ${!darkMode ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 dark:border-slate-700 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-slate-400'}`}
                            >
                                Light
                            </button>
                            <button
                                onClick={() => setDarkMode(true)}
                                className={`flex-1 py-2 text-xs font-medium border rounded-lg transition-colors ${darkMode ? 'border-blue-500 bg-slate-800 text-white' : 'border-slate-200 dark:border-slate-700 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-slate-400'}`}
                            >
                                Dark (Beta)
                            </button>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                        <p className="text-xs text-slate-400 text-center">Version 3.4.0 (Build 20251228)</p>
                    </div>
                </div>
            </Modal>

        </div>
    );
};


export default AppLayout;
