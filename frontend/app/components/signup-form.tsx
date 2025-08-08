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

    const success = await signup(username, email, password)
    if (success) {
      setOpenDialog(true)
    } else {
      setError("Failed to create account. Try again.")
    }
  }

  const handleContinue = () => {
    setOpenDialog(false)
    navigate("/login")
  }

  return (
    <div className={cn("flex flex-col gap-6 mx-2", className)} {...props}>

      <Dialog open={openDialog} onOpenChange={setOpenDialog}>
        <DialogContent className="sm:max-w-md text-center bg-cover bg-no-repeat bg-center py-10" style={{ backgroundImage: "url('/images/parchment.png')" }}>
          <DialogHeader>
            <DialogTitle className="mb-3">You have created an account!</DialogTitle>
            <DialogDescription>
              You have successfully signed up! Please log in to your account.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button className="mx-auto bg-[#99A98B] hover:bg-[#7e9967] hover:cursor-pointer" onClick={handleContinue}>
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
                  className="w-full pr-20 px-4 py-2 bg-[#f9f2eb] text-[#5B4636] placeholder-[#A89B87] italic font-serif focus:outline-none"
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
