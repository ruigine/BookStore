import { useState, useEffect } from "react";
import BookFilters from "../components/bookfilters";
import { SERVICE_URLS } from "../src/constants";

export default function BrowseBooks() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 100]);

  // Mock state to hold fetched data
  const [books, setBooks] = useState([]);

  useEffect(() => {
    const params = new URLSearchParams();

    if (selectedGenre) params.set("genre", selectedGenre);
    if (searchTerm.trim()) params.set("search", searchTerm.trim());
    if (priceRange[0] !== 0) params.set("min_price", priceRange[0].toString());
    if (priceRange[1] !== 100) params.set("max_price", priceRange[1].toString());

    const url = `${SERVICE_URLS.BOOKS}/books?${params.toString()}`;

    const fetchBooks = async () => {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        setBooks(data.books); // or `data` depending on your API shape
        console.log(data)
      } catch (err) {
        console.error("Error fetching books:", err);
      }
    };

    fetchBooks();
  }, [searchTerm, selectedGenre, priceRange]);

  return (
    <div className="grid grid-cols-24 lg:grid-cols-6 gap-4">
      <div className="col-span-11 lg:col-span-2 m-5 relative select-none">
        <BookFilters
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          selectedGenre={selectedGenre}
          setSelectedGenre={setSelectedGenre}
          priceRange={priceRange}
          setPriceRange={setPriceRange}
        />
      </div>

      <div className="col-span-13 lg:col-span-4">
        <h1 className="text-xl font-semibold text-center mt-9">Browse Books</h1>

        {/* Display results
        <ul className="mt-4 space-y-2 px-4">
          {books.map((book, i) => (
            <li key={i} className="border p-2 shadow-sm rounded">
              <strong>{book.title}</strong> by {book.author}
              <div>${book.price}</div>
            </li>
          ))}
        </ul> */}
      </div>
    </div>
  );
}
