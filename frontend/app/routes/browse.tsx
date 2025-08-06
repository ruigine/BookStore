import { useState } from "react";
import { Slider } from "../components/ui/slider";

export default function BrowseBooks() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 100]);

  const handleGenreClick = (genre) => {
    setSelectedGenre(prev => (prev === genre ? null : genre));
  };

  return (
    <div className="grid grid-cols-24 lg:grid-cols-6 gap-4">
      <div className="col-span-11 lg:col-span-2 m-5 relative select-none">
        <div
          className="space-y-8 px-6 py-12 my-5 mx-2.5 relative"
          style={{
            aspectRatio: "768 / 1064",
            borderStyle: "solid",
            borderWidth: "40px",
            borderImageSource: "url('/images/vintage-frame.png')",
            borderImageSlice: "100 fill",
            borderImageRepeat: "stretch",
            borderImageOutset: 0,
            borderImageWidth: 1,
            backgroundColor: "#fdf8eb",
          }}
        >
          <div className="col-span-13 lg:col-span-4">
          <h1 className="text-5xl text-center font-[Great_Vibes]">Filters</h1>
        </div>
          <div>
            <h2 className="text-lg mb-2 font-[Eagle_Lake]">I. What are you looking for?</h2>
            <div className="relative w-full bg-[#FFFAF0] shadow-sm">
              <input
                type="text"
                placeholder="Search by title, author, ISBN..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pr-20 px-4 py-2 bg-transparent text-[#5B4636] placeholder-[#A89B87] italic font-serif focus:outline-none"
              />
              <button
                type="submit"
                className="absolute top-0 right-0 h-full px-4 py-2 text-[#5B4636] font-serif italic bg-[#FFFAF0] hover:bg-[#f3e8d7] transition-colors"
              >
                Search
              </button>
            </div>
          </div>

          <div>
            <h2 className="text-lg mb-2 font-[Eagle_Lake]">II. Genre</h2>
            <div className="space-y-2 font-serif text-[#5B4636]">
              {["Fantasy", "Mystery", "Romance", "Sci-Fi", "Non-fiction"].map((genre, i) => {
                const letter = String.fromCharCode(97 + i); // 'a', 'b', ...
                const isSelected = selectedGenre === genre;

                return (
                  <div className="ml-3">
                    <label
                      key={i}
                      className={`cursor-pointer transition
                        ${isSelected ? "text-[#3b2f23] italic underline" : "text-[#5B4636]"}`}
                    >
                      <input
                        type="radio"
                        name="genre"
                        value={genre}
                        className="hidden"
                        checked={isSelected}
                        onChange={() => setSelectedGenre(genre)}
                        onClick={() => handleGenreClick(genre)}
                      />
                      <span
                        className={`mr-2 p-1 text-center  border-[#CBB994] rounded-full text-sm italic
                          ${isSelected ? "bg-[#f5eee3] font-bold shadow-sm" : "bg-[#f3e9d5]"}`}
                      >
                        {letter}.
                      </span>
                      {genre}
                    </label>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-lg mb-2 font-[Eagle_Lake]">III. Price Range</h2>
            <div className="ml-8 mb-2">
              ${priceRange[0]} – ${priceRange[1]}
            </div>
            <Slider
              defaultValue={priceRange}
              min={1}
              max={100}
              step={1}
              onValueChange={(newRange) => setPriceRange([newRange[0], newRange[1]])}
            />
          </div>
        </div>
      </div>
      <div className="col-span-13 lg:col-span-4">
          <h1 className="text-xl font-semibold text-center mt-9">Browse Books</h1>
      </div>
    </div>
  );
}
