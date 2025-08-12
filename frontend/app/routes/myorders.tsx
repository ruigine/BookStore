import { useEffect, useState, useRef } from "react"
import { SERVICE_URLS } from "~/src/constants"
import { useAuth } from "~/context/authcontext"
import { Link } from "react-router"
import { Button } from "~/components/ui/button"
import { RefreshCcw } from "lucide-react"
import ProtectedRoute from "~/components/protectedroute";

interface Order {
  order_id: number
  book_id: number
  title: string
  authors: string
  quantity: number
  price: string
  status: string
  order_date: string
  url: string
}

export default function MyOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const { user, fetchWithAuth } = useAuth()
  const [page, setPage] = useState(1);
  const scrollAttached = useRef(false);
  const [hasMore, setHasMore] = useState(true);
  
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
    if (!user) return

    const fetchOrders = async () => {
      try {
        if (page == 0 || page == 1 || hasMore) {
          const res = await fetchWithAuth(`${SERVICE_URLS.DISPLAY_ORDERS}/myorders?page=${Math.max(1, page)}`)
          const data = await res.json()

          if (res.ok) {
            setOrders(prev =>
              (page === 1 || page === 0) ? data.data : [...prev, ...data.data]
            )
          }

          setHasMore(data.pagination["has_more"])

          // console.log(data)
          if (!scrollAttached.current) {
            window.addEventListener("scroll", handleScroll)
            scrollAttached.current = true
          }
        }
      } catch (err) {
        console.error("Failed to fetch orders", err)
      } finally {
        setLoading(false)
      }
    }

    fetchOrders()
  }, [user, page])

  return (
    <ProtectedRoute>
      <div className="bg-[#fdfaf3] min-h-screen px-6 sm:px-12 py-16 max-w-5xl mx-auto font-serif text-[#4A3B2E] tracking-wide">
        {/* Vintage Chapter Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-4 mb-6 text-[#c5bca4] text-xl select-none">
            <span className="border-t border-[#c5bca4] w-10" />
            ❧
            <span className="border-t border-[#c5bca4] w-10" />
          </div>
          <h1 className="text-4xl font-[Eagle_Lake] mt-2">My Orders</h1>
          <p className="italic text-base mt-1">View your ongoing and past orders here.</p>
          <div className="my-6 flex justify-center">
            <div className="w-40 border-t border-[#d5c3a3]"></div>
          </div>
        </div>

        {!loading && orders.length > 0 && (
          <div className="flex justify-end mb-8">
            <Button
              onClick={() => {
                setLoading(true)
                setOrders([])
                setHasMore(true);
                setPage((prev) => prev === 1 ? 0 : 1)
              }}
              className="group flex items-center gap-2 bg-[#5a7249] hover:bg-[#465b3a] text-white font-serif tracking-wide rounded-full px-4 py-2 shadow-sm border border-[#4a5e3a] transition-all duration-200"
            >
              <RefreshCcw className="w-4 h-4 group-hover:rotate-[-25deg] transition-transform duration-300" />
              <span>Refresh Orders</span>
            </Button>
          </div>
        )}

        {/* Order Section */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-[#d5c3a3] border-t-transparent rounded-full animate-spin mb-4" />
            <p className="italic text-[#857158] text-lg">Retrieving your personal order log...</p>
          </div>
        ) : orders.length === 0 ? (
          <p className="text-center italic text-stone-500">No orders found.</p>
        ) : (
          <div className="space-y-14">
            {orders.map((order) => (
              <Link
                key={order.order_id}
                to={`/books/${order.book_id}`}
                className="block transform transition duration-300 hover:-translate-y-1 hover:shadow-md rounded-xl"
              >
                <div className="bg-[#fbf8f2] border border-[#d7c9b0] rounded-xl shadow-sm px-6 py-7 relative">
                  {/* Top Label */}
                  <div className="absolute -top-4 left-6 bg-[#fbf8f2] px-3 text-sm italic tracking-wider text-[#857158] border border-[#d7c9b0] rounded-full shadow">
                    Order #{order.order_id}
                  </div>

                  {/* Book and Details */}
                  <div className="flex flex-col sm:flex-row gap-6">
                    <img
                      src={order.url}
                      alt={order.title}
                      className="w-[100px] sm:w-[110px] h-auto object-contain rounded-md shadow"
                    />
                    <div className="space-y-2">
                      <h2 className="text-xl font-semibold">{order.title}</h2>
                      <p className="italic text-sm">by {order.authors}</p>
                      <p className="text-sm">
                        <span className="font-medium">Purchased on:</span>{" "}
                        {new Date(order.order_date).toLocaleDateString("en-SG", {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                        })}
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Quantity:</span> {order.quantity}
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Total Cost:</span> $
                        {(+order.price * order.quantity).toFixed(2)}
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Status:</span>{" "}
                        <span
                          className={
                            order.status === "completed"
                              ? "text-green-800"
                              : order.status === "failed"
                              ? "text-red-800"
                              : "text-yellow-800"
                          }
                        >
                          {order.status}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  )
}