import { createContext, useContext, useEffect, useState } from "react"
import { SERVICE_URLS } from "../src/constants";
import { jwtDecode } from "jwt-decode"
import { useNavigate } from "react-router";

type UserPayload = {
  sub: string
  email?: string
  [key: string]: any
}

type AuthContextType = {
  token: string | null
  user: UserPayload | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  signup: (email: string, password: string, username: string) => Promise<boolean>
  tokenReady: boolean,
}

const AuthContext = createContext<AuthContextType | null>(null)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(null)
  const [tokenReady, setTokenReady] = useState(false)
  const [user, setUser] = useState<UserPayload | null>(null)
  const navigate = useNavigate()

  // Refresh token on mount (from HttpOnly cookie)
  useEffect(() => {
    const refresh = async () => {
      try {
        const res = await fetch(`${SERVICE_URLS.USERS}/refresh-token`, {
          method: "POST",
          credentials: "include"
        })

        const data = await res.json()
        if (res.ok) {
          setToken(data.access_token)
          setUser(jwtDecode(data.access_token))
        } else {
          setToken(null)
          setUser(null)
        }
      } catch (err) {
        setToken(null)
      } finally {
        setTokenReady(true)
      }
    }

    refresh()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const res = await fetch(`${SERVICE_URLS.USERS}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password })
      })

      const data = await res.json()
      if (res.ok) {
        setToken(data.access_token)
        setUser(jwtDecode(data.access_token))
        console.log("user:", user);
        return true
      } else {
        return false
      }
    } catch (err) {
      return false
    }
  }

  const logout = async () => {
    await fetch(`${SERVICE_URLS.USERS}/logout`, {
      method: "POST",
      credentials: "include"
    })
    setToken(null)
    setUser(null)
    navigate("/login")
  }

  const signup = async (username: string, email: string, password: string) => {
    try {
      const res = await fetch(`${SERVICE_URLS.USERS}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password })
      })

      const data = await res.json()
      return res.ok
    } catch (err) {
      return false
    }
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, signup, tokenReady }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used within <AuthProvider>")
  return context
}