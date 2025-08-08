import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { Link } from "react-router";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { useState } from "react"
import { useAuth } from "~/context/authcontext" // adjust path if needed
import { useNavigate } from "react-router"

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    const success = await login(email, password)
    if (success) {
      navigate("/browse")
    } else {
      setError("Invalid email or password.")
    }
  }

  return (
    <div className={cn("flex flex-col gap-6 mx-2", className)} {...props}>
      <Card className="bg-transparent shadow-none border-none">
        <CardHeader>
          <CardTitle>Login to your account</CardTitle>
          <CardDescription>
            Enter your email below to login to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="m@example.com"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pr-20 px-4 py-2 bg-[#f9f2eb] text-[#5B4636] placeholder-[#A89B87] italic font-serif focus:outline-none"
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pr-20 px-4 py-2 bg-[#f9f2eb] text-[#5B4636] placeholder-[#A89B87] italic font-serif focus:outline-none"
                />
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <div className="flex flex-col gap-3">
                <Button type="submit" className="w-full bg-[#99A98B] hover:bg-[#7e9967] hover:cursor-pointer">
                  Login
                </Button>
              </div>
            </div>
            <div className="mt-4 text-center text-sm">
              Don't have an account?{" "}
              <Link to="/signup" className="underline underline-offset-4 cursor-pointer">
                Sign up
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
