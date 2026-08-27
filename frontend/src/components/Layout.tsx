import { Link, NavLink } from "react-router-dom";
import { ChevronDown, FileText, KeyRound, LogOut, Search } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "text-sm font-medium transition-colors",
    isActive ? "text-primary" : "text-muted-foreground hover:text-foreground",
  );

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="relative border-b border-border/80 bg-card/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-8">
            <Link to={user ? "/" : "/login"} className="font-display text-lg font-bold tracking-tight text-foreground">
              Secure Keyword
            </Link>
            {user ? (
              <nav className="hidden items-center gap-6 md:flex">
                <NavLink to="/documents" className={navLinkClass}>
                  Documents
                </NavLink>
                <NavLink to="/search" className={navLinkClass}>
                  Search
                </NavLink>
                {user.role === "ADMIN" ? (
                  <NavLink to="/admin" className={navLinkClass}>
                    Admin
                  </NavLink>
                ) : null}
              </nav>
            ) : null}
          </div>

          {user ? (
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2 md:hidden">
                    Menu
                    <ChevronDown className="h-3.5 w-3.5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52">
                  <DropdownMenuLabel className="font-normal">
                    <div className="truncate text-sm font-medium">{user.email}</div>
                    <Badge variant="secondary" className="mt-1">
                      {user.role}
                    </Badge>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/documents" className="cursor-pointer">
                      <FileText className="mr-2 h-4 w-4" />
                      Documents
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/search" className="cursor-pointer">
                      <Search className="mr-2 h-4 w-4" />
                      Search
                    </Link>
                  </DropdownMenuItem>
                  {user.role === "ADMIN" ? (
                    <DropdownMenuItem asChild>
                      <Link to="/admin" className="cursor-pointer">
                        <KeyRound className="mr-2 h-4 w-4" />
                        Admin
                      </Link>
                    </DropdownMenuItem>
                  ) : null}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => void signOut()}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="hidden gap-2 md:inline-flex">
                    <span className="max-w-[180px] truncate text-sm">{user.email}</span>
                    <Badge variant="secondary">{user.role}</Badge>
                    <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => void signOut()}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ) : null}
        </div>
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px origin-left scale-x-100 bg-gradient-to-r from-transparent via-primary/40 to-transparent animate-header-line" />
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">{children}</main>
    </div>
  );
}
