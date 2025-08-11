import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription } from "~/components/ui/dialog"
import { Link, useNavigate } from "react-router"

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
import { useAuth } from "~/context/authcontext"

export function SignUpForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [openDialog, setOpenDialog] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    const result = await signup(username, email, password)
    if (result.ok) {
      setOpenDialog(true)
    } else {
      setError(result.message)
    }
  }

  const handleContinue = () => {
    setOpenDialog(false)
    navigate("/login")
  }

  return (
    <div className={cn("flex flex-col gap-6 mx-2", className)} {...props}>

      <Dialog open={openDialog} onOpenChange={setOpenDialog}>
        <DialogContent
          className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10 rounded-xl shadow-inner shadow-[#bca77a]/40 border border-[#cbb994]"
          style={{ backgroundImage: "url('/images/parchment.png')" }}
        >
          <DialogHeader>
            <DialogTitle className="mb-3 text-[#3b2f23] font-serif">
              You have created an account!
            </DialogTitle>
            <DialogDescription className="text-[#5B4636] text-sm max-w-[85%] font-serif">
              You have successfully signed up! Please log in to your account.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              className="mx-auto mt-6 bg-[#C1B49A] hover:bg-[#aa9978] text-[#3B2F23] font-serif px-6 py-2"
              onClick={handleContinue}
            >
              Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card className="bg-transparent shadow-none border-none">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
          <CardDescription>
            Enter your details below to create your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-3">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  placeholder="yourusername"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pr-20 px-4 py-2 border border-[#cbb994] bg-[#fefaf2] text-[#5B4636] placeholder-[#aa9980] italic font-serif focus:outline-none"
                />
              </div>
              <div className="grid gap-3">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="m@example.com"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pr-20 px-4 py-2 border border-[#cbb994] bg-[#fefaf2] text-[#5B4636] placeholder-[#aa9980] italic font-serif focus:outline-none"
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
                  className="w-full pr-20 px-4 py-2 border border-[#cbb994] bg-[#fefaf2] text-[#5B4636] placeholder-[#aa9980] italic font-serif focus:outline-none"
                />
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <div className="flex flex-col gap-3">
                <Button type="submit" className="w-full bg-[#C1B49A] hover:bg-[#aa9978] text-[#3B2F23] font-serif transition duration-200 cursor-pointer">
                  Sign Up
                </Button>
              </div>
            </div>
            <div className="mt-4 text-center text-sm">
              Already have an account?{" "}
              <Link to="/login" className="underline underline-offset-4">
                Log in
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
