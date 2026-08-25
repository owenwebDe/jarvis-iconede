import React, { useState, useEffect } from 'react';
import { Button } from './components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-md">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary font-bold text-primary-foreground">
              O
            </div>
            <span className="font-bold tracking-tight">IconEdge</span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={toggleTheme}>
              {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </Button>
            <Button size="sm">Get Started</Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="container mx-auto px-4 py-16 sm:px-8">
        <div className="mx-auto max-w-3xl text-center space-y-6">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl">
            Next-Gen Modular React Architecture
          </h1>
          <p className="text-lg text-muted-foreground">
            Engineered with Shadcn UI, Luxoria Luxury Tokens, and Surgical Component Editing.
          </p>
          <div className="flex justify-center gap-4">
            <Button size="lg">Explore Platform</Button>
            <Button variant="outline" size="lg">Documentation</Button>
          </div>
        </div>
      </main>
    </div>
  );
}
