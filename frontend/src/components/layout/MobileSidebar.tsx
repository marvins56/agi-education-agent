'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'
import { useAuth } from '@/hooks/useAuth'
import {
  Menu,
  BookOpen,
  MessageSquare,
  BarChart3,
  UserCircle,
  ClipboardCheck,
  Route,
  LogOut,
  FlaskConical,
  Mic,
  Timer,
  FileText,
  Home,
  X
} from 'lucide-react'

const navItems = [
  { href: '/', label: 'Dashboard', icon: Home },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/voice', label: 'Voice', icon: Mic },
  { href: '/timeline', label: 'Timeline', icon: Timer },
  { href: '/sources', label: 'Sources', icon: FileText },
  { href: '/profile', label: 'Profile', icon: UserCircle },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/assessments', label: 'Assessments', icon: ClipboardCheck },
  { href: '/learning-path', label: 'Learning Path', icon: Route },
  { href: '/library', label: 'Library', icon: BookOpen },
  { href: '/rag-test', label: 'RAG Test', icon: FlaskConical }
]

interface MobileSidebarProps {
  className?: string
}

export function MobileSidebar({ className }: MobileSidebarProps) {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()
  const { user, logout } = useAuth()

  const handleLinkClick = () => {
    setIsOpen(false)
  }

  const handleLogout = () => {
    logout()
    setIsOpen(false)
  }

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          className={cn("md:hidden h-9 w-9 p-0", className)}
          aria-label="Toggle menu"
        >
          <Menu className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 p-0">
        <div className="flex h-full flex-col bg-background">
          {/* Header */}
          <SheetHeader className="flex h-14 items-center justify-between border-b px-4">
            <div className="flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-primary" />
              <SheetTitle className="text-lg font-bold">EduAGI</SheetTitle>
            </div>
            <Button
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => setIsOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </SheetHeader>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 p-4">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-muted-foreground px-2">
                MAIN
              </p>
              {navItems.slice(0, 5).map((item) => {
                const Icon = item.icon
                const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={handleLinkClick}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                    {active && <Badge variant="secondary" className="ml-auto">Active</Badge>}
                  </Link>
                )
              })}
            </div>

            <div className="space-y-1 pt-4">
              <p className="text-xs font-semibold text-muted-foreground px-2">
                TOOLS
              </p>
              {navItems.slice(5).map((item) => {
                const Icon = item.icon
                const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={handleLinkClick}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                    {active && <Badge variant="secondary" className="ml-auto">Active</Badge>}
                  </Link>
                )
              })}
            </div>
          </nav>

          {/* User section */}
          <div className="border-t p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <UserCircle className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user?.name || 'User'}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user?.email}
                </p>
              </div>
            </div>
            
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full justify-start"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}