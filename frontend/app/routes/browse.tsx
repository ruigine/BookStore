import { useState } from "react";
import BookFilters from "../components/bookfilters";

export default function BrowseBooks() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 100]);

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
        {/* Book grid or list goes here */}
      </div>
    </div>
  );
}