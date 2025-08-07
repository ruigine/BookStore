import { Link, useLocation } from "react-router";
import { Menu } from "lucide-react";
import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../components/ui/sheet";

export default function NavBar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="w-full bg-[#FFFAED] py-4 px-6 font-serif text-sm tracking-wide sticky top-0 shadow-[0_10px_15px_-3px_rgba(0,0,0,0.035),_0_4px_6px_-4px_rgba(0,0,0,0.025)] z-50">
      <nav className="md:px-3 mx-auto flex items-center justify-between relative">

        {/* Left: Full nav (md+) */}
        <div className="hidden md:flex gap-6 text-stone-600 flex-1 justify-start">
          <Link to="/browse" className={`hover:underline hover:italic ${useLocation().pathname === "/browse" && "italic underline text-green-800"}`}>
            I. Browse books
          </Link>

          <Link to="/orders" className={`hover:underline hover:italic ${useLocation().pathname === "/orders" && "italic underline text-green-800"}`}>
            II. My orders
          </Link>
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
                backgroundImage: "url('/images/green-noise.png')",
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

                <Link
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
                </Link>
              </nav>
            </SheetContent>
          </Sheet>
        </div>

        {/* Center logo (always) */}
        <div className="absolute left-1/2 transform -translate-x-1/2 text-xl uppercase tracking-widest font-medium">
          Bookstore
        </div>

        {/* Right: Full nav (md+) */}
        <div className="hidden md:flex gap-6 text-stone-600 flex-1 justify-end">
          <Link to="/login" className={`block group transition-all ${
            useLocation().pathname === "/login"
              ? "underline decoration-gray-300e"
              : "hover:underline hover:italic decoration-gray-300"
          }`}>III. Log in</Link>
        </div>

        {/* Right: Mobile (below md) */}
        <div className="flex md:hidden flex-1 justify-end gap-4 text-stone-600">
          <Link to="/login" className={`block group transition-all ${
            useLocation().pathname === "/login"
              ? "underline decoration-gray-300e"
              : "hover:underline hover:italic decoration-gray-300"
          }`}>Log in</Link>
        </div>

      </nav>
    </header>
  );
}