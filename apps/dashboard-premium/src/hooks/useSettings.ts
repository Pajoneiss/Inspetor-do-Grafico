'use client';

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';

// Settings types
export interface Settings {
    // Visual
    theme: 'dark' | 'light';
    accentColor: 'green' | 'cyan' | 'purple' | 'orange';
    fontSize: 'small' | 'medium' | 'large';
    compactMode: boolean;
    animations: boolean;

    // Language & Locale
    language: 'pt' | 'en';
    currency: 'USD' | 'BRL' | 'EUR' | 'GBP';
    decimalPrecision: 2 | 4 | 6 | 8;
    timezone: 'auto' | 'UTC' | 'America/Sao_Paulo' | 'America/New_York' | 'Europe/London';
    dateFormat: 'DD/MM' | 'MM/DD';

    // Data & Performance
    refreshRate: 5 | 10 | 30 | 60;
    chartDefaultPeriod: '24H' | '7D' | '30D' | 'ALL';
    showClosedPositions: boolean;
    maxAiThoughts: number;

    // Notifications
    soundAlerts: boolean;
    browserNotifications: boolean;
    alertOnLossPercent: number;
    alertOnProfitPercent: number;

    // Trading Display
    showEntryMarkers: boolean;
    showSlTpLines: boolean;
    pnlColorMode: 'standard' | 'colorblind';
    hideSensitiveData: boolean;
}

// Default settings
export const defaultSettings: Settings = {
    // Visual
    theme: 'dark',
    accentColor: 'green',
    fontSize: 'medium',
    compactMode: false,
    animations: true,

    // Language & Locale
    language: 'pt',
    currency: 'USD',
    decimalPrecision: 2,
    timezone: 'auto',
    dateFormat: 'DD/MM',

    // Data & Performance
    refreshRate: 5,
    chartDefaultPeriod: '24H',
    showClosedPositions: false,
    maxAiThoughts: 5,

    // Notifications
    soundAlerts: true,
    browserNotifications: false,
    alertOnLossPercent: 5,
    alertOnProfitPercent: 10,

    // Trading Display
    showEntryMarkers: true,
    showSlTpLines: true,
    pnlColorMode: 'standard',
    hideSensitiveData: false,
};

// Settings context
interface SettingsContextType {
    settings: Settings;
    updateSetting: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
    resetSettings: () => void;
}

const SettingsContext = createContext<SettingsContextType | null>(null);

// Provider component
export function SettingsProvider({ children }: { children: ReactNode }) {
    const [settings, setSettings] = useState<Settings>(defaultSettings);
    const [mounted, setMounted] = useState(false);

    // Load settings from localStorage on mount
    useEffect(() => {
        setMounted(true);
        const saved = localStorage.getItem('dashboard-settings');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                setSettings({ ...defaultSettings, ...parsed });
            } catch (e) {
                console.error('Failed to parse settings:', e);
            }
        }
    }, []);

    // Save settings to localStorage when they change
    useEffect(() => {
        if (mounted) {
            localStorage.setItem('dashboard-settings', JSON.stringify(settings));

            // Apply theme
            document.documentElement.classList.toggle('light-theme', settings.theme === 'light');

            // Apply accent color
            document.documentElement.setAttribute('data-accent', settings.accentColor);

            // Apply font size
            document.documentElement.setAttribute('data-font-size', settings.fontSize);

            // Apply compact mode
            document.documentElement.classList.toggle('compact-mode', settings.compactMode);

            // Apply animations
            document.documentElement.classList.toggle('no-animations', !settings.animations);
        }
    }, [settings, mounted]);

    const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const resetSettings = () => {
        setSettings(defaultSettings);
        localStorage.removeItem('dashboard-settings');
    };

    return (
        <SettingsContext.Provider value= {{ settings, updateSetting, resetSettings }
}>
    { children }
    </SettingsContext.Provider>
  );
}

// Hook to use settings
export function useSettings() {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
}

// Standalone hook for use outside provider (fallback)
export function useSettingsStandalone() {
    const [settings, setSettings] = useState<Settings>(defaultSettings);

    useEffect(() => {
        const saved = localStorage.getItem('dashboard-settings');
        if (saved) {
            try {
                setSettings({ ...defaultSettings, ...JSON.parse(saved) });
            } catch (e) {
                console.error('Failed to parse settings:', e);
            }
        }
    }, []);

    const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
        setSettings(prev => {
            const newSettings = { ...prev, [key]: value };
            localStorage.setItem('dashboard-settings', JSON.stringify(newSettings));
            return newSettings;
        });
    };

    const resetSettings = () => {
        setSettings(defaultSettings);
        localStorage.removeItem('dashboard-settings');
    };

    return { settings, updateSetting, resetSettings };
}
