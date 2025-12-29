'use client';

import { X, Sun, Moon, Palette, Type, Zap, Globe, DollarSign, Hash, Clock, Calendar, RefreshCw, BarChart2, Brain, Bell, Volume2, AlertTriangle, TrendingUp, Target, Eye, EyeOff, RotateCcw } from 'lucide-react';
import { Settings, defaultSettings } from '../hooks/useSettings';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    settings: Settings;
    updateSetting: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
    resetSettings: () => void;
}

// Toggle component
const Toggle = ({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) => (
    <label className="flex items-center justify-between cursor-pointer group">
        <span className="text-sm text-white/80 group-hover:text-white transition-colors">{label}</span>
        <button
            onClick={() => onChange(!checked)}
            className={`relative w-12 h-6 rounded-full transition-all duration-300 ${checked ? 'bg-primary' : 'bg-white/10'}`}
        >
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all duration-300 ${checked ? 'left-7' : 'left-1'}`} />
        </button>
    </label>
);

// Select component
const Select = <T extends string | number>({ value, onChange, options, label }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[]; label: string }) => (
    <label className="flex items-center justify-between">
        <span className="text-sm text-white/80">{label}</span>
        <select
            value={value}
            onChange={(e) => onChange(e.target.value as T)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:border-primary focus:outline-none"
        >
            {options.map(opt => (
                <option key={String(opt.value)} value={opt.value} className="bg-black">{opt.label}</option>
            ))}
        </select>
    </label>
);

// Slider component
const Slider = ({ value, onChange, min, max, label, suffix = '' }: { value: number; onChange: (v: number) => void; min: number; max: number; label: string; suffix?: string }) => (
    <label className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
            <span className="text-sm text-white/80">{label}</span>
            <span className="text-sm font-bold text-primary">{value}{suffix}</span>
        </div>
        <input
            type="range"
            min={min}
            max={max}
            value={value}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
        />
    </label>
);

// Section component
const Section = ({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) => (
    <div className="space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-widest">
            <Icon className="w-4 h-4" />
            {title}
        </div>
        <div className="space-y-3 pl-6">
            {children}
        </div>
    </div>
);

// Color picker
const ColorPicker = ({ value, onChange, label }: { value: string; onChange: (v: 'green' | 'cyan' | 'purple' | 'orange') => void; label: string }) => {
    const colors = [
        { id: 'green', color: '#00ff88', name: 'Green' },
        { id: 'cyan', color: '#00e5ff', name: 'Cyan' },
        { id: 'purple', color: '#a855f7', name: 'Purple' },
        { id: 'orange', color: '#f59e0b', name: 'Orange' },
    ] as const;

    return (
        <label className="flex items-center justify-between">
            <span className="text-sm text-white/80">{label}</span>
            <div className="flex gap-2">
                {colors.map(c => (
                    <button
                        key={c.id}
                        onClick={() => onChange(c.id)}
                        className={`w-6 h-6 rounded-full transition-all ${value === c.id ? 'ring-2 ring-white ring-offset-2 ring-offset-black scale-110' : 'hover:scale-110'}`}
                        style={{ backgroundColor: c.color }}
                        title={c.name}
                    />
                ))}
            </div>
        </label>
    );
};

export default function SettingsModal({ isOpen, onClose, settings, updateSetting, resetSettings }: SettingsModalProps) {
    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
            onClick={onClose}
        >
            <div
                className="bg-[#0a0a0a] border border-white/10 rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-4 duration-300"
                onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/5">
                    <h2 className="text-xl font-bold">Settings</h2>
                    <button onClick={onClose} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[calc(85vh-140px)] space-y-8">

                    {/* Visual Settings */}
                    <Section title="Visual" icon={Palette}>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-white/80">Theme</span>
                            <div className="flex bg-white/5 rounded-lg p-1">
                                <button
                                    onClick={() => updateSetting('theme', 'dark')}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-all ${settings.theme === 'dark' ? 'bg-primary text-black font-bold' : 'text-white/60 hover:text-white'}`}
                                >
                                    <Moon className="w-4 h-4" /> Dark
                                </button>
                                <button
                                    onClick={() => updateSetting('theme', 'light')}
                                    className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-all ${settings.theme === 'light' ? 'bg-primary text-black font-bold' : 'text-white/60 hover:text-white'}`}
                                >
                                    <Sun className="w-4 h-4" /> Light
                                </button>
                            </div>
                        </div>
                        <ColorPicker value={settings.accentColor} onChange={(v) => updateSetting('accentColor', v)} label="Accent Color" />
                        <Select
                            value={settings.fontSize}
                            onChange={(v) => updateSetting('fontSize', v as 'small' | 'medium' | 'large')}
                            options={[
                                { value: 'small', label: 'Small' },
                                { value: 'medium', label: 'Medium' },
                                { value: 'large', label: 'Large' },
                            ]}
                            label="Font Size"
                        />
                        <Toggle checked={settings.compactMode} onChange={(v) => updateSetting('compactMode', v)} label="Compact Mode" />
                        <Toggle checked={settings.animations} onChange={(v) => updateSetting('animations', v)} label="Animations" />
                    </Section>

                    {/* Language & Locale */}
                    <Section title="Language & Locale" icon={Globe}>
                        <Select
                            value={settings.language}
                            onChange={(v) => updateSetting('language', v as 'pt' | 'en')}
                            options={[
                                { value: 'pt', label: 'Português' },
                                { value: 'en', label: 'English' },
                            ]}
                            label="Language"
                        />
                        <Select
                            value={settings.currency}
                            onChange={(v) => updateSetting('currency', v as 'USD' | 'BRL' | 'EUR' | 'GBP')}
                            options={[
                                { value: 'USD', label: 'USD ($)' },
                                { value: 'BRL', label: 'BRL (R$)' },
                                { value: 'EUR', label: 'EUR (€)' },
                                { value: 'GBP', label: 'GBP (£)' },
                            ]}
                            label="Currency"
                        />
                        <Select
                            value={settings.decimalPrecision}
                            onChange={(v) => updateSetting('decimalPrecision', Number(v) as 2 | 4 | 6 | 8)}
                            options={[
                                { value: 2, label: '2 decimals' },
                                { value: 4, label: '4 decimals' },
                                { value: 6, label: '6 decimals' },
                                { value: 8, label: '8 decimals' },
                            ]}
                            label="Decimal Precision"
                        />
                        <Select
                            value={settings.timezone}
                            onChange={(v) => updateSetting('timezone', v as any)}
                            options={[
                                { value: 'auto', label: 'Auto (Local)' },
                                { value: 'UTC', label: 'UTC' },
                                { value: 'America/Sao_Paulo', label: 'São Paulo (BRT)' },
                                { value: 'America/New_York', label: 'New York (EST)' },
                                { value: 'Europe/London', label: 'London (GMT)' },
                            ]}
                            label="Timezone"
                        />
                        <Select
                            value={settings.dateFormat}
                            onChange={(v) => updateSetting('dateFormat', v as 'DD/MM' | 'MM/DD')}
                            options={[
                                { value: 'DD/MM', label: 'DD/MM/YYYY' },
                                { value: 'MM/DD', label: 'MM/DD/YYYY' },
                            ]}
                            label="Date Format"
                        />
                    </Section>

                    {/* Data & Performance */}
                    <Section title="Data & Performance" icon={Zap}>
                        <Select
                            value={settings.refreshRate}
                            onChange={(v) => updateSetting('refreshRate', Number(v) as 5 | 10 | 30 | 60)}
                            options={[
                                { value: 5, label: '5 seconds' },
                                { value: 10, label: '10 seconds' },
                                { value: 30, label: '30 seconds' },
                                { value: 60, label: '1 minute' },
                            ]}
                            label="Refresh Rate"
                        />
                        <Select
                            value={settings.chartDefaultPeriod}
                            onChange={(v) => updateSetting('chartDefaultPeriod', v as any)}
                            options={[
                                { value: '24H', label: '24 Hours' },
                                { value: '7D', label: '7 Days' },
                                { value: '30D', label: '30 Days' },
                                { value: 'ALL', label: 'All Time' },
                            ]}
                            label="Default Chart Period"
                        />
                        <Toggle checked={settings.showClosedPositions} onChange={(v) => updateSetting('showClosedPositions', v)} label="Show Closed Positions" />
                        <Slider value={settings.maxAiThoughts} onChange={(v) => updateSetting('maxAiThoughts', v)} min={3} max={20} label="Max AI Thoughts" />
                    </Section>

                    {/* Notifications */}
                    <Section title="Notifications" icon={Bell}>
                        <Toggle checked={settings.soundAlerts} onChange={(v) => updateSetting('soundAlerts', v)} label="Sound Alerts" />
                        <Toggle checked={settings.browserNotifications} onChange={(v) => updateSetting('browserNotifications', v)} label="Browser Notifications" />
                        <Slider value={settings.alertOnLossPercent} onChange={(v) => updateSetting('alertOnLossPercent', v)} min={1} max={20} label="Alert on Loss >" suffix="%" />
                        <Slider value={settings.alertOnProfitPercent} onChange={(v) => updateSetting('alertOnProfitPercent', v)} min={1} max={50} label="Alert on Profit >" suffix="%" />
                    </Section>

                    {/* Trading Display */}
                    <Section title="Trading Display" icon={BarChart2}>
                        <Toggle checked={settings.showEntryMarkers} onChange={(v) => updateSetting('showEntryMarkers', v)} label="Show Entry Markers" />
                        <Toggle checked={settings.showSlTpLines} onChange={(v) => updateSetting('showSlTpLines', v)} label="Show SL/TP Lines" />
                        <Select
                            value={settings.pnlColorMode}
                            onChange={(v) => updateSetting('pnlColorMode', v as 'standard' | 'colorblind')}
                            options={[
                                { value: 'standard', label: 'Standard (Green/Red)' },
                                { value: 'colorblind', label: 'Colorblind Friendly' },
                            ]}
                            label="PnL Color Mode"
                        />
                        <Toggle checked={settings.hideSensitiveData} onChange={(v) => updateSetting('hideSensitiveData', v)} label="Hide Sensitive Data" />
                    </Section>

                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-white/5 bg-white/[0.02]">
                    <button
                        onClick={resetSettings}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-white/60 hover:text-white transition-colors"
                    >
                        <RotateCcw className="w-4 h-4" />
                        Reset to Defaults
                    </button>
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 bg-primary text-black font-bold rounded-xl hover:opacity-90 transition-opacity"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
}
