import { useEffect, useState } from "react"
import { useParams } from "react-router"
import { SERVICE_URLS } from "../src/constants"
import { Loader } from "lucide-react"

export default function BookDetail() {
  const { id } = useParams()
  const [book, setBook] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBook = async () => {
      const res = await fetch(`${SERVICE_URLS.BOOKS}/books/${id}`)
      const data = await res.json()
      if (res.ok) setBook(data.data)
      setLoading(false)
    }

    fetchBook()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh] text-stone-600">
        <Loader className="animate-spin mr-2" />
        Loading book details...
      </div>
    )
  }

  if (!book) {
    return <div className="text-center text-red-600 mt-10">Book not found.</div>
  }

  return (
    <div className="min-h-screen grid grid-cols-2 font-serif text-[#5B4636] bg-[#fdf9f1]">
      {/* Left Column – Book Image */}
      <div className="relative flex justify-center bg-gradient-to-r from-[#fcf6e8] to-[#fefaf2] pl-20 pr-32 py-20 after:absolute after:top-[-40px] after:bottom-[-40px] after:right-0 after:w-[8px] after:bg-gradient-to-b after:from-black/30 after:via-black/10 after:shadow-[0_0_35px_35px_rgba(0,0,0,0.1)] after:to-black/30 after:blur-md after:rounded-full">
        <div className="group max-h-[500px] mb-6 [perspective:1000px]">
            <div className="h-full w-full relative transition-transform duration-500 group-hover:rotate-y-[18deg] group-hover:scale-[1.04] transform-style-preserve-3d">
            {/* Book Face */}
            <img
                src={book.url}
                alt={book.title}
                className="h-full w-full object-cover hover:rounded-tr-md hover:rounded-br-md rounded-tl-none rounded-bl-none group-hover:shadow-xl relative z-10 transition-all duration-500"
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

            {/* Highlight line */}
            <div className="absolute left-0 top-0 h-full w-[2px] bg-white/10 rounded-none pointer-events-none z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            </div>
        </div>
        </div>
      {/* Right Column – Book Details */}
      <div className="flex flex-col justify-center pl-32 py-20 pr-20 font-serif bg-gradient-to-r from-[#f9f4ea] to-[#fef9ee]">
        {/* Decorative Title Block */}
        <div className="mx-auto relative pb-10 text-center w-full">
            <div className="flex items-center justify-center gap-4 mb-4 text-[#c5bca4] text-xl select-none">
              <span className="border-t border-[#c5bca4] w-10" />
                ❧
              <span className="border-t border-[#c5bca4] w-10" />
            </div>
            <h1 className="text-3xl tracking-widest font-bold text-[#5B4636]">
            {book.title.toUpperCase()}
            </h1>
            <p className="italic text-stone-500 mt-2">by {book.authors}</p>
        </div>

        {/* Sub Info Block */}
        <div className="text-center text-sm text-stone-400 uppercase tracking-wide mb-6">
            {book.format} · {book.genre}
        </div>

        {/* Price */}
        <p className="text-center text-xl text-[#5a7249] font-medium mb-8">${book.price}</p>

        {/* Details */}
        <div className="text-sm leading-relaxed space-y-2 text-stone-700 border-t border-b py-4 border-stone-300">
            <p><span className="font-medium">Publisher:</span> {book.publishers}</p>
            <p><span className="font-medium">ISBN:</span> {book.ISBN}</p>
            <p><span className="font-medium">Available Quantity:</span> {book.quantity}</p>
        </div>

        {/* Add to Cart */}
        <button className="cursor-pointer mx-auto mt-8 w-max px-8 py-2 bg-[#5a7249] text-white uppercase tracking-wider hover:bg-[#465b3a] transition">
            Add to Cart
        </button>

        {/* Description */}
        <div className="mt-10 px-2 text-[0.95rem] text-stone-700 leading-[1.75] italic">
            <p className="first-letter:text-3xl first-letter:font-serif first-letter:float-left first-letter:leading-none first-letter:pr-1">
            {book.description}
            </p>
        </div>
      </div>
    </div>
  )
}