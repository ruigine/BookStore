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
        setBooks(data.books); // or data depending on shape
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
              if (updated.searchTerm !== undefined)
                newParams.set("search", updated.searchTerm);
              if (updated.selectedGenre !== undefined)
                updated.selectedGenre
                  ? newParams.set("genre", updated.selectedGenre)
                  : newParams.delete("genre");
              if (updated.priceRange !== undefined) {
                newParams.set("min_price", updated.priceRange[0].toString());
                newParams.set("max_price", updated.priceRange[1].toString());
              }
              return newParams;
            });
          }}
        />
      </div>

      <div className="col-span-13 lg:col-span-4">
        <h1 className="text-xl font-semibold text-center mt-9">Browse Books</h1>
        {/* Book list here */}
      </div>
    </div>
  );
}
