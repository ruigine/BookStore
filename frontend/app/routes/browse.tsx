import { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router";
import BookFilters from "../components/bookfilters";
import { SERVICE_URLS } from "../src/constants";
import { Menu, Search, ChevronUp, ChevronDown } from "lucide-react";

import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "../components/ui/sheet";

export default function BrowseBooks() {
  const [searchParams, setSearchParams] = useSearchParams();

  const searchTerm = searchParams.get("search") || "";
  const selectedGenre = searchParams.get("genre") || null;
  const minPrice = parseInt(searchParams.get("min_price") || "0", 10);
  const maxPrice = parseInt(searchParams.get("max_price") || "100", 10);
  const priceRange: [number, number] = [minPrice, maxPrice];

  const [books, setBooks] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const [opened, setOpened] = useState(false);

  const scrollAttached = useRef(false);

  const handleScroll = () => {
    const scrollTop = window.scrollY;
    const windowHeight = window.innerHeight;
    const fullHeight = document.documentElement.scrollHeight;
    
    if (scrollTop + windowHeight >= fullHeight - 5) {
      if (scrollAttached.current) {
        window.removeEventListener("scroll", handleScroll);
        scrollAttached.current = false;
      }

      setPage((prev) => prev + 1);
    }
  };

  useEffect(() => {
    setPage(1);
    setHasMore(true);
  }, [searchParams]);

  useEffect(() => {
    const url = `${SERVICE_URLS.BOOKS}/books?${searchParams.toString()}&page=${page}`;

    const fetchBooks = async () => {  
      try {
        if (page == 1 || hasMore) {
          const response = await fetch(url);
  
          if (!response.ok) throw new Error("Failed to fetch");
          const data = await response.json();
          
          if (!scrollAttached.current) {
            window.addEventListener("scroll", handleScroll);
            scrollAttached.current = true;
          }

          setBooks(prevBooks =>
            page === 1 ? data.data : [...prevBooks, ...data.data]
          );

          setHasMore(data.pagination["has_more"])
          
          console.log(url, data);
        }
      } catch (err) {
        console.error("Error fetching books:", err);
      }
    };

    fetchBooks();
  }, [searchParams, page]);

  return (
    <div className="grid md:grid-cols-24 lg:grid-cols-9 gap-4">
      <div className="hidden md:block md:col-span-11 lg:col-span-3 m-5 relative select-none">
        {!opened && (
          <div className="sticky top-15 left-0 -mt-5">
            <BookFilters
              searchTerm={searchTerm}
              selectedGenre={selectedGenre}
              priceRange={priceRange}
              onChangeFilters={(updated) => {
                setSearchParams((prev) => {
                  const newParams = new URLSearchParams(prev);

                  if ("searchTerm" in updated) {
                    updated.searchTerm?.trim()
                      ? newParams.set("search", updated.searchTerm)
                      : newParams.delete("search");
                  }

                  if ("selectedGenre" in updated) {
                    updated.selectedGenre
                      ? newParams.set("genre", updated.selectedGenre)
                      : newParams.delete("genre");
                  }

                  if ("priceRange" in updated) {
                    const [min, max] = updated.priceRange!;
                    newParams.set("min_price", min.toString());
                    newParams.set("max_price", max.toString());
                  }

                  return newParams;
                });

              }}
            />
          </div>
        )}
      </div>

      <div className="col-span-13 lg:col-span-6">
        <Sheet onOpenChange={setOpened}>
          <div 
            className="md:hidden pl-10 py-3 w-full sticky top-13 z-40 text-white"
            style={{
              backgroundImage: "url('/images/green-noise.png')",
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          >
            <SheetTrigger
              className="flex items-center gap-1 cursor-pointer hover:underline hover:italic w-fit select-none"
              onClick={() => setOpened(!opened)}
            >
              <span>Filters</span>
              {opened ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </SheetTrigger>
          </div>

          <SheetContent side="left" className="h-[110vh]"
            style={{
              backgroundImage: "url('/images/paper.jpg')",
              backgroundSize: "cover",
              backgroundPosition: "center",
            }}
          >
            <SheetHeader className="hidden">
              <SheetTitle>Filters</SheetTitle>
              <SheetDescription>
                Adjust your search filters here
              </SheetDescription>
            </SheetHeader>

            <div className="overflow-y-auto">
              <BookFilters
                searchTerm={searchTerm}
                selectedGenre={selectedGenre}
                priceRange={priceRange}
                onChangeFilters={(updated) => {
                  setSearchParams((prev) => {
                    const newParams = new URLSearchParams(prev);
                    
                    if ("searchTerm" in updated) {
                      updated.searchTerm?.trim()
                      ? newParams.set("search", updated.searchTerm)
                      : newParams.delete("search");
                    }
                    
                    if ("selectedGenre" in updated) {
                      updated.selectedGenre
                      ? newParams.set("genre", updated.selectedGenre)
                      : newParams.delete("genre");
                    }
                    
                    if ("priceRange" in updated) {
                      const [min, max] = updated.priceRange!;
                      newParams.set("min_price", min.toString());
                      newParams.set("max_price", max.toString());
                    }
                    
                    return newParams;
                  });
                }}
              />
            </div>
          </SheetContent>
        </Sheet>

        <h1 className="text-4xl text-center mt-10 mb-6 font-[Great_Vibes] text-[#5B4636]">— Browse Books —</h1>

        {Array.isArray(books) && books.length > 0 ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 px-4">
            {books.map((book: any) => (
              <Link to={`/books/${book.book_id}`}
                key={book.book_id}
                className="group text-center text-sm border border-[#eedab8] rounded-xl p-4 hover:shadow-md transition-all"
              >
                <div className="w-max-full w-[140px] h-[200px] mb-6 [perspective:1000px] mx-auto">
                  <div className="h-full w-full relative transition-transform duration-500 group-hover:rotate-y-[18deg] group-hover:scale-[1.04] transform-style-preserve-3d">

                    {/* Book Face */}
                    <img
                      src={book.url}
                      alt={book.title}
                      className="h-full w-full object-cover rounded-md group-hover:rounded-tr-md group-hover:rounded-br-md group-hover:rounded-tl-none group-hover:rounded-bl-none group-hover:shadow-xl relative z-10 transition-all duration-500"
                    />

                    {/* Spine */}
                    <div
                      className="absolute top-0 -left-[9px] h-full w-[9px] z-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-none"
                      style={{
                        backgroundImage: `url(${book.url})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'left center',
                        filter: 'brightness(0.85) contrast(1.05)',
                      }}
                    />

                    {/* highlight */}
                    <div className="absolute left-0 top-0 h-full w-[2px] bg-white/10 rounded-none pointer-events-none z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  </div>
                </div>

                <h2
                  className="text-[#5B4636] font-semibold text-[1rem] truncate px-2 group-hover:underline"
                  title={book.title}
                >
                  {book.title}
                </h2>
                <p className="italic text-[0.90rem] text-stone-500 mb-1 px-2">by {book.authors}</p>
                <p className="text-sm text-green-700">${book.price}</p>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-center mt-6 text-gray-500">No books found.</p>
        )}
      </div>
    </div>
  );
}
