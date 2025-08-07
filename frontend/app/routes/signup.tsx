import { SignUpForm } from "~/components/signup-form"

export default function Page() {
  return (
    <div className="flex mt-5 w-full h-[90vh] items-center justify-center p-6 md:p-10 bg-contain bg-no-repeat bg-center"
      style={{
        backgroundImage: "url('/images/rose-frame.png')",
      }}
    >
      <div className="w-full max-w-sm">
        <SignUpForm />
      </div>
    </div>
  )
}
