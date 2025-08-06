import { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import BookFilters from "../components/bookfilters";
import { SERVICE_URLS } from "../src/constants";

export default function BrowseBooks() {
  const [searchParams, setSearchParams] = useSearchParams();

  const searchTerm = searchParams.get("search") || "";
  const selectedGenre = searchParams.get("genre") || null;
  const minPrice = parseInt(searchParams.get("min_price") || "0", 10);
  const maxPrice = parseInt(searchParams.get("max_price") || "100", 10);
  const priceRange: [number, number] = [minPrice, maxPrice];

  const [books, setBooks] = useState([]);

  useEffect(() => {
    const url = `${SERVICE_URLS.BOOKS}/books?${searchParams.toString()}`;

    const fetchBooks = async () => {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        setBooks(data.data);
        console.log(data);
      } catch (err) {
        console.error("Error fetching books:", err);
      }
    };

    fetchBooks();
  }, [searchParams]);

  return (
    <div className="grid grid-cols-24 lg:grid-cols-6 gap-4">
      <div className="col-span-11 lg:col-span-2 m-5 relative select-none">
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

      <div className="col-span-13 lg:col-span-4">
        <h1 className="text-4xl text-center mt-9 font-[Great_Vibes]">— Browse Books —</h1>

        {Array.isArray(books) && books.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 p-6">
            {books.map((book: any) => (
              <div
                key={book.book_id}
                className="group p-4 text-center text-sm text-stone-700 border border-[#eedab8] rounded-xl "
              >
                <div className="relative w-[140px] h-[200px] mb-6 [perspective:1000px] mx-auto">
                  <div className="h-full w-full relative transition-transform duration-500 group-hover:rotate-y-[18deg] group-hover:scale-[1.04] transform-style-preserve-3d">

                    {/* Book Face */}
                    <img
                      src={book.url}
                      alt={book.title}
                      className="h-full w-full object-cover hover:rounded-tr-md hover:rounded-br-md rounded-tl-none rounded-bl-none hover:shadow-xl relative z-10 transition-all duration-500"
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
                  className="mb-2 truncate group-hover:underline"
                  title={book.title}
                >
                  {book.title}
                </h2>
                <p className="italic text-[0.90rem] text-stone-500 mb-1">by {book.authors}</p>
                <p className="text-sm mb-2 text-green-700">${book.price}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center mt-6 text-gray-500">No books found.</p>
        )}
      </div>
    </div>
  );
}
