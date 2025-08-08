import { useEffect, useState } from "react"
import { useParams } from "react-router"
import { SERVICE_URLS } from "~/src/constants"
import { Loader } from "lucide-react"
import { Button } from "~/components/ui/button"
import { useAuth } from "~/context/authcontext"
import { useNavigate } from "react-router"

import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "~/components/ui/dialog"

export default function BookDetail() {
  const { id } = useParams()
  const [book, setBook] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const { user, fetchWithAuth } = useAuth()
  const navigate = useNavigate()
  const [openConfirm, setOpenConfirm] = useState(false)
  const [openPlaced, setOpenPlaced] = useState(false)
  const [loadingOrder, setLoadingOrder] = useState(false)
  const [openLoginPrompt, setOpenLoginPrompt] = useState(false)
  const [orderId, setOrderId] = useState<string | null>(null)
  const [orderCompleted, setOrderCompleted] = useState(false)
  const [quantity, setQuantity] = useState(1)
  const [openValidationError, setOpenValidationError] = useState(false)
  const [validationMessage, setValidationMessage] = useState("")
  const [hasPending, setHasPending] = useState(false)

  function startPollingOrderStatus() {
    const interval = setInterval(async () => {
      try {
        const res = await fetchWithAuth(`${SERVICE_URLS.PLACE_ORDER}/checkorder/${orderId}`)
        const data = await res.json()

        if (res.ok && data.data.status === "completed") {
          fetchBook()
          setOpenPlaced(false)
          clearInterval(interval)
          setOrderId(null)
          setOrderCompleted(true)
        } else if (data.data.status === "failed") {
          setOpenPlaced(false)
          clearInterval(interval)
          setOrderId(null)
          setValidationMessage("Your order could not be processed due to insufficient stock or a system error.")
          setOpenValidationError(true)
        }
      } catch (err) {
        console.error("Polling error:", err)
        clearInterval(interval)
      }
    }, 2000)

    return interval
  }

  const fetchBook = async () => {
    const res = await fetch(`${SERVICE_URLS.BOOKS}/books/${id}`)
    const data = await res.json()
    if (res.ok) setBook(data.data)
    setLoading(false)
  }

  const handlePlaceOrder = async () => {
    if (quantity < 1 || quantity > book.quantity) {
      setValidationMessage(`Please enter a valid quantity between 1 and ${book.quantity}.`)
      setOpenValidationError(true)
      return
    }

    setLoadingOrder(true)
    setHasPending(true)
    try {
      const res = await fetchWithAuth(`${SERVICE_URLS.PLACE_ORDER}/placeorder`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          book_id: book['book_id'],
          price: book.price,
          quantity: quantity,
          title: book.title,
          authors: book.authors,
          url: book.url
        })
      })
      const data = await res.json()
      if (res.ok) {
        setOrderId(data.data.order_id)
        setOpenConfirm(false)
        setOpenPlaced(true)
      } else {
        setValidationMessage(data.message || "Failed to place order.")
        setOpenValidationError(true)
      }
    } catch (err) {
      setValidationMessage("Something went wrong. Please try again.")
      setOpenValidationError(true)
    } finally {
      setLoadingOrder(false)
    }
  }

  useEffect(() => {
    if (!orderId) return
    const interval = setInterval(async () => {
      try {
        const res = await fetchWithAuth(`${SERVICE_URLS.PLACE_ORDER}/checkorder/${orderId}`)
        const data = await res.json()
        
        if (res.ok && data.data.status === "completed") {
          fetchBook()
          setOpenPlaced(false)
          clearInterval(interval)
          setOrderId(null)
          setHasPending(false)
          setOrderCompleted(true)
        } else if (data.data.status === "failed") {
          setOpenPlaced(false)
          clearInterval(interval)
          setOrderId(null)
          setHasPending(false)
          setValidationMessage("Your order could not be processed due to insufficient stock or a system error.")
          setOpenValidationError(true)
        }
      } catch (err) {
        console.error("Polling error:", err)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [orderId])

  useEffect(() => {
    fetchBook()
  }, [id])

  useEffect(() => {
    const checkPendingOrder = async () => {
      if (!user || !id) return

      try {
        const res = await fetchWithAuth(`${SERVICE_URLS.PLACE_ORDER}/pendingorder/${id}`)
        const data = await res.json()

        if (res.ok && data.hasPending) {
          setHasPending(true)
          console.log(data)
          setOrderId(data.data['order_id'])
        }
      } catch (err) {
        console.error("Failed to check pending order", err)
      }
    }

    checkPendingOrder()
  }, [user, id])

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
    <div
      className="relative min-h-screen grid md:grid-cols-2 font-serif text-[#5B4636] bg-[#fdf9f1]
        after:absolute after:inset-y-0 after:right-0 after:w-[8px]
        after:bg-gradient-to-b after:from-black/30 after:via-black/10 after:to-black/30
        after:shadow-[0_0_35px_35px_rgba(0,0,0,0.1)] after:blur-md after:rounded-full
        md:after:hidden"
    >
      {/* Left Column – Book Image */}
      <div className="relative flex justify-center bg-gradient-to-r from-[#fcf6e8] to-[#fefaf2] px-20 sm:px-12 lg:px-0 pt-20 md:after:absolute md:after:top-[0px] md:after:h-full md:after:right-0 md:after:w-[8px] md:after:bg-gradient-to-b md:after:from-black/30 md:after:via-black/10 md:after:shadow-[0_0_35px_35px_rgba(0,0,0,0.1)] md:after:to-black/30 md:after:blur-md md:after:rounded-full">
        <div className="group max-h-[500px]  mb-6 [perspective:1000px]">
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
      <div className="flex flex-col justify-center py-10 sm:py-20 px-10 sm:px-14 lg:px-20 font-serif bg-gradient-to-r from-[#f9f4ea] to-[#fef9ee]">
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
        
        {/* Purchase */}
        <div className={`mt-8 flex items-center gap-5 ${(book.quantity === 0 || hasPending) ? "justify-center" : "justify-end"}`}>
          {(book.quantity > 0 && !hasPending) && (
          <label
            htmlFor="quantity"
            className="text-sm text-[#5B4636] font-medium tracking-wide"
          >
            Quantity:
          </label>)}

          {(book.quantity > 0 && !hasPending) && (
          <input
            type="number"
            id="quantity"
            min={1}
            max={book.quantity}
            value={quantity}
            onChange={(e) => {
              setQuantity(Number(e.target.value))
            }}
            className="w-14 text-center border border-[#cbb994] rounded px-2 py-1 text-[#5B4636] bg-[#fdfaf3] focus:outline-none focus:ring-1 focus:ring-[#bca77a]"
          />)}

          <Button
            onClick={() => {
              if (!user) {
                setOpenLoginPrompt(true)
                return
              }

              if (quantity < 1 || quantity > book.quantity) {
                setValidationMessage(`Please enter a valid quantity between 1 and ${book.quantity}.`)
                setOpenValidationError(true)
                return
              }

              setOpenConfirm(true)
            }}
            className="disabled:bg-red-900 cursor-pointer px-6 py-2 rounded-none bg-[#5a7249] text-white uppercase tracking-wider hover:bg-[#465b3a] transition font-serif"
            disabled={book.quantity === 0 || hasPending}
          >
            {book.quantity === 0
              ? "Out of Stock"
              : hasPending
              ? "Order is processing"
              : "Purchase"}
          </Button>
        </div>

        {/* Description */}
        <div className="mt-10 px-2 text-[0.95rem] text-stone-700 leading-[1.75] italic">
            <p className="first-letter:text-3xl first-letter:font-serif first-letter:float-left first-letter:leading-none first-letter:pr-1">
            {book.description}
            </p>
        </div>
      </div>

      {/* Confirm Order Dialog */}
      <Dialog open={openConfirm} onOpenChange={setOpenConfirm}>
        <DialogContent
          className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10 rounded-xl shadow-inner shadow-[#bca77a]/40 border border-[#cbb994]"
          style={{ backgroundImage: "url('/images/parchment.png')" }}
        >
          <DialogHeader>
            <DialogTitle className="mb-3 text-[#3b2f23] font-serif">Confirm Order</DialogTitle>
            <div className="text-[#5B4636] text-sm font-serif space-y-1">
              <p>
                Quantity: <strong>{quantity}</strong>
              </p>
              <p>
                Total: <strong>${(book.price * quantity).toFixed(2)}</strong>
              </p>
              <p>
                Place order for <strong>{book.title}</strong>?
              </p>
            </div>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setOpenConfirm(false)} className="bg-[#fefaf2] hover:bg-[#fffefb] text-[#5B4636]">Cancel</Button>
            <Button onClick={handlePlaceOrder} disabled={loadingOrder} className="text-white bg-[#5a7249] hover:bg-[#465b3a] font-serif">
              {loadingOrder ? "Processing..." : "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Order processing */}
      <Dialog open={openPlaced} onOpenChange={setOpenPlaced}>
        <DialogContent
          className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10 rounded-xl shadow-inner shadow-[#bca77a]/40 border border-[#cbb994]"
          style={{ backgroundImage: "url('/images/parchment.png')" }}
        >
          <DialogHeader>
            <DialogTitle className="mb-3 text-[#3b2f23] font-serif">
              Order is processing!
            </DialogTitle>
            <DialogDescription className="text-[#5B4636] text-sm font-serif">
              Your order is being processed. Please wait or view its status from the My Orders page.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setOpenPlaced(false)}
              className="bg-[#fefaf2] hover:bg-[#fffefb] text-[#5B4636]"
            >
              Close
            </Button>
            <Button
              onClick={() => navigate("/orders")}
              className="text-white bg-[#5a7249] hover:bg-[#465b3a] font-serif"
            >
              My Orders
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Order completed */}
      <Dialog open={orderCompleted} onOpenChange={setOrderCompleted}>
        <DialogContent
          className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10 rounded-xl shadow-inner shadow-[#bca77a]/40 border border-[#cbb994]"
          style={{ backgroundImage: "url('/images/parchment.png')" }}
        >
          <DialogHeader>
            <DialogTitle className="mb-3 text-[#3b2f23] font-serif">
              Order Completed!
            </DialogTitle>
            <DialogDescription className="text-[#5B4636] text-sm font-serif">
              Your order has been successfully processed. You can now view it from the My Orders page.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setOpenPlaced(false)}
              className="bg-[#fefaf2] hover:bg-[#fffefb] text-[#5B4636]"
            >
              Close
            </Button>
            <Button
              onClick={() => navigate("/orders")}
              className="text-white bg-[#5a7249] hover:bg-[#465b3a] font-serif"
            >
              My Orders
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Not logged in */}
      <Dialog open={openLoginPrompt} onOpenChange={setOpenLoginPrompt}>
        <DialogContent
          className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10 rounded-xl shadow-inner shadow-[#bca77a]/40 border border-[#cbb994]"
          style={{ backgroundImage: "url('/images/parchment.png')" }}
        >
          <DialogHeader>
            <DialogTitle className="mb-3 text-[#3b2f23] font-serif">You are not logged In</DialogTitle>
            <DialogDescription className="text-[#5B4636] text-sm font-serif">
              You must be logged in to place an order.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setOpenLoginPrompt(false)} className="bg-[#fefaf2] hover:bg-[#fffefb] text-[#5B4636]">Cancel</Button>
            <Button onClick={() => navigate("/login")} className="text-white bg-[#5a7249] hover:bg-[#465b3a] font-serif">Log In</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Failure */}
      <Dialog open={openValidationError} onOpenChange={setOpenValidationError}>
        <DialogContent
          className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10 rounded-xl shadow-inner shadow-[#bca77a]/40 border border-[#cbb994]"
          style={{ backgroundImage: "url('/images/parchment.png')" }}
        >
          <DialogHeader>
            <DialogTitle className="mb-3 text-[#3b2f23] font-serif">Invalid Quantity</DialogTitle>
            <DialogDescription className="text-[#5B4636] text-sm font-serif">
              {validationMessage}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              onClick={() => setOpenValidationError(false)}
              className="bg-[#fefaf2] hover:bg-[#fffefb] text-[#5B4636]"
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}