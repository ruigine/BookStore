import { Link, useLocation } from "react-router";
import { Menu, User } from "lucide-react";
import { useState } from "react";
import { useAuth } from "~/context/authcontext";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../components/ui/sheet";

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "~/components/ui/dropdown-menu"

export default function NavBar() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();

  return (
    <header className="w-full py-4 px-6 font-serif text-sm tracking-wide sticky top-0 shadow-lg z-50" style={{ backgroundImage: "url('/images/paper.jpg')" }}>
      <nav className="md:px-3 mx-auto flex items-center justify-between relative">

        {/* Left: Full nav (md+) */}
        <div className="hidden md:flex gap-6 text-stone-600 flex-1 justify-start">
          <Link to="/browse" className={`hover:underline hover:italic ${useLocation().pathname === "/browse" && "italic underline text-green-800"}`}>
            I. Browse books
          </Link>

          {user && (<Link to="/orders" className={`hover:underline hover:italic ${useLocation().pathname === "/orders" && "italic underline text-green-800"}`}>
            II. My orders
          </Link>)}
        </div>

        {/* Left: Mobile menu icon (below md) */}
        <div className="flex md:hidden flex-1 justify-start">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <button className="hover:underline hover:italic flex items-center gap-2 cursor-pointer">
                <Menu size={18} /> Menu
              </button>
            </SheetTrigger>

            <SheetContent
              side="left"
              className="w-64 p-6 font-serif"
              style={{
                backgroundImage: "url('/images/paper.jpg')",
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            >
              <SheetHeader>
                <SheetTitle className="text-2xl uppercase text-center">Bookstore</SheetTitle>
              </SheetHeader>

              <nav className="space-y-6 font-serif text-[1.05rem]">
                <Link
                  to="/browse"
                  onClick={() => setOpen(false)}
                  className={`block group transition-all ${
                    useLocation().pathname === "/browse"
                      ? "underline decoration-gray-300"
                      : "hover:underline hover:italic decoration-gray-300"
                  }`}
                >
                  <div className="uppercase text-xs tracking-wider text-stone-600">Chapter I</div>
                  <div className="text-lg">Browse Books ---------- 1</div>
                </Link>

                {user && (<Link
                  to="/orders"
                  onClick={() => setOpen(false)}
                  className={`block group transition-all ${
                    useLocation().pathname === "/orders"
                      ? "underline decoration-gray-300e"
                      : "hover:underline hover:italic decoration-gray-300"
                  }`}
                >
                  <div className="uppercase text-xs tracking-wider text-stone-600">Chapter II</div>
                  <div className="text-lg">My Orders -------------- 2</div>
                </Link>)}
              </nav>
            </SheetContent>
          </Sheet>
        </div>

        {/* Center logo (always) */}
        <div className="absolute left-1/2 transform -translate-x-1/2 text-xl uppercase tracking-widest font-medium">
          Bookstore
        </div>
        
        {!user && (
        /* Right: Full nav (md+) */
        <div className="hidden md:flex gap-6 text-stone-600 flex-1 justify-end">
          <Link to="/login" className={`block group transition-all ${
            useLocation().pathname === "/login"
              ? "underline decoration-gray-300e"
              : "hover:underline hover:italic decoration-gray-300"
          }`}>II. Log in</Link>
        </div>
        )}

        {!user && (
        /* Right: Mobile (below md) */
        <div className="flex md:hidden flex-1 justify-end gap-4 text-stone-600">
          <Link to="/login" className={`block group transition-all ${
            useLocation().pathname === "/login"
              ? "underline decoration-gray-300e"
              : "hover:underline hover:italic decoration-gray-300"
          }`}>Log in</Link>
        </div>
        )}

        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2 text-green-800 focus:outline-none cursor-pointer">
                <User size={16} />
                <span>{user?.name || user?.email}</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="text-white"
              style={{
                backgroundImage: "url('/images/green-noise.png')",
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            >
              <DropdownMenuItem
                onClick={() => {
                  logout()
                }}
                className="cursor-pointer !text-white !bg-transparent hover:!bg-white/10"
              >
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </nav>
    </header>
  );
}