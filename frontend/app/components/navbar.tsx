import { Link, useLocation } from "react-router";
import { Menu, Search } from "lucide-react";
import { useState, useEffect } from "react";

export default function NavBar() {
  return (
    <header className="w-full bg-[#FFFAED] py-4 px-6 font-serif text-sm tracking-wide sticky top-0 shadow-[0_10px_15px_-3px_rgba(0,0,0,0.035),_0_4px_6px_-4px_rgba(0,0,0,0.025)] z-50">
      <nav className="md:px-3 mx-auto flex items-center justify-between relative">

        {/* Left: Full nav (shown on md+) */}
        <div className="hidden md:flex gap-6 text-stone-600 flex-1 justify-start">
          <Link to="/browse" className="hover:underline hover:italic">I. Browse books</Link>
          <Link to="/orders" className="hover:underline hover:italic">II. My orders</Link>
        </div>

        {/* Left: Mobile menu icon (shown below md) */}
        <div className="flex md:hidden flex-1 justify-start text-stone-600">
          <button className="hover:underline hover:italic flex items-center gap-2 cursor-pointer">
            <Menu size={18} /> Menu
          </button>
        </div>

        {/* Center logo (always visible) */}
        <div className="absolute left-1/2 transform -translate-x-1/2 text-xl uppercase tracking-widest font-medium">
          Bookstore
        </div>

        {/* Right: Full nav (shown on md+) */}
        <div className="hidden md:flex gap-6 text-stone-600 flex-1 justify-end">
          <Link to="/account" className="hover:underline hover:italic">III. Account</Link>
        </div>

        {/* Right: Mobile icons (shown below md) */}
        <div className="flex md:hidden flex-1 justify-end gap-4 text-stone-600">
          <Link to="/account" className="hover:underline hover:italic">Account</Link>
        </div>

      </nav>
    </header>
  );
}
