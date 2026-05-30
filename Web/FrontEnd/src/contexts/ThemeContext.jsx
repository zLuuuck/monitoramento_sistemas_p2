import { createContext, useState, useEffect, useContext } from 'react';

const ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  // Carrega preferência salva ou sistema
const getInitialTheme = () => {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark') return 'dark';
    if (saved === 'light') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

const [theme, setTheme] = useState(getInitialTheme);

useEffect(() => {
    const root = document.documentElement;
    // ADICIONA a classe 'dark' APENAS quando o tema for 'dark'
    if (theme === 'dark') {
        root.classList.add('dark');
    } else {
        root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
}, [theme]);

const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
};

return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
        {children}
    </ThemeContext.Provider>
    );
};